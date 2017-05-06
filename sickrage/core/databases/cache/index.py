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

from hashlib import md5

from CodernityDB.hash_index import HashIndex


class CacheLastUpdateIndex(HashIndex):
    _version = 2

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(CacheLastUpdateIndex, self).__init__(*args, **kwargs)

    def make_key_value(self, data):
        if data.get('_t') == 'lastUpdate' and data.get('provider'):
            return md5(data.get('provider')).hexdigest(), None

    def make_key(self, key):
        return md5(key.encode('utf-8')).hexdigest()


class CacheLastSearchIndex(HashIndex):
    _version = 2

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(CacheLastSearchIndex, self).__init__(*args, **kwargs)

    def make_key_value(self, data):
        if data.get('_t') == 'lastSearch' and data.get('provider'):
            return md5(data.get('provider')).hexdigest(), None

    def make_key(self, key):
        return md5(key.encode('utf-8')).hexdigest()


class CacheSceneExceptionsIndex(HashIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = 'I'
        super(CacheSceneExceptionsIndex, self).__init__(*args, **kwargs)

    def make_key_value(self, data):
        if data.get('_t') == 'scene_exceptions' and data.get('indexer_id'):
            return data.get('indexer_id'), None

    def make_key(self, key):
        return key


class CacheSceneNamesIndex(HashIndex):
    _version = 2

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(CacheSceneNamesIndex, self).__init__(*args, **kwargs)

    def make_key_value(self, data):
        if data.get('_t') == 'scene_names' and data.get('name'):
            return md5(data.get('name')).hexdigest(), None

    def make_key(self, key):
        return md5(key.encode('utf-8')).hexdigest()


class CacheNetworkTimezonesIndex(HashIndex):
    _version = 2

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(CacheNetworkTimezonesIndex, self).__init__(*args, **kwargs)

    def make_key_value(self, data):
        if data.get('_t') == 'network_timezones' and data.get('network_name'):
            return md5(data.get('network_name')).hexdigest(), None

    def make_key(self, key):
        return md5(key.encode('utf-8')).hexdigest()


class CacheSceneExceptionsRefreshIndex(HashIndex):
    _version = 2

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(CacheSceneExceptionsRefreshIndex, self).__init__(*args, **kwargs)

    def make_key_value(self, data):
        if data.get('_t') == 'scene_exceptions_refresh' and data.get('list'):
            return md5(data.get('list')).hexdigest(), None

    def make_key(self, key):
        return md5(key.encode('utf-8')).hexdigest()


class CacheProvidersIndex(HashIndex):
    _version = 2

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(CacheProvidersIndex, self).__init__(*args, **kwargs)

    def make_key_value(self, data):
        if data.get('_t') == 'providers' and data.get('provider'):
            return md5(data.get('provider')).hexdigest(), None

    def make_key(self, key):
        return md5(key.encode('utf-8')).hexdigest()
