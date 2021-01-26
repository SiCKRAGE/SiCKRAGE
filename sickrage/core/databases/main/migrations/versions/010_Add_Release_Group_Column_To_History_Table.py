"""Initial migration

Revision ID: 10
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '10'
down_revision = '9'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    history = sa.Table('history', meta, autoload=True)

    if not hasattr(history.c, 'release_group'):
        op.add_column('history', sa.Column('release_group', sa.Text, default=''))


def downgrade():
    pass
