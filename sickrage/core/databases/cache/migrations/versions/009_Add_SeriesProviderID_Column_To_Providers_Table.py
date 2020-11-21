"""Initial migration

Revision ID: 7
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
from sickrage.core.enums import SeriesProviderID

revision = '9'
down_revision = '8'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    providers = sa.Table('providers', meta, autoload=True)

    op.add_column('providers', sa.Column('series_provider_id', sa.Enum, default=SeriesProviderID.THETVDB))

    with op.get_context().begin_transaction():
        for row in conn.execute(providers.select()):
            conn.execute(f'UPDATE providers SET series_provider_id = "{SeriesProviderID.THETVDB.name}" WHERE providers.id = {row.id}')


def downgrade():
    pass
