# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from sqlalchemy import Column, Integer, Text, Boolean, Index, ForeignKeyConstraint, orm
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.orm import relationship

import sickrage
from sickrage.core.databases import srDatabase, BaseActions


@as_declarative()
class MainDBBase(object): pass


class MainDB(srDatabase):
    _version = 1

    def __init__(self, name='main'):
        super(MainDB, self).__init__(name)
        MainDBBase.engine = self.engine
        MainDBBase.metadata.create_all(self.engine)
        for model in MainDBBase._decl_class_registry.values():
            if hasattr(model, '__tablename__'):
                self.tables[model.__tablename__] = model

    @property
    def version(self):
        try:
            dbData = MainDB.Version.query().one()
        except orm.exc.NoResultFound:
            MainDB.Version.add(**{'database_version': 1})
            dbData = MainDB.Version.query().one()

        return dbData.database_version

    def upgrade(self):
        current_version = self.version

        while current_version < self._version:
            dbData = MainDB.Version.query().one()
            new_version = current_version + 1
            dbData.database_version = new_version

            upgrade_func = getattr(self, '_upgrade_v' + str(new_version), None)
            if upgrade_func:
                sickrage.app.log.info("Upgrading main database to version {}".format(new_version))
                upgrade_func()

            MainDB.Version.update(**dbData.as_dict())
            current_version = new_version

    class Version(BaseActions, MainDBBase):
        __tablename__ = 'version'

        database_version = Column(Integer, primary_key=True)

    class TVShow(BaseActions, MainDBBase):
        __tablename__ = 'tv_shows'

        indexer_id = Column(Integer, index=True, primary_key=True)
        indexer = Column(Integer, index=True, primary_key=True)
        show_name = Column(Text)
        location = Column(Text)
        network = Column(Text)
        genre = Column(Text)
        overview = Column(Text)
        classification = Column(Text)
        runtime = Column(Integer)
        quality = Column(Integer)
        airs = Column(Text)
        status = Column(Integer)
        flatten_folders = Column(Boolean)
        paused = Column(Boolean)
        air_by_date = Column(Boolean)
        anime = Column(Boolean)
        scene = Column(Boolean)
        sports = Column(Boolean)
        subtitles = Column(Boolean)
        dvdorder = Column(Boolean)
        skip_downloaded = Column(Boolean)
        startyear = Column(Integer)
        lang = Column(Text)
        imdb_id = Column(Text)
        rls_ignore_words = Column(Text)
        rls_require_words = Column(Text)
        default_ep_status = Column(Integer, default=-1)
        sub_use_sr_metadata = Column(Boolean)
        notify_list = Column(Text)
        search_delay = Column(Boolean)
        last_update = Column(Integer)
        last_refresh = Column(Integer)

        episodes = relationship('TVEpisode', back_populates='show', lazy='select')

    class TVEpisode(BaseActions, MainDBBase):
        __tablename__ = 'tv_episodes'
        __table_args__ = (
            ForeignKeyConstraint(['showid', 'indexer'], ['tv_shows.indexer_id', 'tv_shows.indexer']),
            Index('idx_showid_indexer', 'showid', 'indexer'),
            Index('idx_sta_epi_air', 'status', 'episode', 'airdate'),
            Index('idx_sta_epi_sta_air', 'season', 'episode', 'status', 'airdate'),
            Index('idx_status ', 'status', 'season', 'episode', 'airdate'),
            Index('idx_tv_episodes_showid_airdate', 'indexerid', 'airdate'),
        )

        showid = Column(Integer, index=True, primary_key=True)
        indexerid = Column(Integer, index=True, primary_key=True)
        indexer = Column(Integer, index=True, primary_key=True)
        season = Column(Integer)
        episode = Column(Integer)
        scene_season = Column(Integer)
        scene_episode = Column(Integer)
        name = Column(Text)
        description = Column(Text)
        subtitles = Column(Text)
        subtitles_searchcount = Column(Integer)
        subtitles_lastsearch = Column(Integer)
        airdate = Column(Integer)
        hasnfo = Column(Boolean)
        hastbn = Column(Boolean)
        status = Column(Integer)
        location = Column(Text)
        file_size = Column(Integer)
        release_name = Column(Text)
        is_proper = Column(Boolean)
        absolute_number = Column(Integer)
        scene_absolute_number = Column(Integer)
        version = Column(Integer, default=-1)
        release_group = Column(Text)

        show = relationship('TVShow', back_populates='episodes', lazy='select')

    class IMDbInfo(BaseActions, MainDBBase):
        __tablename__ = 'imdb_info'

        indexer_id = Column(Integer, primary_key=True)
        Rated = Column(Text)
        Title = Column(Text)
        DVD = Column(Text)
        Production = Column(Text)
        Website = Column(Text)
        Writer = Column(Text)
        Actors = Column(Text)
        Type = Column(Text)
        imdbVotes = Column(Text)
        totalSeasons = Column(Integer)
        Poster = Column(Text)
        Director = Column(Text)
        Released = Column(Text)
        Awards = Column(Text)
        Genre = Column(Text)
        imdbRating = Column(Text)
        Language = Column(Text)
        Country = Column(Text)
        Runtime = Column(Text)
        imdbID = Column(Text, index=True, unique=True)
        Metascore = Column(Text)
        Year = Column(Integer)
        Plot = Column(Text)
        last_update = Column(Integer)

    class XEMRefresh(BaseActions, MainDBBase):
        __tablename__ = 'xem_refresh'

        indexer_id = Column(Integer, primary_key=True)
        indexer = Column(Integer, primary_key=True)
        last_refreshed = Column(Integer)

    class SceneNumbering(BaseActions, MainDBBase):
        __tablename__ = 'scene_numbering'

        indexer = Column(Integer, primary_key=True)
        indexer_id = Column(Integer, primary_key=True)
        season = Column(Integer, primary_key=True)
        episode = Column(Integer, primary_key=True)
        scene_season = Column(Integer)
        scene_episode = Column(Integer)
        absolute_number = Column(Integer)
        scene_absolute_number = Column(Integer)

    class IndexerMapping(BaseActions, MainDBBase):
        __tablename__ = 'indexer_mapping'

        indexer_id = Column(Integer, primary_key=True)
        indexer = Column(Integer, primary_key=True)
        mindexer_id = Column(Integer)
        mindexer = Column(Integer, primary_key=True)

    class Blacklist(BaseActions, MainDBBase):
        __tablename__ = 'blacklist'

        id = Column(Integer, primary_key=True)
        show_id = Column(Integer)
        keyword = Column(Text)

    class Whitelist(BaseActions, MainDBBase):
        __tablename__ = 'whitelist'

        id = Column(Integer, primary_key=True)
        show_id = Column(Integer)
        keyword = Column(Text)

    class History(BaseActions, MainDBBase):
        __tablename__ = 'history'

        id = Column(Integer, primary_key=True)
        showid = Column(Integer)
        resource = Column(Text)
        season = Column(Integer)
        episode = Column(Integer)
        action = Column(Integer)
        version = Column(Integer, default=-1)
        provider = Column(Text)
        date = Column(Integer)
        quality = Column(Integer)

    class FailedSnatchHistory(BaseActions, MainDBBase):
        __tablename__ = 'failed_snatch_history'

        id = Column(Integer, primary_key=True)
        date = Column(Integer)
        size = Column(Integer)
        release = Column(Text)
        provider = Column(Text)
        showid = Column(Integer)
        season = Column(Integer)
        episode = Column(Integer)
        old_status = Column(Integer)

    class FailedSnatch(BaseActions, MainDBBase):
        __tablename__ = 'failed_snatches'

        id = Column(Integer, primary_key=True)
        release = Column(Text)
        size = Column(Integer)
        provider = Column(Text)
