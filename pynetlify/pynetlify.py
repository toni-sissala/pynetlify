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
from collections import namedtuple
import urllib
import hashlib
import glob
import logging
import pprint
import requests


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


class APIRequest:

    base_url = 'https://api.netlify.com/api/'
    headers = {'User-Agent': 'PyNetlify (toni.sissala@gmail.com)'}

    def __init__(self, auth_token):
        """Initialize an APIRequest object.

        :param auth_token: Authentication token.
        :type auth_token: str
        """
        self._auth_token = auth_token

    def _auth_url(self, *p):
        url = self.base_url + '/'.join(p) + '?access_token={}'.format(self._auth_token)
        return url

    def sites(self):
        """Iterate sites.

        :returns: Generator which iterates sites.
        :rtype: :obj:`Generator`
        """
        url = self._auth_url('v1', 'sites')
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
        response = requests.post(self._auth_url('v1', 'sites'), json=site_properties, headers=self.headers)
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
        url = self._auth_url('v1', 'sites', site.id)
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        if response.status_code != 200:
            logger.warning('Unexpected response status code %s'
                           % (response.status_code,))
        return True

    def deploy_folder_to_site(self, folder, site, force_all=False):
        """Deploy a folder to a site.

        :param folder: Path to a folder.
        :type folder: str
        :param site: Site to deploy to.
        :type site: :obj:`Site`
        :param force_all: Force all flag will deploy all
                          files found from ''folder'' regardless
                          if they are already deployed to the site.
                          Defaults to False.
        :type force_all: bool
        :returns: None if nothing gets deployed. Deploy id if files get deployed.
        :rtype: None or int
        """
        lookup_path = os.path.join(folder, '**')
        files_hashes = {}
        for filepath in glob.iglob(lookup_path, recursive=True):
            if not os.path.isfile(filepath):
                continue
            logger.debug('Preparing hash of %s', filepath)
            with open(filepath, 'rb') as filehandle:
                files_hashes.update({
                    filepath.replace(folder, '', 1):
                    hashlib.sha1(filehandle.read()).hexdigest()
                })
        logger.debug('Requesting required hashes of files %s',
                     ', '.join(files_hashes.keys()))
        response = requests.post(self._auth_url(
            'v1', 'sites', site.id, 'deploys'),
                                 json={'files': files_hashes},
                                 headers=self.headers)
        response.raise_for_status()
        response_json = response.json()
        logger.debug(pprint.pformat(response_json))
        required_hashes = response_json['required']
        logger.debug('Required filehashes: %s', required_hashes)
        if not required_hashes and not force_all:
            return None
        hashes_files = {value: key for (key, value) in files_hashes.items()}
        deploy_id = response_json['id']
        deploy_headers = self.headers.copy()
        deploy_headers.update({'Content-Type': 'application/octet-stream'})
        if force_all:
            required_hashes = files_hashes.values()
        for required_hash in required_hashes:
            filepath = folder + hashes_files[required_hash]
            with open(filepath, 'rb') as filehandle:
                response = requests.put(
                    self._auth_url('v1', 'deploys',
                                   deploy_id, 'files',
                                   urllib.parse.quote(hashes_files[required_hash])),
                    data=filehandle,
                    headers=deploy_headers)
                response.raise_for_status()
        return deploy_id
