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

        super(SceneTimeProvider, self).__init__("SceneTime",'www.scenetime.com')

        self.supportsBacklog = True

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = SceneTimeCache(self)

        self.urls.update({
            'login': '{base_url}/takelogin.php'.format(base_url=self.urls['base_url']),
            'detail': '{base_url}/details.php?id=%s'.format(base_url=self.urls['base_url']),
            'search': '{base_url}/browse.php?search=%s%s'.format(base_url=self.urls['base_url']),
            'download': '{base_url}/download.php/%s/%s'.format(base_url=self.urls['base_url'])
        })

        self.categories = "&c2=1&c43=13&c9=1&c63=1&c77=1&c79=1&c100=1&c101=1"

    def _doLogin(self):

        login_params = {'username': self.username,
                        'password': self.password}

        try:
            response = sickrage.srCore.srWebSession.post(self.urls['login'], data=login_params, timeout=30).text
        except Exception:
            sickrage.srCore.srLogger.warning("[{}]: Unable to connect to provider".format(self.name))
            return False

        if re.search('Username or password incorrect', response):
            sickrage.srCore.srLogger.warning("[{}]: Invalid username or password. Check your settings".format(self.name))
            return False

        return True

    def search(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return results

        for mode in search_params.keys():
            sickrage.srCore.srLogger.debug("Search Mode: %s" % mode)
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug("Search string: %s " % search_string)

                searchURL = self.urls['search'] % (urllib.quote(search_string), self.categories)
                sickrage.srCore.srLogger.debug("Search URL: %s" % searchURL)

                try:
                    data = sickrage.srCore.srWebSession.get(searchURL).text
                except Exception:
                    sickrage.srCore.srLogger.debug("No data returned from provider")
                    continue

                try:
                    with bs4_parser(data) as html:
                        torrent_table = html.select("#torrenttable table")
                        torrent_rows = torrent_table[0].select("tr") if torrent_table else []

                        # Continue only if one Release is found
                        if len(torrent_rows) < 2:
                            sickrage.srCore.srLogger.debug("Data returned from provider does not contain any torrents")
                            continue

                        # Scenetime apparently uses different number of cells in #torrenttable based
                        # on who you are. This works around that by extracting labels from the first
                        # <tr> and using their index to find the correct download/seeders/leechers td.
                        labels = [label.get_text() for label in torrent_rows[0].find_all('td')]

                        for result in torrent_rows[1:]:
                            cells = result.find_all('td')

                            link = cells[labels.index('Name')].find('a')

                            full_id = link['href'].replace('details.php?id=', '')
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
                                if mode != 'RSS':
                                    sickrage.srCore.srLogger.debug(
                                        "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                            title, seeders, leechers))
                                continue

                            item = title, download_url, size, seeders, leechers
                            if mode != 'RSS':
                                sickrage.srCore.srLogger.debug("Found result: %s " % title)

                            items[mode].append(item)

                except Exception:
                    sickrage.srCore.srLogger.error("Failed parsing provider. Traceback: {}".format(traceback.format_exc()))

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
        return {'entries': self.provider.search(search_params)}
