"""Initial migration

Revision ID: 3
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '3'
down_revision = '2'


def upgrade():
    with op.batch_alter_table('search_providers_newznab') as batch_op:
        batch_op.drop_column('key')


def downgrade():
    pass
