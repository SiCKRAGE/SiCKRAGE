from sqlalchemy import *


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    tv_shows = Table('tv_shows', meta, autoload=True)
    if not hasattr(tv_shows.c, 'last_proper_search'):
        last_proper_search = Column('last_proper_search', Integer, default=0)
        last_proper_search.create(tv_shows)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    tv_shows = Table('tv_shows', meta, autoload=True)
    if hasattr(tv_shows.c, 'last_proper_search'):
        tv_shows.c.last_proper_search.drop()
