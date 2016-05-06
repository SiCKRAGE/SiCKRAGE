# Author: Mr_Orange
# URL: http://github.com/SiCKRAGETV/SickRage/
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
import urllib

import sickrage
from sickrage.core.caches import tv_cache
from sickrage.core.helpers import show_names, bs4_parser
from sickrage.providers import TorrentProvider


class TokyoToshokanProvider(TorrentProvider):
    def __init__(self):

        super(TokyoToshokanProvider, self).__init__("TokyoToshokan",'tokyotosho.info')

        self.supportsBacklog = True

        self.supportsAbsoluteNumbering = True
        self.anime_only = True
        self.ratio = None

        self.cache = TokyoToshokanCache(self)

    def seedRatio(self):
        return self.ratio

    def _get_season_search_strings(self, ep_obj):
        return [x.replace('.', ' ') for x in show_names.makeSceneSeasonSearchString(self.show, ep_obj)]

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        return [x.replace('.', ' ') for x in show_names.makeSceneSearchString(self.show, ep_obj)]

    def search(self, search_string, search_mode='eponly', epcount=0, age=0, epObj=None):
        # FIXME ADD MODE
        if self.show and not self.show.is_anime:
            return []

        sickrage.srCore.srLogger.debug("Search string: %s " % search_string)

        params = {
            "terms": search_string.encode('utf-8'),
            "type": 1,  # get anime types
        }

        searchURL = self.urls['base_url'] + '/search.php?' + urllib.urlencode(params)
        sickrage.srCore.srLogger.debug("Search URL: %s" % searchURL)

        try:
            data = sickrage.srCore.srWebSession.get(searchURL).text
        except Exception:
            sickrage.srCore.srLogger.debug("No data returned from provider")
            return []

        results = []
        try:
            with bs4_parser(data) as html:
                torrent_table = html.find('table', attrs={'class': 'listing'})
                torrent_rows = torrent_table.find_all('tr') if torrent_table else []
                if torrent_rows:
                    if torrent_rows[0].find('td', attrs={'class': 'centertext'}):
                        a = 1
                    else:
                        a = 0

                    for top, bottom in zip(torrent_rows[a::2], torrent_rows[a::2]):
                        title = top.find('td', attrs={'class': 'desc-top'}).text
                        title.lstrip()
                        download_url = top.find('td', attrs={'class': 'desc-top'}).find('a')['href']
                        # FIXME
                        size = -1
                        seeders = 1
                        leechers = 0

                        if not all([title, download_url]):
                            continue

                        # Filter unseeded torrent
                        # if seeders < self.minseed or leechers < self.minleech:
                        #    if mode != 'RSS':
                        #        LOGGER.debug(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers))
                        #    continue

                        item = title, download_url, size, seeders, leechers

                        results.append(item)

        except Exception as e:
            sickrage.srCore.srLogger.error("Failed parsing provider. Traceback: %s" % traceback.format_exc())

        # FIXME SORTING
        return results


class TokyoToshokanCache(tv_cache.TVCache):
    def __init__(self, provider_obj):
        tv_cache.TVCache.__init__(self, provider_obj)

        # only poll NyaaTorrents every 15 minutes max
        self.minTime = 15

    def _getRSSData(self):
        params = {
            "filter": '1',
        }

        url = self.provider.url + 'rss.php?' + urllib.urlencode(params)

        sickrage.srCore.srLogger.debug("Cache update URL: %s" % url)

        return self.getRSSFeed(url)
