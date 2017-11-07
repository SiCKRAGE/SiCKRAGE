# coding=utf-8
# Author: Ludovic Reenaers <ludovic.reenaers@gmail.com>
#
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, unicode_literals

import re
from urlparse import urljoin

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, try_int, convert_size
from sickrage.providers import TorrentProvider


class Torrent9Provider(TorrentProvider):
    def __init__(self):
        super(Torrent9Provider, self).__init__('Torrent9', 'http://www.torrent9.biz', False)

        self.urls.update({
            'search': '{base_url}/search_torrent'.format(**self.urls),
            'rss': '{base_url}/torrents_series.html,trie-date-d'.format(**self.urls)
        })

        self.minseed = None
        self.minleech = None

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = TVCache(self)

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals
        results = []

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: {0}".format(mode))
            for search_string in search_strings[mode]:
                if mode == 'Season':
                    search_string = re.sub(r'(.*)S0?', r'\1Saison ', search_string)

                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: {0}".format
                                                   (search_string))

                    search_string = search_string.replace('.', '-').replace(' ', '-')

                    search_url = urljoin(self.urls['search'],
                                         "{search_string}.html,trie-seeds-d".format(search_string=search_string))
                else:
                    search_url = self.urls['rss']

                try:
                    data = sickrage.app.srWebSession.get(search_url).text
                    results += self.parse(data, mode)
                except Exception:
                    sickrage.app.log.debug("No data returned from provider")

        return results

    def parse(self, data, mode):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []

        with bs4_parser(data) as html:
            torrent_rows = html.findAll('tr')
            for result in torrent_rows:
                try:
                    title = result.find('a').get_text(strip=False).replace("HDTV", "HDTV x264-Torrent9")
                    title = re.sub(r' Saison', ' Season', title, flags=re.I)
                    tmp = result.find("a")['href'].split('/')[-1].replace('.html', '.torrent').strip()
                    download_url = (self.urls['base_url'] + '/get_torrent/{0}'.format(tmp) + ".torrent")
                    if not all([title, download_url]):
                        continue

                    seeders = try_int(result.find(class_="seed_ok").get_text(strip=True))
                    leechers = try_int(result.find_all('td')[3].get_text(strip=True))
                    torrent_size = result.find_all('td')[1].get_text(strip=True)

                    size = convert_size(torrent_size, -1, ['o', 'Ko', 'Mo', 'Go', 'To', 'Po'])

                    item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders,
                            'leechers': leechers, 'hash': ''}

                    if mode != 'RSS':
                        sickrage.app.log.debug("Found result: {}".format(title))

                    results.append(item)
                except Exception:
                    sickrage.app.log.error("Failed parsing provider")

        return results