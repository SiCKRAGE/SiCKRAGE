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
import json
import os
from json import JSONDecodeError

from sqlalchemy import *

import sickrage


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    oauth2_token = Table('oauth2_token', meta, autoload=True)
    token_file = os.path.abspath(os.path.join(sickrage.app.data_dir, 'token.json'))

    if os.path.exists(token_file):
        with open(token_file, 'r') as fd:
            try:
                token = json.load(fd)
                migrate_engine.execute(oauth2_token.insert().values(
                    access_token=token['access_token'],
                    refresh_token=token['refresh_token'],
                    expires_in=token['expires_in'],
                    expires_at=token['expires_at'],
                    scope=' '.join(token['scope']) if isinstance(token['scope'], list) else token['scope']
                ))
            except JSONDecodeError:
                pass

        os.remove(token_file)


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pass
