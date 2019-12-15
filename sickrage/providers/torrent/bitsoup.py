# Author: Idan Gutman
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

from requests.utils import dict_from_cookiejar

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser
from sickrage.providers import TorrentProvider


class BitSoupProvider(TorrentProvider):
    def __init__(self):
        super(BitSoupProvider, self).__init__("BitSoup", 'https://www.bitsoup.me', True)

        self._urls.update({
            'login': '{base_url}/takelogin.php'.format(**self._urls),
            'detail': '{base_url}/details.php?id=%s'.format(**self._urls),
            'search': '{base_url}/browse.php'.format(**self._urls),
            'download': '{base_url}/%s'.format(**self._urls)
        })

        self.username = None
        self.password = None

        self.minseed = None
        self.minleech = None

        self.cache = TVCache(self, min_time=20)

    def _check_auth(self):
        if not self.username or not self.password:
            sickrage.app.log.warning(
                "Invalid username or password. Check your settings")

        return True

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {
            'username': self.username,
            'password': self.password,
            'ssl': 'yes'
        }

        try:
            response = self.session.post(self.urls['login'], data=login_params, timeout=30).text
        except Exception:
            sickrage.app.log.warning("Unable to connect to provider")
            return False

        if re.search('Username or password incorrect', response):
            sickrage.app.log.warning(
                "Invalid username or password. Check your settings")
            return False

        return True

    def search(self, search_strings, age=0, show_id=None, season=None, episode=None, **kwargs):
        results = []

        search_params = {
            "c42": 1, "c45": 1, "c49": 1, "c7": 1
        }

        if not self.login():
            return results

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: %s " % search_string)

                search_params['search'] = search_string

                try:
                    data = self.session.get(self.urls['search'], search_params).text
                    results += self.parse(data, mode)
                except Exception:
                    sickrage.app.log.debug("No data returned from provider")

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
            torrent_table = html.find('table', attrs={'class': 'koptekst'})
            torrent_rows = torrent_table.find_all('tr') if torrent_table else []

            # Continue only if one Release is found
            if len(torrent_rows) < 2:
                sickrage.app.log.debug("Data returned from provider does not contain any torrents")
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

                    results += [
                        {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                    ]

                    if mode != 'RSS':
                        sickrage.app.log.debug("Found result: {}".format(title))
                except Exception:
                    sickrage.app.log.error("Failed parsing provider")

        return results
