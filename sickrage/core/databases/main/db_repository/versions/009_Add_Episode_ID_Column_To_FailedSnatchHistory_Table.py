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

from sqlalchemy import *


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    failed_snatch_history = Table('failed_snatch_history', meta, autoload=True)
    if not hasattr(failed_snatch_history.c, 'episode_id'):
        episode_id = Column('episode_id', Integer, default=0)
        episode_id.create(failed_snatch_history)
        failed_snatch_history.c.season.drop()
        failed_snatch_history.c.episode.drop()
        failed_snatch_history.drop()
        failed_snatch_history.create()


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    failed_snatch_history = Table('failed_snatch_history', meta, autoload=True)
    if hasattr(failed_snatch_history.c, 'episode_id'):
        season = Column('season', Integer, default=0)
        episode = Column('episode', Integer, default=0)
        failed_snatch_history.c.episode_id.drop()
        season.create(failed_snatch_history)
        episode.create(failed_snatch_history)
        failed_snatch_history.drop()
        failed_snatch_history.create()
