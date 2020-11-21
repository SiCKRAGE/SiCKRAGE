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
from sickrage.core.enums import SeriesProviderID


def find_episode(episode_id, series_provider_id):
    if not episode_id or not series_provider_id:
        return None

    with sickrage.app.main_db.session() as session:
        db_data = session.query(MainDB.TVEpisode).filter_by(episode_id=int(episode_id), series_provider_id=series_provider_id).one_or_none()
        if db_data:
            series = sickrage.app.shows.get((db_data.series_id, db_data.series_provider_id), None)
            return series.get_episode(db_data.season, db_data.episode)


def find_episode_by_slug(episode_slug):
    if not episode_slug:
        return None

    episode_id, series_provider_slug = episode_slug.split('-')
    series_provider_id = SeriesProviderID.by_slug(series_provider_slug)

    with sickrage.app.main_db.session() as session:
        db_data = session.query(MainDB.TVEpisode).filter_by(episode_id=int(episode_id), series_provider_id=series_provider_id).one_or_none()
        if db_data:
            series = sickrage.app.shows.get((db_data.series_id, db_data.series_provider_id), None)
            return series.get_episode(db_data.season, db_data.episode)
