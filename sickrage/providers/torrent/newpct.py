# coding=utf-8
# Author: CristianBB
# Greetings to Mr. Pine-apple
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import re

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, convert_size
from sickrage.providers import TorrentProvider


class newpctProvider(TorrentProvider):
    def __init__(self):
        super(newpctProvider, self).__init__("Newpct", 'http://www.newpct.com', False)

        self.urls.update({
            'search': '{base_url}/index.php'.format(**self.urls)
        })

        self.onlyspasearch = None

        self.cache = TVCache(self, min_time=20)

    def search(self, search_strings, age=0, ep_obj=None):
        results = []

        # Only search if user conditions are true
        lang_info = '' if not ep_obj or not ep_obj.show else ep_obj.show.lang

        # http://www.newpct.com/index.php?l=doSearch&q=fringe&category_=All&idioma_=1&bus_de_=All
        # Search Params
        search_params = {
            'l': 'doSearch',
            'q': '',  # Show name
            'category_': 'All',  # Category 'Shows' (767)
            'idioma_': 1,  # Language Spanish (1)
            'bus_de_': 'All'  # Date from (All, hoy)
        }

        for mode in search_strings:
            sickrage.srCore.srLogger.debug('Search mode: {}'.format(mode))

            # Only search if user conditions are true
            if self.onlyspasearch and lang_info != 'es' and mode != 'RSS':
                sickrage.srCore.srLogger.debug('Show info is not spanish, skipping provider search')
                continue

            search_params['bus_de_'] = 'All' if mode != 'RSS' else 'hoy'

            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug('Search string: {}'.format(search_string))

                search_params['q'] = search_string
                try:
                    data = sickrage.srCore.srWebSession.get(self.urls['search'], params=search_params).text
                    results += self.parse(data, mode)
                except Exception:
                    sickrage.srCore.srLogger.debug('No data returned from provider')
                    continue

        return results

    def parse(self, data, mode):
        """
        Parse search results for items.

        :param data: The raw response from a search
        :param mode: The current mode used to search, e.g. RSS

        :return: A list of items found
        """

        results = []

        with bs4_parser(data) as html:
            torrent_table = html.find('table', id='categoryTable')
            torrent_rows = torrent_table('tr') if torrent_table else []

            # Continue only if at least one release is found
            if len(torrent_rows) < 3:  # Headers + 1 Torrent + Pagination
                sickrage.srCore.srLogger.debug('Data returned from provider does not contain any torrents')
                return results

            # 'Fecha', 'Título', 'Tamaño', ''
            # Date,    Title,     Size
            labels = [label.get_text(strip=True) for label in torrent_rows[0]('th')]

            # Skip column headers
            for row in torrent_rows[1:-1]:
                cells = row('td')

                try:
                    torrent_anchor = row.find('a')
                    title = self._process_title(torrent_anchor.get_text())
                    download_url = torrent_anchor.get('href', '')
                    if not all([title, download_url]):
                        continue

                    try:
                        r = sickrage.srCore.srWebSession.get(download_url).text
                        download_url = re.search(r'http://tumejorserie.com/descargar/.+\.torrent', r, re.DOTALL).group()
                    except Exception:
                        continue

                    seeders = 1  # Provider does not provide seeders
                    leechers = 0  # Provider does not provide leechers
                    torrent_size = cells[labels.index('Tamaño')].get_text(strip=True)
                    size = convert_size(torrent_size, -1)

                    item = {
                        'title': title,
                        'link': download_url,
                        'size': size,
                        'seeders': seeders,
                        'leechers': leechers,
                    }
                    if mode != 'RSS':
                        sickrage.srCore.srLogger.debug('Found result: {}'.format(title))

                        results.append(item)
                except (AttributeError, TypeError, KeyError, ValueError, IndexError):
                    sickrage.srCore.srLogger.error('Failed parsing provider')

        return results

    @staticmethod
    def _process_title(title):
        # Add encoder and group to title
        title = title.strip() + ' x264-NEWPCT'

        # Quality - Use re module to avoid case sensitive problems with replace
        title = re.sub(r'\[ALTA DEFINICION[^\[]*]', '720p HDTV', title, flags=re.IGNORECASE)
        title = re.sub(r'\[(BluRay MicroHD|MicroHD 1080p)[^\[]*]', '1080p BluRay', title, flags=re.IGNORECASE)
        title = re.sub(r'\[(B[RD]rip|BLuRay)[^\[]*]', '720p BluRay', title, flags=re.IGNORECASE)

        # Language
        title = re.sub(r'\[(Spanish|Castellano|Español)[^\[]*]', 'SPANISH AUDIO', title, flags=re.IGNORECASE)
        title = re.sub(r'\[AC3 5\.1 Español[^\[]*]', 'SPANISH AUDIO AC3 5.1', title, flags=re.IGNORECASE)

        return title
