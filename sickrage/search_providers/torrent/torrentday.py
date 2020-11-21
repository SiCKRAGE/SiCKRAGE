# ##############################################################################
#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#  -
#  This file is part of SiCKRAGE.
#  -
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  -
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
# ##############################################################################


import re
from urllib.parse import urljoin

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import convert_size
from sickrage.search_providers import TorrentProvider


class TorrentDayProvider(TorrentProvider):
    def __init__(self):
        super(TorrentDayProvider, self).__init__("TorrentDay", 'https://www.torrentday.com', True)

        self._urls.update({
            'login': '{base_url}/torrents/'.format(**self._urls),
            'search': '{base_url}/t.json'.format(**self._urls),
            'download': '{base_url}/download.php/'.format(**self._urls)
        })

        # custom settings
        self.custom_settings = {
            'username': '',
            'password': '',
            'freeleech': False,
            'minseed': 0,
            'minleech': 0
        }

        self.enable_cookies = True
        self.required_cookies = ('uid', 'pass')

        # TV/480p - 24
        # TV/Bluray - 32
        # TV/DVD-R - 31
        # TV/DVD-Rip - 33
        # TV/Mobile - 46
        # TV/Packs - 14
        # TV/SD/x264 - 26
        # TV/x264 - 7
        # TV/x265 - 34
        # TV/XviD - 2

        self.categories = {
            'Season': {'14': 1},
            'Episode': {'2': 1, '26': 1, '7': 1, '24': 1, '34': 1},
            'RSS': {'2': 1, '26': 1, '7': 1, '24': 1, '34': 1, '14': 1}
        }

        self.cache = TVCache(self)

    def login(self):
        return self.cookie_login('log in')

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []

        if not self.login():
            return results

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: %s " % search_string)

                search_string = '+'.join(search_string.split())
                search_params = dict({'q': search_string}, **self.categories[mode])

                resp = self.session.get(self.urls['search'], params=search_params)
                if not resp or not resp.content:
                    sickrage.app.log.debug("No data returned from provider")
                    continue

                try:
                    data = resp.json()
                except ValueError:
                    sickrage.app.log.debug("No data returned from provider")
                    continue

                results += self.parse(data, mode)

        return results

    def parse(self, data, mode, **kwargs):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []

        for item in data:
            try:
                # Check if this is a freeleech torrent and if we've configured to only allow freeleech.
                if self.custom_settings['freeleech'] and item.get('download-multiplier') != 0:
                    continue

                title = re.sub(r'\[.*\=.*\].*\[/.*\]', '', item['name']) if item['name'] else None
                download_url = urljoin(self.urls['download'], '{}/{}.torrent'.format(
                    item['t'], item['name']
                )) if item['t'] and item['name'] else None
                if not all([title, download_url]):
                    continue

                seeders = int(item['seeders'])
                leechers = int(item['leechers'])

                torrent_size = item['size']
                size = convert_size(torrent_size, -1)

                results += [{
                    'title': title,
                    'link': download_url,
                    'size': size,
                    'seeders': seeders,
                    'leechers': leechers
                }]

                if mode != 'RSS':
                    sickrage.app.log.debug("Found result: {}".format(title))
            except Exception:
                sickrage.app.log.error("Failed parsing provider.")

        return results
