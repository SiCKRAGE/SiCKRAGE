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
import sqlite3
import threading
from time import sleep

import alembic.command
import alembic.config
import alembic.script
import sqlalchemy
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from attrdict import AttrDict
from sqlalchemy import create_engine, event, inspect, MetaData, Index, TypeDecorator
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


class IntFlag(TypeDecorator):
    impl = sqlalchemy.types.Integer()

    def __init__(self, enum):
        self.enum = enum

    def process_bind_param(self, value, dialect):
        return int(value) if value is not None else None

    def process_result_value(self, value, dialect):
        return self.enum(value) if value is not None else None


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

    def as_attrdict(self):
        return AttrDict(self.as_dict())

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

        self.db_path = os.path.join(sickrage.app.data_dir, '{}.db'.format(self.name))
        self.db_migrations_path = os.path.join(os.path.dirname(__file__), self.name, 'migrations')

        self.session = scoped_session(sessionmaker(class_=ContextSession, bind=self.engine))

    @property
    def engine(self):
        if self.db_type == 'sqlite':
            return create_engine('sqlite:///{}'.format(self.db_path), echo=False, connect_args={'check_same_thread': False, 'timeout': 30})
        elif self.db_type == 'mysql':
            mysql_engine = create_engine('mysql+pymysql://{}:{}@{}:{}/'.format(self.db_username, self.db_password, self.db_host, self.db_port), echo=False)
            mysql_engine.execute(f"CREATE DATABASE IF NOT EXISTS {self.db_prefix}_{self.name}")
            return create_engine(
                'mysql+pymysql://{}:{}@{}:{}/{}_{}'.format(self.db_username, self.db_password, self.db_host, self.db_port, self.db_prefix, self.name),
                echo=False)

    @property
    def version(self):
        context = MigrationContext.configure(self.engine)
        current_rev = context.get_current_revision()
        return current_rev

    def setup(self):
        if self.engine.dialect.has_table(self.engine, 'migrate_version'):
            migrate_version = self.engine.execute("select version from migrate_version").fetchone().version
            alembic.command.stamp(self.get_alembic_config(), str(migrate_version))
            self.engine.execute("drop table migrate_version")

        if not self.engine.dialect.has_table(self.engine, 'alembic_version'):
            alembic.command.stamp(self.get_alembic_config(), 'head')
            sickrage.app.log.info("Performing initialization on {} database".format(self.name))
            self.initialize()

        # perform integrity check
        sickrage.app.log.info("Performing integrity check on {} database".format(self.name))
        self.integrity_check()

        # upgrade database
        sickrage.app.log.info("Performing upgrades on {} database".format(self.name))
        self.upgrade()

        # cleanup
        sickrage.app.log.info("Performing cleanup on {} database".format(self.name))
        self.cleanup()

        # free up space
        sickrage.app.log.info("Performing vacuum on {} database".format(self.name))
        self.vacuum()

    def initialize(self):
        pass

    def upgrade(self):
        db_version = int(self.version)
        alembic_version = int(ScriptDirectory.from_config(self.get_alembic_config()).get_current_head())

        backup_filename = os.path.join(sickrage.app.data_dir, f'{self.name}_db_backup_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json')

        if db_version < alembic_version:
            # temp code to resolve a migration bug introduced from v10.0.0, fixed in v10.0.2+
            if db_version < 21 and self.name == 'main':
                if self.engine.dialect.has_table(self.engine, 'indexer_mapping') and self.engine.dialect.has_table(self.engine, 'series_provider_mapping'):
                    sickrage.app.log.debug('Found offending series_provider_mapping table, removing!')
                    metadata = MetaData(self.engine, reflect=True)
                    table = metadata.tables.get('series_provider_mapping')
                    table.drop(self.engine)

            sickrage.app.log.info(f'Backing up {self.name} database')
            self.backup(backup_filename)

            sickrage.app.log.info(f'Upgrading {self.name} database to v{alembic_version}')
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
                sickrage.app.log.fatal(
                    f"{self.name.capitalize()} database file {self.db_path} is damaged, please restore a backup or delete the database file and restart SiCKRAGE")

    def cleanup(self):
        pass

    def vacuum(self):
        self.engine.execute("VACUUM")

    def backup(self, filename):
        meta = self.get_metadata()

        backup_dict = {
            'schema': {},
            'indexes': {},
            'data': {},
            'version': self.version
        }

        for table_name, table_object in meta.tables.items():
            sickrage.app.log.info(f'Backing up {self.name} database table {table_name} schema')
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
                    sickrage.app.log.info(f'Restoring {self.name} database table {table_name} schema')
                    session.execute(schema)
                session.commit()

            # restore indexes
            if backup_dict.get('indexes', None):
                for table_name, indexes in backup_dict['indexes'].items():
                    sickrage.app.log.info(f'Restoring {self.name} database table {table_name} indexes')
                    for index in indexes:
                        session.execute(index)
                session.commit()

            # restore data
            if backup_dict.get('data', None):
                base = self.get_base()
                meta = self.get_metadata()
                for table_name, data in backup_dict['data'].items():
                    sickrage.app.log.info(f'Restoring {self.name} database table {table_name} data')
                    table = base.classes[table_name]
                    session.query(table).delete()

                    rows = []
                    for row in loads(data, meta, session):
                        if isinstance(row, KeyedTuple):
                            rows.append(row._asdict())
                    session.bulk_insert_mappings(table, rows)
                session.commit()
