from collections import namedtuple
import requests

Site = namedtuple('Site', ['name', 'id', 'url'])


def rdict_to_site(rdict):
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
        response = requests.get(url, self.headers)
        response.raise_for_status()
        for site in response.json():
            yield rdict_to_site(site)

    def create_site(self):
        response = requests.post(self._auth_url('v1', 'sites'), self.headers)
        response.raise_for_status()
        if response.status_code != 201:
            raise Exception('Invalid response status_code %s'
                            % (response.status_code,))
        return rdict_to_site(response.json())

    def delete_site(self, site):
        url = self._auth_url('v1', 'sites', site.id)
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        if response.status_code != 200:
            raise Exception('Invalid response status_code %s'
                            % (response.status_code,))
        return True
