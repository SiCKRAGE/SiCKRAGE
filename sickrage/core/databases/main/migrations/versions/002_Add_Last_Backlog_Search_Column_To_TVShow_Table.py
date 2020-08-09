"""Initial migration

Revision ID: 2
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2'
down_revision = '1'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    tv_shows = sa.Table('tv_shows', meta, autoload=True)

    if not hasattr(tv_shows.c, 'last_backlog_search'):
        op.add_column('tv_shows', sa.Column('last_backlog_search', sa.Integer, default=0))


def downgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    tv_shows = sa.Table('tv_shows', meta, autoload=True)

    if hasattr(tv_shows.c, 'last_backlog_search'):
        op.drop_column('tv_shows', 'last_backlog_search')
