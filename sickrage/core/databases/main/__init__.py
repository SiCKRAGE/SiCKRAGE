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
import datetime

from sqlalchemy import Column, Integer, Text, ForeignKeyConstraint, String, DateTime, Boolean, Index, Date, BigInteger
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.orm import relationship

from sickrage.core import common
from sickrage.core.databases import SRDatabase, SRDatabaseBase


@as_declarative()
class MainDBBase(SRDatabaseBase):
    pass

class MainDB(SRDatabase):
    def __init__(self, db_type, db_prefix, db_host, db_port, db_username, db_password):
        super(MainDB, self).__init__('main', 10, db_type, db_prefix, db_host, db_port, db_username, db_password)
        MainDBBase.metadata.create_all(self.engine)
        for model in MainDBBase._decl_class_registry.values():
            if hasattr(model, '__tablename__'):
                self.tables[model.__tablename__] = model

    class TVShow(MainDBBase):
        __tablename__ = 'tv_shows'

        indexer_id = Column(Integer, index=True, primary_key=True)
        indexer = Column(Integer, index=True, primary_key=True)
        name = Column(Text, default='')
        location = Column(Text, default='')
        network = Column(Text, default='')
        genre = Column(Text, default='')
        overview = Column(Text, default='')
        classification = Column(Text, default='Scripted')
        runtime = Column(Integer, default=0)
        quality = Column(Integer, default=-1)
        airs = Column(Text, default='')
        status = Column(Text, default='')
        flatten_folders = Column(Boolean, default=0)
        paused = Column(Boolean, default=0)
        air_by_date = Column(Boolean, default=0)
        anime = Column(Boolean, default=0)
        scene = Column(Boolean, default=0)
        sports = Column(Boolean, default=0)
        subtitles = Column(Boolean, default=0)
        dvdorder = Column(Boolean, default=0)
        skip_downloaded = Column(Boolean, default=0)
        startyear = Column(Integer, default=0)
        lang = Column(Text, default='')
        imdb_id = Column(Text, default='')
        rls_ignore_words = Column(Text, default='')
        rls_require_words = Column(Text, default='')
        default_ep_status = Column(Integer, default=common.SKIPPED)
        sub_use_sr_metadata = Column(Boolean, default=0)
        notify_list = Column(Text, default='')
        search_delay = Column(Integer, default=0)
        last_update = Column(Integer, default=datetime.datetime.now().toordinal())
        last_refresh = Column(Integer, default=datetime.datetime.now().toordinal())
        last_backlog_search = Column(Integer, default=datetime.datetime.now().toordinal())
        last_proper_search = Column(Integer, default=datetime.datetime.now().toordinal())

        episodes = relationship('TVEpisode', uselist=True, backref='tv_shows', lazy='dynamic')
        imdb_info = relationship('IMDbInfo', uselist=False, backref='tv_shows')

    class TVEpisode(MainDBBase):
        __tablename__ = 'tv_episodes'
        __table_args__ = (
            ForeignKeyConstraint(['showid', 'indexer'], ['tv_shows.indexer_id', 'tv_shows.indexer']),
            Index('idx_showid_indexer', 'showid', 'indexer'),
            Index('idx_showid_indexerid', 'showid', 'indexer_id'),
            Index('idx_sta_epi_air', 'status', 'episode', 'airdate'),
            Index('idx_sea_epi_sta_air', 'season', 'episode', 'status', 'airdate'),
            Index('idx_indexer_id_airdate', 'indexer_id', 'airdate'),
        )

        showid = Column(Integer, index=True, primary_key=True)
        indexer_id = Column(Integer, default=0)
        indexer = Column(Integer, index=True, primary_key=True)
        season = Column(Integer, index=True, primary_key=True)
        episode = Column(Integer, index=True, primary_key=True)
        scene_season = Column(Integer, default=0)
        scene_episode = Column(Integer, default=0)
        name = Column(Text, default='')
        description = Column(Text, default='')
        subtitles = Column(Text, default='')
        subtitles_searchcount = Column(Integer, default=0)
        subtitles_lastsearch = Column(Integer, default=0)
        airdate = Column(Date, default=datetime.datetime.min)
        hasnfo = Column(Boolean, default=False)
        hastbn = Column(Boolean, default=False)
        status = Column(Integer, default=common.UNKNOWN)
        location = Column(Text, default='')
        file_size = Column(BigInteger, default=0)
        release_name = Column(Text, default='')
        is_proper = Column(Boolean, default=False)
        absolute_number = Column(Integer, default=0)
        scene_absolute_number = Column(Integer, default=0)
        version = Column(Integer, default=-1)
        release_group = Column(Text, default='')

        show = relationship('TVShow', uselist=False, backref='tv_episodes')

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
