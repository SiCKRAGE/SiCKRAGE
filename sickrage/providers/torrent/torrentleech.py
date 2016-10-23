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

import re
import traceback
import urllib

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser
from sickrage.providers import TorrentProvider


class TorrentLeechProvider(TorrentProvider):
    def __init__(self):

        super(TorrentLeechProvider, self).__init__("TorrentLeech",'torrentleech.org', True)

        self.supports_backlog = True

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.urls.update({
            'login': '{base_url}/user/account/login/'.format(base_url=self.urls['base_url']),
            'detail': '{base_url}/torrent/%s'.format(base_url=self.urls['base_url']),
            'search': '{base_url}/torrents/browse/index/query/%s/categories/%s'.format(base_url=self.urls['base_url']),
            'download': '{base_url}/%s'.format(base_url=self.urls['base_url']),
            'index': '{base_url}/torrents/browse/index/categories/%s'.format(base_url=self.urls['base_url'])
        })

        self.categories = "2,7,26,27,32,34,35"

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = TVCache(self, min_time=20)

    def login(self):

        login_params = {'username': self.username,
                        'password': self.password,
                        'remember_me': 'on',
                        'login': 'submit'}

        try:
            response = sickrage.srCore.srWebSession.post(self.urls['login'], data=login_params, timeout=30).text
        except Exception:
            sickrage.srCore.srLogger.warning("[{}]: Unable to connect to provider".format(self.name))
            return False

        if re.search('Invalid Username/password', response) or re.search('<title>Login :: TorrentLeech.org</title>',
                                                                         response):
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

                if mode == 'RSS':
                    searchURL = self.urls['index'] % self.categories
                else:
                    searchURL = self.urls['search'] % (
                        urllib.quote_plus(search_string.encode('utf-8')), self.categories)
                    sickrage.srCore.srLogger.debug("Search string: %s " % search_string)

                sickrage.srCore.srLogger.debug("Search URL: %s" % searchURL)

                try:
                    data = sickrage.srCore.srWebSession.get(searchURL).text
                except Exception:
                    sickrage.srCore.srLogger.debug("No data returned from provider")
                    continue

                try:
                    with bs4_parser(data) as html:
                        torrent_table = html.find('table', attrs={'id': 'torrenttable'})
                        torrent_rows = torrent_table.find_all('tr') if torrent_table else []

                        # Continue only if one Release is found
                        if len(torrent_rows) < 2:
                            sickrage.srCore.srLogger.debug("Data returned from provider does not contain any torrents")
                            continue

                        for result in torrent_table.find_all('tr')[1:]:

                            try:
                                link = result.find('td', attrs={'class': 'name'}).find('a')
                                url = result.find('td', attrs={'class': 'quickdownload'}).find('a')
                                title = link.string
                                download_url = self.urls['download'] % url['href']
                                seeders = int(result.find('td', attrs={'class': 'seeders'}).string)
                                leechers = int(result.find('td', attrs={'class': 'leechers'}).string)
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

    def seed_ratio(self):
        return self.ratio
