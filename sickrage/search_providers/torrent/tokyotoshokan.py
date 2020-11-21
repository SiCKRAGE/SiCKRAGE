# Author: Mr_Orange
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import re

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, try_int, convert_size
from sickrage.search_providers import TorrentProvider


class TokyoToshokanProvider(TorrentProvider):
    def __init__(self):
        super(TokyoToshokanProvider, self).__init__("TokyoToshokan", 'https://www.tokyotosho.info', False)

        self._urls.update({
            'search': '{base_url}/search.php'.format(**self._urls),
            'rss': '{base_url}/rss.php'.format(**self._urls)
        })

        self.supports_absolute_numbering = True
        self.anime_only = True

        # custom settings
        self.custom_settings = {
            'minseed': 0,
            'minleech': 0
        }

        self.cache = TVCache(self, min_time=15)

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: {}".format(mode))
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: {}".format(search_string))

                search_params = {
                    "terms": search_string,
                    "type": 1
                }

                resp = self.session.get(self.urls['search'], params=search_params)
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

        with bs4_parser(data) as soup:
            torrent_table = soup.find('table', class_='listing')
            torrent_rows = torrent_table('tr') if torrent_table else []

            # Continue only if one Release is found
            if len(torrent_rows) < 2:
                sickrage.app.log.debug("Data returned from provider does not contain any torrents")
                return results

            a = 1 if len(torrent_rows[0]('td')) < 2 else 0

            for top, bot in zip(torrent_rows[a::2], torrent_rows[a + 1::2]):
                try:
                    title = download_url = ""
                    desc_top = top.find('td', class_='desc-top')
                    if desc_top:
                        title = desc_top.get_text(strip=True)
                        download_url = desc_top.find('a')['href']

                    if not all([title, download_url]):
                        continue

                    stats = bot.find('td', class_='stats').get_text(strip=True)
                    sl = re.match(r'S:(?P<seeders>\d+)L:(?P<leechers>\d+)C:(?:\d+)ID:(?:\d+)', stats.replace(' ', ''))
                    seeders = try_int(sl.group('seeders'))
                    leechers = try_int(sl.group('leechers'))

                    desc_bottom = bot.find('td', class_='desc-bot').get_text(strip=True)
                    size = convert_size(desc_bottom.split('|')[1].strip('Size: '), -1)

                    results += [
                        {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                    ]

                    if mode != 'RSS':
                        sickrage.app.log.debug("Found result: {}".format(title))
                except Exception:
                    sickrage.app.log.error("Failed parsing provider")

        return results
