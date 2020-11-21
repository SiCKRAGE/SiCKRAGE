# coding=utf-8
# Author: Gonçalo M. (aka duramato/supergonkas) <supergonkas@gmail.com>
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


import re

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, try_int, convert_size
from sickrage.search_providers import TorrentProvider


class LimeTorrentsProvider(TorrentProvider):
    def __init__(self):
        super(LimeTorrentsProvider, self).__init__('LimeTorrents', 'https://www.limetorrents.cc', False)

        self._urls.update({
            'update': '{base_url}/post/updatestats.php'.format(**self._urls),
            'search': '{base_url}/search/tv/%s/'.format(**self._urls),
            'rss': '{base_url}/browse-torrents/TV-shows/'.format(**self._urls),
        })

        # custom settings
        self.custom_settings = {
            'confirmed': False,
            'minseed': 0,
            'minleech': 0
        }

        self.proper_strings = ['PROPER', 'REPACK', 'REAL']

        self.cache = TVCache(self)

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []
        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: {}".format(mode))
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: {}".format(search_string))

                search_url = (self.urls['rss'], self.urls['search'] % search_string)[mode != 'RSS']

                resp = self.session.get(search_url)
                if not resp or not resp.text:
                    sickrage.app.log.debug("No data returned from provider")
                    continue

                results += self.parse(resp.text, mode)

        return results

    def parse(self, data, mode, **kwargs):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []

        id_regex = re.compile(r'(?:\/)(.*)(?:-torrent-([0-9]*)\.html)', re.I)
        hash_regex = re.compile(r'(.*)([0-9a-f]{40})(.*)', re.I)

        def process_column_header(th):
            return th.span.get_text() if th.span else th.get_text()

        with bs4_parser(data) as html:
            torrent_table = html.find('table', class_='table2')
            if not torrent_table:
                sickrage.app.log.debug('Data returned from provider does not contain any torrents')
                return results

            torrent_rows = torrent_table.find_all('tr')
            labels = [process_column_header(label) for label in torrent_rows[0].find_all('th')]

            # Skip the first row, since it isn't a valid result
            for row in torrent_rows[1:]:
                cells = row.find_all('td')

                try:
                    title_cell = cells[labels.index('Torrent Name')]

                    verified = title_cell.find('img', title='Verified torrent')
                    if self.custom_settings['confirmed'] and not verified:
                        continue

                    title_anchors = title_cell.find_all('a')
                    if not title_anchors or len(title_anchors) < 2:
                        continue

                    title_url = title_anchors[0].get('href')
                    title = title_anchors[1].get_text(strip=True)
                    regex_result = id_regex.search(title_anchors[1].get('href'))

                    alt_title = regex_result.group(1)
                    if len(title) < len(alt_title):
                        title = alt_title.replace('-', ' ')

                    torrent_id = regex_result.group(2)
                    info_hash = hash_regex.search(title_url).group(2)
                    if not all([title, torrent_id, info_hash]):
                        continue

                    try:
                        self.session.get(self.urls['update'], timeout=30,
                                         params={'torrent_id': torrent_id, 'infohash': info_hash})
                    except Exception:
                        pass

                    download_url = 'magnet:?xt=urn:btih:{hash}&dn={title}'.format(hash=info_hash, title=title)

                    # Remove comma as thousands separator from larger number like 2,000 seeders = 2000
                    seeders = try_int(cells[labels.index('Seed')].get_text(strip=True).replace(',', ''), 1)
                    leechers = try_int(cells[labels.index('Leech')].get_text(strip=True).replace(',', ''))

                    size = convert_size(cells[labels.index('Size')].get_text(strip=True), -1)

                    results += [
                        {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                    ]

                    if mode != 'RSS':
                        sickrage.app.log.debug("Found result: {}".format(title))
                except Exception:
                    sickrage.app.log.error("Failed parsing provider")

        return results
