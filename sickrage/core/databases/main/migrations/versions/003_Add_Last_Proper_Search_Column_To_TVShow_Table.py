"""Initial migration

Revision ID: 3
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '3'
down_revision = '2'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    tv_shows = sa.Table('tv_shows', meta, autoload=True)

    if not hasattr(tv_shows.c, 'last_proper_search'):
        op.add_column('tv_shows', sa.Column('last_proper_search', sa.Integer, default=0))


def downgrade():
    pass
