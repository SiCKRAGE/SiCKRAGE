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

from sqlalchemy import Column, Integer, Text, ForeignKeyConstraint, String, DateTime, Boolean, Index, Date, BigInteger, func, literal_column, Enum, exists
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

import sickrage
from sickrage.core.common import Qualities, EpisodeStatus
from sickrage.core.databases import SRDatabase, SRDatabaseBase, IntFlag
from sickrage.core.enums import SearchFormat, SeriesProviderID


class MainDB(SRDatabase):
    base = declarative_base(cls=SRDatabaseBase)

    def __init__(self, db_type, db_prefix, db_host, db_port, db_username, db_password):
        super(MainDB, self).__init__('main', db_type, db_prefix, db_host, db_port, db_username, db_password)

    def initialize(self):
        self.base.metadata.create_all(self.engine)

    def cleanup(self):
        def remove_orphaned():
            session = self.session()

            # orphaned episode entries
            for orphaned_result in session.query(self.TVEpisode).filter(~exists().where(self.TVEpisode.series_id == self.TVShow.series_id)):
                sickrage.app.log.debug(f"Orphaned episode detected! episode_id: {orphaned_result.episode_id}")
                sickrage.app.log.info(f"Deleting orphaned episode with episode_id: {orphaned_result.episode_id}")
                session.delete(orphaned_result)
                session.commit()

            # orphaned imdb info entries
            for orphaned_result in session.query(self.IMDbInfo).filter(~exists().where(self.IMDbInfo.series_id == self.TVShow.series_id)):
                sickrage.app.log.debug(f"Orphaned imdb info detected! series_id: {orphaned_result.series_id}")
                sickrage.app.log.info(f"Deleting orphaned imdb info with series_id: {orphaned_result.series_id}")
                session.delete(orphaned_result)
                session.commit()

            # orphaned series provider mapping entries
            for orphaned_result in session.query(self.SeriesProviderMapping).filter(~exists().where(self.SeriesProviderMapping.series_id == self.TVShow.series_id)):
                sickrage.app.log.debug(f"Orphaned series provider mapper detected! series_id: {orphaned_result.series_id}")
                sickrage.app.log.info(f"Deleting orphaned series provider mapper with series_id: {orphaned_result.series_id}")
                session.delete(orphaned_result)
                session.commit()

            # orphaned whitelist entries
            for orphaned_result in session.query(self.Whitelist).filter(~exists().where(self.Whitelist.series_id == self.TVShow.series_id)):
                sickrage.app.log.debug(f"Orphaned whitelist detected! series_id: {orphaned_result.series_id}")
                sickrage.app.log.info(f"Deleting orphaned whitelist with series_id: {orphaned_result.series_id}")
                session.delete(orphaned_result)
                session.commit()

            # orphaned blacklist entries
            for orphaned_result in session.query(self.Blacklist).filter(~exists().where(self.Blacklist.series_id == self.TVShow.series_id)):
                sickrage.app.log.debug(f"Orphaned blacklist detected! series_id: {orphaned_result.series_id}")
                sickrage.app.log.info(f"Deleting orphaned blacklist with series_id: {orphaned_result.series_id}")
                session.delete(orphaned_result)
                session.commit()

            # orphaned history entries
            for orphaned_result in session.query(self.History).filter(~exists().where(self.History.series_id == self.TVShow.series_id)):
                sickrage.app.log.debug(f"Orphaned history detected! series_id: {orphaned_result.series_id}")
                sickrage.app.log.info(f"Deleting orphaned history with series_id: {orphaned_result.series_id}")
                session.delete(orphaned_result)
                session.commit()

            # orphaned failed snatch history entries
            for orphaned_result in session.query(self.FailedSnatchHistory).filter(~exists().where(self.FailedSnatchHistory.series_id == self.TVShow.series_id)):
                sickrage.app.log.debug(f"Orphaned failed snatch history detected! series_id: {orphaned_result.series_id}")
                sickrage.app.log.info(f"Deleting orphaned failed snatch history with series_id: {orphaned_result.series_id}")
                session.delete(orphaned_result)
                session.commit()

            # orphaned failed snatch entries
            for orphaned_result in session.query(self.FailedSnatch).filter(~exists().where(self.FailedSnatch.series_id == self.TVShow.series_id)):
                sickrage.app.log.debug(f"Orphaned failed snatch detected! series_id: {orphaned_result.series_id}")
                sickrage.app.log.info(f"Deleting orphaned failed snatch with series_id: {orphaned_result.series_id}")
                session.delete(orphaned_result)
                session.commit()

        def remove_duplicate_shows():
            session = self.session()

            # count by series id
            duplicates = session.query(
                self.TVShow.series_id,
                func.count(self.TVShow.series_id).label('count')
            ).group_by(
                self.TVShow.series_id
            ).having(literal_column('count') > 1).all()

            for cur_duplicate in duplicates:
                sickrage.app.log.debug("Duplicate show detected! series_id: {dupe_id} count: {dupe_count}".format(dupe_id=cur_duplicate.series_id,
                                                                                                                  dupe_count=cur_duplicate.count))

                for result in session.query(self.TVShow).filter_by(series_id=cur_duplicate.series_id).limit(cur_duplicate.count - 1):
                    session.query(self.TVShow).filter_by(series_id=result.series_id).delete()
                    session.commit()

        def remove_duplicate_episodes():
            session = self.session()

            # count by season/episode
            duplicates = session.query(
                self.TVEpisode.series_id,
                self.TVEpisode.season,
                self.TVEpisode.episode,
                func.count(self.TVEpisode.episode_id).label('count')
            ).group_by(
                self.TVEpisode.series_id,
                self.TVEpisode.season,
                self.TVEpisode.episode,
            ).having(literal_column('count') > 1).all()

            for cur_duplicate in duplicates:
                sickrage.app.log.debug("Duplicate episode detected! "
                                       "series_id: {dupe_id} "
                                       "season: {dupe_season} "
                                       "episode {dupe_episode} count: {dupe_count}".format(dupe_id=cur_duplicate.series_id,
                                                                                           dupe_season=cur_duplicate.season,
                                                                                           dupe_episode=cur_duplicate.episode,
                                                                                           dupe_count=cur_duplicate.count))

                for result in session.query(self.TVEpisode).filter_by(series_id=cur_duplicate.series_id,
                                                                      season=cur_duplicate.season,
                                                                      episode=cur_duplicate.episode).limit(cur_duplicate.count - 1):
                    session.query(self.TVEpisode).filter_by(series_id=result.series_id, season=result.season, episode=result.episode).delete()
                    session.commit()

            # count by series id
            duplicates = session.query(
                self.TVEpisode.series_id,
                self.TVEpisode.episode_id,
                self.TVEpisode.season,
                self.TVEpisode.episode,
                func.count(self.TVEpisode.episode_id).label('count')
            ).group_by(
                self.TVEpisode.series_id,
                self.TVEpisode.episode_id
            ).having(literal_column('count') > 1).all()

            for cur_duplicate in duplicates:
                sickrage.app.log.debug("Duplicate episode detected! "
                                       "series_id: {dupe_id} "
                                       "season: {dupe_season} "
                                       "episode {dupe_episode} count: {dupe_count}".format(dupe_id=cur_duplicate.series_id,
                                                                                           dupe_season=cur_duplicate.season,
                                                                                           dupe_episode=cur_duplicate.episode,
                                                                                           dupe_count=cur_duplicate.count))

                for result in session.query(self.TVEpisode).filter_by(series_id=cur_duplicate.series_id,
                                                                      episode_id=cur_duplicate.episode_id).limit(cur_duplicate.count - 1):
                    session.query(self.TVEpisode).filter_by(series_id=result.series_id, episode_id=result.episode_id).delete()
                    session.commit()

        def fix_duplicate_episode_scene_numbering():
            session = self.session()

            duplicates = session.query(
                self.TVEpisode.series_id,
                self.TVEpisode.scene_season,
                self.TVEpisode.scene_episode,
                func.count(self.TVEpisode.series_id).label('count')
            ).group_by(
                self.TVEpisode.series_id,
                self.TVEpisode.scene_season,
                self.TVEpisode.scene_episode
            ).filter(
                self.TVEpisode.scene_season != -1,
                self.TVEpisode.scene_episode != -1
            ).having(literal_column('count') > 1)

            for cur_duplicate in duplicates:
                sickrage.app.log.debug("Duplicate episode scene numbering detected! "
                                       "series_id: {dupe_id} "
                                       "scene season: {dupe_scene_season} "
                                       "scene episode {dupe_scene_episode} count: {dupe_count}".format(dupe_id=cur_duplicate.series_id,
                                                                                                       dupe_scene_season=cur_duplicate.scene_season,
                                                                                                       dupe_scene_episode=cur_duplicate.scene_episode,
                                                                                                       dupe_count=cur_duplicate.count))

                for result in session.query(self.TVEpisode).filter_by(series_id=cur_duplicate.series_id,
                                                                      scene_season=cur_duplicate.scene_season,
                                                                      scene_episode=cur_duplicate.scene_episode).limit(cur_duplicate.count - 1):
                    result.scene_season = -1
                    result.scene_episode = -1
                    session.commit()

        def fix_duplicate_episode_scene_absolute_numbering():
            session = self.session()

            duplicates = session.query(
                self.TVEpisode.series_id,
                self.TVEpisode.scene_absolute_number,
                func.count(self.TVEpisode.series_id).label('count')
            ).group_by(
                self.TVEpisode.series_id,
                self.TVEpisode.scene_absolute_number
            ).filter(
                self.TVEpisode.scene_absolute_number != -1
            ).having(literal_column('count') > 1)

            for cur_duplicate in duplicates:
                sickrage.app.log.debug("Duplicate episode scene absolute numbering detected! "
                                       "series_id: {dupe_id} "
                                       "scene absolute number: {dupe_scene_absolute_number} "
                                       "count: {dupe_count}".format(dupe_id=cur_duplicate.series_id,
                                                                    dupe_scene_absolute_number=cur_duplicate.scene_absolute_number,
                                                                    dupe_count=cur_duplicate.count))

                for result in session.query(self.TVEpisode).filter_by(series_id=cur_duplicate.series_id,
                                                                      scene_absolute_number=cur_duplicate.scene_absolute_number). \
                        limit(cur_duplicate.count - 1):
                    result.scene_absolute_number = -1
                    session.commit()

        def remove_invalid_episodes():
            session = self.session()

            session.query(self.TVEpisode).filter_by(episode_id=0).delete()
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
            session.query(self.TVShow).filter_by(dvd_order=None).update({'dvd_order': False})
            session.query(self.TVShow).filter_by(subtitles=None).update({'subtitles': False})
            session.query(self.TVShow).filter_by(anime=None).update({'anime': False})
            session.query(self.TVShow).filter_by(flatten_folders=None).update({'flatten_folders': False})
            session.query(self.TVShow).filter_by(paused=None).update({'paused': False})
            session.query(self.TVShow).filter_by(last_xem_refresh=None).update({'last_xem_refresh': datetime.datetime.now()})

            session.commit()

        remove_orphaned()
        remove_duplicate_shows()
        remove_duplicate_episodes()
        remove_invalid_episodes()
        fix_invalid_scene_numbering()
        fix_duplicate_episode_scene_numbering()
        fix_duplicate_episode_scene_absolute_numbering()
        fix_tvshow_table_columns()

    class TVShow(base):
        __tablename__ = 'tv_shows'

        series_id = Column(Integer, index=True, primary_key=True)
        series_provider_id = Column(Enum(SeriesProviderID), index=True, primary_key=True)
        name = Column(Text, default='')
        location = Column(Text, default='')
        network = Column(Text, default='')
        genre = Column(Text, default='')
        overview = Column(Text, default='')
        classification = Column(Text, default='Scripted')
        runtime = Column(Integer, default=0)
        quality = Column(IntFlag(Qualities), default=Qualities.SD)
        airs = Column(Text, default='')
        status = Column(Text, default='')
        flatten_folders = Column(Boolean, nullable=False, default=0)
        paused = Column(Boolean, nullable=False, default=0)
        search_format = Column(Enum(SearchFormat), default=SearchFormat.STANDARD)
        scene = Column(Boolean, nullable=False, default=0)
        anime = Column(Boolean, nullable=False, default=0)
        subtitles = Column(Boolean, nullable=False, default=0)
        dvd_order = Column(Boolean, nullable=False, default=0)
        skip_downloaded = Column(Boolean, nullable=False, default=0)
        startyear = Column(Integer, default=0)
        lang = Column(Text, default='')
        imdb_id = Column(Text, default='')
        rls_ignore_words = Column(Text, default='')
        rls_require_words = Column(Text, default='')
        default_ep_status = Column(Enum(EpisodeStatus), default=EpisodeStatus.SKIPPED)
        sub_use_sr_metadata = Column(Boolean, nullable=False, default=0)
        notify_list = Column(Text, default='')
        search_delay = Column(Integer, default=0)
        scene_exceptions = Column(Text, default='')
        last_refresh = Column(DateTime(timezone=True), default=datetime.datetime.now())
        last_xem_refresh = Column(DateTime(timezone=True), default=datetime.datetime.now())
        last_scene_exceptions_refresh = Column(DateTime(timezone=True), default=datetime.datetime.now())
        last_update = Column(DateTime(timezone=True), default=datetime.datetime.now())
        last_backlog_search = Column(DateTime(timezone=True), default=datetime.datetime.now())
        last_proper_search = Column(DateTime(timezone=True), default=datetime.datetime.now())

        episodes = relationship('TVEpisode', uselist=True, backref='tv_shows', cascade="all, delete-orphan", lazy='dynamic')
        imdb_info = relationship('IMDbInfo', uselist=False, backref='tv_shows', cascade="all, delete-orphan")
        series_provider_mapping = relationship('SeriesProviderMapping', uselist=False, backref='tv_shows', cascade="all, delete-orphan")
        blacklist = relationship('Blacklist', uselist=False, backref='tv_shows', cascade="all, delete-orphan")
        whitelist = relationship('Whitelist', uselist=False, backref='tv_shows', cascade="all, delete-orphan")
        history = relationship('History', uselist=False, backref='tv_shows', cascade="all, delete-orphan")
        failed_snatch_history = relationship('FailedSnatchHistory', uselist=False, backref='tv_shows', cascade="all, delete-orphan")
        failed_snatches = relationship('FailedSnatch', uselist=False, backref='tv_shows', cascade="all, delete-orphan")

    class TVEpisode(base):
        __tablename__ = 'tv_episodes'
        __table_args__ = (
            ForeignKeyConstraint(['series_id', 'series_provider_id'], ['tv_shows.series_id', 'tv_shows.series_provider_id'], ondelete='CASCADE',
                                 name=f'fk_{__tablename__}_series_id_series_provider_id'),
            Index('idx_series_id_series_provider_id', 'series_id', 'series_provider_id'),
            Index('idx_series_id_episode_id', 'series_id', 'episode_id'),
            Index('idx_status_episode_airdate', 'status', 'episode', 'airdate'),
            Index('idx_season_episode_status_airdate', 'season', 'episode', 'status', 'airdate'),
            Index('idx_episode_id_airdate', 'episode_id', 'airdate'),
        )

        series_id = Column(Integer, index=True, primary_key=True)
        series_provider_id = Column(Enum(SeriesProviderID), index=True, primary_key=True)
        episode_id = Column(Integer, default=0)
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
        subtitles_lastsearch = Column(DateTime(timezone=True), default=func.current_timestamp())
        airdate = Column(Date, default=datetime.datetime.min)
        hasnfo = Column(Boolean, nullable=False, default=False)
        hastbn = Column(Boolean, nullable=False, default=False)
        status = Column(Enum(EpisodeStatus), default=EpisodeStatus.UNKNOWN)
        location = Column(Text, default='')
        file_size = Column(BigInteger, default=0)
        release_name = Column(Text, default='')
        is_proper = Column(Boolean, nullable=False, default=False)
        version = Column(Integer, default=-1)
        release_group = Column(Text, default='')

        show = relationship('TVShow', uselist=False, backref='tv_episodes')

    class IMDbInfo(base):
        __tablename__ = 'imdb_info'
        __table_args__ = (
            ForeignKeyConstraint(['series_id', 'imdb_id'], ['tv_shows.series_id', 'tv_shows.imdb_id'], ondelete='CASCADE',
                                 name=f'fk_{__tablename__}_series_id_imdb_id'),
        )

        series_id = Column(Integer, primary_key=True)
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
        last_update = Column(DateTime(timezone=True), default=datetime.datetime.now())

    class SeriesProviderMapping(base):
        __tablename__ = 'series_provider_mapping'
        __table_args__ = (
            ForeignKeyConstraint(['series_id', 'series_provider_id'], ['tv_shows.series_id', 'tv_shows.series_provider_id'], ondelete='CASCADE',
                                 name=f'fk_{__tablename__}_series_id_series_provider_id'),
        )

        series_id = Column(Integer, primary_key=True)
        series_provider_id = Column(Enum(SeriesProviderID), primary_key=True)
        mapped_series_id = Column(Integer, nullable=False)
        mapped_series_provider_id = Column(Enum(SeriesProviderID), primary_key=True)

    class Blacklist(base):
        __tablename__ = 'blacklist'
        __table_args__ = (
            ForeignKeyConstraint(['series_id', 'series_provider_id'], ['tv_shows.series_id', 'tv_shows.series_provider_id'], ondelete='CASCADE',
                                 name=f'fk_{__tablename__}_series_id_series_provider_id'),
        )

        id = Column(Integer, autoincrement=True, primary_key=True)
        series_id = Column(Integer, nullable=False)
        series_provider_id = Column(Enum(SeriesProviderID), nullable=False)
        keyword = Column(Text, nullable=False)

    class Whitelist(base):
        __tablename__ = 'whitelist'
        __table_args__ = (
            ForeignKeyConstraint(['series_id', 'series_provider_id'], ['tv_shows.series_id', 'tv_shows.series_provider_id'], ondelete='CASCADE',
                                 name=f'fk_{__tablename__}_series_id_series_provider_id'),
        )

        id = Column(Integer, autoincrement=True, primary_key=True)
        series_id = Column(Integer, nullable=False)
        series_provider_id = Column(Enum(SeriesProviderID), nullable=False)
        keyword = Column(Text, nullable=False)

    class History(base):
        __tablename__ = 'history'
        __table_args__ = (
            ForeignKeyConstraint(['series_id', 'series_provider_id'], ['tv_shows.series_id', 'tv_shows.series_provider_id'], ondelete='CASCADE',
                                 name=f'fk_{__tablename__}_series_id_series_provider_id'),
        )

        id = Column(Integer, autoincrement=True, primary_key=True)
        series_id = Column(Integer, nullable=False)
        series_provider_id = Column(Enum(SeriesProviderID), nullable=False)
        season = Column(Integer, nullable=False)
        episode = Column(Integer, nullable=False)
        resource = Column(Text, nullable=False, index=True)
        action = Column(Integer, nullable=False)
        version = Column(Integer, default=-1)
        provider = Column(Text, nullable=False)
        date = Column(DateTime, nullable=False)
        quality = Column(IntFlag(Qualities), nullable=False)
        release_group = Column(Text, nullable=False)

    class FailedSnatchHistory(base):
        __tablename__ = 'failed_snatch_history'
        __table_args__ = (
            ForeignKeyConstraint(['series_id', 'series_provider_id'], ['tv_shows.series_id', 'tv_shows.series_provider_id'], ondelete='CASCADE',
                                 name=f'fk_{__tablename__}_series_id_series_provider_id'),
        )

        id = Column(Integer, autoincrement=True, primary_key=True)
        series_id = Column(Integer, nullable=False)
        series_provider_id = Column(Enum(SeriesProviderID), nullable=False)
        date = Column(DateTime, nullable=False)
        size = Column(Integer, nullable=False)
        release = Column(Text, nullable=False, index=True)
        provider = Column(Text, nullable=False)
        season = Column(Integer, nullable=False)
        episode = Column(Integer, nullable=False)
        old_status = Column(Enum(EpisodeStatus), nullable=False)

    class FailedSnatch(base):
        __tablename__ = 'failed_snatches'
        __table_args__ = (
            ForeignKeyConstraint(['series_id', 'series_provider_id'], ['tv_shows.series_id', 'tv_shows.series_provider_id'], ondelete='CASCADE',
                                 name=f'fk_{__tablename__}_series_id_series_provider_id'),
        )

        id = Column(Integer, autoincrement=True, primary_key=True)
        series_id = Column(Integer, nullable=False)
        series_provider_id = Column(Enum(SeriesProviderID), nullable=False)
        release = Column(Text, nullable=False, index=True)
        size = Column(Integer, nullable=False)
        provider = Column(Text, nullable=False)
