# -*- coding: utf-8 -*-
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
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

import re
import six
import time
import os.path
import sqlite3
import threading
import sickbeard

import logging
from sickrage.helper.encoding import ek, uu
from sickrage.helper.exceptions import ex


def dbFilename(filename="sickbeard.db", suffix=None):
    """
    @param filename: The sqlite database filename to use. If not specified,
                     will be made to be sickbeard.db
    @param suffix: The suffix to append to the filename. A '.' will be added
                   automatically, i.e. suffix='v0' will make dbfile.db.v0
    @return: the correct location of the database file.
    """
    if suffix:
        filename = "%s.%s" % (filename, suffix)
    return ek(os.path.join, sickbeard.DATA_DIR, filename)


class Cursor:
    def __init__(self, cursor):
        self.cursor = cursor
        self.lock = threading.Lock()

    def _execute(self, query, args):
        try:
            if not args:
                return self.cursor.execute(query)
            return self.cursor.execute(query, args)
        except:
            raise

    def execute(self, query, args, fetchall=False, fetchone=False):
        with self.lock:
            try:
                if fetchall:
                    return self._execute(query, args).fetchall()
                elif fetchone:
                    return self._execute(query, args).fetchone()
                else:
                    return self._execute(query, args)
            except:
                raise

    @property
    def rowcount(self):
        with self.lock:
            return self.cursor.rowcount


class DBConnection(object):
    def __init__(self, filename="sickbeard.db", suffix=None, row_type=None, *args, **kwargs):
        self.filename = filename
        self.suffix = suffix
        self.row_type = row_type
        self.connection = None
        self.cursor = None
        self.lock = threading.Lock()

        try:
            self.open()
        except Exception as e:
            logging.error("DB error: {}".format(ex(e)))

    def open(self):
        try:
            if not self.connection:
                self.connection = sqlite3.connect(dbFilename(self.filename, self.suffix), timeout=20,
                                                  check_same_thread=False, isolation_level=None)
                self.connection.row_factory = self._dict_factory if self.row_type == "dict" else sqlite3.Row
                self.cursor = Cursor(self.connection.cursor())
        except:
            raise

    def close(self):
        self.commit()

    def execute(self, query, args=None, fetchall=False, fetchone=False):
        self.open()
        try:
            return self.cursor.execute(query, args, fetchall=fetchall, fetchone=fetchone)
        except:
            self.commit()

    def commit(self):
        if self.connection:
            try:
                self.connection.commit()
            finally:
                self.connection.close()
                self.connection = None

    def checkDBVersion(self):
        """
        Fetch database version

        :return: Integer inidicating current DB version
        """
        result = None

        try:
            if self.hasTable('db_version'):
                return self.select("SELECT db_version FROM db_version")
        except:
            pass

        return 0

    def mass_action(self, querylist=[], logTransaction=False, fetchall=False):
        """
        Execute multiple queries

        :param querylist: list of queries
        :param logTransaction: Boolean to wrap all in one transaction
        :param fetchall: Boolean, when using a select query force returning all results
        :return: list of results
        """

        with self.lock:
            querylist = [i for i in querylist if i is not None and len(i)]

            sqlResult = []
            attempt = 0

            while attempt < 5:
                try:
                    for qu in querylist:
                        if len(qu) == 1:
                            if logTransaction:
                                logging.debug(qu[0])
                            sqlResult.append(self.execute(qu[0], fetchall=fetchall))
                        elif len(qu) > 1:
                            if logTransaction:
                                logging.debug(qu[0] + " with args " + str(qu[1]))
                            sqlResult.append(self.execute(qu[0], qu[1], fetchall=fetchall))

                    logging.debug("Transaction with " + str(len(querylist)) + " queries executed")
                except sqlite3.OperationalError as e:
                    sqlResult = []
                    if self.connection:
                        self.connection.rollback()
                    if "unable to open database file" in e.args[0] or "database is locked" in e.args[0]:
                        logging.warning("DB error: {}".format(ex(e)))
                        attempt += 1
                        time.sleep(1)
                    else:
                        logging.error("DB error: {}".format(ex(e)))
                        raise
                except sqlite3.DatabaseError as e:
                    sqlResult = []
                    if self.connection:
                        self.connection.rollback()
                    logging.error("Fatal error executing query: {}".format(ex(e)))
                    raise
                finally:
                    self.commit()
                    break

            return sqlResult

    def action(self, query, args=None, fetchall=False, fetchone=False):
        """
        Execute single query

        :param query: Query string
        :param args: Arguments to query string
        :param fetchall: Boolean to indicate all results must be fetched
        :param fetchone: Boolean to indicate one result must be fetched (to walk results for instance)
        :return: query results
        """

        with self.lock:
            if not query:
                return

            sqlResult = None
            attempt = 0

            while attempt < 5:
                try:
                    if not args:
                        logging.db(self.filename + ": " + query)
                    else:
                        logging.db(self.filename + ": " + query + " with args " + str(args))

                    sqlResult = self.execute(query, args, fetchall=fetchall, fetchone=fetchone)
                except sqlite3.OperationalError as e:
                    if "unable to open database file" in e.args[0] or "database is locked" in e.args[0]:
                        logging.warning("DB error: {}".format(ex(e)))
                        attempt += 1
                        time.sleep(1)
                    else:
                        logging.error("DB error: {}".format(ex(e)))
                        raise
                except sqlite3.DatabaseError as e:
                    logging.error("Fatal error executing query: {}".format(ex(e)))
                    raise
                finally:
                    self.commit()
                    break

            return sqlResult

    def select(self, query, args=None):
        """
        Perform single select query on database

        :param query: query string
        :param args:  arguments to query string
        :return: query results
        """

        sqlResults = self.action(query, args, fetchall=True)

        if sqlResults == None:
            return []

        return sqlResults

    def selectOne(self, query, args=None):
        """
        Perform single select query on database, returning one result

        :param query: query string
        :param args: arguments to query string
        :return: query results
        """
        sqlResults = self.action(query, args, fetchone=True)

        if sqlResults == None:
            return []

        return sqlResults

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

        self.action(query, valueDict.values() + keyDict.values())

        if not self.cursor.rowcount > 0:
            query = "INSERT INTO [" + tableName + "] (" + ", ".join(valueDict.keys() + keyDict.keys()) + ")" + \
                    " VALUES (" + ", ".join(["?"] * len(valueDict.keys() + keyDict.keys())) + ")"
            self.action(query, valueDict.values() + keyDict.values())

    def tableInfo(self, tableName):
        """
        Return information on a database table

        :param tableName: name of table
        :return: array of name/type info
        """
        sqlResult = self.select("PRAGMA table_info(`%s`)" % tableName)
        columns = {}
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
        return len(self.select("SELECT 1 FROM sqlite_master WHERE name = ?;", (tableName,))) > 0

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
        self.action("UPDATE [%s] SET %s = ?" % (table, column), (default,))


def sanityCheckDatabase(connection, sanity_check):
    sanity_check(connection).check()


class DBSanityCheck(object):
    def __init__(self, connection):
        self.connection = connection

    def check(self):
        pass


# ===============
# = Upgrade API =
# ===============

def upgradeDatabase(connection, schema):
    """
    Perform database upgrade and provide logging

    :param connection: Existing DB Connection to use
    :param schema: New schema to upgrade to
    """

    def _processUpgrade(connection, upgradeClass):
        while (True):
            version = connection.checkDBVersion()

            logging.debug("Checking database structure..." + connection.filename)

            try:
                instance = upgradeClass(connection)

                if not instance.test():
                    logging.debug("Database upgrade required: " + prettyName(upgradeClass.__name__))
                    instance.execute()
                    logging.debug(upgradeClass.__name__ + " upgrade completed")
                else:
                    logging.debug(upgradeClass.__name__ + " upgrade not required")

                return True
            except sqlite3.DatabaseError, e:
                if not restoreDatabase(version):
                    break

    if _processUpgrade(connection, schema):
        for upgradeSubClass in schema.__subclasses__():
            _processUpgrade(connection, upgradeSubClass)


def prettyName(class_name):
    return ' '.join([x.group() for x in re.finditer("([A-Z])([a-z0-9]+)", class_name)])


def restoreDatabase(version):
    """
    Restores a database to a previous version (backup file of version must still exist)

    :param version: Version to restore to
    :return: True if restore succeeds, False if it fails
    """
    logging.info("Restoring database before trying upgrade again")
    if not sickbeard.helpers.restoreVersionedFile(dbFilename(suffix='v' + str(version)), version):
        logging.info("Database restore failed, abort upgrading database")
        return False
    return True


# Base migration class. All future DB changes should be subclassed from this class
class SchemaUpgrade(object):
    def __init__(self, connection):
        self.connection = connection

    def hasTable(self, tableName):
        return len(self.connection.select("SELECT 1 FROM sqlite_master WHERE name = ?;", (tableName,))) > 0

    def hasColumn(self, tableName, column):
        return column in self.connection.tableInfo(tableName)

    def addColumn(self, table, column, type="NUMERIC", default=0):
        self.connection.action("ALTER TABLE [%s] ADD %s %s" % (table, column, type))
        self.connection.action("UPDATE [%s] SET %s = ?" % (table, column), (default,))

    def checkDBVersion(self):
        return self.connection.checkDBVersion()

    def incDBVersion(self):
        new_version = self.checkDBVersion() + 1
        self.connection.action("UPDATE db_version SET db_version = ?", [new_version])
        return new_version
