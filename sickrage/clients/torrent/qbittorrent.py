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
from sickrage.clients import TorrentClient
from sickrage.core.tv.show.helpers import find_show


class QBittorrentAPI(TorrentClient):
    def __init__(self, host=None, username=None, password=None):
        super(QBittorrentAPI, self).__init__('qbittorrent', host, username, password)
        self.api_version = None

    def get_api_version(self):
        """Get API version."""
        version = (1, 0, 0)

        url = urljoin(self.host, 'api/v2/app/webapiVersion')
        response = self.session.get(url, verify=sickrage.app.config.torrent.verify_cert)

        try:
            if response and response.text:
                version = tuple(map(int, response.text.split('.')))
                version + (0,) * (3 - len(version))
            elif response is not None:
                status_code = response.status_code
                if status_code == 404:
                    url = urljoin(self.host, 'version/api')
                    response = self.session.get(url, verify=sickrage.app.config.torrent.verify_cert)
                    if response and response.text:
                        version = int(response.text)
                        version = (1, version % 100, 0)
        except ValueError:
            pass

        return version

    def _get_auth(self):
        self.auth = False

        data = {
            'username': self.username,
            'password': self.password
        }

        url = urljoin(self.host, 'api/v2/auth/login')
        self.response = self.session.post(url, data=data, verify=sickrage.app.config.torrent.verify_cert)
        if self.response and self.response.text and not self.response.text == 'Fails.':
            self.session.cookies = self.response.cookies
            self.auth = True
        elif self.response is not None:
            status_code = self.response.status_code
            if status_code == 404:
                url = urljoin(self.host, 'login')
                self.response = self.session.post(url, data=data, verify=sickrage.app.config.torrent.verify_cert)
                if self.response:
                    self.session.cookies = self.response.cookies
                    self.auth = True

        if self.auth:
            self.api_version = self.get_api_version()
        else:
            sickrage.app.log.warning('{name}: Invalid Username or Password, check your config'.format(name=self.name))

        return self.auth

    def _set_torrent_label(self, result):
        label = sickrage.app.config.torrent.label_anime if find_show(result.series_id, result.series_provider_id).is_anime else sickrage.app.config.torrent.label
        if not label:
            return True

        data = {'hashes': result.hash.lower()}

        if self.api_version >= (2, 0, 0):
            label_key = 'category'
            data[label_key.lower()] = label.replace(' ', '_')
            self.url = urljoin(self.host, 'api/v2/torrents/setCategory')
        elif self.api_version > (1, 6, 0) and label:
            label_key = 'Category' if self.api_version >= (1, 10, 0) else 'Label'
            data[label_key.lower()] = label.replace(' ', '_')
            self.url = urljoin(self.host, 'command/set{}'.format(label_key))

        return self._request(method='post', data=data, cookies=self.session.cookies)

    def _add_torrent_uri(self, result):
        command = 'api/v2/torrents/add' if self.api_version >= (2, 0, 0) else 'command/download'
        self.url = urljoin(self.host, command)
        data = {'urls': result.url}
        return self._request(method='post', data=data, cookies=self.session.cookies)

    def _add_torrent_file(self, result):
        command = 'api/v2/torrents/add' if self.api_version >= (2, 0, 0) else 'command/upload'
        self.url = urljoin(self.host, command)
        files = {'torrent': result.content}
        return self._request(method='post', files=files, cookies=self.session.cookies)

    def _set_torrent_priority(self, result):
        command = 'api/v2/torrents' if self.api_version >= (2, 0, 0) else 'command'
        priority = '{}Prio'.format('increase' if result.priority == 1 else 'decrease')
        self.url = urljoin(self.host, '{command}/{priority}'.format(command=command, priority=priority))
        data = {'hashes': result.hash}
        return self._request(method='post', data=data, cookies=self.session.cookies)

    def _set_torrent_pause(self, result):
        command = 'api/v2/torrents' if self.api_version >= (2, 0, 0) else 'command'
        state = 'pause' if sickrage.app.config.torrent.paused else 'resume'
        self.url = urljoin(self.host, '{command}/{state}'.format(command=command, state=state))
        data = {'hashes' if self.api_version >= (1, 18, 0) else 'hash': result.hash}
        return self._request(method='post', data=data, cookies=self.session.cookies)

    def remove_torrent(self, info_hash):
        self.url = urljoin(self.host, 'api/v2/torrents/delete' if self.api_version >= (2, 0, 0) else 'command/deletePerm')
        data = {'hashes': info_hash.lower()}
        if self.api_version >= (2, 0, 0):
            data['deleteFiles'] = True
        return self._request(method='post', data=data, cookies=self.session.cookies)
