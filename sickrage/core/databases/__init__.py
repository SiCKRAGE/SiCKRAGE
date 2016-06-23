# Author: echel0n <echel0n@sickrage.ca>
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

from Queue import Queue
from time import sleep

try:
    from futures import ThreadPoolExecutor
except ImportError:
    from concurrent.futures import ThreadPoolExecutor

__all__ = ["main_db", "cache_db", "failed_db"]

import os
import re
import sqlite3
import threading
from contextlib import contextmanager
from collections import defaultdict

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


class UniRow(sqlite3.Row):
    def __init__(self, *args, **kwargs):
        super(UniRow, self).__init__(*args, **kwargs)

    def __getitem__(self, y):
        return super(UniRow, self).__getitem__(str(y))


class Transaction(object):
    """A context manager for safe, concurrent access to the database.
    All SQL commands should be executed through a transaction.
    """

    def __init__(self, db):
        self.db = db

    def __enter__(self):
        """Begin a transaction. This transaction may be created while
        another is active in a different thread.
        """
        with self.db._tx_stack() as stack:
            first = not stack
            stack.append(self)
        if first:
            # Beginning a "root" transaction, which corresponds to an
            # SQLite transaction.
            self.db._db_lock.acquire()

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Complete a transaction. This must be the most recently
        entered but not yet exited transaction. If it is the last active
        transaction, the database updates are committed.
        """
        with self.db._tx_stack() as stack:
            assert stack.pop() is self
            empty = not stack
        if empty:
            self.db._db_lock.release()

    def query(self, query):
        """Execute an SQL statement with substitution values and return
        a list of rows from the database.
        """
        result = []
        with self.db._conn_cursor() as (conn, cursor):
            attempt = 0
            while attempt <= 5:
                attempt += 1

                try:
                    # execute query
                    cursor.execute(*query)

                    # get result
                    result = cursor.fetchall()
                except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                    conn.rollback()
                    sleep(1)
                except Exception as e:
                    sickrage.srCore.srLogger.error("QUERY: {} ERROR: {}".format(query, e.message))
                finally:
                    return result

    def upsert(self, tableName, valueDict, keyDict):
        """
        Update values, or if no updates done, insert values

        :param tableName: table to update/insert
        :param valueDict: values in table to update/insert
        :param keyDict:  columns in table to update
        """

        with self.db._conn_cursor() as (conn, cursor):
            # update existing row if exists
            genParams = lambda myDict: [x + " = ?" for x in myDict.keys()]
            query = ["UPDATE [" + tableName + "] SET " + ", ".join(
                genParams(valueDict)) + " WHERE " + " AND ".join(genParams(keyDict)),
                     valueDict.values() + keyDict.values()]

            cursor.execute(*query)
            if not conn.total_changes:
                # insert new row if update failed
                query = ["INSERT INTO [" + tableName + "] (" + ", ".join(
                    valueDict.keys() + keyDict.keys()) + ")" + " VALUES (" + ", ".join(
                    ["?"] * len(valueDict.keys() + keyDict.keys())) + ")", valueDict.values() + keyDict.values()]
                cursor.execute(*query)

            return (False, True)[conn.total_changes > 0]


class Connection(object):
    def __init__(self, filename=None, suffix=None, row_type=None, timeout=None):
        self.filename = dbFilename(filename, suffix)
        self.row_type = row_type or UniRow
        self._shared_map_lock = threading.Lock()
        self._db_lock = threading.Lock()
        self._connections = {}
        self._tx_stacks = defaultdict(list)
        self.last_id = 0
        self.timeout = timeout or 20

    @contextmanager
    def _conn(self):
        with self._shared_map_lock:
            thread_id = threading.current_thread().ident

            if thread_id not in self._connections:
                with sqlite3.connect(self.filename, timeout=self.timeout, check_same_thread=False) as conn:
                    conn.row_factory = (self._dict_factory, self.row_type)[self.row_type != 'dict']
                    conn.execute("PRAGMA journal_mode=WAL")
                    self._connections[thread_id] = conn

            # yield database connection
            try:
                yield self._connections[thread_id]
            finally:
                del self._connections[thread_id]

    @contextmanager
    def _conn_cursor(self):
        with self._conn() as conn:
            cursor = conn.cursor()
            try:
                yield (conn, cursor)
            finally:
                cursor.close()
                conn.commit()

    @contextmanager
    def _tx_stack(self):
        """A context manager providing access to the current thread's
        transaction stack. The context manager synchronizes access to
        the stack map. Transactions should never migrate across threads.
        """
        thread_id = threading.current_thread().ident
        with self._shared_map_lock:
            yield self._tx_stacks[thread_id]

    @contextmanager
    def transaction(self):
        """Get a :class:`Transaction` object for interacting directly
        with the underlying SQLite database.
        """
        _ = threading.currentThread().getName()
        threading.currentThread().setName("DB")
        yield Transaction(self)
        threading.currentThread().setName(_)

    def _get_id(self):
        with self._db_lock:
            self.last_id += 1
            return self.last_id

    def checkDBVersion(self):
        """
        Fetch database version

        :return: Integer inidicating current DB version
        """
        try:
            if self.hasTable('db_version'):
                return self.select("SELECT db_version FROM db_version")[0]["db_version"]
        except:
            return 0

    def mass_upsert(self, upserts):
        """
        Execute multiple upserts

        :param upserts: list of upserts
        :return: list of results
        """

        sqlResults = []

        q = Queue()
        map(q.put, upserts)
        while not q.empty():
            with ThreadPoolExecutor(1) as executor, self.transaction() as tx:
                sqlResults += [executor.submit(tx.upsert, *q.get()).result()]

        sickrage.srCore.srLogger.db("{} Upserts executed".format(len(sqlResults)))

        return sqlResults

    def mass_action(self, queries):
        """
        Execute multiple queries

        :param queries: list of queries
        :return: list of results
        """

        sqlResults = []

        q = Queue()
        map(q.put, queries)
        while not q.empty():
            with ThreadPoolExecutor(1) as executor, self.transaction() as tx:
                sqlResults += [executor.submit(tx.query, q.get()).result()]

        sickrage.srCore.srLogger.db("{} Transactions executed".format(len(sqlResults)))
        return sqlResults

    def action(self, query, *args):
        """
        Execute single query

        :rtype: query results
        :param query: Query string
        """

        sickrage.srCore.srLogger.db("{}: {} with args {}".format(self.filename, query, args))

        with ThreadPoolExecutor(1) as executor, self.transaction() as tx:
            return executor.submit(tx.query, [query, list(*args)]).result()

    def upsert(self, tableName, valueDict, keyDict):
        """
        Update values, or if no updates done, insert values
        TODO: Make this return true/false on success/error

        :param tableName: table to update/insert
        :param valueDict: values in table to update/insert
        :param keyDict:  columns in table to update
        """

        with ThreadPoolExecutor(1) as executor, self.transaction() as tx:
            return executor.submit(tx.upsert, tableName, valueDict, keyDict).result()

    def select(self, query, *args):
        """
        Perform single select query on database

        :param query: query string
        :param args:  arguments to query string
        :return: query results
        """
        return self.action(query, *args)

    def tableInfo(self, tableName):
        """
        Return information on a database table

        :param tableName: name of table
        :return: array of name/type info
        """
        columns = {}

        sqlResult = self.select("PRAGMA table_info(`{}`)".format(tableName))

        for column in sqlResult:
            columns[column['name']] = {'type': column['type']}

        return columns

    def _dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def hasIndex(self, indexName):
        """
        Check if a index exists in database

        :param indexName: index name to check
        :return: True if table exists, False if it does not
        """
        return (False, True)[len(self.select("PRAGMA index_info('{}')".format(indexName))) > 0]

    def hasTable(self, tableName):
        """
        Check if a table exists in database

        :param tableName: table name to check
        :return: True if table exists, False if it does not
        """
        return (False, True)[len(self.select("SELECT 1 FROM sqlite_master WHERE name = ?;", [tableName])) > 0]

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
        self.action("ALTER TABLE [{}] ADD {} {}".format(table, column, type))
        self.action("UPDATE [{}] SET {} = ?".format(table, column), [default])

    def incDBVersion(self, version=None):
        if not version:
            version = self.checkDBVersion() + 1

        self.action("UPDATE db_version SET db_version = {}".format(version))


class SchemaUpgrade(Connection):
    def __init__(self, filename=None, suffix=None, row_type=None):
        super(SchemaUpgrade, self).__init__(filename, suffix, row_type)

    def upgrade(self):
        """
        Perform database upgrade and provide logging
        """

        def _processUpgrade(upgradeClass, version):
            name = prettyName(upgradeClass.__name__)

            while (True):
                sickrage.srCore.srLogger.debug("Checking {} database structure".format(name))

                try:
                    instance = upgradeClass()

                    if not instance.test():
                        sickrage.srCore.srLogger.debug("Database upgrade required: {}".format(name))
                        instance.execute()
                        sickrage.srCore.srLogger.debug("{} upgrade completed".format(name))
                    else:
                        sickrage.srCore.srLogger.debug("{} upgrade not required".format(name))

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

        sickrage.srCore.srLogger.info("Restoring database before trying upgrade again")
        if not restoreVersionedFile(dbFilename(suffix='v' + str(version)), version):
            sickrage.srCore.srLogger.info("Database restore failed, abort upgrading database")
            return False
        return True

    def backup(self, version):
        sickrage.srCore.srLogger.info("Backing up database before upgrade")
        if not backupVersionedFile(dbFilename(), version):
            sickrage.srCore.srLogger.log_error_and_exit("Database backup failed, abort upgrading database")
        else:
            sickrage.srCore.srLogger.info("Proceeding with upgrade")

    @classmethod
    def get_subclasses(cls):
        yield cls
        if cls.__subclasses__():
            for sub in cls.__subclasses__():
                for s in sub.get_subclasses():
                    yield s
