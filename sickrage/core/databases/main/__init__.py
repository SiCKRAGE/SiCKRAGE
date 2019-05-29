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

from sqlalchemy import Column, Integer, Text, ForeignKeyConstraint, String, DateTime
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.orm import sessionmaker, scoped_session

from sickrage.core.databases import SRDatabase, ContextSession


@as_declarative()
class MainDBBase(object):
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def update(self, **kwargs):
        primary_keys = [pk.name for pk in self.__table__.primary_key]
        for key, value in kwargs.items():
            if key not in primary_keys:
                setattr(self, key, value)


class MainDB(SRDatabase):
    db_version = 10

    session = sessionmaker(class_=ContextSession)

    def __init__(self, db_type, db_prefix, db_host, db_port, db_username, db_password):
        super(MainDB, self).__init__('main', db_type, db_prefix, db_host, db_port, db_username, db_password)
        MainDB.session.configure(bind=self.engine)
        MainDBBase.metadata.create_all(self.engine)
        for model in MainDBBase._decl_class_registry.values():
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
            _Session = functools.partial(MainDB.session, expire_on_commit=False)
            return decorator(args[0])
        else:
            # Arguments were specified, turn them into arguments for Session creation e.g. @with_session(autocommit=True)
            _Session = functools.partial(MainDB.session, *args, **kwargs)
            return decorator

    class IMDbInfo(MainDBBase):
        __tablename__ = 'imdb_info'
        __table_args__ = (
            ForeignKeyConstraint(['indexer_id'], ['tv_shows.indexer_id']),
        )

        indexer_id = Column(Integer, primary_key=True)
        imdb_id = Column(String(10), index=True, unique=True)
        rated = Column(Text)
        title = Column(Text)
        production = Column(Text)
        website = Column(Text)
        writer = Column(Text)
        actors = Column(Text)
        type = Column(Text)
        votes = Column(Text, nullable=False)
        seasons = Column(Text)
        poster = Column(Text)
        director = Column(Text)
        released = Column(Text)
        awards = Column(Text)
        genre = Column(Text, nullable=False)
        rating = Column(Text, nullable=False)
        language = Column(Text)
        country = Column(Text)
        runtime = Column(Text)
        metascore = Column(Text)
        year = Column(Text)
        plot = Column(Text)
        last_update = Column(Integer, nullable=False)

    class XEMRefresh(MainDBBase):
        __tablename__ = 'xem_refresh'

        indexer_id = Column(Integer, primary_key=True)
        indexer = Column(Integer, primary_key=True)
        last_refreshed = Column(Integer, nullable=False)

    class SceneNumbering(MainDBBase):
        __tablename__ = 'scene_numbering'

        indexer = Column(Integer, primary_key=True)
        indexer_id = Column(Integer, primary_key=True)
        season = Column(Integer, primary_key=True)
        episode = Column(Integer, primary_key=True)
        scene_season = Column(Integer, nullable=False)
        scene_episode = Column(Integer, nullable=False)
        absolute_number = Column(Integer, nullable=False)
        scene_absolute_number = Column(Integer, nullable=False)

    class IndexerMapping(MainDBBase):
        __tablename__ = 'indexer_mapping'

        indexer_id = Column(Integer, primary_key=True)
        indexer = Column(Integer, primary_key=True)
        mindexer_id = Column(Integer, nullable=False)
        mindexer = Column(Integer, primary_key=True)

    class Blacklist(MainDBBase):
        __tablename__ = 'blacklist'

        id = Column(Integer, primary_key=True)
        show_id = Column(Integer, nullable=False)
        keyword = Column(Text, nullable=False)

    class Whitelist(MainDBBase):
        __tablename__ = 'whitelist'

        id = Column(Integer, primary_key=True)
        show_id = Column(Integer, nullable=False)
        keyword = Column(Text, nullable=False)

    class History(MainDBBase):
        __tablename__ = 'history'

        id = Column(Integer, primary_key=True)
        showid = Column(Integer, nullable=False)
        season = Column(Integer, nullable=False)
        episode = Column(Integer, nullable=False)
        resource = Column(Text, nullable=False)
        action = Column(Integer, nullable=False)
        version = Column(Integer, default=-1)
        provider = Column(Text, nullable=False)
        date = Column(DateTime, nullable=False)
        quality = Column(Integer, nullable=False)
        release_group = Column(Text, nullable=False)

    class FailedSnatchHistory(MainDBBase):
        __tablename__ = 'failed_snatch_history'

        id = Column(Integer, primary_key=True)
        date = Column(DateTime, nullable=False)
        size = Column(Integer, nullable=False)
        release = Column(Text, nullable=False)
        provider = Column(Text, nullable=False)
        showid = Column(Integer, nullable=False)
        season = Column(Integer, nullable=False)
        episode = Column(Integer, nullable=False)
        old_status = Column(Integer, nullable=False)

    class FailedSnatch(MainDBBase):
        __tablename__ = 'failed_snatches'

        id = Column(Integer, primary_key=True)
        release = Column(Text, nullable=False)
        size = Column(Integer, nullable=False)
        provider = Column(Text, nullable=False)
