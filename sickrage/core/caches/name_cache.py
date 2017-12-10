# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
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

import time
from datetime import datetime, timedelta

from CodernityDB.database import RecordNotFound

import sickrage
from sickrage.core.helpers import full_sanitizeSceneName
from sickrage.core.scene_exceptions import retrieve_exceptions, get_scene_seasons, get_scene_exceptions


class NameCache(object):
    def __init__(self, *args, **kwargs):
        self.min_time = 10
        self.last_update = {}
        self.cache = {}

    def should_update(self, show):
        # if we've updated recently then skip the update
        if datetime.today() - (self.last_update.get(show.name) or datetime.fromtimestamp(
                int(time.mktime(datetime.today().timetuple())))) < timedelta(minutes=self.min_time):
            return True

    def put(self, name, indexer_id=0):
        """
        Adds the show & tvdb id to the scene_names table in cache.db.

        :param name: The show name to cache
        :param indexer_id: the TVDB id that this show should be cached with (can be None/0 for unknown)
        """

        # standardize the name we're using to account for small differences in providers
        name = full_sanitizeSceneName(name)
        if name not in self.cache:
            self.cache[name] = int(indexer_id)

            try:
                if not len([x['doc'] for x in sickrage.app.cache_db.db.get_many('scene_names', name, with_doc=True) if
                            x['doc']['indexer_id'] == indexer_id]):
                    # insert name into cache
                    sickrage.app.cache_db.db.insert({
                        '_t': 'scene_names',
                        'indexer_id': indexer_id,
                        'name': name
                    })
            except RecordNotFound:
                # insert name into cache
                sickrage.app.cache_db.db.insert({
                    '_t': 'scene_names',
                    'indexer_id': indexer_id,
                    'name': name
                })

    def get(self, name):
        """
        Looks up the given name in the scene_names table in cache.db.

        :param name: The show name to look up.
        :return: the TVDB id that resulted from the cache lookup or None if the show wasn't found in the cache
        """
        name = full_sanitizeSceneName(name)
        if name in self.cache:
            return int(self.cache[name])

    def clear(self, indexerid=0):
        """
        Deletes all "unknown" entries from the cache (names with indexer_id of 0).
        """
        [sickrage.app.cache_db.db.delete(x['doc']) for x in
         sickrage.app.cache_db.db.all('scene_names', with_doc=True)
         if x['doc']['indexer_id'] in [indexerid, 0]]

        for item in [self.cache[key] for key, value in self.cache.items() if value == 0 or value == indexerid]:
            del item

    def load(self):
        self.cache = dict([(x['doc']['name'], x['doc']['indexer_id']) for x in
                           sickrage.app.cache_db.db.all('scene_names', with_doc=True)])

    def save(self):
        """Commit cache to database file"""
        for name, indexer_id in self.cache.items():
            try:
                if len([x['doc'] for x in sickrage.app.cache_db.db.get_many('scene_names', name, with_doc=True) if
                        x['doc']['indexer_id'] == indexer_id]):
                    continue
            except RecordNotFound:
                pass

            # insert name into cache
            sickrage.app.cache_db.db.insert({
                '_t': 'scene_names',
                'indexer_id': indexer_id,
                'name': name
            })

    def build(self, show):
        """Build internal name cache

        :param show: Specify show to build name cache for, if None, just do all shows
        """

        retrieve_exceptions()

        if self.should_update(show):
            self.last_update[show.name] = datetime.fromtimestamp(int(time.mktime(datetime.today().timetuple())))

            self.clear(show.indexerid)
            for curSeason in [-1] + get_scene_seasons(show.indexerid):
                for name in list(set(get_scene_exceptions(show.indexerid, season=curSeason) + [show.name])):
                    self.put(name, show.indexerid)
