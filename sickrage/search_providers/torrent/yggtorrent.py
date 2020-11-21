# coding=utf-8
# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage
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


class YggtorrentProvider(TorrentProvider):
    def __init__(self):
        """Initialize the class."""
        super(YggtorrentProvider, self).__init__('Yggtorrent', 'https://www2.yggtorrent.si', True)

        # URLs
        self._urls.update({
            'auth': '{base_url}/user/ajax_usermenu'.format(**self._urls),
            'login': '{base_url}/user/login'.format(**self._urls),
            'search': '{base_url}/engine/search'.format(**self._urls),
            'download': '{base_url}/engine/download_torrent?id=%s'.format(**self._urls)
        })

        # custom settings
        self.custom_settings = {
            'username': '',
            'password': '',
            'minseed': 0,
            'minleech': 0
        }

        # Proper Strings
        self.proper_strings = ['PROPER', 'REPACK', 'REAL', 'RERIP']

        # Cache
        self.cache = TVCache(self, min_time=20)

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        """
        Search a provider and parse the results.

        :param search_strings: A dict with mode (key) and the search value (value)
        :param age: Not used
        :param ep_obj: Not used
        :returns: A list of search results (structure)
        """
        results = []

        if not self.login():
            return results

        # Search Params
        search_params = {
            'category': 2145,
            'do': 'search'
        }

        for mode in search_strings:
            sickrage.app.log.debug('Search mode: {}'.format(mode))
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug('Search string: {}'.format(search_string))

                search_params['name'] = re.sub(r'[()]', '', search_string)

                resp = self.session.get(self.urls['search'], params=search_params)
                if not resp or not resp.text:
                    sickrage.app.log.debug('No data returned from provider')
                    continue

                results += self.parse(resp.text, mode)

        return results

    def parse(self, data, mode, **kwargs):
        """
        Parse search results for items.

        :param data: The raw response from a search
        :param mode: The current mode used to search, e.g. RSS

        :return: A list of items found
        """
        results = []

        with bs4_parser(data) as html:
            torrent_table = html.find(class_='table-responsive results')
            torrent_rows = torrent_table('tr') if torrent_table else []

            # Continue only if at least one Release is found
            if len(torrent_rows) < 2:
                sickrage.app.log.debug('Data returned from provider does not contain any torrents')
                return results

            for result in torrent_rows[1:]:
                cells = result('td')
                if len(cells) < 9:
                    continue

                try:
                    info = cells[1].find('a')
                    title = info.get_text(strip=True)
                    download_url = info.get('href')
                    if not (title and download_url):
                        continue

                    torrent_id = re.search(r'/(\d+)-', download_url)
                    download_url = self.urls['download'] % torrent_id.group(1)

                    seeders = try_int(cells[7].get_text(strip=True), 0)
                    leechers = try_int(cells[8].get_text(strip=True), 0)

                    torrent_size = cells[5].get_text()
                    size = convert_size(torrent_size, -1, ['O', 'KO', 'MO', 'GO', 'TO', 'PO'])

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

    def login(self):
        """Login method used for logging in before doing search and torrent downloads."""
        login_params = {
            'id': self.custom_settings['username'],
            'pass': self.custom_settings['password']
        }

        if not self._is_authenticated():
            resp = self.session.post(self.urls['login'], data=login_params)
            if not resp:
                sickrage.app.log.warning('Unable to connect or login to provider')
                return False

            if not resp.ok and resp.status_code == 401:
                sickrage.app.log.warning('Invalid username or password. Check your settings')
                return False

            if not self._is_authenticated():
                sickrage.app.log.warning('Unable to connect or login to provider')
                return False

        return True

    def _is_authenticated(self):
        try:
            self.session.get(self.urls['auth'], params={'attempt': 1}).json()
        except Exception:
            return False
        return True
