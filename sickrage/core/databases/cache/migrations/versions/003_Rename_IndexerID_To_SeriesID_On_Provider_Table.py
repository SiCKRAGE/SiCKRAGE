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
    providers = sa.Table('providers', meta, autoload=True)

    if hasattr(providers.c, 'indexer_id'):
        providers.c.indexer_id.alter(name='series_id')


def downgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    providers = sa.Table('providers', meta, autoload=True)

    if hasattr(providers.c, 'series_id'):
        providers.c.series_id.alter(name='indexer_id')
