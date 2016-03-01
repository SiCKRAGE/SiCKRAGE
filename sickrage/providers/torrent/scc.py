# Author: Idan Gutman
# Modified by jkaberg, https://github.com/jkaberg for SceneAccess
# URL: http://github.com/SiCKRAGETV/SickRage/
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
import time
import urllib

import sickrage
from core.caches import tv_cache
from core.common import cpu_presets
from core.helpers import bs4_parser
from providers import TorrentProvider


class SCCProvider(TorrentProvider):
    def __init__(self):

        super(SCCProvider, self).__init__("SceneAccess")

        self.supportsBacklog = True

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = SCCCache(self)

        self.urls = {'base_url': 'https://sceneaccess.eu',
                     'login': 'https://sceneaccess.eu/login',
                     'detail': 'https://www.sceneaccess.eu/details?id=%s',
                     'search': 'https://sceneaccess.eu/all?search=%s&method=1&%s',
                     'download': 'https://www.sceneaccess.eu/%s'}

        self.url = self.urls['base_url']

        self.categories = {'sponly': 'c26=26&c44=44&c45=45',
                           # Archive, non-scene HD, non-scene SD; need to include non-scene because WEB-DL packs get added to those categories
                           'eponly': 'c27=27&c17=17&c44=44&c45=45&c33=33&c34=34'}  # TV HD, TV SD, non-scene HD, non-scene SD, foreign XviD, foreign x264

    def _doLogin(self):

        login_params = {'username': self.username,
                        'password': self.password,
                        'submit': 'come on in'}

        response = self.getURL(self.urls['login'], post_data=login_params, timeout=30)
        if not response:
            sickrage.srLogger.warning("Unable to connect to provider")
            return False

        if re.search(r'Username or password incorrect', response) \
                or re.search(r'<title>SceneAccess \| Login</title>', response):
            sickrage.srLogger.warning("Invalid username or password. Check your settings")
            return False

        return True

    @staticmethod
    def _isSection(section, text):
        title = r'<title>.+? \| %s</title>' % section
        return re.search(title, text, re.IGNORECASE)

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []

        if not self._doLogin():
            return results

        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_strings.keys():
            if mode is not 'RSS':
                sickrage.srLogger.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:
                if mode is not 'RSS':
                    sickrage.srLogger.debug("Search string: %s " % search_string)

                searchURL = self.urls['search'] % (urllib.quote(search_string), self.categories[search_mode])

                try:
                    sickrage.srLogger.debug("Search URL: %s" % searchURL)
                    data = self.getURL(searchURL)
                    time.sleep(cpu_presets[sickrage.srConfig.CPU_PRESET])
                except Exception as e:
                    sickrage.srLogger.warning("Unable to fetch data. Error: %s" % repr(e))

                if not data:
                    continue

                with bs4_parser(data) as html:
                    torrent_table = html.find('table', attrs={'id': 'torrents-table'})
                    torrent_rows = torrent_table.find_all('tr') if torrent_table else []

                    # Continue only if at least one Release is found
                    if len(torrent_rows) < 2:
                        sickrage.srLogger.debug("Data returned from provider does not contain any torrents")
                        continue

                    for result in torrent_table.find_all('tr')[1:]:

                        try:
                            link = result.find('td', attrs={'class': 'ttr_name'}).find('a')
                            url = result.find('td', attrs={'class': 'td_dl'}).find('a')

                            title = link.string
                            if re.search(r'\.\.\.', title):
                                data = self.getURL(self.url + "/" + link[b'href'])
                                if data:
                                    with bs4_parser(data) as details_html:
                                        title = re.search('(?<=").+(?<!")', details_html.title.string).group(0)
                            download_url = self.urls['download'] % url[b'href']
                            seeders = int(result.find('td', attrs={'class': 'ttr_seeders'}).string)
                            leechers = int(result.find('td', attrs={'class': 'ttr_leechers'}).string)
                            size = self._convertSize(result.find('td', attrs={'class': 'ttr_size'}).contents[0])
                        except (AttributeError, TypeError):
                            continue

                        if not all([title, download_url]):
                            continue

                        # Filter unseeded torrent
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode is not 'RSS':
                                sickrage.srLogger.debug(
                                        "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                                title, seeders, leechers))
                            continue

                        item = title, download_url, size, seeders, leechers
                        if mode is not 'RSS':
                            sickrage.srLogger.debug("Found result: %s " % title)

                        items[mode].append(item)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio

    @staticmethod
    def _convertSize(size):
        size, base = size.split()
        size = float(size)
        if base in 'KB':
            size = size * 1024
        elif base in 'MB':
            size = size * 1024 ** 2
        elif base in 'GB':
            size = size * 1024 ** 3
        elif base in 'TB':
            size = size * 1024 ** 4
        return int(size)


class SCCCache(tv_cache.TVCache):
    def __init__(self, provider_obj):
        tv_cache.TVCache.__init__(self, provider_obj)

        # only poll SCC every 20 minutes max
        self.minTime = 20

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_strings)}
