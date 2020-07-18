from sqlalchemy import *

from sickrage.core.common import SearchFormats


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    tv_shows = Table('tv_shows', meta, autoload=True)
    if not hasattr(tv_shows.c, 'scene'):
        scene = Column('scene', Boolean, default=0)
        scene.create(tv_shows)

        with migrate_engine.begin() as conn:
            for row in migrate_engine.execute(tv_shows.select()):
                if row.search_format == 5:
                    conn.execute(tv_shows.update().where(tv_shows.c.indexer_id == row.indexer_id).values(scene=1, search_format=SearchFormats.STANDARD))


def downgrade(migrate_engine):
    pass
