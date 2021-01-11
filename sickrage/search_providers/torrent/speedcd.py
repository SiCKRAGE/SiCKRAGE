# Author: Mr_Orange
# URL: https://github.com/mr-orange/Sick-Beard
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


from urllib.parse import urljoin

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, try_int, convert_size
from sickrage.search_providers import TorrentProvider


class SpeedCDProvider(TorrentProvider):
    def __init__(self):
        super(SpeedCDProvider, self).__init__("Speedcd", 'https://speed.cd', True)

        self._urls.update({
            'login': '{base_url}/login.php'.format(**self._urls),
            'search': '{base_url}/browse.php'.format(**self._urls),
        })

        # custom settings
        self.custom_settings = {
            # 'username': '',
            # 'password': '',
            'freeleech': False,
            'minseed': 0,
            'minleech': 0
        }

        self.enable_cookies = True
        self.required_cookies = ('inSpeed_uid', 'inSpeed_speedian')

        self.proper_strings = ['PROPER', 'REPACK', 'REAL', 'RERIP']

        self.cache = TVCache(self, min_time=20)

    # def login(self):
    #     return self.cookie_login('log in')

    def login(self):
        return self.cookie_login('loginform')

        # if any(dict_from_cookiejar(self.session.cookies).values()):
        #     return True
        #
        # login_params = {
        #     'username': self.username,
        #     'password': self.password
        # }
        #
        # try:
        #     with bs4_parser(self.session.get(self.urls['login']).text) as html:
        #         login_url = urljoin(self.urls['base_url'], html.find('form', id='loginform').get('action'))
        #         response = self.session.post(login_url, data=login_params, timeout=30).text
        # except Exception as e:
        #     sickrage.app.log.warning("Unable to connect to provider")
        #     self.session.cookies.clear()
        #     return False
        #
        # if 'logout.php' not in response.lower():
        #     sickrage.app.log.warning("Invalid username or password, check your settings.")
        #     self.session.cookies.clear()
        #     return False
        #
        # return True

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []

        if not self.login():
            return results

        # http://speed.cd/browse.php?c49=1&c50=1&c52=1&c41=1&c55=1&c2=1&c30=1&freeleech=on&search=arrow&d=on
        # Search Params
        search_params = {
            'c2': 1,  # TV/Episodes
            'c30': 1,  # Anime
            'c41': 1,  # TV/Packs
            'c49': 1,  # TV/HD
            'c50': 1,  # TV/Sports
            'c52': 1,  # TV/B-Ray
            'c55': 1,  # TV/Kids
            'search': '',
            'freeleech': 'on' if self.custom_settings['freeleech'] else None
        }

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: %s " % search_string)

                search_params['search'] = search_string

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

        with bs4_parser(data) as html:
            torrent_table = html.find('div', class_='boxContent')
            torrent_table = torrent_table.find('table') if torrent_table else None
            torrent_rows = torrent_table('tr') if torrent_table else []

            # Continue only if at least one release is found
            if len(torrent_rows) < 2:
                sickrage.app.log.debug('Data returned from provider does not contain any torrents')
                return results

            # Skip column headers
            for row in torrent_rows[1:]:
                cells = row('td')

                try:
                    title = cells[1].find('a').get_text()
                    download_url = urljoin(self.urls['base_url'], cells[2].find(title='Download').parent['href'])
                    if not all([title, download_url]):
                        continue

                    seeders = try_int(cells[6].get_text(strip=True))
                    leechers = try_int(cells[7].get_text(strip=True))

                    torrent_size = cells[4].get_text()
                    torrent_size = torrent_size[:-2] + ' ' + torrent_size[-2:]
                    size = convert_size(torrent_size, -1)

                    results += [{
                        'title': title,
                        'link': download_url,
                        'size': size,
                        'seeders': seeders,
                        'leechers': leechers
                    }]

                    if mode != 'RSS':
                        sickrage.app.log.debug("Found result: {}".format(title))

                except (AttributeError, TypeError, KeyError, ValueError, IndexError):
                    sickrage.app.log.error('Failed parsing provider.')

        return results
