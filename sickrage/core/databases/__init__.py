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

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, scoped_session, Query

import sickrage


class srDatabase(object):
    def __init__(self, name):
        self.name = name
        self.tables = {}

        self.db_path = os.path.join(sickrage.app.data_dir, '{}.db'.format(self.name))
        self.engine = create_engine('sqlite:///{}'.format(self.db_path), echo=False)
        self.Session = scoped_session(sessionmaker(bind=self.engine))

    @contextmanager
    def session(self):
        """ Creates a context with an open SQLAlchemy session.
        """
        session = self.Session()

        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @property
    def version(self):
        return 1

    def upgrade(self):
        pass

    def migrate(self):
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
                    if column not in self.tables[table].__table__.columns.keys():
                        del row[column]

                migrate_tables[table] += [row]

            for table, rows in migrate_tables.items():
                sickrage.app.log.info('Migrating {} database table {}'.format(self.name, table))
                try:
                    self.delete(self.tables[table])
                    self.bulk_add(self.tables[table], rows)
                except Exception as e:
                    pass

            shutil.move(migrate_file, backup_file)

            # cleanup
            del migrate_tables
            del rows

    def bulk_add(self, table, rows):
        with self.session() as session:
            try:
                session.bulk_insert_mappings(table, rows)
            except Exception:
                [session.add(table(**row)) for row in rows]

    def add(self, instance):
        with self.session() as session:
            session.add(instance)

    def update(self, obj):
        primary_keys = dict((key.name, getattr(obj, key.name)) for key in inspect(obj.__table__).primary_key)
        with self.session() as session:
            session.query(obj.__table__).filter_by(**primary_keys).update(
                dict((k, v) for k, v in obj.as_dict().items() if k not in primary_keys))

    def delete(self, table, *args, **kwargs):
        with self.session() as session:
            return session.query(table).filter_by(**kwargs).filter(*args).delete()
