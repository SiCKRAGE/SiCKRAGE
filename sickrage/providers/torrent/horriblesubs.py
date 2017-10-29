# Author: Mr_Orange <mr_orange@hotmail.it>
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, try_int
from sickrage.providers import TorrentProvider


class HorribleSubsProvider(TorrentProvider):
    def __init__(self):

        super(HorribleSubsProvider, self).__init__("HorribleSubs", 'http://horriblesubs.info', False)

        self.supports_absolute_numbering = True
        self.anime_only = True

        self.minseed = None
        self.minleech = None

        self.urls.update({
            'search': '{base_url}/lib/search.php'.format(**self.urls),
            'rss': '{base_url}/lib/latest.php'.format(**self.urls)
        })

        self.cache = TVCache(self, min_time=15)

    def search(self, search_strings, age=0, ep_obj=None):
        results = []

        search_params = {
            "nextid": 0
        }

        for mode in search_strings.keys():
            sickrage.srCore.srLogger.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug("Search string: " + search_string)
                    search_params["value"] = search_string

                searchURL = self.urls[('search', 'rss')[mode == 'RSS']]

                try:
                    data = sickrage.srCore.srWebSession.get(searchURL, params=search_params).text
                except Exception:
                    sickrage.srCore.srLogger.debug("No data returned from provider")
                    continue

                with bs4_parser(data) as html:
                    torrent_tables = html.find_all('table', class_='release-table')

                    torrent_rows = []
                    for torrent_table in torrent_tables:
                        curr_torrent_rows = torrent_table('tr') if torrent_table else []
                        torrent_rows.extend(curr_torrent_rows)

                    # Continue only if one Release is found
                    if len(torrent_rows) < 1:
                        sickrage.srCore.srLogger.debug("Data returned from provider does not contain any torrents")
                        continue

                    for torrent_row in torrent_rows:
                        try:
                            label = torrent_row.find('td', class_='dl-label')
                            title = label.get_text(strip=True)

                            size = -1
                            seeders = 1
                            leechers = 1

                            link = torrent_row.find('td', class_='hs-torrent-link')
                            download_url = link.find('a')['href'] if link and link.find('a') else None

                            if not download_url:
                                # fallback to magnet link
                                link = torrent_row.find('td', class_='hs-magnet-link')
                                download_url = link.find('a')['href'] if link and link.find('a') else None

                        except StandardError:
                            continue

                        if not all([title, download_url]):
                            continue

                        item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders,
                                'leechers': leechers, 'hash': ''}

                        if mode != 'RSS':
                            sickrage.srCore.srLogger.debug("Found result: {}".format(title))

                        results.append(item)

        # Sort all the items by seeders if available
        results.sort(key=lambda k: try_int(k.get('seeders', 0)), reverse=True)

        return results
