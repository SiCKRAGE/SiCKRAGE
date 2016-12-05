

# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from thetvdb.api import Tvdb

INDEXER_TVDB = 1
INDEXER_TVRAGE = 2  # Must keep

indexerConfig = {
    INDEXER_TVDB: {
        'id': INDEXER_TVDB,
        'name': 'theTVDB',
        'module': Tvdb,
        'api_params': {'apikey': 'F9C450E78D99172E',
                       'apitoken': '',
                       'language': 'en',
                       'useZip': True,
                       },
        'trakt_id': 'tvdb_id',
        'xem_origin': 'tvdb',
        'icon': 'thetvdb16.png',
        'scene_loc': 'http://sickragetv.github.io/scene_exceptions/thetvdb.txt',
        'show_url': 'http://thetvdb.com/?tab=series&id=',
        'base_url': 'http://thetvdb.com/api/F9C450E78D99172E/series/',
    }
}