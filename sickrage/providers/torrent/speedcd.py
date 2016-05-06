# Author: Mr_Orange
# URL: https://github.com/mr-orange/Sick-Beard
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

import sickrage
from sickrage.core.caches import tv_cache
from sickrage.providers import TorrentProvider


class SpeedCDProvider(TorrentProvider):
    def __init__(self):

        super(SpeedCDProvider, self).__init__("Speedcd",'speed.cd')

        self.supportsBacklog = True

        self.username = None
        self.password = None
        self.ratio = None
        self.freeleech = False
        self.minseed = None
        self.minleech = None

        self.urls.update({
            'login': '{base_url}/take_login.php'.format(base_url=self.urls['base_url']),
            'detail': '{base_url}/t/%s'.format(base_url=self.urls['base_url']),
            'search': '{base_url}/V3/API/API.php'.format(base_url=self.urls['base_url']),
            'download': '{base_url}/download.php?torrent=%s'.format(base_url=self.urls['base_url'])
        })

        self.categories = {'Season': {'c14': 1}, 'Episode': {'c2': 1, 'c49': 1}, 'RSS': {'c14': 1, 'c2': 1, 'c49': 1}}

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = SpeedCDCache(self)

    def _doLogin(self):

        login_params = {'username': self.username,
                        'password': self.password}

        try:
            response = sickrage.srCore.srWebSession.post(self.urls['login'], data=login_params, timeout=30).text
        except Exception:
            sickrage.srCore.srLogger.warning("[{}]: Unable to connect to provider".format(self.name))
            return False

        if re.search('Incorrect username or Password. Please try again.', response):
            sickrage.srCore.srLogger.warning("[{}]: Invalid username or password. Check your settings".format(self.name))
            return False

        return True

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

                post_data = dict({'/browse.php?': None, 'cata': 'yes', 'jxt': 4, 'jxw': 'b', 'search': search_string},
                                 **self.categories[mode])

                try:
                    parsedJSON = sickrage.srCore.srWebSession.post(self.urls['search'], data=post_data).json()
                    torrents = parsedJSON['Fs'][0]['Cn']['torrents']
                except Exception:
                    continue

                for torrent in torrents:
                    if self.freeleech and not torrent['free']:
                        continue

                    title = re.sub('<[^>]*>', '', torrent['name'])
                    download_url = self.urls['download'] % (torrent['id'])
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
                                "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                    title, seeders, leechers))
                        continue

                    item = title, download_url, size, seeders, leechers
                    if mode != 'RSS':
                        sickrage.srCore.srLogger.debug("Found result: %s " % title)

                    items[mode].append(item)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class SpeedCDCache(tv_cache.TVCache):
    def __init__(self, provider_obj):
        tv_cache.TVCache.__init__(self, provider_obj)

        # only poll Speedcd every 20 minutes max
        self.minTime = 20

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider.search(search_params)}
