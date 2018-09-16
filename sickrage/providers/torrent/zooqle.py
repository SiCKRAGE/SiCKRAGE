# Author: echel0n <echel0n@sickrage.ca>
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
from sickrage.core.helpers import try_int, convert_size, bs4_parser
from sickrage.providers import TorrentProvider


class ZooqleProvider(TorrentProvider):
    def __init__(self):
        """Initialize the class."""
        super(ZooqleProvider, self).__init__('Zooqle', 'https://zooqle.com', False)

        # URLs
        self.urls.update({
            'search': '{base_url}/search'.format(**self.urls),
        })

        # Proper Strings
        self.proper_strings = ['PROPER', 'REPACK', 'REAL']

        # Miscellaneous Options

        # Torrent Stats
        self.minseed = None
        self.minleech = None

        # Cache
        self.cache = TVCache(self, min_time=15)

    def search(self, search_strings, age=0, ep_obj=None, **kwargs):
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
                    search_params = {'q': '{} category:TV'.format(search_string)}

                try:
                    data = self.session.get(self.urls['search'], params=search_params).text
                    results += self.parse(data, mode)
                except Exception:
                    sickrage.app.log.debug('No data returned from provider')

        return results

    def parse(self, data, mode):
        """
        Parse search results for items.

        :param data: The raw response from a search
        :param mode: The current mode used to search, e.g. RSS

        :return: A list of items found
        """
        results = []

        with bs4_parser(data) as html:
            torrent_table = html.find(class_='table-torrents')
            torrent_rows = torrent_table('tr') if torrent_table else []

            # Continue only if at least one release is found
            if len(torrent_rows) < 2:
                sickrage.app.log.debug('Data returned from provider does not contain any torrents')
                return results

            # Skip column headers
            for row in torrent_rows[1:]:
                cells = row('td')

                try:
                    title = cells[1].find('a').get_text()
                    download_url = cells[2].find('a', title='Magnet link')['href']
                    if not all([title, download_url]):
                        continue

                    seeders = 1
                    leechers = 0
                    if len(cells) > 5:
                        peers = cells[5].find('div')
                        if peers and peers.get('title'):
                            peers = peers['title'].replace(',', '').split(' | ', 1)
                            seeders = try_int(peers[0][9:])
                            leechers = try_int(peers[1][10:])

                    torrent_size = cells[3].get_text().replace(',', '')
                    size = convert_size(torrent_size, -1)

                    results += [
                        {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                    ]

                    if mode != 'RSS':
                        sickrage.app.log.debug('Found result: {}'.format(title))
                except Exception:
                    sickrage.app.log.error("Failed parsing provider")

        return results
