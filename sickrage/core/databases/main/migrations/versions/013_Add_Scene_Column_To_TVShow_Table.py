"""Initial migration

Revision ID: 13
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '13'
down_revision = '12'


class SearchFormats(object):
    STANDARD = 1
    AIR_BY_DATE = 2
    ANIME = 3
    SPORTS = 4
    COLLECTION = 6

    search_format_strings = {
        STANDARD: 'Standard (Show.S01E01)',
        AIR_BY_DATE: 'Air By Date (Show.2010.03.02)',
        ANIME: 'Anime (Show.265)',
        SPORTS: 'Sports (Show.2010.03.02)',
        COLLECTION: 'Collection (Show.Series.1.1of10) or (Show.Series.1.Part.1)'
    }


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    tv_shows = sa.Table('tv_shows', meta, autoload=True)

    if not hasattr(tv_shows.c, 'scene'):
        op.add_column('tv_shows', sa.Column('scene', sa.Boolean, default=0))

    with op.get_context().begin_transaction():
        for row in conn.execute(tv_shows.select()):
            if row.search_format == 5:
                conn.execute(f'UPDATE tv_shows SET scene = 1 WHERE tv_shows.indexer_id = {row.indexer_id}')
                conn.execute(f'UPDATE tv_shows SET search_format = {SearchFormats.STANDARD} WHERE tv_shows.indexer_id = {row.indexer_id}')


def downgrade():
    pass
