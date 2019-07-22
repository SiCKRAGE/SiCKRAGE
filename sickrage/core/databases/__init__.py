# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
import datetime
import errno
import os
import pickle
import shutil
import sqlite3
from collections import OrderedDict
from sqlite3 import OperationalError
from time import sleep

import sqlalchemy
from migrate import DatabaseAlreadyControlledError, DatabaseNotControlledError
from migrate.versioning import api
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, mapper
from sqlalchemy.pool import QueuePool

import sickrage
from sickrage.core.helpers import backup_versioned_file


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if not isinstance(dbapi_connection, sqlite3.Connection):
        return

    cursor = dbapi_connection.cursor()

    try:
        # cursor.execute('PRAGMA foreign_keys=ON;')
        cursor.execute('PRAGMA page_size=4096;')
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute('PRAGMA synchronous=NORMAL;')
        cursor.execute('PRAGMA busy_timeout=%i;' % 15000)
    except OperationalError:
        pass

    cursor.close()


@event.listens_for(mapper, "init")
def instant_defaults_listener(target, args, kwargs):
    for key, column in inspect(target.__class__).columns.items():
        if column.default is not None:
            if callable(column.default.arg):
                setattr(target, key, column.default.arg(target))
            else:
                setattr(target, key, column.default.arg)


class ContextSession(sqlalchemy.orm.Session):
    """:class:`sqlalchemy.orm.Session` which can be used as context manager"""

    def __init__(self, *args, **kwargs):
        super(ContextSession, self).__init__(*args, **kwargs)
        self.lockfile = self.bind.url.database + '-lock'
        self.max_attempts = 5

    @property
    def has_lock(self):
        return os.path.exists(self.lockfile)

    def write_lock(self):
        if self.has_lock:
            return

        with open(self.lockfile, 'w', encoding='utf-8') as f:
            f.write('PID: %s\n' % os.getpid())

    def release_lock(self):
        if not self.has_lock:
            return

        try:
            os.remove(self.lockfile)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        attempt = 0

        while attempt <= self.max_attempts:
            try:
                self.commit()
                break
            except OperationalError as e:
                self.rollback()
                if not attempt < self.max_attempts:
                    raise
                sleep(1)
            except Exception as e:
                self.rollback()
                raise

            attempt += 1

            sickrage.app.log.debug('Retrying database commit, attempt {}'.format(attempt))

        self.close()


class SRDatabase(object):
    def __init__(self, name, db_type='sqlite', db_prefix='sickrage', db_host='localhost', db_port='3306', db_username='sickrage', db_password='sickrage'):
        self.name = name
        self.db_type = db_type
        self.db_prefix = db_prefix
        self.db_host = db_host
        self.db_port = db_port
        self.db_username = db_username
        self.db_password = db_password

        self.tables = {}

        self.db_path = os.path.join(sickrage.app.data_dir, '{}.db'.format(self.name))
        self.db_repository = os.path.join(os.path.dirname(__file__), self.name, 'db_repository')

        if not self.version:
            api.version_control(self.engine, self.db_repository, api.version(self.db_repository))
        else:
            try:
                api.version_control(self.engine, self.db_repository)
            except DatabaseAlreadyControlledError:
                pass

    @property
    def engine(self):
        if self.db_type == 'sqlite':
            return create_engine('sqlite:///{}'.format(self.db_path), echo=False, pool_size=200, poolclass=QueuePool,
                                 connect_args={'check_same_thread': False, 'timeout': 10})
        elif self.db_type == 'mysql':
            mysql_engine = create_engine('mysql+pymysql://{}:{}@{}:{}/'.format(self.db_username, self.db_password, self.db_host, self.db_port), echo=False)
            mysql_engine.execute("CREATE DATABASE IF NOT EXISTS {}_{}".format(self.db_prefix, self.name))
            return create_engine(
                'mysql+pymysql://{}:{}@{}:{}/{}_{}'.format(self.db_username, self.db_password, self.db_host, self.db_port, self.db_prefix, self.name),
                echo=False)

    @property
    def session(self):
        return self.session

    @property
    def version(self):
        try:
            return int(api.db_version(self.engine, self.db_repository))
        except DatabaseNotControlledError:
            return 0

    def integrity_check(self):
        if self.db_type == 'sqlite':
            if self.session().scalar("PRAGMA integrity_check") != "ok":
                sickrage.app.log.fatal("{} database file {} is damaged, please restore a backup"
                                       " or delete the database file and restart SiCKRAGE".format(self.name.capitalize(), self.db_path))

    def sync_db_repo(self):
        if self.version < self.db_version:
            if self.db_type == 'sqlite':
                backup_versioned_file(self.db_path, self.version)
                backup_versioned_file(self.db_path + '-shm', self.version)
                backup_versioned_file(self.db_path + '-wal', self.version)
            api.upgrade(self.engine, self.db_repository)
            sickrage.app.log.info('Upgraded {} database to version {}'.format(self.name, self.version))
        elif self.version > self.db_version:
            if self.db_type == 'sqlite':
                backup_versioned_file(self.db_path, self.version)
                backup_versioned_file(self.db_path + '-shm', self.version)
                backup_versioned_file(self.db_path + '-wal', self.version)
            api.downgrade(self.engine, self.db_repository, self.db_version)
            sickrage.app.log.info('Downgraded {} database to version {}'.format(self.name, self.version))

    def cleanup(self):
        pass

    def migrate(self):
        migration_table_column_mapper = {
            'main': {
                'tv_shows': {
                    'show_name': 'name'
                },
                'tv_episodes': {
                    'indexerid': 'indexer_id'
                },
            },
            'cache': {}
        }

        backup_file = os.path.join(sickrage.app.data_dir, '{}_{}.codernitydb.bak'.format(self.name,
                                                                                         datetime.datetime.now().strftime(
                                                                                             '%Y%m%d_%H%M%S')))

        migrate_file = os.path.join(sickrage.app.data_dir, '{}.codernitydb'.format(self.name))
        if os.path.exists(migrate_file):
            # self.backup(backup_file)
            sickrage.app.log.info('Migrating {} database using {}'.format(self.name, migrate_file))
            with open(migrate_file, 'rb') as f:
                rows = pickle.load(f, encoding='bytes')

            migrate_tables = OrderedDict({
                'tv_shows': [],
                'tv_episodes': [],
                'scene_numbering': [],
                'blacklist': [],
                'whitelist': [],
                'scene_exceptions': [],
                'scene_names': []
            })

            for row in rows:
                table = row.pop('_t')
                if table not in self.tables:
                    continue

                if table not in migrate_tables:
                    continue

                for column in row.copy():
                    if column not in self.tables[table].__table__.columns:
                        if table in migration_table_column_mapper[self.name]:
                            if column in migration_table_column_mapper[self.name][table]:
                                new_column = migration_table_column_mapper[self.name][table][column]
                                row[new_column] = row[column]

                        del row[column]

                    if table == 'tv_shows':
                        if column == 'runtime':
                            row[column] = int(row[column] or 0)
                    elif table == 'tv_episodes':
                        if column == 'airdate':
                            row[column] = datetime.date.fromordinal(row[column])
                        elif column == 'subtitles_lastsearch':
                            row[column] = 0

                migrate_tables[table] += [row]

            for table, rows in migrate_tables.items():
                if not len(rows):
                    continue

                sickrage.app.log.info('Migrating {} database table {}'.format(self.name, table))

                try:
                    with self.session() as session:
                        session.query(self.tables[table]).delete()
                except Exception:
                    pass

                try:
                    with self.session() as session:
                        session.bulk_insert_mappings(self.tables[table], rows)
                except Exception:
                    for row in rows:
                        try:
                            with self.session() as session:
                                session.add(self.tables[table](**row))
                        except Exception:
                            continue

            shutil.move(migrate_file, backup_file)

            # cleanup
            del migrate_tables
            del rows
