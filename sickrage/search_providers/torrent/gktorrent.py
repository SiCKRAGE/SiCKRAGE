# coding=utf-8
# ##############################################################################
#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#  -
#  This file is part of SiCKRAGE.
#  -
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  -
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
# ##############################################################################


from urllib.parse import urljoin

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, try_int, convert_size, validate_url
from sickrage.search_providers import TorrentProvider


class GKTorrentProvider(TorrentProvider):
    def __init__(self):
        super(GKTorrentProvider, self).__init__('GKTorrent', 'https://www.gktorrent.pw', False)

        self._urls.update({
            'search': '{base_url}/recherche/'.format(**self._urls),
            'rss': '{base_url}/torrents/séries'.format(**self._urls),
        })

        # custom settings
        self.custom_settings = {
            'custom_url': '',
            'minseed': 0,
            'minleech': 0
        }

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = TVCache(self, min_time=20)

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: {0}".format(mode))
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: {}".format(search_string))
                    search_url = urljoin(self.urls['search'], "{search_query}".format(search_query=search_string))
                else:
                    search_url = self.urls['rss']

                if self.custom_settings['custom_url']:
                    if not validate_url(self.custom_settings['custom_url']):
                        sickrage.app.log.warning("Invalid custom url: {}".format(self.custom_settings['custom_url']))
                        return results
                    search_url = urljoin(self.custom_settings['custom_url'], search_url.split(self.urls['base_url'])[1])

                resp = self.session.get(search_url)
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
            table_body = html.find('tbody')

            # Continue only if at least one release is found
            if not table_body:
                sickrage.app.log.debug('Data returned from provider does not contain any torrents')
                return results

            for row in table_body('tr'):
                cells = row('td')
                if len(cells) < 4:
                    continue

                try:
                    title = download_url = None
                    info_cell = cells[0].a
                    if info_cell:
                        title = info_cell.get_text()
                        download_url = self._get_download_link(urljoin(self.urls['base_url'], info_cell.get('href')))
                    if not all([title, download_url]):
                        continue

                    title = '{name} {codec}'.format(name=title, codec='x264')

                    if self.custom_settings['custom_url'] and self.urls['base_url'] in download_url:
                        if not validate_url(self.custom_settings['custom_url']):
                            sickrage.app.log.warning("Invalid custom url: {}".format(self.custom_settings['custom_url']))
                            return results
                        download_url = urljoin(self.custom_settings['custom_url'], download_url.split(self.urls['base_url'])[1])

                    seeders = try_int(cells[2].get_text(strip=True))
                    leechers = try_int(cells[3].get_text(strip=True))

                    torrent_size = cells[1].get_text()
                    size = convert_size(torrent_size, -1)

                    results += [{
                        'title': title,
                        'link': download_url,
                        'size': size,
                        'seeders': seeders,
                        'leechers': leechers
                    }]

                    if mode != 'RSS':
                        sickrage.app.log.debug("Found result: {}".format(title))
                except Exception:
                    sickrage.app.log.error("Failed parsing provider")

        return results

    def _get_download_link(self, url, download_type="torrent"):
        links = {
            "torrent": "",
            "magnet": "",
        }

        try:
            data = self.session.get(url).text
            with bs4_parser(data) as html:
                downloads = html.find('div', {'class': 'download'})
                if downloads:
                    for download in downloads.findAll('a'):
                        link = download['href']
                        if link.startswith("magnet"):
                            links["magnet"] = link
                        else:
                            links["torrent"] = urljoin(self.urls['base_url'], link)
        except Exception:
            pass

        return links[download_type]
