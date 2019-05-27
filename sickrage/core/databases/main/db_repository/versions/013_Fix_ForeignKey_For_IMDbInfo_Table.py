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

from migrate import *
from sqlalchemy import MetaData, Table


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    tv_shows = Table('tv_shows', meta, autoload=True)
    imdb_info = Table('imdb_info', meta, autoload=True)

    uc = UniqueConstraint(tv_shows.c.imdb_id)
    uc.create()

    fkc = ForeignKeyConstraint(columns=[imdb_info.c.indexer_id], refcolumns=[tv_shows.c.indexer_id])
    fkc.drop()

    fkc = ForeignKeyConstraint(columns=[imdb_info.c.imdb_id], refcolumns=[tv_shows.c.imdb_id])
    fkc.create()


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    tv_shows = Table('tv_shows', meta, autoload=True)
    imdb_info = Table('imdb_info', meta, autoload=True)

    uc = UniqueConstraint(tv_shows.c.imdb_id)
    uc.drop()

    fkc = ForeignKeyConstraint(columns=[imdb_info.c.imdb_id], refcolumns=[tv_shows.c.imdb_id])
    fkc.drop()

    fkc = ForeignKeyConstraint(columns=[imdb_info.c.indexer_id], refcolumns=[tv_shows.c.indexer_id])
    fkc.create()
