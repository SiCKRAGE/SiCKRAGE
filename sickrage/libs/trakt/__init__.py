from __future__ import absolute_import, division, print_function

import logging

from six import add_metaclass
from trakt.client import TraktClient
from trakt.core.errors import ERRORS
from trakt.core.exceptions import RequestError, ClientError, ServerError
from trakt.helpers import has_attribute
from trakt.version import __version__  # NOQA

__all__ = (
    'Trakt',
    'RequestError',
    'ClientError',
    'ServerError',
    'ERRORS'
)


class TraktMeta(type):
    def __getattr__(self, name):
        if has_attribute(self, name):
            return super(TraktMeta, self).__getattribute__(name)

        if self.client is None:
            self.construct()

        return getattr(self.client, name)

    def __setattr__(self, name, value):
        if has_attribute(self, name):
            return super(TraktMeta, self).__setattr__(name, value)

        if self.client is None:
            self.construct()

        setattr(self.client, name, value)

    def __getitem__(self, key):
        if self.client is None:
            self.construct()

        return self.client[key]


@add_metaclass(TraktMeta)
class Trakt(object):
    client = None

    @classmethod
    def construct(cls):
        cls.client = TraktClient()


# Set default logging handler to avoid "No handler found" warnings.
try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
