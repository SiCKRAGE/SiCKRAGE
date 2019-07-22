# ##############################################################################
#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#  -
#  This file is part of SiCKRAGE.
#  -
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  -
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
# ##############################################################################

from sqlalchemy import *


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    imdb_info = Table('imdb_info', meta, autoload=True)

    if hasattr(imdb_info.c, 'imdbVotes'):
        imdb_info.c.imdbVotes.alter(name='votes')
    if hasattr(imdb_info.c, 'imdbRating'):
        imdb_info.c.imdbRating.alter(name='rating')
    if hasattr(imdb_info.c, 'Rated'):
        imdb_info.c.Rated.alter(name='rated')
    if hasattr(imdb_info.c, 'Title'):
        imdb_info.c.Title.alter(name='title')
    if hasattr(imdb_info.c, 'DVD'):
        imdb_info.c.DVD.alter(name='dvd')
    if hasattr(imdb_info.c, 'Production'):
        imdb_info.c.Production.alter(name='production')
    if hasattr(imdb_info.c, 'Website'):
        imdb_info.c.Website.alter(name='website')
    if hasattr(imdb_info.c, 'Writer'):
        imdb_info.c.Writer.alter(name='writer')
    if hasattr(imdb_info.c, 'Actors'):
        imdb_info.c.Actors.alter(name='actors')
    if hasattr(imdb_info.c, 'Type'):
        imdb_info.c.Type.alter(name='type')
    if hasattr(imdb_info.c, 'totalSeasons'):
        imdb_info.c.totalSeasons.alter(name='seasons')
    if hasattr(imdb_info.c, 'Poster'):
        imdb_info.c.Poster.alter(name='poster')
    if hasattr(imdb_info.c, 'Director'):
        imdb_info.c.Director.alter(name='director')
    if hasattr(imdb_info.c, 'Released'):
        imdb_info.c.Released.alter(name='released')
    if hasattr(imdb_info.c, 'Awards'):
        imdb_info.c.Awards.alter(name='awards')
    if hasattr(imdb_info.c, 'Genre'):
        imdb_info.c.Genre.alter(name='genre')
    if hasattr(imdb_info.c, 'Language'):
        imdb_info.c.Language.alter(name='language')
    if hasattr(imdb_info.c, 'Country'):
        imdb_info.c.Country.alter(name='country')
    if hasattr(imdb_info.c, 'Runtime'):
        imdb_info.c.Runtime.alter(name='runtime')
    if hasattr(imdb_info.c, 'imdbID'):
        imdb_info.c.imdbID.alter(name='imdb_id')
    if hasattr(imdb_info.c, 'Metascore'):
        imdb_info.c.Metascore.alter(name='metascore')
    if hasattr(imdb_info.c, 'Year'):
        imdb_info.c.Year.alter(name='year')
    if hasattr(imdb_info.c, 'Plot'):
        imdb_info.c.Plot.alter(name='plot')


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    imdb_info = Table('imdb_info', meta, autoload=True)
    imdb_info.c.votes.alter(name='imdbVotes')
    imdb_info.c.rating.alter(name='imdbRating')
    imdb_info.c.rated.alter(name='Rated')
    imdb_info.c.title.alter(name='Title')
    imdb_info.c.dvd.alter(name='DVD')
    imdb_info.c.production.alter(name='Production')
    imdb_info.c.website.alter(name='Website')
    imdb_info.c.writer.alter(name='Writer')
    imdb_info.c.actors.alter(name='Actors')
    imdb_info.c.type.alter(name='Type')
    imdb_info.c.seasons.alter(name='totalSeasons')
    imdb_info.c.poster.alter(name='Poster')
    imdb_info.c.director.alter(name='Director')
    imdb_info.c.released.alter(name='Released')
    imdb_info.c.awards.alter(name='Awards')
    imdb_info.c.genre.alter(name='Genre')
    imdb_info.c.language.alter(name='Language')
    imdb_info.c.country.alter(name='Country')
    imdb_info.c.runtime.alter(name='Runtime')
    imdb_info.c.imdb_id.alter(name='imdbID')
    imdb_info.c.metascore.alter(name='Metascore')
    imdb_info.c.year.alter(name='Year')
    imdb_info.c.plot.alter(name='Plot')
