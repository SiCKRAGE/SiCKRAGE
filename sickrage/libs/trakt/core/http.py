from __future__ import absolute_import, division, print_function

import calendar
import datetime
import logging
import socket
import time
from threading import RLock

import requests
from requests.adapters import DEFAULT_POOLBLOCK, HTTPAdapter

from trakt.core.configuration import DEFAULT_HTTP_RETRY, DEFAULT_HTTP_MAX_RETRIES, DEFAULT_HTTP_TIMEOUT, \
    DEFAULT_HTTP_RETRY_SLEEP
from trakt.core.context_stack import ContextStack
from trakt.core.helpers import synchronized
from trakt.core.keylock import KeyLock
from trakt.core.request import TraktRequest

try:
    import ssl
except ImportError:
    ssl = None

log = logging.getLogger(__name__)


class HttpClient(object):
    def __init__(self, client, adapter_kwargs=None, keep_alive=True):
        self.client = client

        self.adapter_kwargs = adapter_kwargs or {}
        self.keep_alive = keep_alive

        # Build client
        self.configuration = ContextStack()
        self.session = None

        self._proxies = {}
        self._ssl_version = None

        self._oauth_refreshing = KeyLock()
        self._oauth_validate_lock = RLock()

        # Build requests session
        self.rebuild()

    @property
    def proxies(self):
        if self.session and self.session.proxies:
            return self.session.proxies

        return self._proxies

    @proxies.setter
    def proxies(self, proxies):
        if self.session:
            self.session.proxies = proxies

        self._proxies = proxies

    @property
    def ssl_version(self):
        return self._ssl_version

    @ssl_version.setter
    def ssl_version(self, version):
        self._ssl_version = version

        # Rebuild session (to apply ssl version change)
        self.rebuild()

    def configure(self, path=None):
        self.configuration.push(base_path=path)

        return self

    def request(self, method, path=None, params=None, data=None, query=None, authenticated=False,
                validate_token=True, **kwargs):

        # Retrieve configuration
        ctx = self.configuration.pop()

        # Build request
        request = TraktRequest(
            self.client,
            method=method,

            path=self._build_path(ctx, path),
            params=params,

            data=data,
            query=query,

            authenticated=authenticated,
            **kwargs
        )

        # Validate authentication details (OAuth)
        if authenticated and validate_token and not self.validate():
            return None

        # Prepare request
        prepared = request.prepare()

        if not self.keep_alive:
            prepared.headers['Connection'] = 'close'

        # Send request
        return self.send(prepared)

    def send(self, request):
        # Retrieve http configuration
        retry = self.client.configuration.get('http.retry', DEFAULT_HTTP_RETRY)
        max_retries = self.client.configuration.get('http.max_retries', DEFAULT_HTTP_MAX_RETRIES)
        retry_sleep = self.client.configuration.get('http.retry_sleep', DEFAULT_HTTP_RETRY_SLEEP)
        timeout = self.client.configuration.get('http.timeout', DEFAULT_HTTP_TIMEOUT)

        # Send request
        response = None

        for i in range(max_retries + 1):
            if i > 0:
                log.warn('Retry # %s', i)

            # Send request
            try:
                response = self.session.send(request, timeout=timeout)
            except socket.gaierror as e:
                code, __ = e

                if code != 8:
                    raise e

                log.warn('Encountered socket.gaierror (code: 8)')

                response = self.rebuild().send(request, timeout=timeout)

            # Retry requests on errors >= 500 (when enabled)
            if not retry or response.status_code < 500:
                break

            log.warn('Continue retry since status is %s, waiting %s seconds', response.status_code, retry_sleep)
            time.sleep(retry_sleep)

        return response

    def delete(self, path=None, params=None, data=None, **kwargs):
        return self.request('DELETE', path, params, data, **kwargs)

    def get(self, path=None, params=None, data=None, **kwargs):
        return self.request('GET', path, params, data, **kwargs)

    def post(self, path=None, params=None, data=None, **kwargs):
        return self.request('POST', path, params, data, **kwargs)

    def put(self, path=None, params=None, data=None, **kwargs):
        return self.request('PUT', path, params, data, **kwargs)

    def rebuild(self):
        if self.session:
            log.info('Rebuilding session and connection pools...')

        # Build the connection pool
        self.session = requests.Session()
        self.session.proxies = self.proxies

        # Mount adapters
        self.session.mount('http://', HTTPAdapter(**self.adapter_kwargs))
        self.session.mount('https://', HTTPSAdapter(ssl_version=self._ssl_version, **self.adapter_kwargs))

        return self.session

    def validate(self):
        config = self.client.configuration

        # xAuth
        if config['auth.login'] and config['auth.token']:
            return True

        # OAuth
        if config['oauth.token']:
            # Validate OAuth token, refresh if needed
            return self._validate_oauth()

        return False

    def _build_path(self, ctx, path):
        if not ctx:
            # No context available
            return path

        if ctx.base_path and path:
            # Prepend `base_path` to relative `path`s
            if not path.startswith('/'):
                path = ctx.base_path + '/' + path
        elif ctx.base_path:
            # Set path to `base_path
            path = ctx.base_path

        return path

    @synchronized(lambda self: self._oauth_validate_lock)
    def _validate_oauth(self):
        config = self.client.configuration

        # Ensure token expiry is available
        if config['oauth.created_at'] is None or config['oauth.expires_in'] is None:
            log.debug('OAuth - Missing "created_at" or "expires_in" parameters, '
                      'unable to determine if the current token is still valid')
            return True

        # Calculate expiry
        current = calendar.timegm(datetime.datetime.utcnow().utctimetuple())
        expires_at = config['oauth.created_at'] + config['oauth.expires_in'] - (48 * 60 * 60)

        if current < expires_at:
            return True

        if not config['oauth.refresh']:
            log.warn('OAuth - Unable to refresh expired token (token refreshing hasn\'t been enabled)')
            return False

        if not config['oauth.refresh_token']:
            log.warn('OAuth - Unable to refresh expired token ("refresh_token" parameter hasn\'t been defined)')
            return False

        # Retrieve username
        username = config['oauth.username']

        if not username:
            log.info('OAuth - Current username is not available ("username" parameter hasn\'t been defined)')

        # Acquire refreshing lock
        if not self._oauth_refreshing[username].acquire(False):
            log.warn('OAuth - Token is already being refreshed for %r', username)
            return False

        log.info('OAuth - Token has expired, refreshing token...')

        # Refresh token
        try:
            if not self._refresh_oauth():
                return False

            log.info('OAuth - Token has been refreshed')
            return True
        finally:
            # Release refreshing lock
            self._oauth_refreshing[username].release()

    def _refresh_oauth(self):
        config = self.client.configuration

        # Refresh token
        response = self.client['oauth'].token_refresh(
            config['oauth.refresh_token'], 'urn:ietf:wg:oauth:2.0:oob',
            parse=False
        )

        if response is None:
            log.warn('OAuth - Unable to refresh expired token (no response returned)')
            return False

        if response.status_code < 200 or response.status_code >= 300:
            # Clear current configuration
            config.current.oauth.clear()

            # Handle refresh rejection
            if response.status_code == 401:
                log.warn('OAuth - Unable to refresh expired token (rejected)')

                # Fire rejected event
                self.client.emit('oauth.refresh.rejected', config['oauth.username'])
                return False

            # Unknown error returned
            log.warn('OAuth - Unable to refresh expired token (code: %r)', response.status_code)
            return False

        # Retrieve authorization parameters from response
        authorization = response.json()

        # Update current configuration
        config.current.oauth.from_response(
            authorization,
            refresh=config['oauth.refresh'],
            username=config['oauth.username']
        )

        # Fire refresh event
        self.client.emit('oauth.refresh', config['oauth.username'], authorization)

        # Fire legacy refresh event
        self.client.emit('oauth.token_refreshed', authorization)
        return True


class HTTPSAdapter(HTTPAdapter):
    def __init__(self, ssl_version=None, *args, **kwargs):
        self._ssl_version = ssl_version

        super(HTTPSAdapter, self).__init__(*args, **kwargs)

    def init_poolmanager(self, connections, maxsize, block=DEFAULT_POOLBLOCK, **pool_kwargs):
        pool_kwargs['ssl_version'] = self._ssl_version

        return super(HTTPSAdapter, self).init_poolmanager(
            connections, maxsize, block,
            **pool_kwargs
        )
