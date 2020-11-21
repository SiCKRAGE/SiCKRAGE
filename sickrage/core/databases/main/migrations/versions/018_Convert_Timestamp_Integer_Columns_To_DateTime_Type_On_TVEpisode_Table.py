"""Initial migration

Revision ID: 7
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '18'
down_revision = '17'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    tv_episodes = sa.Table('tv_episodes', meta, autoload=True)

    with op.get_context().begin_transaction():
        for row in conn.execute(tv_episodes.select()):
            conn.execute(f'UPDATE tv_episodes SET subtitles_lastsearch = "" WHERE tv_episodes.indexer_id = {row.indexer_id}')

    with op.batch_alter_table("tv_episodes") as batch_op:
        batch_op.alter_column('subtitles_lastsearch', type_=sa.DateTime(timezone=True))

    with op.get_context().begin_transaction():
        for row in conn.execute(tv_episodes.select()):
            conn.execute(f'UPDATE tv_episodes SET subtitles_lastsearch = {sa.func.current_timestamp()} WHERE tv_episodes.indexer_id = {row.indexer_id}')

def downgrade():
    pass
