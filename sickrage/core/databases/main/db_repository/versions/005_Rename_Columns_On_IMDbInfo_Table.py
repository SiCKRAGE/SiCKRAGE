#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#
#  This file is part of SiCKRAGE.
#
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.

from sqlalchemy import *


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    imdb_info = Table('imdb_info', meta, autoload=True)
    imdb_info.c.imdbVotes.alter(name='votes')
    imdb_info.c.imdbRating.alter(name='rating')
    imdb_info.c.Rated.alter(name='rated')
    imdb_info.c.Title.alter(name='title')
    imdb_info.c.DVD.alter(name='dvd')
    imdb_info.c.Production.alter(name='production')
    imdb_info.c.Website.alter(name='website')
    imdb_info.c.Writer.alter(name='writer')
    imdb_info.c.Actors.alter(name='actors')
    imdb_info.c.Type.alter(name='type')
    imdb_info.c.totalSeasons.alter(name='seasons')
    imdb_info.c.Poster.alter(name='poster')
    imdb_info.c.Director.alter(name='director')
    imdb_info.c.Released.alter(name='released')
    imdb_info.c.Awards.alter(name='awards')
    imdb_info.c.Genre.alter(name='genre')
    imdb_info.c.Language.alter(name='language')
    imdb_info.c.Country.alter(name='country')
    imdb_info.c.Runtime.alter(name='runtime')
    imdb_info.c.imdbID.alter(name='imdb_id')
    imdb_info.c.Metascore.alter(name='metascore')
    imdb_info.c.Year.alter(name='year')
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
