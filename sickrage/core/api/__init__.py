from __future__ import unicode_literals

import json
from urlparse import urljoin

from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session

import sickrage
from sickrage.core.api.exceptions import unauthorized, error


class API(object):
    def __init__(self, username=None, password=None):
        self.client_id = '5YBSSD10UQN644DC13OHURJCESCOQBVR'
        self.api_url = 'https://api.sickrage.ca/'
        self.token_url = urljoin(self.api_url, 'oauth/v2/token')
        self.username = username
        self.password = password
        self.token = None
        self.client = None
        self.login()

    def login(self):
        if self.client and self.token:
            return True

        self.username = self.username or sickrage.app.config.api_username
        self.password = self.password or sickrage.app.config.api_password

        if self.username and self.password:
            oauth = OAuth2Session(client=LegacyApplicationClient(client_id=self.client_id))

            try:
                self.token = oauth.fetch_token(token_url=self.token_url, client_id=self.client_id, verify=False,
                                               timeout=30, username=self.username, password=self.password)

                self.client = OAuth2Session(self.client_id, token=self.token, auto_refresh_url=self.token_url,
                                            auto_refresh_kwargs={"client_id": self.client_id},
                                            token_updater=self.token_saver)

                return True
            except Exception:
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
        self._request('POST', 'v1/providers/cache/results', data=json.dumps(data))

    def get_cache_results(self, provider, indexerid=None):
        query = ('v1/providers/cache/results/{}'.format(provider),
                 'v1/providers/cache/results/{}/indexerids/{}'.format(provider, indexerid))[indexerid is not None]

        return self._request('GET', query)
