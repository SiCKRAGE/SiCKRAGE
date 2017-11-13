from __future__ import unicode_literals

import functools
import json
from urlparse import urljoin

import sickrage
from sickrage.core.api.exceptions import unauthorized, error


def login_required(f):
    @functools.wraps(f)
    def wrapper(obj, *args, **kwargs):
        if not obj.logged_in:
            obj.login()

        try:
            return f(obj, *args, **kwargs)
        except unauthorized:
            obj.login(True)
            return f(obj, *args, **kwargs)

    return wrapper


class API(object):
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        self.token = None
        self.refresh_token = None
        self.login()

    def logout(self):
        self.token = self.refresh_token = None

    @property
    def logged_in(self):
        return self.token is not None

    def login(self, refresh=False):
        try:
            url = 'login'
            params = {'username': self.username or sickrage.app.config.api_username,
                      'password': self.password or sickrage.app.config.api_password}

            if refresh and self.refresh_token:
                url = 'auth/refresh'
                params = {'refresh_token': self.refresh_token}

            resp = self._request('POST', url, params=params)

            self.token = resp['access_token']
            self.refresh_token = resp['refresh_token']
        except Exception as e:
            self.logout()

    def _request(self, method, url, **kwargs):
        if not sickrage.app.config.enable_api:
            return

        headers = {'Content-type': 'application/json'}
        if self.token:
            headers['authorization'] = 'Bearer {}'.format(self.token)

        url = urljoin(sickrage.app.api_url, url)

        try:
            resp = sickrage.app.wsession.request(method, url, headers=headers, timeout=30, **kwargs)
        except Exception as e:
            raise error(e.message)

        # handle requests exceptions
        if resp.status_code == 401:
            raise unauthorized(resp.json()['message'])
        elif resp.status_code >= 400:
            raise error(resp.json()['message'])

        return resp.json()

    @login_required
    def user_profile(self):
        return self._request('GET', 'users/me')

    @login_required
    def add_cache_result(self, data):
        self._request('POST', 'providers/cache/results', data=json.dumps(data))

    @login_required
    def get_cache_results(self, provider, indexerid=None):
        query = ('providers/cache/results/{}'.format(provider),
                 'providers/cache/results/{}/indexerids/{}'.format(provider, indexerid))[indexerid is not None]
        return self._request('GET', query)
