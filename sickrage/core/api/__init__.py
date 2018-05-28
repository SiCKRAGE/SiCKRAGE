from __future__ import unicode_literals

import json
import os
from urlparse import urljoin

from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session

import sickrage
from sickrage.core.api.exceptions import unauthorized, error


class API(object):
    def __init__(self, username=None, password=None):
        self.api_url = 'https://api.sickrage.ca/'
        self.token_url = urljoin(self.api_url, 'oauth/token')
        self.token_file = os.path.join(sickrage.app.data_dir, 'sr_token.json')
        self._username = username
        self._password = password
        self._session = None
        self._token = None

    @property
    def credentials(self):
        return {
            'client_id': 2,
            'client_secret': '7kEyr9jKuqOV4FFy2bOxOwA2RiB4WSHsEUU2P3BJ',
            'username': self._username or sickrage.app.config.api_username,
            'password': self._password or sickrage.app.config.api_password
        }

    @property
    def session(self):
        if self._session is None:
            self._session = OAuth2Session(self.credentials['client_id'],
                                          token=self.token,
                                          auto_refresh_url=self.token_url,
                                          auto_refresh_kwargs={'client_id': self.credentials['client_id'],
                                                               'client_secret': self.credentials['client_secret']},
                                          token_updater=self._token_updater)
        return self._session

    @property
    def token(self):
        if self._token is None:
            if self._username != sickrage.app.config.api_username or self._password != sickrage.app.config.api_password:
                if os.path.isfile(self.token_file):
                    os.remove(self.token_file)

            if not os.path.isfile(self.token_file):
                oauth = OAuth2Session(client=LegacyApplicationClient(client_id=self.credentials['client_id']))
                self._token = oauth.fetch_token(token_url=self.token_url,
                                                timeout=30,
                                                **self.credentials)

                self._token_updater(self._token)
            else:
                with open(self.token_file) as infile:
                    self._token = json.load(infile)

        return self._token

    def _token_updater(self, token):
        with open(self.token_file, 'w') as outfile:
            json.dump(token, outfile)

    def _request(self, method, url, **kwargs):
        if not sickrage.app.config.enable_api:
            return

        resp = self.session.request(method, urljoin(self.api_url, url), timeout=30, **kwargs)
        if resp.status_code == 401:
            raise unauthorized(resp.json()['message'])
        elif resp.status_code >= 400:
            raise error(resp.json()['message'])

        return resp.json()

    def user_profile(self):
        return self._request('GET', 'user')
