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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
import functools

from sqlalchemy import Column, Integer, Text, String
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.orm import sessionmaker

from sickrage.core.databases import SRDatabase, ContextSession


@as_declarative()
class CacheDBBase(object):
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class CacheDB(SRDatabase):
    db_version = 3

    session = sessionmaker(class_=ContextSession)

    def __init__(self, db_type, db_prefix, db_host, db_port, db_username, db_password):
        super(CacheDB, self).__init__('cache', db_type, db_prefix, db_host, db_port, db_username, db_password)
        CacheDB.session.configure(bind=self.engine)
        CacheDBBase.metadata.create_all(self.engine)
        for model in CacheDBBase._decl_class_registry.values():
            if hasattr(model, '__tablename__'):
                self.tables[model.__tablename__] = model

    @staticmethod
    def with_session(*args, **kwargs):
        def decorator(func):
            def wrapper(*args, **kwargs):
                if kwargs.get('session'):
                    return func(*args, **kwargs)
                with _Session() as session:
                    kwargs['session'] = session
                    return func(*args, **kwargs)

            return wrapper

        if len(args) == 1 and not kwargs and callable(args[0]):
            # Used without arguments, e.g. @with_session
            # We default to expire_on_commit being false, in case the decorated function returns db instances
            _Session = functools.partial(CacheDB.session, expire_on_commit=False)
            return decorator(args[0])
        else:
            # Arguments were specified, turn them into arguments for Session creation e.g. @with_session(autocommit=True)
            _Session = functools.partial(CacheDB.session, *args, **kwargs)
            return decorator

    def cleanup(self):
        def remove_duplicates_from_last_search_table():
            found = []

            with self.session() as session:
                for x in session.query(CacheDB.LastSearch).all():
                    if x.provider in found:
                        x.delete()
                    else:
                        found.append(x.provider)

        remove_duplicates_from_last_search_table()

    class LastUpdate(CacheDBBase):
        __tablename__ = 'last_update'

        provider = Column(String(32), primary_key=True)
        time = Column(Integer)

    class LastSearch(CacheDBBase):
        __tablename__ = 'last_search'

        provider = Column(String(32), primary_key=True)
        time = Column(Integer)

    class SceneException(CacheDBBase):
        __tablename__ = 'scene_exceptions'

        id = Column(Integer, primary_key=True)
        indexer_id = Column(Integer)
        show_name = Column(Text)
        season = Column(Integer)

    class SceneName(CacheDBBase):
        __tablename__ = 'scene_names'

        id = Column(Integer, primary_key=True)
        indexer_id = Column(Integer)
        name = Column(Text)

    class NetworkTimezone(CacheDBBase):
        __tablename__ = 'network_timezones'

        network_name = Column(String(256), primary_key=True)
        timezone = Column(Text)

    class SceneExceptionRefresh(CacheDBBase):
        __tablename__ = 'scene_exceptions_refresh'

        exception_list = Column(String(32), primary_key=True)
        last_refreshed = Column(Integer)

    class Provider(CacheDBBase):
        __tablename__ = 'providers'

        id = Column(Integer, primary_key=True)
        provider = Column(Text)
        name = Column(Text)
        season = Column(Integer)
        episodes = Column(Text)
        series_id = Column(Integer)
        url = Column(String(256), index=True, unique=True)
        time = Column(Integer)
        quality = Column(Integer)
        release_group = Column(Text)
        version = Column(Integer, default=-1)
        seeders = Column(Integer)
        leechers = Column(Integer)
        size = Column(Integer)

    class QuickSearchShow(CacheDBBase):
        __tablename__ = 'quicksearch_shows'

        category = Column(Text)
        showid = Column(Integer, index=True, primary_key=True)
        seasons = Column(Integer)
        name = Column(Text)
        img = Column(Text)

    class QuickSearchEpisode(CacheDBBase):
        __tablename__ = 'quicksearch_episodes'

        category = Column(Text)
        showid = Column(Integer, index=True, primary_key=True)
        episodeid = Column(Integer)
        season = Column(Integer, index=True, primary_key=True)
        episode = Column(Integer, index=True, primary_key=True)
        name = Column(Text)
        showname = Column(Text)
        img = Column(Text)
