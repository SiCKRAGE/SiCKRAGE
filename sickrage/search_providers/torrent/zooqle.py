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


import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import try_int
from sickrage.search_providers import TorrentProvider


class ZooqleProvider(TorrentProvider):
    def __init__(self):
        """Initialize the class."""
        super(ZooqleProvider, self).__init__('Zooqle', 'https://zooqle.com', False)

        # URLs
        self._urls.update({
            'search': '{base_url}/search'.format(**self._urls),
            'api': '{base_url}/api/media/%s'.format(**self._urls),
        })

        # custom settings
        self.custom_settings = {
            'minseed': 0,
            'minleech': 0
        }


        # Proper Strings
        self.proper_strings = ['PROPER', 'REPACK', 'REAL']

        # Cache
        self.cache = TVCache(self, min_time=15)

    def _get_torrent_info(self, torrent_hash):
        try:
            return self.session.get(self.urls['api'] % torrent_hash).json()
        except Exception:
            return {}

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
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
            'q': '* category:TV',
            's': 'dt',
            'v': 't',
            'sd': 'd',
        }

        for mode in search_strings:
            sickrage.app.log.debug('Search mode: {}'.format(mode))

            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug('Search string: {}'.format(search_string))
                    search_params['q'] = '{} category:TV'.format(search_string)

                search_params['fmt'] = 'rss'
                search_params['pg'] = 1

                while search_params['pg'] < 11:
                    data = self.cache.get_rss_feed(self.urls['search'], params=search_params)
                    if not data or not data.get('feed'):
                        sickrage.app.log.debug('No data returned from provider')
                        break

                    results += self.parse(data, mode)

                    total_results = try_int(data['feed'].get('opensearch_totalresults'))
                    start_index = try_int(data['feed'].get('opensearch_startindex'))
                    items_per_page = try_int(data['feed'].get('opensearch_itemsperpage'))
                    if not total_results or start_index + items_per_page > total_results:
                        break

                    search_params['pg'] += 1

        return results

    def parse(self, data, mode):
        """
        Parse search results for items.

        :param data: The raw response from a search
        :param mode: The current mode used to search, e.g. RSS

        :return: A list of items found
        """
        results = []

        if not data.get('entries'):
            sickrage.app.log.debug('Data returned from provider does not contain any torrents')
            return results

        for item in data['entries']:
            try:
                title = item.get('title')
                download_url = item.get('torrent_magneturi')
                if not all([title, download_url]):
                    continue

                seeders = try_int(item['torrent_seeds'])
                leechers = try_int(item['torrent_peers'])
                size = try_int(item['torrent_contentlength'], -1)

                results += [{
                    'title': title,
                    'link': download_url,
                    'size': size,
                    'seeders': seeders,
                    'leechers': leechers
                }]

                if mode != 'RSS':
                    sickrage.app.log.debug('Found result: {}'.format(title))
            except Exception:
                sickrage.app.log.error("Failed parsing provider")

        return results
