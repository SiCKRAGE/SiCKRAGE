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
import os
import pickle
import random
import shutil
import sqlite3
import threading
from collections import OrderedDict
from time import sleep

import alembic.command
import alembic.config
import alembic.script
import sqlalchemy
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, event, inspect, MetaData, Index
from sqlalchemy.engine import Engine, reflection
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.serializer import loads, dumps
from sqlalchemy.orm import sessionmaker, mapper, scoped_session
from sqlalchemy.sql.ddl import CreateTable, CreateIndex
from sqlalchemy.util import KeyedTuple

import sickrage


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if not isinstance(dbapi_connection, sqlite3.Connection):
        return

    old_isolation = dbapi_connection.isolation_level
    dbapi_connection.isolation_level = None
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()
    dbapi_connection.isolation_level = old_isolation


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
        self._lock = threading.RLock()
        self.max_attempts = 50

    def commit(self, close=False):
        statement = None
        params = None
        for i in range(self.max_attempts):
            try:
                if statement and params:
                    self.bind.execute(statement, params)
                super(ContextSession, self).commit()
            except OperationalError as e:
                self.rollback()

                if 'database is locked' not in str(e):
                    raise

                statement = e.statement
                params = e.params

                timer = random.randint(10, 30)
                sickrage.app.log.debug('Retrying database commit in {}s, attempt {}'.format(timer, i))
                sleep(timer)
            except Exception as e:
                self.rollback()
                raise
            else:
                break
            finally:
                if close:
                    self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class SRDatabaseBase(object):
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def update(self, **kwargs):
        primary_keys = [pk.name for pk in self.__table__.primary_key]
        for key, value in kwargs.items():
            if key not in primary_keys:
                setattr(self, key, value)


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
        self.db_migrations_path = os.path.join(os.path.dirname(__file__), self.name, 'migrations')

        self.session = scoped_session(sessionmaker(class_=ContextSession, bind=self.engine))

        if self.engine.dialect.has_table(self.engine, 'migrate_version'):
            migrate_version = self.engine.execute("select version from migrate_version").fetchone().version
            alembic.command.stamp(self.get_alembic_config(), str(migrate_version))
            self.engine.execute("drop table migrate_version")

        if not self.engine.dialect.has_table(self.engine, 'alembic_version'):
            alembic.command.stamp(self.get_alembic_config(), 'head')

    @property
    def engine(self):
        if self.db_type == 'sqlite':
            return create_engine('sqlite:///{}'.format(self.db_path), echo=False, connect_args={'check_same_thread': False, 'timeout': 30})
        elif self.db_type == 'mysql':
            mysql_engine = create_engine('mysql+pymysql://{}:{}@{}:{}/'.format(self.db_username, self.db_password, self.db_host, self.db_port), echo=False)
            mysql_engine.execute("CREATE DATABASE IF NOT EXISTS {}_{}".format(self.db_prefix, self.name))
            return create_engine(
                'mysql+pymysql://{}:{}@{}:{}/{}_{}'.format(self.db_username, self.db_password, self.db_host, self.db_port, self.db_prefix, self.name),
                echo=False)

    @property
    def version(self):
        context = MigrationContext.configure(self.engine)
        current_rev = context.get_current_revision()
        return current_rev

    def upgrade(self):
        db_version = int(self.version)
        alembic_version = int(ScriptDirectory.from_config(self.get_alembic_config()).get_current_head())

        backup_filename = os.path.join(sickrage.app.data_dir, '{}_db_backup_{}.json'.format(self.name, datetime.datetime.now().strftime('%Y%m%d_%H%M%S')))

        if db_version < alembic_version:
            sickrage.app.log.info('Upgrading {} database to v{}'.format(self.name, alembic_version))

            self.backup(backup_filename)

            alembic.command.upgrade(self.get_alembic_config(), 'head')

    def get_alembic_config(self):
        config = alembic.config.Config()
        config.set_main_option('script_location', self.db_migrations_path)
        config.set_main_option('sqlalchemy.url', str(self.engine.url))
        config.set_main_option('url', str(self.engine.url))
        return config

    def get_metadata(self):
        return MetaData(bind=self.engine, reflect=True)

    def get_base(self):
        base = automap_base(metadata=self.get_metadata())
        base.prepare()
        return base

    def integrity_check(self):
        if self.db_type == 'sqlite':
            if self.session().scalar("PRAGMA integrity_check") != "ok":
                sickrage.app.log.fatal("{} database file {} is damaged, please restore a backup"
                                       " or delete the database file and restart SiCKRAGE".format(self.name.capitalize(), self.db_path))

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

            session = self.session()
            for table, rows in migrate_tables.items():
                if not len(rows):
                    continue

                sickrage.app.log.info('Migrating {} database table {}'.format(self.name, table))

                try:
                    session.query(self.tables[table]).delete()
                    session.commit()
                except Exception:
                    pass

                try:
                    session.bulk_insert_mappings(self.tables[table], rows)
                    session.commit()
                except Exception:
                    for row in rows:
                        try:
                            session.add(self.tables[table](**row))
                            session.commit()
                        except Exception:
                            continue

            shutil.move(migrate_file, backup_file)

            # cleanup
            del migrate_tables
            del rows

    def backup(self, filename):
        meta = self.get_metadata()

        backup_dict = {
            'schema': {},
            'indexes': {},
            'data': {},
            'version': self.version
        }

        for table_name, table_object in meta.tables.items():
            backup_dict['indexes'].update({table_name: []})
            backup_dict['schema'].update({table_name: str(CreateTable(table_object))})
            backup_dict['data'].update({table_name: dumps(self.session().query(table_object).all(), protocol=pickle.DEFAULT_PROTOCOL)})
            for index in reflection.Inspector.from_engine(self.engine).get_indexes(table_name):
                cols = [table_object.c[col] for col in index['column_names']]
                idx = Index(index['name'], *cols)
                backup_dict['indexes'][table_name].append(str(CreateIndex(idx)))

        with open(filename, 'wb') as fh:
            pickle.dump(backup_dict, fh, protocol=pickle.DEFAULT_PROTOCOL)

    def restore(self, filename):
        session = self.session()

        with open(filename, 'rb') as fh:
            backup_dict = pickle.load(fh)

            # drop all tables
            self.get_base().metadata.drop_all()

            # restore schema
            if backup_dict.get('schema', None):
                for table_name, schema in backup_dict['schema'].items():
                    sickrage.app.log.info('Restoring {} database table {} schema'.format(self.name, table_name))
                    session.execute(schema)
                session.commit()

            # restore indexes
            if backup_dict.get('indexes', None):
                for table_name, indexes in backup_dict['indexes'].items():
                    sickrage.app.log.info('Restoring {} database table {} indexes'.format(self.name, table_name))
                    for index in indexes:
                        session.execute(index)
                session.commit()

            # restore data
            if backup_dict.get('data', None):
                base = self.get_base()
                meta = self.get_metadata()
                for table_name, data in backup_dict['data'].items():
                    sickrage.app.log.info('Restoring {} database table {} data'.format(self.name, table_name))
                    table = base.classes[table_name]
                    session.query(table).delete()

                    rows = []
                    for row in loads(data, meta, session):
                        if isinstance(row, KeyedTuple):
                            rows.append(row._asdict())
                    session.bulk_insert_mappings(table, rows)
                session.commit()
