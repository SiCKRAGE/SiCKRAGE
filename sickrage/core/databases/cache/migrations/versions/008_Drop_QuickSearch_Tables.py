"""Initial migration

Revision ID: 8
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
from sqlalchemy import inspect

revision = '8'
down_revision = '7'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)

    if inspect(conn).has_table('quicksearch_shows'):
        op.drop_table('quicksearch_shows')

    if inspect(conn).has_table('quicksearch_episodes'):
        op.drop_table('quicksearch_episodes')



def downgrade():
    pass
