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
from sqlalchemy import orm

import sickrage
from sickrage.core.databases.main import MainDB
from sickrage.indexers import IndexerApi, ShowListUI


def map_indexers(indexer, indexer_id, name):
    session = sickrage.app.main_db.session()

    mapped = {}

    # init mapped indexers object
    for mindexer in IndexerApi().indexers:
        mapped[mindexer] = indexer_id if int(mindexer) == int(indexer) else 0

    # for each mapped entry
    for dbData in session.query(MainDB.IndexerMapping).filter_by(indexer_id=indexer_id, indexer=indexer):
        # Check if its mapped with both tvdb and tvrage.
        if len([i for i in dbData if i is not None]) >= 4:
            sickrage.app.log.debug("Found indexer mapping in cache for show: " + name)
            mapped[int(dbData.mindexer)] = int(dbData.mindexer_id)
            return mapped
    else:
        for mindexer in IndexerApi().indexers:
            if mindexer == indexer:
                mapped[mindexer] = indexer_id
                continue

            indexer_api_parms = IndexerApi(mindexer).api_params.copy()
            indexer_api_parms['custom_ui'] = ShowListUI

            t = IndexerApi(mindexer).indexer(**indexer_api_parms)
            mapped_show = t[name]
            if not mapped_show:
                continue

            if mapped_show and len(mapped_show) == 1:
                sickrage.app.log.debug("Mapping " + IndexerApi(indexer).name + "->" + IndexerApi(mindexer).name + " for show: " + name)

                mapped[mindexer] = int(mapped_show['id'])

                sickrage.app.log.debug("Adding indexer mapping to DB for show: " + name)

                try:
                    session.query(MainDB.IndexerMapping).filter_by(indexer_id=indexer_id, indexer=indexer, mindexer_id=int(mapped_show['id'])).one()
                except orm.exc.NoResultFound:
                    session.add(MainDB.IndexerMapping(**{
                        'indexer_id': indexer_id,
                        'indexer': indexer,
                        'mindexer_id': int(mapped_show['id']),
                        'mindexer': mindexer
                    }))
                    session.commit()

    return mapped