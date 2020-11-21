# coding=utf-8
# Author: CristianBB
# Greetings to Mr. Pine-apple
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import re

from unidecode import unidecode

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, convert_size
from sickrage.core.helpers.show_names import all_possible_show_names
from sickrage.core.tv.show.helpers import find_show
from sickrage.search_providers import TorrentProvider


class NewpctProvider(TorrentProvider):
    def __init__(self):
        super(NewpctProvider, self).__init__("Newpct", 'http://www.newpct.com', False)

        self._urls.update({
            'search': ['{base_url}/descargar-serie/%s'.format(**self._urls),
                       '{base_url}/descargar-seriehd/%s'.format(**self._urls),
                       '{base_url}/descargar-serievo/%s'.format(**self._urls)],
            'rss': '{base_url}/feed'.format(**self._urls),
            'download': 'https://tumejorserie.com/descargar/index.php?link=torrents/%s.torrent'.format(**self._urls),
        })

        # custom settings
        self.custom_settings = {
            'onlyspasearch': False
        }

        self.cache = NewpctCache(self, min_time=20)

    def _get_season_search_strings(self, series_id, series_provider_id, season, episode):
        """
        Get season search strings.
        """
        search_strings = {
            'Season': []
        }

        season_strings = ['%s/capitulo-%s%s/',
                          '%s/capitulo-%s%s/hdtv/',
                          '%s/capitulo-%s%s/hdtv-720p-ac3-5-1/',
                          '%s/capitulo-%s%s/hdtv-1080p-ac3-5-1/',
                          '%s/capitulo-%s%s/bluray-1080p/']

        show_object = find_show(series_id, series_provider_id)
        if not show_object:
            return [search_strings]

        episode_object = show_object.get_episode(season, episode)

        for show_name in all_possible_show_names(series_id, series_provider_id, episode_object.season):
            for season_string in season_strings:
                season_string = season_string % (
                    show_name.replace(' ', '-'), episode_object.get_season_episode_numbering()[0], episode_object.get_season_episode_numbering()[1]
                )
                search_strings['Season'].append(season_string.strip())

        return [search_strings]

    def _get_episode_search_strings(self, series_id, series_provider_id, season, episode, add_string=''):
        """
        Get episode search strings.
        """

        search_strings = {
            'Episode': []
        }

        episode_strings = ['%s/capitulo-%s%s/',
                           '%s/capitulo-%s%s/hdtv/',
                           '%s/capitulo-%s%s/hdtv-720p-ac3-5-1/',
                           '%s/capitulo-%s%s/hdtv-1080p-ac3-5-1/',
                           '%s/capitulo-%s%s/bluray-1080p/']

        show_object = find_show(series_id, series_provider_id)
        if not show_object:
            return [search_strings]

        episode_object = show_object.get_episode(season, episode)

        for show_name in all_possible_show_names(series_id, series_provider_id, episode_object.season):
            for episode_string in episode_strings:
                episode_string = episode_string % (
                    show_name.replace(' ', '-'), episode_object.get_season_episode_numbering()[0], episode_object.get_season_episode_numbering()[1]
                )
                search_strings['Episode'].append(episode_string.strip())

        return [search_strings]

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []

        # Only search if user conditions are true
        lang_info = find_show(series_id, series_provider_id).lang

        for mode in search_strings:
            sickrage.app.log.debug('Search mode: {}'.format(mode))

            # Only search if user conditions are true
            if self.custom_settings['onlyspasearch'] and lang_info != 'es' and mode != 'RSS':
                sickrage.app.log.debug('Show info is not spanish, skipping provider search')
                continue

            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug('Search string: {}'.format(search_string))

                for search_url in self.urls['search']:
                    resp = self.session.get(search_url % search_string)
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

        with bs4_parser(data) as html:
            if 'no encontrada' in html.get_text():
                return results

            try:
                link = html.find(rel='canonical')
                if not link:
                    return results

                try:
                    title = unidecode(html.find('h1').get_text().split('/')[1])
                    title = self._process_title(title, link['href'])
                except Exception:
                    title = None

                try:
                    download_url = self.urls['download'] % re.search(
                        r'http://tumejorserie.com/descargar/.+?(\d{6}).+?\.html', html.get_text(), re.DOTALL).group(1)
                except Exception:
                    download_url = None

                if not all([title, download_url]):
                    return results

                seeders = 1  # Provider does not provide seeders
                leechers = 0  # Provider does not provide leechers

                torrent_size = html.find_all(class_='imp')[1].get_text()
                torrent_size = re.sub(r'Size: ([\d.]+).+([KMGT]B)', r'\1 \2', torrent_size)
                size = convert_size(torrent_size, -1)

                results += [
                    {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                ]

                if mode != 'RSS':
                    sickrage.app.log.debug("Found result: {}".format(title))
            except Exception:
                sickrage.app.log.error('Failed parsing provider')

        return results

    def _process_title(self, title, url):
        # Convert to unicode and strip unwanted characters
        try:
            title = title.encode('latin-1').decode('utf8').strip()
        except Exception:
            title = title.strip()

        # Check if subtitled
        subtitles = re.search(r'\[V.O.[^\[]*]', title, flags=re.I)

        # Quality - Use re module to avoid case sensitive problems with replace
        title = re.sub(r'\[HDTV.1080[p][^\[]*]', '1080p HDTV x264', title, flags=re.IGNORECASE)
        title = re.sub(r'\[(HDTV.720[p]|ALTA.DEFINICION)[^\[]*]', '720p HDTV x264', title, flags=re.IGNORECASE)
        title = re.sub(r'\[(BluRay.MicroHD|MicroHD.1080p)[^\[]*]', '1080p BluRay x264', title, flags=re.IGNORECASE)
        title = re.sub(r'\[(B[RD]rip|B[Ll]uRay)[^\[]*]', '720p BluRay x264', title, flags=re.IGNORECASE)
        title = re.sub(r'\[HDTV[^\[]*]', 'HDTV x264', title, flags=re.IGNORECASE)

        # detect hdtv/bluray by url
        # hdtv 1080p example url: http://www.newpct.com/descargar-seriehd/foo/capitulo-610/hdtv-1080p-ac3-5-1/
        # hdtv 720p example url: http://www.newpct.com/descargar-seriehd/foo/capitulo-26/hdtv-720p-ac3-5-1/
        # hdtv example url: http://www.newpct.com/descargar-serie/foo/capitulo-214/hdtv/
        # bluray compilation example url: http://www.newpct.com/descargar-seriehd/foo/capitulo-11/bluray-1080p/
        title_hdtv = re.search(r'HDTV', title, flags=re.I)
        title_720p = re.search(r'720p', title, flags=re.I)
        title_1080p = re.search(r'1080p', title, flags=re.I)
        title_x264 = re.search(r'x264', title, flags=re.I)
        title_bluray = re.search(r'bluray', title, flags=re.I)
        title_serie_hd = re.search(r'descargar-seriehd', title, flags=re.I)
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
        title = re.sub(r'(\[Cap.(\d{1,2})(\d{2})[^\[]*]).*', r'\1 SPANISH AUDIO', title, flags=re.IGNORECASE)

        # Group
        if subtitles:
            title += '-NEWPCTVO'
        else:
            title += '-NEWPCT'

        return title

    def _process_link(self, url):
        try:
            return self.urls['download'] % re.search(r'http://tumejorserie.com/descargar/.+?(\d{6}).+?\.html',
                                                     self.session.get(url).text, re.DOTALL).group(1)
        except Exception:
            pass


class NewpctCache(TVCache):
    def _get_rss_data(self):
        results = {'entries': []}

        for result in self.get_rss_feed(self.provider.urls['rss']).get('entries', []):
            if 'Series' in result.category:
                title = self.provider._process_title(result.title, result.link)
                link = self.provider._process_link(result.link)
                results['entries'].append({'title': title, 'link': link})

        return results
