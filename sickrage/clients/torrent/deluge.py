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

import sickrage
from sickrage.clients import TorrentClient
from sickrage.core.tv.show.helpers import find_show


class DelugeAPI(TorrentClient):
    def __init__(self, host=None, username=None, password=None):

        super(DelugeAPI, self).__init__('Deluge', host, username, password)

        self.url = self.host + 'json'
        self.session.headers.update({'Content-type': "application/json"})

    def _get_auth(self):
        post_data = {"method": "auth.login",
                     "params": [self.password],
                     "id": 1}

        self.response = self.session.post(self.url, json=post_data, verify=bool(sickrage.app.config.torrent.verify_cert))
        if not self.response or not self.response.content:
            return None

        try:
            data = self.response.json()
        except ValueError:
            return None

        self.auth = data.get("result")

        post_data = {
            "method": "web.connected",
            "params": [],
            "id": 10
        }

        self.response = self.session.post(self.url, json=post_data, verify=bool(sickrage.app.config.torrent.verify_cert))
        if not self.response or not self.response.content:
            return None

        try:
            connected = self.response.json()
        except ValueError:
            return None

        if not connected.get('result'):
            post_data = {
                "method": "web.get_hosts",
                "params": [],
                "id": 11
            }

            self.response = self.session.post(self.url, json=post_data, verify=bool(sickrage.app.config.torrent.verify_cert))
            if not self.response or not self.response.content:
                return None

            try:
                hosts = self.response.json()
            except ValueError:
                return None

            if not hosts.get('result'):
                sickrage.app.log.warning(self.name + ': WebUI does not contain daemons')
                return None

            post_data = {
                "method": "web.connect",
                "params": [hosts[0][0]],
                "id": 11
            }

            self.response = self.session.post(self.url, json=post_data, verify=bool(sickrage.app.config.torrent.verify_cert))
            if not self.response:
                return None

            post_data = {
                "method": "web.connected",
                "params": [],
                "id": 10
            }

            self.response = self.session.post(self.url, json=post_data, verify=bool(sickrage.app.config.torrent.verify_cert))
            if not self.response or not self.response.content:
                return None

            try:
                connected = self.response.json()
            except ValueError:
                return None

            if not connected.get('result'):
                sickrage.app.log.warning(self.name + ': WebUI could not connect to daemon')
                return None

        return self.auth

    def _add_torrent_uri(self, result):
        post_data = {"method": "core.add_torrent_magnet",
                     "params": [result.url, {}],
                     "id": 2}

        self._request(method='post', json=post_data)

        result.hash = self.response.json()['result']

        return self.response.json()['result']

    def _add_torrent_file(self, result):
        post_data = {"method": "core.add_torrent_file",
                     "params": [result.name + '.torrent', b64encode(result.content), {}],
                     "id": 2}

        self._request(method='post', json=post_data)

        result.hash = self.response.json()['result']

        return self.response.json()['result']

    def _set_torrent_label(self, result):
        label = sickrage.app.config.torrent.label

        tv_show = find_show(result.series_id, result.series_provider_id)

        if tv_show.is_anime:
            label = sickrage.app.config.torrent.label_anime

        if ' ' in label:
            sickrage.app.log.warning(self.name + ': Invalid label. Label must not contain a space')
            return False

        if label:
            # check if label already exists and create it if not
            post_data = {"method": 'label.get_labels',
                         "params": [],
                         "id": 3}

            self._request(method='post', json=post_data)
            labels = self.response.json()['result']

            if labels is not None:
                if label not in labels:
                    sickrage.app.log.debug(self.name + ': ' + label + " label does not exist in Deluge we must add it")
                    post_data = {"method": 'label.add',
                                 "params": [label],
                                 "id": 4}

                    self._request(method='post', json=post_data)
                    sickrage.app.log.debug(self.name + ': ' + label + " label added to Deluge")

                # add label to torrent
                post_data = {"method": 'label.set_torrent',
                             "params": [result.hash, label],
                             "id": 5}

                self._request(method='post', json=post_data)
                sickrage.app.log.debug(self.name + ': ' + label + " label added to torrent")
            else:
                sickrage.app.log.debug(self.name + ': ' + "label plugin not detected")
                return False

        return not self.response.json()['error']

    def _set_torrent_ratio(self, result):
        ratio = None
        if result.ratio:
            ratio = result.ratio

        if ratio:
            post_data = {"method": "core.set_torrent_stop_at_ratio",
                         "params": [result.hash, True],
                         "id": 5}

            self._request(method='post', json=post_data)

            post_data = {"method": "core.set_torrent_stop_ratio",
                         "params": [result.hash, float(ratio)],
                         "id": 6}

            self._request(method='post', json=post_data)

            return not self.response.json()['error']

        return True

    def _set_torrent_path(self, result):
        if sickrage.app.config.torrent.path:
            post_data = {"method": "core.set_torrent_move_completed",
                         "params": [result.hash, True],
                         "id": 7}

            self._request(method='post', json=post_data)

            post_data = {"method": "core.set_torrent_move_completed_path",
                         "params": [result.hash, sickrage.app.config.torrent.path],
                         "id": 8}

            self._request(method='post', json=post_data)

            return not self.response.json()['error']

        return True

    def _set_torrent_pause(self, result):
        if sickrage.app.config.torrent.paused:
            post_data = {"method": "core.pause_torrent",
                         "params": [[result.hash]],
                         "id": 9}

            self._request(method='post', json=post_data)

            return not self.response.json()['error']

        return True
