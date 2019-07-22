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

from migrate.changeset.constraint import PrimaryKeyConstraint
from sqlalchemy import MetaData, Table, String


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    last_search = Table('last_search', meta, autoload=True)

    with migrate_engine.begin() as conn:
        conn.execute(last_search.delete())

    last_search.c.provider.alter(type=String(32))
    primary_key = PrimaryKeyConstraint(last_search.c.provider)
    primary_key.create()
    last_search.c.id.drop()


def downgrade(migrate_engine):
    pass
