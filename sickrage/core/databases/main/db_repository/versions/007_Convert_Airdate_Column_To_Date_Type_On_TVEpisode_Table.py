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

import datetime

from sqlalchemy import *


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    tv_episodes = Table('tv_episodes', meta, autoload=True)

    tv_episodes.c.airdate.alter(type=String(32))

    with migrate_engine.begin() as conn:
        for row in migrate_engine.execute(tv_episodes.select()):
            conn.execute(tv_episodes.update().where(tv_episodes.c.indexer_id == row.indexer_id).values(airdate=datetime.date.fromordinal(int(row.airdate))))

    tv_episodes.c.airdate.alter(type=Date)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    tv_episodes = Table('tv_episodes', meta, autoload=True)

    tv_episodes.c.airdate.alter(type=String(32))

    with migrate_engine.begin() as conn:
        for row in migrate_engine.execute(tv_episodes.select()):
            conn.execute(tv_episodes.update().where(tv_episodes.c.indexer_id == row.indexer_id).values(airdate=str(row.airdate.toordinal())))

    tv_episodes.c.airdate.alter(type=Integer)
