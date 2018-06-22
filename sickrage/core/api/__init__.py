from __future__ import unicode_literals

import json
import os
import time
from urlparse import urljoin

from oauthlib.oauth2 import MissingTokenError, InvalidClientIdError, TokenExpiredError
from requests_oauthlib import OAuth2Session

import sickrage
from sickrage.core.api.exceptions import unauthorized, error


class API(object):
    def __init__(self):
        self.api_url = 'https://api.sickrage.ca/api/v1/'
        self.token_file = os.path.join(sickrage.app.data_dir, 'sr_token.json')
        self._token = {}

    @property
    def session(self):
        return OAuth2Session(token=self.token)

    @property
    def token(self):
        if os.path.exists(self.token_file):
            with open(self.token_file) as infile:
                self._token = json.load(infile)
        return self._token

    @token.setter
    def token(self, value):
        with open(self.token_file, 'w') as outfile:
            json.dump(value, outfile)

    @property
    def userinfo(self):
        if self.token:
            return sickrage.app.oidc_client.userinfo(self.token['access_token'])

    def register_appid(self, appid):
        self._request('POST', 'register-appid', json={'appid': appid})

    def _request(self, method, url, **kwargs):
        try:
            resp = self.session.request(method, urljoin(self.api_url, url), timeout=30,
                                        hooks={'response': self.throttle_hook}, **kwargs)

            if resp.status_code == 401:
                msg = resp.json()['message']
                raise unauthorized(msg)
            elif resp.status_code >= 400:
                msg = resp.json()['message']
                if resp.status_code == 500 and msg == 'Token is expired':
                    raise TokenExpiredError
                raise error(msg)

            return resp.json()
        except TokenExpiredError as e:
            try:
                self.token = sickrage.app.oidc_client.refresh_token(self.token['refresh_token'])
            except Exception:
                if os.path.exists(self.token_file):
                    os.remove(self.token_file)
            return self._request(method, url, **kwargs)
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
