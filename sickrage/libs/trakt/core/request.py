from __future__ import absolute_import, division, print_function

import json
from urllib.parse import urlencode

from requests import Request


class TraktRequest(object):
    def __init__(self, client, **kwargs):
        self.client = client
        self.configuration = client.configuration
        self.kwargs = kwargs

        self.request = None

        # Parsed Attributes
        self.path = None
        self.params = None
        self.query = None

        self.data = None
        self.method = None

    def prepare(self):
        self.request = Request()

        self.transform_parameters()
        self.request.url = self.construct_url()

        self.request.method = self.transform_method()
        self.request.headers = self.transform_headers()

        data = self.transform_data()

        if data:
            self.request.data = json.dumps(data)

        return self.request.prepare()

    def transform_parameters(self):
        # Transform `path`
        self.path = self.kwargs.get('path')

        if not self.path.startswith('/'):
            self.path = '/' + self.path

        if self.path.endswith('/'):
            self.path = self.path[:-1]

        # Transform `params` into list
        self.params = self.kwargs.get('params') or []

        if isinstance(self.params, str):
            self.params = [self.params]

        # Transform `query`
        self.query = self.kwargs.get('query') or {}

    def transform_method(self):
        self.method = self.kwargs.get('method')

        # Pick `method` (if not provided)
        if not self.method:
            self.method = 'POST' if self.data else 'GET'

        return self.method

    def transform_headers(self):
        headers = self.kwargs.get('headers') or {}
        headers['Content-Type'] = 'application/json'

        headers['trakt-api-version'] = '2'

        # API Key / Client ID
        if self.client.configuration['client.id']:
            headers['trakt-api-key'] = self.client.configuration['client.id']

        # xAuth
        if self.configuration['auth.login'] and self.configuration['auth.token']:
            headers['trakt-user-login'] = self.configuration['auth.login']
            headers['trakt-user-token'] = self.configuration['auth.token']

        # OAuth
        if self.configuration['oauth.token']:
            headers['Authorization'] = 'Bearer %s' % self.configuration['oauth.token']

        # User-Agent
        if self.configuration['app.name'] and self.configuration['app.version']:
            headers['User-Agent'] = '%s (%s)' % (self.configuration['app.name'], self.configuration['app.version'])
        elif self.configuration['app.name']:
            headers['User-Agent'] = self.configuration['app.name']
        else:
            headers['User-Agent'] = 'trakt.py (%s)' % self.client.version

        return headers

    def transform_data(self):
        return self.kwargs.get('data') or None

    def construct_url(self):
        """Construct a full trakt request URI, with `params` and `query`."""
        path = [self.path]
        path.extend(self.params)

        # Build URL
        url = self.client.base_url + '/'.join(
            str(value) for value in path
            if value
        )

        # Append query parameters (if defined)
        query = self.encode_query(self.query)

        if query:
            url += '?' + query

        return url

    @classmethod
    def encode_query(cls, parameters):
        if not parameters:
            return ''

        return urlencode([
            (key, cls.encode_query_parameter(value))
            for key, value in parameters.items()
            if value is not None
        ])

    @classmethod
    def encode_query_parameter(cls, value):
        # Encode tuple into range string
        if isinstance(value, tuple):
            if len(value) != 2:
                raise ValueError('Invalid tuple parameter (expected 2-length tuple)')

            return '%s-%s' % value

        # Encode list into comma-separated string
        if isinstance(value, list):
            return ','.join([
                cls.encode_query_parameter(item)
                for item in value
            ])

        # Ensure values are strings
        return str(value)
