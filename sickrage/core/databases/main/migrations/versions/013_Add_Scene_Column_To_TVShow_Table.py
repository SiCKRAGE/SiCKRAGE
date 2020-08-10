"""Initial migration

Revision ID: 13
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import sqlalchemy as sa
from alembic import op

from sickrage.core.common import SearchFormats

# revision identifiers, used by Alembic.
revision = '13'
down_revision = '12'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    tv_shows = sa.Table('tv_shows', meta, autoload=True)

    if not hasattr(tv_shows.c, 'scene'):
        op.add_column('tv_shows', sa.Column('scene', sa.Boolean, default=0))

    with op.get_context().begin_transaction():
        for row in conn.execute(tv_shows.select()):
            if row.search_format == 5:
                conn.execute('UPDATE tv_shows SET scene = 1 WHERE tv_shows.indexer_id = {}'
                             .format(row.indexer_id))
                conn.execute('UPDATE tv_shows SET search_format = {} WHERE tv_shows.indexer_id = {}'
                             .format(SearchFormats.STANDARD, row.indexer_id))


def downgrade():
    pass
