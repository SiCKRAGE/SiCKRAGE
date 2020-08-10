"""Rename Columns On TV Episodes Table

Revision ID: 6
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '6'
down_revision = '5'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    tv_episodes = sa.Table('tv_episodes', meta, autoload=True)

    if hasattr(tv_episodes.c, 'indexerid'):
        op.alter_column('tv_episodes', 'indexerid', new_column_name='indexer_id')

    if 'idx_indexerid_airdate' in tv_episodes.indexes:
        op.drop_index('idx_indexerid_airdate', 'tv_episodes')
        op.create_index('idx_indexer_id_airdate', 'tv_episodes', ['indexer_id', 'airdate'])


def downgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    tv_episodes = sa.Table('tv_episodes', meta, autoload=True)

    if hasattr(tv_episodes.c, 'indexer_id'):
        op.alter_column('tv_episodes', 'indexer_id', new_column_name='indexerid')

    if 'idx_indexer_id_airdate' in tv_episodes.indexes:
        op.drop_index('idx_indexer_id_airdate', 'tv_episodes')
        op.create_index('idx_indexerid_airdate', 'tv_episodes', ['indexerid', 'airdate'])
