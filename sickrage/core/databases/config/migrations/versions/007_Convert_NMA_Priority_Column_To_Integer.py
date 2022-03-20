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
    nma = sa.Table('nma', meta, autoload=True)

    for row in conn.execute(nma.select()):
        priority = row.priority

        if isinstance(priority, str):
            try:
                priority = int(priority or 0)
            except ValueError:
                priority = 0

        conn.execute(f'UPDATE nma SET priority = {priority} WHERE nma.id = {row.id}')


def downgrade():
    pass
