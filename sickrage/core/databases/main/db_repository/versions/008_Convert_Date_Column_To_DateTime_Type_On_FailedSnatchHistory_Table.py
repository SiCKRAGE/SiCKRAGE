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
    failed_snatch_history = Table('failed_snatch_history', meta, autoload=True)

    failed_snatch_history.c.date.alter(type=String(32))

    date_format = '%Y%m%d%H%M%S'
    with migrate_engine.begin() as conn:
        for row in migrate_engine.execute(failed_snatch_history.select()):
            conn.execute(failed_snatch_history.update().where(failed_snatch_history.c.id == row.id).values(
                date=datetime.datetime.strptime(str(row.date), date_format)))

    failed_snatch_history.c.date.alter(type=DateTime)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    failed_snatch_history = Table('failed_snatch_history', meta, autoload=True)

    failed_snatch_history.c.date.alter(type=String(32))

    with migrate_engine.begin() as conn:
        for row in migrate_engine.execute(failed_snatch_history.select()):
            conn.execute(failed_snatch_history.update().where(failed_snatch_history.c.id == row.id).values(airdate=str(row.date.toordinal())))

    failed_snatch_history.c.date.alter(type=Integer)
