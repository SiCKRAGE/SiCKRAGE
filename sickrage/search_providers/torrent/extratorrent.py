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
from sickrage.core.helpers import convert_size, try_int, bs4_parser
from sickrage.search_providers import TorrentProvider


class ExtraTorrentProvider(TorrentProvider):
    def __init__(self):
        super(ExtraTorrentProvider, self).__init__("ExtraTorrent", 'https://extratorrent.si', False)

        self._urls.update({
            'search': '{base_url}/search/'.format(**self._urls),
            'rss': '{base_url}/category/8/TV+Torrents.html'.format(**self._urls)
        })

        # custom settings
        self.custom_settings = {
            'minseed': 0,
            'minleech': 0
        }

        self.cache = TVCache(self)

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []

        if not self.login():
            return results

        # Search Params
        search_params = {
            'page': 1,
            's_cat': 8,
        }

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: %s" % mode)

            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: %s " % search_string)
                    search_params['search'] = search_string
                    search_url = self.urls['search']
                else:
                    search_url = self.urls['rss']

                while search_params['page'] < 11:
                    resp = self.session.get(search_url, params=search_params)
                    if not resp or not resp.text:
                        sickrage.app.log.debug("No data returned from provider")
                        break

                    results += self.parse(resp.text, mode)
                    search_params['page'] += 1

        return results

    def parse(self, data, mode, **kwargs):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []

        with bs4_parser(data) as html:
            torrent_table = html.find('table', class_='tl')
            if not torrent_table:
                sickrage.app.log.debug('Data returned from provider does not contain any torrents')
                return results

            # Continue only if at least one Release is found
            torrent_rows = torrent_table.find_all('tr')
            if len(torrent_rows) < 2:
                sickrage.app.log.debug('Data returned from provider does not contain any torrents')
                return results

            for result in torrent_rows[2:]:
                cells = result('td')
                if len(cells) < 8:
                    continue

                try:
                    title = cells[2].find('a').get_text(strip=True)
                    download_url = cells[0].find_all('a')[1].get('href')
                    if not (title and download_url):
                        continue

                    seeders = try_int(cells[5].get_text(strip=True), 0)
                    leechers = try_int(cells[6].get_text(strip=True), 0)

                    torrent_size = cells[4].get_text()
                    size = convert_size(torrent_size, -1, ['B', 'KIB', 'MIB', 'GIB', 'TIB', 'PIB'])

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
                    sickrage.app.log.error('Failed parsing provider.')

        return results
