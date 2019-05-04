# Author: echel0n <echel0n@sickrage.ca>
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.



import re

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import try_int, show_names, sanitizeSceneName
from sickrage.core.tv.episode.helpers import find_episode
from sickrage.providers import TorrentProvider


class ZooqleProvider(TorrentProvider):
    def __init__(self):
        """Initialize the class."""
        super(ZooqleProvider, self).__init__('Zooqle', 'https://zooqle.com', False)

        # URLs
        self.urls.update({
            'search': '{base_url}/search'.format(**self.urls),
            'api': '{base_url}/api/media/%s'.format(**self.urls),
        })

        # Proper Strings
        self.proper_strings = ['PROPER', 'REPACK', 'REAL']

        # Miscellaneous Options

        # Torrent Stats
        self.minseed = None
        self.minleech = None

        # Cache
        self.cache = TVCache(self, min_time=15)

    def _get_season_search_strings(self, show_id, episode_id):
        search_string = {'Season': []}

        episode_obj = find_episode(show_id, episode_id)

        for show_name in set(show_names.all_possible_show_names(show_id)):
            for sep in ' ', ' - ':
                season_string = show_name + sep + 'Series '
                if episode_obj.show.air_by_date or episode_obj.show.sports:
                    season_string += str(episode_obj.airdate).split('-')[0]
                elif episode_obj.show.anime:
                    season_string += '%d' % episode_obj.scene_absolute_number
                else:
                    season_string += '%d' % int(episode_obj.scene_season)

                search_string['Season'].append(re.sub(r'\s+', ' ', season_string.replace('.', ' ').strip()))

        return [search_string]

    def _get_episode_search_strings(self, show_id, episode_id, add_string=''):
        search_string = {'Episode': []}

        episode_obj = find_episode(show_id, episode_id)

        for show_name in set(show_names.all_possible_show_names(show_id)):
            for sep in ' ', ' - ':
                ep_string = sanitizeSceneName(show_name) + sep
                if episode_obj.show.air_by_date:
                    ep_string += str(episode_obj.airdate)
                elif episode_obj.show.sports:
                    ep_string += str(episode_obj.airdate) + '|' + episode_obj.airdate.strftime('%b')
                elif episode_obj.show.anime:
                    ep_string += '%i' % int(episode_obj.scene_absolute_number)
                else:
                    ep_string += sickrage.app.naming_ep_type[4] % {'seasonnumber': episode_obj.scene_season,
                                                                   'episodenumber': episode_obj.scene_episode}

                if add_string:
                    ep_string += ' %s' % add_string

                search_string['Episode'].append(re.sub(r'\s+', ' ', ep_string.replace('.', ' ').strip()))

        return [search_string]

    def _get_torrent_info(self, torrent_hash):
        try:
            return self.session.get(self.urls['api'] % torrent_hash).json()
        except Exception:
            return {}

    def search(self, search_strings, age=0, show_id=None, episode_id=None, **kwargs):
        """
        Search a provider and parse the results.

        :param search_strings: A dict with mode (key) and the search value (value)
        :param age: Not used
        :param ep_obj: Not used
        :returns: A list of search results (structure)
        """
        results = []

        # Search Params
        search_params = {
            'q': '* category:TV',
            's': 'dt',
            'v': 't',
            'sd': 'd',
        }

        for mode in search_strings:
            sickrage.app.log.debug('Search mode: {}'.format(mode))

            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug('Search string: {}'.format(search_string))
                    search_params['q'] = '{} category:TV'.format(search_string)

                search_params['fmt'] = 'rss'
                search_params['pg'] = 1

                while search_params['pg'] < 11:
                    data = self.cache.get_rss_feed(self.urls['search'], params=search_params)
                    if not data or not data.get('feed'):
                        sickrage.app.log.debug('No data returned from provider')
                        break

                    results += self.parse(data, mode)

                    total_results = try_int(data['feed'].get('opensearch_totalresults'))
                    start_index = try_int(data['feed'].get('opensearch_startindex'))
                    items_per_page = try_int(data['feed'].get('opensearch_itemsperpage'))
                    if not total_results or start_index + items_per_page > total_results:
                        break

                    search_params['pg'] += 1

        return results

    def parse(self, data, mode):
        """
        Parse search results for items.

        :param data: The raw response from a search
        :param mode: The current mode used to search, e.g. RSS

        :return: A list of items found
        """
        results = []

        if not data.get('entries'):
            sickrage.app.log.debug('Data returned from provider does not contain any torrents')
            return results

        for item in data['entries']:
            try:
                title = item.get('title')
                download_url = item.get('torrent_magneturi')
                if not all([title, download_url]):
                    continue

                seeders = try_int(item['torrent_seeds'])
                leechers = try_int(item['torrent_peers'])
                size = try_int(item['torrent_contentlength'], -1)

                results += [{
                    'title': title,
                    'link': download_url,
                    'size': size,
                    'seeders': seeders,
                    'leechers': leechers
                }]

                if mode != 'RSS':
                    sickrage.app.log.debug('Found result: {}'.format(title))
            except Exception:
                sickrage.app.log.error("Failed parsing provider")

        return results
