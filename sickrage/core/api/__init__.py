import time
from urllib.parse import urljoin

import requests
import requests.exceptions
from keycloak.exceptions import KeycloakClientError
from oauthlib.oauth2 import MissingTokenError, InvalidClientIdError, TokenExpiredError, InvalidGrantError, OAuth2Token
from requests_oauthlib import OAuth2Session
from sqlalchemy import orm

import sickrage
from sickrage.core.api.exceptions import APIError
from sickrage.core.databases.cache import CacheDB


class API(object):
    def __init__(self):
        self.name = 'SR-API'
        self.api_base = 'https://www.sickrage.ca/api/'
        self.api_version = 'v3'
        self.client_id = sickrage.app.oidc_client_id
        self.client_secret = sickrage.app.oidc_client_secret
        self._session = None

    @property
    def imdb(self):
        return self.IMDbAPI(self)

    @property
    def account(self):
        return self.AccountAPI(self)

    @property
    def provider(self):
        return self.ProviderAPI(self)

    @property
    def announcement(self):
        return self.AnnouncementsAPI(self)

    @property
    def google(self):
        return self.GoogleDriveAPI(self)

    @property
    def torrent_cache(self):
        return self.TorrentCacheAPI(self)

    @property
    def provider_cache(self):
        return self.ProviderCacheAPI(self)

    @property
    def session(self):
        extra = {
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        if not self._session:
            self._session = OAuth2Session(token=self.token, auto_refresh_kwargs=extra, auto_refresh_url=self.token_url, token_updater=self.token_updater)

        return self._session

    @property
    def token(self):
        session = sickrage.app.cache_db.session()
        try:
            token = session.query(CacheDB.OAuth2Token).one()
            return token.as_dict()
        except orm.exc.NoResultFound:
            return {}

    @token.setter
    def token(self, value):
        new_token = {
            'access_token': value.get('access_token'),
            'refresh_token': value.get('refresh_token'),
            'expires_in': value.get('expires_in'),
            'expires_at': value.get('expires_at', int(time.time() + value.get('expires_in'))),
            'scope': value.scope if isinstance(value, OAuth2Token) else value.get('scope')
        }

        session = sickrage.app.cache_db.session()

        try:
            token = session.query(CacheDB.OAuth2Token).one()
            token.update(**new_token)
        except orm.exc.NoResultFound:
            session.add(CacheDB.OAuth2Token(**new_token))
        finally:
            session.commit()

        self._session = None

    @token.deleter
    def token(self):
        session = sickrage.app.cache_db.session()
        session.query(CacheDB.OAuth2Token).delete()
        session.commit()

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
        return self.request('GET', 'userinfo')

    def token_updater(self, value):
        self.token = value

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
        return self.request('GET', 'allowed-usernames')

    def download_privatekey(self):
        return self.request('GET', 'account/private-key')

    def upload_privatekey(self, privatekey):
        return self.request('POST', 'account/private-key', data=dict({'privatekey': privatekey}))

    def request(self, method, url, timeout=30, **kwargs):
        latest_exception = None

        if not self.token:
            return

        for i in range(3):
            try:
                if not self.health:
                    latest_exception = "SiCKRAGE backend API is currently unreachable ..."
                    continue

                resp = self.session.request(method, urljoin(self.api_base, "/".join([self.api_version, url])), timeout=timeout,
                                            hooks={'response': self.throttle_hook}, **kwargs)
                resp.raise_for_status()
                if resp.status_code == 204:
                    return

                try:
                    return resp.json()
                except ValueError:
                    return resp.content
            except TokenExpiredError:
                self.refresh_token()
            except (InvalidClientIdError, MissingTokenError, InvalidGrantError) as e:
                latest_exception = "Invalid token error, please re-authenticate by logging out then logging back in from web-ui"
                break
            except requests.exceptions.ReadTimeout:
                timeout += timeout
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code
                error_message = e.response.text
                if status_code == 403 and "login-pf-page" in error_message:
                    self.refresh_token()
                    continue
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

    class AccountAPI:
        def __init__(self, api):
            self.api = api

        def register_app_id(self):
            return self.api.request('GET', 'account/app-id')

        def unregister_app_id(self, app_id):
            data = {
                'app-id': app_id
            }

            return self.api.request('DELETE', 'account/app-id', data=data)

        def upload_config(self, app_id, pkey_sig, config):
            data = {
                'app-id': app_id,
                'pkey-sig': pkey_sig,
                'config': config
            }
            return self.api.request('POST', 'account/config', data=data)

        def download_config(self, pkey_sig):
            data = {
                'pkey-sig': pkey_sig
            }

            return self.api.request('GET', 'account/config', json=data)['config']

    class AnnouncementsAPI:
        def __init__(self, api):
            self.api = api

        def get_announcements(self):
            return self.api.request('GET', 'announcements')

    class ProviderAPI:
        def __init__(self, api):
            self.api = api

        def get_urls(self, provider):
            query = 'provider/{}/urls'.format(provider)
            return self.api.request('GET', query)

        def get_status(self, provider):
            query = 'provider/{}/status'.format(provider)
            return self.api.request('GET', query)

    class ProviderCacheAPI:
        def __init__(self, api):
            self.api = api

        def get(self, provider, series_id, season, episode):
            query = 'cache/provider/{}/series-id/{}/season/{}/episode/{}'.format(provider, series_id, season, episode)
            return self.api.request('GET', query)

        def add(self, data):
            return self.api.request('POST', 'cache/provider', json=data)

    class TorrentCacheAPI:
        def __init__(self, api):
            self.api = api

        def get(self, hash):
            query = 'cache/torrent/{}'.format(hash)
            return self.api.request('GET', query)

        def add(self, url):
            return self.api.request('POST', 'cache/torrent', json={'url': url})

    class IMDbAPI:
        def __init__(self, api):
            self.api = api

        def search_by_imdb_title(self, title):
            query = 'imdb/search-by-title/{}'.format(title)
            return self.api.request('GET', query)

        def search_by_imdb_id(self, id):
            query = 'imdb/search-by-id/{}'.format(id)
            return self.api.request('GET', query)

    class GoogleDriveAPI:
        def __init__(self, api):
            self.api = api

        def is_connected(self):
            query = 'google-drive/is-connected'
            return self.api.request('GET', query)

        def upload(self, file, folder):
            query = 'google-drive/upload'
            return self.api.request('POST', query, files={'file': open(file, 'rb')}, params={'folder': folder})

        def download(self, id):
            query = 'google-drive/download/{id}'.format(id=id)
            return self.api.request('GET', query)

        def delete(self, id):
            query = 'google-drive/delete/{id}'.format(id=id)
            return self.api.request('GET', query)

        def search_files(self, id, term):
            query = 'google-drive/search-files/{id}/{term}'.format(id=id, term=term)
            return self.api.request('GET', query)

        def list_files(self, id):
            query = 'google-drive/list-files/{id}'.format(id=id)
            return self.api.request('GET', query)

        def clear_folder(self, id):
            query = 'google-drive/clear-folder/{id}'.format(id=id)
            return self.api.request('GET', query)
