# coding=utf-8
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


from urllib.parse import urljoin

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import validate_url, try_int, bs4_parser, convert_size
from sickrage.search_providers import TorrentProvider


class SkyTorrents(TorrentProvider):
    def __init__(self):
        super(SkyTorrents, self).__init__('SkyTorrents', 'https://www.skytorrents.lol', False)
        self._urls.update({
            "rss": "{base_url}/top100".format(**self._urls)
        })

        # custom settings
        self.custom_settings = {
            'custom_url': '',
            'minseed': 0,
            'minleech': 0
        }

        self.cache = TVCache(self)

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: {}".format(mode))
            for search_string in search_strings[mode]:
                if mode != "RSS":
                    sickrage.app.log.debug("Search string: {0}".format(search_string))

                search_url = (self.urls["base_url"], self.urls["rss"])[mode == "RSS"]

                if self.custom_settings['custom_url']:
                    if not validate_url(self.custom_settings['custom_url']):
                        sickrage.app.log.warning("Invalid custom url: {}".format(self.custom_settings['custom_url']))
                        return results
                    search_url = urljoin(self.custom_settings['custom_url'], search_url.split(self.urls['base_url'])[1])

                if mode != "RSS":
                    search_params = {'query': search_string, 'sort': ('seeders', 'created')[mode == 'RSS'], 'type': 'video', 'tag': 'hd', 'category': 'show'}
                else:
                    search_params = {'category': 'show', 'type': 'video', 'sort': 'created'}

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

        with bs4_parser(data) as html:
            labels = [label.get_text(strip=True) for label in html('th')]
            for item in html('tr', attrs={'data-size': True}):
                try:
                    cells = item.findChildren('td')

                    title_block_links = cells[labels.index('Name')].find_all('a')
                    title = title_block_links[0].get_text(strip=True)
                    download_url = title_block_links[2]['href']

                    seeders = try_int(cells[labels.index(('Seeders', 'Seeds')[mode == "RSS"])].get_text(strip=True))
                    leechers = try_int(cells[labels.index(('Leechers', 'Peers')[mode == "RSS"])].get_text(strip=True))

                    size = try_int(item['data-size'])

                    results += [
                        {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                    ]

                    if mode != 'RSS':
                        sickrage.app.log.debug("Found result: {}".format(title))
                except Exception:
                    sickrage.app.log.error("Failed parsing provider")

        return results
