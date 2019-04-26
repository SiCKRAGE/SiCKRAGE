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
import shutil
from contextlib import contextmanager

from migrate import DatabaseAlreadyControlledError
from migrate.versioning import api
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, scoped_session, mapperlib

import sickrage


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


class srDatabase(object):
    def __init__(self, name):
        self.name = name
        self.tables = {}

        self.db_path = os.path.join(sickrage.app.data_dir, '{}.db'.format(self.name))
        self.db_repository = os.path.join(os.path.dirname(__file__), self.name, 'db_repository')
        self.engine = create_engine('sqlite:///{}'.format(self.db_path), echo=False)
        self.Session = scoped_session(sessionmaker(bind=self.engine, expire_on_commit=False))

        if not os.path.exists(self.db_path):
            api.version_control(self.engine, self.db_repository, api.version(self.db_repository))
        else:
            try:
                api.version_control(self.engine, self.db_repository)
            except DatabaseAlreadyControlledError:
                pass

    @contextmanager
    def session(self):
        """ Creates a context with an open SQLAlchemy session.
        """
        session = self.Session()

        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise

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

                migrate_tables[table] += [row]

            for table, rows in migrate_tables.items():
                sickrage.app.log.info('Migrating {} database table {}'.format(self.name, table))
                self.delete(self.tables[table])

                try:
                    self.bulk_add(self.tables[table], rows)
                except Exception as e:
                    for row in rows:
                        try:
                            self.add(self.tables[table](**row))
                        except Exception as e:
                            pass

            shutil.move(migrate_file, backup_file)

            # cleanup
            del migrate_tables
            del rows

    def get_table_mapper(self, tbl):
        mappers = [
            mapper for mapper in mapperlib._mapper_registry
            if tbl in mapper.tables
        ]
        if len(mappers) > 1:
            raise ValueError(
                "Multiple mappers found for table '%s'." % tbl.name
            )
        elif not mappers:
            raise ValueError(
                "Could not get mapper for table '%s'." % tbl.name
            )
        else:
            return mappers[0]

    def bulk_add(self, table, rows):
        with self.session() as session:
            session.bulk_insert_mappings(table, rows)

    def add(self, instance):
        with self.session() as session:
            session.add(instance)

    def delete(self, table, *args, **kwargs):
        with self.session() as session:
            found = session.query(table).filter_by(**kwargs).filter(*args)
            return found.delete() if found.count() else 0

    def update(self, obj):
        with self.session() as session:
            session.merge(obj)
