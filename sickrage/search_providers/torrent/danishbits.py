# coding=utf-8
#
# URL: https://sickrage.ca
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE. If not, see <http://www.gnu.org/licenses/>.


import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import convert_size
from sickrage.search_providers import TorrentProvider


class DanishbitsProvider(TorrentProvider):
    def __init__(self):
        super(DanishbitsProvider, self).__init__('Danishbits', 'https://danishbits.org', True)

        # URLs
        self._urls.update({
            'login': '{base_url}/login.php'.format(**self._urls),
            'search': '{base_url}/couchpotato.php'.format(**self._urls),
        })

        # custom settings
        self.custom_settings = {
            'username': '',
            'passkey': '',
            'freeleech': True,
            'minseed': 0,
            'minleech': 0
        }

        # Proper Strings
        self.proper_strings = ['PROPER', 'REPACK', 'REAL', 'RERIP']

        # Cache
        self.cache = TVCache(self)

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []

        # Search Params
        search_params = {
            'user': self.custom_settings['username'],
            'passkey': self.custom_settings['passkey'],
            'search': '.',
            'latest': 'true'
        }

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: {0}".format(mode))
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: {0}".format(search_string))
                    search_params['latest'] = 'false'
                    search_params['search'] = search_string

                resp = self.session.get(self.urls['search'], params=search_params)
                if not resp or resp.content:
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

        for torrent in data.get('results', []):
            try:
                title = torrent.get('release_name')
                download_url = torrent.get('download_url')
                if not all([title, download_url]):
                    continue

                seeders = torrent.get('seeders')
                leechers = torrent.get('leechers')

                freeleech = torrent.get('freeleech')
                if self.custom_settings['freeleech'] and not freeleech:
                    continue

                torrent_size = '{} MB'.format(torrent.get('size', -1))
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
                sickrage.app.log.error('Failed parsing provider')

        return results
