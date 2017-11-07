# Author: Idan Gutman
# Modified by jkaberg, https://github.com/jkaberg for SceneAccess
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

import re
import urllib

from requests.utils import dict_from_cookiejar

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, convert_size
from sickrage.providers import TorrentProvider


class SCCProvider(TorrentProvider):
    def __init__(self):
        super(SCCProvider, self).__init__("SceneAccess", 'http://sceneaccess.eu', True)

        self.urls.update({
            'login': '{base_url}/login'.format(**self.urls),
            'detail': '{base_url}/details?id=%s'.format(**self.urls),
            'search': '{base_url}/all?search=%s&method=1&%s'.format(**self.urls),
            'download': '{base_url}/%s'.format(**self.urls)
        })

        self.username = None
        self.password = None

        self.minseed = None
        self.minleech = None

        self.categories = {
            'Season': 'c26=26&c44=44&c45=45',
        # Archive, non-scene HD, non-scene SD; need to include non-scene because WEB-DL packs get added to those categories
            'Episode': 'c17=17&c27=27&c33=33&c34=34&c44=44&c45=45',
        # TV HD, TV SD, non-scene HD, non-scene SD, foreign XviD, foreign x264
            'RSS': 'c17=17&c26=26&c27=27&c33=33&c34=34&c44=44&c45=45'  # Season + Episode
        }

        self.cache = TVCache(self, min_time=20)

    def login(self):
        if any(dict_from_cookiejar(sickrage.app.srWebSession.cookies).values()):
            return True

        login_params = {'username': self.username,
                        'password': self.password,
                        'submit': 'come on in'}

        try:
            response = sickrage.app.srWebSession.post(self.urls['login'], data=login_params, timeout=30).text
        except Exception:
            sickrage.app.srLogger.warning("Unable to connect to provider".format(self.name))
            return False

        if re.search(r'Username or password incorrect', response) \
                or re.search(r'<title>SceneAccess \| Login</title>', response):
            sickrage.app.srLogger.warning(
                "Invalid username or password. Check your settings".format(self.name))
            return False

        return True

    @staticmethod
    def _isSection(section, text):
        title = r'<title>.+? \| %s</title>' % section
        return re.search(title, text, re.IGNORECASE)

    def search(self, search_strings, age=0, ep_obj=None):
        results = []

        if not self.login():
            return results

        for mode in search_strings.keys():
            if mode != 'RSS':
                sickrage.app.srLogger.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.srLogger.debug("Search string: %s " % search_string)

                searchURL = self.urls['search'] % (urllib.quote(search_string), self.categories[mode])
                sickrage.app.srLogger.debug("Search URL: %s" % searchURL)

                try:
                    data = sickrage.app.srWebSession.get(searchURL).text
                    results += self.parse(data, mode)
                except Exception:
                    sickrage.app.srLogger.debug("No data returned from provider")

        return results

    def parse(self, data, mode):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []

        with bs4_parser(data) as html:
            torrent_table = html.find('table', attrs={'id': 'torrents-table'})
            torrent_rows = torrent_table.find_all('tr') if torrent_table else []

            # Continue only if at least one Release is found
            if len(torrent_rows) < 2:
                sickrage.app.srLogger.debug("Data returned from provider does not contain any torrents")
                return results

            for result in torrent_table.find_all('tr')[1:]:
                try:
                    link = result.find('td', attrs={'class': 'ttr_name'}).find('a')
                    url = result.find('td', attrs={'class': 'td_dl'}).find('a')

                    title = link.string
                    if re.search(r'\.\.\.', title):
                        data = sickrage.app.srWebSession.get(self.urls['base_url'] + "/" + link['href']).text
                        with bs4_parser(data) as details_html:
                            title = re.search('(?<=").+(?<!")', details_html.title.string).group(0)
                    download_url = self.urls['download'] % url['href']
                    seeders = int(result.find('td', attrs={'class': 'ttr_seeders'}).string)
                    leechers = int(result.find('td', attrs={'class': 'ttr_leechers'}).string)
                    size = convert_size(result.find('td', attrs={'class': 'ttr_size'}).contents[0], -1)

                    if not all([title, download_url]):
                        continue

                    item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders,
                            'leechers': leechers, 'hash': ''}

                    if mode != 'RSS':
                        sickrage.app.srLogger.debug("Found result: {}".format(title))

                    results.append(item)
                except Exception:
                    sickrage.app.srLogger.error("Failed parsing provider")

        return results