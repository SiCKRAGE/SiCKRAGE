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

import re

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, try_int, convert_size
from sickrage.providers import TorrentProvider


class TokyoToshokanProvider(TorrentProvider):
    def __init__(self):

        super(TokyoToshokanProvider, self).__init__("TokyoToshokan", 'http://tokyotosho.info', False)

        self.supports_absolute_numbering = True
        self.anime_only = True

        self.minseed = None
        self.minleech = None

        self.urls.update({
            'search': '{base_url}/search.php'.format(**self.urls),
            'rss': '{base_url}/rss.php'.format(**self.urls)
        })

        self.cache = TVCache(self, min_time=15)

    def search(self, search_strings, age=0, ep_obj=None):
        results = []

        if not ep_obj.show or not ep_obj.show.is_anime:
            return results

        for mode in search_strings:
            sickrage.srCore.srLogger.debug("Search Mode: {}".format(mode))
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug("Search string: {}".format(search_string))

                search_params = {
                    "terms": search_string,
                    "type": 1,  # get anime types
                }

                data = sickrage.srCore.srWebSession.get(self.urls['search'], params=search_params).text
                if not data:
                    continue

                with bs4_parser(data) as soup:
                    torrent_table = soup.find('table', class_='listing')
                    torrent_rows = torrent_table('tr') if torrent_table else []

                    # Continue only if one Release is found
                    if len(torrent_rows) < 2:
                        sickrage.srCore.srLogger.debug("Data returned from provider does not contain any torrents")
                        continue

                    a = 1 if len(torrent_rows[0]('td')) < 2 else 0

                    for top, bot in zip(torrent_rows[a::2], torrent_rows[a + 1::2]):
                        try:
                            desc_top = top.find('td', class_='desc-top')
                            title = desc_top.get_text(strip=True)
                            download_url = desc_top.find('a')['href']

                            desc_bottom = bot.find('td', class_='desc-bot').get_text(strip=True)
                            size = convert_size(desc_bottom.split('|')[1].strip('Size: '), -1)

                            stats = bot.find('td', class_='stats').get_text(strip=True)
                            sl = re.match(r'S:(?P<seeders>\d+)L:(?P<leechers>\d+)C:(?:\d+)ID:(?:\d+)',
                                          stats.replace(' ', ''))
                            seeders = try_int(sl.group('seeders')) if sl else 0
                            leechers = try_int(sl.group('leechers')) if sl else 0
                        except StandardError:
                            continue

                        if not all([title, download_url]):
                            continue

                        # Filter unseeded torrent
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != 'RSS':
                                sickrage.srCore.srLogger.debug(
                                    "Discarding torrent because it doesn't meet the minimum seeders or leechers: {} "
                                    "(S:{} L:{})".format
                                    (title, seeders, leechers))
                            continue

                        item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders,
                                'leechers': leechers, 'hash': ''}

                        if mode != 'RSS':
                            sickrage.srCore.srLogger.debug("Found result: {}".format(title))

                        results.append(item)

        # Sort all the items by seeders if available
        results.sort(key=lambda k: try_int(k.get('seeders', 0)), reverse=True)

        return results

    def parse(self, data, mode):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []