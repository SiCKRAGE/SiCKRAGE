"""Initial migration

Revision ID: 14
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '14'
down_revision = '13'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    tv_shows = sa.Table('tv_shows', meta, autoload=True)
    xem_refresh = sa.Table('xem_refresh', meta, autoload=True)

    if not hasattr(tv_shows.c, 'last_xem_refresh'):
        op.add_column('tv_shows', sa.Column('last_xem_refresh', sa.Integer, default=datetime.datetime.now().toordinal()))

    with op.get_context().begin_transaction():
        for row in conn.execute(xem_refresh.select()):
            last_xem_refresh = row.last_refreshed or datetime.datetime.now().toordinal()
            conn.execute(f'UPDATE tv_shows SET last_xem_refresh = {last_xem_refresh} WHERE tv_shows.indexer_id = {row.indexer_id}')

    op.drop_table('xem_refresh')


def downgrade():
    pass
