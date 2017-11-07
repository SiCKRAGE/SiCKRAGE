# coding=utf-8
# Author: Gonçalo M. (aka duramato/supergonkas) <supergonkas@gmail.com>
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

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, try_int, convert_size
from sickrage.providers import TorrentProvider


class LimeTorrentsProvider(TorrentProvider):
    def __init__(self):
        super(LimeTorrentsProvider, self).__init__('LimeTorrents', 'https://www.limetorrents.cc', False)

        self.urls.update({
            'search': '{base_url}/searchrss/tv/'.format(**self.urls),
            'rss': '{base_url}/rss/tv/'.format(**self.urls),
        })

        self.minseed = None
        self.minleech = None

        self.proper_strings = ['PROPER', 'REPACK', 'REAL']

        self.cache = TVCache(self, search_params={'RSS': ['rss']})

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: {0}".format(mode))
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: {0}".format
                                                   (search_string))

                search_url = (self.urls['rss'], self.urls['search'] + search_string)[mode != 'RSS']

                try:
                    data = sickrage.app.wsession.get(search_url).text
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

        if not data.startswith('<?xml'):
            sickrage.app.log.debug('Expected xml but got something else, is your mirror failing?')
            return results

        with bs4_parser(data) as html:
            entries = html('item')
            if not entries:
                sickrage.app.log.debug('Returned xml contained no results')
                return results

            for item in entries:
                try:
                    title = item.title.text
                    # Use the itorrents link limetorrents provides,
                    # unless it is not itorrents or we are not using blackhole
                    # because we want to use magnets if connecting direct to client
                    # so that proxies work.
                    download_url = item.enclosure['url']
                    if sickrage.app.config.TORRENT_METHOD != "blackhole" or 'itorrents' not in download_url:
                        download_url = item.enclosure['url']
                        # http://itorrents.org/torrent/C7203982B6F000393B1CE3A013504E5F87A46A7F.torrent?title=The-Night-of-the-Generals-(1967)[BRRip-1080p-x264-by-alE13-DTS-AC3][Lektor-i-Napisy-PL-Eng][Eng]
                        # Keep the hash a separate string for when its needed for failed
                        torrent_hash = re.match(r"(.*)([A-F0-9]{40})(.*)", download_url, re.I).group(2)
                        download_url = "magnet:?xt=urn:btih:" + torrent_hash + "&dn=" + title

                    if not (title and download_url):
                        continue

                    # seeders and leechers are presented diferently when doing a search and when looking for newly added
                    if mode == 'RSS':
                        # <![CDATA[
                        # Category: <a href="http://www.limetorrents.cc/browse-torrents/TV-shows/">TV shows</a><br /> Seeds: 1<br />Leechers: 0<br />Size: 7.71 GB<br /><br /><a href="http://www.limetorrents.cc/Owen-Hart-of-Gold-Djon91-torrent-7180661.html">More @ limetorrents.cc</a><br />
                        # ]]>
                        description = item.find('description')
                        seeders = try_int(description('br')[0].next_sibling.strip().lstrip('Seeds: '))
                        leechers = try_int(description('br')[1].next_sibling.strip().lstrip('Leechers: '))
                    else:
                        # <description>Seeds: 6982 , Leechers 734</description>
                        description = item.find('description').text.partition(',')
                        seeders = try_int(description[0].lstrip('Seeds: ').strip())
                        leechers = try_int(description[2].lstrip('Leechers ').strip())

                    torrent_size = item.find('size').text

                    size = convert_size(torrent_size, -1)

                    item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders,
                            'leechers': leechers, 'hash': ''}

                    if mode != 'RSS':
                        sickrage.app.log.debug("Found result: {}".format(title))

                    results.append(item)
                except Exception:
                    sickrage.app.log.error("Failed parsing provider")

        return results