# coding=utf-8
# Author: Bart Sommer <bart.sommer88@gmail.com>
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

from requests.utils import dict_from_cookiejar

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.exceptions import AuthException
from sickrage.core.helpers import bs4_parser, try_int, convert_size
from sickrage.search_providers import TorrentProvider


class ImmortalseedProvider(TorrentProvider):
    def __init__(self):
        super(ImmortalseedProvider, self).__init__('Immortalseed', 'https://immortalseed.me', True)

        # URLs
        self._urls.update({
            'login': '{base_url}/takelogin.php'.format(**self._urls),
            'search': '{base_url}/browse.php'.format(**self._urls),
            'rss': '{base_url}/rss.php'.format(**self._urls),
        })

        # custom settings
        self.custom_settings = {
            'username': '',
            'password': '',
            'passkey': '',
            'freeleech': False,
            'minseed': 0,
            'minleech': 0
        }

        # Proper Strings
        self.proper_strings = ['PROPER', 'REPACK']

        # Cache
        self.cache = ImmortalseedCache(self, min_time=20)

    def _check_auth(self):
        if not self.custom_settings['username'] or not self.custom_settings['password']:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def _check_auth_from_data(self, data):
        if not self.custom_settings['passkey']:
            sickrage.app.log.warning('Invalid passkey. Check your settings')

        return True

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {
            'username': self.custom_settings['username'],
            'password': self.custom_settings['password'],
        }

        try:
            response = self.session.post(self.urls['login'], data=login_params).text
        except Exception:
            sickrage.app.log.warning("Unable to connect to provider")
            return False

        if re.search('Username or password incorrect!', response):
            sickrage.app.log.warning("Invalid username or password. Check your settings")
            return False

        return True

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []
        if not self.login():
            return results

        # Search Params
        search_params = {
            'do': 'search',
            'include_dead_torrents': 'no',
            'search_type': 't_name',
            'category': 0,
            'keywords': ''
        }

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: {0}".format(mode))
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: {0}".format(search_string))
                    search_params['keywords'] = search_string

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

        def process_column_header(td):
            td_title = ''
            if td.img:
                td_title = td.img.get('title', td.get_text(strip=True))
            if not td_title:
                td_title = td.get_text(strip=True)
            return td_title

        with bs4_parser(data) as html:
            torrent_table = html.find('table', id='sortabletable')
            torrent_rows = torrent_table('tr') if torrent_table else []

            # Continue only if at least one Release is found
            if len(torrent_rows) < 2:
                sickrage.app.log.debug("Data returned from provider does not contain any torrents")
                return results

            labels = [process_column_header(label) for label in torrent_rows[0]('td')]

            # Skip column headers
            for result in torrent_rows[1:]:
                try:
                    tooltip = result.find('div', class_='tooltip-target')
                    if not tooltip:
                        continue

                    title = tooltip.get_text(strip=True)

                    # skip if torrent has been nuked due to poor quality
                    if title.startswith('Nuked.'):
                        continue

                    download_url = result.find('img', title='Click to Download this Torrent in SSL!').parent['href']
                    if not all([title, download_url]):
                        continue

                    cells = result('td')
                    seeders = try_int(cells[labels.index('Seeders')].get_text(strip=True))
                    leechers = try_int(cells[labels.index('Leechers')].get_text(strip=True))
                    torrent_size = cells[labels.index('Size')].get_text(strip=True)
                    size = convert_size(torrent_size, -1)

                    results += [
                        {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                    ]

                    if mode != 'RSS':
                        sickrage.app.log.debug("Found result: {}".format(title))
                except Exception:
                    sickrage.app.log.error("Failed parsing provider")

        return results


class ImmortalseedCache(TVCache):
    def _get_rss_data(self):
        params = {
            'secret_key': self.provider.custom_settings['passkey'],
            'feedtype': 'downloadssl',
            'timezone': '-5',
            'categories': '44,32,7,47,8,48,9',
            'showrows': '50',
        }

        return self.get_rss_feed(self.provider.urls['rss'], params=params)

    def _check_auth(self, data):
        return self.provider._check_auth_from_data(data)
