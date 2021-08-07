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


import os
import re
from urllib.parse import urljoin

import sickrage
from sickrage.clients import TorrentClient


class DownloadStationAPI(TorrentClient):
    def __init__(self, host=None, username=None, password=None):

        super(DownloadStationAPI, self).__init__('DownloadStation', host, username, password)

        self.urls = {
            'auth': urljoin(self.host, '/webapi/auth.cgi'),
            'query': urljoin(self.host, '/webapi/query.cgi'),
            'task': urljoin(self.host, '/webapi/DownloadStation/task.cgi'),
            'info': urljoin(self.host, '/webapi/DownloadStation/info.cgi'),
        }

        self.url = self.urls['task']

        self.checked_destination = False
        self.destination = sickrage.app.config.torrent.path

        self.post_task = {
            'method': 'create',
            'api': 'SYNO.DownloadStation.Task',
            'session': 'DownloadStation',
        }

        generic_errors = {
            100: 'Unknown error',
            101: 'Invalid parameter',
            102: 'The requested API does not exist',
            103: 'The requested method does not exist',
            104: 'The requested version does not support the functionality',
            105: 'The logged in session does not have permission',
            106: 'Session timeout',
            107: 'Session interrupted by duplicate login',
        }

        self.error_map = {
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

        for api_method in self.error_map:
            self.error_map[api_method].update(generic_errors)

    def _check_response(self):
        try:
            resp = self._response.json()
        except (ValueError, AttributeError):
            self.session.cookies.clear()
            self.auth = False
            return self.auth
        else:
            self.auth = resp.get('success')
            if not self.auth:
                error_code = resp.get('error', {}).get('code')
                api_method = resp.get('method', 'login')
                log_string = self.error_map.get(api_method)[error_code]
                sickrage.app.log.info('{}: {}'.format(self.name, log_string))
                self.session.cookies.clear()
            elif resp.get('data', {}).get('sid'):
                self.post_task['_sid'] = resp['data']['sid']

        return self.auth

    def _get_auth(self):
        if self.auth:
            return self.auth

        params = {
            'api': 'SYNO.API.Auth',
            'method': 'login',
            'account': self.username,
            'passwd': self.password,
            'session': 'DownloadStation',
            'format': 'cookie'
        }

        api_info = self._get_api_info(params['api'])
        params['version'] = api_info.get('maxVersion')

        self.response = self.session.get(self.urls['auth'], params=params, verify=bool(sickrage.app.config.torrent.verify_cert))
        if not self.response:
            self.session.cookies.clear()
            self.auth = False
            return self.auth

        # get sid
        self.auth = self.response

        return self._check_response()

    def _get_api_info(self, method):
        json_data = {}

        params = {
            'api': 'SYNO.API.Info',
            'version': 1,
            'method': 'query',
            'query': method
        }

        resp = self.session.get(self.urls['query'], params=params, verify=bool(sickrage.app.config.torrent.verify_cert))
        if not resp:
            return json_data

        try:
            json_resp = resp.json()
        except (ValueError, AttributeError):
            return json_data
        else:
            success = json_resp.get('success')
            if success:
                json_data = json_resp.get('data')

        return json_data.get(method, {})

    def _add_torrent_uri(self, result):
        data = self.post_task
        api_info = self._get_api_info(data['api'])
        data['version'] = api_info.get('maxVersion')
        data['uri'] = result.url

        return self._send_dsm_request(method='post', data=data)

    def _add_torrent_file(self, result):
        data = self.post_task
        api_info = self._get_api_info(data['api'])
        data['version'] = api_info.get('maxVersion')

        files = {'file': ('{}.torrent'.format(result.name), result.content)}

        return self._send_dsm_request(method='post', data=data, files=files)

    def _check_destination(self):
        """Validate and set torrent destination."""
        torrent_path = sickrage.app.config.torrent.path

        if not (self.auth or self._get_auth()):
            return False

        if self.checked_destination and self.destination == torrent_path:
            return True

        params = {
            'api': 'SYNO.DownloadStation.Info',
            'method': 'getinfo',
            'session': 'DownloadStation',
        }

        api_info = self._get_api_info(params['api'])
        params['version'] = api_info.get('maxVersion')

        self.response = self.session.get(self.urls['info'], params=params, verify=False, timeout=120)
        if not self.response or not self.response.content:
            self.session.cookies.clear()
            self.auth = False
            return False

        destination = ''
        if self._check_response():
            jdata = self.response.json()
            version_string = jdata.get('data', {}).get('version_string')
            if not version_string:
                sickrage.app.log.warning('Could not get the version string from DSM: {}'.format(jdata))
                return False

            #  This is DSM6, lets make sure the location is relative
            if torrent_path and os.path.isabs(torrent_path):
                torrent_path = re.sub(r'^/volume\d/', '', torrent_path).lstrip('/')
            else:
                #  Since they didn't specify the location in the settings,
                #  lets make sure the default is relative,
                #  or forcefully set the location setting
                params.update({
                    'method': 'getconfig'
                })

                self.response = self.session.get(self.urls['info'], params=params, verify=False, timeout=120)
                if not self.response or not self.response.content:
                    self.session.cookies.clear()
                    self.auth = False
                    return False

                if self._check_response():
                    jdata = self.response.json()
                    destination = jdata.get('data', {}).get('default_destination')
                    if not destination:
                        sickrage.app.log.info('Default destination could not be determined for DSM6: {}'.format(jdata))
                        return False
                    elif os.path.isabs(destination):
                        torrent_path = re.sub(r'^/volume\d/', '', destination).lstrip('/')

        if destination or torrent_path:
            sickrage.app.log.info('Destination is now {}'.format(torrent_path or destination))

        self.checked_destination = True
        self.destination = torrent_path
        return True

    def _send_dsm_request(self, method, data, **kwargs):
        if not self._check_destination():
            return False

        data['destination'] = self.destination

        self._request(method=method, data=data, **kwargs)
        return self._check_response()
