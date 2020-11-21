"""Initial migration

Revision ID: 16
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '16'
down_revision = '15'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)

    if conn.engine.dialect.has_table(conn.engine, 'scene_numbering'):
        scene_numbering = sa.Table('scene_numbering', meta, autoload=True)
        with op.get_context().begin_transaction():
            for row in conn.execute(scene_numbering.select()):
                conn.execute(
                    f'UPDATE tv_episodes SET scene_season = {row.scene_season} WHERE tv_episodes.showid = {row.indexer_id} and tv_episodes.season = {row.season} and tv_episodes.episode = {row.episode}')
                conn.execute(
                    f'UPDATE tv_episodes SET scene_episode = {row.scene_episode} WHERE tv_episodes.showid = {row.indexer_id} and tv_episodes.season = {row.season} and tv_episodes.episode = {row.episode}')

        op.drop_table('scene_numbering')


def downgrade():
    pass
