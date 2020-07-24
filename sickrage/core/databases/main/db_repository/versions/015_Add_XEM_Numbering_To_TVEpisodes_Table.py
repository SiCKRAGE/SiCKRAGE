import datetime

from sqlalchemy import *


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    tv_episodes = Table('tv_episodes', meta, autoload=True)
    if not hasattr(tv_episodes.c, 'xem_season'):
        xem_season = Column('xem_season', Integer, default=-1)
        xem_season.create(tv_episodes)
    if not hasattr(tv_episodes.c, 'xem_episode'):
        xem_episode = Column('xem_episode', Integer, default=-1)
        xem_episode.create(tv_episodes)
    if not hasattr(tv_episodes.c, 'xem_absolute_number'):
        xem_absolute_number = Column('xem_absolute_number', Integer, default=-1)
        xem_absolute_number.create(tv_episodes)


def downgrade(migrate_engine):
    pass
