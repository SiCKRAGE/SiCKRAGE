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
import sickrage
from sickrage.core.databases.main import MainDB


def find_epsiode(episode_id):
    if not episode_id:
        return None

    with sickrage.app.main_db.session() as session:
        db_data = session.query(MainDB.TVEpisode).filter_by(indexer_id=episode_id).one_or_none()
        if db_data:
            series = sickrage.app.shows.get((db_data.showid, db_data.indexer), None)
            if series:
                return series.get_episode(db_data.season, db_data.episode)
