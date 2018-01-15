from __future__ import unicode_literals

from urlparse import urljoin

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

import sickrage
from sickrage.core.api.exceptions import unauthorized, error


class RefreshOAuth2Session(OAuth2Session):
    def __init__(self, *args, **kwargs):
        self.token_url = kwargs.pop('token_url')
        super(RefreshOAuth2Session, self).__init__(*args, **kwargs)

    def request(self, *args, **kwargs):
        resp = super(RefreshOAuth2Session, self).request(*args, **kwargs)
        if resp.status_code == 401:
            self.token = self.fetch_token(
                token_url=self.token_url,
                **self.auto_refresh_kwargs
            )
            self.token_updater(self.token)
            resp = super(RefreshOAuth2Session, self).request(*args, **kwargs)
        return resp


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
            self._session = RefreshOAuth2Session(
                client=BackendApplicationClient(client_id=self.credentials['client_id']),
                token=self.token,
                token_url=self.token_url,
                token_updater=self.token_updater
            )
        return self._session

    @property
    def token(self):
        if self._token is None:
            self._token = RefreshOAuth2Session(
                client=BackendApplicationClient(client_id=self.credentials['client_id']),
                token_url=self.token_url,
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
            if resp.status_code == 401:
                raise unauthorized(resp.json()['message'])
            elif resp.status_code >= 400:
                raise error(resp.json()['message'])
        except Exception as e:
            raise error(e.message)

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
