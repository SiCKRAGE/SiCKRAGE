
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

import re
from urllib import urlencode

import sickrage
from sickrage.clients import GenericClient


class PutioAPI(GenericClient):
    def __init__(self, host=None, username=None, password=None):
        super(PutioAPI, self).__init__('putio', host, username, password)

        self.client_id = "48901323822-1arri7nf5i65fartv81e4odekbt8c7td.apps.googleusercontent.com"
        self.redirect_uri = 'https://auth.sickrage.ca/auth'
        self.url = 'https://api.put.io/login'

    def _get_auth(self):
        next_params = {
            'client_id': self.client_id,
            'response_type': 'token',
            'redirect_uri': self.redirect_uri
        }

        post_data = {
            'name': self.username,
            'password': self.password,
            'next': '/v2/oauth2/authenticate?' + urlencode(next_params)
        }

        try:
            response = sickrage.srCore.srWebSession.post(self.url, data=post_data,
                                                         allow_redirects=False,
                                                         verify=bool(sickrage.srCore.srConfig.TORRENT_VERIFY_CERT))

            response = sickrage.srCore.srWebSession.get(response.headers['location'],
                                                        allow_redirects=False,
                                                        verify=bool(sickrage.srCore.srConfig.TORRENT_VERIFY_CERT))

            resulting_uri = '{redirect_uri}#access_token=(.*)'.format(
                redirect_uri=re.escape(self.redirect_uri))

            self.auth = re.search(resulting_uri, response.headers['location']).group(1)
        except Exception:
            self.auth = None

        return self.auth

    def _add_torrent_uri(self, result):
        post_data = {
            'url': result.url,
            'save_parent_id': 0,
            'extract': True,
            'oauth_token': self.auth
        }

        try:
            self.response = sickrage.srCore.srWebSession.post('https://api.put.io/v2/transfers/add',
                                                              data=post_data).json()
        except Exception:
            return False

        return self.response.get("transfer", {}).get('save_parent_id', None) == 0

    def _add_torrent_file(self, result):
        post_data = {
            'name': 'putio_torrent',
            'parent': 0,
            'oauth_token': self.auth
        }

        try:
            sickrage.srCore.srWebSession.post('https://api.put.io/v2/files/upload',
                                              data=post_data, files=('putio_torrent', result.content))
        except Exception:
            return False

        return self.response.json()['status'] == "OK"


api = PutioAPI()
