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
    op.add_column('general', sa.Column('sso_api_key', sa.Text, default=''))


def downgrade():
    pass
