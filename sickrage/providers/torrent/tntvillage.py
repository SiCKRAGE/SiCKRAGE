# coding=utf-8
# Author: Giovanni Borri
# Modified by gborri, https://github.com/gborri for TNTVillage
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import re

from unidecode import unidecode

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.common import Quality
from sickrage.core.helpers import bs4_parser, try_int
from sickrage.providers import TorrentProvider


class TNTVillageProvider(TorrentProvider):
    def __init__(self):
        super(TNTVillageProvider, self).__init__("TNTVillage", 'http://www.tntvillage.scambioetico.org', False)

        self._urls.update({
            'search': '{base_url}/src/releaselist.php'.format(**self._urls),
        })

        self.subtitle = None
        self.minseed = None
        self.minleech = None
        self.engrelease = None

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = TVCache(self, min_time=30)

    def search(self, search_strings, age=0, show_id=None, season=None, episode=None, **kwargs):
        results = []

        if not self.login():
            return results

        # Search Params
        search_params = {
            'srcrel': '',
            'page': 0,
            'cat': 29,
        }

        for mode in search_strings:
            sickrage.app.log.debug('Search mode: {}'.format(mode))
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug('Search string: {}'.format(search_string))
                    search_params['srcrel'] = search_string

                while search_params['page'] <= 10:
                    search_params['page'] += 1
                    resp = self.session.post(self.urls['search'], data=search_params)
                    if not resp or not resp.text:
                        sickrage.app.log.debug("No data returned from provider")
                        continue

                    results += self.parse(resp.text, mode)

        return results

    def parse(self, data, mode, **kwargs):
        """
        Parse search results for items.

        :param data: The raw response from a search
        :param mode: The current mode used to search, e.g. RSS

        :return: A list of items found
        """
        results = []

        hdtext = [' Versione 720p',
                  ' V 720p',
                  ' V 720',
                  ' V HEVC',
                  ' V  HEVC',
                  ' V 1080',
                  ' Versione 1080p',
                  ' 720p HEVC',
                  ' Ver 720',
                  ' 720p HEVC',
                  ' 720p']

        with bs4_parser(data) as html:
            torrent_table = html.find(class_='showrelease_tb')
            torrent_rows = torrent_table('tr') if torrent_table else []

            # Continue only if at least one release is found
            if len(torrent_rows) < 3:
                sickrage.app.log.debug('Data returned from provider does not contain any torrents')
                return results

            # Skip column headers
            for row in torrent_table('tr')[1:]:
                cells = row('td')
                if not cells:
                    continue

                try:
                    title = unidecode(cells[6].text)
                    title = title.replace('·', '').replace(',', '')
                    title = title.replace('by', '-').strip()
                    title = title.strip('-').strip()

                    download_url = cells[1].find('a')['href']
                    if not all([title, download_url]):
                        continue

                    seeders = try_int(cells[4].text, 1)
                    leechers = try_int(cells[3].text)

                    filename_qt = self._reverse_quality(self._episode_quality(title))
                    for text in hdtext:
                        title1 = title
                        title = title.replace(text, filename_qt)
                        if title != title1:
                            break

                    if Quality.name_quality(title) == Quality.UNKNOWN:
                        title += filename_qt

                    if self._has_only_subs(title) and not self.subtitle:
                        sickrage.app.log.debug('Torrent is only subtitled, skipping: {}'.format(title))
                        continue

                    if self.engrelease and not self._is_english(title):
                        sickrage.app.log.debug("Torrent isn't english audio/subtitled, skipping: {} ".format(title))
                        continue

                    size = -1

                    results += [
                        {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                    ]

                    if mode != 'RSS':
                        sickrage.app.log.debug("Found result: {}".format(title))
                except Exception:
                    sickrage.app.log.error('Failed parsing provider')

        return results

    @staticmethod
    def _reverse_quality(quality):
        quality_string = ''

        if quality == Quality.SDTV:
            quality_string = ' HDTV x264'
        if quality == Quality.SDDVD:
            quality_string = ' DVDRIP'
        elif quality == Quality.HDTV:
            quality_string = ' 720p HDTV x264'
        elif quality == Quality.FULLHDTV:
            quality_string = ' 1080p HDTV x264'
        elif quality == Quality.RAWHDTV:
            quality_string = ' 1080i HDTV mpeg2'
        elif quality == Quality.HDWEBDL:
            quality_string = ' 720p WEB-DL h264'
        elif quality == Quality.FULLHDWEBDL:
            quality_string = ' 1080p WEB-DL h264'
        elif quality == Quality.HDBLURAY:
            quality_string = ' 720p Bluray x264'
        elif quality == Quality.FULLHDBLURAY:
            quality_string = ' 1080p Bluray x264'

        return quality_string

    @staticmethod
    def _episode_quality(title):
        def checkName(options, func):
            return func([re.search(option, title, re.I) for option in options])

        dvdOptions = checkName(["dvd", "dvdrip", "dvdmux", "DVD9", "DVD5"], any)
        bluRayOptions = checkName(["BD", "BDmux", "BDrip", "BRrip", "Bluray"], any)
        sdOptions = checkName(["h264", "divx", "XviD", "tv", "TVrip", "SATRip", "DTTrip", "Mpeg2"], any)
        hdOptions = checkName(["720p"], any)
        fullHD = checkName(["1080p", "fullHD"], any)

        webdl = checkName(
            ["webdl", "webmux", "webrip", "dl-webmux", "web-dlmux", "webdl-mux", "web-dl", "webdlmux", "dlmux"], any)

        if sdOptions and not dvdOptions and not fullHD and not hdOptions:
            return Quality.SDTV
        elif dvdOptions:
            return Quality.SDDVD
        elif hdOptions and not bluRayOptions and not fullHD and not webdl:
            return Quality.HDTV
        elif not hdOptions and not bluRayOptions and fullHD and not webdl:
            return Quality.FULLHDTV
        elif hdOptions and not bluRayOptions and not fullHD and webdl:
            return Quality.HDWEBDL
        elif not hdOptions and not bluRayOptions and fullHD and webdl:
            return Quality.FULLHDWEBDL
        elif bluRayOptions and hdOptions and not fullHD:
            return Quality.HDBLURAY
        elif bluRayOptions and fullHD and not hdOptions:
            return Quality.FULLHDBLURAY
        else:
            return Quality.UNKNOWN

    @staticmethod
    def _is_english(title):
        english = False
        if re.search("eng", title, re.I):
            sickrage.app.log.debug("Found English release:  " + title)
            english = True

        return english

    @staticmethod
    def _has_only_subs(title):
        title = title.lower()
        if 'sub' in title:
            title = title.split()
            counter = 0
            for word in title:
                if 'ita' in word:
                    counter += 1
                if 'eng' in word:
                    counter += 1
            if counter < 2:
                return True
