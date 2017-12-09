# coding=utf-8
#
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, unicode_literals

import json

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import convert_size
from sickrage.providers import TorrentProvider


class DanishbitsProvider(TorrentProvider):
    def __init__(self):
        super(DanishbitsProvider, self).__init__('Danishbits', 'https://danishbits.org', True)

        # Credentials
        self.username = None
        self.passkey = None

        # Torrent Stats
        self.minseed = 0
        self.minleech = 0
        self.freeleech = True

        # URLs
        self.urls.update({
            'login': '{base_url}/login.php'.format(**self.urls),
            'search': '{base_url}/couchpotato.php'.format(**self.urls),
        })

        # Proper Strings

        # Cache
        self.cache = TVCache(self, min_time=10)

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if not self.login():
            return results

        # Search Params
        search_params = {
            'user': self.username,
            'passkey': self.passkey,
            'search': search_strings,
        }

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: {0}".format(mode))
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: {0}".format(search_string))

                search_params['search'] = search_string

                try:
                    data = self.session.get(self.urls['search'], params=search_params).text
                    results += self.parse(data, mode)
                except Exception:
                    sickrage.app.log.debug("No data returned from provider")

        return results

    def parse(self, data, mode):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []

        torrents = json.loads(data)

        if 'results' in torrents:
            for torrent in torrents['results']:
                try:
                    title = torrent['release_name']
                    download_url = torrent['download_url']
                    seeders = torrent['seeders']
                    leechers = torrent['leechers']

                    freeleech = torrent['freeleech']
                    if self.freeleech and not freeleech:
                        continue

                    size = convert_size(torrent['size'], -1)

                    results += [
                        {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                    ]

                    if mode != 'RSS':
                        sickrage.app.log.debug("Found result: {}".format(title))
                except Exception:
                    sickrage.app.log.error('Failed parsing provider')

        return results
