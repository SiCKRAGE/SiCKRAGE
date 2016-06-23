# Author: echel0n <echel0n@sickrage.ca>
# URL: http://github.com/SiCKRAGETV/SickRage/
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import tornado
import tornado.web

route_list = []

class Route(object):
    _routes = []

    def __init__(self, uri, name=None):
        self._uri = uri
        self.name = name

    def __call__(self, _handler):
        """gets called when we class decorate"""
        name = self.name and self.name or _handler.__name__
        self._routes.append((self._uri, _handler, name))
        return _handler

    @staticmethod
    def get_routes(webroot=''):
        Route._routes.reverse()
        routes = [tornado.web.url(webroot + _uri, _handler, name=name) for _uri, _handler, name, in Route._routes]
        return routes


def route_redirect(from_, to, name=None):
    Route._routes.append(tornado.web.url(from_, tornado.web.RedirectHandler, dict(url=to), name=name))
