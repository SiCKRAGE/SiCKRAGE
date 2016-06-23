# Author: echel0n <echel0n@sickrage.ca>
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

import datetime
import json
import re
import time
import traceback

import sickrage
from sickrage.core.caches import tv_cache
from sickrage.indexers.config import INDEXER_TVDB
from sickrage.providers import TorrentProvider

class RarbgProvider(TorrentProvider):
    def __init__(self):
        super(RarbgProvider, self).__init__("Rarbg",'torrentapi.org')

        self.supportsBacklog = True

        self.ratio = None
        self.minseed = None
        self.ranked = None
        self.sorting = None
        self.minleech = None
        self.token = None
        self.tokenExpireDate = None

        self.urls.update({
            'token': '{base_url}/pubapi_v2.php?get_token=get_token&format=json&app_id=sickrage'.format(base_url=self.urls['base_url']),
            'listing': '{base_url}/pubapi_v2.php?mode=list&app_id=sickrage'.format(base_url=self.urls['base_url']),
            'search': '{base_url}/pubapi_v2.php?mode=search&app_id=sickrage&search_string=%s'.format(base_url=self.urls['base_url']),
            'search_tvdb': '{base_url}/pubapi_v2.php?mode=search&app_id=sickrage&search_tvdb=%s&search_string=%s'.format(base_url=self.urls['base_url']),
            'api_spec': '{base_url}/apidocs_v2.txt'.format(base_url=self.urls['base_url'])
        })

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

        self.cache = RarbgCache(self)

    def _doLogin(self):
        if self.token and self.tokenExpireDate and datetime.datetime.now() < self.tokenExpireDate:
            return True

        try:
            response = sickrage.srCore.srWebSession.get(self.urls['token'], timeout=30).json()
        except Exception:
            sickrage.srCore.srLogger.warning("[{}]: Unable to connect to provider".format(self.name))
            return False

        try:
            if response['token']:
                self.token = response['token']
                self.tokenExpireDate = datetime.datetime.now() + datetime.timedelta(minutes=14)
                return True
        except Exception as e:
            sickrage.srCore.srLogger.warning("No token found")
            sickrage.srCore.srLogger.debug("No token found: %s" % repr(e))

        return False

    def search(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return results

        if epObj is not None:
            ep_indexerid = epObj.show.indexerid
            ep_indexer = epObj.show.indexer
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
                        searchURL = self.urls['search'] % (search_string) + self.defaultOptions
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

                try:
                    retry = 3
                    while retry > 0:
                        time_out = 0
                        while (datetime.datetime.now() < self.next_request) and time_out <= 15:
                            time_out = time_out + 1
                            time.sleep(1)

                        self.next_request = datetime.datetime.now() + datetime.timedelta(seconds=10)

                        try:
                            data = sickrage.srCore.srWebSession.get(searchURL + self.urlOptions['token'].format(token=self.token)).text
                        except Exception:
                            sickrage.srCore.srLogger.debug("No data returned from provider")
                            raise StopIteration

                        if re.search('ERROR', data):
                            sickrage.srCore.srLogger.debug("Error returned from provider")
                            raise StopIteration
                        if re.search('No results found', data):
                            sickrage.srCore.srLogger.debug("No results found")
                            raise StopIteration
                        if re.search('Invalid token set!', data):
                            sickrage.srCore.srLogger.warning("Invalid token!")
                            return results
                        if re.search('Too many requests per minute. Please try again later!', data):
                            sickrage.srCore.srLogger.warning("Too many requests per minute")
                            retry = retry - 1
                            time.sleep(10)
                            continue
                        if re.search('Cant find search_tvdb in database. Are you sure this imdb exists?', data):
                            sickrage.srCore.srLogger.warning(
                                "No results found. The tvdb id: %s do not exist on provider" % ep_indexerid)
                            raise StopIteration
                        if re.search('Invalid token. Use get_token for a new one!', data):
                            sickrage.srCore.srLogger.debug("Invalid token, retrieving new token")
                            retry = retry - 1
                            self.token = None
                            self.tokenExpireDate = None
                            if not self._doLogin():
                                sickrage.srCore.srLogger.debug("Failed retrieving new token")
                                return results
                            sickrage.srCore.srLogger.debug("Using new token")
                            continue

                        # No error found break
                        break
                    else:
                        sickrage.srCore.srLogger.debug("Retried 3 times without getting results")
                        continue
                except StopIteration:
                    continue

                try:
                    data = re.search(r'\[\{\"title\".*\}\]', data)
                    if data is not None:
                        data_json = json.loads(data.group())
                    else:
                        data_json = {}
                except Exception:
                    sickrage.srCore.srLogger.error("JSON load failed: %s" % traceback.format_exc())
                    sickrage.srCore.srLogger.debug("JSON load failed. Data dump: %s" % data)
                    continue

                try:
                    for item in data_json:
                        try:
                            title = item['title']
                            download_url = item['download']
                            size = item['size']
                            seeders = item['seeders']
                            leechers = item['leechers']
                            # pubdate = item['pubdate']

                            if not all([title, download_url]):
                                continue

                            item = title, download_url, size, seeders, leechers
                            if mode != 'RSS':
                                sickrage.srCore.srLogger.debug("Found result: %s " % title)
                            items[mode].append(item)

                        except Exception:
                            sickrage.srCore.srLogger.debug("Skipping invalid result. JSON item: {}".format(item))

                except Exception:
                    sickrage.srCore.srLogger.error("Failed parsing provider. Traceback: %s" % traceback.format_exc())

            # For each search mode sort all the items by seeders
            items[mode].sort(key=lambda tup: tup[3], reverse=True)
            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class RarbgCache(tv_cache.TVCache):
    def __init__(self, provider_obj):
        tv_cache.TVCache.__init__(self, provider_obj)

        # only poll RARBG every 10 minutes max
        self.minTime = 10

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider.search(search_params)}
