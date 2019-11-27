import json
import os
import time
import requests.exceptions
from urllib.parse import urljoin

from oauthlib.oauth2 import MissingTokenError, InvalidClientIdError, TokenExpiredError, InvalidGrantError
from raven.utils.json import JSONDecodeError
from requests_oauthlib import OAuth2Session

import sickrage
from sickrage.core.api.exceptions import ApiUnauthorized, ApiError


class API(object):
    def __init__(self):
        self.name = 'SR-API'
        self.api_url = 'https://www.sickrage.ca/api/v2/'
        self.client_id = sickrage.app.oidc_client_id
        self.client_secret = sickrage.app.oidc_client_secret
        self.token_url = sickrage.app.oidc_client.well_known['token_endpoint']
        self.token_file = os.path.abspath(os.path.join(sickrage.app.data_dir, 'token.json'))
        self.token_refreshed = False

    @property
    def session(self):
        extra = {
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        def token_updater(value):
            self.token = value

        return OAuth2Session(token=self.token,
                             auto_refresh_kwargs=extra,
                             auto_refresh_url=self.token_url,
                             token_updater=token_updater)

    @property
    def token(self):
        token = {}

        if os.path.exists(self.token_file):
            with open(self.token_file, 'r') as fd:
                try:
                    token = json.load(fd)
                    if len(token) and not token.get('expires_at'):
                        token['expires_at'] = time.time() - 10
                except JSONDecodeError:
                    token = {}

        return token

    @token.setter
    def token(self, value):
        token = value.decode() if isinstance(value, bytes) else value
        if not isinstance(token, dict):
            token = {}

        if token.get('expires_in'):
            token['expires_at'] = int(time.time() + token['expires_in'])

        with open(self.token_file, 'w') as fd:
            json.dump(token, fd)

    @property
    def userinfo(self):
        return self._request('GET', 'userinfo')

    def allowed_usernames(self):
        return self._request('GET', 'allowed-usernames')

    def download_privatekey(self):
        return self._request('GET', 'account/private-key')

    def upload_privatekey(self, privatekey):
        return self._request('POST', 'account/private-key', data=dict({'privatekey': privatekey}))

    def _request(self, method, url, timeout=30, **kwargs):
        latest_exception = None

        for i in range(3):
            try:
                resp = self.session.request(method, urljoin(self.api_url, url), timeout=timeout, hooks={'response': self.throttle_hook}, **kwargs)
                if resp.status_code >= 400:
                    if 'error' in resp.json():
                        raise ApiError(resp.json()['error'])
                elif resp.status_code == 204:
                    return

                return resp.json()
            except (InvalidClientIdError, MissingTokenError) as e:
                latest_exception = "SiCKRAGE token issue, please try logging out and back in again to the web-ui"
            except requests.exceptions.ReadTimeout:
                timeout += timeout
            except requests.exceptions.RequestException as e:
                latest_exception = e

            time.sleep(1)

        if latest_exception:
            sickrage.app.log.warning('{!r}'.format(latest_exception))

    def exchange_token(self, token, scope='offline_access'):
        exchange = {'scope': scope, 'subject_token': token['access_token']}
        self.token = sickrage.app.oidc_client.token_exchange(**exchange)

    @staticmethod
    def throttle_hook(response, **kwargs):
        if "X-RateLimit-Remaining" in response.headers:
            remaining = int(response.headers["X-RateLimit-Remaining"])
            if remaining == 1:
                sickrage.app.log.debug("Throttling SiCKRAGE API Calls... Sleeping for 60 secs...\n")
                time.sleep(60)
