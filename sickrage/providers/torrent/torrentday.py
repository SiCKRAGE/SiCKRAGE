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

import re

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.providers import TorrentProvider


class TorrentDayProvider(TorrentProvider):
    def __init__(self):
        super(TorrentDayProvider, self).__init__("TorrentDay", 'https://www.torrentday.com', True)

        self.urls.update({
            'login': '{base_url}/t'.format(**self.urls),
            'search': '{base_url}/V3/API/API.php'.format(**self.urls),
            'download': '{base_url}/download.php/%s/%s'.format(**self.urls)
        })

        self.username = None
        self.password = None

        self.freeleech = False
        self.minseed = None
        self.minleech = None

        self.enable_cookies = True
        self.required_cookies = ('uid', 'pass')

        self.categories = {
            'Season': {'c14': 1},
            'Episode': {'c2': 1, 'c26': 1, 'c7': 1, 'c24': 1, 'c34': 1},
            'RSS': {'c2': 1, 'c26': 1, 'c7': 1, 'c24': 1, 'c34': 1, 'c14': 1}
        }

        self.cache = TVCache(self)

    def login(self):
        return self.cookie_login('log in')

    def search(self, search_strings, age=0, ep_obj=None, **kwargs):
        results = []

        if not self.login():
            return results

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: %s " % search_string)

                search_string = '+'.join(search_string.split())

                post_data = dict({'/browse.php?': None, 'cata': 'yes', 'jxt': 8, 'jxw': 'b', 'search': search_string},
                                 **self.categories[mode])

                if self.freeleech:
                    post_data.update({'free': 'on'})

                try:
                    data = self.session.post(self.urls['search'], data=post_data).json()
                    results += self.parse(data, mode)
                except Exception:
                    sickrage.app.log.debug("No data returned from provider")

        return results

    def parse(self, data, mode, **kwargs):
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
                title = re.sub(r"\[.*=.*\].*\[/.*\]", "", torrent['name'])
                download_url = self.urls['download'] % (torrent['id'], torrent['fname'])
                seeders = int(torrent['seed'])
                leechers = int(torrent['leech'])
                # FIXME
                size = -1

                if not all([title, download_url]):
                    continue

                results += [
                    {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                ]

                if mode != 'RSS':
                    sickrage.app.log.debug("Found result: {}".format(title))
            except Exception:
                sickrage.app.log.error("Failed parsing provider.")

        return results
