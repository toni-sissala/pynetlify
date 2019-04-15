# PyNetlify - Python client and library to interact with Netlify API.
# Copyright (C) 2019  Toni Sissala
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import sys
from collections import namedtuple
import hashlib
import glob
import logging
import pprint
import requests


if sys.version_info[0] == 2:
    from urllib import quote as quote_url
else:
    from urllib.parse import quote as quote_url


Site = namedtuple('Site', ['name', 'id', 'url'])
logger = logging.getLogger(__name__)


def rdict_to_site(rdict):
    """Create a new :obj:`Site` from a dictionary received from
    a HTTP response JSON payload.

    :param rdict: HTTP response dictionary.
    :type rdict: dict
    :returns: Site created from the dictionary.
    :rtype: :obj:`Site`
    """
    logger.debug(pprint.pformat(rdict))
    return Site(name=rdict['name'], id=rdict['id'], url=rdict['url'])


def _iter_folder_filepaths_py3(folder):
    lookup_path = os.path.join(folder, '**')
    for filepath in glob.iglob(lookup_path, recursive=True):
        yield filepath


def _iter_folder_filepaths_py2(folder):
    yield folder
    for root, dirnames, filenames in os.walk(folder):
        for filename in filenames + dirnames:
            yield os.path.join(root, filename)


iterate_folder_filepaths = _iter_folder_filepaths_py2 if sys.version_info[0] == 2 else _iter_folder_filepaths_py3


class APIRequest:

    base_url = 'https://api.netlify.com/api/'
    api_version = 'v1'
    headers = {'User-Agent': 'PyNetlify (toni.sissala@gmail.com)'}

    def __init__(self, auth_token):
        """Initialize an APIRequest object.

        :param auth_token: Authentication token.
        :type auth_token: str
        """
        self._auth_token = auth_token

    def _auth_url(self, *p):
        if self.api_version is not None:
            api_url = self.base_url + self.api_version + '/'
        else:
            api_url = self.base_url
        url = api_url + '/'.join(p) + '?access_token={}'.format(self._auth_token)
        return url

    def get_site(self, site_id_or_domain):
        """Get site information.

        :param site_id_or_domain: Site id or domain
        :type site_id_or_domain: stream
        :returns: Site.
        :rtype: :obj:`Site`
        """
        url = self._auth_url('sites', site_id_or_domain)
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        response_json = response.json()
        logger.debug(pprint.pformat(response_json))
        return rdict_to_site(response_json)

    def get_site_files(self, site):
        """Get files in site.

        :param site: Target site.
        :type site: :obj:`Site`
        :returns: List of files.
        :rtype: list
        """
        url = self._auth_url('sites', site.id, 'files')
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        response_json = response.json()
        logger.debug(pprint.pformat(response_json))
        return response_json

    def sites(self):
        """Iterate sites.

        :returns: Sites one by one.
        :rtype: :obj:`Site`
        """
        url = self._auth_url('sites')
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        for site in response.json():
            yield rdict_to_site(site)

    def create_site(self, site_properties):
        """Create a new site.

        :param site_properties: Site properties get passed into
                                the HTTP POST request body.
        :type site_properties: dict
        :returns: Created site.
        :rtype: :obj:`Site`
        """
        response = requests.post(self._auth_url('sites'), json=site_properties, headers=self.headers)
        response.raise_for_status()
        if response.status_code != 201:
            logger.warning('Unexpected response status code %s'
                           % (response.status_code,))
        return rdict_to_site(response.json())

    def delete_site(self, site):
        """Delete a site.

        :param site: Site to delete.
        :type site: :obj:`Site`
        :returns: True if success.
        :rtype: bool
        """
        url = self._auth_url('sites', site.id)
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        if response.status_code != 204:
            logger.warning('Unexpected response status code %s'
                           % (response.status_code,))
        return True

    def deploy_folder_to_site(self, folder, site):
        """Deploy a folder to a site.

        :param folder: Path to a folder.
        :type folder: str
        :param site: Site to deploy to.
        :type site: :obj:`Site`
        :returns: None if nothing gets deployed. Deploy id if files get deployed.
        :rtype: None or int
        """
        folder = folder + os.sep if not folder.endswith(os.sep) else folder
        files_hashes = {}
        for filepath in iterate_folder_filepaths(folder):
            if not os.path.isfile(filepath):
                continue
            logger.debug('Preparing hash of %s', filepath)
            with open(filepath, 'rb') as filehandle:
                files_hashes.update({
                    filepath.replace(folder, '', 1):
                    hashlib.sha1(filehandle.read()).hexdigest()
                })
        if files_hashes == {}:
            # TODO Should we POST anyway to delete all previously deployed files?
            logger.warning('Found no files from path %s', (folder,))
            return None
        logger.debug('Requesting required hashes of files %s',
                     ', '.join(files_hashes.keys()))
        response = requests.post(self._auth_url('sites',
                                                site.id,
                                                'deploys'),
                                 json={'files': files_hashes},
                                 headers=self.headers)
        response.raise_for_status()
        response_json = response.json()
        logger.debug(pprint.pformat(response_json))
        deploy_id = response_json['id']
        required_hashes = response_json['required']
        logger.debug('Required filehashes: %s', required_hashes)
        if not required_hashes:
            return deploy_id
        hashes_files = {value: key for (key, value) in files_hashes.items()}

        deploy_headers = self.headers.copy()
        deploy_headers.update({'Content-Type': 'application/octet-stream'})
        for required_hash in required_hashes:
            filepath = folder + hashes_files[required_hash]
            with open(filepath, 'rb') as filehandle:
                response = requests.put(
                    self._auth_url('deploys',
                                   deploy_id, 'files',
                                   quote_url(hashes_files[required_hash])),
                    data=filehandle,
                    headers=deploy_headers)
                response.raise_for_status()
        return deploy_id

    def get_deploy(self, deploy_id):
        """Get deploy info.

        :param deploy_id: ID of the deploy.
        :returns: Deploy information.
        :rtype: dict
        """
        url = self._auth_url('deploys', deploy_id)
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        response_json = response.json()
        logger.debug(pprint.pformat(response_json))
        return response.json()
