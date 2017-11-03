# Author: seedboy
# URL: https://github.com/seedboy
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
from urlparse import urljoin

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, convert_size, validate_url
from sickrage.providers import TorrentProvider


class IPTorrentsProvider(TorrentProvider):
    def __init__(self):
        super(IPTorrentsProvider, self).__init__("IPTorrents", 'https://iptorrents.eu', True)

        self.urls.update({
            'login': '{base_url}/take_login.php'.format(**self.urls),
            'search': '{base_url}/t?%s%s&q=%s&qf=#torrents'.format(**self.urls)
        })

        self.username = None
        self.password = None

        self.freeleech = False
        self.enable_cookies = True
        self.required_cookies = ('uid', 'pass')
        self.minseed = None
        self.minleech = None
        self.categories = '73=&60='

        self.custom_url = ""

        self.cache = TVCache(self, min_time=10)

    def login(self):
        return self.cookie_login('sign in')

    def search(self, search_strings, age=0, ep_obj=None):
        results = []

        freeleech = '&free=on' if self.freeleech else ''

        if not self.login():
            return results

        for mode in search_strings:
            sickrage.srCore.srLogger.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug("Search string: %s " % search_string)

                # URL with 50 tv-show results, or max 150 if adjusted in IPTorrents profile
                search_url = self.urls['search'] % (self.categories, freeleech, search_string)
                search_url += ';o=seeders' if mode != 'RSS' else ''

                if self.custom_url:
                    if not validate_url(self.custom_url):
                        sickrage.srCore.srLogger.warning("Invalid custom url: {}".format(self.custom_url))
                        return results
                    search_url = urljoin(self.custom_url, search_url.split(self.urls['base_url'])[1])

                sickrage.srCore.srLogger.debug("Search URL: %s" % search_url)

                try:
                    data = sickrage.srCore.srWebSession.get(search_url).text
                    results += self.parse(data, mode)
                except Exception:
                    sickrage.srCore.srLogger.debug("No data returned from provider")

        return results

    def parse(self, data, mode):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []

        data = re.sub(r'(?im)<button.+?<[/]button>', '', data, 0)
        with bs4_parser(data) as html:
            if not html:
                sickrage.srCore.srLogger.debug("No data returned from provider")
                return results

            if html.find(text='No Torrents Found!'):
                sickrage.srCore.srLogger.debug("Data returned from provider does not contain any torrents")
                return results

            torrent_table = html.find('table', id='torrents')
            torrents = torrent_table.find_all('tr') if torrent_table else []

            # Continue only if one Release is found
            if len(torrents) < 2:
                sickrage.srCore.srLogger.debug("Data returned from provider does not contain any torrents")
                return results

            for result in torrents[1:]:
                try:
                    title = result.find_all('td')[1].find('a').text
                    download_url = self.urls['base_url'] + result.find_all('td')[3].find('a')['href']
                    size = convert_size(result.find_all('td')[5].text, -1)
                    seeders = int(result.find('td', attrs={'class': 'ac t_seeders'}).text)
                    leechers = int(result.find('td', attrs={'class': 'ac t_leechers'}).text)

                    if not all([title, download_url]):
                        continue

                    item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders,
                            'leechers': leechers, 'hash': ''}

                    if mode != 'RSS':
                        sickrage.srCore.srLogger.debug("Found result: {}".format(title))

                    results.append(item)
                except Exception:
                    sickrage.srCore.srLogger.error("Failed parsing provider")

        return results