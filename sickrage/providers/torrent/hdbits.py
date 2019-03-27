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



import json
from urllib.parse import urlencode

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.exceptions import AuthException
from sickrage.core.helpers import try_int
from sickrage.providers import TorrentProvider


class HDBitsProvider(TorrentProvider):
    def __init__(self):
        super(HDBitsProvider, self).__init__("HDBits", 'https://hdbits.org', True)

        self.urls.update({
            'search': '{base_url}/api/torrents'.format(**self.urls),
            'rss': '{base_url}/api/torrents'.format(**self.urls),
            'download': '{base_url}/download.php'.format(**self.urls)
        })

        self.username = None
        self.passkey = None

        self.cache = HDBitsCache(self, min_time=15)

    def _check_auth(self):
        if not self.username or not self.passkey:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def _check_auth_from_data(self, parsedJSON):
        if 'status' in parsedJSON and 'message' in parsedJSON:
            if parsedJSON.get('status') == 5:
                sickrage.app.log.warning(
                    "Invalid username or password. Check your settings")

        return True

    def _get_season_search_strings(self, ep_obj):
        season_search_string = [self._make_post_data_JSON(show=ep_obj.show, season=ep_obj)]
        return season_search_string

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        episode_search_string = [self._make_post_data_JSON(show=ep_obj.show, episode=ep_obj)]
        return episode_search_string

    def _get_title_and_url(self, item):
        title = item['name']
        if title:
            title = self._clean_title_from_provider(title)

        url = self.urls['download'] + '?' + urlencode({'id': item['id'], 'passkey': self.passkey})

        return title, url

    def search(self, search_strings, age=0, ep_obj=None, **kwargs):
        results = []

        sickrage.app.log.debug("Search string: %s" % search_strings)

        self._check_auth()

        try:
            parsedJSON = self.session.post(self.urls['search'], data=search_strings).json()
        except Exception:
            return []

        if self._check_auth_from_data(parsedJSON):
            if parsedJSON and 'data' in parsedJSON:
                for item in parsedJSON['data']:
                    results.append(item)
            else:
                sickrage.app.log.warning("Resulting JSON from provider isn't correct, not parsing it")

        # sort by number of seeders
        results.sort(key=lambda k: try_int(k.get('seeders', 0)), reverse=True)

        return results

    def _make_post_data_JSON(self, show=None, episode=None, season=None, search_term=None):
        post_data = {
            'username': self.username,
            'passkey': self.passkey,
            'category': [2],
            # TV Category
        }

        if episode:
            if show.air_by_date:
                post_data['tvdb'] = {
                    'id': show.indexerid,
                    'episode': str(episode.airdate).replace('-', '|')
                }
            elif show.sports:
                post_data['tvdb'] = {
                    'id': show.indexerid,
                    'episode': episode.airdate.strftime('%b')
                }
            elif show.anime:
                post_data['tvdb'] = {
                    'id': show.indexerid,
                    'episode': "%i" % int(episode.scene_absolute_number)
                }
            else:
                post_data['tvdb'] = {
                    'id': show.indexerid,
                    'season': episode.scene_season,
                    'episode': episode.scene_episode
                }

        if season:
            if show.air_by_date or show.sports:
                post_data['tvdb'] = {
                    'id': show.indexerid,
                    'season': str(season.airdate)[:7],
                }
            elif show.anime:
                post_data['tvdb'] = {
                    'id': show.indexerid,
                    'season': "%d" % season.scene_absolute_number,
                }
            else:
                post_data['tvdb'] = {
                    'id': show.indexerid,
                    'season': season.scene_season,
                }

        if search_term:
            post_data['search'] = search_term

        return json.dumps(post_data)


class HDBitsCache(TVCache):
    def _get_rss_data(self):
        results = []

        try:
            resp = self.provider.session.post(self.provider.urls['rss'],
                                                     data=self.provider._make_post_data_JSON()).json()

            if self.provider._check_auth_from_data(resp):
                results = resp['data']
        except Exception:
            pass

        return {'entries': results}
