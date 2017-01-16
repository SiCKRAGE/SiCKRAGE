

# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
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

import json
import time

import requests

import sickrage



class TraktAPI():
    def __init__(self, ssl_verify=True, timeout=30):
        self.timeout = timeout if timeout else None
        self.auth_url = sickrage.srCore.srConfig.TRAKT_OAUTH_URL
        self.api_url = sickrage.srCore.srConfig.TRAKT_API_URL
        self.headers = {
            'Content-Type': 'application/json',
            'trakt-api-version': '2',
            'trakt-api-key': sickrage.srCore.srConfig.TRAKT_API_KEY
        }

    def traktToken(self, trakt_pin=None, refresh=False, count=0):

        if count > 3:
            sickrage.srCore.srConfig.TRAKT_ACCESS_TOKEN = ''
            return False
        elif count > 0:
            time.sleep(2)

        data = {
            'client_id': sickrage.srCore.srConfig.TRAKT_API_KEY,
            'client_secret': sickrage.srCore.srConfig.TRAKT_API_SECRET,
            'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob'
        }

        if refresh:
            data['grant_type'] = 'refresh_token'
            data['refresh_token'] = sickrage.srCore.srConfig.TRAKT_REFRESH_TOKEN
        else:
            data['grant_type'] = 'authorization_code'
            if not None == trakt_pin:
                data['code'] = trakt_pin

        headers = {
            'Content-Type': 'application/json'
        }

        resp = self.traktRequest('oauth/token', data=data, headers=headers, url=self.auth_url, method='POST',
                                 count=count)

        if 'access_token' in resp:
            sickrage.srCore.srConfig.TRAKT_ACCESS_TOKEN = resp['access_token']
            if 'refresh_token' in resp:
                sickrage.srCore.srConfig.TRAKT_REFRESH_TOKEN = resp['refresh_token']
            return True
        return False

    def validateAccount(self):

        resp = self.traktRequest('users/settings')

        if 'account' in resp:
            return True
        return False

    def traktRequest(self, path, data=None, headers=None, url=None, method='GET', count=0):
        if None == url:
            url = self.api_url

        count += 1

        if None == headers:
            headers = self.headers

        if None == sickrage.srCore.srConfig.TRAKT_ACCESS_TOKEN:
            sickrage.srCore.srLogger.warning('You must get a Trakt TOKEN. Check your Trakt settings')
            return {}

        headers['Authorization'] = 'Bearer ' + sickrage.srCore.srConfig.TRAKT_ACCESS_TOKEN

        try:
            resp = sickrage.srCore.srWebSession.request(method, url + path,
                                        headers=headers,
                                        timeout=self.timeout,
                                        data=json.dumps(data) if data else [])

            # check for http errors and raise if any are present
            resp.raise_for_status()

            # convert response to json
            resp = resp.json()
        except requests.RequestException as e:
            code = getattr(e.response, 'status_code', None)
            if not code:
                if 'timed out' in e:
                    sickrage.srCore.srLogger.warning(
                        'Timeout connecting to Trakt. Try to increase timeout value in Trakt settings')
                # This is pretty much a fatal error if there is no status_code
                # It means there basically was no response at all                    
                else:
                    sickrage.srCore.srLogger.debug('Could not connect to Trakt. Error: {0}'.format(e.message))
            elif code == 502:
                # Retry the request, cloudflare had a proxying issue
                sickrage.srCore.srLogger.debug('Retrying trakt api request: %s' % path)
                return self.traktRequest(path, data, headers, url, method)
            elif code == 401:
                if self.traktToken(refresh=True, count=count):
                    return self.traktRequest(path, data, headers, url, method)
                else:
                    sickrage.srCore.srLogger.warning('Unauthorized. Please check your Trakt settings')
            elif code in (500, 501, 503, 504, 520, 521, 522):
                # http://docs.trakt.apiary.io/#introduction/status-codes
                sickrage.srCore.srLogger.debug('Trakt may have some issues and it\'s unavailable. Try again later please')
            elif code == 404:
                sickrage.srCore.srLogger.debug('Trakt error (404) the resource does not exist: %s' % url + path)
            else:
                sickrage.srCore.srLogger.error('Could not connect to Trakt. Code error: {0}'.format(code))
            return {}

        # check and confirm trakt call did not fail
        if isinstance(resp, dict) and resp.get('status', False) == 'failure':
            if 'message' in resp:
                raise traktException(resp['message'])
            if 'error' in resp:
                raise traktException(resp['error'])
            else:
                raise traktException('Unknown Error')

        return resp


class traktException(Exception):
    pass


class traktAuthException(traktException):
    pass


class traktServerBusy(traktException):
    pass
