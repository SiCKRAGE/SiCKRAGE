# Author: Mr_Orange
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import convert_size, try_int
from sickrage.providers import TorrentProvider


class NyaaProvider(TorrentProvider):
    def __init__(self):
        super(NyaaProvider, self).__init__("NyaaTorrents", 'http://nyaa.si', False)

        self.supports_absolute_numbering = True
        self.anime_only = True

        self.minseed = 0
        self.minleech = 0
        self.confirmed = False

        self.cache = TVCache(self, min_time=20)

    def search(self, search_strings, age=0, ep_obj=None):
        """
        Search a provider and parse the results.

        :param search_strings: A dict with mode (key) and the search value (value)
        :param age: Not used
        :param ep_obj: Not used
        :returns: A list of search results (structure)
        """
        results = []

        # Search Params
        search_params = {
            'page': 'rss',
            'c': '1_0',  # All Anime
            'f': 0,  # No filter
            'q': '',
        }

        for mode in search_strings:
            sickrage.srCore.srLogger.debug('Search mode: {}'.format(mode))

            if self.confirmed:
                search_params['f'] = 2  # Trusted only
                sickrage.srCore.srLogger.debug('Searching only confirmed torrents')

            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug('Search string: {}'.format(search_string))
                    search_params['q'] = search_string

                data = self.cache.getRSSFeed(self.urls['base_url'], params=search_params)
                if not data:
                    sickrage.srCore.srLogger.debug('No data returned from provider')
                    continue
                if not data.get('entries'):
                    sickrage.srCore.srLogger.debug('Data returned from provider does not contain any {0}torrents',
                                                   'confirmed ' if self.confirmed else '')
                    continue

                results += self.parse(data['entries'], mode)

        return results

    def parse(self, data, mode):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []

        for item in data:
            try:
                title = item['title']
                download_url = item['link']
                if not all([title, download_url]):
                    continue

                seeders = try_int(item['nyaa_seeders'])
                leechers = try_int(item['nyaa_leechers'])

                # Filter unseeded torrent
                if seeders < min(self.minseed, 1):
                    if mode != 'RSS':
                        sickrage.srCore.srLogger.debug("Discarding torrent because it doesn't meet the "
                                                       "minimum seeders: {}. Seeders: {}".format(title, seeders))
                    continue

                size = convert_size(item['nyaa_size'], -1, units=['B', 'KIB', 'MIB', 'GIB', 'TIB', 'PIB'])

                item = {
                    'title': title,
                    'link': download_url,
                    'size': size,
                    'seeders': seeders,
                    'leechers': leechers
                }
                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug('Found result: {}'.format(title))

                results.append(item)
            except (AttributeError, TypeError, KeyError, ValueError, IndexError):
                sickrage.srCore.srLogger.error('Failed parsing provider')

        return results