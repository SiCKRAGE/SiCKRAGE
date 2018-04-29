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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from urlparse import urljoin

from requests.utils import dict_from_cookiejar

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, convert_size, try_int
from sickrage.providers import TorrentProvider


class TorrentLeechProvider(TorrentProvider):
    def __init__(self):
        super(TorrentLeechProvider, self).__init__("TorrentLeech", 'https://www.torrentleech.org', True)

        self.urls.update({
            'login': '{base_url}/user/account/login/'.format(**self.urls),
            'search': '{base_url}/torrents/browse'.format(**self.urls),
        })

        self.username = None
        self.password = None

        self.minseed = None
        self.minleech = None

        self.proper_strings = ['PROPER', 'REPACK', 'REAL', 'RERIP']

        self.cache = TVCache(self, min_time=20)

    def login(self):
        cookies = dict_from_cookiejar(self.session.cookies)
        if any(cookies.values()) and cookies.get('member_id'):
            return True

        login_params = {
            'username': self.username,
            'password': self.password,
            'login': 'submit',
            'remember_me': 'on',
        }

        try:
            response = self.session.post(self.urls['login'], data=login_params, timeout=30).text
        except Exception:
            sickrage.app.log.warning("Unable to connect to provider")
            return False

        if '<title>Login :: TorrentLeech.org</title>' in response:
            sickrage.app.log.warning("Invalid username or password. Check your settings")
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):
        results = []

        if not self.login():
            return results

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: %s" % search_string)

                    categories = ["2", "7", "35"]
                    categories += ["26", "32", "44"] if mode == "Episode" else ["27"]
                    if ep_obj.show and ep_obj.show.is_anime:
                        categories += ["34"]
                else:
                    categories = ["2", "26", "27", "32", "7", "34", "35", "44"]

                search_params = {
                    "categories": ",".join(categories),
                    "query": search_string
                }

                try:
                    data = self.session.get(self.urls["search"], params=search_params).text
                    results += self.parse(data, mode)
                except Exception:
                    sickrage.app.log.debug("No data returned from provider")

        return results

    def parse(self, data, mode):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []

        def process_column_header(td):
            result = ''
            if td.a:
                result = td.a.get('title')
            if not result:
                result = td.get_text(strip=True)
            return result

        with bs4_parser(data) as html:
            torrent_table = html.find('table', id='torrenttable')
            torrent_rows = torrent_table('tr') if torrent_table else []

            # Continue only if one Release is found
            if len(torrent_rows) < 2:
                sickrage.app.log.debug("Data returned from provider does not contain any torrents")
                return results

            labels = [process_column_header(label) for label in torrent_rows[0]('th')]

            for row in torrent_rows[1:]:
                cells = row('td')

                try:
                    name = cells[labels.index('Name')]
                    title = name.find('a').get_text(strip=True)
                    download_url = row.find('td', class_='quickdownload').find('a')
                    if not all([title, download_url]):
                        continue

                    download_url = urljoin(self.urls['base_url'], download_url['href'])

                    seeders = try_int(cells[labels.index('Seeders')].get_text(strip=True), 0)
                    leechers = try_int(cells[labels.index('Leechers')].get_text(strip=True), 0)

                    size = convert_size(cells[labels.index('Size')].get_text(), -1)

                    results += [
                        {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                    ]

                    if mode != 'RSS':
                        sickrage.app.log.debug("Found result: {}".format(title))
                except Exception:
                    sickrage.app.log.error("Failed parsing provider.")

        return results
