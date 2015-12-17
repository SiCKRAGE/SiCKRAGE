# -*- coding: utf-8 -*-
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
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
import re
import datetime
import json
import time

import logging
from sickbeard import tvcache
from sickbeard.providers import generic
from sickbeard.common import USER_AGENT
from sickbeard.indexers.indexer_config import INDEXER_TVDB


class GetOutOfLoop(Exception):
    pass


class RarbgProvider(generic.TorrentProvider):
    def __init__(self):
        generic.TorrentProvider.__init__(self, "Rarbg")

        self.supportsBacklog = True
        self.public = True
        self.ratio = None
        self.minseed = None
        self.ranked = None
        self.sorting = None
        self.minleech = None
        self.token = None
        self.tokenExpireDate = None

        self.urls = {'url': 'https://rarbg.com',
                     'token': 'http://torrentapi.org/pubapi_v2.php?get_token=get_token&format=json&app_id=sickrage',
                     'listing': 'http://torrentapi.org/pubapi_v2.php?mode=list&app_id=sickrage',
                     'search': 'http://torrentapi.org/pubapi_v2.php?mode=search&app_id=sickrage&search_string={search_string}',
                     'search_tvdb': 'http://torrentapi.org/pubapi_v2.php?mode=search&app_id=sickrage&search_tvdb={tvdb}&search_string={search_string}',
                     'api_spec': 'https://rarbg.com/pubapi/apidocs.txt'}

        self.url = self.urls[b'listing']

        self.urlOptions = {'categories': '&category={categories}',
                           'seeders': '&min_seeders={min_seeders}',
                           'leechers': '&min_leechers={min_leechers}',
                           'sorting': '&sort={sorting}',
                           'limit': '&limit={limit}',
                           'format': '&format={format}',
                           'ranked': '&ranked={ranked}',
                           'token': '&token={token}'}

        self.defaultOptions = self.urlOptions[b'categories'].format(categories='tv') + \
                              self.urlOptions[b'limit'].format(limit='100') + \
                              self.urlOptions[b'format'].format(format='json_extended')

        self.proper_strings = ['{{PROPER|REPACK}}']

        self.next_request = datetime.datetime.now()

        self.headers.update({'User-Agent': USER_AGENT})

        self.cache = RarbgCache(self)

    def _doLogin(self):
        if self.token and self.tokenExpireDate and datetime.datetime.now() < self.tokenExpireDate:
            return True

        response = self.getURL(self.urls[b'token'], timeout=30, json=True)
        if not response:
            logging.warning("Unable to connect to provider")
            return False

        try:
            if response[b'token']:
                self.token = response[b'token']
                self.tokenExpireDate = datetime.datetime.now() + datetime.timedelta(minutes=14)
                return True
        except Exception as e:
            logging.warning("No token found")
            logging.debug("No token found: %s" % repr(e))

        return False

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return results

        if epObj != None:
            ep_indexerid = epObj.show.indexerid
            ep_indexer = epObj.show.indexer
        else:
            ep_indexerid = None
            ep_indexer = None

        for mode in search_params.keys():  # Mode = RSS, Season, Episode
            logging.debug("Search Mode: %s" % mode)
            for search_string in search_params[mode]:

                if mode is not 'RSS':
                    logging.debug("Search string: %s " % search_string)

                if mode is 'RSS':
                    searchURL = self.urls[b'listing'] + self.defaultOptions
                elif mode == 'Season':
                    if ep_indexer == INDEXER_TVDB:
                        searchURL = self.urls[b'search_tvdb'].format(search_string=search_string,
                                                                    tvdb=ep_indexerid) + self.defaultOptions
                    else:
                        searchURL = self.urls[b'search'].format(search_string=search_string) + self.defaultOptions
                elif mode == 'Episode':
                    if ep_indexer == INDEXER_TVDB:
                        searchURL = self.urls[b'search_tvdb'].format(search_string=search_string,
                                                                    tvdb=ep_indexerid) + self.defaultOptions
                    else:
                        searchURL = self.urls[b'search'].format(search_string=search_string) + self.defaultOptions
                else:
                    logging.error("Invalid search mode: %s " % mode)

                if self.minleech:
                    searchURL += self.urlOptions[b'leechers'].format(min_leechers=int(self.minleech))

                if self.minseed:
                    searchURL += self.urlOptions[b'seeders'].format(min_seeders=int(self.minseed))

                if self.sorting:
                    searchURL += self.urlOptions[b'sorting'].format(sorting=self.sorting)

                if self.ranked:
                    searchURL += self.urlOptions[b'ranked'].format(ranked=int(self.ranked))

                logging.debug("Search URL: %s" % searchURL)

                try:
                    retry = 3
                    while retry > 0:
                        time_out = 0
                        while (datetime.datetime.now() < self.next_request) and time_out <= 15:
                            time_out = time_out + 1
                            time.sleep(1)

                        data = self.getURL(searchURL + self.urlOptions[b'token'].format(token=self.token))

                        self.next_request = datetime.datetime.now() + datetime.timedelta(seconds=10)

                        if not data:
                            logging.debug("No data returned from provider")
                            raise GetOutOfLoop
                        if re.search('ERROR', data):
                            logging.debug("Error returned from provider")
                            raise GetOutOfLoop
                        if re.search('No results found', data):
                            logging.debug("No results found")
                            raise GetOutOfLoop
                        if re.search('Invalid token set!', data):
                            logging.warning("Invalid token!")
                            return results
                        if re.search('Too many requests per minute. Please try again later!', data):
                            logging.warning("Too many requests per minute")
                            retry = retry - 1
                            time.sleep(10)
                            continue
                        if re.search('Cant find search_tvdb in database. Are you sure this imdb exists?', data):
                            logging.warning("No results found. The tvdb id: %s do not exist on provider" % ep_indexerid)
                            raise GetOutOfLoop
                        if re.search('Invalid token. Use get_token for a new one!', data):
                            logging.debug("Invalid token, retrieving new token")
                            retry = retry - 1
                            self.token = None
                            self.tokenExpireDate = None
                            if not self._doLogin():
                                logging.debug("Failed retrieving new token")
                                return results
                            logging.debug("Using new token")
                            continue

                        # No error found break
                        break
                    else:
                        logging.debug("Retried 3 times without getting results")
                        continue
                except GetOutOfLoop:
                    continue

                try:
                    data = re.search(r'\[\{\"title\".*\}\]', data)
                    if data is not None:
                        data_json = json.loads(data.group())
                    else:
                        data_json = {}
                except Exception:
                    logging.error("JSON load failed: %s" % traceback.format_exc())
                    logging.debug("JSON load failed. Data dump: %s" % data)
                    continue

                try:
                    for item in data_json:
                        try:
                            title = item[b'title']
                            download_url = item[b'download']
                            size = item[b'size']
                            seeders = item[b'seeders']
                            leechers = item[b'leechers']
                            # pubdate = item[b'pubdate']

                            if not all([title, download_url]):
                                continue

                            item = title, download_url, size, seeders, leechers
                            if mode is not 'RSS':
                                logging.debug("Found result: %s " % title)
                            items[mode].append(item)

                        except Exception:
                            logging.debug("Skipping invalid result. JSON item: %s" % item)

                except Exception:
                    logging.error("Failed parsing provider. Traceback: %s" % traceback.format_exc())

            # For each search mode sort all the items by seeders
            items[mode].sort(key=lambda tup: tup[3], reverse=True)
            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class RarbgCache(tvcache.TVCache):
    def __init__(self, provider_obj):
        tvcache.TVCache.__init__(self, provider_obj)

        # only poll RARBG every 10 minutes max
        self.minTime = 10

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}


provider = RarbgProvider()
