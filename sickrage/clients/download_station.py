#!/usr/bin/env python2

# Author: echel0n <echel0n@sickrage.ca>
# URL: https://git.sickrage.ca
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

import sickrage
from sickrage.clients import GenericClient


class DownloadStationAPI(GenericClient):
    def __init__(self, host=None, username=None, password=None):

        super(DownloadStationAPI, self).__init__('DownloadStation', host, username, password)

        self.url = self.host + 'webapi/DownloadStation/task.cgi'

    def _get_auth(self):
        auth_url = self.host + 'webapi/auth.cgi?api=SYNO.API.Auth&version=2&method=login&account=' + self.username + '&passwd=' + self.password + '&session=DownloadStation&format=sid'

        try:
            self.response = sickrage.srCore.srWebSession.get(auth_url,
                                                             raise_exceptions=False,
                                                             verify=bool(sickrage.srCore.srConfig.TORRENT_VERIFY_CERT))

            self.auth = self.response.json()['data']['sid']
        except Exception:
            return None

        return self.auth

    def _add_torrent_uri(self, result):

        data = {
            'api': 'SYNO.DownloadStation.Task',
            'version': '1',
            'method': 'create',
            'session': 'DownloadStation',
            '_sid': self.auth,
            'uri': result.url
        }

        if sickrage.srCore.srConfig.TORRENT_PATH:
            data['destination'] = sickrage.srCore.srConfig.TORRENT_PATH
        self._request(method='post', data=data)

        return self.response.json()['success']

    def _add_torrent_file(self, result):

        data = {
            'api': 'SYNO.DownloadStation.Task',
            'version': '1',
            'method': 'create',
            'session': 'DownloadStation',
            '_sid': self.auth
        }

        if sickrage.srCore.srConfig.TORRENT_PATH:
            data['destination'] = sickrage.srCore.srConfig.TORRENT_PATH
        files = {'file': (result.name + '.torrent', result.content)}
        self._request(method='post', data=data, files=files)

        return self.response.json()['success']


api = DownloadStationAPI()
