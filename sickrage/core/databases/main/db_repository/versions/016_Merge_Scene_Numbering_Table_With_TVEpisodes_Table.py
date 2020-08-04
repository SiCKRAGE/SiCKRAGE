from sqlalchemy import *
from sqlalchemy.exc import NoSuchTableError


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    tv_episodes = Table('tv_episodes', meta, autoload=True)

    try:
        scene_numbering = Table('scene_numbering', meta, autoload=True)
    except NoSuchTableError:
        scene_numbering = None

    if scene_numbering is not None:
        with migrate_engine.begin() as conn:
            for row in migrate_engine.execute(scene_numbering.select()):
                conn.execute(tv_episodes.update().where(
                    tv_episodes.c.show_id == row.indexer_id,
                    tv_episodes.c.season == row.season,
                    tv_episodes.c.episode == row.episode
                ).values(
                    scene_season=row.scene_season,
                    scene_episode=row.scene_episode
                ))

        scene_numbering.drop()


def downgrade(migrate_engine):
    pass
