from __future__ import unicode_literals

import json
import os
from urlparse import urljoin

from oauthlib.oauth2 import LegacyApplicationClient, MissingTokenError
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
            'client_id': 1,
            'client_secret': 'NmINyDwMfguMmbEMTSezHxaU5hTeUz12fk5RC9hk',
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
            try:
                if not os.path.isfile(self.token_file):
                    oauth = OAuth2Session(client=LegacyApplicationClient(client_id=self.credentials['client_id']))
                    self._token = oauth.fetch_token(token_url=self.token_url,
                                                    scope=['read-cache', 'write-cache'],
                                                    timeout=30,
                                                    **self.credentials)
                    self._token_updater(self._token)
                else:
                    with open(self.token_file) as infile:
                        self._token = json.load(infile)
            except MissingTokenError:
                self._token = ""
        return self._token

    def _token_updater(self, token):
        with open(self.token_file, 'w') as outfile:
            json.dump(token, outfile)

    def _request(self, method, url, **kwargs):
        if not sickrage.app.config.enable_api:
            return

        try:
            resp = self.session.request(method, urljoin(self.api_url, url), timeout=30, **kwargs)
            if resp.status_code == 401:
                raise unauthorized(resp.json()['message'])
            elif resp.status_code >= 400:
                raise error(resp.json()['message'])
        except Exception as e:
            raise error(str(e))

        return resp.json()

    def user_profile(self):
        return self._request('GET', 'user')

    def add_provider_cache_result(self, data):
        self._request('POST', 'v1/cache/providers', json=data)

    def get_provider_cache_results(self, provider, indexerid, season, episode):
        query = 'v1/cache/providers/{}/indexerids/{}/seasons/()/episodes/()'.format(provider, indexerid, season,
                                                                                    episode)
        return self._request('GET', query)

    def get_torrent_cache_results(self, hash):
        query = 'v1/cache/torrents/{}'.format(hash)
        return self._request('GET', query)

    def add_torrent_cache_result(self, url):
        self._request('POST', 'v1/cache/torrents', data=dict({'url': url}))

    def search_by_imdb_title(self, title):
        query = 'v1/imdb/search-by-title/{}'.format(title)
        return self._request('GET', query)

    def search_by_imdb_id(self, id):
        query = 'v1/imdb/search-by-id/{}'.format(id)
        return self._request('GET', query)

    def clear_drive_app_data(self):
        query = 'v1/drive/appdata/clear'
        return self._request('GET', query)

    def upload_drive_app_data_file(self, name, file):
        query = 'v1/drive/appdata/upload'
        return self._request('POST', query)

    def download_drive_app_data(self):
        query = 'v1/drive/appdata/download'
        return self._request('GET', query)
