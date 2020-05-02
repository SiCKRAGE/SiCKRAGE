import datetime

from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from sickrage.core import common
from sickrage.core.common import SearchFormats

Base = declarative_base()


def upgrade(migrate_engine):
    meta = MetaData(migrate_engine)

    tv_shows = Table('tv_shows', meta, autoload=True)

    if not hasattr(tv_shows.c, 'search_format'):
        search_format = Column('search_format', Integer, default=0)
        search_format.create(tv_shows)

        with migrate_engine.begin() as conn:
            for row in migrate_engine.execute(tv_shows.select()):
                if row.anime == 1 and not row.scene == 1:
                    value = SearchFormats.ANIME
                elif row.anime == 1 and row.scene == 1:
                    value = SearchFormats.SCENE
                elif row.sports == 1:
                    value = SearchFormats.SPORTS
                elif row.air_by_date == 1:
                    value = SearchFormats.AIR_BY_DATE
                elif row.scene == 1:
                    value = SearchFormats.SCENE
                else:
                    value = SearchFormats.STANDARD

                conn.execute(tv_shows.update().where(tv_shows.c.indexer_id == row.indexer_id).values(search_format=value))

        class TVShowBackup(Base):
            __tablename__ = 'tv_shows_backup'

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
            search_format = Column(Integer, default=SearchFormats.STANDARD)
            anime = Column(Boolean, default=0)
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
            scene_exceptions = Column(Text, default='')
            last_scene_exceptions_refresh = Column(Integer, default=0)
            last_update = Column(Integer, default=datetime.datetime.now().toordinal())
            last_refresh = Column(Integer, default=datetime.datetime.now().toordinal())
            last_backlog_search = Column(Integer, default=0)
            last_proper_search = Column(Integer, default=0)

        TVShowBackup.__table__.create(migrate_engine)
        tv_shows_backup = Table('tv_shows_backup', meta, autoload=True)

        session = sessionmaker(bind=migrate_engine)()

        for row in session.query(tv_shows):
            tv_shows_backup.insert().execute(dict((k, getattr(row, k)) for k in row.keys() if k not in ['scene', 'sports', 'air_by_date']))

        session.commit()
        session.close()

        tv_shows.drop()
        tv_shows_backup.rename('tv_shows')


def downgrade(migrate_engine):
    pass
