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
from sickrage.indexers.config import indexerConfig, indexerModules
from sickrage.indexers.ui import ShowListUI


class IndexerApi(object):
    def __init__(self, indexer_id=1):
        self.indexer_id = indexer_id

    def indexer(self, *args, **kwargs):
        instance = indexerModules[self.indexer_id]
        instance.settings(*args, **kwargs)
        return instance

    @property
    def config(self):
        return indexerConfig[self.indexer_id]

    @property
    def name(self):
        return indexerConfig[self.indexer_id]['name']

    @property
    def slug(self):
        return indexerConfig[self.indexer_id]['slug']

    @property
    def trakt_id(self):
        return indexerConfig[self.indexer_id]['trakt_id']

    @property
    def api_params(self):
        if sickrage.app.config.proxy_setting and sickrage.app.config.proxy_indexers:
            indexerConfig[self.indexer_id]['api_params']['proxy'] = sickrage.app.config.proxy_setting

        return indexerConfig[self.indexer_id]['api_params']

    @property
    def cache(self):
        return self.api_params['cache']

    @property
    def indexers(self):
        return list(indexerConfig.values())

    @property
    def indexers_by_slug(self):
        return dict((x['slug'], x) for x in indexerConfig.values())

    @property
    def indexers_by_trakt_id(self):
        return dict((x['trakt_id'], x) for x in indexerConfig.values())

    def search_for_show_id(self, show_name, custom_ui=None):
        """
        Contacts indexer to check for information on shows by showid

        :param show_name: Name of show
        :param custom_ui: Custom UI for indexer use
        :return:
        """

        show_name = re.sub('[. -]', ' ', show_name)

        # Query Indexers for each search term and build the list of results
        indexer_api_parms = self.api_params.copy()
        indexer_api_parms['custom_ui'] = custom_ui or ShowListUI

        sickrage.app.log.debug("Trying to find show ID for show {} on indexer {}".format(show_name, self.name))

        t = self.indexer(**indexer_api_parms)
        indexer_data = t[show_name]
        if not indexer_data:
            return

        return indexer_data['id']
