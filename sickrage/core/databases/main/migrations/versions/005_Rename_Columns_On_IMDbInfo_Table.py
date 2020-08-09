"""Initial migration

Revision ID: 5
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '5'
down_revision = '4'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    imdb_info = sa.Table('imdb_info', meta, autoload=True)

    with op.batch_alter_table("imdb_info") as batch_op:
        if hasattr(imdb_info.c, 'imdbVotes'):
            batch_op.alter_column('imdbVotes', new_column_name='votes')
        if hasattr(imdb_info.c, 'imdbRating'):
            batch_op.alter_column('imdbRating', new_column_name='rating')
        if hasattr(imdb_info.c, 'Rated'):
            batch_op.alter_column('Rated', new_column_name='rated')
        if hasattr(imdb_info.c, 'Title'):
            batch_op.alter_column('Title', new_column_name='title')
        if hasattr(imdb_info.c, 'DVD'):
            batch_op.alter_column('DVD', new_column_name='dvd')
        if hasattr(imdb_info.c, 'Production'):
            batch_op.alter_column('Production', new_column_name='production')
        if hasattr(imdb_info.c, 'Website'):
            batch_op.alter_column('Website', new_column_name='website')
        if hasattr(imdb_info.c, 'Writer'):
            batch_op.alter_column('Writer', new_column_name='writer')
        if hasattr(imdb_info.c, 'Actors'):
            batch_op.alter_column('Actors', new_column_name='actors')
        if hasattr(imdb_info.c, 'Type'):
            batch_op.alter_column('Type', new_column_name='type')
        if hasattr(imdb_info.c, 'totalSeasons'):
            batch_op.alter_column('totalSeasons', new_column_name='seasons')
        if hasattr(imdb_info.c, 'Poster'):
            batch_op.alter_column('Poster', new_column_name='poster')
        if hasattr(imdb_info.c, 'Director'):
            batch_op.alter_column('Director', new_column_name='director')
        if hasattr(imdb_info.c, 'Released'):
            batch_op.alter_column('Released', new_column_name='released')
        if hasattr(imdb_info.c, 'Awards'):
            batch_op.alter_column('Awards', new_column_name='awards')
        if hasattr(imdb_info.c, 'Genre'):
            batch_op.alter_column('Genre', new_column_name='genre')
        if hasattr(imdb_info.c, 'Language'):
            batch_op.alter_column('Language', new_column_name='language')
        if hasattr(imdb_info.c, 'Country'):
            batch_op.alter_column('Country', new_column_name='country')
        if hasattr(imdb_info.c, 'Runtime'):
            batch_op.alter_column('Runtime', new_column_name='runtime')
        if hasattr(imdb_info.c, 'imdbID'):
            batch_op.alter_column('imdbID', new_column_name='imdb_id')
        if hasattr(imdb_info.c, 'Metascore'):
            batch_op.alter_column('Metascore', new_column_name='metascore')
        if hasattr(imdb_info.c, 'Year'):
            batch_op.alter_column('Year', new_column_name='year')
        if hasattr(imdb_info.c, 'Plot'):
            batch_op.alter_column('Plot', new_column_name='plot')


def downgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    imdb_info = sa.Table('imdb_info', meta, autoload=True)

    with op.batch_alter_table("imdb_info") as batch_op:
        if hasattr(imdb_info.c, 'votes'):
            batch_op.alter_column('votes', new_column_name='imdbVotes')
        if hasattr(imdb_info.c, 'rating'):
            batch_op.alter_column('rating', new_column_name='imdbRating')
        if hasattr(imdb_info.c, 'rated'):
            batch_op.alter_column('rated', new_column_name='Rated')
        if hasattr(imdb_info.c, 'title'):
            batch_op.alter_column('title', new_column_name='Title')
        if hasattr(imdb_info.c, 'dvd'):
            batch_op.alter_column('dvd', new_column_name='DVD')
        if hasattr(imdb_info.c, 'production'):
            batch_op.alter_column('production', new_column_name='Production')
        if hasattr(imdb_info.c, 'website'):
            batch_op.alter_column('website', new_column_name='Website')
        if hasattr(imdb_info.c, 'writer'):
            batch_op.alter_column('writer', new_column_name='Writer')
        if hasattr(imdb_info.c, 'actors'):
            batch_op.alter_column('actors', new_column_name='Actors')
        if hasattr(imdb_info.c, 'typr'):
            batch_op.alter_column('type', new_column_name='Type')
        if hasattr(imdb_info.c, 'seasons'):
            batch_op.alter_column('season', new_column_name='totalSeasons')
        if hasattr(imdb_info.c, 'poster'):
            batch_op.alter_column('poster', new_column_name='Poster')
        if hasattr(imdb_info.c, 'director'):
            batch_op.alter_column('director', new_column_name='Director')
        if hasattr(imdb_info.c, 'released'):
            batch_op.alter_column('released', new_column_name='Released')
        if hasattr(imdb_info.c, 'awards'):
            batch_op.alter_column('awards', new_column_name='Awards')
        if hasattr(imdb_info.c, 'genre'):
            batch_op.alter_column('genre', new_column_name='Genre')
        if hasattr(imdb_info.c, 'language'):
            batch_op.alter_column('language', new_column_name='Language')
        if hasattr(imdb_info.c, 'country'):
            batch_op.alter_column('country', new_column_name='Country')
        if hasattr(imdb_info.c, 'runtime'):
            batch_op.alter_column('runtime', new_column_name='Runtime')
        if hasattr(imdb_info.c, 'imdb_id'):
            batch_op.alter_column('imdb_id', new_column_name='imdbID')
        if hasattr(imdb_info.c, 'metascore'):
            batch_op.alter_column('metascore', new_column_name='Metascore')
        if hasattr(imdb_info.c, 'year'):
            batch_op.alter_column('year', new_column_name='Year')
        if hasattr(imdb_info.c, 'plot'):
            batch_op.alter_column('plot', new_column_name='Plot')
