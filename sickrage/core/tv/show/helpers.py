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
from sqlalchemy import orm


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
