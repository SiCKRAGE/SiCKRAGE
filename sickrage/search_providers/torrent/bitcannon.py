# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
from urllib.parse import urljoin

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import try_int, convert_size, validate_url
from sickrage.core.tv.show.helpers import find_show
from sickrage.search_providers import TorrentProvider


class BitCannonProvider(TorrentProvider):
    def __init__(self):
        super(BitCannonProvider, self).__init__("BitCannon", 'http://localhost:3000', False)
        self._urls.update({
            'search': '{base_url}/api/search'.format(**self._urls)
        })

        # custom settings
        self.custom_settings = {
            'api_key': '',
            'custom_url': '',
            'minseed': 0,
            'minleech': 0
        }

        self.cache = TVCache(self, search_strings={'RSS': ['tv', 'anime']})

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []

        search_url = self.urls["search"]
        if self.custom_settings['custom_url']:
            if not validate_url(self.custom_settings['custom_url']):
                sickrage.app.log.warning("Invalid custom url: {0}".format(self.custom_settings['custom_url']))
                return results
            search_url = urljoin(self.custom_settings['custom_url'], search_url.split(self.urls['base_url'])[1])

        show_object = find_show(series_id, series_provider_id)

        # Search Params
        search_params = {
            'category': ("tv", "anime")[bool(show_object.anime)],
            'apiKey': self.custom_settings['api_key'],
        }

        for mode in search_strings:
            sickrage.app.log.debug('Search mode: {}'.format(mode))
            for search_string in search_strings[mode]:
                search_params['q'] = search_string
                if mode != 'RSS':
                    sickrage.app.log.debug('Search string: {}'.format(search_string))

                resp = self.session.get(search_url, params=search_params)
                if not resp or not resp.content:
                    sickrage.app.log.debug('No data returned from provider')
                    continue

                try:
                    data = resp.json()
                except ValueError:
                    sickrage.app.log.debug('No data returned from provider')
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

        torrent_rows = data.pop('torrents', {})

        if not self._check_auth_from_data(data):
            return results

        # Skip column headers
        for row in torrent_rows:
            try:
                title = row.pop('title', '')
                info_hash = row.pop('infoHash', '')
                download_url = 'magnet:?xt=urn:btih:' + info_hash
                if not all([title, download_url, info_hash]):
                    continue

                swarm = row.pop('swarm', {})
                seeders = try_int(swarm.pop('seeders'))
                leechers = try_int(swarm.pop('leechers'))

                size = convert_size(row.pop('size', -1), -1)

                results += [
                    {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                ]

                if mode != 'RSS':
                    sickrage.app.log.debug('Found result: {}'.format(title))
            except Exception:
                sickrage.app.log.error('Failed parsing provider')

        return results

    @staticmethod
    def _check_auth_from_data(data):
        if not all([isinstance(data, dict),
                    data.pop('status', 200) != 401,
                    data.pop('message', '') != 'Invalid API key']):
            sickrage.app.log.warning('Invalid api key. Check your settings')
            return False

        return True
