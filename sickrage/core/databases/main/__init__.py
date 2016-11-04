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

from .index import TVShowsIndex, TVEpisodesIndex, IMDBInfoIndex, XEMRefreshIndex, SceneNumberingIndex, \
    IndexerMappingIndex, HistoryIndex, InfoIndex, BlacklistIndex, WhitelistIndex


class MainDB(srDatabase):
    _indexes = {
        'tv_shows': TVShowsIndex,
        'tv_episodes': TVEpisodesIndex,
        'imdb_info': IMDBInfoIndex,
        'xem_refresh': XEMRefreshIndex,
        'scene_numbering': SceneNumberingIndex,
        'indexer_mapping': IndexerMappingIndex,
        'history': HistoryIndex,
        'info': InfoIndex,
        'blacklist': BlacklistIndex,
        'whitelist': WhitelistIndex,
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
        self.old_db_path = os.path.join(sickrage.DATA_DIR, 'sickrage.db')
