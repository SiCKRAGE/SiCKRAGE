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


class MoreThanTVProvider(TorrentProvider):
    def __init__(self):
        super(MoreThanTVProvider, self).__init__("MoreThanTV",'www.morethan.tv', True)

        self.supports_backlog = True

        self._uid = None
        self._hash = None
        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None
        # self.freeleech = False

        self.urls.update({
            'login': '{base_url}/login.php'.format(base_url=self.urls['base_url']),
            'detail': '{base_url}/torrents.php?id=%s'.format(base_url=self.urls['base_url']),
            'search': '{base_url}/torrents.php?tags_type=1&order_by=time&order_way=desc&action=basic&searchsubmit=1&searchstr=%s'.format(base_url=self.urls['base_url']),
            'download': '{base_url}/torrents.php?action=download&id=%s'.format(base_url=self.urls['base_url'])
        })

        self.cookies = None

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = TVCache(self, min_time=10)

    def _check_auth(self):

        if not self.username or not self.password:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def login(self):
        if any(requests.utils.dict_from_cookiejar(sickrage.srCore.srWebSession.cookies).values()):
            return True

        if self._uid and self._hash:
            requests.utils.add_dict_to_cookiejar(sickrage.srCore.srWebSession.cookies, self.cookies)
        else:
            login_params = {'username': self.username,
                            'password': self.password,
                            'login': 'Log in',
                            'keeplogged': '1'}

            try:
                response = sickrage.srCore.srWebSession.post(self.urls['login'], data=login_params, timeout=30).text
            except Exception:
                sickrage.srCore.srLogger.warning("[{}]: Unable to connect to provider".format(self.name))
                return False

            if re.search('Your username or password was incorrect.', response):
                sickrage.srCore.srLogger.warning("[{}]: Invalid username or password. Check your settings".format(self.name))
                return False

            return True

    def search(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        # freeleech = '3' if self.freeleech else '0'

        if not self.login():
            return results

        for mode in search_params.keys():
            sickrage.srCore.srLogger.debug("Search Mode: %s" % mode)
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug("Search string: %s " % search_string)

                searchURL = self.urls['search'] % (search_string.replace('(', '').replace(')', ''))
                sickrage.srCore.srLogger.debug("Search URL: %s" % searchURL)

                # returns top 15 results by default, expandable in user profile to 100
                try:
                    data = sickrage.srCore.srWebSession.get(searchURL).text
                except Exception:
                    sickrage.srCore.srLogger.debug("No data returned from provider")
                    continue

                try:
                    with bs4_parser(data) as html:
                        torrent_table = html.find('table', attrs={'class': 'torrent_table'})
                        torrent_rows = torrent_table.findChildren('tr') if torrent_table else []

                        # Continue only if one Release is found
                        if len(torrent_rows) < 2:
                            sickrage.srCore.srLogger.debug("Data returned from provider does not contain any torrents")
                            continue

                        # skip colheader
                        for result in torrent_rows[1:]:
                            cells = result.findChildren('td')
                            link = cells[1].find('span', attrs={'title': 'Download'}).parent
                            title_anchor = cells[1].find('a', attrs={'dir': 'ltr'})

                            # skip if torrent has been nuked due to poor quality
                            if cells[1].find('img', alt='Nuked') is not None:
                                continue

                            torrent_id_long = link['href'].replace('torrents.php?action=download&id=', '')

                            try:
                                if title_anchor.has_key('title'):
                                    title = cells[1].find('a', {'title': 'View torrent'}).contents[0].strip()
                                else:
                                    title = title_anchor.contents[0]
                                download_url = self.urls['download'] % torrent_id_long

                                seeders = cells[6].contents[0]

                                leechers = cells[7].contents[0]

                                size = -1
                                if re.match(r'\d+([,\.]\d+)?\s*[KkMmGgTt]?[Bb]', cells[4].contents[0]):
                                    size = convert_size(cells[4].text.strip())

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
