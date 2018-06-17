from __future__ import unicode_literals

import json
import os
import time
from urlparse import urljoin

from oauthlib.oauth2 import LegacyApplicationClient, MissingTokenError, InvalidClientIdError
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
            'username': self._username or sickrage.app.config.app_username,
            'password': self._password or sickrage.app.config.app_password,
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
            if any([self._username, self._password]) and os.path.isfile(self.token_file):
                os.remove(self.token_file)

            if not os.path.exists(self.token_file):
                oauth = OAuth2Session(client=LegacyApplicationClient(client_id=self.credentials['client_id']))

                try:
                    self._token = oauth.fetch_token(token_url=self.token_url, timeout=30, **self.credentials)
                except MissingTokenError:
                    self._token = None

                self._token_updater(self._token)
            else:
                with open(self.token_file) as infile:
                    self._token = json.load(infile)

        return self._token

    def _token_updater(self, token):
        with open(self.token_file, 'w') as outfile:
            json.dump(token, outfile)

    def _request(self, method, url, **kwargs):
        try:
            resp = self.session.request(method, urljoin(self.api_url, url), timeout=30,
                                        hooks={'response': self.throttle_hook}, **kwargs)

            if resp.status_code == 401:
                raise unauthorized(resp.json()['message'])
            elif resp.status_code >= 400:
                raise error(resp.json()['message'])

            return resp.json()
        except (InvalidClientIdError, MissingTokenError) as e:
            sickrage.app.log.warning("SiCKRAGE username or password is incorrect, please try again")

    @staticmethod
    def throttle_hook(response, **kwargs):
        ratelimited = "X-RateLimit-Remaining" in response.headers

        if ratelimited:
            remaining = int(response.headers["X-RateLimit-Remaining"])
            if remaining == 1:
                sickrage.app.log.debug("Throttling SiCKRAGE API Calls... Sleeping for 60 secs...\n")
                time.sleep(60)
