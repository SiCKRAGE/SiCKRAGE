# Author: Idan Gutman
# Modified by jkaberg, https://github.com/jkaberg for SceneAccess
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import re
from urllib.parse import urljoin

from requests.utils import dict_from_cookiejar

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, convert_size, try_int
from sickrage.search_providers import TorrentProvider


class HDTorrentsProvider(TorrentProvider):
    def __init__(self):
        super(HDTorrentsProvider, self).__init__("HDTorrents", 'https://hd-torrents.org', True)

        self._urls.update({
            'login': '{base_url}/login.php'.format(**self._urls),
            'search': '{base_url}/torrents.php'.format(**self._urls)
        })

        # custom settings
        self.custom_settings = {
            'username': '',
            'password': '',
            'freeleech': False,
            'minseed': 0,
            'minleech': 0
        }

        self.proper_strings = ['PROPER', 'REPACK', 'REAL', 'RERIP']

        self.cache = TVCache(self, min_time=30)

    def _check_auth(self):
        if not self.custom_settings['username'] or not self.custom_settings['password']:
            sickrage.app.log.warning(
                "Invalid username or password. Check your settings")

        return True

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {'uid': self.custom_settings['username'],
                        'pwd': self.custom_settings['password'],
                        'submit': 'Confirm'}

        try:
            response = self.session.post(self.urls['login'], data=login_params, timeout=30).text
        except Exception:
            sickrage.app.log.warning("Unable to connect to provider")
            return False

        if re.search('You need cookies enabled to log in.', response):
            sickrage.app.log.warning(
                "Invalid username or password. Check your settings")
            return False

        return True

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []

        if not self.login():
            return results

        # Search Params
        search_params = {
            'search': '',
            'active': 5 if self.custom_settings['freeleech'] else 1,
            'options': 0,
            'category[0]': 59,
            'category[1]': 60,
            'category[2]': 30,
            'category[3]': 38,
            'category[4]': 65,
        }

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    search_params['search'] = search_string
                    sickrage.app.log.debug("Search string: %s" % search_string)

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

        # Search result page contains some invalid html that prevents html parser from returning all data.
        # We cut everything before the table that contains the data we are interested in thus eliminating
        # the invalid html portions
        try:
            index = data.lower().index('<table class="mainblockcontenttt"')
        except ValueError:
            sickrage.app.log.debug("Could not find table of torrents mainblockcontenttt")
            return results

        with bs4_parser(data[index:]) as html:
            torrent_table = html.find('table', class_='mainblockcontenttt')
            torrent_rows = torrent_table('tr') if torrent_table else []

            if not torrent_rows or torrent_rows[2].find('td', class_='lista'):
                sickrage.app.log.debug('Data returned from provider does not contain any torrents')
                return results

            # Cat., Active, Filename, Dl, Wl, Added, Size, Uploader, S, L, C
            labels = [label.a.get_text(strip=True) if label.a else label.get_text(strip=True) for label in
                      torrent_rows[0]('td')]

            # Skip column headers
            for row in torrent_rows[1:]:
                try:
                    cells = row.findChildren('td')[:len(labels)]
                    if len(cells) < len(labels):
                        continue

                    title = cells[labels.index('Filename')].a
                    title = title.get_text(strip=True) if title else None
                    link = cells[labels.index('Dl')].a
                    link = link.get('href') if link else None
                    download_url = urljoin(self.urls['base_url'], link) if link else None
                    if not all([title, download_url]):
                        continue

                    seeders = try_int(cells[labels.index('S')].get_text(strip=True))
                    leechers = try_int(cells[labels.index('L')].get_text(strip=True))
                    torrent_size = cells[labels.index('Size')].get_text()
                    size = convert_size(torrent_size, -1, ['B', 'KIB', 'MIB', 'GIB', 'TIB', 'PIB'])

                    results += [
                        {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                    ]

                    if mode != 'RSS':
                        sickrage.app.log.debug("Found result: {}".format(title))
                except Exception:
                    sickrage.app.log.error("Failed parsing provider")

        return results
