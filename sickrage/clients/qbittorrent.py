# Author: Mr_Orange <mr_orange@hotmail.it>
# URL: http://github.com/SiCKRAGETV/SickRage/
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

from requests.auth import HTTPDigestAuth

import sickrage
from sickrage.clients import GenericClient


class qbittorrentAPI(GenericClient):
    def __init__(self, host=None, username=None, password=None):
        super(qbittorrentAPI, self).__init__('qbittorrent', host, username, password)
        self.url = self.host

    def _get_auth(self):

        try:
            self.response = sickrage.srCore.srWebSession.get(self.host,
                                                             auth=HTTPDigestAuth(self.username, self.password),
                                                             raise_exceptions=False,
                                                             verify=bool(sickrage.srCore.srConfig.TORRENT_VERIFY_CERT))

            self.auth = self.response.text
        except Exception:
            return None

        return self.auth if not self.response.status_code == 404 else None

    def _add_torrent_uri(self, result):

        self.url = self.host + 'command/download'
        data = {'urls': result.url}
        return self._request(method='post', data=data)

    def _add_torrent_file(self, result):

        self.url = self.host + 'command/upload'
        files = {'torrents': (result.name + '.torrent', result.content)}
        return self._request(method='post', files=files)

    def _set_torrent_priority(self, result):

        self.url = self.host + 'command/decreasePrio '
        if result.priority == 1:
            self.url = self.host + 'command/increasePrio'

        data = {'hashes': result.hash}
        return self._request(method='post', data=data)

    def _set_torrent_pause(self, result):

        self.url = self.host + 'command/resume'
        if sickrage.srCore.srConfig.TORRENT_PAUSED:
            self.url = self.host + 'command/pause'

        data = {'hash': result.hash}
        return self._request(method='post', data=data)


api = qbittorrentAPI()
