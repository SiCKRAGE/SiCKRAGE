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
from sickrage.core.helpers import bs4_parser, convert_size, show_names
from sickrage.providers import TorrentProvider


class NewpctProvider(TorrentProvider):
    def __init__(self):
        super(NewpctProvider, self).__init__("Newpct", 'http://www.newpct.com', False)

        self.urls.update({
            'search': '{base_url}/series'.format(**self.urls),
            'rss': '{base_url}/feed'.format(**self.urls),
            'download': 'http://tumejorserie.com/descargar/index.php?link=torrents/%s.torrent'.format(**self.urls),
        })

        self.onlyspasearch = None
        self.supports_backlog = False

        self.cache = NewpctCache(self, min_time=20)

    def _get_season_search_strings(self, ep_obj):
        search_string = {'Season': []}

        for show_name in set(show_names.allPossibleShowNames(ep_obj.show)):
            search_string['Season'].append(show_name.replace(' ', '-'))

        return [search_string]

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        search_string = {'Episode': []}

        for show_name in set(show_names.allPossibleShowNames(ep_obj.show)):
            search_string['Episode'].append(show_name.replace(' ', '-'))

        return [search_string]

    def search(self, search_strings, age=0, ep_obj=None):
        results = []

        # Only search if user conditions are true
        lang_info = '' if not ep_obj or not ep_obj.show else ep_obj.show.lang

        for mode in search_strings:
            sickrage.srCore.srLogger.debug('Search mode: {}'.format(mode))

            # Only search if user conditions are true
            if self.onlyspasearch and lang_info != 'es' and mode != 'RSS':
                sickrage.srCore.srLogger.debug('Show info is not spanish, skipping provider search')
                continue

            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug('Search string: {}'.format(search_string))

                searchURL = self.urls['search'] + '/' + search_string

                try:
                    data = sickrage.srCore.srWebSession.get(searchURL).text
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

        def _process_title(title):
            # Strip word Serie from start of title
            title = title.split(' ', 1)[1]

            # Add encoder and group to title
            title = title.strip() + ' x264-NEWPCT'

            # Quality - Use re module to avoid case sensitive problems with replace
            title = re.sub(r'\[ALTA DEFINICION[^\[]*]', '720p HDTV', title, flags=re.IGNORECASE)
            title = re.sub(r'\[(BluRay MicroHD|MicroHD 1080p)[^\[]*]', '1080p BluRay', title, flags=re.IGNORECASE)
            title = re.sub(r'\[(B[RD]rip|BLuRay)[^\[]*]', '720p BluRay', title, flags=re.IGNORECASE)

            # Language
            title = re.sub(r'\[(Spanish|Castellano|Español)[^\[]*]', 'SPANISH AUDIO', title, flags=re.IGNORECASE)
            title = re.sub(r'\[AC3 5\.1 Español[^\[]*]', 'SPANISH AUDIO AC3 5.1', title, flags=re.IGNORECASE)

            # Season and Episode
            title = re.sub(r'Temporada[^\[]*?', 'SEASON', title, flags=re.IGNORECASE)
            title = re.sub(r'Capitulo[^\[]*?', 'EPISODE', title, flags=re.IGNORECASE)

            return title

        with bs4_parser(data) as html:
            torrent_table = html.find('ul', class_='buscar-list')
            torrent_rows = torrent_table('li') if torrent_table else []

            # Continue only if at least one release is found
            if len(torrent_rows) < 3:  # Headers + 1 Torrent + Pagination
                sickrage.srCore.srLogger.debug('Data returned from provider does not contain any torrents')
                return results

            for row in torrent_rows[1:-1]:
                try:
                    torrent_anchor = row.find_all('a')[1]
                    title = _process_title(torrent_anchor.get_text())
                    download_url = self.process_link(torrent_anchor.get('href', ''))
                    if not all([title, download_url]):
                        continue

                    seeders = 1  # Provider does not provide seeders
                    leechers = 0  # Provider does not provide leechers
                    torrent_size = row.find_all('span')[4].get_text(strip=True)
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
                except Exception:
                    sickrage.srCore.srLogger.error('Failed parsing provider')

        return results

    def process_link(self, url):
        try:
            url = sickrage.srCore.srWebSession.get(url).text
            download_id = re.search(r'http://tumejorserie.com/descargar/.+?(\d{6}).+?\.html', url, re.DOTALL).group(1)
            url = self.urls['download'] % download_id
        except Exception:
            pass

        return url

class NewpctCache(TVCache):
    def _get_rss_data(self):
        results = {'entries': []}

        sickrage.srCore.srLogger.debug("Cache update URL: %s" % self.provider.urls['rss'])

        data = self.getRSSFeed(self.provider.urls['rss'])
        for entry in data.entries:
            if 'Series' in entry.category:
                entry.link = self.provider.process_link(entry.link)
                results['entries'].append(entry)

        return results