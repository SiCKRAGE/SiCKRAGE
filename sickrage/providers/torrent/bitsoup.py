# Author: Idan Gutman
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
from sickrage.core.helpers import bs4_parser, try_int
from sickrage.providers import TorrentProvider


class BitSoupProvider(TorrentProvider):
    def __init__(self):
        super(BitSoupProvider, self).__init__("BitSoup", 'http://www.bitsoup.me', True)

        self.urls.update({
            'login': '{base_url}/takelogin.php'.format(**self.urls),
            'detail': '{base_url}/details.php?id=%s'.format(**self.urls),
            'search': '{base_url}/browse.php'.format(**self.urls),
            'download': '{base_url}/%s'.format(**self.urls)
        })

        self.username = None
        self.password = None

        self.minseed = None
        self.minleech = None

        self.cache = TVCache(self, min_time=20)

    def _check_auth(self):
        if not self.username or not self.password:
            sickrage.srCore.srLogger.warning(
                "[{}]: Invalid username or password. Check your settings".format(self.name))

        return True

    def login(self):

        login_params = {
            'username': self.username,
            'password': self.password,
            'ssl': 'yes'
        }

        try:
            response = sickrage.srCore.srWebSession.post(self.urls['login'], data=login_params, timeout=30).text
        except Exception:
            sickrage.srCore.srLogger.warning("[{}]: Unable to connect to provider".format(self.name))
            return False

        if re.search('Username or password incorrect', response):
            sickrage.srCore.srLogger.warning(
                "[{}]: Invalid username or password. Check your settings".format(self.name))
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):
        results = []

        search_params = {
            "c42": 1, "c45": 1, "c49": 1, "c7": 1
        }

        if not self.login():
            return results

        for mode in search_strings.keys():
            sickrage.srCore.srLogger.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug("Search string: %s " % search_string)

                search_params['search'] = search_string

                try:
                    data = sickrage.srCore.srWebSession.get(self.urls['search'], search_params).text
                    results += self.parse(data, mode)
                except Exception:
                    sickrage.srCore.srLogger.debug("No data returned from provider")

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

        with bs4_parser(data) as html:
            torrent_table = html.find('table', attrs={'class': 'koptekst'})
            torrent_rows = torrent_table.find_all('tr') if torrent_table else []

            # Continue only if one Release is found
            if len(torrent_rows) < 2:
                sickrage.srCore.srLogger.debug("Data returned from provider does not contain any torrents")
                return results

            for row in torrent_rows[1:]:
                try:
                    cells = row.find_all('td')

                    link = cells[1].find('a')
                    download_url = self.urls['download'] % cells[2].find('a')['href']

                    try:
                        title = link.getText()
                        seeders = int(cells[10].getText())
                        leechers = int(cells[11].getText())
                        # FIXME
                        size = -1
                    except (AttributeError, TypeError):
                        continue

                    if not all([title, download_url]):
                        continue

                        # Filter unseeded torrent
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode != 'RSS':
                            sickrage.srCore.srLogger.debug(
                                "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                    title, seeders, leechers))
                        continue

                    item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders,
                            'leechers': leechers, 'hash': ''}

                    if mode != 'RSS':
                        sickrage.srCore.srLogger.debug("Found result: {}".format(title))

                    results.append(item)
                except Exception:
                    sickrage.srCore.srLogger.error("Failed parsing provider")