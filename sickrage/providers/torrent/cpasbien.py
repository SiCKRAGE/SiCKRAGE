#!/usr/bin/env python2

# Author: echel0n <echel0n@sickrage.ca>
# URL: https://git.sickrage.ca
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

import traceback

import sickrage
from sickrage.core.caches import tv_cache
from sickrage.core.helpers import bs4_parser
from sickrage.providers import TorrentProvider


class CpasbienProvider(TorrentProvider):
    def __init__(self):
        super(CpasbienProvider, self).__init__("Cpasbien","www.cpasbien.io")

        self.supportsBacklog = True

        self.ratio = None
        self.urls.update({
            'download': '{base_url}/telechargement/%s'.format(base_url=self.urls['base_url'])
        })

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = CpasbienCache(self)

    def search(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        size = -1
        seeders = 1
        leechers = 0

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

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

    def seedRatio(self):
        return self.ratio


class CpasbienCache(tv_cache.TVCache):
    def __init__(self, provider_obj):
        tv_cache.TVCache.__init__(self, provider_obj)

        self.minTime = 30

    def _getRSSData(self):
        # search_strings = {'RSS': ['']}
        return {'entries': {}}
