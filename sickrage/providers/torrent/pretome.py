# Author: Nick Sologoub
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import re
import traceback
import urllib

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, convert_size
from sickrage.providers import TorrentProvider


class PretomeProvider(TorrentProvider):
    def __init__(self):
        super(PretomeProvider, self).__init__("Pretome",'pretome.info', True)

        self.supports_backlog = True

        self.username = None
        self.password = None
        self.pin = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.urls.update({
            'login': '{base_url}/takelogin.php'.format(base_url=self.urls['base_url']),
            'detail': '{base_url}/details.php?id=%s'.format(base_url=self.urls['base_url']),
            'search': '{base_url}/browse.php?search=%s%s'.format(base_url=self.urls['base_url']),
            'download': '{base_url}/download.php/%s/%s.torrent'.format(base_url=self.urls['base_url'])
        })

        self.categories = "&st=1&cat%5B%5D=7"

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = TVCache(self, min_time=30)

    def _check_auth(self):

        if not self.username or not self.password or not self.pin:
            sickrage.srCore.srLogger.warning("Invalid username or password or pin. Check your settings")

        return True

    def login(self):

        login_params = {'username': self.username,
                        'password': self.password,
                        'login_pin': self.pin}

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

        if not self.login():
            return results

        for mode in search_params.keys():
            sickrage.srCore.srLogger.debug("Search Mode: %s" % mode)
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug("Search string: %s " % search_string)

                searchURL = self.urls['search'] % (urllib.quote(search_string.encode('utf-8')), self.categories)
                sickrage.srCore.srLogger.debug("Search URL: %s" % searchURL)

                try:
                    data = sickrage.srCore.srWebSession.get(searchURL).text
                except Exception:
                    sickrage.srCore.srLogger.debug("No data returned from provider")
                    continue

                try:
                    with bs4_parser(data) as html:
                        # Continue only if one Release is found
                        empty = html.find('h2', text="No .torrents fit this filter criteria")
                        if empty:
                            sickrage.srCore.srLogger.debug("Data returned from provider does not contain any torrents")
                            continue

                        torrent_table = html.find('table', attrs={'style': 'border: none; width: 100%;'})
                        if not torrent_table:
                            sickrage.srCore.srLogger.error("Could not find table of torrents")
                            continue

                        torrent_rows = torrent_table.find_all('tr', attrs={'class': 'browse'})

                        for result in torrent_rows:
                            cells = result.find_all('td')
                            size = None
                            link = cells[1].find('a', attrs={'style': 'font-size: 1.25em; font-weight: bold;'})

                            torrent_id = link['href'].replace('details.php?id=', '')

                            try:
                                if link.has_key('title'):
                                    title = link['title']
                                else:
                                    title = link.contents[0]

                                download_url = self.urls['download'] % (torrent_id, link.contents[0])
                                seeders = int(cells[9].contents[0])
                                leechers = int(cells[10].contents[0])

                                # Need size for failed downloads handling
                                if size is None:
                                    if re.match(r'[0-9]+,?\.?[0-9]*[KkMmGg]+[Bb]+', cells[7].text):
                                        size = convert_size(cells[7].text)
                                        if not size:
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

                except Exception as e:
                    sickrage.srCore.srLogger.error("Failed parsing provider. Traceback: %s" % traceback.format_exc())

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seed_ratio(self):
        return self.ratio
