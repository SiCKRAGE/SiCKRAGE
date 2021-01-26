"""Initial migration

Revision ID: 11
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '11'
down_revision = '10'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    tv_shows = sa.Table('tv_shows', meta, autoload=True)

    if not hasattr(tv_shows.c, 'scene_exceptions'):
        op.add_column('tv_shows', sa.Column('scene_exceptions', sa.Text, default=''))

    if not hasattr(tv_shows.c, 'last_scene_exceptions_refresh'):
        op.add_column('tv_shows', sa.Column('last_scene_exceptions_refresh', sa.Integer, default=0))


def downgrade():
    pass
