# Author: echel0n <echel0n@sickrage.ca>
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

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, try_int
from sickrage.providers import TorrentProvider


class CpasbienProvider(TorrentProvider):
    def __init__(self):
        super(CpasbienProvider, self).__init__("Cpasbien", "http://www.cpasbien.io", False)

        self.urls.update({
            'download': '{base_url}/telechargement/%s'.format(**self.urls)
        })

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = TVCache(self, min_time=30)

    def search(self, search_params, age=0, ep_obj=None):
        results = []

        size = -1
        seeders = 1
        leechers = 0

        for mode in search_params.keys():
            sickrage.srCore.srLogger.debug("Search Mode: %s" % mode)
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug("Search string: %s " % search_string)

                searchURL = self.urls['base_url'] + '/recherche/' + search_string.replace('.', '-') + '.html'
                sickrage.srCore.srLogger.debug("Search URL: %s" % searchURL)

                try:
                    data = sickrage.srCore.srWebSession.get(searchURL).text
                except Exception:
                    sickrage.srCore.srLogger.debug("No data returned from provider")
                    continue

                try:
                    with bs4_parser(data) as html:
                        lin = erlin = 0
                        resultdiv = []
                        while erlin == 0:
                            try:
                                classlin = 'ligne' + str(lin)
                                resultlin = html.findAll(attrs={'class': [classlin]})
                                if resultlin:
                                    for ele in resultlin:
                                        resultdiv.append(ele)
                                    lin += 1
                                else:
                                    erlin = 1
                            except Exception:
                                erlin = 1

                        for row in resultdiv:
                            try:
                                link = row.find("a", title=True)
                                title = link.text.lower().strip()
                                pageURL = link['href']

                                # downloadTorrentLink = torrentSoup.find("a", title.startswith('Cliquer'))
                                tmp = pageURL.split('/')[-1].replace('.html', '.torrent')

                                downloadTorrentLink = (self.urls['download'] % tmp)

                                if downloadTorrentLink:
                                    download_url = downloadTorrentLink
                                    size = -1
                                    seeders = 1
                                    leechers = 0

                            except (AttributeError, TypeError):
                                continue

                            if not all([title, download_url]):
                                continue

                            item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders,
                                    'leechers': leechers, 'hash': ''}

                            if mode != 'RSS':
                                sickrage.srCore.srLogger.debug("Found result: {}".format(title))

                            results.append(item)
                except Exception:
                    sickrage.srCore.srLogger.error("Failed parsing provider.")

        # Sort all the items by seeders if available
        results.sort(key=lambda k: try_int(k.get('seeders', 0)), reverse=True)

        return results

    def parse(self, data, mode):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []