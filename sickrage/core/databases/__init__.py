# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
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
import datetime
import os
import pickle
import shutil
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

import sickrage


class BaseActions(object):
    @classmethod
    @contextmanager
    def session(cls):
        """ Creates a context with an open SQLAlchemy session.
        """
        session = scoped_session(sessionmaker(bind=cls.engine))()

        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @classmethod
    def query(cls, **kwargs):
        with cls.session() as session:
            return session.query(cls).filter_by(**kwargs)

    @classmethod
    def bulk_add(cls, values):
        with cls.session() as session:
            try:
                session.bulk_insert_mappings(cls, values)
            except Exception:
                [cls.add(**row) for row in values]

    @classmethod
    def add(cls, **kwargs):
        with cls.session() as session:
            obj = cls(**kwargs)
            session.add(obj)
            return obj

    @classmethod
    def update(cls, value):
        with cls.session() as session:
            cls.query().update(session.merge(value))
            cls.commit()

    @classmethod
    def delete(cls, obj):
        with cls.session() as session:
            session.delete(session.merge(obj))

    @classmethod
    def commit(cls):
        with cls.session() as session:
            try:
                session.commit()
            except Exception:
                session.rollback()

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class srDatabase(object):
    def __init__(self, name):
        self.name = name
        self.tables = {}

        self.db_path = os.path.join(sickrage.app.data_dir, '{}.db'.format(self.name))
        self.engine = create_engine('sqlite:///{}'.format(self.db_path), echo=True)

    @property
    def version(self):
        return 1

    def upgrade(self):
        pass

    def migrate(self):
        backup_file = os.path.join(sickrage.app.data_dir, 'migrate', '{}_{}.codernitydb.bak'.format(self.name,
                                                                                                    datetime.datetime.now().strftime(
                                                                                                        '%Y%m%d_%H%M%S')))

        migrate_file = os.path.join(sickrage.app.data_dir, 'migrate', '{}.codernitydb'.format(self.name))
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

                table_columns = [column.key for column in self.tables[table].__table__.columns]
                for column in row.copy():
                    if column not in table_columns:
                        del row[column]

                migrate_tables[table] += [row]

            for table, rows in migrate_tables.items():
                sickrage.app.log.info('Migrating {} database table {}'.format(self.name, table))
                try:
                    self.tables[table].bulk_add(rows)
                except:
                    pass

            shutil.move(migrate_file, backup_file)

            # cleanup
            del migrate_tables
            del rows
