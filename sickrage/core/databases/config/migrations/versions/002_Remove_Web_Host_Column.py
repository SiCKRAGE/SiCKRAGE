"""Initial migration

Revision ID: 1
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '2'
down_revision = '1'


def upgrade():
    with op.batch_alter_table('general') as batch_op:
        batch_op.drop_column('web_host')


def downgrade():
    pass
