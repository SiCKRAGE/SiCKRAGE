# coding=utf-8
# Author: CristianBB
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


import re

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, try_int
from sickrage.core.tv.show.helpers import find_show
from sickrage.providers import TorrentProvider


class EliteTorrentProvider(TorrentProvider):
    def __init__(self):
        super(EliteTorrentProvider, self).__init__('EliteTorrent', 'https://elitetorrent.eu', False)

        self._urls.update({
            'search': '{base_url}/torrents.php'.format(**self._urls)
        })

        self.onlyspasearch = None
        self.minseed = None
        self.minleech = None

        self.cache = TVCache(self)

    def search(self, search_strings, age=0, show_id=None, season=None, episode=None, **kwargs):
        results = []

        lang_info = find_show(show_id).lang

        """
        Search query:
        http://www.elitetorrent.net/torrents.php?cat=4&modo=listado&orden=fecha&pag=1&buscar=fringe

        cat = 4 => Shows
        modo = listado => display results mode
        orden = fecha => order
        buscar => Search show
        pag = 1 => page number
        """

        search_params = {
            'cat': 4,
            'modo': 'listado',
            'orden': 'fecha',
            'pag': 1,
            'buscar': ''

        }

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: {}".format(mode))

            # Only search if user conditions are true
            if self.onlyspasearch and lang_info != 'es' and mode != 'RSS':
                sickrage.app.log.debug("Show info is not spanish, skipping provider search")
                continue

            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: {0}".format(search_string))

                search_string = re.sub(r'S0*(\d*)E?(\d*)', r'\1x\2', search_string)
                search_params['buscar'] = search_string.strip() if mode != 'RSS' else ''

                try:
                    data = self.session.get(self.urls['search'], params=search_params).text
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

        def _process_title(title):
            # Quality, if no literal is defined it's HDTV
            if 'calidad' not in title:
                title += ' HDTV x264'
            else:
                title = title.replace('(calidad baja)', 'HDTV x264')
                title = title.replace('(Buena calidad)', '720p HDTV x264')
                title = title.replace('(Alta calidad)', '720p HDTV x264')
                title = title.replace('(calidad regular)', 'DVDrip x264')
                title = title.replace('(calidad media)', 'DVDrip x264')

            # Language, all results from this provider have spanish audio, we append it to title (avoid to download undesired torrents)
            title += ' SPANISH AUDIO-ELITETORRENT'

            return title

        with bs4_parser(data) as html:
            torrent_table = html.find('table', class_='fichas-listado')
            torrent_rows = torrent_table('tr') if torrent_table else []

            if len(torrent_rows) < 2:
                sickrage.app.log.debug("Data returned from provider does not contain any torrents")
                return results

            for row in torrent_rows[1:]:
                try:
                    title = _process_title(row.find('a', class_='nombre')['title'])
                    download_url = self.urls['base_url'] + row.find('a')['href']
                    if not all([title, download_url]):
                        continue

                    seeders = try_int(row.find('td', class_='semillas').get_text(strip=True))
                    leechers = try_int(row.find('td', class_='clientes').get_text(strip=True))

                    # seeders are not well reported. Set 1 in case of 0
                    seeders = max(1, seeders)

                    # Provider does not provide size
                    size = -1

                    results += [
                        {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                    ]

                    if mode != 'RSS':
                        sickrage.app.log.debug("Found result: {}".format(title))
                except Exception:
                    sickrage.app.log.error("Failed parsing provider")

        return results
