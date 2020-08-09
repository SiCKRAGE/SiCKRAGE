"""Initial migration

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
    oauth2_token = sa.Table('oauth2_token', meta, autoload=True)

    if not hasattr(oauth2_token.c, 'session_state'):
        op.add_column('oauth2_token', sa.Column('session_state', sa.Text, default=''))


def downgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    oauth2_token = sa.Table('oauth2_token', meta, autoload=True)

    if hasattr(oauth2_token.c, 'session_state'):
        op.drop_column('oauth2_token', 'session_state')
