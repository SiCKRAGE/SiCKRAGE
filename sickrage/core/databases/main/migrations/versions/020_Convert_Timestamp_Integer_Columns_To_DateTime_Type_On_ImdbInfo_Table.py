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

Revision ID: 20
Revises:
Create Date: 2017-12-29 14:39:27.854291

"""
import datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '20'
down_revision = '19'


def upgrade():
    conn = op.get_bind()
    meta = sa.MetaData(bind=conn)
    imdb_info = sa.Table('imdb_info', meta, autoload=True)

    with op.get_context().begin_transaction():
        for row in conn.execute(imdb_info.select()):
            conn.execute(f'UPDATE imdb_info SET last_update = "" WHERE imdb_info.indexer_id = {row.indexer_id}')

    with op.batch_alter_table("imdb_info") as batch_op:
        batch_op.alter_column('last_update', type_=sa.DateTime(timezone=True))

    with op.get_context().begin_transaction():
        for row in conn.execute(imdb_info.select()):
            conn.execute(f'UPDATE imdb_info SET last_update = {sa.func.current_timestamp()} WHERE imdb_info.indexer_id = {row.indexer_id}')

def downgrade():
    pass
