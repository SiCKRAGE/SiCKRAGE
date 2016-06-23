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


class mlnetAPI(GenericClient):
    def __init__(self, host=None, username=None, password=None):

        super(mlnetAPI, self).__init__('mlnet', host, username, password)

        self.url = self.host

    def _get_auth(self):

        try:
            self.response = sickrage.srCore.srWebSession.get(self.host,
                                                             auth=(self.username, self.password),
                                                             raise_exceptions=False,
                                                             verify=bool(sickrage.srCore.srConfig.TORRENT_VERIFY_CERT))
            self.auth = self.response.text
        except Exception:
            return None

        return self.auth if not self.response.status_code == 404 else None

    def _add_torrent_uri(self, result):

        self.url = self.host + 'submit'
        params = {'q': 'dllink ' + result.url}
        return self._request(method='get', params=params)

    def _add_torrent_file(self, result):

        self.url = self.host + 'submit'
        params = {'q': 'dllink ' + result.url}
        return self._request(method='get', params=params)


api = mlnetAPI()
