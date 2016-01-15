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

import requests

import sickrage
from sickrage.core.caches import tv_cache
from sickrage.providers import TorrentProvider


class TorrentDayProvider(TorrentProvider):
    def __init__(self):

        super(TorrentDayProvider, self).__init__("TorrentDay")

        self.supportsBacklog = True

        self._uid = None
        self._hash = None
        self.username = None
        self.password = None
        self.ratio = None
        self.freeleech = False
        self.minseed = None
        self.minleech = None

        self.cache = TorrentDayCache(self)

        self.urls = {'base_url': 'https://classic.torrentday.com',
                     'login': 'https://classic.torrentday.com/torrents/',
                     'search': 'https://classic.torrentday.com/V3/API/API.php',
                     'download': 'https://classic.torrentday.com/download.php/%s/%s'}

        self.url = self.urls['base_url']

        self.cookies = None

        self.categories = {'Season': {'c14': 1}, 'Episode': {'c2': 1, 'c26': 1, 'c7': 1, 'c24': 1},
                           'RSS': {'c2': 1, 'c26': 1, 'c7': 1, 'c24': 1, 'c14': 1}}

    def _doLogin(self):

        if any(requests.utils.dict_from_cookiejar(self.session.cookies).values()):
            return True

        if self._uid and self._hash:
            requests.utils.add_dict_to_cookiejar(self.session.cookies, self.cookies)
        else:

            login_params = {'username': self.username,
                            'password': self.password,
                            'submit.x': 0,
                            'submit.y': 0}

            response = self.getURL(self.urls['login'], post_data=login_params, timeout=30)
            if not response:
                sickrage.LOGGER.warning("Unable to connect to provider")
                return False

            if re.search('You tried too often', response):
                sickrage.LOGGER.warning("Too many login access attempts")
                return False

            try:
                if requests.utils.dict_from_cookiejar(self.session.cookies)['uid'] and \
                        requests.utils.dict_from_cookiejar(self.session.cookies)['pass']:
                    self._uid = requests.utils.dict_from_cookiejar(self.session.cookies)['uid']
                    self._hash = requests.utils.dict_from_cookiejar(self.session.cookies)['pass']

                    self.cookies = {'uid': self._uid,
                                    'pass': self._hash}
                    return True
            except:
                pass

            sickrage.LOGGER.warning("Unable to obtain cookie")
            return False

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return results

        for mode in search_params.keys():
            sickrage.LOGGER.debug("Search Mode: %s" % mode)
            for search_string in search_params[mode]:

                if mode is not 'RSS':
                    sickrage.LOGGER.debug("Search string: %s " % search_string)

                search_string = '+'.join(search_string.split())

                post_data = dict({'/browse.php?': None, 'cata': 'yes', 'jxt': 8, 'jxw': 'b', 'search': search_string},
                                 **self.categories[mode])

                if self.freeleech:
                    post_data.update({'free': 'on'})

                parsedJSON = self.getURL(self.urls['search'], post_data=post_data, json=True)
                if not parsedJSON:
                    sickrage.LOGGER.debug("No data returned from provider")
                    continue

                try:
                    torrents = parsedJSON.get('Fs', [])[0].get('Cn', {}).get('torrents', [])
                except Exception:
                    sickrage.LOGGER.debug("Data returned from provider does not contain any torrents")
                    continue

                for torrent in torrents:

                    title = re.sub(r"\[.*=.*\].*\[/.*\]", "", torrent[b'name'])
                    download_url = self.urls['download'] % (torrent[b'id'], torrent[b'fname'])
                    seeders = int(torrent[b'seed'])
                    leechers = int(torrent[b'leech'])
                    # FIXME
                    size = -1

                    if not all([title, download_url]):
                        continue

                    # Filter unseeded torrent
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode is not 'RSS':
                            sickrage.LOGGER.debug(
                                    "Discarding torrent because it doesn't meet the minimum seeders or leechers: {} (S:{} L:{})".format(
                                            title, seeders, leechers))
                        continue

                    item = title, download_url, size, seeders, leechers
                    if mode is not 'RSS':
                        sickrage.LOGGER.debug("Found result: %s " % title)

                    items[mode].append(item)

            # For each search mode sort all the items by seeders if available if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class TorrentDayCache(tv_cache.TVCache):
    def __init__(self, provider_obj):
        tv_cache.TVCache.__init__(self, provider_obj)

        # Only poll IPTorrents every 10 minutes max
        self.minTime = 10

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}
