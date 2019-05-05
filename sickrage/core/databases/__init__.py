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
import functools
import os
import pickle
import shutil
from sqlite3 import OperationalError
from time import sleep

import sqlalchemy
from migrate import DatabaseAlreadyControlledError
from migrate.versioning import api
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import sessionmaker, scoped_session

import sickrage


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute('PRAGMA busy_timeout=%i;' % 15000)
    cursor.close()


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


class srDatabase(object):
    def __init__(self, name):
        self.name = name
        self.tables = {}

        self.db_path = os.path.join(sickrage.app.data_dir, '{}.db'.format(self.name))
        self.db_repository = os.path.join(os.path.dirname(__file__), self.name, 'db_repository')
        self.engine = create_engine('sqlite:///{}'.format(self.db_path), echo=False,
                                    connect_args={'check_same_thread': False, 'timeout': 10})
        self.Session = scoped_session(
            sessionmaker(bind=self.engine, class_=ContextSession, autoflush=False))

        if not os.path.exists(self.db_path):
            api.version_control(self.engine, self.db_repository, api.version(self.db_repository))
        else:
            try:
                api.version_control(self.engine, self.db_repository)
            except DatabaseAlreadyControlledError:
                pass

    @property
    def version(self):
        return int(api.db_version(self.engine, self.db_repository))

    def upgrade(self):
        if self.version < int(api.version(self.db_repository)):
            api.upgrade(self.engine, self.db_repository)
            sickrage.app.log.info('Upgraded {} database to version {}'.format(self.name, self.version))

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
            'cache': {
                'providers': {
                    'indexerid': 'indexer_id'
                }
            }
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

            migrate_tables = {}
            for row in rows:
                table = row.pop('_t')
                if table not in self.tables:
                    continue

                if table not in migrate_tables:
                    migrate_tables[table] = []

                for column in row.copy():
                    if column not in self.tables[table].__table__.columns:
                        if table in migration_table_column_mapper[self.name]:
                            if column in migration_table_column_mapper[self.name][table]:
                                new_column = migration_table_column_mapper[self.name][table][column]
                                row[new_column] = row[column]

                        del row[column]

                    if table == 'tv_episodes':
                        if column == 'airdate':
                            row[column] = datetime.date.fromordinal(row[column])

                migrate_tables[table] += [row]

            for table, rows in migrate_tables.items():
                sickrage.app.log.info('Migrating {} database table {}'.format(self.name, table))

                try:
                    self.delete(self.tables[table])
                except Exception:
                    pass

                try:
                    self.bulk_add(self.tables[table], rows)
                except Exception:
                    for row in rows:
                        try:
                            self.add(self.tables[table](**row))
                        except Exception as e:
                            pass

            shutil.move(migrate_file, backup_file)

            # cleanup
            del migrate_tables
            del rows

    def with_session(self, *args, **kwargs):
        """"
        A decorator which creates a new session if one was not passed via keyword argument to the function.

        Automatically commits and closes the session if one was created, caller is responsible for commit if passed in.

        If arguments are given when used as a decorator, they will automatically be passed to the created Session when
        one is not supplied.
        """

        def decorator(func):
            def wrapper(*args, **kwargs):
                if kwargs.get('session'):
                    return func(*args, **kwargs)
                with _Session() as session:
                    kwargs['session'] = session
                    return func(*args, **kwargs)

            return wrapper

        if len(args) == 1 and not kwargs and callable(args[0]):
            # Used without arguments, e.g. @with_session
            # We default to expire_on_commit being false, in case the decorated function returns db instances
            _Session = functools.partial(self.Session, expire_on_commit=False)
            return decorator(args[0])
        else:
            # Arguments were specified, turn them into arguments for Session creation e.g. @with_session(
            # autocommit=True)
            _Session = functools.partial(self.Session, *args, **kwargs)
            return decorator

    def bulk_add(self, table, rows):
        with self.Session() as session:
            session.bulk_insert_mappings(table, rows)

    def add(self, instance):
        with self.Session() as session:
            session.add(instance)

    def delete(self, table, *args, **kwargs):
        with self.Session() as session:
            session.query(table).filter_by(**kwargs).filter(*args).delete()
