# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.
import os
import sickbeard

from indexer_config import initConfig, indexerConfig


class IndexerApi(object):
    def __init__(self, indexer_id=None):
        self.indexer_id = int(indexer_id) if indexer_id else None

    def __del__(self):
        pass

    def indexer(self, *args, **kwargs):
        if self.indexer_id:
            return indexerConfig[self.indexer_id]['module'](*args, **kwargs)

    @property
    def config(self):
        if self.indexer_id:
            return indexerConfig[self.indexer_id]
        return initConfig

    @property
    def name(self):
        if self.indexer_id:
            return indexerConfig[self.indexer_id]['name']

    @property
    def api_params(self):
        if self.indexer_id:
            if sickbeard.CACHE_DIR:
                indexerConfig[self.indexer_id]['api_params']['cache'] = os.path.join(sickbeard.CACHE_DIR, self.name)
            return indexerConfig[self.indexer_id]['api_params']

    @property
    def cache(self):
        if sickbeard.CACHE_DIR:
            return self.api_params['cache']

    @property
    def indexers(self):
        return dict((x['id'], x['name']) for x in indexerConfig.values())