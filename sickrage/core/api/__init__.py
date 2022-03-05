import collections
import errno
import time
import traceback
from urllib.parse import urljoin

import oauthlib.oauth2
import requests
import requests.exceptions
from jose import ExpiredSignatureError
from keycloak.exceptions import KeycloakClientError
from requests_oauthlib import OAuth2Session

import sickrage
from sickrage.core.api.exceptions import APIError


class API(object):
    def __init__(self):
        self.name = 'SR-API'
        self.api_base = 'https://www.sickrage.ca/api/'
        self.api_version = 'v6'
        self._token = {}

    @property
    def imdb(self):
        return self.IMDbAPI(self)

    @property
    def server(self):
        return self.ServerAPI(self)

    @property
    def search_provider(self):
        return self.SearchProviderAPI(self)

    @property
    def series_provider(self):
        return self.SeriesProviderAPI(self)

    @property
    def announcement(self):
        return self.AnnouncementsAPI(self)

    @property
    def google(self):
        return self.GoogleDriveAPI(self)

    @property
    def torrent(self):
        return self.TorrentAPI(self)

    @property
    def scene_exceptions(self):
        return self.SceneExceptions(self)

    @property
    def alexa(self):
        return self.AlexaAPI(self)

    @property
    def session(self):
        if not self.token_url:
            return

        return OAuth2Session(
            token=self.token,
            auto_refresh_kwargs={'client_id': sickrage.app.auth_server.client_id},
            auto_refresh_url=self.token_url,
            token_updater=self.token_updater
        )

    @property
    def token(self):
        if not self._token:
            self.login()
        elif self.token_time_remaining < (int(self._token.get('expires_in')) / 2):
            self.refresh_token()

        return self._token

    @property
    def token_expiration(self):
        try:
            if not self._token:
                return time.time()

            certs = sickrage.app.auth_server.certs()
            if not certs:
                return time.time()

            decoded_token = sickrage.app.auth_server.decode_token(self._token.get('access_token'), certs)
            return decoded_token.get('exp', time.time())
        except ExpiredSignatureError:
            return time.time()

    @property
    def token_time_remaining(self):
        return max(self.token_expiration - time.time(), 0)

    @property
    def token_is_expired(self):
        return self.token_expiration <= time.time()

    @property
    def token_url(self):
        return sickrage.app.auth_server.get_url('token_endpoint')

    @property
    def health(self):
        for i in range(3):
            try:
                health = requests.get(urljoin(self.api_base, "health"), verify=False, timeout=30).ok
            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
                pass
            else:
                break
        else:
            health = False

        if not health:
            sickrage.app.log.debug("SiCKRAGE API is currently unreachable")
            return False

        return True

    @property
    def userinfo(self):
        return self.request('GET', 'userinfo')

    def token_updater(self, value):
        self._token = value

    def login(self):
        if not self.health:
            return False

        if not self.token_url:
            return False

        session = requests.session()

        data = {
            'client_id': sickrage.app.auth_server.client_id,
            'grant_type': 'password',
            'apikey': sickrage.app.config.general.sso_api_key
        }

        try:
            resp = session.post(self.token_url, data)
            resp.raise_for_status()
            self._token = resp.json()
        except requests.exceptions.RequestException:
            return False

        return True

    def logout(self):
        if self._token:
            try:
                sickrage.app.auth_server.logout(self._token.get('refresh_token'))
            except KeycloakClientError:
                pass

    def refresh_token(self):
        retries = 3

        for i in range(retries):
            try:
                if not self._token:
                    return self.login()

                self._token = sickrage.app.auth_server.refresh_token(self._token.get('refresh_token'))
            except KeycloakClientError:
                return self.login()
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                if i > retries:
                    return False
                time.sleep(0.2)
                continue

            return True

    def allowed_usernames(self):
        return self.request('GET', 'allowed-usernames')

    def download_privatekey(self):
        return self.request('GET', 'server/config/private-key')

    def upload_privatekey(self, privatekey):
        return self.request('POST', 'server/config/private-key', data=dict({'privatekey': privatekey}))

    def network_timezones(self):
        return self.request('GET', 'network-timezones')

    def request(self, method, url, timeout=120, **kwargs):
        if not self.session:
            return

        url = urljoin(self.api_base, "/".join([self.api_version, url]))

        for i in range(5):
            resp = None

            try:
                if not self.health:
                    if i > 3:
                        return None
                    continue

                resp = self.session.request(method, url, timeout=timeout, verify=False, hooks={'response': self.throttle_hook}, **kwargs)

                resp.raise_for_status()
                if resp.status_code == 204:
                    return resp.ok

                try:
                    return resp.json()
                except ValueError:
                    return resp.content
            except (oauthlib.oauth2.TokenExpiredError, oauthlib.oauth2.InvalidGrantError):
                self.refresh_token()
                time.sleep(1)
            except (oauthlib.oauth2.InvalidClientIdError, oauthlib.oauth2.MissingTokenError) as e:
                self.refresh_token()
                time.sleep(1)
            except requests.exceptions.ReadTimeout as e:
                if i > 3:
                    sickrage.app.log.debug(f'Error connecting to url {url} Error: {e}')
                    return resp or e.response

                timeout += timeout
                time.sleep(1)
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code
                error_message = e.response.text

                if status_code == 403 and "login-pf-page" in error_message:
                    self.refresh_token()
                    time.sleep(1)
                    continue

                if 'application/json' in e.response.headers.get('content-type', ''):
                    status_code = e.response.json().get('error', status_code)
                    error_message = e.response.json().get('message', error_message)
                    sickrage.app.log.debug(f'SiCKRAGE API response returned for url {url} Response: {error_message}, Code: {status_code}')
                else:
                    sickrage.app.log.debug(f'The response returned a non-200 response while requesting url {url} Error: {e!r}')

                return resp or e.response
            except requests.exceptions.ConnectionError as e:
                if i > 3:
                    sickrage.app.log.debug(f'Error connecting to url {url} Error: {e}')
                    return resp or e.response

                time.sleep(1)
            except requests.exceptions.RequestException as e:
                sickrage.app.log.debug(f'Error requesting url {url} Error: {e}')
                return resp or e.response
            except Exception as e:
                if (isinstance(e, collections.Iterable) and 'ECONNRESET' in e) or (getattr(e, 'errno', None) == errno.ECONNRESET):
                    sickrage.app.log.warning(f'Connection reset by peer accessing url {url} Error: {e}')
                else:
                    sickrage.app.log.info(f'Unknown exception in url {url} Error: {e}')
                    sickrage.app.log.debug(traceback.format_exc())

                return None

    @staticmethod
    def throttle_hook(response, **kwargs):
        if "X-RateLimit-Remaining" in response.headers:
            remaining = int(response.headers["X-RateLimit-Remaining"])
            if remaining == 1:
                sickrage.app.log.debug("Throttling SiCKRAGE API Calls... Sleeping for 60 secs...\n")
                time.sleep(60)

    class ServerAPI:
        def __init__(self, api):
            self.api = api

        def register_server(self, ip_addresses, web_protocol, web_port, web_root, server_version):
            data = {
                'ip-addresses': ip_addresses,
                'web-protocol': web_protocol,
                'web-port': web_port,
                'web-root': web_root,
                'server-version': server_version
            }

            return self.api.request('POST', 'server', data=data)

        def unregister_server(self, server_id):
            data = {
                'server-id': server_id
            }

            return self.api.request('DELETE', 'server', data=data)

        def update_server(self, server_id, ip_addresses, web_protocol, web_port, web_root, server_version):
            data = {
                'server-id': server_id,
                'ip-addresses': ip_addresses,
                'web-protocol': web_protocol,
                'web-port': web_port,
                'web-root': web_root,
                'server-version': server_version
            }

            return self.api.request('PUT', 'server', data=data)

        def get_status(self, server_id):
            return self.api.request('GET', f'server/{server_id}/status')

        def get_server_certificate(self, server_id):
            return self.api.request('GET', f'server/{server_id}/certificate')

        def declare_amqp_queue(self, server_id):
            return self.api.request('GET', f'server/{server_id}/declare-amqp-queue')

        def upload_config(self, server_id, pkey_sig, config):
            data = {
                'server-id': server_id,
                'pkey-sig': pkey_sig,
                'config': config
            }
            return self.api.request('POST', f'server/{server_id}/config', data=data)

        def download_config(self, server_id, pkey_sig):
            data = {
                'pkey-sig': pkey_sig
            }

            return self.api.request('GET', f'server/{server_id}/config', json=data)['config']

    class AnnouncementsAPI:
        def __init__(self, api):
            self.api = api

        def get_announcements(self):
            return self.api.request('GET', 'announcements')

    class SearchProviderAPI:
        def __init__(self, api):
            self.api = api

        def get_url(self, provider):
            endpoint = f'provider/{provider}/url'
            return self.api.request('GET', endpoint)

        def get_status(self, provider):
            endpoint = f'provider/{provider}/status'
            return self.api.request('GET', endpoint)

        def get_search_result(self, provider, series_id, season, episode):
            endpoint = f'provider/{provider}/series-id/{series_id}/season/{season}/episode/{episode}'
            return self.api.request('GET', endpoint)

        def add_search_result(self, provider, data):
            return self.api.request('POST', f'provider/{provider}', json=data)

    class TorrentAPI:
        def __init__(self, api):
            self.api = api

        def get_trackers(self):
            endpoint = f'torrent/trackers'
            return self.api.request('GET', endpoint)

        def get_torrent(self, hash):
            endpoint = f'torrent/{hash}'
            return self.api.request('GET', endpoint)

        def add_torrent(self, url):
            return self.api.request('POST', 'torrent', json={'url': url})

    class IMDbAPI:
        def __init__(self, api):
            self.api = api

        def search_by_imdb_title(self, title):
            endpoint = f'imdb/search-by-title/{title}'
            return self.api.request('GET', endpoint)

        def search_by_imdb_id(self, imdb_id):
            endpoint = f'imdb/search-by-id/{imdb_id}'
            return self.api.request('GET', endpoint)

    class GoogleDriveAPI:
        def __init__(self, api):
            self.api = api

        def is_connected(self):
            endpoint = 'google-drive/is-connected'
            return self.api.request('GET', endpoint)

        def upload(self, file, folder):
            endpoint = 'google-drive/upload'
            return self.api.request('POST', endpoint, files={'file': open(file, 'rb')}, params={'folder': folder})

        def download(self, id):
            endpoint = f'google-drive/download/{id}'
            return self.api.request('GET', endpoint)

        def delete(self, id):
            endpoint = f'google-drive/delete/{id}'
            return self.api.request('GET', endpoint)

        def search_files(self, id, term):
            endpoint = f'google-drive/search-files/{id}/{term}'
            return self.api.request('GET', endpoint)

        def list_files(self, id):
            endpoint = f'google-drive/list-files/{id}'
            return self.api.request('GET', endpoint)

        def clear_folder(self, id):
            endpoint = f'google-drive/clear-folder/{id}'
            return self.api.request('GET', endpoint)

    class SceneExceptions:
        def __init__(self, api):
            self.api = api

        def get(self, *args, **kwargs):
            endpoint = 'scene-exceptions'
            return self.api.request('GET', endpoint)

        def search_by_id(self, series_id):
            endpoint = f'scene-exceptions/search-by-id/{series_id}'
            return self.api.request('GET', endpoint)

    class AlexaAPI:
        def __init__(self, api):
            self.api = api

        def send_notification(self, message):
            return self.api.request('POST', 'alexa/notification', json={'message': message})

    class SeriesProviderAPI:
        def __init__(self, api):
            self.api = api

        def search(self, provider, query, language='eng'):
            endpoint = f'series-provider/{provider}/search/{query}/{language}'
            return self.api.request('GET', endpoint)

        def search_by_id(self, provider, remote_id, language='eng'):
            endpoint = f'series-provider/{provider}/search-by-id/{remote_id}/{language}'
            return self.api.request('GET', endpoint)

        def get_series_info(self, provider, series_id, language='eng'):
            endpoint = f'series-provider/{provider}/series/{series_id}/{language}'
            return self.api.request('GET', endpoint)

        def get_episodes_info(self, provider, series_id, season_type='default', language='eng'):
            endpoint = f'series-provider/{provider}/series/{series_id}/episodes/{season_type}/{language}'
            return self.api.request('GET', endpoint)

        def languages(self, provider):
            endpoint = f'series-provider/{provider}/languages'
            return self.api.request('GET', endpoint)

        def updates(self, provider, since):
            endpoint = f'series-provider/{provider}/updates/{since}'
            return self.api.request('GET', endpoint)
