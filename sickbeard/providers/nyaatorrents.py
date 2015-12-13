# Author: Mr_Orange
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

from __future__ import unicode_literals

import urllib
import re

import logging
from sickbeard import tvcache
from sickbeard.providers import generic


class NyaaProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "NyaaTorrents")

        self.supportsBacklog = True
        self.public = True
        self.supportsAbsoluteNumbering = True
        self.anime_only = True
        self.ratio = None

        self.cache = NyaaCache(self)

        self.urls = {'base_url': 'http://www.nyaa.se/'}

        self.url = self.urls[b'base_url']

        self.minseed = 0
        self.minleech = 0
        self.confirmed = False

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):
        if self.show and not self.show.is_anime:
            return []

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_strings.keys():
            logging.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:
                if mode is not 'RSS':
                    logging.debug("Search string: %s" % search_string)

                params = {
                    "page": 'rss',
                    "cats": '1_0',  # All anime
                    "sort": 2,  # Sort Descending By Seeders
                    "order": 1
                }
                if mode is not 'RSS':
                    params[b"term"] = search_string.encode('utf-8')

                searchURL = self.url + '?' + urllib.urlencode(params)
                logging.debug("Search URL: %s" % searchURL)

                summary_regex = ur"(\d+) seeder\(s\), (\d+) leecher\(s\), \d+ download\(s\) - (\d+.?\d* [KMGT]iB)(.*)"
                s = re.compile(summary_regex, re.DOTALL)

                results = []
                for curItem in self.cache.getRSSFeed(searchURL)['entries'] or []:
                    title = curItem[b'title']
                    download_url = curItem[b'link']
                    if not all([title, download_url]):
                        continue

                    seeders, leechers, size, verified = s.findall(curItem[b'summary'])[0]
                    size = self._convertSize(size)

                    # Filter unseeded torrent
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode is not 'RSS':
                            logging.debug(
                                "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                    title, seeders, leechers))
                        continue

                    if self.confirmed and not verified and mode is not 'RSS':
                        logging.debug(
                            "Found result " + title + " but that doesn't seem like a verified result so I'm ignoring it")
                        continue

                    item = title, download_url, size, seeders, leechers
                    if mode is not 'RSS':
                        logging.debug("Found result: %s " % title)

                    items[mode].append(item)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    @staticmethod
    def _convertSize(size):
        size, modifier = size.split(' ')
        size = float(size)
        if modifier in 'KiB':
            size = size * 1024
        elif modifier in 'MiB':
            size = size * 1024 ** 2
        elif modifier in 'GiB':
            size = size * 1024 ** 3
        elif modifier in 'TiB':
            size = size * 1024 ** 4
        return int(size)

    def seedRatio(self):
        return self.ratio


class NyaaCache(tvcache.TVCache):
    def __init__(self, provider_obj):
        tvcache.TVCache.__init__(self, provider_obj)

        # only poll NyaaTorrents every 15 minutes max
        self.minTime = 15

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}


provider = NyaaProvider()
