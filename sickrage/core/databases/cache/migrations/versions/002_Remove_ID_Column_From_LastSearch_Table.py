"""Initial migration

Revision ID: 2
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '2'
down_revision = '1'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    last_search = sa.Table('last_search', meta, autoload=True)

    conn.execute(last_search.delete())

    last_search.c.provider.alter(type=sa.String(32))
    primary_key = sa.PrimaryKeyConstraint(last_search.c.provider)
    primary_key.create()
    last_search.c.id.drop()


def downgrade():
    pass
