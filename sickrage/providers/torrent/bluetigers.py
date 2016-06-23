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
        super(BLUETIGERSProvider, self).__init__("BLUETIGERS",'www.bluetigers.ca')

        self.supportsBacklog = True

        self.username = None
        self.password = None
        self.ratio = None
        self.token = None
        self.tokenLastUpdate = None

        self.cache = BLUETIGERSCache(self)

        self.urls.update({
            'search': '{base_url}/torrents-search.php'.format(base_url=self.urls['base_url']),
            'login': '{base_url}/account-login.php'.format(base_url=self.urls['base_url']),
            'download': '{base_url}/torrents-details.php?id=%s&hit=1'.format(base_url=self.urls['base_url'])
        })

        self.search_params = {
            "c16": 1, "c10": 1, "c130": 1, "c131": 1, "c17": 1, "c18": 1, "c19": 1
        }

    def _doLogin(self):
        if any(requests.utils.dict_from_cookiejar(sickrage.srCore.srWebSession.cookies).values()):
            return True

        login_params = {
            'username': self.username,
            'password': self.password,
            'take_login': '1'
        }

        try:
            response = sickrage.srCore.srWebSession.post(self.urls['login'], data=login_params, timeout=30).text
        except Exception:
            sickrage.srCore.srLogger.warning("[{}]: Unable to connect to provider".format(self.name))
            return False

        if not re.search('/account-logout.php', response):
            sickrage.srCore.srLogger.warning("[{}]: Invalid username or password. Check your settings".format(self.name))
            return False

        return True

    def search(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        # check for auth
        if not self._doLogin():
            return results

        for mode in search_strings.keys():
            sickrage.srCore.srLogger.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug("Search string: %s " % search_string)

                self.search_params['search'] = search_string

                try:
                    data = sickrage.srCore.srWebSession.get(self.urls['search'], params=self.search_params).text
                except Exception:
                    sickrage.srCore.srLogger.debug("No data returned from provider")
                    continue

                try:
                    with bs4_parser(data) as html:
                        result_linkz = html.findAll('a', href=re.compile("torrents-details"))

                        if not result_linkz:
                            sickrage.srCore.srLogger.debug("Data returned from provider do not contains any torrent")
                            continue

                        if result_linkz:
                            for link in result_linkz:
                                title = link.text
                                download_url = self.urls['base_url'] + "/" + link['href']
                                download_url = download_url.replace("torrents-details", "download")
                                # FIXME
                                size = -1
                                seeders = 1
                                leechers = 0

                                if not title or not download_url:
                                    continue

                                # Filter unseeded torrent
                                # if seeders < self.minseed or leechers < self.minleech:
                                #    if mode != 'RSS':
                                #        LOGGER.debug(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers))
                                #    continue

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


class BLUETIGERSAuth(AuthBase):
    """Attaches HTTP Authentication to the given Request object."""

    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = self.token
        return r


class BLUETIGERSCache(tv_cache.TVCache):
    def __init__(self, provider_obj):
        tv_cache.TVCache.__init__(self, provider_obj)

        # Only poll BLUETIGERS every 10 minutes max
        self.minTime = 10

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider.search(search_strings)}
