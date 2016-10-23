# Author: Seamus Wassman
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
import traceback

import requests
import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.exceptions import AuthException
from sickrage.core.helpers import bs4_parser, convert_size
from sickrage.providers import TorrentProvider


class GFTrackerProvider(TorrentProvider):
    def __init__(self):
        super(GFTrackerProvider, self).__init__("GFTracker",'www.thegft.org', True)

        self.supports_backlog = True

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.urls.update({
            'login': '{base_url}/loginsite.php'.format(base_url=self.urls['base_url']),
            'search': '{base_url}/browse.php?view=%s%s'.format(base_url=self.urls['base_url']),
            'download': '{base_url}/%s'.format(base_url=self.urls['base_url'])
        })

        self.cookies = None

        self.categories = "0&c26=1&c37=1&c19=1&c47=1&c17=1&c4=1&search="

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = TVCache(self, min_time=20)

    def _check_auth(self):

        if not self.username or not self.password:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def login(self):

        login_params = {'username': self.username,
                        'password': self.password}



        try:
            response = sickrage.srCore.srWebSession.post(self.urls['login'], data=login_params, timeout=30).text
        except Exception:
            sickrage.srCore.srLogger.warning("[{}]: Unable to connect to provider".format(self.name))
            return False

        # Save cookies from response
        if re.search('Username or password incorrect', response):
            sickrage.srCore.srLogger.warning("[{}]: Invalid username or password. Check your settings".format(self.name))
            return False

        requests.utils.add_dict_to_cookiejar(sickrage.srCore.srWebSession.cookies, self.cookies)

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

                searchURL = self.urls['search'] % (self.categories, search_string)
                sickrage.srCore.srLogger.debug("Search URL: %s" % searchURL)

                # Set cookies from response
                # Returns top 30 results by default, expandable in user profile

                try:
                    data = sickrage.srCore.srWebSession.get(searchURL, cookies=self.cookies).text
                except Exception:
                    sickrage.srCore.srLogger.debug("No data returned from provider")
                    continue

                try:
                    with bs4_parser(data) as html:
                        torrent_table = html.find("div", id="torrentBrowse")
                        torrent_rows = torrent_table.findChildren("tr") if torrent_table else []

                        # Continue only if at least one release is found
                        if len(torrent_rows) < 1:
                            sickrage.srCore.srLogger.debug("Data returned from provider does not contain any torrents")
                            continue

                        for result in torrent_rows[1:]:
                            cells = result.findChildren("td")
                            title = cells[1].find("a").find_next("a")
                            link = cells[3].find("a")
                            shares = cells[8].get_text().split("/", 1)
                            torrent_size = cells[7].get_text().split("/", 1)[0]

                            try:
                                if title.has_key('title'):
                                    title = title['title']
                                else:
                                    title = cells[1].find("a")['title']

                                download_url = self.urls['download'] % (link['href'])
                                seeders = int(shares[0])
                                leechers = int(shares[1])

                                size = -1
                                if re.match(r"\d+([,\.]\d+)?\s*[KkMmGgTt]?[Bb]", torrent_size):
                                    size = convert_size(torrent_size.rstrip())

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
