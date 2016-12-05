
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


class LastUpdateIndex(HashIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(LastUpdateIndex, self).__init__(*args, **kwargs)

    def make_key_value(self, data):
        if data.get('_t') == 'lastUpdate' and data.get('provider'):
            return md5(data.get('provider')).hexdigest(), None

    def make_key(self, key):
        return md5(key).hexdigest()


class LastSearchIndex(HashIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(LastSearchIndex, self).__init__(*args, **kwargs)

    def make_key_value(self, data):
        if data.get('_t') == 'lastSearch' and data.get('provider'):
            return md5(data.get('provider')).hexdigest(), None

    def make_key(self, key):
        return md5(key).hexdigest()


class SceneExceptionsIndex(HashIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = 'I'
        super(SceneExceptionsIndex, self).__init__(*args, **kwargs)

    def make_key_value(self, data):
        if data.get('_t') == 'scene_exceptions' and data.get('indexer_id'):
            return data.get('indexer_id'), None

    def make_key(self, key):
        return key


class SceneNamesIndex(HashIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(SceneNamesIndex, self).__init__(*args, **kwargs)

    def make_key_value(self, data):
        if data.get('_t') == 'scene_names' and data.get('name'):
            return md5(data.get('name')).hexdigest(), None

    def make_key(self, key):
        return md5(key).hexdigest()


class NetworkTimezonesIndex(HashIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(NetworkTimezonesIndex, self).__init__(*args, **kwargs)

    def make_key_value(self, data):
        if data.get('_t') == 'network_timezones' and data.get('network_name'):
            return md5(data.get('network_name')).hexdigest(), None

    def make_key(self, key):
        return md5(key).hexdigest()


class SceneExceptionsRefreshIndex(HashIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(SceneExceptionsRefreshIndex, self).__init__(*args, **kwargs)

    def make_key_value(self, data):
        if data.get('_t') == 'scene_exceptions_refresh' and data.get('list'):
            return md5(data.get('list')).hexdigest(), None

    def make_key(self, key):
        return md5(key).hexdigest()

class ProvidersIndex(HashIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(ProvidersIndex, self).__init__(*args, **kwargs)

    def make_key_value(self, data):
        if data.get('_t') == 'providers' and data.get('provider'):
            return md5(data.get('provider')).hexdigest(), None

    def make_key(self, key):
        return md5(key).hexdigest()
