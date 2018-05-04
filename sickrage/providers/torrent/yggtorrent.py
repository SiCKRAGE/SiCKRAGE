# coding=utf-8
# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage
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


class YggtorrentProvider(TorrentProvider):
    def __init__(self):
        """Initialize the class."""
        super(YggtorrentProvider, self).__init__('Yggtorrent', 'https://ww1.yggtorrent.com', True)

        # URLs
        self.urls.update({
            'login': '{base_url}/user/login'.format(**self.urls),
            'search': '{base_url}/engine/search'.format(**self.urls),
        })

        # Credentials
        self.username = None
        self.password = None

        # Proper Strings
        self.proper_strings = ['PROPER', 'REPACK', 'REAL', 'RERIP']

        # Miscellaneous Options
        self.translation = {
            'seconde': 'second',
            'secondes': 'seconds',
            'minute': 'minute',
            'minutes': 'minutes',
            'heure': 'hour',
            'heures': 'hours',
            'jour': 'day',
            'jours': 'days',
            'mois': 'month',
            'an': 'year',
            'année': 'year',
            'ans': 'years',
            'années': 'years'
        }

        # Torrent Stats
        self.minseed = None
        self.minleech = None

        # Cache
        self.cache = TVCache(self, min_time=30)

    def search(self, search_strings, age=0, ep_obj=None, **kwargs):
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
            'category': 2145
        }

        for mode in search_strings:
            sickrage.app.log.debug('Search mode: {}'.format(mode))
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug('Search string: {}'.format(search_string))

                search_params['q'] = re.sub(r'[()]', '', search_string)

                try:
                    data = self.session.get(self.urls['search'], params=search_params).text
                    results += self.parse(data, mode)
                except Exception:
                    sickrage.app.log.debug('No data returned from provider')

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
            torrent_table = html.find(class_='table table-striped')
            torrent_rows = torrent_table('tr') if torrent_table else []

            # Continue only if at least one Release is found
            if len(torrent_rows) < 2:
                sickrage.app.log.debug('Data returned from provider does not contain any torrents')
                return results

            # Skip column headers
            for result in torrent_rows[1:]:
                cells = result('td')
                if len(cells) < 5:
                    continue

                try:
                    title = cells[0].find('a', class_='torrent-name').get_text(strip=True)
                    download_url = cells[0].find_all('a')[2]['href']
                    if not (title and download_url):
                        continue

                    seeders = try_int(cells[4].get_text(strip=True), 1)
                    leechers = try_int(cells[5].get_text(strip=True), 0)

                    torrent_size = cells[3].get_text()
                    size = convert_size(torrent_size, -1)

                    results += [
                        {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                    ]

                    if mode != 'RSS':
                        sickrage.app.log.debug("Found result: {}".format(title))
                except Exception:
                    sickrage.app.log.error('Failed parsing provider.')

        return results

    def login(self):
        """Login method used for logging in before doing search and torrent downloads."""
        login_params = {
            'id': self.username,
            'pass': self.password,
            'submit': ''
        }

        try:
            self.session.post(self.urls['login'], data=login_params)
            response = self.session.get(self.urls['base_url']).text
        except Exception:
            sickrage.app.log.warning('Unable to connect to provider')
            return False

        if 'Ces identifiants sont invalides' in response:
            sickrage.app.log.warning('Invalid username or password. Check your settings')
            return False

        if 'Mon compte' not in response:
            sickrage.app.log.warning('Unable to login to provider')
            return False

        return True


provider = YggtorrentProvider()
