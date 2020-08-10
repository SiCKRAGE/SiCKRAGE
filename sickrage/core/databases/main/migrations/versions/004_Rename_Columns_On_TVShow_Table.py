"""Initial migration

Revision ID: 4
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '4'
down_revision = '3'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    tv_shows = sa.Table('tv_shows', meta, autoload=True)

    if hasattr(tv_shows.c, 'show_name'):
        op.alter_column('tv_shows', 'show_name', new_column_name='name')


def downgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    tv_shows = sa.Table('tv_shows', meta, autoload=True)

    if hasattr(tv_shows.c, 'name'):
        op.alter_column('tv_shows', 'name', new_column_name='show_name')
