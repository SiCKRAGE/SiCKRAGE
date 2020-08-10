"""Initial migration

Revision ID: 7
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '7'
down_revision = '6'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    tv_episodes = sa.Table('tv_episodes', meta, autoload=True)

    op.alter_column('tv_episodes', 'airdate', type=sa.String(32))

    with op.get_context().begin_transaction():
        for row in conn.execute(tv_episodes.select()):
            date = datetime.date.fromordinal(int(row.airdate))
            conn.execute('UPDATE tv_episodes SET airdate = {} WHERE tv_episodes.indexer_id = {}'
                         .format(date, row.indexer_id))

    op.alter_column('tv_episodes', 'airdate', type=sa.Date)


def downgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    tv_episodes = sa.Table('tv_episodes', meta, autoload=True)

    op.alter_column('tv_episodes', 'airdate', type=sa.String(32))

    with op.get_context().begin_transaction():
        for row in conn.execute(tv_episodes.select()):
            date = str(row.airdate.toordinal())
            conn.execute('UPDATE tv_episodes SET airdate = {} WHERE tv_episodes.indexer_id = {}'
                         .format(date, row.indexer_id))

    op.alter_column('tv_episodes', 'airdate', type=sa.Integer)
