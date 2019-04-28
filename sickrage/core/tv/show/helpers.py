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
from sickrage.core.databases.main import MainDB
from sickrage.core.api.imdb import IMDbAPI
from sickrage.core.exceptions import EpisodeNotFoundException, EpisodeDeletedException
from sickrage.core.helpers import safe_getattr, try_int
from sickrage.indexers.config import INDEXER_TVRAGE
from sickrage.indexers.exceptions import indexer_attributenotfound


def find_show(indexer_id):
    from sickrage.core.tv.show import TVShow

    if not indexer_id:
        return None

    try:
        return TVShow.query.filter_by(indexer_id=indexer_id).one()
    except orm.exc.NoResultFound:
        return None


def find_show_by_name(term):
    from sickrage.core.tv.show import TVShow

    try:
        return TVShow.query.filter_by(name=term).one()
    except orm.exc.NoResultFound:
        return None


def get_show_list():
    from sickrage.core.tv.show import TVShow

    return list(TVShow.query)


def load_imdb_info(indexer_id):
    imdb_info_mapper = {
        'imdbvotes': 'votes',
        'imdbrating': 'rating',
        'totalseasons': 'seasons',
        'imdbid': 'imdb_id'
    }

    show = find_show(indexer_id)

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
        sickrage.app.log.debug(str(indexer_id) + ": Loading show info from IMDb")

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

        sickrage.app.log.debug(str(indexer_id) + ": Obtained IMDb info ->" + str(imdb_info))

        # save imdb info to database
        imdb_info.update({
            'indexer_id': indexer_id,
            'last_update': datetime.date.today().toordinal()
        })

        try:
            dbData = MainDB.IMDbInfo.query.filter_by(indexer_id=indexer_id).one()
            dbData.update(**imdb_info)
        except orm.exc.NoResultFound:
            sickrage.app.main_db.add(MainDB.IMDbInfo(**imdb_info))
