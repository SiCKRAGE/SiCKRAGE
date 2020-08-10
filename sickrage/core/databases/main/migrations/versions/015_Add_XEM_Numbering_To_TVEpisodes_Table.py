"""Initial migration

Revision ID: 15
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '15'
down_revision = '14'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    tv_episodes = sa.Table('tv_episodes', meta, autoload=True)

    with op.batch_alter_table("tv_episodes") as batch_op:
        if not hasattr(tv_episodes.c, 'xem_season'):
            batch_op.add_column(sa.Column('xem_season', sa.Integer, default=-1))
        if not hasattr(tv_episodes.c, 'xem_episode'):
            batch_op.add_column(sa.Column('xem_episode', sa.Integer, default=-1))
        if not hasattr(tv_episodes.c, 'xem_absolute_number'):
            batch_op.add_column(sa.Column('xem_absolute_number', sa.Integer, default=-1))


def downgrade():
    pass
