# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
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
import re

import sickrage
from sickrage.core.classes import ShowListUI
from sickrage.core.helpers import findCertainShow
from sickrage.indexers.config import indexerConfig


class srIndexerApi(object):
    def __init__(self, indexerID=1):
        self.indexerID = indexerID
        self.module = indexerConfig[self.indexerID]['module']

    def indexer(self, *args, **kwargs):
        return self.module(*args, **kwargs)

    @property
    def config(self):
        return indexerConfig[self.indexerID]

    @property
    def name(self):
        return indexerConfig[self.indexerID]['name']

    @property
    def api_params(self):
        if sickrage.srCore.srConfig.CACHE_DIR:
            indexerConfig[self.indexerID]['api_params']['cache'] = os.path.join(sickrage.srCore.srConfig.CACHE_DIR,
                                                                                'indexers',
                                                                                self.name)
        if sickrage.srCore.srConfig.PROXY_SETTING and sickrage.srCore.srConfig.PROXY_INDEXERS:
            indexerConfig[self.indexerID]['api_params']['proxy'] = sickrage.srCore.srConfig.PROXY_SETTING

        return indexerConfig[self.indexerID]['api_params']

    @property
    def cache(self):
        return self.api_params['cache']

    @property
    def indexers(self):
        return dict((int(x['id']), x['name']) for x in indexerConfig.values())

    def searchForShowID(self, regShowName, showid=None, ui=ShowListUI):
        """
        Contacts indexer to check for information on shows by showid

        :param regShowName: Name of show
        :param showid: Which indexer ID to look for
        :param ui: Custom UI for indexer use
        :return:
        """

        showNames = [re.sub('[. -]', ' ', regShowName)]

        # Query Indexers for each search term and build the list of results

        # Query Indexers for each search term and build the list of results
        lINDEXER_API_PARMS = self.api_params.copy()
        if ui is not None:
            lINDEXER_API_PARMS['custom_ui'] = ui
        t = self.indexer(**lINDEXER_API_PARMS)

        for name in showNames:
            sickrage.srCore.srLogger.debug("Trying to find " + name + " on " + self.name)

            try:
                search = t[showid] if showid else t[name]
            except Exception:
                continue

            try:
                seriesname = search[0]['seriesname']
            except Exception:
                seriesname = None

            try:
                series_id = search[0]['id']
            except Exception:
                series_id = None

            if not (seriesname and series_id):
                continue

            ShowObj = findCertainShow(sickrage.srCore.SHOWLIST, int(series_id))

            # Check if we can find the show in our list (if not, it's not the right show)
            if (showid is None) and (ShowObj is not None) and (ShowObj.indexerid == int(series_id)):
                return seriesname, self.indexerID, int(series_id)
            elif (showid is not None) and (int(showid) == int(series_id)):
                return seriesname, self.indexerID, int(showid)

        return None, None, None
