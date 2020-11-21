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

import sickrage
from sickrage.core.databases.cache import CacheDB
from sickrage.core.helpers import full_sanitize_scene_name


class NameCache(object):
    def __init__(self, *args, **kwargs):
        self.name = "NAMECACHE"
        self.running = False
        self.min_time = 10
        self.last_update = {}
        self.cache = {}

    def should_update(self, show):
        # if we've updated recently then skip the update
        if datetime.today() - (self.last_update.get(show.name) or datetime.fromtimestamp(
                int(time.mktime(datetime.today().timetuple())))) < timedelta(minutes=self.min_time):
            return True

    def put(self, name, series_id=0):
        """
        Adds the show & tvdb id to the scene_names table in cache db

        :param name: The show name to cache
        :param series_id: the TVDB id that this show should be cached with (can be None/0 for unknown)
        """

        session = sickrage.app.cache_db.session()

        # standardize the name we're using to account for small differences in providers
        name = full_sanitize_scene_name(name)

        self.cache[name] = int(series_id)

        try:
            session.query(CacheDB.SceneName).filter_by(name=name, series_id=int(series_id)).one()
        except orm.exc.NoResultFound:
            session.add(CacheDB.SceneName(**{
                'series_id': series_id,
                'name': name
            }))
        finally:
            session.commit()

    def get(self, name):
        """
        Looks up the given name in the scene_names table in cache db

        :param name: The show name to look up.
        :return: the TVDB id that resulted from the cache lookup or None if the show wasn't found in the cache
        """
        name = full_sanitize_scene_name(name)
        if name in self.cache:
            return int(self.cache[name])

    def clear(self, series_id=None, name=None):
        """
        Deletes all entries from the cache matching the series_id or name.
        """

        session = sickrage.app.cache_db.session()

        if any([series_id, name]):
            if series_id:
                session.query(CacheDB.SceneName).filter_by(series_id=series_id).delete()
                session.commit()
            elif name:
                session.query(CacheDB.SceneName).filter_by(name=name).delete()
                session.commit()

            for key, value in self.cache.copy().items():
                if value == series_id or key == name:
                    del self.cache[key]

    def load(self):
        session = sickrage.app.cache_db.session()
        self.cache = dict([(x.name, x.series_id) for x in session.query(CacheDB.SceneName)])

    def save(self):
        """
        Commit cache to database file
        """

        session = sickrage.app.cache_db.session()

        sql_t = []

        for name, series_id in self.cache.items():
            try:
                session.query(CacheDB.SceneName).filter_by(name=name, series_id=series_id).one()
            except orm.exc.NoResultFound:
                sql_t.append({
                    'series_id': series_id,
                    'name': name
                })

        session.bulk_insert_mappings(CacheDB.SceneName, sql_t)
        session.commit()
