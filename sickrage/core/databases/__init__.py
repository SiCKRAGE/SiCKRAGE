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

from __future__ import unicode_literals

import os
import re
import shutil
import tarfile
import time
import traceback
from sqlite3 import OperationalError

from CodernityDB.database_super_thread_safe import SuperThreadSafeDatabase
from CodernityDB.index import IndexNotFoundException, IndexConflict, IndexException
from CodernityDB.storage import IU_Storage

import sickrage
from sickrage.core.helpers import randomString


def Custom_IU_Storage_get(self, start, size, status='c'):
    if status == 'd':
        return None
    else:
        self._f.seek(start)
        return self.data_from(self._f.read(size))


class srDatabase(object):
    _indexes = {}
    _migrate_list = {}

    def __init__(self, name=''):
        self.name = name
        self.old_db_path = ''

        self.db_path = os.path.join(sickrage.DATA_DIR, 'database', self.name)
        self.db = SuperThreadSafeDatabase(self.db_path)

    def initialize(self):
        # Remove database folder if both exists
        if self.db.exists() and os.path.isfile(self.old_db_path):
            self.db.open()
            self.db.destroy()

        if self.db.exists():
            # Backup before start and cleanup old backups
            backup_path = os.path.join(sickrage.DATA_DIR, 'db_backup', self.name)
            backup_count = 5
            existing_backups = []
            if not os.path.isdir(backup_path): os.makedirs(backup_path)

            for root, dirs, files in os.walk(backup_path):
                # Only consider files being a direct child of the backup_path
                if root == backup_path:
                    for backup_file in sorted(files):
                        ints = re.findall('\d+', backup_file)

                        # Delete non zip files
                        if len(ints) != 1:
                            try:
                                os.remove(os.path.join(root, backup_file))
                            except:
                                pass
                        else:
                            existing_backups.append((int(ints[0]), backup_file))
                else:
                    # Delete stray directories.
                    shutil.rmtree(root)

            # Remove all but the last 5
            for eb in existing_backups[:-backup_count]:
                os.remove(os.path.join(backup_path, eb[1]))

            # Create new backup
            new_backup = os.path.join(backup_path, '%s.tar.gz' % int(time.time()))
            with tarfile.open(new_backup, 'w:gz') as zipf:
                for root, dirs, files in os.walk(self.db_path):
                    for zfilename in files:
                        zipf.add(os.path.join(root, zfilename),
                                 arcname='database/%s/%s' % (
                                     self.name,
                                     os.path.join(root[len(self.db_path) + 1:], zfilename))
                                 )

            self.db.open()
        else:
            self.db.create()

        # setup database indexes
        self.setupIndexes()

    def compact(self, try_repair=True, **kwargs):
        # Removing left over compact files
        for f in os.listdir(self.db.path):
            for x in ['_compact_buck', '_compact_stor']:
                if f[-len(x):] == x:
                    os.unlink(os.path.join(self.db.path, f))

        try:
            start = time.time()
            size = float(self.db.get_db_details().get('size', 0))
            sickrage.srCore.srLogger.debug(
                'Compacting {} database, current size: {}MB'.format(self.name, round(size / 1048576, 2)))

            self.db.compact()
            new_size = float(self.db.get_db_details().get('size', 0))
            sickrage.srCore.srLogger.debug(
                'Done compacting {} database in {}s, new size: {}MB, saved: {}MB'.format(
                    self.name, round(time.time() - start, 2),
                    round(new_size / 1048576, 2), round((size - new_size) / 1048576, 2))
            )
        except (IndexException, AttributeError):
            if try_repair:
                sickrage.srCore.srLogger.error('Something wrong with indexes, trying repair')

                # Remove all indexes
                old_indexes = self._indexes.keys()
                for index_name in old_indexes:
                    try:
                        self.db.destroy_index(index_name)
                    except IndexNotFoundException:
                        pass
                    except:
                        sickrage.srCore.srLogger.error('Failed removing old index %s', index_name)

                # Add them again
                for index_name in self._indexes:
                    try:
                        self.db.add_index(self._indexes[index_name](self.db.path, index_name))
                        self.db.reindex_index(index_name)
                    except IndexConflict:
                        pass
                    except:
                        sickrage.srCore.srLogger.error('Failed adding index %s', index_name)
                        raise

                self.compact(try_repair=False)
            else:
                sickrage.srCore.srLogger.error('Failed compact: {}'.format(traceback.format_exc()))
        except:
            sickrage.srCore.srLogger.error('Failed compact: {}'.format(traceback.format_exc()))

    def setupIndexes(self):
        # setup database indexes
        for index_name in self._indexes:
            try:
                # Make sure store and bucket don't exist
                exists = []
                for x in ['buck', 'stor']:
                    full_path = os.path.join(self.db.path, '%s_%s' % (index_name, x))
                    if os.path.exists(full_path):
                        exists.append(full_path)

                if index_name not in self.db.indexes_names:
                    # Remove existing buckets if index isn't there
                    for x in exists:
                        os.unlink(x)

                    self.db.add_index(self._indexes[index_name](self.db.path, index_name))
                    # self.db.reindex_index(self.db.indexes_names[index_name])
                else:
                    # Previous info
                    previous_version = self.db.indexes_names[index_name]._version
                    current_version = self._indexes[index_name]._version

                    # Only edit index if versions are different
                    if previous_version < current_version:
                        self.db.destroy_index(self.db.indexes_names[index_name])
                        self.db.add_index(self._indexes[index_name](self.db.path, index_name))
                        self.db.reindex_index(index_name)
            except:
                sickrage.srCore.srLogger.error('Failed adding index {}'.format(index_name))

    def close(self):
        self.db.close()

    def check_integrity(self):
        for index_name in self._indexes:
            try:
                for x in self.db.all(index_name):
                    try:
                        self.db.get('id', x.get('_id'), with_doc=True)
                    except (ValueError, TypeError) as e:
                        self.db.delete(self.db.get(index_name, x.get('key'), with_doc=True)['doc'])
            except Exception as e:
                if index_name in self.db.indexes_names:
                    self.db.destroy_index(self.db.indexes_names[index_name])

    def migrate(self):
        if os.path.isfile(self.old_db_path):
            sickrage.srCore.srLogger.info('=' * 30)
            sickrage.srCore.srLogger.info('Migrating %s database, please wait...', self.name)
            migrate_start = time.time()

            import sqlite3
            conn = sqlite3.connect(self.old_db_path)

            migrate_data = {}
            rename_old = False

            try:
                c = conn.cursor()

                for ml in self._migrate_list:
                    migrate_data[ml] = {}
                    rows = self._migrate_list[ml]

                    try:
                        c.execute('SELECT {} FROM `{}`'.format('`' + '`,`'.join(rows) + '`', ml))
                    except:
                        # ignore faulty destination_id database
                        rename_old = True
                        raise

                    for p in c.fetchall():
                        columns = {}
                        for row in self._migrate_list[ml]:
                            columns[row] = p[rows.index(row)]

                        if not migrate_data[ml].get(p[0]):
                            migrate_data[ml][p[0]] = columns
                        else:
                            if not isinstance(migrate_data[ml][p[0]], list):
                                migrate_data[ml][p[0]] = [migrate_data[ml][p[0]]]
                            migrate_data[ml][p[0]].append(columns)

                conn.close()

                sickrage.srCore.srLogger.info('Getting data took %s', (time.time() - migrate_start))

                if not self.db.opened:
                    return

                for t_name in migrate_data:
                    t_data = migrate_data.get(t_name, {})
                    sickrage.srCore.srLogger.info('Importing %s %s' % (len(t_data), t_name))
                    for k, v in t_data.items():
                        if isinstance(v, list):
                            for d in v:
                                d.update({'_t': t_name})
                                self.db.insert(d)
                        else:
                            v.update({'_t': t_name})
                            self.db.insert(v)

                sickrage.srCore.srLogger.info('Total migration took %s', (time.time() - migrate_start))
                sickrage.srCore.srLogger.info('=' * 30)

                rename_old = True
            except OperationalError:
                sickrage.srCore.srLogger.error('Migrating from unsupported/corrupt %s database version', self.name)
                rename_old = True
            except:
                sickrage.srCore.srLogger.error('Migration of %s database failed', self.name)

            # rename old database
            if rename_old:
                random = randomString()
                sickrage.srCore.srLogger.info('Renaming old database to %s.%s_old' % (self.old_db_path, random))
                os.rename(self.old_db_path, '{}.{}_old'.format(self.old_db_path, random))

                if os.path.isfile(self.old_db_path + '-wal'):
                    os.rename(self.old_db_path + '-wal', '{}-wal.{}_old'.format(self.old_db_path, random))
                if os.path.isfile(self.old_db_path + '-shm'):
                    os.rename(self.old_db_path + '-shm', '{}-shm.{}_old'.format(self.old_db_path, random))


# Monkey-Patch storage to suppress logging messages
IU_Storage.get = Custom_IU_Storage_get
