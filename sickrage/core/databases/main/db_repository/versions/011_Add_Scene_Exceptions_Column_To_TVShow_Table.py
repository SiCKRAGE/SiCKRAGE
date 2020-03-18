from sqlalchemy import *


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    tv_shows = Table('tv_shows', meta, autoload=True)
    if not hasattr(tv_shows.c, 'scene_exceptions'):
        scene_exceptions = Column('scene_exceptions', Text, default='')
        scene_exceptions.create(tv_shows)
    if not hasattr(tv_shows.c, 'last_scene_exceptions_refresh'):
        last_scene_exceptions_refresh = Column('last_scene_exceptions_refresh', Integer, default=0)
        last_scene_exceptions_refresh.create(tv_shows)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    tv_shows = Table('tv_shows', meta, autoload=True)
    if hasattr(tv_shows.c, 'scene_exceptions'):
        tv_shows.c.scene_exceptions.drop()
    if hasattr(tv_shows.c, 'last_scene_exceptions_refresh'):
        tv_shows.c.scene_exceptions.drop()
