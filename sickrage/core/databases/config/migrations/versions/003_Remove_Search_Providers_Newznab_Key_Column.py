"""Initial migration

Revision ID: 3
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3'
down_revision = '2'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    search_providers_newznab = sa.Table('search_providers_newznab', meta, autoload=True)

    with op.get_context().begin_transaction():
        for row in conn.execute(search_providers_newznab.select()):
            if row.key:
                conn.execute(f'UPDATE search_providers_newznab SET api_key = "{row.key}" WHERE search_providers_newznab.id = {row.id}')

    with op.batch_alter_table('search_providers_newznab') as batch_op:
        batch_op.drop_column('key')


def downgrade():
    pass
