import sys
import unittest
from tempfile import NamedTemporaryFile
from pynetlify import pynetlify


running_python2 = sys.version_info[0] == 2
if running_python2:
    import mock
else:
    from unittest import mock


class APIRequestTestBase(unittest.TestCase):

    _test_sites = [{'name': 'some_sitename',
                    'id': 'site_id',
                    'url': 'some_url'},
                   {'name': 'another_sitename',
                    'id': 'another_site_id',
                    'url': 'another_url'}]
    _netlify_api_url = 'https://api.netlify.com/api/v1/'

    def setUp(self):
        self._patchers = []
        patch_requests = mock.patch.object(pynetlify, 'requests')
        self._mock_requests = patch_requests.start()
        self._patchers.append(self._mock_requests)
        self._api = pynetlify.APIRequest('auth-token')

    def tearDown(self):
        for patcher in self._patchers:
            patcher.stop()


class TestAPIRequests(APIRequestTestBase):
    """Tests to assert correct calls to Netlify API"""

    def test_get_site(self):
        mock_response = mock.Mock()
        mock_response.json.return_value = self._test_sites[0]
        self._mock_requests.get.return_value = mock_response
        site = self._api.get_site('some_site_id')
        self._mock_requests.get.assert_called_once_with(
            self._netlify_api_url + 'sites/some_site_id?access_token={}'.format('auth-token'),
            headers=self._api.headers)
        self.assertEqual(site, pynetlify.rdict_to_site(self._test_sites[0]))

    def test_get_site_files(self):
        mock_response = mock.Mock()
        mock_response.json.return_value = ['file.html', 'other_file.html']
        self._mock_requests.get.return_value = mock_response
        files = self._api.get_site_files(pynetlify.Site(id='some_site_id', name=None, url=None))
        self._mock_requests.get.assert_called_once_with(
            self._netlify_api_url + 'sites/some_site_id/files?access_token={}'.format('auth-token'),
            headers=self._api.headers)
        self.assertEqual(files, ['file.html', 'other_file.html'])

    def test_sites(self):
        # Mock
        mock_response = mock.Mock()
        mock_response.json.return_value = self._test_sites
        self._mock_requests.get.return_value = mock_response
        # Call
        sites = list(self._api.sites())
        # Assert
        self._mock_requests.get.assert_called_once_with(
            self._netlify_api_url + 'sites?access_token={}'.format('auth-token'),
            headers=self._api.headers)
        self.assertEqual(len(sites), 2)
        if running_python2:
            self.assertItemsEqual(sites, [
                pynetlify.rdict_to_site(self._test_sites[0]),
                pynetlify.rdict_to_site(self._test_sites[1])])
        else:
            self.assertCountEqual(sites, [
                pynetlify.rdict_to_site(self._test_sites[0]),
                pynetlify.rdict_to_site(self._test_sites[1])])
        mock_response.json.assert_called_with()

    def test_create_site(self):
        # Mock
        mock_response = mock.Mock()
        mock_response.json.return_value = self._test_sites[0]
        self._mock_requests.post.return_value = mock_response
        # Call
        rval = self._api.create_site({'prop_1': 'val_1',
                                      'prop_2': 'val_2'})
        # Assert
        self._mock_requests.post.assert_called_once_with(
            self._netlify_api_url + 'sites?access_token={}'.format('auth-token'),
            headers=self._api.headers,
            json={'prop_1': 'val_1',
                  'prop_2': 'val_2'})
        self.assertEqual(rval, pynetlify.rdict_to_site(self._test_sites[0]))

    def test_delete_site(self):
        rval = self._api.delete_site(pynetlify.Site(id='del_id', name=None, url='some.url'))
        self._mock_requests.delete.assert_called_once_with(
            self._netlify_api_url + 'sites/del_id?access_token={}'.format('auth-token'),
            headers=self._api.headers)
        self.assertEqual(rval, True)

    def test_get_deploy(self):
        mock_response = mock.Mock()
        mock_response.json.return_value = {'deploy': 'deploy_id'}
        self._mock_requests.get.return_value = mock_response
        deploy = self._api.get_deploy('some_deploy_id')
        self._mock_requests.get.assert_called_once_with(
            self._netlify_api_url + 'deploys/some_deploy_id?access_token={}'.format('auth-token'),
            headers=self._api.headers)
        self.assertEqual(deploy, {'deploy': 'deploy_id'})


class TestAPIRequestsDeploy(APIRequestTestBase):

    @mock.patch.object(pynetlify, 'glob')
    def test_deploy_folder_to_site_does_not_post_none_files(self, mock_glob):
        mock_site = mock.Mock(id='some_id')
        rval = self._api.deploy_folder_to_site('/some/path', mock_site)
        mock_glob.iglob.assert_called_once_with('/some/path/**', recursive=True)
        self._mock_requests.post.assert_not_called()
        self.assertEqual(rval, None)

    @mock.patch.object(pynetlify, 'glob')
    def test_deploy_folder_to_site_posts_filepath(self, mock_glob):
        tempfile = NamedTemporaryFile()
        stripped_name = tempfile.name.replace('/tmp/', '', 1)
        mock_glob.iglob.return_value = [tempfile.name]
        self._api.deploy_folder_to_site('/tmp', mock.Mock(id='some_other_id'))
        self.assertEqual(self._mock_requests.post.call_count, 1)
        _, kwargs = self._mock_requests.post.call_args
        self.assertEqual(list(kwargs['json']['files'].keys())[0], stripped_name)

    @mock.patch.object(pynetlify, 'hashlib')
    @mock.patch.object(pynetlify, 'glob')
    def test_deploy_folder_to_site_puts_filecontents(self,
                                                     mock_glob,
                                                     mock_hashlib):
        mock_hash = mock.Mock()
        mock_hash.hexdigest.return_value = 'some_hash'
        mock_hashlib.sha1.return_value = mock_hash
        mock_response = mock.Mock()
        mock_response.json.return_value = {'id': 'dep_id',
                                           'required': ['some_hash']}
        tempfile = NamedTemporaryFile()
        expected_url = self._netlify_api_url +\
            'deploys/dep_id/files/{}?access_token={}'\
            .format(tempfile.name.replace('/tmp/', '', 1),
                    'auth-token')
        mock_glob.iglob.return_value = [tempfile.name]
        self._mock_requests.post.return_value = mock_response
        rval = self._api.deploy_folder_to_site('/tmp', mock.Mock(id='some_other_id'))
        self.assertEqual(self._mock_requests.put.call_count, 1)
        args, _ = self._mock_requests.put.call_args
        url = args[0]
        print(url)
        self.assertEqual(url, expected_url)
        self.assertEqual(rval, 'dep_id')


if __name__ == '__main__':
    unittest.main()
