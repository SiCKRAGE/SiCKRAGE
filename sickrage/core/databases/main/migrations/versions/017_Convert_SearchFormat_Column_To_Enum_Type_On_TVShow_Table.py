"""Initial migration

Revision ID: 17
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import enum

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '17'
down_revision = '16'


class SearchFormat(enum.Enum):
    STANDARD = 1
    AIR_BY_DATE = 2
    ANIME = 3
    SPORTS = 4
    COLLECTION = 6


def upgrade():
    conn = op.get_bind()

    for item in SearchFormat:
        conn.execute(f'UPDATE tv_shows SET search_format = "{item.name}" WHERE search_format = {item.value}')

    with op.batch_alter_table('tv_shows') as batch_op:
        batch_op.alter_column('search_format', type_=sa.Enum(SearchFormat), default=SearchFormat.STANDARD)


def downgrade():
    pass
