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
from urllib.parse import urlencode

from requests.utils import dict_from_cookiejar

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.exceptions import AuthException
from sickrage.core.helpers import bs4_parser
from sickrage.search_providers import TorrentProvider


class NebulanceProvider(TorrentProvider):
    def __init__(self):
        super(NebulanceProvider, self).__init__("Nebulance", 'https://nebulance.io', True)

        # custom settings
        self.custom_settings = {
            'username': '',
            'password': '',
            'minseed': 0,
            'minleech': 0
        }

        self.cache = TVCache(self, min_time=20)

    def _check_auth(self):
        if not self.custom_settings['username'] or not self.custom_settings['password']:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {
            'uid': self.custom_settings['username'],
            'pwd': self.custom_settings['password'],
            'remember_me': 'on',
            'login': 'submit'
        }

        try:
            response = self.session.post(self.urls['base_url'], params={'page': 'login'}, data=login_params, timeout=30).text
        except Exception:
            sickrage.app.log.warning("Unable to connect to provider")
            return False

        if re.search('Username Incorrect', response) or re.search('Password Incorrect', response):
            sickrage.app.log.warning(
                "Invalid username or password. Check your settings")
            return False

        return True

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []

        if not self.login():
            return results

        search_params = {
            "page": 'torrents',
            "category": 0,
            "active": 1
        }

        for mode in search_strings:
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: %s " % search_string)

                search_url = self.urls['base_url'] + "?" + urlencode(search_params)

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
            torrent_rows = []

            down_elems = html.findAll("img", {"alt": "Download Torrent"})
            for down_elem in down_elems:
                if down_elem:
                    torr_row = down_elem.findParent('tr')
                    if torr_row:
                        torrent_rows.append(torr_row)

            # Continue only if one Release is found
            if len(torrent_rows) < 1:
                sickrage.app.log.debug("Data returned from provider does not contain any torrents")
                return results

            for torrent_row in torrent_rows:
                try:
                    title = torrent_row.find('a', {"data-src": True})['data-src'].rsplit('.', 1)[0]
                    download_href = torrent_row.find('img', {"alt": 'Download Torrent'}).findParent()['href']
                    seeders = int(
                        torrent_row.findAll('a', {'title': 'Click here to view peers details'})[
                            0].text.strip())
                    leechers = int(
                        torrent_row.findAll('a', {'title': 'Click here to view peers details'})[
                            1].text.strip())
                    download_url = self.urls['base_url'] + download_href
                    # FIXME
                    size = -1

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
