# Author: Nick Sologoub
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
from urllib import parse

from requests.utils import dict_from_cookiejar

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, convert_size
from sickrage.search_providers import TorrentProvider


class PretomeProvider(TorrentProvider):
    def __init__(self):
        super(PretomeProvider, self).__init__("Pretome", 'https://pretome.info', True)

        self._urls.update({
            'login': '{base_url}/takelogin.php'.format(**self._urls),
            'detail': '{base_url}/details.php?id=%s'.format(**self._urls),
            'search': '{base_url}/browse.php?search=%s%s'.format(**self._urls),
            'download': '{base_url}/download.php/%s/%s.torrent'.format(**self._urls)
        })

        # custom settings
        self.custom_settings = {
            'username': '',
            'password': '',
            'pin': '',
            'minseed': 0,
            'minleech': 0
        }

        self.categories = "&st=1&cat%5B%5D=7"

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = TVCache(self, min_time=30)

    def _check_auth(self):

        if not self.custom_settings['username'] or not self.custom_settings['password'] or not self.custom_settings['pin']:
            sickrage.app.log.warning("Invalid username or password or pin. Check your settings")

        return True

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {'username': self.custom_settings['username'],
                        'password': self.custom_settings['password'],
                        'login_pin': self.custom_settings['pin']}

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

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []

        if not self.login():
            return results

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: %s " % search_string)

                search_url = self.urls['search'] % (parse.quote(search_string), self.categories)

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

        with bs4_parser(data) as html:
            # Continue only if one Release is found
            empty = html.find('h2', text="No .torrents fit this filter criteria")
            if empty:
                sickrage.app.log.debug("Data returned from provider does not contain any torrents")
                return results

            torrent_table = html.find('table', attrs={'style': 'border: none; width: 100%;'})
            if not torrent_table:
                sickrage.app.log.debug("Could not find table of torrents")
                return results

            torrent_rows = torrent_table.find_all('tr', attrs={'class': 'browse'})

            for result in torrent_rows:
                cells = result.find_all('td')
                size = None
                link = cells[1].find('a', attrs={'style': 'font-size: 1.25em; font-weight: bold;'})

                torrent_id = link['href'].replace('details.php?id=', '')

                try:
                    if 'title' in link:
                        title = link['title']
                    else:
                        title = link.contents[0]

                    download_url = self.urls['download'] % (torrent_id, link.contents[0])
                    seeders = int(cells[9].contents[0])
                    leechers = int(cells[10].contents[0])

                    # Need size for failed downloads handling
                    if size is None:
                        if re.match(r'[0-9]+,?\.?[0-9]*[KkMmGg]+[Bb]+', cells[7].text):
                            size = convert_size(cells[7].text, -1)

                    if not all([title, download_url]):
                        continue

                    results += [
                        {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                    ]

                    if mode != 'RSS':
                        sickrage.app.log.debug("Found result: {}".format(title))
                except Exception:
                    sickrage.app.log.error("Failed parsing provider.")

        return results
