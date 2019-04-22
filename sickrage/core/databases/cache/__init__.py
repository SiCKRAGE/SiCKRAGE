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

from sqlalchemy import Column, Integer, Text
from sqlalchemy.ext.declarative import as_declarative

from sickrage.core.databases import srDatabase


@as_declarative()
class CacheDBBase(object):
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class CacheDB(srDatabase):
    def __init__(self, name='cache'):
        super(CacheDB, self).__init__(name)
        CacheDBBase.query = self.Session.query_property()
        CacheDBBase.metadata.create_all(self.engine)
        for model in CacheDBBase._decl_class_registry.values():
            if hasattr(model, '__tablename__'):
                self.tables[model.__tablename__] = model

    class LastUpdate(CacheDBBase):
        __tablename__ = 'last_update'

        provider = Column(Text, primary_key=True)
        time = Column(Integer)

    class LastSearch(CacheDBBase):
        __tablename__ = 'last_search'

        id = Column(Integer, primary_key=True)
        provider = Column(Text)
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

        network_name = Column(Text, primary_key=True)
        timezone = Column(Text)

    class SceneExceptionRefresh(CacheDBBase):
        __tablename__ = 'scene_exceptions_refresh'

        exception_list = Column(Text, primary_key=True)
        last_refreshed = Column(Integer)

    class Provider(CacheDBBase):
        __tablename__ = 'providers'

        id = Column(Integer, primary_key=True)
        provider = Column(Text)
        name = Column(Text)
        season = Column(Integer)
        episodes = Column(Text)
        indexerid = Column(Integer)
        url = Column(Text, index=True, unique=True)
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
