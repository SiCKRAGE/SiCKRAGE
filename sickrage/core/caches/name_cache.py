# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
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
import threading
import time
from datetime import datetime, timedelta

from sqlalchemy import orm

from sickrage.core.databases.cache import CacheDB
from sickrage.core.helpers import full_sanitize_scene_name, strip_accents
from sickrage.core.scene_exceptions import retrieve_exceptions, get_scene_seasons, get_scene_exceptions
from sickrage.core.tv.show.helpers import get_show_list


class NameCache(object):
    def __init__(self, *args, **kwargs):
        self.name = "NAMECACHE"
        self.min_time = 10
        self.last_update = {}
        self.cache = {}

    def run(self):
        threading.currentThread().setName(self.name)
        self.build_all()

    def should_update(self, show):
        # if we've updated recently then skip the update
        if datetime.today() - (self.last_update.get(show.name) or datetime.fromtimestamp(
                int(time.mktime(datetime.today().timetuple())))) < timedelta(minutes=self.min_time):
            return True

    @CacheDB.with_session
    def put(self, name, indexer_id=0, session=None):
        """
        Adds the show & tvdb id to the scene_names table in cache db

        :param name: The show name to cache
        :param indexer_id: the TVDB id that this show should be cached with (can be None/0 for unknown)
        """

        # standardize the name we're using to account for small differences in providers
        name = full_sanitize_scene_name(name)

        self.cache[name] = int(indexer_id)

        try:
            session.query(CacheDB.SceneName).filter_by(name=name, indexer_id=indexer_id).one()
        except orm.exc.NoResultFound:
            session.add(CacheDB.SceneName(**{
                'indexer_id': indexer_id,
                'name': name
            }))

    def get(self, name):
        """
        Looks up the given name in the scene_names table in cache db

        :param name: The show name to look up.
        :return: the TVDB id that resulted from the cache lookup or None if the show wasn't found in the cache
        """
        name = full_sanitize_scene_name(name)
        if name in self.cache:
            return int(self.cache[name])

    @CacheDB.with_session
    def clear(self, indexer_id=None, name=None, session=None):
        """
        Deletes all entries from the cache matching the indexer_id or name.
        """
        if any([indexer_id, name]):
            if indexer_id:
                session.query(CacheDB.SceneName).filter_by(indexer_id=indexer_id).delete()
            elif name:
                session.query(CacheDB.SceneName).filter_by(name=name).delete()

            for key, value in self.cache.copy().items():
                if value == indexer_id or key == name:
                    del self.cache[key]

    @CacheDB.with_session
    def load(self, session=None):
        self.cache = dict([(x.name, x.indexer_id) for x in session.query(CacheDB.SceneName)])

    @CacheDB.with_session
    def save(self, session=None):
        """
        Commit cache to database file
        """

        sql_t = []

        for name, indexer_id in self.cache.items():
            try:
                session.query(CacheDB.SceneName).filter_by(name=name, indexer_id=indexer_id).one()
            except orm.exc.NoResultFound:
                sql_t.append({
                    'indexer_id': indexer_id,
                    'name': name
                })

        session.bulk_insert_mappings(CacheDB.SceneName, sql_t)

    def build(self, show):
        """Build internal name cache

        :param show: Specify show to build name cache for, if None, just do all shows
        """

        retrieve_exceptions()

        if self.should_update(show):
            self.last_update[show.name] = datetime.fromtimestamp(int(time.mktime(datetime.today().timetuple())))

            self.clear(indexer_id=show.indexer_id)

            show_names = []
            for curSeason in [-1] + get_scene_seasons(show.indexer_id):
                for name in list(set(get_scene_exceptions(show.indexer_id, season=curSeason) + [show.name])):
                    show_names.append(name)
                    show_names.append(strip_accents(name))
                    show_names.append(strip_accents(name).replace("'", " "))

            for show_name in set(show_names):
                self.clear(name=show_name)
                self.put(show_name, show.indexer_id)

    def build_all(self):
        for show in get_show_list():
            self.build(show)
