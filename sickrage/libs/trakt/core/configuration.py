# flake8: noqa: E241

from trakt.core.context_collection import ContextCollection

DEFAULT_HTTP_RETRY = False
DEFAULT_HTTP_MAX_RETRIES = 3
DEFAULT_HTTP_RETRY_SLEEP = 5
DEFAULT_HTTP_TIMEOUT = (6.05, 24)


class ConfigurationManager(object):
    def __init__(self):
        self.defaults = Configuration(self)
        self.stack = ContextCollection([self.defaults])

        self.oauth = OAuthConfiguration(self)

    @property
    def current(self):
        return self.stack[-1]

    def app(self, name=None, version=None, date=None, id=None):
        return Configuration(self).app(name, version, date, id)

    def auth(self, login=None, token=None):
        return Configuration(self).auth(login, token)

    def client(self, id=None, secret=None):
        return Configuration(self).client(id, secret)

    def http(self, retry=DEFAULT_HTTP_RETRY, max_retries=DEFAULT_HTTP_MAX_RETRIES, retry_sleep=DEFAULT_HTTP_RETRY_SLEEP,
             timeout=DEFAULT_HTTP_TIMEOUT):

        return Configuration(self).http(retry, max_retries, retry_sleep, timeout)

    def get(self, key, default=None):
        for x in range(len(self.stack) - 1, -1, -1):
            value = self.stack[x].get(key)

            if value is not None:
                return value

        return default

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.current[key] = value


class Configuration(object):
    def __init__(self, manager):
        self.manager = manager

        self.data = {}

        self.oauth = OAuthConfiguration(self)

    def app(self, name=None, version=None, date=None, id=None):
        self.data['app.name'] = name
        self.data['app.version'] = version
        self.data['app.date'] = date
        self.data['app.id'] = id

        return self

    def auth(self, login=None, token=None):
        self.data['auth.login'] = login
        self.data['auth.token'] = token

        return self

    def client(self, id=None, secret=None):
        self.data['client.id'] = id
        self.data['client.secret'] = secret

        return self

    def http(self, retry=DEFAULT_HTTP_RETRY, max_retries=DEFAULT_HTTP_MAX_RETRIES, retry_sleep=DEFAULT_HTTP_RETRY_SLEEP,
             timeout=DEFAULT_HTTP_TIMEOUT):

        self.data['http.retry'] = retry
        self.data['http.max_retries'] = max_retries
        self.data['http.retry_sleep'] = retry_sleep

        self.data['http.timeout'] = timeout

        return self

    def get(self, key, default=None):
        return self.data.get(key, default)

    def __enter__(self):
        self.manager.stack.append(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        item = self.manager.stack.pop()

        assert item == self, 'Removed %r from stack, expecting %r' % (item, self)

        # Clear old context lists
        if len(self.manager.stack) == 1:
            self.manager.stack.clear()

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value


class OAuthConfiguration(object):
    def __init__(self, owner):
        self.owner = owner

    def __call__(self, token=None, refresh_token=None, created_at=None, expires_in=None, refresh=None, username=None):
        if type(self.owner) is ConfigurationManager:
            return Configuration(self.owner).oauth(token, refresh_token, created_at, expires_in, refresh)

        self.owner.data.update({
            'oauth.token':          token,
            'oauth.refresh_token':  refresh_token,

            'oauth.created_at':     created_at,
            'oauth.expires_in':     expires_in,

            'oauth.refresh':        refresh,
            'oauth.username':       username
        })

        return self.owner

    def clear(self):
        if type(self.owner) is ConfigurationManager:
            return Configuration(self.owner).oauth.clear()

        self.owner.data.update({
            'oauth.token':          None,
            'oauth.refresh_token':  None,

            'oauth.created_at':     None,
            'oauth.expires_in':     None
        })

        return self.owner

    def from_response(self, response=None, refresh=None, username=None):
        if type(self.owner) is ConfigurationManager:
            return Configuration(self.owner).oauth.from_response(
                response=response,
                refresh=refresh,
                username=username
            )

        if not response:
            raise ValueError('Invalid "response" parameter provided to oauth.from_response()')

        self.owner.data.update({
            'oauth.token':          response.get('access_token'),
            'oauth.refresh_token':  response.get('refresh_token'),

            'oauth.created_at':     response.get('created_at'),
            'oauth.expires_in':     response.get('expires_in'),

            'oauth.refresh':        refresh,
            'oauth.username':       username
        })

        return self.owner
