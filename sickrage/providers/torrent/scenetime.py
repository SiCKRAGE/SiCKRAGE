# Author: Idan Gutman
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import re
import traceback
import urllib

import sickrage
from sickrage.core.caches import tv_cache
from sickrage.core.helpers import bs4_parser
from sickrage.providers import TorrentProvider


class SceneTimeProvider(TorrentProvider):
    def __init__(self):

        super(SceneTimeProvider, self).__init__("SceneTime")

        self.supportsBacklog = True

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = SceneTimeCache(self)

        self.urls = {'base_url': 'https://www.scenetime.com',
                     'login': 'https://www.scenetime.com/takelogin.php',
                     'detail': 'https://www.scenetime.com/details.php?id=%s',
                     'search': 'https://www.scenetime.com/browse.php?search=%s%s',
                     'download': 'https://www.scenetime.com/download.php/%s/%s'}

        self.url = self.urls['base_url']

        self.categories = "&c2=1&c43=13&c9=1&c63=1&c77=1&c79=1&c100=1&c101=1"

    def _doLogin(self):

        login_params = {'username': self.username,
                        'password': self.password}

        response = self.getURL(self.urls['login'], post_data=login_params, timeout=30)
        if not response:
            sickrage.LOGGER.warning("Unable to connect to provider")
            return False

        if re.search('Username or password incorrect', response):
            sickrage.LOGGER.warning("Invalid username or password. Check your settings")
            return False

        return True

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return results

        for mode in search_params.keys():
            sickrage.LOGGER.debug("Search Mode: %s" % mode)
            for search_string in search_params[mode]:

                if mode is not 'RSS':
                    sickrage.LOGGER.debug("Search string: %s " % search_string)

                searchURL = self.urls['search'] % (urllib.quote(search_string), self.categories)
                sickrage.LOGGER.debug("Search URL: %s" % searchURL)

                data = self.getURL(searchURL)
                if not data:
                    continue

                try:
                    with bs4_parser(data) as html:
                        torrent_table = html.select("#torrenttable table")
                        torrent_rows = torrent_table[0].select("tr") if torrent_table else []

                        # Continue only if one Release is found
                        if len(torrent_rows) < 2:
                            sickrage.LOGGER.debug("Data returned from provider does not contain any torrents")
                            continue

                        # Scenetime apparently uses different number of cells in #torrenttable based
                        # on who you are. This works around that by extracting labels from the first
                        # <tr> and using their index to find the correct download/seeders/leechers td.
                        labels = [label.get_text() for label in torrent_rows[0].find_all('td')]

                        for result in torrent_rows[1:]:
                            cells = result.find_all('td')

                            link = cells[labels.index('Name')].find('a')

                            full_id = link[b'href'].replace('details.php?id=', '')
                            torrent_id = full_id.split("&")[0]

                            try:
                                title = link.contents[0].get_text()
                                filename = "%s.torrent" % title.replace(" ", ".")
                                download_url = self.urls['download'] % (torrent_id, filename)

                                int(cells[labels.index('Seeders')].get_text())
                                seeders = int(cells[labels.index('Seeders')].get_text())
                                leechers = int(cells[labels.index('Leechers')].get_text())
                                # FIXME
                                size = -1

                            except (AttributeError, TypeError):
                                continue

                            if not all([title, download_url]):
                                continue

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode is not 'RSS':
                                    sickrage.LOGGER.debug(
                                            "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                                    title, seeders, leechers))
                                continue

                            item = title, download_url, size, seeders, leechers
                            if mode is not 'RSS':
                                sickrage.LOGGER.debug("Found result: %s " % title)

                            items[mode].append(item)

                except Exception:
                    sickrage.LOGGER.error("Failed parsing provider. Traceback: {}".format(traceback.format_exc()))

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class SceneTimeCache(tv_cache.TVCache):
    def __init__(self, provider_obj):
        tv_cache.TVCache.__init__(self, provider_obj)

        # only poll SceneTime every 20 minutes max
        self.minTime = 20

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}
