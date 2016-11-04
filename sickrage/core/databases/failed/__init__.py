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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import os

import sickrage
from sickrage.core.databases import srDatabase
from sickrage.core.databases.failed.index import FailedIndex, HistoryIndex


class FailedDB(srDatabase):
    _indexes = {
        'failed': FailedIndex,
        'history': HistoryIndex,
    }

    _migrate_list = {
        'failed': ['release', 'size', 'provider'],
        'history': ['date', 'size', 'release', 'provider', 'old_status', 'showid', 'season', 'episode'],
    }

    def __init__(self, name='failed'):
        super(FailedDB, self).__init__(name)
        self.old_db_path = os.path.join(sickrage.DATA_DIR, 'failed.db')
