# coding=utf-8
# Author: Gonçalo M. (aka duramato/supergonkas) <supergonkas@gmail.com>
#
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, unicode_literals

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import convert_size, try_int
from sickrage.providers import TorrentProvider


class HD4FreeProvider(TorrentProvider):
    def __init__(self):
        super(HD4FreeProvider, self).__init__('HD4Free', 'https://hd4free.xyz', True)

        self.urls.update({
            'search': '{base_url}/searchapi.php'.format(**self.urls)
        })

        self.freeleech = None
        self.username = None
        self.api_key = None
        self.minseed = None
        self.minleech = None

        self.cache = TVCache(self, min_time=10)

    def _check_auth(self):
        if self.username and self.api_key:
            return True

        sickrage.srCore.srLogger.warning(
            'Your authentication credentials for {} are missing, check your config.'.format(self.name))

        return False

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if not self._check_auth:
            return results

        search_params = {
            'tv': 'true',
            'username': self.username,
            'apikey': self.api_key
        }

        for mode in search_strings:

            sickrage.srCore.srLogger.debug("Search Mode: {0}".format(mode))
            for search_string in search_strings[mode]:
                if self.freeleech:
                    search_params['fl'] = 'true'
                else:
                    search_params.pop('fl', '')

                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug("Search string: {}".format(search_string.strip()))
                    search_params['search'] = search_string
                else:
                    search_params.pop('search', '')

                try:
                    jdata = sickrage.srCore.srWebSession.get(self.urls['search'], params=search_params).json()
                except ValueError:
                    sickrage.srCore.srLogger.debug("No data returned from provider")
                    continue

                if not jdata:
                    sickrage.srCore.srLogger.debug("No data returned from provider")
                    continue

                error = jdata.get('error')
                if error:
                    sickrage.srCore.srLogger.debug(error)
                    return results

                try:
                    if jdata['0']['total_results'] == 0:
                        sickrage.srCore.srLogger.debug("Provider has no results for this search")
                        continue
                except StandardError:
                    continue

                for i in jdata:
                    try:
                        title = jdata[i]["release_name"]
                        download_url = jdata[i]["download_url"]
                        if not all([title, download_url]):
                            continue

                        seeders = jdata[i]["seeders"]
                        leechers = jdata[i]["leechers"]
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != 'RSS':
                                sickrage.srCore.srLogger.debug(
                                    "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                    (title, seeders, leechers))
                            continue

                        torrent_size = str(jdata[i]["size"]) + ' MB'
                        size = convert_size(torrent_size, -1)

                        item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders,
                                'leechers': leechers, 'hash': ''}

                        if mode != 'RSS':
                            sickrage.srCore.srLogger.debug("Found result: {}".format(title))

                        results.append(item)
                    except StandardError:
                        continue

        # Sort all the items by seeders if available
        results.sort(key=lambda k: try_int(k.get('seeders', 0)), reverse=True)

        return results
