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

import datetime

from sqlalchemy import orm

import sickrage
from sickrage.core.api.imdb import IMDbAPI
from sickrage.core.databases.main import MainDB


@MainDB.with_session
def find_show(indexer_id, session=None):
    from sickrage.core.tv.show import TVShow

    try:
        return session.query(TVShow).filter_by(indexer_id=indexer_id).one()
    except orm.exc.NoResultFound:
        return None


@MainDB.with_session
def find_show_by_name(term, session=None):
    from sickrage.core.tv.show import TVShow

    try:
        return session.query(TVShow).filter(TVShow.name.like('%{}%'.format(term))).one()
    except (orm.exc.NoResultFound, orm.exc.MultipleResultsFound):
        return None


@MainDB.with_session
def get_show_list(session=None):
    from sickrage.core.tv.show import TVShow
    return session.query(TVShow).all()


@MainDB.with_session
def load_imdb_info(indexer_id, session=None):
    imdb_info_mapper = {
        'imdbvotes': 'votes',
        'imdbrating': 'rating',
        'totalseasons': 'seasons',
        'imdbid': 'imdb_id'
    }

    show = find_show(indexer_id, session=session)

    if not show.imdb_id:
        resp = IMDbAPI().search_by_imdb_title(show.name)
        for x in resp['Search'] if 'Search' in resp else []:
            try:
                if int(x.get('Year'), 0) == show.startyear and x.get('Title') in show.name:
                    show.imdb_id = x.get('imdbID')
                    break
            except:
                continue

    if show.imdb_id:
        sickrage.app.log.debug(str(indexer_id) + ": Obtaining IMDb info")

        imdb_info = IMDbAPI().search_by_imdb_id(show.imdb_id)
        if not imdb_info:
            sickrage.app.log.debug(str(indexer_id) + ': Unable to obtain IMDb info')
            return

        imdb_info = dict((k.lower(), v) for k, v in imdb_info.items())
        for column in imdb_info.copy():
            if column in imdb_info_mapper:
                imdb_info[imdb_info_mapper[column]] = imdb_info[column]

            if column not in MainDB.IMDbInfo.__table__.columns.keys():
                del imdb_info[column]

        if not all([imdb_info.get('imdb_id'), imdb_info.get('votes'), imdb_info.get('rating'), imdb_info.get('genre')]):
            sickrage.app.log.debug(str(indexer_id) + ': IMDb info obtained does not meet our requirements')
            return

        sickrage.app.log.debug(str(indexer_id) + ": Obtained IMDb info ->" + str(imdb_info))

        # save imdb info to database
        imdb_info.update({
            'indexer_id': indexer_id,
            'last_update': datetime.date.today().toordinal()
        })

        try:
            dbData = session.query(MainDB.IMDbInfo).filter_by(indexer_id=indexer_id).one()
            dbData.update(**imdb_info)
        except orm.exc.NoResultFound:
            session.add(MainDB.IMDbInfo(**imdb_info))