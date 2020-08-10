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
                conn.execute('UPDATE tv_episodes SET scene_season = {} WHERE tv_episodes.showid = {}, tv_episodes.season = {}, tv_episodes.episode = {}'
                             .format(row.scene_season, row.indexer_id, row.season, row.episode))
                conn.execute('UPDATE tv_episodes SET scene_episode = {} WHERE tv_episodes.showid = {}, tv_episodes.season = {}, tv_episodes.episode = {}'
                             .format(row.scene_episode, row.indexer_id, row.season, row.episode))

        op.drop_table('scene_numbering')


def downgrade():
    pass
