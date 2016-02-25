# Author: echel0n <sickrage.tv@gmail.com>
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

import os

import sickrage
from sickrage.core.srsession import srSession
from sickrage.indexers.indexer_config import indexerConfig


class srIndexerApi(object):
    def __init__(self, indexerID=1):
        self.indexerID = indexerID

    def indexer(self, *args, **kwargs):
        return indexerConfig[self.indexerID]['module'](session=self.session, *args, **kwargs)

    @property
    def config(self):
        return indexerConfig[self.indexerID]

    @property
    def name(self):
        return indexerConfig[self.indexerID]['name']

    @property
    def api_params(self):
        if sickrage.srConfig.CACHE_DIR:
            indexerConfig[self.indexerID]['api_params']['cache'] = os.path.join(sickrage.srConfig.CACHE_DIR,
                                                                                'indexers',
                                                                                self.name)
        if sickrage.srConfig.PROXY_SETTING and sickrage.srConfig.PROXY_INDEXERS:
            indexerConfig[self.indexerID]['api_params']['proxy'] = sickrage.srConfig.PROXY_SETTING

        return indexerConfig[self.indexerID]['api_params']

    @property
    def cache(self):
        return self.api_params['cache']

    @property
    def indexers(self):
        return dict((int(x['id']), x['name']) for x in indexerConfig.values())

    @property
    def session(self):
        return indexerConfig[self.indexerID]['session'] or srSession().session
