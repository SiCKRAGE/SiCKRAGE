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

from sqlalchemy import Column, Integer, Text, String, Boolean
from sqlalchemy.ext.declarative import as_declarative

from sickrage.core.databases import SRDatabase, SRDatabaseBase


@as_declarative()
class CacheDBBase(SRDatabaseBase):
    pass


class CacheDB(SRDatabase):
    def __init__(self, db_type, db_prefix, db_host, db_port, db_username, db_password):
        super(CacheDB, self).__init__('cache', db_type, db_prefix, db_host, db_port, db_username, db_password)
        CacheDBBase.metadata.create_all(self.engine)
        for model in CacheDBBase._decl_class_registry.values():
            if hasattr(model, '__tablename__'):
                self.tables[model.__tablename__] = model

    def cleanup(self):
        def remove_duplicates_from_last_search_table():
            found = []

            session = self.session()

            for x in session.query(CacheDB.LastSearch).all():
                if x.provider in found:
                    x.delete()
                    session.commit()
                else:
                    found.append(x.provider)

        def remove_duplicates_from_scene_name_table():
            found = []

            session = self.session()

            for x in session.query(CacheDB.SceneName).all():
                if (x.indexer_id, x.name) in found:
                    x.delete()
                    session.commit()
                else:
                    found.append((x.indexer_id, x.name))

        remove_duplicates_from_last_search_table()
        # remove_duplicates_from_scene_name_table()

    class LastUpdate(CacheDBBase):
        __tablename__ = 'last_update'

        provider = Column(String(32), primary_key=True)
        time = Column(Integer)

    class LastSearch(CacheDBBase):
        __tablename__ = 'last_search'

        provider = Column(String(32), primary_key=True)
        time = Column(Integer)

    class SceneName(CacheDBBase):
        __tablename__ = 'scene_names'

        id = Column(Integer, primary_key=True)
        indexer_id = Column(Integer)
        name = Column(Text)

    class NetworkTimezone(CacheDBBase):
        __tablename__ = 'network_timezones'

        network_name = Column(String(256), primary_key=True)
        timezone = Column(Text)

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

    class OAuth2Token(CacheDBBase):
        __tablename__ = 'oauth2_token'

        id = Column(Integer, primary_key=True)
        access_token = Column(String(255), unique=True, nullable=False)
        refresh_token = Column(String(255), index=True)
        expires_in = Column(Integer, nullable=False, default=0)
        expires_at = Column(Integer, nullable=False, default=0)
        scope = Column(Text, default="")
        session_state = Column(Text, default="")
        token_type = Column(Text, default="bearer")

    class Announcements(CacheDBBase):
        __tablename__ = 'announcements'

        id = Column(Integer, primary_key=True)
        hash = Column(String(255), unique=True, nullable=False)
        seen = Column(Boolean, default=False)
