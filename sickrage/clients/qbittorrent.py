# Author: Mr_Orange <mr_orange@hotmail.it>
# URL: https://sickrage.ca
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.

import sickrage
from sickrage.clients import GenericClient
from sickrage.core.tv.show.helpers import find_show


class qbittorrentAPI(GenericClient):
    def __init__(self, host=None, username=None, password=None):
        super(qbittorrentAPI, self).__init__('qbittorrent', host, username, password)
        self.url = self.host

    @property
    def api(self):
        """Get API version."""
        try:
            self.url = '{}version/api'.format(self.host)
            version = int(self.session.get(self.url, verify=sickrage.app.config.torrent_verify_cert).content)
        except Exception:
            version = 1

        return version

    def _get_auth(self):
        if self.api > 1:
            self.url = '{host}login'.format(host=self.host)
            data = {
                'username': self.username,
                'password': self.password,
            }
            try:
                self.response = self.session.post(self.url, data=data)
            except Exception:
                return None

        else:
            try:
                self.response = self.session.get(self.host, verify=sickrage.app.config.torrent_verify_cert)
                self.auth = self.response.content
            except Exception:
                return None

        self.session.cookies = self.response.cookies
        self.auth = self.response.content

        return self.auth if not self.response.status_code == 404 else None

    def _set_torrent_label(self, result):
        label = sickrage.app.config.torrent_label
        show_object = find_show(result.show_id)

        if show_object.is_anime:
            label = sickrage.app.config.torrent_label_anime

        if self.api > 6 and label:
            label_key = 'Category' if self.api >= 10 else 'Label'
            self.url = '{}command/set{}'.format(self.host, label_key)
            data = {
                'hashes': result.hash.lower(),
                label_key.lower(): label.replace(' ', '_'),
            }
            return self._request(method='post', data=data, cookies=self.session.cookies)
        return True

    def _add_torrent_uri(self, result):
        self.url = '{}command/download'.format(self.host)
        data = {'urls': result.url}
        return self._request(method='post', data=data, cookies=self.session.cookies)

    def _add_torrent_file(self, result):
        self.url = '{}command/upload'.format(self.host)
        files = {'torrent': result.content}
        return self._request(method='post', files=files, cookies=self.session.cookies)

    def _set_torrent_priority(self, result):
        self.url = '{}command/{}Prio'.format(self.host, 'increase' if result.priority == 1 else 'decrease')
        data = {'hashes': result.hash}
        return self._request(method='post', data=data, cookies=self.session.cookies)

    def _set_torrent_pause(self, result):
        self.url = '{}command/{}'.format(self.host, 'pause' if sickrage.app.config.torrent_paused else 'resume')
        data = {'hash': result.hash}
        return self._request(method='post', data=data, cookies=self.session.cookies)

    def remove_torrent(self, info_hash):
        self.url = '{}command/deletePerm'.format(self.host)
        data = {
            'hashes': info_hash.lower(),
        }
        return self._request(method='post', data=data, cookies=self.session.cookies)


api = qbittorrentAPI()
