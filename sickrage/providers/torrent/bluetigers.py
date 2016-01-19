#!/usr/bin/env python2

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

import re
import traceback

import requests
from requests.auth import AuthBase

import sickrage
from sickrage.core.caches import tv_cache
from sickrage.core.helpers import bs4_parser
from sickrage.providers import TorrentProvider


class BLUETIGERSProvider(TorrentProvider):
    def __init__(self):
        super(BLUETIGERSProvider, self).__init__("BLUETIGERS")

        self.supportsBacklog = True

        self.username = None
        self.password = None
        self.ratio = None
        self.token = None
        self.tokenLastUpdate = None

        self.cache = BLUETIGERSCache(self)

        self.urls = {
            'base_url': 'https://www.bluetigers.ca/',
            'search': 'https://www.bluetigers.ca/torrents-search.php',
            'login': 'https://www.bluetigers.ca/account-login.php',
            'download': 'https://www.bluetigers.ca/torrents-details.php?id=%s&hit=1',
        }

        self.search_params = {
            "c16": 1, "c10": 1, "c130": 1, "c131": 1, "c17": 1, "c18": 1, "c19": 1
        }

        self.url = self.urls['base_url']

    def _doLogin(self):
        if any(requests.utils.dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {
            'username': self.username,
            'password': self.password,
            'take_login': '1'
        }

        response = self.getURL(self.urls['login'], post_data=login_params, timeout=30)
        if not response:
            sickrage.LOGGER.warning("Unable to connect to provider")
            return False

        if not re.search('/account-logout.php', response):
            sickrage.LOGGER.warning("Invalid username or password. Check your settings")
            return False

        return True

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        # check for auth
        if not self._doLogin():
            return results

        for mode in search_strings.keys():
            sickrage.LOGGER.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:

                if mode is not 'RSS':
                    sickrage.LOGGER.debug("Search string: %s " % search_string)

                self.search_params[b'search'] = search_string

                data = self.getURL(self.urls['search'], params=self.search_params)
                if not data:
                    continue

                try:
                    with bs4_parser(data) as html:
                        result_linkz = html.findAll('a', href=re.compile("torrents-details"))

                        if not result_linkz:
                            sickrage.LOGGER.debug("Data returned from provider do not contains any torrent")
                            continue

                        if result_linkz:
                            for link in result_linkz:
                                title = link.text
                                download_url = self.urls['base_url'] + "/" + link[b'href']
                                download_url = download_url.replace("torrents-details", "download")
                                # FIXME
                                size = -1
                                seeders = 1
                                leechers = 0

                                if not title or not download_url:
                                    continue

                                # Filter unseeded torrent
                                # if seeders < self.minseed or leechers < self.minleech:
                                #    if mode is not 'RSS':
                                #        sickrage.LOGGER.debug(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers))
                                #    continue

                                item = title, download_url, size, seeders, leechers
                                if mode is not 'RSS':
                                    sickrage.LOGGER.debug("Found result: %s " % title)

                                items[mode].append(item)

                except Exception as e:
                    sickrage.LOGGER.error("Failed parsing provider. Traceback: %s" % traceback.format_exc())

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class BLUETIGERSAuth(AuthBase):
    """Attaches HTTP Authentication to the given Request object."""

    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers[b'Authorization'] = self.token
        return r


class BLUETIGERSCache(tv_cache.TVCache):
    def __init__(self, provider_obj):
        tv_cache.TVCache.__init__(self, provider_obj)

        # Only poll BLUETIGERS every 10 minutes max
        self.minTime = 10

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_strings)}
