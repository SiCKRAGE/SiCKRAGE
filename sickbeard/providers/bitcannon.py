# -*- coding: utf-8 -*-
# Author: miigotu <miigotu@gmail.com>
# URL: http://github.com/SiCKRAGETV/SickRage
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

from urllib import quote_plus

import logging
from sickbeard import tvcache
from sickbeard.providers import generic


class BitCannonProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "BitCannon")

        self.supportsBacklog = True
        self.public = True

        self.minseed = None
        self.minleech = None
        self.ratio = 0

        self.cache = BitCannonCache(self)

        self.url = 'http://127.0.0.1:1337/'
        self.urls = {
            'base_url': self.url,
            'search': self.url + 'search/',
            'trackers': self.url + 'stats',
        }

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):
        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        trackers = (self.getURL(self.urls[b'trackers'], json=True) or {}).get('Trackers', [])
        if not trackers:
            logging.info('Could not get tracker list from BitCannon, aborting search')
            return results

        for mode in search_strings.keys():
            logging.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:
                searchURL = self.urls[b'search'] + search_string
                logging.debug("Search URL: %s" % searchURL)
                data = self.getURL(searchURL, json=True)
                for item in data or []:
                    if 'tv' not in (item.get('Category') or '').lower():
                        continue

                    title = item.get('Title', '')
                    info_hash = item.get('Btih', '')
                    if not all([title, info_hash]):
                        continue

                    swarm = item.get('Swarm', {})
                    seeders = swarm.get('Seeders', 0)
                    leechers = swarm.get('Leechers', 0)
                    size = item.get('Size', -1)

                    # Filter unseeded torrent
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode is not 'RSS':
                            logging.debug(
                                "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                    title, seeders, leechers))
                        continue

                    # Only build the url if we selected it
                    download_url = 'magnet:?xt=urn:btih:%s&dn=%s&tr=%s' % (info_hash, quote_plus(title.encode('utf-8')),
                                                                           '&tr='.join(
                                                                                   [quote_plus(x.encode('utf-8')) for x
                                                                                    in trackers]))

                    item = title, download_url, size, seeders, leechers
                    if mode is not 'RSS':
                        logging.debug("Found result: %s " % title)

                    items[mode].append(item)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class BitCannonCache(tvcache.TVCache):
    def __init__(self, provider_obj):
        tvcache.TVCache.__init__(self, provider_obj)

        # only poll KickAss every 10 minutes max
        self.minTime = 20

    def _getRSSData(self):
        return {'entries': []}
        # search_strings = {'RSS': ['']}
        # return {'entries': self.provider._doSearch(search_strings)}


provider = BitCannonProvider()
