"""Initial migration

Revision ID: 9
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '9'
down_revision = '8'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    history = sa.Table('history', meta, autoload=True)

    op.alter_column('history', 'date', type_=sa.String(32))

    date_format = '%Y%m%d%H%M%S'

    with op.get_context().begin_transaction():
        for row in conn.execute(history.select()):
            date = datetime.datetime.strptime(str(row.date), date_format)
            conn.execute(f'UPDATE history SET date = {date} WHERE history.id = {row.id}')

    op.alter_column('history', 'date', type_=sa.DateTime)


def downgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    history = sa.Table('history', meta, autoload=True)

    op.alter_column('history', 'date', type_=sa.String(32))

    with op.get_context().begin_transaction():
        for row in conn.execute(history.select()):
            date = str(row.date.toordinal())
            conn.execute(f'UPDATE history SET date = {date} WHERE history.id = {row.id}')

    op.alter_column('history', 'date', type_=sa.Integer)
