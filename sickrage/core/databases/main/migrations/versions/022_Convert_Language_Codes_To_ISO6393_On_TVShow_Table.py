"""Initial migration

Revision ID: 22
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""

import babelfish
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '22'
down_revision = '21'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    tv_shows = sa.Table('tv_shows', meta, autoload=True)

    with op.get_context().begin_transaction():
        for row in conn.execute(tv_shows.select()):
            if len(row.lang) == 2:
                lang = babelfish.Language.fromalpha2(row.lang)
                conn.execute(f'UPDATE tv_shows SET lang = "{lang.alpha3}" WHERE tv_shows.series_id = {row.series_id}')


def downgrade():
    pass
