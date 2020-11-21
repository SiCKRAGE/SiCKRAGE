"""Initial migration

Revision ID: 7
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '19'
down_revision = '18'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    tv_shows = sa.Table('tv_shows', meta, autoload=True)

    with op.get_context().begin_transaction():
        for row in conn.execute(tv_shows.select()):
            conn.execute(f'UPDATE tv_shows SET last_refresh = "" WHERE tv_shows.indexer_id = {row.indexer_id}')
            conn.execute(f'UPDATE tv_shows SET last_xem_refresh = "" WHERE tv_shows.indexer_id = {row.indexer_id}')
            conn.execute(f'UPDATE tv_shows SET last_scene_exceptions_refresh = "" WHERE tv_shows.indexer_id = {row.indexer_id}')
            conn.execute(f'UPDATE tv_shows SET last_update = "" WHERE tv_shows.indexer_id = {row.indexer_id}')
            conn.execute(f'UPDATE tv_shows SET last_backlog_search = "" WHERE tv_shows.indexer_id = {row.indexer_id}')
            conn.execute(f'UPDATE tv_shows SET last_proper_search = "" WHERE tv_shows.indexer_id = {row.indexer_id}')

    with op.batch_alter_table("tv_shows") as batch_op:
        batch_op.alter_column('last_refresh', type_=sa.DateTime(timezone=True))
        batch_op.alter_column('last_xem_refresh', type_=sa.DateTime(timezone=True))
        batch_op.alter_column('last_scene_exceptions_refresh', type_=sa.DateTime(timezone=True))
        batch_op.alter_column('last_update', type_=sa.DateTime(timezone=True))
        batch_op.alter_column('last_backlog_search', type_=sa.DateTime(timezone=True))
        batch_op.alter_column('last_proper_search', type_=sa.DateTime(timezone=True))

    with op.get_context().begin_transaction():
        for row in conn.execute(tv_shows.select()):
            conn.execute(f'UPDATE tv_shows SET last_refresh = {sa.func.current_timestamp()} WHERE tv_shows.indexer_id = {row.indexer_id}')
            conn.execute(f'UPDATE tv_shows SET last_xem_refresh = {sa.func.current_timestamp()} WHERE tv_shows.indexer_id = {row.indexer_id}')
            conn.execute(f'UPDATE tv_shows SET last_scene_exceptions_refresh = {sa.func.current_timestamp()} WHERE tv_shows.indexer_id = {row.indexer_id}')
            conn.execute(f'UPDATE tv_shows SET last_update = {sa.func.current_timestamp()} WHERE tv_shows.indexer_id = {row.indexer_id}')
            conn.execute(f'UPDATE tv_shows SET last_backlog_search = {sa.func.current_timestamp()} WHERE tv_shows.indexer_id = {row.indexer_id}')
            conn.execute(f'UPDATE tv_shows SET last_proper_search = {sa.func.current_timestamp()} WHERE tv_shows.indexer_id = {row.indexer_id}')


def downgrade():
    pass
