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

from urlparse import urljoin

import sickrage
from sickrage.clients import GenericClient


class DownloadStationAPI(GenericClient):
    def __init__(self, host=None, username=None, password=None):

        super(DownloadStationAPI, self).__init__('DownloadStation', host, username, password)

        self.urls = {
            'auth': urljoin(self.host, 'webapi/auth.cgi'),
            'task': urljoin(self.host, 'webapi/DownloadStation/task.cgi'),
        }

        self.url = self.urls['task']

        self.post_task = {
            'method': 'create',
            'version': '1',
            'api': 'SYNO.DownloadStation.Task',
            'session': 'DownloadStation',
        }

        self.error_map = {
            'generic': {
                100: 'Unknown error',
                101: 'Invalid parameter',
                102: 'The requested API does not exist',
                103: 'The requested method does not exist',
                104: 'The requested version does not support the functionality',
                105: 'The logged in session does not have permission',
                106: 'Session timeout',
                107: 'Session interrupted by duplicate login',
            },
            'create': {
                400: 'File upload failed',
                401: 'Max number of tasks reached',
                402: 'Destination denied',
                403: 'Destination does not exist',
                404: 'Invalid task id',
                405: 'Invalid task action',
                406: 'No default destination',
                407: 'Set destination failed',
                408: 'File does not exist'
            },
            'login': {
                400: 'No such account or incorrect password',
                401: 'Account disabled',
                402: 'Permission denied',
                403: '2-step verification code required',
                404: 'Failed to authenticate 2-step verification code'
            }
        }

    @property
    def response(self):
        try:
            resp = self._response.json()
        except (ValueError, AttributeError):
            sickrage.app.log.info(
                'Could not convert response to json, check the host:port: {!r}'.format(self.response))
            return False

        if not resp.get('success'):
            error_code = resp.get('error', {}).get('code')
            api_method = resp.get('method', 'generic')
            log_string = self.error_map.get(api_method)[error_code]
            sickrage.app.log.info('{}: {}'.format(self.name, log_string))
        elif resp.get('data', {}).get('sid'):
            self.post_task['_sid'] = resp['data']['sid']

        return resp.get('success')

    @response.setter
    def response(self, value):
        self._response = value

    def _get_auth(self):
        if self.auth:
            return self.auth

        params = {
            'api': 'SYNO.API.Auth',
            'version': 2,
            'method': 'login',
            'account': self.username,
            'passwd': self.password,
            'session': 'DownloadStation',
            'format': 'cookie'
        }

        try:
            # login to API
            self.response = sickrage.app.srWebSession.get(self.urls['auth'],
                                                             params=params,
                                                             verify=bool(sickrage.app.config.TORRENT_VERIFY_CERT))

            # get sid
            self.auth = self.response
        except Exception:
            self.auth = None

        return self.auth

    def _add_torrent_uri(self, result):
        data = self.post_task
        data['uri'] = result.url

        return self._send_dsm_request(method='post', data=data)

    def _add_torrent_file(self, result):
        data = self.post_task
        files = {'file': ('{}.torrent'.format(result.name), result.content)}

        return self._send_dsm_request(method='post', data=data, files=files)

    def _send_dsm_request(self, method, data, **kwargs):

        if sickrage.app.config.TORRENT_PATH:
            data['destination'] = sickrage.app.config.TORRENT_PATH

        self._request(method=method, data=data, **kwargs)
        return self.response


api = DownloadStationAPI()
