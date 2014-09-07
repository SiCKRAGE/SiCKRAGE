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

import datetime

import sickbeard
import os.path

from sickbeard import db, helpers, logger


MIN_DB_VERSION = 1  # oldest db version we support migrating from
MAX_DB_VERSION = 2

def backupDatabase(version):
    logger.log(u"Backing up database before upgrade")
    if not helpers.backupVersionedFile(db.dbFilename(filename="anidb.db"), version):
        logger.log_error_and_exit(u"Database backup failed, abort upgrading database")
    else:
        logger.log(u"Proceeding with upgrade")

# ======================
# = Main DB Migrations =
# ======================
# Add new migrations at the bottom of the list; subclass the previous migration.

class InitialSchema(db.SchemaUpgrade):
    def test(self):
        return self.hasTable("db_version")

    def execute(self):
        if not self.hasTable("db_version"):
            queries = [
                "CREATE TABLE db_version (db_version INTEGER);",
                "CREATE TABLE file_response (time INTEGER, fid INTEGER PRIMARY KEY, aid INTEGER, eid INTEGER, gid INTEGER, state INTEGER, file_size INTEGER, ed2k TEXT, crc32 TEXT, source TEXT, video_resolution TEXT, epno TEXT);",
                "INSERT INTO db_version (db_version) VALUES (1);"
            ]
            for query in queries:
                self.connection.action(query)

        else:
            cur_db_version = self.checkDBVersion()

            if cur_db_version < MIN_DB_VERSION:
                logger.log_error_and_exit(u"Your database version (" + str(
                    cur_db_version) + ") is too old to migrate from what this version of SickRage supports (" + \
                                          str(MIN_DB_VERSION) + ").\n" + \
                                          "Upgrade using a previous version (tag) build 496 to build 501 of SickRage first or remove database file to begin fresh."
                )

            if cur_db_version > MAX_DB_VERSION:
                logger.log_error_and_exit(u"Your database version (" + str(
                    cur_db_version) + ") has been incremented past what this version of SickRage supports (" + \
                                          str(MAX_DB_VERSION) + ").\n" + \
                                          "If you have used other forks of SickRage, your database may be unusable due to their modifications."
                )


class AddGroupTable(InitialSchema):
    def test(self):
        return self.checkDBVersion() > 1

    def execute(self):
        backupDatabase(1)

        logger.log(u"Adding group table")
        self.connection.action("CREATE TABLE group_response (time INTEGER , gid INTEGER PRIMARY KEY, gname TEXT, gshortname TEXT)")

        self.incDBVersion()