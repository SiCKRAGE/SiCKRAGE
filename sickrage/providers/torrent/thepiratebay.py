# Author: Mr_Orange <mr_orange@hotmail.it>
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

import re
from urllib import urlencode

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import convert_size
from sickrage.providers import TorrentProvider


class ThePirateBayProvider(TorrentProvider):
    def __init__(self):

        super(ThePirateBayProvider, self).__init__("ThePirateBay",'pirateproxy.la', False)

        self.supports_backlog = True

        self.ratio = None
        self.confirmed = True
        self.minseed = None
        self.minleech = None

        self.urls.update({
            'search': '{base_url}/s/'.format(base_url=self.urls['base_url']),
            'rss': '{base_url}/tv/latest'.format(base_url=self.urls['base_url'])
        })

        self.re_title_url = r'/torrent/(?P<id>\d+)/(?P<title>.*?)".+?(?P<url>magnet.*?)".+?Size (?P<size>[\d\.]*&nbsp;[TGKMiB]{2,3}).+?(?P<seeders>\d+)</td>.+?(?P<leechers>\d+)</td>'

        self.cache = TVCache(self, min_time=30)

    def search(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):
        results = []

        """
        205 = SD, 208 = HD, 200 = All Videos
        https://pirateproxy.pl/s/?q=Game of Thrones&type=search&orderby=7&page=0&category=200
        """
        search_params = {
            "q": "",
            "type": "search",
            "orderby": 7,
            "page": 0,
            "category": 200
        }

        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_strings.keys():
            sickrage.srCore.srLogger.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:

                search_params.update({'q': search_string.strip()})

                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug("Search string: " + search_string)

                searchURL = self.urls[('search', 'rss')[mode == 'RSS']] + '?' + urlencode(search_params)
                sickrage.srCore.srLogger.debug("Search URL: %s" % searchURL)

                try:
                    data = sickrage.srCore.srWebSession.get(searchURL).text
                except Exception:
                    sickrage.srCore.srLogger.debug("No data returned from provider")
                    continue

                matches = re.compile(self.re_title_url, re.DOTALL).finditer(data)
                for torrent in matches:
                    title = torrent.group('title')
                    download_url = torrent.group('url')
                    size = convert_size(torrent.group('size'))
                    seeders = int(torrent.group('seeders'))
                    leechers = int(torrent.group('leechers'))

                    if not all([title, download_url]):
                        continue

                    # Filter unseeded torrent
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode != 'RSS':
                            sickrage.srCore.srLogger.debug(
                                "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                    title, seeders, leechers))
                        continue

                    # Accept Torrent only from Good People for every Episode Search
                    if self.confirmed and re.search(r'(VIP|Trusted|Helper|Moderator)', torrent.group(0)) is None:
                        if mode != 'RSS':
                            sickrage.srCore.srLogger.debug(
                                "Found result %s but that doesn't seem like a trusted result so I'm ignoring it" % title)
                        continue

                    item = title, download_url, size, seeders, leechers
                    if mode != 'RSS':
                        sickrage.srCore.srLogger.debug("Found result: %s " % title)

                    items[mode].append(item)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seed_ratio(self):
        return self.ratio