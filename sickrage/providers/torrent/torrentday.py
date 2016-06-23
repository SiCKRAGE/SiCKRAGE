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

import requests

import sickrage
from sickrage.core.caches import tv_cache
from sickrage.providers import TorrentProvider


class TorrentDayProvider(TorrentProvider):
    def __init__(self):

        super(TorrentDayProvider, self).__init__("TorrentDay", 'classic.torrentday.com')

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

        self.urls.update({
            'login': '{base_url}/torrents/'.format(base_url=self.urls['base_url']),
            'search': '{base_url}/V3/API/API.php'.format(base_url=self.urls['base_url']),
            'download': '{base_url}/download.php/%s/%s'.format(base_url=self.urls['base_url'])
        })

        self.cookies = None

        self.categories = {'Season': {'c14': 1}, 'Episode': {'c2': 1, 'c26': 1, 'c7': 1, 'c24': 1},
                           'RSS': {'c2': 1, 'c26': 1, 'c7': 1, 'c24': 1, 'c14': 1}}

    def _doLogin(self):

        if any(requests.utils.dict_from_cookiejar(sickrage.srCore.srWebSession.cookies).values()):
            return True

        if self._uid and self._hash:
            requests.utils.add_dict_to_cookiejar(sickrage.srCore.srWebSession.cookies, self.cookies)
        else:

            login_params = {'username': self.username,
                            'password': self.password,
                            'submit.x': 0,
                            'submit.y': 0}

            try:
                response = sickrage.srCore.srWebSession.post(self.urls['login'], data=login_params, timeout=30).text
            except Exception:
                sickrage.srCore.srLogger.warning("[{}]: Unable to connect to provider".format(self.name))
                return False

            if re.search('You tried too often', response):
                sickrage.srCore.srLogger.warning("Too many login access attempts")
                return False

            try:
                    self._uid = requests.utils.dict_from_cookiejar(sickrage.srCore.srWebSession.cookies)['uid']
                    self._hash = requests.utils.dict_from_cookiejar(sickrage.srCore.srWebSession.cookies)['pass']
                    self.cookies = {'uid': self._uid, 'pass': self._hash}
                    return True
            except Exception:
                pass

            sickrage.srCore.srLogger.warning("Unable to obtain cookie")
            return False

    def search(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return results

        for mode in search_params.keys():
            sickrage.srCore.srLogger.debug("Search Mode: %s" % mode)
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug("Search string: %s " % search_string)

                search_string = '+'.join(search_string.split())

                post_data = dict({'/browse.php?': None, 'cata': 'yes', 'jxt': 8, 'jxw': 'b', 'search': search_string},
                                 **self.categories[mode])

                if self.freeleech:
                    post_data.update({'free': 'on'})

                try:
                    parsedJSON = sickrage.srCore.srWebSession.post(self.urls['search'], data=post_data).json()
                    torrents = parsedJSON['Fs'][0]['Cn']['torrents']
                except Exception:
                    sickrage.srCore.srLogger.debug("No data returned from provider")
                    continue

                for torrent in torrents:
                    title = re.sub(r"\[.*=.*\].*\[/.*\]", "", torrent['name'])
                    download_url = self.urls['download'] % (torrent['id'], torrent['fname'])
                    seeders = int(torrent['seed'])
                    leechers = int(torrent['leech'])
                    # FIXME
                    size = -1

                    if not all([title, download_url]):
                        continue

                    # Filter unseeded torrent
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode != 'RSS':
                            sickrage.srCore.srLogger.debug(
                                "Discarding torrent because it doesn't meet the minimum seeders or leechers: {} (S:{} L:{})".format(
                                    title, seeders, leechers))
                        continue

                    item = title, download_url, size, seeders, leechers
                    if mode != 'RSS':
                        sickrage.srCore.srLogger.debug("Found result: %s " % title)

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
        return {'entries': self.provider.search(search_params)}
