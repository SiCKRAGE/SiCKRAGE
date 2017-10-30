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

import datetime
from time import sleep

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import convert_size, try_int
from sickrage.indexers.config import INDEXER_TVDB
from sickrage.providers import TorrentProvider


class RarbgProvider(TorrentProvider):
    def __init__(self):
        super(RarbgProvider, self).__init__("Rarbg", 'http://torrentapi.org', False)

        self.urls.update({
            'token': '{base_url}/pubapi_v2.php?get_token=get_token&format=json&app_id=sickrage'.format(**self.urls),
            'listing': '{base_url}/pubapi_v2.php?mode=list&app_id=sickrage'.format(**self.urls),
            'search': '{base_url}/pubapi_v2.php?mode=search&app_id=sickrage&search_string=%s'.format(**self.urls),
            'search_tvdb': '{base_url}/pubapi_v2.php'
                           '?mode=search'
                           '&app_id=sickrage'
                           '&search_tvdb=%s'
                           '&search_string=%s'.format(**self.urls),
            'api_spec': '{base_url}/apidocs_v2.txt'.format(**self.urls)
        })

        self.minseed = None
        self.ranked = None
        self.sorting = None
        self.minleech = None
        self.token = None
        self.tokenExpireDate = None

        self.urlOptions = {'categories': '&category={categories}',
                           'seeders': '&min_seeders={min_seeders}',
                           'leechers': '&min_leechers={min_leechers}',
                           'sorting': '&sort={sorting}',
                           'limit': '&limit={limit}',
                           'format': '&format={format}',
                           'ranked': '&ranked={ranked}',
                           'token': '&token={token}'}

        self.defaultOptions = self.urlOptions['categories'].format(categories='tv') + \
                              self.urlOptions['limit'].format(limit='100') + \
                              self.urlOptions['format'].format(format='json_extended')

        self.proper_strings = ['{{PROPER|REPACK}}']

        self.next_request = datetime.datetime.now()

        self.cache = TVCache(self, min_time=10)

    def login(self, reset=False):
        if not reset and self.token and self.tokenExpireDate and datetime.datetime.now() < self.tokenExpireDate:
            return True

        try:
            response = sickrage.srCore.srWebSession.get(self.urls['token'], timeout=30).json()
        except Exception:
            sickrage.srCore.srLogger.warning("[{}]: Unable to connect to provider".format(self.name))
            return False

        self.token = response.get('token')
        self.tokenExpireDate = datetime.datetime.now() + datetime.timedelta(minutes=14) if self.token else None

        return self.token is not None

    def search(self, search_params, age=0, ep_obj=None):
        results = []

        if not self.login():
            return results

        if ep_obj is not None:
            ep_indexerid = ep_obj.show.indexerid
            ep_indexer = ep_obj.show.indexer
        else:
            ep_indexerid = None
            ep_indexer = None

        for mode in search_params.keys():  # Mode = RSS, Season, Episode
            sickrage.srCore.srLogger.debug("Search Mode: %s" % mode)
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug("Search string: %s " % search_string)

                if mode == 'RSS':
                    searchURL = self.urls['listing'] + self.defaultOptions
                elif mode == 'Season':
                    if ep_indexer == INDEXER_TVDB:
                        searchURL = self.urls['search_tvdb'] % (ep_indexerid, search_string) + self.defaultOptions
                    else:
                        searchURL = self.urls['search'] % search_string + self.defaultOptions
                elif mode == 'Episode':
                    if ep_indexer == INDEXER_TVDB:
                        searchURL = self.urls['search_tvdb'] % (ep_indexerid, search_string) + self.defaultOptions
                    else:
                        searchURL = self.urls['search'] % (search_string) + self.defaultOptions
                else:
                    sickrage.srCore.srLogger.error("Invalid search mode: %s " % mode)

                if self.minleech:
                    searchURL += self.urlOptions['leechers'].format(min_leechers=int(self.minleech))

                if self.minseed:
                    searchURL += self.urlOptions['seeders'].format(min_seeders=int(self.minseed))

                if self.sorting:
                    searchURL += self.urlOptions['sorting'].format(sorting=self.sorting)

                if self.ranked:
                    searchURL += self.urlOptions['ranked'].format(ranked=int(self.ranked))

                sickrage.srCore.srLogger.debug("Search URL: %s" % searchURL)

                for r in range(0, 3):
                    try:
                        data = sickrage.srCore.srWebSession.get(
                            searchURL + self.urlOptions['token'].format(token=self.token)).json()
                    except Exception:
                        sickrage.srCore.srLogger.debug("No data returned from provider")
                        return results

                    if data.get('error'):
                        if data.get('error_code') == 4:
                            if not self.login(True): return results
                            continue
                        elif data.get('error_code') == 5:
                            sleep(5)
                            continue
                        elif data.get('error_code') != 20:
                            sickrage.srCore.srLogger.debug(data['error'])
                            continue

                    for item in data.get('torrent_results') or []:
                        try:
                            title = item['title']
                            download_url = item['download']
                            size = convert_size(item['size'], -1)
                            seeders = item['seeders']
                            leechers = item['leechers']
                            # pubdate = item['pubdate']

                            if not all([title, download_url]):
                                continue

                            item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders,
                                    'leechers': leechers, 'hash': ''}

                            if mode != 'RSS':
                                sickrage.srCore.srLogger.debug("Found result: {}".format(title))
                            results.append(item)
                        except Exception:
                            continue
                    break

        # Sort all the items by seeders
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