from __future__ import unicode_literals

from urlparse import urljoin

from oauthlib.oauth2 import BackendApplicationClient, TokenExpiredError
from requests_oauthlib import OAuth2Session

import sickrage
from sickrage.core.api.exceptions import unauthorized, error


class CustomBackendApplicationClient(BackendApplicationClient):
    def prepare_refresh_body(self, body='', refresh_token=None, scope=None, **kwargs):
        return super(CustomBackendApplicationClient, self).prepare_refresh_body(boby=body, scope=scope, **kwargs)


class API(object):
    def __init__(self, client_id=None, client_secret=None):
        self.api_url = 'https://api.sickrage.ca/'
        self.token_url = urljoin(self.api_url, 'oauth/v2/token')
        self._client_id = client_id
        self._client_secret = client_secret
        self._session = None
        self._token = None

    @property
    def credentials(self):
        return {
            'client_id': self._client_id or sickrage.app.config.api_client_id,
            'client_secret': self._client_secret or sickrage.app.config.api_client_secret
        }

    @property
    def session(self):
        if self._session is None:
            self._session = OAuth2Session(
                client=CustomBackendApplicationClient(client_id=self.credentials['client_id']),
                token=self.token,
                token_updater=self.token_updater,
                auto_refresh_url=self.token_url,
                auto_refresh_kwargs=self.credentials
            )
        return self._session

    @property
    def token(self):
        if self._token is None:
            self._token = OAuth2Session(
                client=CustomBackendApplicationClient(client_id=self.credentials['client_id'])
            ).fetch_token(
                token_url=self.token_url,
                timeout=30,
                **self.credentials
            )
        return self._token

    def token_updater(self, token):
        self._token = token

    def _request(self, method, url, **kwargs):
        if not sickrage.app.config.enable_api:
            return

        try:
            resp = self.session.request(method, urljoin(self.api_url, url), timeout=30, **kwargs)
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

    def add_provider_cache_result(self, data):
        self._request('POST', 'v1/providers/cache/results', json=data)

    def get_provider_cache_results(self, provider, indexerid=None):
        query = ('v1/providers/cache/results/{}'.format(provider),
                 'v1/providers/cache/results/{}/indexerids/{}'.format(provider, indexerid))[indexerid is not None]

        return self._request('GET', query)

    def get_torrent_cache_results(self, hash=None):
        query = ('v1/torrents/cache/results',
                 'v1/torrents/cache/results/{}'.format(hash))[hash is not None]

        return self._request('GET', query)

    def add_torrent_cache_result(self, url):
        self._request('POST', 'v1/torrents/cache/results', data=dict({'url': url}))

    def search_by_imdb_title(self, title):
        query = 'v1/imdb/search_by_title/{}'.format(title)

        return self._request('GET', query)

    def search_by_imdb_id(self, id):
        query = 'v1/imdb/search_by_id/{}'.format(id)

        return self._request('GET', query)
