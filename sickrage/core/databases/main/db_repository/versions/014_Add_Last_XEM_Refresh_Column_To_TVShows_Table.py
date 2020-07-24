import datetime

from sqlalchemy import *


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    tv_shows = Table('tv_shows', meta, autoload=True)
    if not hasattr(tv_shows.c, 'last_xem_refresh'):
        last_xem_refresh = Column('last_xem_refresh', Integer, default=datetime.datetime.now().toordinal())
        last_xem_refresh.create(tv_shows)

    xem_refresh = Table('xem_refresh', meta, autoload=True)
    if xem_refresh is not None:
        with migrate_engine.begin() as conn:
            for row in migrate_engine.execute(xem_refresh.select()):
                conn.execute(tv_shows.update().where(tv_shows.c.indexer_id == row.indexer_id).values(last_xem_refresh=row.last_refreshed))
        xem_refresh.drop()


def downgrade(migrate_engine):
    pass
