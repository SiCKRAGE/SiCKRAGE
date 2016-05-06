# URL: http://code.google.com/p/sickrage
# Originally written for SickGear
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import urllib

import sickrage
from sickrage.core.caches import tv_cache
from sickrage.core.exceptions import AuthException
from sickrage.providers import TorrentProvider


class TitansOfTVProvider(TorrentProvider):
    def __init__(self):
        super(TitansOfTVProvider, self).__init__('TitansOfTV','titansof.tv')
        self.supportsBacklog = True

        self.supportsAbsoluteNumbering = True
        self.api_key = None
        self.ratio = None
        self.cache = TitansOfTVCache(self)

        self.urls.update({
            'api': '{base_url}/api/torrents'.format(base_url=self.urls['base_url']),
            'download': '{base_url}/api/torrents/%s/download?apikey=%s'.format(base_url=self.urls['base_url'])
        })

    def seedRatio(self):
        return self.ratio

    def _checkAuth(self):
        if not self.api_key:
            raise AuthException('Your authentication credentials for ' + self.name + ' are missing, check your config.')

        return True

    @staticmethod
    def _checkAuthFromData(data):

        if 'error' in data:
            sickrage.srCore.srLogger.warning("Invalid api key. Check your settings")

        return True

    def search(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):
        # FIXME ADD MODE
        self._checkAuth()
        results = []
        params = {}

        if search_params:
            params.update(search_params)

        searchURL = self.urls['api'] + '?' + urllib.urlencode(params)
        sickrage.srCore.srLogger.debug("Search string: %s " % search_params)
        sickrage.srCore.srLogger.debug("Search URL: %s" % searchURL)

        try:
            parsedJSON = sickrage.srCore.srWebSession.get(searchURL, headers={'X-Authorization': self.api_key}).json()
        except Exception:
            sickrage.srCore.srLogger.debug("No data returned from provider")
            return results

        if self._checkAuthFromData(parsedJSON):
            try:
                found_torrents = parsedJSON['results']
            except Exception:
                found_torrents = {}

            for result in found_torrents:
                title = result.get('release_name', '')
                tid = result.get('id', '')
                download_url = self.urls['download'] % (tid, self.api_key)
                # FIXME size, seeders, leechers
                size = -1
                seeders = 1
                leechers = 0

                if not all([title, download_url]):
                    continue

                # Filter unseeded torrent
                # if seeders < self.minseed or leechers < self.minleech:
                #    if mode != 'RSS':
                #        LOGGER.debug(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers))
                #    continue

                item = title, download_url, size, seeders, leechers

                sickrage.srCore.srLogger.debug("Found result: %s " % title)
                results.append(item)

        # FIXME SORTING
        return results

    def _get_season_search_strings(self, ep_obj):
        search_params = {'limit': 100, 'season': 'Season %02d' % ep_obj.scene_season}

        if ep_obj.show.indexer == 1:
            search_params['series_id'] = ep_obj.show.indexerid
        elif ep_obj.show.indexer == 2:
            tvdbid = ep_obj.show.mapIndexers()[1]
            if tvdbid:
                search_params['series_id'] = tvdbid

        return [search_params]

    def _get_episode_search_strings(self, ep_obj, add_string='', **kwargs):

        if not ep_obj:
            return [{}]

        search_params = {'limit': 100, 'episode': 'S%02dE%02d' % (ep_obj.scene_season, ep_obj.scene_episode)}

        # Do a general name search for the episode, formatted like SXXEYY

        if ep_obj.show.indexer == 1:
            search_params['series_id'] = ep_obj.show.indexerid
        elif ep_obj.show.indexer == 2:
            tvdbid = ep_obj.show.mapIndexers()[1]
            if tvdbid:
                search_params['series_id'] = tvdbid

        return [search_params]


class TitansOfTVCache(tv_cache.TVCache):
    def __init__(self, provider_obj):
        tv_cache.TVCache.__init__(self, provider_obj)

        # At least 10 minutes between queries
        self.minTime = 10

    def _getRSSData(self):
        search_params = {'limit': 100}
        return self.provider.search(search_params)
