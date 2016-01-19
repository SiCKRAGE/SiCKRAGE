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

import sickrage
from sickrage.core.caches import tv_cache
from sickrage.core.helpers import bs4_parser
from sickrage.providers import TorrentProvider


class BitSoupProvider(TorrentProvider):
    def __init__(self):
        super(BitSoupProvider, self).__init__("BitSoup")

        self.urls = {
            'base_url': 'https://www.bitsoup.me',
            'login': 'https://www.bitsoup.me/takelogin.php',
            'detail': 'https://www.bitsoup.me/details.php?id=%s',
            'search': 'https://www.bitsoup.me/browse.php',
            'download': 'https://bitsoup.me/%s',
        }

        self.url = self.urls['base_url']

        self.supportsBacklog = True

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = BitSoupCache(self)

        self.search_params = {
            "c42": 1, "c45": 1, "c49": 1, "c7": 1
        }

    def _checkAuth(self):
        if not self.username or not self.password:
            sickrage.LOGGER.warning("Invalid username or password. Check your settings")

        return True

    def _doLogin(self):

        login_params = {
            'username': self.username,
            'password': self.password,
            'ssl': 'yes'
        }

        response = self.getURL(self.urls['login'], post_data=login_params, timeout=30)
        if not response:
            sickrage.LOGGER.warning("Unable to connect to provider")
            return False

        if re.search('Username or password incorrect', response):
            sickrage.LOGGER.warning("Invalid username or password. Check your settings")
            return False

        return True

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return results

        for mode in search_strings.keys():
            sickrage.LOGGER.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:

                if mode is not 'RSS':
                    sickrage.LOGGER.debug("Search string: %s " % search_string)

                self.search_params[b'search'] = search_string

                data = self.getURL(self.urls['search'], params=self.search_params)
                if not data:
                    continue

                try:
                    with bs4_parser(data) as html:
                        torrent_table = html.find('table', attrs={'class': 'koptekst'})
                        torrent_rows = torrent_table.find_all('tr') if torrent_table else []

                        # Continue only if one Release is found
                        if len(torrent_rows) < 2:
                            sickrage.LOGGER.debug("Data returned from provider does not contain any torrents")
                            continue

                        for result in torrent_rows[1:]:
                            cells = result.find_all('td')

                            link = cells[1].find('a')
                            download_url = self.urls['download'] % cells[2].find('a')['href']

                            try:
                                title = link.getText()
                                seeders = int(cells[10].getText())
                                leechers = int(cells[11].getText())
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
                    sickrage.LOGGER.warning("Failed parsing provider. Traceback: %s" % traceback.format_exc())

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class BitSoupCache(tv_cache.TVCache):
    def __init__(self, provider_obj):
        tv_cache.TVCache.__init__(self, provider_obj)

        # only poll TorrentBytes every 20 minutes max
        self.minTime = 20

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_strings)}
