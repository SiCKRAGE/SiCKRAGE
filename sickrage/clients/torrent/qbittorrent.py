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

from urllib.parse import urljoin

from requests import HTTPError

import sickrage
from sickrage.clients.torrent import GenericClient
from sickrage.core.tv.show.helpers import find_show


class QBittorrentAPI(GenericClient):
    def __init__(self, host=None, username=None, password=None):
        super(QBittorrentAPI, self).__init__('qbittorrent', host, username, password)
        self.api_version = None

    def get_api_version(self):
        """Get API version."""
        version = 1.0

        try:
            url = urljoin(self.host, 'api/v2/app/webapiVersion')
            version = float(self.session.get(url, verify=sickrage.app.config.torrent_verify_cert).text)
        except HTTPError as e:
            status_code = e.response.status_code
            if status_code == 404:
                url = urljoin(self.host, 'version/api')
                try:
                    version = float(self.session.get(url, verify=sickrage.app.config.torrent_verify_cert).text)
                except HTTPError as e:
                    pass

        return version

    def _get_auth(self):
        self.auth = False

        data = {
            'username': self.username,
            'password': self.password
        }

        try:
            url = urljoin(self.host, 'api/v2/auth/login')
            self.response = self.session.post(url, data=data, verify=sickrage.app.config.torrent_verify_cert)
            self.session.cookies = self.response.cookies
            self.auth = True
        except HTTPError as e:
            status_code = e.response.status_code
            if status_code == 404:
                try:
                    url = urljoin(self.host, 'login')
                    self.response = self.session.post(url, data=data, verify=sickrage.app.config.torrent_verify_cert)
                    self.session.cookies = self.response.cookies
                    self.auth = True
                except HTTPError as e:
                    pass

        if self.auth:
            self.api_version = self.get_api_version()

        return self.auth

    def _set_torrent_label(self, result):
        label = sickrage.app.config.torrent_label_anime if find_show(result.show_id).is_anime else sickrage.app.config.torrent_label
        if not label:
            return True

        data = {'hashes': result.hash.lower()}

        if self.api_version >= 2.0:
            label_key = 'category'
            data[label_key.lower()] = label.replace(' ', '_')
            self.url = urljoin(self.host, 'api/v2/torrents/setCategory')
        elif self.api_version > 1.6 and label:
            label_key = 'Category' if self.api_version >= 1.10 else 'Label'
            data[label_key.lower()] = label.replace(' ', '_')
            self.url = urljoin(self.host, 'command/set{}'.format(label_key))

        return self._request(method='post', data=data, cookies=self.session.cookies)

    def _add_torrent_uri(self, result):
        command = 'api/v2/torrents/add' if self.api_version >= 2.0 else 'command/download'
        self.url = urljoin(self.host, command)
        data = {'urls': result.url}
        return self._request(method='post', data=data, cookies=self.session.cookies)

    def _add_torrent_file(self, result):
        command = 'api/v2/torrents/add' if self.api_version >= 2.0 else 'command/upload'
        self.url = urljoin(self.host, command)
        files = {'torrent': result.content}
        return self._request(method='post', files=files, cookies=self.session.cookies)

    def _set_torrent_priority(self, result):
        command = 'api/v2/torrents' if self.api_version >= 2.0 else 'command'
        priority = '{}Prio'.format('increase' if result.priority == 1 else 'decrease')
        self.url = urljoin(self.host, command, priority)
        data = {'hashes': result.hash}
        return self._request(method='post', data=data, cookies=self.session.cookies)

    def _set_torrent_pause(self, result):
        command = 'api/v2/torrents' if self.api_version >= 2.0 else 'command'
        state = 'pause' if sickrage.app.config.torrent_paused else 'resume'
        self.url = urljoin(self.host, command, state)
        data = {'hashes' if self.api_version >= 1.18 else 'hash': result.hash}
        return self._request(method='post', data=data, cookies=self.session.cookies)

    def remove_torrent(self, info_hash):
        self.url = urljoin(self.host, 'api/v2/torrents/delete' if self.api_version >= 2.0 else 'command/deletePerm')
        data = {'hashes': info_hash.lower()}
        if self.api_version >= 2.0:
            data['deleteFiles'] = True
        return self._request(method='post', data=data, cookies=self.session.cookies)

