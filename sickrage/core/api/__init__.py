from __future__ import unicode_literals

from urlparse import urljoin

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

import sickrage
from sickrage.core.api.exceptions import unauthorized, error


class API(object):
    def __init__(self, client_id=None, client_secret=None):
        self.api_url = 'https://api.sickrage.ca/'
        self.token_url = urljoin(self.api_url, 'oauth/v2/token')
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.client = None
        self.login()

    def login(self):
        if self.client and self.token:
            return True

        credentials = {
            'client_id': self.client_id or sickrage.app.config.api_client_id,
            'client_secret': self.client_secret or sickrage.app.config.api_client_secret
        }

        oauth = OAuth2Session(client=BackendApplicationClient(client_id=credentials['client_id']))

        try:
            self.token = oauth.fetch_token(token_url=self.token_url, timeout=30, **credentials)
            self.client = OAuth2Session(credentials['client_id'], token=self.token, auto_refresh_url=self.token_url,
                                        auto_refresh_kwargs=credentials, token_updater=self.token_saver)

            return True
        except Exception as e:
            pass

    def logout(self):
        self.token = self.client = None

    def token_saver(self, token):
        self.token = token

    def _request(self, method, url, **kwargs):
        if not sickrage.app.config.enable_api:
            return

        if not self.login():
            return

        try:
            resp = self.client.request(method, urljoin(self.api_url, url), timeout=30, **kwargs)
        except Exception as e:
            raise error(e.message)

        # handle requests exceptions
        if resp.status_code == 401:
            raise unauthorized(resp.json()['message'])
        elif resp.status_code >= 400:
            raise error(resp.json()['message'])

        return resp.json()

    def user_profile(self):
        return self._request('GET', 'users/me')

    def add_cache_result(self, data):
        self._request('POST', 'v1/providers/cache/results', json=data)

    def get_cache_results(self, provider, indexerid=None):
        query = ('v1/providers/cache/results/{}'.format(provider),
                 'v1/providers/cache/results/{}/indexerids/{}'.format(provider, indexerid))[indexerid is not None]

        return self._request('GET', query)

    def magnet2torrent(self, magnet):
        return self._request('POST', 'v1/mag2tor', data=dict({'magnet':magnet}))
