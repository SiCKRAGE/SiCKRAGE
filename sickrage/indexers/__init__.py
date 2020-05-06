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

import re

import sickrage
from sickrage.indexers.config import indexerConfig
from sickrage.indexers.ui import ShowListUI


class IndexerApi(object):
    def __init__(self, indexerID=1):
        self.indexerID = indexerID
        self.module = indexerConfig[self.indexerID]['module']

    def indexer(self, *args, **kwargs):
        self.module.settings(*args, **kwargs)
        return self.module

    @property
    def config(self):
        return indexerConfig[self.indexerID]

    @property
    def name(self):
        return indexerConfig[self.indexerID]['name']

    @property
    def trakt_id(self):
        return indexerConfig[self.indexerID]['trakt_id']

    @property
    def api_params(self):
        if sickrage.app.config.proxy_setting and sickrage.app.config.proxy_indexers:
            indexerConfig[self.indexerID]['api_params']['proxy'] = sickrage.app.config.proxy_setting

        return indexerConfig[self.indexerID]['api_params']

    @property
    def cache(self):
        return self.api_params['cache']

    @property
    def indexers(self):
        return dict((int(x['id']), x['name']) for x in indexerConfig.values())

    @property
    def indexersByTraktID(self):
        return dict((x['trakt_id'], int(x['id'])) for x in indexerConfig.values())

    def search_for_show_id(self, show_name, custom_ui=None):
        """
        Contacts indexer to check for information on shows by showid

        :param show_name: Name of show
        :param custom_ui: Custom UI for indexer use
        :return:
        """

        show_name = re.sub('[. -]', ' ', show_name)

        # Query Indexers for each search term and build the list of results
        lINDEXER_API_PARMS = self.api_params.copy()
        lINDEXER_API_PARMS['custom_ui'] = custom_ui or ShowListUI

        sickrage.app.log.debug("Trying to find show ID for show {} on indexer {}".format(show_name, self.name))

        t = self.indexer(**lINDEXER_API_PARMS)
        indexer_data = t[show_name]
        if not indexer_data:
            return

        return indexer_data['id']
