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

from sqlalchemy import Column, Integer, Text, ForeignKeyConstraint, String, DateTime, Boolean, Index, Date, BigInteger, func, literal_column
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.orm import relationship

import sickrage
from sickrage.core import common
from sickrage.core.common import SearchFormats
from sickrage.core.databases import SRDatabase, SRDatabaseBase


@as_declarative()
class MainDBBase(SRDatabaseBase):
    pass


class MainDB(SRDatabase):
    def __init__(self, db_type, db_prefix, db_host, db_port, db_username, db_password):
        super(MainDB, self).__init__('main', db_type, db_prefix, db_host, db_port, db_username, db_password)
        MainDBBase.metadata.create_all(self.engine)
        for model in MainDBBase._decl_class_registry.values():
            if hasattr(model, '__tablename__'):
                self.tables[model.__tablename__] = model

    def cleanup(self):
        def remove_duplicate_shows():
            session = self.session()

            # count by indexer ID
            duplicates = session.query(
                self.TVShow.indexer_id,
                func.count(self.TVShow.indexer_id).label('count')
            ).group_by(
                self.TVShow.indexer_id
            ).having(literal_column('count') > 1).all()

            for cur_duplicate in duplicates:
                sickrage.app.log.debug("Duplicate show detected! indexer_id: {dupe_id} count: {dupe_count}".format(dupe_id=cur_duplicate.indexer_id,
                                                                                                                   dupe_count=cur_duplicate.count))

                for result in session.query(self.TVShow).filter_by(indexer_id=cur_duplicate.indexer_id).limit(cur_duplicate.count - 1):
                    session.query(self.TVShow).filter_by(indexer_id=result.indexer_id).delete()
                    session.commit()

        def remove_duplicate_episodes():
            session = self.session()

            # count by show ID
            duplicates = session.query(
                self.TVEpisode.showid,
                self.TVEpisode.season,
                self.TVEpisode.episode,
                func.count(self.TVEpisode.showid).label('count')
            ).group_by(
                self.TVEpisode.showid,
                self.TVEpisode.season,
                self.TVEpisode.episode
            ).having(literal_column('count') > 1).all()

            # count by indexer ID
            duplicates += session.query(
                self.TVEpisode.showid,
                self.TVEpisode.season,
                self.TVEpisode.episode,
                func.count(self.TVEpisode.indexer_id).label('count')
            ).group_by(
                self.TVEpisode.showid,
                self.TVEpisode.season,
                self.TVEpisode.episode
            ).having(literal_column('count') > 1).all()

            for cur_duplicate in duplicates:
                sickrage.app.log.debug("Duplicate episode detected! "
                                       "showid: {dupe_id} "
                                       "season: {dupe_season} "
                                       "episode {dupe_episode} count: {dupe_count}".format(dupe_id=cur_duplicate.showid,
                                                                                           dupe_season=cur_duplicate.season,
                                                                                           dupe_episode=cur_duplicate.episode,
                                                                                           dupe_count=cur_duplicate.count))

                for result in session.query(self.TVEpisode).filter_by(showid=cur_duplicate.showid,
                                                                      season=cur_duplicate.season,
                                                                      episode=cur_duplicate.episode).limit(cur_duplicate.count - 1):
                    session.query(self.TVEpisode).filter_by(indexer_id=result.indexer_id).delete()
                    session.commit()

        def fix_duplicate_episode_scene_numbering():
            session = self.session()

            duplicates = session.query(
                self.TVEpisode.showid,
                self.TVEpisode.scene_season,
                self.TVEpisode.scene_episode,
                func.count(self.TVEpisode.showid).label('count')
            ).group_by(
                self.TVEpisode.showid,
                self.TVEpisode.scene_season,
                self.TVEpisode.scene_episode
            ).filter(
                self.TVEpisode.scene_season != -1,
                self.TVEpisode.scene_episode != -1
            ).having(literal_column('count') > 1)

            for cur_duplicate in duplicates:
                sickrage.app.log.debug("Duplicate episode scene numbering detected! "
                                       "showid: {dupe_id} "
                                       "scene season: {dupe_scene_season} "
                                       "scene episode {dupe_scene_episode} count: {dupe_count}".format(dupe_id=cur_duplicate.showid,
                                                                                                       dupe_scene_season=cur_duplicate.scene_season,
                                                                                                       dupe_scene_episode=cur_duplicate.scene_episode,
                                                                                                       dupe_count=cur_duplicate.count))

                for result in session.query(self.TVEpisode).filter_by(showid=cur_duplicate.showid,
                                                                      scene_season=cur_duplicate.scene_season,
                                                                      scene_episode=cur_duplicate.scene_episode).limit(cur_duplicate.count - 1):
                    result.scene_season = -1
                    result.scene_episode = -1
                    session.commit()

        def fix_duplicate_episode_scene_absolute_numbering():
            session = self.session()

            duplicates = session.query(
                self.TVEpisode.showid,
                self.TVEpisode.scene_absolute_number,
                func.count(self.TVEpisode.showid).label('count')
            ).group_by(
                self.TVEpisode.showid,
                self.TVEpisode.scene_absolute_number
            ).filter(
                self.TVEpisode.scene_absolute_number != -1
            ).having(literal_column('count') > 1)

            for cur_duplicate in duplicates:
                sickrage.app.log.debug("Duplicate episode scene absolute numbering detected! "
                                       "showid: {dupe_id} "
                                       "scene absolute number: {dupe_scene_absolute_number} "
                                       "count: {dupe_count}".format(dupe_id=cur_duplicate.showid,
                                                                    dupe_scene_absolute_number=cur_duplicate.scene_absolute_number,
                                                                    dupe_count=cur_duplicate.count))

                for result in session.query(self.TVEpisode).filter_by(showid=cur_duplicate.showid,
                                                                      scene_absolute_number=cur_duplicate.scene_absolute_number).\
                        limit(cur_duplicate.count - 1):
                    result.scene_absolute_number = -1
                    session.commit()

        def remove_invalid_episodes():
            session = self.session()

            session.query(self.TVEpisode).filter_by(indexer_id=0).delete()
            session.commit()

        def fix_invalid_scene_numbering():
            session = self.session()

            session.query(self.TVEpisode).filter_by(scene_season=0, scene_episode=0).update({
                self.TVEpisode.scene_season: -1,
                self.TVEpisode.scene_episode: -1
            })

            session.commit()

            session.query(self.TVEpisode).filter_by(scene_absolute_number=0).update({
                self.TVEpisode.scene_absolute_number: -1
            })

            session.commit()

            session.query(self.TVEpisode).filter(self.TVEpisode.season == self.TVEpisode.scene_season,
                                                 self.TVEpisode.episode == self.TVEpisode.scene_episode).update({
                self.TVEpisode.scene_season: -1,
                self.TVEpisode.scene_episode: -1
            })

            session.commit()

            session.query(self.TVEpisode).filter(self.TVEpisode.absolute_number == self.TVEpisode.scene_absolute_number).update({
                self.TVEpisode.scene_absolute_number: -1
            })

            session.commit()

        def fix_tvshow_table_columns():
            session = self.session()

            session.query(self.TVShow).filter_by(sub_use_sr_metadata=None).update({'sub_use_sr_metadata': False})
            session.query(self.TVShow).filter_by(skip_downloaded=None).update({'skip_downloaded': False})
            session.query(self.TVShow).filter_by(dvdorder=None).update({'dvdorder': False})
            session.query(self.TVShow).filter_by(subtitles=None).update({'subtitles': False})
            session.query(self.TVShow).filter_by(anime=None).update({'anime': False})
            session.query(self.TVShow).filter_by(flatten_folders=None).update({'flatten_folders': False})
            session.query(self.TVShow).filter_by(paused=None).update({'paused': False})

            session.commit()

        remove_duplicate_shows()
        remove_duplicate_episodes()
        remove_invalid_episodes()
        fix_invalid_scene_numbering()
        fix_duplicate_episode_scene_numbering()
        fix_duplicate_episode_scene_absolute_numbering()
        fix_tvshow_table_columns()

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
        flatten_folders = Column(Boolean, nullable=False, default=0)
        paused = Column(Boolean, nullable=False, default=0)
        search_format = Column(Integer, default=SearchFormats.STANDARD)
        scene = Column(Boolean, nullable=False, default=0)
        anime = Column(Boolean, nullable=False, default=0)
        subtitles = Column(Boolean, nullable=False, default=0)
        dvdorder = Column(Boolean, nullable=False, default=0)
        skip_downloaded = Column(Boolean, nullable=False, default=0)
        startyear = Column(Integer, default=0)
        lang = Column(Text, default='')
        imdb_id = Column(Text, default='')
        rls_ignore_words = Column(Text, default='')
        rls_require_words = Column(Text, default='')
        default_ep_status = Column(Integer, default=common.SKIPPED)
        sub_use_sr_metadata = Column(Boolean, nullable=False, default=0)
        notify_list = Column(Text, default='')
        search_delay = Column(Integer, default=0)
        scene_exceptions = Column(Text, default='')
        last_refresh = Column(Integer, default=datetime.datetime.now().toordinal())
        last_xem_refresh = Column(Integer, default=datetime.datetime.now().toordinal())
        last_scene_exceptions_refresh = Column(Integer, default=datetime.datetime.now().toordinal())
        last_update = Column(Integer, default=datetime.datetime.now().toordinal())
        last_backlog_search = Column(Integer, default=0)
        last_proper_search = Column(Integer, default=0)

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
        absolute_number = Column(Integer, default=-1)
        scene_season = Column(Integer, default=-1)
        scene_episode = Column(Integer, default=-1)
        scene_absolute_number = Column(Integer, default=-1)
        xem_season = Column(Integer, default=-1)
        xem_episode = Column(Integer, default=-1)
        xem_absolute_number = Column(Integer, default=-1)
        name = Column(Text, default='')
        description = Column(Text, default='')
        subtitles = Column(Text, default='')
        subtitles_searchcount = Column(Integer, default=0)
        subtitles_lastsearch = Column(Integer, default=0)
        airdate = Column(Date, default=datetime.datetime.min)
        hasnfo = Column(Boolean, nullable=False, default=False)
        hastbn = Column(Boolean, nullable=False, default=False)
        status = Column(Integer, default=common.UNKNOWN)
        location = Column(Text, default='')
        file_size = Column(BigInteger, default=0)
        release_name = Column(Text, default='')
        is_proper = Column(Boolean, nullable=False, default=False)
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
