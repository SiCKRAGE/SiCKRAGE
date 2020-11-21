# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import re

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, convert_size
from sickrage.search_providers import TorrentProvider


class TORRENTZProvider(TorrentProvider):
    def __init__(self):
        super(TORRENTZProvider, self).__init__("Torrentz", 'https://torrentz2.eu', False)

        self._urls.update({
            'verified': '{base_url}/feed_verified'.format(**self._urls),
            'feed': '{base_url}/feed'.format(**self._urls)
        })

        # custom settings
        self.custom_settings = {
            'confirmed': False,
            'minseed': 0,
            'minleech': 0
        }

        self.cache = TVCache(self, min_time=15)

    @staticmethod
    def _split_description(description):
        match = re.findall(r'[0-9]+', description)
        return int(match[0]) * 1024 ** 2, int(match[1]), int(match[2])

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []

        for mode in search_strings:
            sickrage.app.log.debug('Search Mode: {}'.format(mode))
            for search_string in search_strings[mode]:
                search_params = {'f': search_string}
                search_url = self.urls['feed']

                if mode != 'RSS':
                    sickrage.app.log.debug('Search string: {}'.format(search_string))

                resp = self.session.get(search_url, params=search_params)
                if not resp or not resp.text:
                    sickrage.app.log.debug("No data returned from provider")
                    continue

                results += self.parse(resp.text, mode)

        return results

    def parse(self, data, mode, **kwargs):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []

        if not data.startswith('<?xml'):
            sickrage.app.log.info('Expected xml but got something else, is your mirror failing?')
            return results

        with bs4_parser(data) as parser:
            for item in parser('item'):
                try:
                    if item.category and 'tv' not in item.category.get_text(strip=True).lower():
                        continue

                    title = item.title.get_text(strip=True)
                    t_hash = item.guid.get_text(strip=True).rsplit('/', 1)[-1]
                    if not all([title, t_hash]):
                        continue

                    download_url = "magnet:?xt=urn:btih:" + t_hash + "&dn=" + title
                    torrent_size, seeders, leechers = self._split_description(item.find('description').text)
                    size = convert_size(torrent_size, -1)

                    results += [
                        {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                    ]

                    if mode != 'RSS':
                        sickrage.app.log.debug("Found result: {}".format(title))
                except Exception:
                    sickrage.app.log.error("Failed parsing provider.")

        return results
