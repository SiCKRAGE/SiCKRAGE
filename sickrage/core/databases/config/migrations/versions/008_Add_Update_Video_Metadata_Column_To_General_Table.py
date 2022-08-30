"""Initial migration

Revision ID: 8
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.

revision = '8'
down_revision = '7'


def upgrade():
    op.add_column('general', sa.Column('update_video_metadata', sa.Boolean, server_default='true'))


def downgrade():
    pass
