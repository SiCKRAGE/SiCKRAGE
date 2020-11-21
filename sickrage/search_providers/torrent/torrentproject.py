# coding=utf-8
# Author: Gonçalo M. (aka duramato/supergonkas) <supergonkas@gmail.com>
#
# URL: https://sickrage.ca
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE. If not, see <http://www.gnu.org/licenses/>.


import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import validate_url, try_int, convert_size
from sickrage.search_providers import TorrentProvider


class TorrentProjectProvider(TorrentProvider):
    def __init__(self):
        super(TorrentProjectProvider, self).__init__('TorrentProject', 'https://torrentproject.se', False)

        # custom settings
        self.custom_settings = {
            'custom_url': '',
            'minseed': 0,
            'minleech': 0
        }

        # Cache
        self.cache = TVCache(self, search_strings={'RSS': ['0day']})

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []

        search_params = {
            'out': 'json',
            'filter': 2101,
            'showmagnets': 'on',
            'num': 50
        }

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: {0}".format(mode))

            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: {0}".format
                                           (search_string))

                search_params['s'] = search_string

                search_url = self.urls['base_url']
                if self.custom_settings['custom_url']:
                    if not validate_url(self.custom_settings['custom_url']):
                        sickrage.app.log.warning("Invalid custom url set, please check your settings")
                        return results
                    search_url = self.custom_settings['custom_url']

                resp = self.session.get(search_url, params=search_params)
                if not resp or not resp.content:
                    sickrage.app.log.debug("No data returned from provider")
                    continue

                try:
                    data = resp.json()
                except ValueError:
                    sickrage.app.log.debug("No data returned from provider")
                    continue

                results += self.parse(data, mode)

        return results

    def parse(self, data, mode, **kwargs):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []

        if not (data and "total_found" in data and int(data["total_found"]) > 0):
            sickrage.app.log.debug("Data returned from provider does not contain any torrents")
            return results

        del data["total_found"]

        for i in data:
            try:
                title = data[i]["title"]
                download_url = data[i]["magnet"]
                if not all([title, download_url]):
                    continue

                seeders = try_int(data[i]["seeds"], 1)
                leechers = try_int(data[i]["leechs"], 0)
                torrent_size = data[i]["torrent_size"]

                size = convert_size(torrent_size, -1)

                results += [
                    {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                ]

                if mode != 'RSS':
                    sickrage.app.log.debug("Found result: {}".format(title))
            except Exception:
                sickrage.app.log.error("Failed parsing provider.")

        return results
