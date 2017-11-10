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
from sickrage.core.helpers.show_names import allPossibleShowNames
from sickrage.providers import TorrentProvider


class NewpctProvider(TorrentProvider):
    def __init__(self):
        super(NewpctProvider, self).__init__("Newpct", 'http://www.newpct.com', False)

        self.urls.update({
            'search': ['{base_url}/descargar-serie/%s'.format(**self.urls),
                       '{base_url}/descargar-seriehd/%s'.format(**self.urls)],
            'rss': '{base_url}/feed'.format(**self.urls),
            'download': 'http://tumejorserie.com/descargar/index.php?link=torrents/%s.torrent'.format(**self.urls),
        })

        self.onlyspasearch = None

        self.cache = NewpctCache(self, min_time=20)

    def _get_season_search_strings(self, episode):
        """
        Get season search strings.
        """
        search_string = {
            'Season': []
        }

        for show_name in allPossibleShowNames(episode.show, episode.scene_season):
            for string in ['%s/capitulo-%s%s/', '%s/capitulo-%s%s/hdtv/', '%s/capitulo-%s%s/hdtv-720p-ac3-5-1/']:
                season_string = string % (show_name.replace(' ', '-'), episode.season, episode.episode)
                search_string['Season'].append(season_string.strip())

        return [search_string]

    def _get_episode_search_strings(self, episode, add_string=''):
        """
        Get episode search strings.
        """
        if not episode:
            return []

        search_string = {
            'Episode': []
        }

        for show_name in allPossibleShowNames(episode.show, episode.scene_season):
            for string in ['%s/capitulo-%s%s/', '%s/capitulo-%s%s/hdtv/', '%s/capitulo-%s%s/hdtv-720p-ac3-5-1/']:
                episode_string = string % (show_name.replace(' ', '-'), episode.season, episode.episode)
                search_string['Episode'].append(episode_string.strip())

        return [search_string]

    def search(self, search_strings, age=0, ep_obj=None):
        results = []

        # Only search if user conditions are true
        lang_info = '' if not ep_obj or not ep_obj.show else ep_obj.show.lang

        for mode in search_strings:
            sickrage.app.log.debug('Search mode: {}'.format(mode))

            # Only search if user conditions are true
            if self.onlyspasearch and lang_info != 'es' and mode != 'RSS':
                sickrage.app.log.debug('Show info is not spanish, skipping provider search')
                continue

            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug('Search string: {}'.format(search_string))

                for search_url in self.urls['search']:
                    try:
                        data = sickrage.app.wsession.get(search_url % search_string).text
                        items = self.parse(data, mode)
                        if not len(items): break
                        results += items
                    except Exception:
                        sickrage.app.log.debug('No data returned from provider')

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
            if 'no encontrada' in html.get_text():
                return results

            try:
                title = self._process_title(html.find('h1').get_text().split('/')[1])
                download_id = re.search(r'http://tumejorserie.com/descargar/.+?(\d{6}).+?\.html', html.get_text(),
                                        re.DOTALL).group(1)
                download_url = self.urls['download'] % download_id
                if not all([title, download_url]):
                    return results

                seeders = 1  # Provider does not provide seeders
                leechers = 0  # Provider does not provide leechers

                torrent_size = html.find_all(class_='imp')[1].get_text()
                torrent_size = re.sub(r'Size: ([\d.]+).+([KMGT]B)', r'\1 \2', torrent_size)
                size = convert_size(torrent_size, -1)

                item = {
                    'title': title,
                    'link': download_url,
                    'size': size,
                    'seeders': seeders,
                    'leechers': leechers,
                }
                if mode != 'RSS':
                    sickrage.app.log.debug('Found result: {}'.format(title))

                    results.append(item)
            except Exception:
                sickrage.app.log.error('Failed parsing provider')

        return results

    def _process_title(self, title):
        # Strip unwanted characters
        title = title.strip()

        # Quality - Use re module to avoid case sensitive problems with replace
        title = re.sub(r'\[HDTV.1080[p][^\[]*]', '[1080p HDTV x264]', title, flags=re.IGNORECASE)
        title = re.sub(r'\[(HDTV.720[p]|ALTA.DEFINICION)[^\[]*]', '[720p HDTV x264]', title, flags=re.IGNORECASE)
        title = re.sub(r'\[(BluRay.MicroHD|MicroHD.1080p)[^\[]*]', '[1080p BluRay x264]', title, flags=re.IGNORECASE)
        title = re.sub(r'\[(B[RD]rip|BLuRay)[^\[]*]', '[720p BluRay x264]', title, flags=re.IGNORECASE)
        title = re.sub(r'\[HDTV[^\[]*]', '[HDTV x264]', title, flags=re.IGNORECASE)

        # Language
        title = re.sub(r'(\[Cap.(\d{1,2})(\d{2})[^\[]*]).*', r'\1[SPANISH AUDIO]', title, flags=re.IGNORECASE)

        # Add encoder and group to title
        title += '[NEWPCT]'

        return title

    def _process_link(self, url):
        try:
            url = sickrage.app.wsession.get(url).text
            download_id = re.search(r'http://tumejorserie.com/descargar/.+?(\d{6}).+?\.html', url, re.DOTALL).group(1)
            url = self.urls['download'] % download_id
        except Exception as e:
            pass

        return url


class NewpctCache(TVCache):
    def _get_rss_data(self):
        results = {'entries': []}

        for result in self.getRSSFeed(self.provider.urls['rss']).entries:
            if 'Series' in result.category:
                title = self.provider._process_title(result.title)
                link = self.provider._process_link(result.link)
                results['entries'].append({'title': title, 'link': link})

        return results
