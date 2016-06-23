#!/usr/bin/env python2

# Author: echel0n <echel0n@sickrage.ca>
# URL: https://git.sickrage.ca
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

from __future__ import unicode_literals

import sickrage
from sickrage.core.caches import tv_cache
from sickrage.providers import TorrentProvider


class BTDIGGProvider(TorrentProvider):
    def __init__(self):
        super(BTDIGGProvider, self).__init__("BTDigg",'btdigg.org')

        self.supportsBacklog = True

        self.ratio = 0

        self.urls.update({
            'api': 'api.{base_url}/'.format(base_url=self.urls['base_url'])
        })

        self.cache = BTDiggCache(self)

    def search(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_strings.keys():
            sickrage.srCore.srLogger.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug("Search string: %s" % search_string)

                searchURL = self.urls['api'] + "api/private-341ada3245790954/s02?q=" + search_string + "&p=0&order=1"
                sickrage.srCore.srLogger.debug("Search URL: %s" % searchURL)

                try:
                    jdata = sickrage.srCore.srWebSession.get(searchURL).json()
                except Exception:
                    sickrage.srCore.srLogger.info("No data returned to be parsed!!!")
                    continue

                for torrent in jdata:
                    if not torrent['ff']:
                        title = torrent['name']
                        download_url = torrent['magnet']
                        size = torrent['size']
                        # FIXME
                        seeders = 1
                        leechers = 0

                        if not all([title, download_url]):
                            continue

                        # Filter unseeded torrent
                        # if seeders < self.minseed or leechers < self.minleech:
                        #    if mode != 'RSS':
                        #        LOGGER.debug(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers))
                        #    continue

                        item = title, download_url, size, seeders, leechers
                        if mode != 'RSS':
                            sickrage.srCore.srLogger.debug("Found result: %s" % title)

                        items[mode].append(item)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class BTDiggCache(tv_cache.TVCache):
    def __init__(self, provider_obj):
        tv_cache.TVCache.__init__(self, provider_obj)

        # Cache results for a hour ,since BTDigg takes some time to crawl
        self.minTime = 60

    def _getRSSData(self):
        # Use x264 for RSS search since most results will use that codec and since the site doesnt have latest results search
        search_params = {'RSS': ['x264']}
        return {'entries': self.provider.search(search_params)}
