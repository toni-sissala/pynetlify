import sys
import unittest
from pynetlify import cli

running_python2 = sys.version_info[0] == 2
if running_python2:
    import mock
    from StringIO import StringIO
else:
    from unittest import mock
    from io import StringIO


class CliOperationsTest(unittest.TestCase):

    def setUp(self):
        self.mock_netlify_api = mock.MagicMock()

    def test_list_sites_calls_sites(self):
        cli.list_sites(self.mock_netlify_api, None)
        self.mock_netlify_api.sites.assert_called_once_with()

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_list_sites_prints_sites(self, mock_stdout):
        self.mock_netlify_api.sites.return_value = ['site1', 'site2', 'site3']
        cli.list_sites(self.mock_netlify_api, None)
        self.assertEqual(mock_stdout.getvalue(), 'site1\nsite2\nsite3\n')

    @mock.patch.object(cli.pynetlify, 'Site')
    def test_delete_site_calls_initiates_Site(self, mock_Site):
        cli.delete_site(self.mock_netlify_api, mock.Mock(site_id='some_id'))
        mock_Site.assert_called_once_with(name=None, url=None, id='some_id')

    @mock.patch.object(cli.pynetlify, 'Site')
    def test_delete_site_calls_delete_site_with_site(self, mock_Site):
        mock_Site.return_value = 'some_site'
        cli.delete_site(self.mock_netlify_api, mock.Mock(site_id='some_id'))
        self.mock_netlify_api.delete_site.assert_called_once_with('some_site')

    def test_delete_all_sites_calls_sites_on_netlify_api(self):
        cli.delete_all_sites(self.mock_netlify_api, None)
        self.mock_netlify_api.sites.assert_called_once_with()

    def test_delete_all_sites_calls_netlify_api(self):
        self.mock_netlify_api.sites.return_value = ['site_1', 'site_2']
        cli.delete_all_sites(self.mock_netlify_api, None)
        self.assertEqual(self.mock_netlify_api.delete_site.call_count, 2)
        self.mock_netlify_api.delete_site.assert_has_calls([
            mock.call('site_1'), mock.call('site_2')])


if __name__ == '__main__':
    unittest.main()
