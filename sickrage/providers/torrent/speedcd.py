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

from requests.utils import dict_from_cookiejar

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.providers import TorrentProvider


class SpeedCDProvider(TorrentProvider):
    def __init__(self):
        super(SpeedCDProvider, self).__init__("Speedcd", 'http://speed.cd', True)

        self.urls.update({
            'login': '{base_url}/take_login.php'.format(**self.urls),
            'detail': '{base_url}/t/%s'.format(**self.urls),
            'search': '{base_url}/V3/API/API.php'.format(**self.urls),
            'download': '{base_url}/download.php?torrent=%s'.format(**self.urls)
        })

        self.username = None
        self.password = None

        self.freeleech = False
        self.minseed = None
        self.minleech = None

        self.categories = {'Season': {'c14': 1}, 'Episode': {'c2': 1, 'c49': 1}, 'RSS': {'c14': 1, 'c2': 1, 'c49': 1}}

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = TVCache(self, min_time=20)

    def login(self):
        if any(dict_from_cookiejar(sickrage.srCore.srWebSession.cookies).values()):
            return True

        login_params = {'username': self.username,
                        'password': self.password}

        try:
            response = sickrage.srCore.srWebSession.post(self.urls['login'], data=login_params, timeout=30).text
        except Exception:
            sickrage.srCore.srLogger.warning("Unable to connect to provider".format(self.name))
            return False

        if re.search('Incorrect username or Password. Please try again.', response):
            sickrage.srCore.srLogger.warning(
                "Invalid username or password. Check your settings".format(self.name))
            return False

        return True

    def search(self, search_params, age=0, ep_obj=None):
        results = []

        if not self.login():
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
                    data = sickrage.srCore.srWebSession.post(self.urls['search'], data=post_data).json()
                    results += self.parse(data, mode)
                except Exception:
                    sickrage.srCore.srLogger.debug("No data returned from provider")

        return results

    def parse(self, data, mode):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []

        try:
            torrents = data['Fs'][0]['Cn']['torrents']
        except Exception:
            return results

        for torrent in torrents:
            try:
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

                item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders,
                        'leechers': leechers, 'hash': ''}

                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug("Found result: {}".format(title))

                results.append(item)
            except Exception:
                sickrage.srCore.srLogger.error("Failed parsing provider")

        return results