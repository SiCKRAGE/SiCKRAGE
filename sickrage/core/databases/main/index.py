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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from CodernityDB.hash_index import HashIndex


class MainTVShowsIndex(HashIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = 'I'
        super(MainTVShowsIndex, self).__init__(*args, **kwargs)

    def make_key(self, key):
        return key

    def make_key_value(self, data):
        if data.get('_t') == 'tv_shows' and data.get('indexer_id'):
            return data.get('indexer_id'), None


class MainTVEpisodesIndex(HashIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = 'I'
        super(MainTVEpisodesIndex, self).__init__(*args, **kwargs)

    def make_key(self, key):
        return key

    def make_key_value(self, data):
        if data.get('_t') == 'tv_episodes' and data.get('showid'):
            return data.get('showid'), None


class MainIMDBInfoIndex(HashIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = 'I'
        super(MainIMDBInfoIndex, self).__init__(*args, **kwargs)

    def make_key(self, key):
        return key

    def make_key_value(self, data):
        if data.get('_t') == 'imdb_info' and data.get('indexer_id'):
            return data.get('indexer_id'), None


class MainSceneNumberingIndex(HashIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = 'I'
        super(MainSceneNumberingIndex, self).__init__(*args, **kwargs)

    def make_key(self, key):
        return key

    def make_key_value(self, data):
        if data.get('_t') == 'scene_numbering' and data.get('indexer_id'):
            return data.get('indexer_id'), None


class MainXEMRefreshIndex(HashIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = 'I'
        super(MainXEMRefreshIndex, self).__init__(*args, **kwargs)

    def make_key(self, key):
        return key

    def make_key_value(self, data):
        if data.get('_t') == 'xem_refresh' and data.get('indexer_id'):
            return data.get('indexer_id'), None


class MainIndexerMappingIndex(HashIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = 'I'
        super(MainIndexerMappingIndex, self).__init__(*args, **kwargs)

    def make_key(self, key):
        return key

    def make_key_value(self, data):
        if data.get('_t') == 'indexer_mapping' and data.get('indexer_id'):
            return data.get('indexer_id'), None


class MainHistoryIndex(HashIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = 'I'
        super(MainHistoryIndex, self).__init__(*args, **kwargs)

    def make_key(self, key):
        return key

    def make_key_value(self, data):
        if data.get('_t') == 'history' and data.get('showid'):
            return data.get('showid'), None


class MainInfoIndex(HashIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = 'I'
        super(MainInfoIndex, self).__init__(*args, **kwargs)

    def make_key(self, key):
        return key

    def make_key_value(self, data):
        if data.get('_t') == 'info' and data.get('last_indexer'):
            return data.get('last_indexer'), None


class MainBlacklistIndex(HashIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = 'I'
        super(MainBlacklistIndex, self).__init__(*args, **kwargs)

    def make_key(self, key):
        return key

    def make_key_value(self, data):
        if data.get('_t') == 'blacklist' and data.get('show_id'):
            return data.get('show_id'), None


class MainWhitelistIndex(HashIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = 'I'
        super(MainWhitelistIndex, self).__init__(*args, **kwargs)

    def make_key(self, key):
        return key

    def make_key_value(self, data):
        if data.get('_t') == 'whitelist' and data.get('show_id'):
            return data.get('show_id'), None
