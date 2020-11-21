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

import sickrage
from sickrage.clients import TorrentClient


class mlnetAPI(TorrentClient):
    def __init__(self, host=None, username=None, password=None):

        super(mlnetAPI, self).__init__('mlnet', host, username, password)

        self.url = self.host

    def _get_auth(self):
        self.auth = None

        self.response = self.session.get(self.host, auth=(self.username, self.password), verify=bool(sickrage.app.config.torrent.verify_cert))
        if self.response and self.response.text:
            self.auth = self.response.text

        return self.auth

    def _add_torrent_uri(self, result):

        self.url = self.host + 'submit'
        params = {'q': 'dllink ' + result.url}
        return self._request(method='get', params=params)

    def _add_torrent_file(self, result):

        self.url = self.host + 'submit'
        params = {'q': 'dllink ' + result.url}
        return self._request(method='get', params=params)
