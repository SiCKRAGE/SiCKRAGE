import base64
import json
import os
import time
from urllib.parse import urljoin

from oauthlib.oauth2 import MissingTokenError, InvalidClientIdError, TokenExpiredError, InvalidGrantError
from requests_oauthlib import OAuth2Session

import sickrage
from sickrage.core.api.exceptions import unauthorized, error


class API(object):
    def __init__(self):
        self.api_url = 'https://api.sickrage.ca/api/v1/'
        self.client_id = sickrage.app.oidc_client._client_id
        self.client_secret = sickrage.app.oidc_client._client_secret
        self.token_url = sickrage.app.oidc_client.well_known['token_endpoint']
        self.token_file = os.path.abspath(os.path.join(sickrage.app.data_dir, 'token.json'))
        self.token_refreshed = False

    @property
    def session(self):
        return OAuth2Session(token=self.token)

    @property
    def token(self):
        if os.path.exists(self.token_file):
            with open(self.token_file, 'r') as fd:
                return json.load(fd)
        return {}

    @token.setter
    def token(self, value):
        with open(self.token_file, 'w') as fd:
            json.dump(value, fd)

    @property
    def userinfo(self):
        return self._request('GET', 'userinfo')

    def allowed_usernames(self):
        return self._request('GET', 'allowed-usernames')

    def download_privatekey(self):
        return self._request('GET', 'app/private-key')

    def upload_privatekey(self, privatekey):
        return self._request('POST', 'app/private-key', data=dict({'privatekey': privatekey}))

    def _request(self, method, url, **kwargs):
        try:
            resp = self.session.request(method, urljoin(self.api_url, url), timeout=30,
                                        hooks={'response': self.throttle_hook}, **kwargs)

            if resp.status_code == 401:
                if not self.token_refreshed:
                    raise TokenExpiredError
                if 'error' in resp.json():
                    raise error(resp.json()['error'])
            elif resp.status_code >= 400:
                if 'error' in resp.json():
                    raise error(resp.json()['error'])

            return resp.json()
        except TokenExpiredError:
            self.refresh_token()
            return self._request(method, url, **kwargs)
        except (InvalidClientIdError, MissingTokenError) as e:
            sickrage.app.log.warning("SiCKRAGE token issue, please try logging out and back in again to the web-ui")

    def refresh_token(self):
        self.token_refreshed = True

        extras = {'client_id': self.client_id, 'client_secret': self.client_secret}

        try:
            self.token = self.session.refresh_token(self.token_url, **extras)
        except InvalidGrantError as e:
            self.token = ''

        return self.token

    @staticmethod
    def throttle_hook(response, **kwargs):
        ratelimited = "X-RateLimit-Remaining" in response.headers

        if ratelimited:
            remaining = int(response.headers["X-RateLimit-Remaining"])
            if remaining == 1:
                sickrage.app.log.debug("Throttling SiCKRAGE API Calls... Sleeping for 60 secs...\n")
                time.sleep(60)
