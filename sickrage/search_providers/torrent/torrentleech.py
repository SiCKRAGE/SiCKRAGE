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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import math
from urllib.parse import urljoin

from requests.utils import dict_from_cookiejar

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.tv.show.helpers import find_show
from sickrage.search_providers import TorrentProvider


class TorrentLeechProvider(TorrentProvider):
    def __init__(self):
        super(TorrentLeechProvider, self).__init__("TorrentLeech", 'https://www.torrentleech.org', True)

        self._urls.update({
            'login': '{base_url}/user/account/login'.format(**self._urls),
            'search': '{base_url}/torrents/browse/list/'.format(**self._urls),
            'download': '{base_url}/download/%s/%s'.format(**self._urls),
            'details': '{base_url}/download/%s/%s'.format(**self._urls),
        })

        # custom settings
        self.custom_settings = {
            'username': '',
            'password': '',
            'minseed': 0,
            'minleech': 0
        }

        # self.enable_cookies = True
        # self.required_cookies = ('tluid', 'tlpass')

        self.proper_strings = ['PROPER', 'REPACK', 'REAL', 'RERIP']

        self.cache = TVCache(self, min_time=20)

    # def login(self):
    #     return self.cookie_login('log in')

    def login(self):
        cookies = dict_from_cookiejar(self.session.cookies)
        if any(cookies.values()) and cookies.get('member_id'):
            return True

        login_params = {
            'username': self.custom_settings['username'],
            'password': self.custom_settings['password'],
            'login': 'submit',
            'remember_me': 'on',
        }

        try:
            response = self.session.post(self.urls['login'], data=login_params, timeout=30).text
        except Exception:
            sickrage.app.log.warning("Unable to connect to provider")
            return False

        if '/user/account/logout' not in response:
            sickrage.app.log.warning("Invalid username or password. Check your settings")
            return False

        return True

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []

        if not self.login():
            return results

        show = find_show(series_id, series_provider_id)

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: %s" % search_string)

                    categories = ["2", "7", "35"]
                    categories += ["26", "32", "44"] if mode == "Episode" else ["27"]
                    if show.is_anime:
                        categories += ["34"]
                else:
                    categories = ["2", "26", "27", "32", "7", "34", "35", "44"]

                # Create the query URL
                categories_url = 'categories/{}/'.format(",".join(categories))
                query_url = 'query/{}'.format(search_string)
                params_url = urljoin(categories_url, query_url)
                search_url = urljoin(self.urls['search'], params_url)

                try:
                    data = self.session.get(search_url).json()
                    results += self.parse(data, mode)

                    # Handle pagination
                    num_found = data.get('numFound', 0)
                    per_page = data.get('perPage', 35)

                    try:
                        pages = int(math.ceil(100 / per_page))
                    except ZeroDivisionError:
                        pages = 1

                    for page in range(2, pages + 1):
                        if num_found and num_found > per_page and pages > 1:
                            page_url = urljoin(search_url, 'page/{}/'.format(page))

                            resp = self.session.get(page_url)
                            if not resp or not resp.content:
                                sickrage.app.log.debug("No data returned from provider")
                                continue

                            try:
                                data = resp.json()
                            except ValueError:
                                sickrage.app.log.debug("No data returned from provider")
                                continue

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

        for item in data.get('torrentList') or []:
            try:
                title = item['name']
                download_url = self.urls['download'] % (item['fid'], item['filename'])

                seeders = item['seeders']
                leechers = item['leechers']
                size = item['size']

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
                sickrage.app.log.error("Failed parsing provider.")

        return results
