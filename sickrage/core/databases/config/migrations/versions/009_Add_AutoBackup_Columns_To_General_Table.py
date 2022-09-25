"""Initial migration

Revision ID: 9
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.

revision = '9'
down_revision = '8'


def upgrade():
    op.add_column('general', sa.Column('auto_backup_enable', sa.Boolean))
    op.add_column('general', sa.Column('auto_backup_freq', sa.Integer, server_default='24'))
    op.add_column('general', sa.Column('auto_backup_keep_num', sa.Integer, server_default='1'))
    op.add_column('general', sa.Column('auto_backup_dir', sa.Text, server_default=''))


def downgrade():
    pass
