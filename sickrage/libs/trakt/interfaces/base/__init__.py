from __future__ import absolute_import, division, print_function

import functools
import logging
import warnings

from trakt.core.errors import log_request_error
from trakt.core.exceptions import RequestFailedError, ServerError, ClientError
from trakt.core.helpers import try_convert
from trakt.core.pagination import PaginationIterator
from trakt.helpers import setdefault

log = logging.getLogger(__name__)


def authenticated(func):
    @functools.wraps(func)
    def wrap(*args, **kwargs):
        if 'authenticated' not in kwargs:
            kwargs['authenticated'] = True

        return func(*args, **kwargs)

    return wrap


def application(func):
    @functools.wraps(func)
    def wrap(*args, **kwargs):
        if args and isinstance(args[0], Interface):
            interface = args[0]

            setdefault(kwargs, {
                'app_version': interface.client.configuration['app.version'],
                'app_date': interface.client.configuration['app.date']
            }, lambda key, value: value)

        return func(*args, **kwargs)

    return wrap


class Interface(object):
    path = None

    def __init__(self, client):
        self.client = client

    def __getitem__(self, name):
        if hasattr(self, name):
            return getattr(self, name)

        raise ValueError('Unknown action "%s" on %s' % (name, self))

    @property
    def http(self):
        if not self.client:
            return None

        return self.client.http.configure(self.path)

    def get_data(self, response, exceptions=False, pagination=False, parse=True):
        if response is None:
            if exceptions:
                raise RequestFailedError('No response available')

            log.warn('Request failed (no response returned)')
            return None

        # Return response, if parse=False
        if not parse:
            return response

        # Check status code, log any errors
        error = False

        if response.status_code < 200 or response.status_code >= 300:
            log_request_error(log, response)

            # Raise an exception (if enabled)
            if exceptions:
                if response.status_code >= 500:
                    raise ServerError(response)
                else:
                    raise ClientError(response)

            # Set error flag
            error = True

        # Return `None` if we encountered an error, return response data
        if error:
            return None

        # Check for pagination response
        page_count = try_convert(response.headers.get('x-pagination-page-count'), int)

        if page_count and page_count > 1:
            if pagination:
                return PaginationIterator(self.client, response)

            warnings.warn(
                'Unhandled pagination response, more pages can be returned with `pagination=True`',
                stacklevel=3
            )

        # Parse response, return data
        content_type = response.headers.get('content-type')

        if content_type and content_type.startswith('application/json'):
            # Try parse json response
            try:
                data = response.json()
            except Exception as e:
                log.warning('unable to parse JSON response: %s', e)
                return None
        else:
            log.debug('response returned content-type: %r, falling back to raw data', content_type)

            # Fallback to raw content
            data = response.content

        return data


class InterfaceProxy(object):
    def __init__(self, interface, args):
        self.interface = interface
        self.args = list(args)

    def __getattr__(self, name):
        value = getattr(self.interface, name)

        if not callable(value):
            return value

        @functools.wraps(value)
        def wrap(*args, **kwargs):
            args = self.args + list(args)

            return value(*args, **kwargs)

        return wrap
