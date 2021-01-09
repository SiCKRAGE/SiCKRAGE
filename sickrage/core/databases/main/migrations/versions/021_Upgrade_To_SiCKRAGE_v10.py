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

"""Initial migration

Revision ID: 21
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""

import datetime
import enum

import sqlalchemy as sa
from alembic import op

from sickrage.core.common import Qualities, EpisodeStatus
from sickrage.core.databases import IntFlag
from sickrage.core.databases.main import MainDB

# revision identifiers, used by Alembic.
revision = '21'
down_revision = '20'


class SeriesProviderID(enum.Enum):
    THETVDB = 1


def upgrade():
    conn = op.get_bind()
    maindb_meta = MainDB.base.metadata
    maindb_meta.bind = conn

    op.alter_column('tv_shows', 'indexer_id', new_column_name='series_id')
    op.alter_column('tv_shows', 'indexer', new_column_name='series_provider_id')
    op.alter_column('tv_shows', 'dvdorder', new_column_name='dvd_order')
    op.alter_column('tv_episodes', 'showid', new_column_name='series_id')
    op.alter_column('tv_episodes', 'indexer_id', new_column_name='episode_id')
    op.alter_column('tv_episodes', 'indexer', new_column_name='series_provider_id')
    op.alter_column('imdb_info', 'indexer_id', new_column_name='series_id')

    for item in SeriesProviderID:
        conn.execute(f'UPDATE tv_shows SET series_provider_id = "{item.name}" WHERE series_provider_id = {item.value}')
        conn.execute(f'UPDATE tv_episodes SET series_provider_id = "{item.name}" WHERE series_provider_id = {item.value}')

    for item in EpisodeStatus:
        conn.execute(f'UPDATE tv_shows SET default_ep_status = "{item.name}" WHERE default_ep_status = {item.value}')
        conn.execute(f'UPDATE tv_episodes SET status = "{item.name}" WHERE status = {item.value}')

    with op.batch_alter_table('tv_shows') as batch_op:
        batch_op.alter_column('series_provider_id', type_=sa.Enum(SeriesProviderID))
        batch_op.alter_column('default_ep_status', type_=sa.Enum(EpisodeStatus))
        batch_op.alter_column('quality', type_=IntFlag(Qualities))

    with op.batch_alter_table('tv_episodes') as batch_op:
        batch_op.alter_column('series_provider_id', type_=sa.Enum(SeriesProviderID))
        batch_op.alter_column('status', type_=sa.Enum(EpisodeStatus))

    tv_episodes_results = []
    for x in conn.execute('SELECT * FROM tv_episodes'):
        x = dict(x)

        if 'airdate' in x:
            try:
                x['airdate'] = datetime.datetime.strptime(x['airdate'], '%Y-%m-%d')
            except ValueError:
                continue

        if 'subtitles_lastsearch' in x:
            try:
                x['subtitles_lastsearch'] = datetime.datetime.now()
            except ValueError:
                continue

        tv_episodes_results.append(x)

    blacklist_results = []
    for x in conn.execute('SELECT * FROM blacklist'):
        x = dict(x)

        x['series_provider_id'] = SeriesProviderID.THETVDB

        blacklist_results.append(x)

    whitelist_results = []
    for x in conn.execute('SELECT * FROM whitelist'):
        x = dict(x)

        x['series_provider_id'] = SeriesProviderID.THETVDB

        whitelist_results.append(x)

    imdb_info_results = []
    for x in conn.execute('SELECT * FROM imdb_info'):
        x = dict(x)

        x['last_update'] = datetime.datetime.now()

        imdb_info_results.append(x)

    op.drop_table('indexer_mapping')
    op.drop_table('tv_episodes')
    op.drop_table('imdb_info')
    op.drop_table('blacklist')
    op.drop_table('whitelist')
    op.drop_table('history')
    op.drop_table('failed_snatch_history')
    op.drop_table('failed_snatches')

    sa.Table('series_provider_mapping', maindb_meta, autoload=True).create()
    sa.Table('tv_episodes', maindb_meta, autoload=True).create()
    sa.Table('imdb_info', maindb_meta, autoload=True).create()
    sa.Table('blacklist', maindb_meta, autoload=True).create()
    sa.Table('whitelist', maindb_meta, autoload=True).create()
    sa.Table('history', maindb_meta, autoload=True).create()
    sa.Table('failed_snatch_history', maindb_meta, autoload=True).create()
    sa.Table('failed_snatches', maindb_meta, autoload=True).create()

    tv_episodes = sa.Table('tv_episodes', maindb_meta, autoload=True)
    imdb_info = sa.Table('imdb_info', maindb_meta, autoload=True)
    blacklist = sa.Table('blacklist', maindb_meta, autoload=True)
    whitelist = sa.Table('whitelist', maindb_meta, autoload=True)

    op.bulk_insert(tv_episodes, tv_episodes_results)
    op.bulk_insert(imdb_info, imdb_info_results)
    op.bulk_insert(blacklist, blacklist_results)
    op.bulk_insert(whitelist, whitelist_results)


def downgrade():
    pass
