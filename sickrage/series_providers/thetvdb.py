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


from operator import itemgetter
from urllib.parse import quote

import sickrage
from sickrage.core.enums import SeriesProviderID
from sickrage.series_providers import SeriesProvider


class SeriesProviderActors(list):
    """Holds all Actor instances for a show
    """
    pass


class SeriesProviderActor(dict):
    """Represents a single actor. Should contain..

    id,
    image,
    name,
    role,
    sortorder
    """

    def __repr__(self):
        return "<Actor \"{}\">".format(self.get("name"))


class TheTVDB(SeriesProvider):
    """Create easy-to-use interface to name of season/episode name
    """

    def __init__(self):
        super(TheTVDB, self).__init__(SeriesProviderID.THETVDB)
        self.trakt_id = 'tvdb'
        self.xem_origin = 'tvdb'
        self.icon = 'thetvdb16.png'
        self.show_url = 'http://thetvdb.com/?tab=series&id='
        self.dvd_order = False

    def search(self, query, language='eng'):
        """
        This searches TheTVDB.com for the series by name and returns the result list
        """

        sickrage.app.log.debug(f"Searching for show using query term: {query}")

        search_results = sickrage.app.api.series_provider.search(provider=self.slug, query=quote(query), language=language)
        if not search_results or 'error' in search_results:
            sickrage.app.log.debug(f'Series search using query term {query} returned zero results, cannot find series on {self.name}')

        return search_results

    def search_by_id(self, remote_id, language='eng'):
        """
        This searches TheTVDB.com for the seriesid, imdbid, or zap2itid  and returns the result list
        """

        sickrage.app.log.debug(f"Searching for show using remote id: {remote_id}")

        if not isinstance(remote_id, int):
            remote_id = quote(remote_id)

        search_result = sickrage.app.api.series_provider.search_by_id(provider=self.slug, remote_id=remote_id, language=language)
        if not search_result or 'error' in search_result:
            sickrage.app.log.debug(f'Series search using remote id {remote_id} returned zero results, cannot find series on {self.name}')

        return search_result

    def get_series_info(self, sid, language='eng', dvd_order=False, enable_cache=True):
        """
        Takes a series id, gets the episodes URL and parses the TVDB
        """

        # check if series is in cache
        if sid in self.cache and enable_cache:
            search_result = self.cache[sid]
            if search_result:
                return search_result

        # get series data
        sickrage.app.log.debug(f"[{sid}]: Getting series info from {self.name}")

        resp = sickrage.app.api.series_provider.get_series_info(provider=self.slug, series_id=sid, language=language)
        if not resp or 'error' in resp:
            sickrage.app.log.debug(f"[{sid}]: Unable to get series info from {self.name}")
            return None

        # add season data to cache
        for season in resp['seasons']:
            season_number = int(float(season.get('seasonNumber')))

            for k, v in season.items():
                self.cache.add_season_data(sid, season_number, k, v)

        # add series data to cache
        [self.cache.add_show_data(sid, k, v) for k, v in resp.items() if k != 'seasons']

        # get season and episode data
        sickrage.app.log.debug(f'[{sid}]: Getting episode data from {self.name}')

        season_type = 'dvd' if dvd_order else 'official'
        resp = sickrage.app.api.series_provider.get_episodes_info(provider=self.slug, series_id=sid, season_type=season_type, language=language)
        if not resp or 'error' in resp:
            sickrage.app.log.debug(f"[{sid}]: Unable to get episode data from {self.name}")
            return None

        # add episode data to cache
        episode_incomplete = False
        for episode in resp:
            season_number, episode_number = episode.get('seasonNumber'), episode.get('episodeNumber')
            if season_number is None or episode_number is None:
                episode_incomplete = True
                continue

            season_number = int(float(season_number))
            episode_number = int(float(episode_number))

            for k, v in episode.items():
                self.cache.add_episode_data(sid, season_number, episode_number, k, v)

        if episode_incomplete:
            sickrage.app.log.debug(f"{sid}: Series has incomplete season/episode numbers")

        # set last updated
        # self.cache.add_show_data(sid, 'last_updated', int(time.mktime(datetime.now().timetuple())))

        return self.cache[int(sid)]

    def image_types(self):
        return {
            'series': {
                'banner': 1,
                'poster': 2,
                'fanart': 3
            },
            'season': {
                'banner': 6,
                'poster': 7,
                'fanart': 8
            }
        }

    def images(self, sid, key_type='poster', season=None, language='eng'):
        sickrage.app.log.debug(f'Getting {key_type} images for {sid}')

        images = []

        series_info = self.get_series_info(sid=sid, language=language)
        if not series_info:
            return []

        season_map = {}
        for season_number in series_info:
            season_map[season_number] = series_info[season_number]['id']

        for item in sorted(series_info.artworks, key=itemgetter("score"), reverse=True):
            if season and season_map[season] == item['seasonId'] and item['type'] == self.image_types()['season'][key_type]:
                images.append(item)
            elif not season and item['type'] == self.image_types()['series'][key_type]:
                images.append(item)

        if not images and key_type == 'poster':
            if season:
                image_url = series_info[season].imageUrl
                if image_url != '':
                    images.append({'image': image_url})
            else:
                image_url = series_info.imageUrl
                if image_url != '':
                    images.append({'image': image_url})

        return images

    def updates(self, since):
        resp = sickrage.app.api.series_provider.updates(provider=self.slug, since=since)
        if resp and 'error' not in resp:
            return resp

    def languages(self):
        resp = sickrage.app.api.series_provider.languages(provider=self.slug)
        if not resp or 'error' in resp:
            return {}

        return sorted(resp, key=lambda i: i['name'])

    def __repr__(self):
        return repr(self.cache)
