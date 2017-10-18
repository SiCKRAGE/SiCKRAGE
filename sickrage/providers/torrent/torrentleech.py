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
import urllib

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, convert_size, try_int
from sickrage.providers import TorrentProvider


class TorrentLeechProvider(TorrentProvider):
    def __init__(self):
        super(TorrentLeechProvider, self).__init__("TorrentLeech", 'http://torrentleech.org', True)

        self.urls.update({
            'login': '{base_url}/user/account/login/'.format(**self.urls),
            'detail': '{base_url}/torrent/%s'.format(**self.urls),
            'search': '{base_url}/torrents/browse/index/query/%s/categories/%s'.format(**self.urls),
            'download': '{base_url}/%s'.format(**self.urls),
            'index': '{base_url}/torrents/browse/index/categories/%s'.format(**self.urls)
        })

        self.username = None
        self.password = None

        self.minseed = None
        self.minleech = None

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
            sickrage.srCore.srLogger.warning(
                "[{}]: Invalid username or password. Check your settings".format(self.name))
            return False

        return True

    def search(self, search_params, age=0, ep_obj=None):
        results = []

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
                    data = sickrage.srCore.srWebSession.get(searchURL, cache=False).text
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
                                download_url = url['href']
                                seeders = try_int(result.find('td', attrs={'class': 'seeders'}).text, 0)
                                leechers = try_int(result.find('td', attrs={'class': 'leechers'}).text, 0)

                                size = -1
                                if re.match(r'\d+([,.]\d+)?\s*[KkMmGgTt]?[Bb]',
                                            result('td', class_="listcolumn")[1].text):
                                    size = convert_size(result('td', class_="listcolumn")[1].text.strip(), -1)
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

                            item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}
                            if mode != 'RSS':
                                sickrage.srCore.srLogger.debug("Found result: {}".format(title))

                            results.append(item)
                except Exception:
                    sickrage.srCore.srLogger.error("Failed parsing provider.")

        # Sort all the items by seeders if available
        results.sort(key=lambda k: try_int(k.get('seeders', 0)), reverse=True)

        return results

