"""Initial migration

Revision ID: 4
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import babelfish
from alembic import op

# revision identifiers, used by Alembic.

revision = '5'
down_revision = '4'


def upgrade():
    conn = op.get_bind()
    row = conn.execute(f"SELECT series_provider_default_language FROM general").first()
    if len(row.series_provider_default_language) == 2:
        lang = babelfish.Language.fromalpha2(row.series_provider_default_language)
        conn.execute(f'UPDATE general SET series_provider_default_language = "{lang.alpha3}"')


def downgrade():
    pass
