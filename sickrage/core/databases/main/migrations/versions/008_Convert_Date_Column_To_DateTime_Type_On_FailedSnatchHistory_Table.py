"""Initial migration

Revision ID: 8
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '8'
down_revision = '7'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    failed_snatch_history = sa.Table('failed_snatch_history', meta, autoload=True)

    op.alter_column('failed_snatch_history', 'date', type_=sa.String(32))

    date_format = '%Y%m%d%H%M%S'

    with op.get_context().begin_transaction():
        for row in conn.execute(failed_snatch_history.select()):
            date = datetime.datetime.strptime(str(row.date), date_format)
            conn.execute(f'UPDATE failed_snatch_history SET date = {date} WHERE failed_snatch_history.id = {row.id}')

    op.alter_column('failed_snatch_history', 'date', type_=sa.DateTime)


def downgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    failed_snatch_history = sa.Table('failed_snatch_history', meta, autoload=True)

    op.alter_column('failed_snatch_history', 'date', type_=sa.String(32))

    with op.get_context().begin_transaction():
        for row in conn.execute(failed_snatch_history.select()):
            date = str(row.date.toordinal())
            conn.execute(f'UPDATE failed_snatch_history SET date = {date} WHERE failed_snatch_history.id = {row.id}')

    op.alter_column('failed_snatch_history', 'date', type_=sa.Integer)
