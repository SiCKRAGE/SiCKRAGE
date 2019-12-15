# coding=utf-8
# Author: ellmout <ellmout@ellmout.net>
# Inspired from : adaur <adaur.underground@gmail.com> (ABNormal)
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

from requests.compat import urljoin
from requests.utils import dict_from_cookiejar

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, try_int, convert_size
from sickrage.providers import TorrentProvider


class ArcheTorrentProvider(TorrentProvider):
    def __init__(self):
        super(ArcheTorrentProvider, self).__init__('ArcheTorrent', 'https://www.archetorrent.com', True)
        # Credentials
        self.username = None
        self.password = None

        # Torrent Stats
        self.minseed = None
        self.minleech = None

        # Freelech
        self.freeleech = False

        # URLs
        self._urls.update({
            'login': '{base_url}/account-login.php'.format(**self._urls),
            'search': '{base_url}/torrents-search.php'.format(**self._urls),
            'download': '{base_url}/download.php'.format(**self._urls),
        })

        # Proper Strings
        self.proper_strings = ['PROPER']

        # Cache
        self.cache = TVCache(self, min_time=15)

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {
            'username': self.username,
            'password': self.password,
            'returnto': '/index.php'
        }

        try:
            self.session.post(self.urls['login'], data=login_params)
            search = self.session.get(self.urls['search']).text
        except Exception:
            sickrage.app.log.warning('Unable to connect to provider')
            return False

        if not re.search('torrents.php', search):
            sickrage.app.log.warning('Invalid username or password. Check your settings')
            return False

        return True

    def search(self, search_strings, age=0, show_id=None, season=None, episode=None, **kwargs):
        results = []

        if not self.login():
            return results

        freeleech = '2' if self.freeleech else '0'

        # Search Params
        # c59=1&c73=1&c5=1&c41=1&c60=1&c66=1&c65=1&c67=1&c62=1&c64=1&c61=1&search=Good+Behavior+S01E01&cat=0&incldead=0&freeleech=0&lang=0
        search_params = {
            'c5': '1',  # Category: Series - DVDRip
            'c41': '1',  # Category: Series - HD
            'c60': '1',  # Category: Series - Pack TV
            'c62': '1',  # Category: Series - BDRip
            'c64': '1',  # Category: Series - VOSTFR
            'c65': '1',  # Category: Series - TV 720p
            'c66': '1',  # Category: Series - TV 1080p
            'c67': '1',  # Category: Series - Pack TV HD
            'c73': '1',  # Category: Anime
            'incldead': '0',  # Include dead torrent - 0: off 1: yes 2: only dead
            'freeleech': freeleech,  # Only freeleech torrent - 0: off 1: no freeleech 2: Only freeleech
            'lang': '0'  # Langugage - 0: off 1: English 2: French ....
        }

        for mode in search_strings:
            sickrage.app.log.debug('Search Mode: {0}'.format(mode))
            for search_string in search_strings[mode]:
                sickrage.app.log.debug('Search String: {0} for mode {1}'.format(search_strings[mode], mode))

                if mode != 'RSS':
                    sickrage.app.log.debug('Search string: {0}'.format(search_string))

                search_params['search'] = re.sub(r'[()]', '', search_string)

                try:
                    data = self.session.get(self.urls['search'], params=search_params).text
                    results += self.parse(data, mode)
                except Exception:
                    sickrage.app.log.debug('No data returned from provider')

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
            torrent_table = html.find(class_='ttable_headinner')
            torrent_rows = torrent_table('tr') if torrent_table else []

            # Continue only if at least one Release is found
            if len(torrent_rows) < 2:
                sickrage.app.log.debug('Data returned from provider does not contain any torrents')
                return results

            # Catégorie, Release, Date, DL, Size, C, S, L
            labels = [label.get_text(strip=True) for label in torrent_rows[0]('th')]

            # Skip column headers
            for result in torrent_rows[1:]:
                try:
                    cells = result('td')
                    if len(cells) < len(labels):
                        continue

                    id = re.search('id=([0-9]+)', cells[labels.index('Nom')].find('a')['href']).group(1)
                    title = cells[labels.index('Nom')].get_text(strip=True)
                    download_url = urljoin(self.urls['download'], '?id={0}&name={1}'.format(id, title))
                    if not all([title, download_url]):
                        continue

                    seeders = try_int(cells[labels.index('S')].get_text(strip=True))
                    leechers = try_int(cells[labels.index('L')].get_text(strip=True))

                    size_index = labels.index('Size') if 'Size' in labels else labels.index('Taille')
                    torrent_size = cells[size_index].get_text()
                    size = convert_size(torrent_size, -1)

                    results += [
                        {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                    ]

                    if mode != 'RSS':
                        sickrage.app.log.debug('Found result: {}'.format(title))
                except Exception:
                    sickrage.app.log.error('Failed parsing provider')

        return results
