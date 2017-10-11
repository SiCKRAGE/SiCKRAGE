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
from urllib import urlencode

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, convert_size, try_int
from sickrage.providers import TorrentProvider


class newpctProvider(TorrentProvider):
    def __init__(self):
        super(newpctProvider, self).__init__("Newpct", 'http://www.newpct.com', False)

        self.supports_backlog = True
        self.onlyspasearch = None

        self.cache = TVCache(self, min_time=20)

        self.urls.update({
            'search': '{base_url}/index.php'.format(base_url=self.urls['base_url'])
        })

    def search(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):
        results = []

        search_params = {
            'l': 'doSearch',
            'q': '',
            'category_': 'All',
            'idioma_': 1,
            'bus_de_': 'All'
        }

        lang_info = '' if not epObj or not epObj.show else epObj.show.lang

        for mode in search_strings.keys():
            sickrage.srCore.srLogger.debug("Search Mode: %s" % mode)

            if self.onlyspasearch:
                search_params['idioma_'] = 1
            else:
                search_params['idioma_'] = 'All'

            # Only search if user conditions are true
            if self.onlyspasearch and lang_info != 'es' and mode != 'RSS':
                sickrage.srCore.srLogger.debug("Show info is not spanish, skipping provider search")
                continue

            search_params['bus_de_'] = 'All' if mode != 'RSS' else 'semana'

            for search_string in search_strings[mode]:
                search_params['q'] = search_string.strip()

                sickrage.srCore.srLogger.debug(
                    "Search URL: %s" % self.urls['search'] + '?' + urlencode(search_params))

                try:
                    data = sickrage.srCore.srWebSession.post(self.urls['search'], data=search_params, timeout=30).text
                except Exception:
                    continue

                try:
                    with bs4_parser(data) as html:
                        torrent_table = html.find('table', id='categoryTable')
                        torrent_rows = torrent_table('tr') if torrent_table else []

                        if len(torrent_rows) < 3:
                            sickrage.srCore.srLogger.debug("Data returned from provider does not contain any torrents")
                            continue

                        for row in torrent_rows[1:-1]:
                            try:
                                cells = row('td')

                                torrent_row = row.find('a')
                                download_url = torrent_row.get('href', '')
                                title = self._processTitle(torrent_row.get('title', ''), download_url)
                                if not all([title, download_url]):
                                    continue

                                # Provider does not provide seeders/leechers
                                seeders = 1
                                leechers = 0
                                torrent_size = cells[2].get_text(strip=True)

                                size = convert_size(torrent_size) or -1
                                item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders,
                                        'leechers': leechers, 'hash': ''}

                                if mode != 'RSS':
                                    sickrage.srCore.srLogger.debug('Found result: {}'.format(title))

                                results.append(item)
                            except (AttributeError, TypeError):
                                continue

                except Exception:
                    sickrage.srCore.srLogger.error("Failed parsing provider.")

        results.sort(key=lambda k: try_int(k.get('seeders', 0)), reverse=True)

        return results

    @staticmethod
    def _processTitle(title, url):
        # Remove 'Mas informacion sobre ' literal from title
        title = title[22:]
        title = re.sub(r'[ ]{2,}', ' ', title, flags=re.I)

        # Quality - Use re module to avoid case sensitive problems with replace
        title = re.sub(r'\[HDTV 1080p?[^\[]*]', '1080p HDTV x264', title, flags=re.I)
        title = re.sub(r'\[HDTV 720p?[^\[]*]', '720p HDTV x264', title, flags=re.I)
        title = re.sub(r'\[ALTA DEFINICION 720p?[^\[]*]', '720p HDTV x264', title, flags=re.I)
        title = re.sub(r'\[HDTV]', 'HDTV x264', title, flags=re.I)
        title = re.sub(r'\[DVD[^\[]*]', 'DVDrip x264', title, flags=re.I)
        title = re.sub(r'\[BluRay 1080p?[^\[]*]', '1080p BluRay x264', title, flags=re.I)
        title = re.sub(r'\[BluRay Rip 1080p?[^\[]*]', '1080p BluRay x264', title, flags=re.I)
        title = re.sub(r'\[BluRay Rip 720p?[^\[]*]', '720p BluRay x264', title, flags=re.I)
        title = re.sub(r'\[BluRay MicroHD[^\[]*]', '1080p BluRay x264', title, flags=re.I)
        title = re.sub(r'\[MicroHD 1080p?[^\[]*]', '1080p BluRay x264', title, flags=re.I)
        title = re.sub(r'\[BLuRay[^\[]*]', '720p BluRay x264', title, flags=re.I)
        title = re.sub(r'\[BRrip[^\[]*]', '720p BluRay x264', title, flags=re.I)
        title = re.sub(r'\[BDrip[^\[]*]', '720p BluRay x264', title, flags=re.I)

        #detect hdtv/bluray by url
        #hdtv 1080p example url: http://www.newpct.com/descargar-seriehd/foo/capitulo-610/hdtv-1080p-ac3-5-1/
        #hdtv 720p example url: http://www.newpct.com/descargar-seriehd/foo/capitulo-26/hdtv-720p-ac3-5-1/
        #hdtv example url: http://www.newpct.com/descargar-serie/foo/capitulo-214/hdtv/
        #bluray compilation example url: http://www.newpct.com/descargar-seriehd/foo/capitulo-11/bluray-1080p/
        title_hdtv = re.search(r'HDTV', title, flags=re.I)
        title_720p = re.search(r'720p', title, flags=re.I)
        title_1080p = re.search(r'1080p', title, flags=re.I)
        title_x264 = re.search(r'x264', title, flags=re.I)
        title_bluray = re.search(r'bluray', title, flags=re.I)
        title_serie_hd = re.search(r'descargar\-seriehd', title, flags=re.I)
        url_hdtv = re.search(r'HDTV', url, flags=re.I)
        url_720p = re.search(r'720p', url, flags=re.I)
        url_1080p = re.search(r'1080p', url, flags=re.I)
        url_bluray = re.search(r'bluray', url, flags=re.I)

        if not title_hdtv and url_hdtv:
            title += ' HDTV'
            if not title_x264:
                title += ' x264'
        if not title_bluray and url_bluray:
            title += ' BluRay'
            if not title_x264:
                title += ' x264'
        if not title_1080p and url_1080p:
            title += ' 1080p'
            title_1080p = True
        if not title_720p and url_720p:
            title += ' 720p'
            title_720p = True
        if not (title_720p or title_1080p) and title_serie_hd:
            title += ' 720p'

        # Language
        title = re.sub(r'\[Spanish[^\[]*]', 'SPANISH AUDIO', title, flags=re.I)
        title = re.sub(r'\[Castellano[^\[]*]', 'SPANISH AUDIO', title, flags=re.I)
        title = re.sub(r'\[Español[^\[]*]', 'SPANISH AUDIO', title, flags=re.I)
        title = re.sub(r'\[AC3 5\.1 Español[^\[]*]', 'SPANISH AUDIO', title, flags=re.I)

        if re.search(r'\[V.O.[^\[]*]', title, flags=re.I):
            title += '-NEWPCTVO'
        else:
            title += '-NEWPCT'

        return title.strip()
