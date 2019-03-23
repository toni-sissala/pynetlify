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
    logger.debug(pprint.pformat(rdict))
    return Site(name=rdict['name'], id=rdict['id'], url=rdict['url'])


class APIRequest:

    base_url = 'https://api.netlify.com/api/'
    headers = {'User-Agent': 'PyNetlify (toni.sissala@gmail.com)'}

    def __init__(self, auth_token):
        self._auth_token = auth_token

    def _auth_url(self, *p):
        url = self.base_url + '/'.join(p) + '?access_token={}'.format(
            self._auth_token)
        return url

    def sites(self):
        url = self._auth_url('v1', 'sites')
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        for site in response.json():
            yield rdict_to_site(site)

    def create_site(self, **site_properties):
        response = requests.post(self._auth_url('v1', 'sites'), json=site_properties, headers=self.headers)
        response.raise_for_status()
        if response.status_code != 201:
            logger.warning('Unexpected response status code %s'
                           % (response.status_code,))
        return rdict_to_site(response.json())

    def delete_site(self, site):
        url = self._auth_url('v1', 'sites', site.id)
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        if response.status_code != 200:
            logger.warning('Unexpected response status code %s'
                           % (response.status_code,))
        return True

    def deploy_folder_to_site(self, folder, site, force_all=False):
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
            return
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
