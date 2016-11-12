# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage
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

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, convert_size
from sickrage.providers import TorrentProvider


class TORRENTZProvider(TorrentProvider):
    def __init__(self):

        super(TORRENTZProvider, self).__init__("Torrentz", 'torrentz2.eu', False)

        self.supports_backlog = True
        self.confirmed = True
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = TVCache(self, min_time=15)

        self.urls.update({
            'verified': '{base_url}/feed_verified'.format(base_url=self.urls['base_url']),
            'feed': '{base_url}/feed'.format(base_url=self.urls['base_url'])
        })

    def seed_ratio(self):
        return self.ratio

    @staticmethod
    def _split_description(description):
        match = re.findall(r'[0-9]+', description)
        return int(match[0]) * 1024 ** 2, int(match[1]), int(match[2])

    def search(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):
        results = []

        for mode in search_strings:
            items = []
            sickrage.srCore.srLogger.debug('Search Mode: {}'.format(mode))
            for search_string in search_strings[mode]:
                search_url = self.urls['feed']
                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug('Search string: {}'.format(search_string))

                try:
                    data = sickrage.srCore.srWebSession.get(search_url, params={'f': search_string}).text
                except Exception:
                    sickrage.srCore.srLogger.debug('No data returned from provider')
                    continue

                if not data.startswith('<?xml'):
                    sickrage.srCore.srLogger.info('Expected xml but got something else, is your mirror failing?')
                    continue

                with bs4_parser(data) as parser:
                    for item in parser('item'):
                        if item.category and 'tv' not in item.category.get_text(strip=True):
                            continue

                        title = item.title.get_text(strip=True)
                        t_hash = item.guid.get_text(strip=True).rsplit('/', 1)[-1]

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

                        items += [{
                            'title': title,
                            'link': download_url,
                            'size': size,
                            'seeders': seeders,
                            'leechers': leechers,
                            'hash': t_hash
                        }]

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: int(d.get('seeders', 0)), reverse=True)
            results += items

        return results

