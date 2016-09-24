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

import os
import time
import traceback
from sqlite3 import OperationalError

import sickrage
from sickrage.core.databases import srDatabase
from sickrage.core.helpers import randomString

from .index import TVShowsIndex, TVEpisodesIndex, IMDBInfoIndex, XEMRefreshIndex, SceneNumberingIndex, \
    IndexerMappingIndex


class MainDB(srDatabase):
    _database = {
        'tv_shows': TVShowsIndex,
        'tv_episodes': TVEpisodesIndex,
        'imdb_info': IMDBInfoIndex,
        'xem_refresh': XEMRefreshIndex,
        'scene_numbering': SceneNumberingIndex,
        'indexer_mapping': IndexerMappingIndex
    }

    _migrate_list = {
        'tv_shows': ['show_id', 'indexer_id', 'indexer', 'show_name', 'location', 'network', 'genre',
                     'classification', 'runtime', 'quality', 'airs', 'status', 'flatten_folders', 'paused',
                     'startyear', 'air_by_date', 'lang', 'subtitles', 'notify_list', 'imdb_id',
                     'last_update_indexer', 'dvdorder', 'archive_firstmatch', 'rls_require_words',
                     'rls_ignore_words', 'sports', 'anime', 'scene', 'default_ep_status'],
        'tv_episodes': ['episode_id', 'showid', 'indexerid', 'indexer', 'name', 'season', 'episode',
                        'description',
                        'airdate', 'hasnfo', 'hastbn', 'status', 'location', 'file_size', 'release_name',
                        'subtitles', 'subtitles_searchcount', 'subtitles_lastsearch', 'is_proper',
                        'scene_season',
                        'scene_episode', 'absolute_number', 'scene_absolute_number', 'version',
                        'release_group'],
        'history': ['action', 'date', 'showid', 'season', 'episode', 'quality', 'resource', 'provider',
                    'version'],
        'imdb_info': ['indexer_id', 'imdb_id', 'title', 'year', 'akas', 'runtimes', 'genres', 'countries',
                      'country_codes', 'certificates', 'rating', 'votes', 'last_update'],
        'info': ['last_backlog', 'last_indexer', 'last_proper_search'],
        'scene_numbering': ['indexer', 'indexer_id', 'season', 'episode', 'scene_season', 'scene_episode',
                            'absolute_number', 'scene_absolute_number'],
        'blacklist': ['show_id', 'range', 'keyword'],
        'whitelist': ['show_id', 'range', 'keyword'],
        'xem_refresh': ['indexer', 'indexer_id', 'last_refreshed'],
        'indexer_mapping': ['indexer_id', 'indexer', 'mindexer_id', 'mindexer'],
    }

    def __init__(self, name='main'):
        super(MainDB, self).__init__(name)

    def migrate(self):
        old_db = os.path.join(sickrage.DATA_DIR, 'sickrage.db')
        if os.path.isfile(old_db):
            sickrage.srCore.srLogger.info('=' * 30)
            sickrage.srCore.srLogger.info('Migrating database, please wait...')
            migrate_start = time.time()

            import sqlite3
            conn = sqlite3.connect(old_db)

            migrate_list = {
                'tv_shows': ['show_id', 'indexer_id', 'indexer', 'show_name', 'location', 'network', 'genre',
                             'classification', 'runtime', 'quality', 'airs', 'status', 'flatten_folders', 'paused',
                             'startyear', 'air_by_date', 'lang', 'subtitles', 'notify_list', 'imdb_id',
                             'last_update_indexer', 'dvdorder', 'archive_firstmatch', 'rls_require_words',
                             'rls_ignore_words', 'sports', 'anime', 'scene', 'default_ep_status'],
                'tv_episodes': ['episode_id', 'showid', 'indexerid', 'indexer', 'name', 'season', 'episode',
                                'description',
                                'airdate', 'hasnfo', 'hastbn', 'status', 'location', 'file_size', 'release_name',
                                'subtitles', 'subtitles_searchcount', 'subtitles_lastsearch', 'is_proper',
                                'scene_season',
                                'scene_episode', 'absolute_number', 'scene_absolute_number', 'version',
                                'release_group'],
                'history': ['action', 'date', 'showid', 'season', 'episode', 'quality', 'resource', 'provider',
                            'version'],
                'imdb_info': ['indexer_id', 'imdb_id', 'title', 'year', 'akas', 'runtimes', 'genres', 'countries',
                              'country_codes', 'certificates', 'rating', 'votes', 'last_update'],
                'info': ['last_backlog', 'last_indexer', 'last_proper_search'],
                'scene_numbering': ['indexer', 'indexer_id', 'season', 'episode', 'scene_season', 'scene_episode',
                                    'absolute_number', 'scene_absolute_number'],
                'blacklist': ['show_id', 'range', 'keyword'],
                'whitelist': ['show_id', 'range', 'keyword'],
                'xem_refresh': ['indexer', 'indexer_id', 'last_refreshed'],
                'indexer_mapping': ['indexer_id', 'indexer', 'mindexer_id', 'mindexer'],
            }

            migrate_data = {}
            rename_old = False

            try:
                c = conn.cursor()

                for ml in migrate_list:
                    migrate_data[ml] = {}
                    rows = migrate_list[ml]

                    try:
                        c.execute('SELECT {} FROM `{}`'.format('`' + '`,`'.join(rows) + '`', ml))
                    except:
                        # ignore faulty destination_id database
                        rename_old = True
                        raise

                    for p in c.fetchall():
                        columns = {}
                        for row in migrate_list[ml]:
                            columns[row] = p[rows.index(row)]

                        if not migrate_data[ml].get(p[0]):
                            migrate_data[ml][p[0]] = columns
                        else:
                            if not isinstance(migrate_data[ml][p[0]], list):
                                migrate_data[ml][p[0]] = [migrate_data[ml][p[0]]]
                            migrate_data[ml][p[0]].append(columns)

                conn.close()

                sickrage.srCore.srLogger.info('Getting data took %s', (time.time() - migrate_start))

                self.db.open()
                if not self.db.opened:
                    return

                # TV Shows
                tv_shows = migrate_data['tv_shows']
                sickrage.srCore.srLogger.info('Importing %s tv shows', len(tv_shows))
                for x in tv_shows:
                    tv_show = tv_shows[x]

                sickrage.srCore.srLogger.info('Total migration took %s', (time.time() - migrate_start))
                sickrage.srCore.srLogger.info('=' * 30)

                rename_old = True
            except OperationalError:
                sickrage.srCore.srLogger.error(
                    'Migrating from unsupported/corrupt database version: %s', traceback.format_exc())
                rename_old = True
            except:
                sickrage.srCore.srLogger.error('Migration failed: %s', traceback.format_exc())

            # rename old database
            if rename_old:
                return
                random = randomString()
                sickrage.srCore.srLogger.info('Renaming old database to %s.%s_old', (old_db, random))
                os.rename(old_db, '{}.{}_old'.format(old_db, random))

                if os.path.isfile(old_db + '-wal'):
                    os.rename(old_db + '-wal', '{}-wal.{}_old'.format(old_db, random))
                if os.path.isfile(old_db + '-shm'):
                    os.rename(old_db + '-shm', '{}-shm.{}_old'.format(old_db, random))
