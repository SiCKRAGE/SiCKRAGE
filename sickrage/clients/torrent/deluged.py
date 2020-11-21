# ##############################################################################
#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#  -
#  This file is part of SiCKRAGE.
#  -
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  -
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
# ##############################################################################


from base64 import b64encode

from deluge_client import DelugeRPCClient

import sickrage
from sickrage.clients import TorrentClient
from sickrage.core.tv.show.helpers import find_show


class DelugeDAPI(TorrentClient):
    drpc = None

    def __init__(self, host=None, username=None, password=None):
        super(DelugeDAPI, self).__init__('DelugeD', host, username, password)

    def _get_auth(self):
        if not self.connect():
            return None

        return True

    def connect(self, reconnect=False):
        hostname = self.host.replace("/", "").split(':')
        if not len(hostname) == 3:
            return self.drpc

        if not self.drpc or reconnect:
            self.drpc = DelugeRPC(hostname[1], port=hostname[2], username=self.username, password=self.password)

        return self.drpc

    def _add_torrent_uri(self, result):
        # label = sickrage.TORRENT_LABEL
        # if result.show.is_anime:
        #     label = sickrage.TORRENT_LABEL_ANIME

        options = {
            'add_paused': sickrage.app.config.torrent.paused
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
            'add_paused': sickrage.app.config.torrent.paused
        }

        remote_torrent = self.drpc.add_torrent_file(result.name + '.torrent', result.content, options, result.hash)

        if not remote_torrent:
            return None

        result.hash = remote_torrent

        return remote_torrent

    def _set_torrent_label(self, result):
        label = sickrage.app.config.torrent.label

        tv_show = find_show(result.series_id, result.series_provider_id)

        if tv_show.is_anime:
            label = sickrage.app.config.torrent.label_anime

        if ' ' in label:
            sickrage.app.log.warning(self.name + ': Invalid label. Label must not contain a space')
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

        path = sickrage.app.config.torrent.path
        if path:
            return self.drpc.set_torrent_path(result.hash, path)
        return True

    def _set_torrent_pause(self, result):

        if sickrage.app.config.torrent.paused:
            return self.drpc.pause_torrent(result.hash)
        return True

    def test_authentication(self):
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
        self.client = DelugeRPCClient(self.host, int(self.port), self.username, self.password)
        self.client.connect()
        return self.client.connected

    def disconnect(self):
        self.client.disconnect()

    def test(self):
        try:
            return self.connect()
        except Exception:
            return False

    def add_torrent_magnet(self, torrent, options, torrent_hash):
        try:
            if not self.connect():
                return False

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
        try:
            if not self.connect():
                return False

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
            if not self.connect():
                return False

            self.client.label.set_torrent(torrent_id, label).get()
        except Exception:
            return False
        finally:
            if self.client:
                self.disconnect()

        return True

    def set_torrent_path(self, torrent_id, path):
        try:
            if not self.connect():
                return False

            self.client.core.set_torrent_move_completed_path(torrent_id, path).get()
            self.client.core.set_torrent_move_completed(torrent_id, 1).get()
        except Exception:
            return False
        finally:
            if self.client:
                self.disconnect()

        return True

    def set_torrent_priority(self, torrent_ids, priority):
        try:
            if not self.connect():
                return False

            if priority:
                self.client.core.queue_top([torrent_ids]).get()
        except Exception as err:
            return False
        finally:
            if self.client:
                self.disconnect()
        return True

    def set_torrent_ratio(self, torrent_ids, ratio):
        try:
            if not self.connect():
                return False

            self.client.core.set_torrent_stop_at_ratio(torrent_ids, True).get()
            self.client.core.set_torrent_stop_ratio(torrent_ids, ratio).get()
        except Exception as err:
            return False
        finally:
            if self.client:
                self.disconnect()

        return True

    def pause_torrent(self, torrent_ids):
        try:
            if not self.connect():
                return False

            self.client.core.pause_torrent(torrent_ids).get()
        except Exception:
            return False
        finally:
            if self.client:
                self.disconnect()

        return True

    def _check_torrent(self, torrent_hash):
        torrent_id = self.client.core.get_torrent_status(torrent_hash, {}).get()
        if torrent_id['hash']:
            sickrage.app.log.debug('DelugeD: Torrent already exists in Deluge')
            return torrent_hash

        return False
