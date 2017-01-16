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

from base64 import b64encode

import sickrage
from sickrage.clients import GenericClient
from sickrage.clients.synchronousdeluge.client import DelugeClient


class DelugeDAPI(GenericClient):
    drpc = None

    def __init__(self, host=None, username=None, password=None):
        super(DelugeDAPI, self).__init__('DelugeD', host, username, password)

    def _get_auth(self):
        if not self.connect():
            return None

        return True

    def connect(self, reconnect=False):
        hostname = self.host.replace("/", "").split(':')

        if not self.drpc or reconnect:
            self.drpc = DelugeRPC(hostname[1], port=hostname[2], username=self.username, password=self.password)

        return self.drpc

    def _add_torrent_uri(self, result):
        # label = sickrage.TORRENT_LABEL
        # if result.show.is_anime:
        #     label = sickrage.TORRENT_LABEL_ANIME

        options = {
            'add_paused': sickrage.srCore.srConfig.TORRENT_PAUSED
        }

        remote_torrent = self.drpc.add_torrent_magnet(result.url, options, result.hash)

        if not remote_torrent:
            return None

        result.hash = remote_torrent

        return remote_torrent

    def _add_torrent_file(self, result):
        # label = sickrage.TORRENT_LABEL
        # if result.show.is_anime:
        #     label = sickrage.TORRENT_LABEL_ANIME

        if not result.content:
            result.content = {}
            return None

        options = {
            'add_paused': sickrage.srCore.srConfig.TORRENT_PAUSED
        }

        remote_torrent = self.drpc.add_torrent_file(result.name + '.torrent', result.content, options, result.hash)

        if not remote_torrent:
            return None

        result.hash = remote_torrent

        return remote_torrent

    def _set_torrent_label(self, result):

        label = sickrage.srCore.srConfig.TORRENT_LABEL
        if result.show.is_anime:
            label = sickrage.srCore.srConfig.TORRENT_LABEL_ANIME
        if ' ' in label:
            sickrage.srCore.srLogger.error(self.name + ': Invalid label. Label must not contain a space')
            return False

        if label:
            return self.drpc.set_torrent_label(result.hash, label)
        return True

    def _set_torrent_ratio(self, result):
        if result.ratio:
            ratio = float(result.ratio)
            return self.drpc.set_torrent_ratio(result.hash, ratio)
        return True

    def _set_torrent_priority(self, result):
        if result.priority == 1:
            return self.drpc.set_torrent_priority(result.hash, True)
        return True

    def _set_torrent_path(self, result):

        path = sickrage.srCore.srConfig.TORRENT_PATH
        if path:
            return self.drpc.set_torrent_path(result.hash, path)
        return True

    def _set_torrent_pause(self, result):

        if sickrage.srCore.srConfig.TORRENT_PAUSED:
            return self.drpc.pause_torrent(result.hash)
        return True

    def testAuthentication(self):
        if self.connect(True) and self.drpc.test():
            return True, 'Success: Connected and Authenticated'
        else:
            return False, 'Error: Unable to Authenticate!  Please check your config!'


class DelugeRPC(object):
    host = 'localhost'
    port = 58846
    username = None
    password = None
    client = None

    def __init__(self, host='localhost', port=58846, username=None, password=None):
        super(DelugeRPC, self).__init__()

        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def connect(self):
        self.client = DelugeClient()
        self.client.connect(self.host, int(self.port), self.username, self.password)

    def test(self):
        try:
            self.connect()
        except Exception:
            return False
        return True

    def add_torrent_magnet(self, torrent, options, torrent_hash):
        torrent_id = False
        try:
            self.connect()
            # noinspection PyUnresolvedReferences
            torrent_id = self.client.core.add_torrent_magnet(torrent, options).get()
            if not torrent_id:
                torrent_id = self._check_torrent(torrent_hash)
        except Exception:
            return False
        finally:
            if self.client:
                self.disconnect()

        return torrent_id

    def add_torrent_file(self, filename, torrent, options, torrent_hash):
        torrent_id = False
        try:
            self.connect()
            # noinspection PyUnresolvedReferences
            torrent_id = self.client.core.add_torrent_file(filename, b64encode(torrent), options).get()
            if not torrent_id:
                torrent_id = self._check_torrent(torrent_hash)
        except Exception:
            return False
        finally:
            if self.client:
                self.disconnect()

        return torrent_id

    def set_torrent_label(self, torrent_id, label):
        try:
            self.connect()
            # noinspection PyUnresolvedReferences
            self.client.label.set_torrent(torrent_id, label).get()
        except Exception:
            return False
        finally:
            if self.client:
                self.disconnect()
        return True

    def set_torrent_path(self, torrent_id, path):
        try:
            self.connect()
            # noinspection PyUnresolvedReferences
            self.client.core.set_torrent_move_completed_path(torrent_id, path).get()
            # noinspection PyUnresolvedReferences
            self.client.core.set_torrent_move_completed(torrent_id, 1).get()
        except Exception:
            return False
        finally:
            if self.client:
                self.disconnect()
        return True

    def set_torrent_priority(self, torrent_ids, priority):
        try:
            self.connect()
            if priority:
                # noinspection PyUnresolvedReferences
                self.client.core.queue_top([torrent_ids]).get()
        except Exception, err:
            return False
        finally:
            if self.client:
                self.disconnect()
        return True

    def set_torrent_ratio(self, torrent_ids, ratio):
        try:
            self.connect()
            # noinspection PyUnresolvedReferences
            self.client.core.set_torrent_stop_at_ratio(torrent_ids, True).get()
            # noinspection PyUnresolvedReferences
            self.client.core.set_torrent_stop_ratio(torrent_ids, ratio).get()
        except Exception, err:
            return False
        finally:
            if self.client:
                self.disconnect()
        return True

    def pause_torrent(self, torrent_ids):
        try:
            self.connect()
            # noinspection PyUnresolvedReferences
            self.client.core.pause_torrent(torrent_ids).get()
        except Exception:
            return False
        finally:
            if self.client:
                self.disconnect()
        return True

    def disconnect(self):
        self.client.disconnect()

    def _check_torrent(self, torrent_hash):
        # noinspection PyUnresolvedReferences
        torrent_id = self.client.core.get_torrent_status(torrent_hash, {}).get()
        if torrent_id['hash']:
            sickrage.srCore.srLogger.debug('DelugeD: Torrent already exists in Deluge')
            return torrent_hash
        return False


api = DelugeDAPI()
