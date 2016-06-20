# Author: Tyler Fenby <tylerfenby@gmail.com>
# URL: http://github.com/SiCKRAGETV/SickRage/
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

from sickrage.core.common import Quality
from sickrage.core.databases import Connection, SchemaUpgrade


class FailedDB(Connection):
    def __init__(self, filename='failed.db', suffix=None, row_type=None):
        super(FailedDB, self).__init__(filename, suffix, row_type)

    # Add new migrations at the bottom of the list; subclass the previous migration.
    class InitialSchema(SchemaUpgrade):

        def __init__(self, filename='failed.db', suffix=None, row_type=None):
            super(FailedDB.InitialSchema, self).__init__(filename, suffix, row_type)

        def test(self):
            return self.hasTable('db_version')

        def execute(self, **kwargs):
            queries = [
                ('CREATE TABLE failed (release TEXT, size NUMERIC, provider TEXT);',),
                ('CREATE TABLE history (date NUMERIC, size NUMERIC, release TEXT, provider TEXT, '
                 'old_status NUMERIC DEFAULT 0, showid NUMERIC DEFAULT -1, season NUMERIC DEFAULT -1, '
                 'episode NUMERIC DEFAULT -1);',),
                ('CREATE TABLE db_version (db_version INTEGER);',),
                ('INSERT INTO db_version (db_version) VALUES (1);',),
            ]
            for query in queries:
                if len(query) == 1:
                    self.action(query[0])
                else:
                    self.action(query[0], query[1:])

    class SizeAndProvider(InitialSchema):
        def test(self):
            return self.hasColumn('failed', 'size') and self.hasColumn('failed', 'provider')

        def execute(self, **kwargs):
            self.addColumn('failed', 'size', 'NUMERIC')
            self.addColumn('failed', 'provider', 'TEXT', '')

    class History(SizeAndProvider):
        """Snatch history that can't be modified by the user"""

        def test(self):
            return self.hasTable('history')

        def execute(self, **kwargs):
            self.action('CREATE TABLE history (date NUMERIC, ' +
                        'size NUMERIC, release TEXT, provider TEXT);')

    class HistoryStatus(History):
        """Store episode status before snatch to revert to if necessary"""

        def test(self):
            return self.hasColumn('history', 'old_status')

        def execute(self, **kwargs):
            self.addColumn('history', 'old_status', 'NUMERIC', Quality.NONE)
            self.addColumn('history', 'showid', 'NUMERIC', '-1')
            self.addColumn('history', 'season', 'NUMERIC', '-1')
            self.addColumn('history', 'episode', 'NUMERIC', '-1')
