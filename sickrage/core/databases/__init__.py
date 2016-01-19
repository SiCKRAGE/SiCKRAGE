# Author: echel0n <sickrage.tv@gmail.com>
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

__all__ = ["main_db", "cache_db", "failed_db"]

import os

import re
import sqlite3
import threading
from contextlib import contextmanager
from tornado import gen

import sickrage
from sickrage.core.helpers import backupVersionedFile, restoreVersionedFile


def prettyName(class_name):
    return ' '.join([x.group() for x in re.finditer("([A-Z])([a-z0-9]+)", class_name)])


def dbFilename(filename=None, suffix=None):
    """
    @param filename: The sqlite database filename to use. If not specified,
                     will be made to be sickrage.db
    @param suffix: The suffix to append to the filename. A '.' will be added
                   automatically, i.e. suffix='v0' will make dbfile.db.v0
    @return: the correct location of the database file.
    """

    filename = filename or 'sickrage.db'

    if suffix:
        filename = filename + ".{}".format(suffix)
    return os.path.join(sickrage.DATA_DIR, filename)


class Connection(object):
    def __init__(self, filename=None, suffix=None, row_type=None):
        self.filename = dbFilename(filename, suffix)
        self.row_type = row_type or sqlite3.Row
        self.lock = threading.Lock()

    @contextmanager
    def connection(self):
        _connection = sqlite3.connect(self.filename, timeout=20, check_same_thread=False, isolation_level=None)
        _connection.row_factory = (self._dict_factory, self.row_type)[self.row_type != 'dict']
        try:
            yield _connection
        finally:
            _connection.commit()
            _connection.close()

    @contextmanager
    def _cursor(self):
        with self.lock, self.connection() as _connection:
            _cursor = _connection.cursor()

            try:
                yield _cursor
            finally:
                _cursor.close()

    def _execute(self, query, *args, **kwargs):
        with self._cursor() as cursor:
            result = []

            options = {'fetchall': kwargs.pop('fetchall', False),
                       'fetchone': kwargs.pop('fetchone', False)}

            args = reduce(lambda l, i: l + type(l)(i) if isinstance(i, (list, tuple)) else l + [i], args, []),

            attempt = 0
            while attempt < 5:
                try:
                    if isinstance(query, list):
                        if len(query) == 1:
                            map(lambda x: cursor.execute(*x), zip(*[iter(query)] * 2))
                        else:
                            map(lambda x: cursor.execute(*x), query)
                    else:
                        if len(args):
                            cursor.execute(query, *args)
                        else:
                            cursor.execute(query)

                    if options['fetchall']:
                        result += cursor.fetchall()
                    elif options['fetchone']:
                        result += cursor.fetchone()
                    else:
                        result = cursor
                        if not result:
                            result = cursor.fetchall()

                except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                    sickrage.LOGGER.error("DB error: {}".format(e))
                    gen.sleep(1)
                    attempt += 1

                    try:
                        cursor.connection.rollback()
                    except:
                        pass
                except Exception as e:
                    sickrage.LOGGER.error("DB error: {}".format(e))
                finally:
                    return result

    def checkDBVersion(self):
        """
        Fetch database version

        :return: Integer inidicating current DB version
        """
        try:
            if self.hasTable('db_version'):
                return self.selectOne("SELECT db_version FROM db_version")[0]
        except:
            pass

        return 0

    def mass_action(self, querylist, *args, **kwargs):
        """
        Execute multiple queries

        :param querylist: list of queries
        :return: list of results
        """

        sqlResult = self._execute(querylist, *args, **kwargs)
        sickrage.LOGGER.log(sickrage.LOGGER.logLevels[b'DB'],
                            "Transaction with {} queries executed of ".format(len(querylist)))

        return sqlResult

    def action(self, query, *args, **kwargs):
        """
        Execute single query

        :rtype: query results
        :param query: Query string
        """

        sickrage.LOGGER.log(sickrage.LOGGER.logLevels[b'DB'],
                            "{}: {} with args {}".format(self.filename, query, args))

        return self._execute(query, *args, **kwargs)

    def select(self, query, *args, **kwargs):
        """
        Perform single select query on database

        :param query: query string
        :param args:  arguments to query string
        :return: query results
        """
        return self.action(query, *args, **{'fetchall': kwargs.pop('fetchall', True)})

    def selectOne(self, query, *args, **kwargs):
        """
        Perform single select query on database, returning one result

        :param query: query string
        :param args: arguments to query string
        :return: query results
        """
        return self.action(query, *args, **{'fetchone': kwargs.pop('fetchone', True)})

    def upsert(self, tableName, valueDict, keyDict):
        """
        Update values, or if no updates done, insert values
        TODO: Make this return true/false on success/error

        :param tableName: table to update/insert
        :param valueDict: values in table to update/insert
        :param keyDict:  columns in table to update
        """

        genParams = lambda myDict: [x + " = ?" for x in myDict.keys()]

        query = "UPDATE [" + tableName + "] SET " + ", ".join(genParams(valueDict)) + " WHERE " + " AND ".join(
                genParams(keyDict))

        if not self.action(query, valueDict.values() + keyDict.values()).rowcount > 0:
            query = "INSERT INTO [" + tableName + "] (" + ", ".join(valueDict.keys() + keyDict.keys()) + ")" + \
                    " VALUES (" + ", ".join(["?"] * len(valueDict.keys() + keyDict.keys())) + ")"
            self.action(query, valueDict.values() + keyDict.values())

    def tableInfo(self, tableName):
        """
        Return information on a database table

        :param tableName: name of table
        :return: array of name/type info
        """
        columns = {}

        sqlResult = self.select("PRAGMA table_info(`{}`)".format(tableName))

        for column in sqlResult:
            columns[column[b'name']] = {'type': column[b'type']}

        return columns

    def _dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def hasTable(self, tableName):
        """
        Check if a table exists in database

        :param tableName: table name to check
        :return: True if table exists, False if it does not
        """
        return len(self.select("SELECT 1 FROM sqlite_master WHERE name = ?;", tableName)) > 0

    def hasColumn(self, tableName, column):
        """
        Check if a table has a column

        :param tableName: Table to check
        :param column: Column to check for
        :return: True if column exists, False if it does not
        """
        return column in self.tableInfo(tableName)

    def addColumn(self, table, column, type="NUMERIC", default=0):
        """
        Adds a column to a table, default column type is NUMERIC
        TODO: Make this return true/false on success/failure

        :param table: Table to add column too
        :param column: Column name to add
        :param type: Column type to add
        :param default: Default value for column
        """
        self.action("ALTER TABLE [%s] ADD %s %s" % (table, column, type))
        self.action("UPDATE [%s] SET %s = ?" % (table, column), default)


class SchemaUpgrade(Connection):
    def __init__(self, filename=None, suffix=None, row_type=None):
        super(SchemaUpgrade, self).__init__(filename, suffix, row_type)

    def hasTable(self, tableName):
        return len(self.select("SELECT 1 FROM sqlite_master WHERE name = ?;", [tableName],)) > 0

    def hasColumn(self, tableName, column):
        return column in self.tableInfo(tableName)

    def addColumn(self, table, column, type="NUMERIC", default=0):
        self.action("ALTER TABLE [{}] ADD {} {}".format(table, column, type))
        self.action("UPDATE [{}] SET {} = ?".format(table, column), default)

    def incDBVersion(self):
        new_version = self.checkDBVersion() + 1
        self.action("UPDATE db_version SET db_version = ?", [new_version],)
        return new_version

    def upgrade(self):
        """
        Perform database upgrade and provide logging
        """

        def _processUpgrade(upgradeClass, version):
            name = prettyName(upgradeClass.__name__)

            while (True):
                sickrage.LOGGER.debug("Checking {} database structure".format(name))

                try:
                    instance = upgradeClass()

                    if not instance.test():
                        sickrage.LOGGER.debug("Database upgrade required: {}".format(name))
                        instance.execute()
                        sickrage.LOGGER.debug("{} upgrade completed".format(name))
                    else:
                        sickrage.LOGGER.debug("{} upgrade not required".format(name))

                    return True
                except sqlite3.DatabaseError:
                    if not self.restore(version):
                        break

        for klass in self.get_subclasses():
            _processUpgrade(klass, self.checkDBVersion())

    def restore(self, version):
        """
        Restores a database to a previous version (backup file of version must still exist)

        :param version: Version to restore to
        :return: True if restore succeeds, False if it fails
        """

        sickrage.LOGGER.info("Restoring database before trying upgrade again")
        if not restoreVersionedFile(dbFilename(suffix='v' + str(version)), version):
            sickrage.LOGGER.info("Database restore failed, abort upgrading database")
            return False
        return True

    def backup(self, version):
        sickrage.LOGGER.info("Backing up database before upgrade")
        if not backupVersionedFile(dbFilename(), version):
            sickrage.LOGGER.log_error_and_exit("Database backup failed, abort upgrading database")
        else:
            sickrage.LOGGER.info("Proceeding with upgrade")

    @classmethod
    def get_subclasses(cls):
        yield cls
        if cls.__subclasses__():
            for sub in cls.__subclasses__():
                for s in sub.get_subclasses():
                    yield s
