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


import base64
import re
from urllib.parse import urlencode
from xml.etree import ElementTree

import sickrage
from sickrage.core.websession import WebSession
from sickrage.notification_providers import NotificationProvider


class PLEXNotification(NotificationProvider):
    def __init__(self):
        super(PLEXNotification, self).__init__()
        self.name = 'plex'

        self.headers = {
            'X-Plex-Device-Name': 'SiCKRAGE',
            'X-Plex-Product': 'SiCKRAGE Notifier',
            'X-Plex-Client-Identifier': sickrage.app.user_agent,
            'X-Plex-Version': sickrage.version()
        }

    def _send_to_plex(self, command, host, username=None, password=None):
        """Handles communication to Plex hosts via HTTP API

        Args:
            command: Dictionary of field/data pairs, encoded via urllib and passed to the legacy xbmcCmds HTTP API
            host: Plex host:port
            username: Plex API username
            password: Plex API password

        Returns:
            Returns 'OK' for successful commands or False if there was an error

        """

        # fill in omitted parameters
        if not username:
            username = sickrage.app.config.plex.client_username
        if not password:
            password = sickrage.app.config.plex.client_password

        if not host:
            sickrage.app.log.warning('PLEX: No host specified, check your settings')
            return False

        enc_command = urlencode(command)
        sickrage.app.log.debug('PLEX: Encoded API command: ' + enc_command)

        url = 'http://%s/xbmcCmds/xbmcHttp/?%s' % (host, enc_command)

        headers = {}

        # if we have a password, use authentication
        if password:
            base64string = base64.b64encode(bytes('{}:{}'.format(username, password).replace('\n', ''), 'utf-8'))
            authheader = "Basic {}".format(base64string.decode('ascii'))
            headers['Authorization'] = authheader
            sickrage.app.log.debug('PLEX: Contacting (with auth header) via url: ' + url)
        else:
            sickrage.app.log.debug('PLEX: Contacting via url: ' + url)

        resp = WebSession().get(url, headers=headers)
        if not resp or not resp.text:
            sickrage.app.log.warning('PLEX: Warning: Couldn\'t contact Plex at {}: {}'.format(url, e))
            return False

        sickrage.app.log.debug('PLEX: HTTP response: ' + resp.text.replace('\n', ''))

        return 'OK'

    def _notify_pmc(self, message, title='SiCKRAGE', host=None, username=None, password=None, force=False):
        """Internal wrapper for the notify_snatch and notify_download functions

        Args:
            message: Message body of the notice to send
            title: Title of the notice to send
            host: Plex Media Client(s) host:port
            username: Plex username
            password: Plex password
            force: Used for the Test method to override config safety checks

        Returns:
            Returns a list results in the format of host:ip:result
            The result will either be 'OK' or False, this is used to be parsed by the calling function.

        """

        # suppress notifications if the notifier is disabled but the notify options are checked
        if not sickrage.app.config.plex.enable_client and not force:
            return False

        # fill in omitted parameters
        if not host:
            host = sickrage.app.config.plex.host
        if not username:
            username = sickrage.app.config.plex.client_username
        if not password:
            password = sickrage.app.config.plex.client_password

        result = ''
        for curHost in [x.strip() for x in host.split(',')]:
            sickrage.app.log.debug('PLEX: Sending notification to \'%s\' - %s' % (curHost, message))

            command = {'command': 'ExecBuiltIn',
                       'parameter': 'Notification(%s,%s)' % (title, message)}
            notify_result = self._send_to_plex(command, curHost, username, password)
            if notify_result:
                result += '%s:%s' % (curHost, str(notify_result))

        return result

    ##############################################################################
    # Public functions
    ##############################################################################

    def notify_snatch(self, ep_name):
        if sickrage.app.config.plex.notify_on_snatch:
            self._notify_pmc(ep_name, self.notifyStrings[self.NOTIFY_SNATCH])

    def notify_download(self, ep_name):
        if sickrage.app.config.plex.notify_on_download:
            self._notify_pmc(ep_name, self.notifyStrings[self.NOTIFY_DOWNLOAD])

    def notify_subtitle_download(self, ep_name, lang):
        if sickrage.app.config.plex.notify_on_subtitle_download:
            self._notify_pmc(ep_name + ': ' + lang, self.notifyStrings[self.NOTIFY_SUBTITLE_DOWNLOAD])

    def notify_version_update(self, new_version='??'):
        if sickrage.app.config.plex.enable:
            update_text = self.notifyStrings[self.NOTIFY_GIT_UPDATE_TEXT]
            title = self.notifyStrings[self.NOTIFY_GIT_UPDATE]
            if update_text and title and new_version:
                self._notify_pmc(update_text + new_version, title)

    def test_notify_pmc(self, host, username, password):
        return self._notify_pmc('This is a test notification from SiCKRAGE', 'Test Notification', host, username, password, force=True)

    def test_notify_pms(self, host, username, password, plex_server_token):
        return self.update_library(host=host, username=username, password=password, plex_server_token=plex_server_token, force=False)

    def update_library(self, ep_obj=None, host=None, username=None, password=None, plex_server_token=None, force=True):
        """Handles updating the Plex Media Server host via HTTP API

        Plex Media Server currently only supports updating the whole video library and not a specific path.

        Returns:
            Returns None for no issue, else a string of host with connection issues

        """

        if sickrage.app.config.plex.enable and sickrage.app.config.plex.update_library:
            if not sickrage.app.config.plex.server_host:
                sickrage.app.log.debug('PLEX: No Plex Media Server host specified, check your settings')
                return False

            if not host:
                host = sickrage.app.config.plex.server_host

            if not self.get_token(username, password, plex_server_token):
                sickrage.app.log.warning('PLEX: Error getting auth token for Plex Media Server, check your settings')
                return 'Error getting auth token for Plex Media Server, check your settings'

            file_location = '' if None is ep_obj else ep_obj.location
            host_list = [x.strip() for x in host.split(',')]
            hosts_all = {}
            hosts_match = {}
            hosts_failed = set()

            for cur_host in host_list:
                try:
                    url = 'http://%s/library/sections' % cur_host
                    resp = WebSession().get(url, headers=self.headers)
                    if not resp or not resp.text:
                        sickrage.app.log.warning('PLEX: Unable to get library data from Plex Media Server')
                        continue
                    media_container = ElementTree.fromstring(resp.text)
                except IOError as e:
                    sickrage.app.log.warning('PLEX: Error while trying to contact Plex Media Server: {}'.format(e))
                    hosts_failed.add(cur_host)
                    continue
                except Exception as e:
                    if 'invalid token' in str(e):
                        sickrage.app.log.error('PLEX: Please set TOKEN in Plex settings')
                    else:
                        sickrage.app.log.error('PLEX: Error while trying to contact Plex Media Server: {}'.format(e))
                    continue

                sections = media_container.findall('.//Directory')
                if not sections:
                    sickrage.app.log.debug('PLEX: Plex Media Server not running on: ' + cur_host)
                    hosts_failed.add(cur_host)
                    continue

                for section in sections:
                    if 'show' == section.attrib['type']:

                        keyed_host = [(str(section.attrib['key']), cur_host)]
                        hosts_all.update(keyed_host)
                        if not file_location:
                            continue

                        for section_location in section.findall('.//Location'):
                            section_path = re.sub(r'[/\\]+', '/', section_location.attrib['path'].lower())
                            section_path = re.sub(r'^(.{,2})[/\\]', '', section_path)
                            location_path = re.sub(r'[/\\]+', '/', file_location.lower())
                            location_path = re.sub(r'^(.{,2})[/\\]', '', location_path)

                            if section_path in location_path:
                                hosts_match.update(keyed_host)

            hosts_try = (hosts_all.copy(), hosts_match.copy())[bool(hosts_match)]
            host_list = []
            for section_key, cur_host in hosts_try.items():
                url = 'http://%s/library/sections/%s/refresh' % (cur_host, section_key)
                resp = WebSession().get(url, headers=self.headers)
                if not resp or not resp.ok:
                    sickrage.app.log.warning('PLEX: Error updating library section for Plex Media Server')
                    hosts_failed.add(cur_host)
                    continue

                host_list.append(cur_host)

            if hosts_match:
                sickrage.app.log.debug('PLEX: Updating hosts where TV section paths match the downloaded show: ' + ', '.join(set(host_list)))
            else:
                sickrage.app.log.debug('PLEX: Updating TV sections on these hosts: {}'.format(', '.join(set(host_list))))

            return (', '.join(set(hosts_failed)), None)[not len(hosts_failed)]

    def get_token(self, username=None, password=None, plex_server_token=None):
        if plex_server_token:
            self.headers['X-Plex-Token'] = plex_server_token

        if 'X-Plex-Token' in self.headers:
            return True

        if not (username and password):
            return True

        sickrage.app.log.debug('PLEX: fetching plex.tv credentials for user: ' + username)

        params = {
            'user[login]': username,
            'user[password]': password
        }

        resp = WebSession().post('https://plex.tv/users/sign_in.json', data=params, headers=self.headers)

        try:
            data = resp.json()
        except ValueError:
            sickrage.app.log.debug("PLEX: No data returned from plex.tv when attempting to fetch credentials")
            self.headers.pop('X-Plex-Token', '')
            return False

        if data and 'error' in data:
            sickrage.app.log.debug('PLEX: Error fetching credentials from from plex.tv for user %s: %s' % (username, data['error']))
            self.headers.pop('X-Plex-Token', '')
            return False
        elif data and 'user' in data:
            self.headers['X-Plex-Token'] = data['user']['authentication_token']

        return 'X-Plex-Token' in self.headers
