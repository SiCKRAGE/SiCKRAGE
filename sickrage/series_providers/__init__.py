# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
import importlib
import inspect
import os
import pkgutil

from sickrage.series_providers.cache import SeriesProviderShowCache


class SeriesProvider(object):
    def __init__(self, series_provider_id):
        self.id = series_provider_id

        self.apikey = ""
        self.trakt_id = ""

        self.headers = {}

        self.cache = SeriesProviderShowCache()

    @property
    def name(self):
        return self.id.display_name

    @property
    def slug(self):
        return self.id.slug


class SeriesProviders(dict):
    def __init__(self):
        super(SeriesProviders, self).__init__()
        for (__, name, __) in pkgutil.iter_modules([os.path.dirname(__file__)]):
            imported_module = importlib.import_module('.' + name, package='sickrage.series_providers')
            for __, klass in inspect.getmembers(imported_module,
                                                predicate=lambda o: inspect.isclass(o) and issubclass(o, SeriesProvider) and o is not SeriesProvider):
                self[klass().id] = klass()
                break
