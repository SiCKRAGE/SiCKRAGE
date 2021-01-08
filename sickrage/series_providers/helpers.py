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
import re

from sqlalchemy import orm

import sickrage
from sickrage.core.databases.main import MainDB
from sickrage.core.enums import SeriesProviderID
from sickrage.core.tv.show.helpers import find_show


def map_series_providers(series_provider_id, series_id, name):
    session = sickrage.app.main_db.session()

    mapped = {}
    for series_provider_id in SeriesProviderID:
        mapped[series_provider_id.name] = None

    # init mapped series_provider_ids object
    for mapped_series_provider_id in SeriesProviderID:
        if mapped_series_provider_id == series_provider_id:
            mapped[mapped_series_provider_id.name] = series_id

    # for each mapped entry
    for dbData in session.query(MainDB.SeriesProviderMapping).filter_by(series_id=series_id, series_provider_id=series_provider_id):
        # Check if its mapped with both tvdb and tvrage.
        if len([i for i in dbData if i is not None]) >= 4:
            sickrage.app.log.debug("Found series_provider_id mapping in cache for show: " + name)
            mapped[dbData.mapped_series_provider_id.name] = dbData.mapped_series_id
            return mapped
    else:
        for mapped_series_provider_id in SeriesProviderID:
            if mapped_series_provider_id == series_provider_id:
                mapped[mapped_series_provider_id.name] = series_id
                continue

            mapped_series_provider = sickrage.app.series_provider[mapped_series_provider_id]

            mapped_show = mapped_series_provider.search(name)
            if not mapped_show:
                continue

            if mapped_show and len(mapped_show) == 1:
                sickrage.app.log.debug(f"Mapping {sickrage.app.series_providers[series_provider_id].name} -> {mapped_series_provider} for show: {name}")

                mapped[mapped_series_provider_id.name] = int(mapped_show['id'])

                sickrage.app.log.debug("Adding series_provider_id mapping to DB for show: " + name)

                try:
                    session.query(MainDB.SeriesProviderMapping).filter_by(series_id=series_id, series_provider_id=series_provider_id,
                                                                          mapped_series_id=int(mapped_show['id'])).one()
                except orm.exc.NoResultFound:
                    session.add(MainDB.SeriesProviderMapping(**{
                        'series_id': series_id,
                        'series_provider_id': series_provider_id,
                        'mapped_series_id': int(mapped_show['id']),
                        'mapped_series_provider_id': mapped_series_provider_id['id']
                    }))
                    session.commit()

    return mapped


def search_series_provider_for_series_id(show_name, series_provider_id):
    """
    Contacts series provider to check for information on shows by series name to retrieve series id

    :param show_name: Name of show
    :param series_provider_id: series provider id
    :return:
    """

    show_name = re.sub('[. -]', ' ', show_name)

    series_provider = sickrage.app.series_providers[series_provider_id]

    # Query series provider for search term and build the list of results
    sickrage.app.log.debug("Trying to find show ID for show {} on series provider {}".format(show_name, series_provider.name))

    series_provider_data = series_provider.search(show_name)
    if not series_provider_data:
        return

    # try to pick a show that's in my show list
    for series in series_provider_data:
        series_id = series.get('id', None)
        if not series_id:
            continue

        if find_show(int(series_id), series_provider_id):
            return series_id

    return series_provider_data[0].get('id', None)
