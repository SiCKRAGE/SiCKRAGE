import requests
import time
from urllib.parse import urljoin

import requests.exceptions
from keycloak.exceptions import KeycloakClientError
from oauthlib.oauth2 import MissingTokenError, InvalidClientIdError, TokenExpiredError, InvalidGrantError, OAuth2Token
from requests_oauthlib import OAuth2Session
from sqlalchemy import orm

import sickrage
from sickrage.core.api.exceptions import APIError, APITokenExpired
from sickrage.core.databases.cache import CacheDB


class API(object):
    def __init__(self):
        self.name = 'SR-API'
        self.api_base = 'https://www.sickrage.ca/api/'
        self.api_version = 'v3'
        self.client_id = sickrage.app.oidc_client_id
        self.client_secret = sickrage.app.oidc_client_secret

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
    @CacheDB.with_session
    def token(self, session=None):
        try:
            token = session.query(CacheDB.OAuth2Token).one()
            return token.as_dict()
        except orm.exc.NoResultFound:
            return {}

    @token.setter
    @CacheDB.with_session
    def token(self, value, session=None):
        new_token = {
            'access_token': value.get('access_token'),
            'refresh_token': value.get('refresh_token'),
            'expires_in': value.get('expires_in'),
            'expires_at': value.get('expires_at', int(time.time() + value.get('expires_in'))),
            'scope': value.scope if isinstance(value, OAuth2Token) else value.get('scope')
        }

        try:
            token = session.query(CacheDB.OAuth2Token).one()
            token.update(**new_token)
        except orm.exc.NoResultFound:
            session.add(CacheDB.OAuth2Token(**new_token))

    @token.deleter
    @CacheDB.with_session
    def token(self, session=None):
        session.query(CacheDB.OAuth2Token).delete()

    @property
    def token_url(self):
        try:
            return sickrage.app.oidc_client.well_known['token_endpoint']
        except KeycloakClientError:
            return "https://auth.sickrage.ca/auth/realms/sickrage/protocol/openid-connect/token"

    @property
    def health(self):
        return requests.get(urljoin(self.api_base, "oauth/health")).ok

    @property
    def userinfo(self):
        return self._request('GET', 'userinfo')

    def logout(self):
        sickrage.app.oidc_client.logout(self.token.get('refresh_token'))

    def refresh_token(self):
        extra = {
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        self.token = self.session.refresh_token(self.token_url, **extra)

    def exchange_token(self, token, scope='offline_access'):
        exchange = {'scope': scope, 'subject_token': token['access_token']}
        self.token = sickrage.app.oidc_client.token_exchange(**exchange)

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
                if not self.health:
                    latest_exception = "SiCKRAGE backend API is currently unreachable ..."
                    continue

                resp = self.session.request(method, urljoin(self.api_base, "/".join([self.api_version, url])), timeout=timeout, hooks={'response': self.throttle_hook}, **kwargs)
                resp.raise_for_status()
                if resp.status_code == 204:
                    return

                try:
                    return resp.json()
                except ValueError:
                    return resp.content
            except TokenExpiredError:
                self.refresh_token()
            except (InvalidClientIdError, MissingTokenError, InvalidGrantError):
                latest_exception = "Invalid token error, please re-authenticate by logging out then logging back in from web-ui"
                break
            except requests.exceptions.ReadTimeout:
                timeout += timeout
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code
                error_message = e.response.text
                if 'application/json' in e.response.headers.get('content-type', ''):
                    json_data = e.response.json().get('error', {})
                    status_code = json_data.get('status', status_code)
                    error_message = json_data.get('message', error_message)
                raise APIError(status=status_code, message=error_message)
            except requests.exceptions.RequestException as e:
                latest_exception = e

            time.sleep(1)

        if latest_exception:
            sickrage.app.log.warning('{!r}'.format(latest_exception))

    @staticmethod
    def throttle_hook(response, **kwargs):
        if "X-RateLimit-Remaining" in response.headers:
            remaining = int(response.headers["X-RateLimit-Remaining"])
            if remaining == 1:
                sickrage.app.log.debug("Throttling SiCKRAGE API Calls... Sleeping for 60 secs...\n")
                time.sleep(60)
