# Author: Dustyn Gibson <miigotu@gmail.com>
# URL: https://github.com/SiCKRAGETV/SickRage
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

import re
from urllib import quote_plus

import sickrage
from sickrage.core.caches import tv_cache
from sickrage.core.helpers import bs4_parser, convert_size
from sickrage.providers import TorrentProvider


class TORRENTZProvider(TorrentProvider):
    def __init__(self):

        super(TORRENTZProvider, self).__init__("Torrentz", 'torrentz.eu')

        self.supportsBacklog = True
        self.confirmed = True
        self.ratio = None
        self.minseed = None
        self.minleech = None
        self.cache = TORRENTZCache(self)

        self.urls.update({
            'verified': '{base_url}/feed_verified'.format(base_url=self.urls['base_url']),
            'feed': '{base_url}/feed'.format(base_url=self.urls['base_url'])
        })

    def seedRatio(self):
        return self.ratio

    @staticmethod
    def _split_description(description):
        match = re.findall(r'[0-9]+', description)
        return int(match[0]) * 1024 ** 2, int(match[1]), int(match[2])

    def search(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):
        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_strings:
            for search_string in search_strings[mode]:
                search_url = self.urls['verified'] if self.confirmed else self.urls['feed']
                if mode != 'RSS':
                    search_url += '?q=' + quote_plus(search_string)
                    sickrage.srCore.srLogger.info(search_url)

                try:
                    data = sickrage.srCore.srWebSession.get(search_url).text
                except Exception:
                    sickrage.srCore.srLogger.info('Seems to be down right now!')
                    continue

                if not data.startswith('<?xml'):
                    sickrage.srCore.srLogger.info('Expected xml but got something else, is your mirror failing?')
                    continue

                with bs4_parser(data) as html:
                    if not html:
                        sickrage.srCore.srLogger.debug("No html data parsed from provider")
                        continue

                    for item in html('item'):
                        if item.category and 'tv' not in item.category.get_text(strip=True):
                            continue

                        title = item.title.text.rsplit(' ', 1)[0].replace(' ', '.')
                        t_hash = item.guid.text.rsplit('/', 1)[-1]

                        if not all([title, t_hash]):
                            continue

                        download_url = "magnet:?xt=urn:btih:" + t_hash + "&dn=" + title
                        torrent_size, seeders, leechers = self._split_description(item.find('description').text)
                        size = convert_size(torrent_size) or -1

                        # Filter unseeded torrent
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != 'RSS':
                                sickrage.srCore.srLogger.debug("Discarding torrent because it doesn't meet the minimum seeders or leechers: {} (S:{} L:{})".format(title, seeders, leechers))
                            continue

                        items[mode].append((title, download_url, size, seeders, leechers))

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)
            results += items[mode]

        return results


class TORRENTZCache(tv_cache.TVCache):
    def __init__(self, provider_obj):
        tv_cache.TVCache.__init__(self, provider_obj)

        # only poll every 15 minutes max
        self.minTime = 15

    def _getRSSData(self):
        return {'entries': self.provider.search({'RSS': ['']})}
