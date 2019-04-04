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

from sickrage.core.databases import srDatabase, BaseActions


@as_declarative()
class CacheDBBase(object):
    pass


class CacheDB(srDatabase):
    _version = 1

    def __init__(self, name='cache'):
        super(CacheDB, self).__init__(name)
        CacheDBBase.engine = self.engine
        CacheDBBase.query = self.Session.query_property()
        CacheDBBase.metadata.create_all(self.engine)
        for model in CacheDBBase._decl_class_registry.values():
            if hasattr(model, '__tablename__'):
                self.tables[model.__tablename__] = model

    class LastUpdate(BaseActions, CacheDBBase):
        __tablename__ = 'last_update'

        provider = Column(Text, primary_key=True)
        time = Column(Integer)

    class LastSearch(BaseActions, CacheDBBase):
        __tablename__ = 'last_search'

        id = Column(Integer, primary_key=True)
        provider = Column(Text)
        time = Column(Integer)

    class SceneException(BaseActions, CacheDBBase):
        __tablename__ = 'scene_exceptions'

        id = Column(Integer, primary_key=True)
        indexer_id = Column(Integer)
        show_name = Column(Text)
        season = Column(Integer)

    class SceneName(BaseActions, CacheDBBase):
        __tablename__ = 'scene_names'

        id = Column(Integer, primary_key=True)
        indexer_id = Column(Integer)
        name = Column(Text)

    class NetworkTimezone(BaseActions, CacheDBBase):
        __tablename__ = 'network_timezones'

        network_name = Column(Text, primary_key=True)
        timezone = Column(Text)

    class SceneExceptionRefresh(BaseActions, CacheDBBase):
        __tablename__ = 'scene_exceptions_refresh'

        exception_list = Column(Text, primary_key=True)
        last_refreshed = Column(Integer)

    class Provider(BaseActions, CacheDBBase):
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

    class QuickSearchShow(BaseActions, CacheDBBase):
        __tablename__ = 'quicksearch_shows'

        category = Column(Text)
        showid = Column(Integer, primary_key=True)
        seasons = Column(Integer)
        name = Column(Text)
        img = Column(Text)

    class QuickSearchEpisode(BaseActions, CacheDBBase):
        __tablename__ = 'quicksearch_episodes'

        category = Column(Text)
        showid = Column(Integer, primary_key=True)
        episodeid = Column(Integer, primary_key=True)
        season = Column(Integer)
        episode = Column(Integer)
        name = Column(Text)
        showname = Column(Text)
        img = Column(Text)
