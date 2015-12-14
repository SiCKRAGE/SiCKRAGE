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

import datetime
import logging
import urllib

from sickbeard.providers import generic

from sickbeard import classes
from sickbeard import tvcache
from sickrage.helper.exceptions import AuthException

try:
    import json
except ImportError:
    import simplejson as json


class HDBitsProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "HDBits")

        self.supportsBacklog = True

        self.username = None
        self.passkey = None
        self.ratio = None

        self.cache = HDBitsCache(self)

        self.urls = {'base_url': 'https://hdbits.org',
                     'search': 'https://hdbits.org/api/torrents',
                     'rss': 'https://hdbits.org/api/torrents',
                     'download': 'https://hdbits.org/download.php?'}

        self.url = self.urls[b'base_url']

    def _checkAuth(self):

        if not self.username or not self.passkey:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def _checkAuthFromData(self, parsedJSON):

        if 'status' in parsedJSON and 'message' in parsedJSON:
            if parsedJSON.get('status') == 5:
                logging.warning("Invalid username or password. Check your settings")

        return True

    def _get_season_search_strings(self, ep_obj):
        season_search_string = [self._make_post_data_JSON(show=ep_obj.show, season=ep_obj)]
        return season_search_string

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        episode_search_string = [self._make_post_data_JSON(show=ep_obj.show, episode=ep_obj)]
        return episode_search_string

    def _get_title_and_url(self, item):

        title = item[b'name']
        if title:
            title = self._clean_title_from_provider(title)

        url = self.urls[b'download'] + urllib.urlencode({'id': item[b'id'], 'passkey': self.passkey})

        return (title, url)

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        # FIXME
        results = []

        logging.debug("Search string: %s" % search_params)

        self._checkAuth()

        parsedJSON = self.getURL(self.urls[b'search'], post_data=search_params, json=True)
        if not parsedJSON:
            return []

        if self._checkAuthFromData(parsedJSON):
            if parsedJSON and 'data' in parsedJSON:
                items = parsedJSON[b'data']
            else:
                logging.error("Resulting JSON from provider isn't correct, not parsing it")
                items = []

            for item in items:
                results.append(item)
        # FIXME SORTING
        return results

    def findPropers(self, search_date=None):
        results = []

        search_terms = [' proper ', ' repack ']

        for term in search_terms:
            for item in self._doSearch(self._make_post_data_JSON(search_term=term)):
                if item[b'utadded']:
                    try:
                        result_date = datetime.datetime.fromtimestamp(int(item[b'utadded']))
                    except Exception:
                        result_date = None

                    if result_date:
                        if not search_date or result_date > search_date:
                            title, url = self._get_title_and_url(item)
                            results.append(classes.Proper(title, url, result_date, self.show))

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
                post_data[b'tvdb'] = {
                    'id': show.indexerid,
                    'episode': str(episode.airdate).replace('-', '|')
                }
            elif show.sports:
                post_data[b'tvdb'] = {
                    'id': show.indexerid,
                    'episode': episode.airdate.strftime('%b')
                }
            elif show.anime:
                post_data[b'tvdb'] = {
                    'id': show.indexerid,
                    'episode': "%i" % int(episode.scene_absolute_number)
                }
            else:
                post_data[b'tvdb'] = {
                    'id': show.indexerid,
                    'season': episode.scene_season,
                    'episode': episode.scene_episode
                }

        if season:
            if show.air_by_date or show.sports:
                post_data[b'tvdb'] = {
                    'id': show.indexerid,
                    'season': str(season.airdate)[:7],
                }
            elif show.anime:
                post_data[b'tvdb'] = {
                    'id': show.indexerid,
                    'season': "%d" % season.scene_absolute_number,
                }
            else:
                post_data[b'tvdb'] = {
                    'id': show.indexerid,
                    'season': season.scene_season,
                }

        if search_term:
            post_data[b'search'] = search_term

        return post_data

    def seedRatio(self):
        return self.ratio


class HDBitsCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # only poll HDBits every 15 minutes max
        self.minTime = 15

    def _getRSSData(self):
        results = []

        try:
            parsedJSON = self.provider.getURL(self.provider.urls[b'rss'], post_data=self.provider._make_post_data_JSON(),
                                              json=True)

            if self.provider._checkAuthFromData(parsedJSON):
                results = parsedJSON[b'data']
        except Exception:
            pass

        return {'entries': results}


provider = HDBitsProvider()
