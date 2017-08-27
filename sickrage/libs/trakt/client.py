from __future__ import absolute_import, division, print_function

from trakt.core.configuration import ConfigurationManager
from trakt.core.emitter import Emitter
from trakt.core.http import HttpClient
from trakt.interfaces import construct_map
from trakt.interfaces.base import InterfaceProxy
from trakt.version import __version__


class TraktClient(Emitter):
    base_url = 'https://api.trakt.tv'
    version = __version__

    __interfaces = None

    def __init__(self, adapter_kwargs=None):
        # Set parameter defaults
        if adapter_kwargs is None:
            adapter_kwargs = {}

        adapter_kwargs.setdefault('max_retries', 3)

        # Construct
        self.configuration = ConfigurationManager()
        self.http = HttpClient(self, adapter_kwargs)

        self.__interfaces = construct_map(self)

        self._site_url = None

    @property
    def site_url(self):
        if self._site_url is not None:
            return self._site_url

        url = self.base_url

        schema_end = url.find('://') + 3
        domain_start = url.find('.', schema_end) + 1

        return url[0:schema_end] + url[domain_start:]

    @site_url.setter
    def site_url(self, value):
        self._site_url = value

    def __getitem__(self, path):
        parts = path.strip('/').split('/')

        cur = self.__interfaces
        parameters = []

        while parts and type(cur) is dict:
            key = parts.pop(0)

            if key not in cur:
                if '*' in cur:
                    if key != '*':
                        parameters.append(key)

                    cur = cur['*']
                    continue

                return None

            cur = cur[key]

        if type(cur) is dict:
            cur = cur.get(None)

        if parts:
            parameters.extend(parts)

        if parameters:
            return InterfaceProxy(cur, parameters)

        return cur
