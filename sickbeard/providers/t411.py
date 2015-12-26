#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Author: echel0n <sickrage.tv@gmail.com>
# URL: http://www.github.com/sickragetv/sickrage/
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

import time
import logging
import traceback
from requests.auth import AuthBase
from sickbeard import tvcache
from sickbeard.providers import generic


class T411Provider(generic.TorrentProvider):
    def __init__(self):
        generic.TorrentProvider.__init__(self, "T411")

        self.supportsBacklog = True

        self.username = None
        self.password = None
        self.ratio = None
        self.token = None
        self.tokenLastUpdate = None

        self.cache = T411Cache(self)

        self.urls = {'base_url': 'http://www.t411.in/',
                     'search': 'https://api.t411.in/torrents/search/%s?cid=%s&limit=100',
                     'rss': 'https://api.t411.in/torrents/top/today',
                     'login_page': 'https://api.t411.in/auth',
                     'download': 'https://api.t411.in/torrents/download/%s'}

        self.url = self.urls[b'base_url']

        self.subcategories = [433, 637, 455, 639]

        self.minseed = 0
        self.minleech = 0
        self.confirmed = False

    def _doLogin(self):

        if self.token is not None:
            if time.time() < (self.tokenLastUpdate + 30 * 60):
                return True

        login_params = {'username': self.username,
                        'password': self.password}

        response = self.getURL(self.urls[b'login_page'], post_data=login_params, timeout=30, json=True)
        if not response:
            logging.warning("Unable to connect to provider")
            return False

        if response and 'token' in response:
            self.token = response[b'token']
            self.tokenLastUpdate = time.time()
            self.uid = response[b'uid'].encode('ascii', 'ignore')
            self.session.auth = T411Auth(self.token)
            return True
        else:
            logging.warning("Token not found in authentication response")
            return False

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return results

        for mode in search_params.keys():
            logging.debug("Search Mode: %s" % mode)
            for search_string in search_params[mode]:

                if mode is not 'RSS':
                    logging.debug("Search string: %s " % search_string)

                searchURLS = \
                ([self.urls[b'search'] % (search_string, u) for u in self.subcategories], [self.urls[b'rss']])[
                    mode is 'RSS']
                for searchURL in searchURLS:
                    logging.debug("Search URL: %s" % searchURL)
                    data = self.getURL(searchURL, json=True)
                    if not data:
                        continue

                    try:
                        if 'torrents' not in data and mode is not 'RSS':
                            logging.debug("Data returned from provider does not contain any torrents")
                            continue

                        torrents = data[b'torrents'] if mode is not 'RSS' else data

                        if not torrents:
                            logging.debug("Data returned from provider does not contain any torrents")
                            continue

                        for torrent in torrents:
                            if mode is 'RSS' and int(torrent[b'category']) not in self.subcategories:
                                continue

                            try:
                                title = torrent[b'name']
                                torrent_id = torrent[b'id']
                                download_url = (self.urls[b'download'] % torrent_id).encode('utf8')
                                if not all([title, download_url]):
                                    continue

                                size = int(torrent[b'size'])
                                seeders = int(torrent[b'seeders'])
                                leechers = int(torrent[b'leechers'])
                                verified = bool(torrent[b'isVerified'])

                                # Filter unseeded torrent
                                if seeders < self.minseed or leechers < self.minleech:
                                    if mode is not 'RSS':
                                        logging.debug(
                                            "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                                title, seeders, leechers))
                                    continue

                                if self.confirmed and not verified and mode is not 'RSS':
                                    logging.debug(
                                        "Found result " + title + " but that doesn't seem like a verified result so I'm ignoring it")
                                    continue

                                item = title, download_url, size, seeders, leechers
                                if mode is not 'RSS':
                                    logging.debug("Found result: %s " % title)

                                items[mode].append(item)

                            except Exception:
                                logging.debug("Invalid torrent data, skipping result: %s" % torrent)
                                logging.debug("Failed parsing provider. Traceback: %s" % traceback.format_exc())
                                continue

                    except Exception:
                        logging.error("Failed parsing provider. Traceback: %s" % traceback.format_exc())

            # For each search mode sort all the items by seeders if available if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class T411Auth(AuthBase):
    """Attaches HTTP Authentication to the given Request object."""

    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers[b'Authorization'] = self.token
        return r


class T411Cache(tvcache.TVCache):
    def __init__(self, provider_obj):
        tvcache.TVCache.__init__(self, provider_obj)

        # Only poll T411 every 10 minutes max
        self.minTime = 10

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}


provider = T411Provider()
