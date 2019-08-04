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
    providers = Table('providers', meta, autoload=True)

    if hasattr(providers.c, 'indexer_id'):
        providers.c.indexer_id.alter(name='series_id')


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    providers = Table('providers', meta, autoload=True)

    if hasattr(providers.c, 'series_id'):
        providers.c.series_id.alter(name='indexer_id')
