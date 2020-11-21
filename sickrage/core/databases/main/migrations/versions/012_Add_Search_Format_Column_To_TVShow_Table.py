"""Initial migration

Revision ID: 12
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '12'
down_revision = '11'


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

    if not hasattr(tv_shows.c, 'search_format'):
        op.add_column('tv_shows', sa.Column('search_format', sa.Integer, default=0))

    with op.get_context().begin_transaction():
        for row in conn.execute(tv_shows.select()):
            if row.anime == 1 and not row.scene == 1:
                value = SearchFormats.ANIME
            elif row.anime == 1 and row.scene == 1:
                value = 5
            elif row.sports == 1:
                value = SearchFormats.SPORTS
            elif row.air_by_date == 1:
                value = SearchFormats.AIR_BY_DATE
            elif row.scene == 1:
                value = 5
            else:
                value = SearchFormats.STANDARD

            conn.execute(f'UPDATE tv_shows SET search_format = {value} WHERE tv_shows.indexer_id = {row.indexer_id}')

    with op.batch_alter_table('tv_shows') as batch_op:
        if hasattr(tv_shows.c, 'sports'):
            batch_op.drop_column('sports')

        if hasattr(tv_shows.c, 'air_by_date'):
            batch_op.drop_column('air_by_date')


def downgrade():
    pass
