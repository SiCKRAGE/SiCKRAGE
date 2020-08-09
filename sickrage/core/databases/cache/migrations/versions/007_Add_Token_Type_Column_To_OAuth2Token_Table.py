"""Initial migration

Revision ID: 7
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '7'
down_revision = '6'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    oauth2_token = sa.Table('oauth2_token', meta, autoload=True)

    if not hasattr(oauth2_token.c, 'token_type'):
        op.add_column('oauth2_token', sa.Column('token_type', sa.Text, default='bearer'))


def downgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    oauth2_token = sa.Table('oauth2_token', meta, autoload=True)

    if hasattr(oauth2_token.c, 'token_type'):
        op.drop_column('oauth2_token', 'token_type')
