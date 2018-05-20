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

import sickrage
from sickrage.core.databases import srDatabase
from sickrage.core.databases.main.index import MainTVShowsIndex, MainTVEpisodesIndex, MainIMDBInfoIndex, \
    MainXEMRefreshIndex, MainSceneNumberingIndex, MainIndexerMappingIndex, MainHistoryIndex, \
    MainBlacklistIndex, MainWhitelistIndex, MainFailedSnatchHistoryIndex, MainFailedSnatchesIndex, MainVersionIndex


class MainDB(srDatabase):
    _version = 2

    _indexes = {
        'version': MainVersionIndex,
        'tv_shows': MainTVShowsIndex,
        'tv_episodes': MainTVEpisodesIndex,
        'imdb_info': MainIMDBInfoIndex,
        'xem_refresh': MainXEMRefreshIndex,
        'scene_numbering': MainSceneNumberingIndex,
        'indexer_mapping': MainIndexerMappingIndex,
        'blacklist': MainBlacklistIndex,
        'whitelist': MainWhitelistIndex,
        'history': MainHistoryIndex,
        'failed_snatch_history': MainFailedSnatchHistoryIndex,
        'failed_snatches': MainFailedSnatchesIndex,
    }

    _migrate_list = {
        'tv_shows': ['indexer_id', 'indexer', 'show_name', 'location', 'network', 'genre',
                     'classification', 'runtime', 'quality', 'airs', 'status', 'flatten_folders', 'paused',
                     'startyear', 'air_by_date', 'lang', 'subtitles', 'notify_list', 'imdb_id',
                     'dvdorder', 'archive_firstmatch', 'rls_require_words', 'rls_ignore_words', 'sports', 'anime',
                     'scene', 'default_ep_status'],
        'tv_episodes': ['showid', 'indexerid', 'indexer', 'name', 'season', 'episode', 'scene_season', 'scene_episode',
                        'description', 'airdate', 'hasnfo', 'hastbn', 'status', 'location', 'file_size', 'release_name',
                        'subtitles', 'subtitles_searchcount', 'subtitles_lastsearch', 'is_proper', 'absolute_number',
                        'scene_absolute_number', 'version', 'release_group'],
        'history': ['action', 'date', 'showid', 'season', 'episode', 'quality', 'resource', 'provider', 'version'],
        'imdb_info': ['indexer_id', 'imdb_id', 'title', 'year', 'akas', 'runtimes', 'genres', 'countries',
                      'country_codes', 'certificates', 'rating', 'votes', 'last_update'],
        'scene_numbering': ['indexer', 'indexer_id', 'season', 'episode', 'scene_season', 'scene_episode',
                            'absolute_number', 'scene_absolute_number'],
        'blacklist': ['show_id', 'range', 'keyword'],
        'whitelist': ['show_id', 'range', 'keyword'],
        'xem_refresh': ['indexer', 'indexer_id', 'last_refreshed'],
        'indexer_mapping': ['indexer_id', 'indexer', 'mindexer_id', 'mindexer'],
    }

    def __init__(self, name='main'):
        super(MainDB, self).__init__(name)
        self.old_db_path = os.path.join(sickrage.app.data_dir, 'sickrage.db')

    def upgrade(self):
        current_version = self.version

        while current_version < self._version:
            dbData = list(self.all('version'))[-1]

            new_version = current_version + 1
            dbData['database_version'] = new_version

            upgrade_func = getattr(self, '_upgrade_v' + str(new_version), None)
            if upgrade_func:
                sickrage.app.log.info("Upgrading main database to version {}".format(new_version))
                upgrade_func()

            self.update(dbData)
            current_version = new_version

    def _upgrade_v2(self):
        # convert archive_firstmatch to skip_downloaded
        for show in self.all('tv_shows'):
            if 'archive_firstmatch' in show:
                show['skip_downloaded'] = show['archive_firstmatch']
                del show['archive_firstmatch']
                self.update(show)

    def cleanup(self):
        self.fix_show_none_types()
        self.fix_episode_none_types()
        self.fix_dupe_shows()
        self.fix_dupe_episodes()
        self.fix_orphaned_episodes()

    def fix_show_none_types(self):
        checked = []

        for show in self.all('tv_shows'):
            if show['indexer_id'] in checked:
                continue

            dirty = False
            for k, v in show.items():
                if v is None:
                    try:
                        show[k] = ""
                        dirty = True
                    except Exception:
                        pass

            if dirty:
                self.update(show)

            checked += [show['indexer_id']]

        del checked

    def fix_episode_none_types(self):
        checked = []

        for ep in self.all('tv_episodes'):
            if ep['showid'] in checked:
                continue

            dirty = False
            for k, v in ep.items():
                if v is None:
                    try:
                        ep[k] = ""
                        dirty = True
                    except Exception:
                        pass

            if dirty:
                self.update(ep)

            checked += [ep['showid']]

        del checked

    def fix_dupe_shows(self):
        found = []

        for show in self.all('tv_shows'):
            if show['indexer_id'] in found:
                sickrage.app.log.info("Deleting duplicate show with id: {}".format(show["indexer_id"]))
                self.delete(show)
            found += [show['indexer_id']]

        del found

    def fix_dupe_episodes(self):
        found = []

        for ep in self.all('tv_episodes'):
            if ep['indexerid'] in found:
                sickrage.app.log.info("Deleting duplicate episode with id: {}".format(ep["indexerid"]))
                self.delete(ep)
            found += [ep['indexerid']]

        del found

    def fix_orphaned_episodes(self):
        for ep in self.all('tv_episodes'):
            if not self.get('tv_shows', ep['showid']):
                sickrage.app.log.info("Deleting orphan episode with id: {}".format(ep["indexerid"]))
                self.delete(ep)