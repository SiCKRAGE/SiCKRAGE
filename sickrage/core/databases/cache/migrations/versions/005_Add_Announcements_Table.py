"""Initial migration

Revision ID: 5
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5'
down_revision = '4'


def upgrade():
    op.create_table(
        'announcements',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('hash', sa.String(255), unique=True, nullable=False),
        sa.Column('seen', sa.Boolean, server_default='false')
    )


def downgrade():
    pass
