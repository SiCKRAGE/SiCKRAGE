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

import base64
import re
import urllib
import urllib2
from xml.etree import ElementTree

import sickrage
from sickrage.core.common import NOTIFY_SNATCH, NOTIFY_DOWNLOAD, NOTIFY_SUBTITLE_DOWNLOAD, NOTIFY_GIT_UPDATE_TEXT, \
    NOTIFY_GIT_UPDATE
from sickrage.core.common import notifyStrings
from sickrage.notifiers import srNotifiers


class PLEXNotifier(srNotifiers):
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
            username = sickrage.srCore.srConfig.PLEX_CLIENT_USERNAME
        if not password:
            password = sickrage.srCore.srConfig.PLEX_CLIENT_PASSWORD

        if not host:
            sickrage.srCore.srLogger.warning('PLEX: No host specified, check your settings')
            return False

        for key in command:
            if type(command[key]) == unicode:
                command[key] = command[key].encode('utf-8')

        enc_command = urllib.urlencode(command)
        sickrage.srCore.srLogger.debug('PLEX: Encoded API command: ' + enc_command)

        url = 'http://%s/xbmcCmds/xbmcHttp/?%s' % (host, enc_command)
        try:
            req = urllib2.Request(url)
            # if we have a password, use authentication
            if password:
                base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
                authheader = 'Basic %s' % base64string
                req.add_header('Authorization', authheader)
                sickrage.srCore.srLogger.debug('PLEX: Contacting (with auth header) via url: ' + url)
            else:
                sickrage.srCore.srLogger.debug('PLEX: Contacting via url: ' + url)

            response = urllib2.urlopen(req)

            result = response.read().decode(sickrage.SYS_ENCODING)
            response.close()

            sickrage.srCore.srLogger.debug('PLEX: HTTP response: ' + result.replace('\n', ''))
            # could return result response = re.compile('<html><li>(.+\w)</html>').findall(result)
            return 'OK'

        except (urllib2.URLError, IOError) as e:
            sickrage.srCore.srLogger.warning('PLEX: Warning: Couldn\'t contact Plex at ' + url + ' ' + e)
            return False

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
        if not sickrage.srCore.srConfig.USE_PLEX_CLIENT and not force:
            return False

        # fill in omitted parameters
        if not host:
            host = sickrage.srCore.srConfig.PLEX_HOST
        if not username:
            username = sickrage.srCore.srConfig.PLEX_CLIENT_USERNAME
        if not password:
            password = sickrage.srCore.srConfig.PLEX_CLIENT_PASSWORD

        result = ''
        for curHost in [x.strip() for x in host.split(',')]:
            sickrage.srCore.srLogger.debug('PLEX: Sending notification to \'%s\' - %s' % (curHost, message))

            command = {'command': 'ExecBuiltIn',
                       'parameter': 'Notification(%s,%s)' % (title.encode('utf-8'), message.encode('utf-8'))}
            notify_result = self._send_to_plex(command, curHost, username, password)
            if notify_result:
                result += '%s:%s' % (curHost, str(notify_result))

        return result

    ##############################################################################
    # Public functions
    ##############################################################################

    def _notify_snatch(self, ep_name):
        if sickrage.srCore.srConfig.PLEX_NOTIFY_ONSNATCH:
            self._notify_pmc(ep_name, notifyStrings[NOTIFY_SNATCH])

    def _notify_download(self, ep_name):
        if sickrage.srCore.srConfig.PLEX_NOTIFY_ONDOWNLOAD:
            self._notify_pmc(ep_name, notifyStrings[NOTIFY_DOWNLOAD])

    def _notify_subtitle_download(self, ep_name, lang):
        if sickrage.srCore.srConfig.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notify_pmc(ep_name + ': ' + lang, notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD])

    def _notify_version_update(self, new_version='??'):
        if sickrage.srCore.srConfig.USE_PLEX:
            update_text = notifyStrings[NOTIFY_GIT_UPDATE_TEXT]
            title = notifyStrings[NOTIFY_GIT_UPDATE]
            if update_text and title and new_version:
                self._notify_pmc(update_text + new_version, title)

    def test_notify_pmc(self, host, username, password):
        return self._notify_pmc('This is a test notification from SiCKRAGE', 'Test Notification', host, username,
                                password, force=True)

    def test_notify_pms(self, host, username, password, plex_server_token):
        return self.update_library(host=host, username=username, password=password, plex_server_token=plex_server_token,
                                   force=False)

    def update_library(self, ep_obj=None, host=None, username=None, password=None, plex_server_token=None, force=True):
        """Handles updating the Plex Media Server host via HTTP API

        Plex Media Server currently only supports updating the whole video library and not a specific path.

        Returns:
            Returns None for no issue, else a string of host with connection issues

        """

        if sickrage.srCore.srConfig.USE_PLEX and sickrage.srCore.srConfig.PLEX_UPDATE_LIBRARY:

            if not sickrage.srCore.srConfig.PLEX_SERVER_HOST:
                sickrage.srCore.srLogger.debug('PLEX: No Plex Media Server host specified, check your settings')
                return False

            if not host:
                host = sickrage.srCore.srConfig.PLEX_SERVER_HOST
            if not username:
                username = sickrage.srCore.srConfig.PLEX_USERNAME
            if not password:
                password = sickrage.srCore.srConfig.PLEX_PASSWORD

            if not plex_server_token:
                plex_server_token = sickrage.srCore.srConfig.PLEX_SERVER_TOKEN

            # if username and password were provided, fetch the auth token from plex.tv
            token_arg = ''
            if plex_server_token:
                token_arg = '?X-Plex-Token=' + plex_server_token
            elif username and password:
                sickrage.srCore.srLogger.debug('PLEX: fetching plex.tv credentials for user: ' + username)
                req = urllib2.Request('https://plex.tv/users/sign_in.xml', data='')
                authheader = 'Basic %s' % base64.encodestring('%s:%s' % (username, password))[:-1]
                req.add_header('Authorization', authheader)
                req.add_header('X-Plex-Device-Name', 'SiCKRAGE')
                req.add_header('X-Plex-Product', 'SiCKRAGE Notifier')
                req.add_header('X-Plex-Client-Identifier', sickrage.srCore.srConfig.USER_AGENT)
                req.add_header('X-Plex-Version', '1.0')

                try:
                    response = urllib2.urlopen(req)
                    auth_tree = ElementTree.parse(response)
                    token = auth_tree.findall('.//authentication-token')[0].text
                    token_arg = '?X-Plex-Token=' + token

                except urllib2.URLError as e:
                    sickrage.srCore.srLogger.debug(
                            'PLEX: Error fetching credentials from from plex.tv for user %s: %s' % (username, e))

                except (ValueError, IndexError) as e:
                    sickrage.srCore.srLogger.debug('PLEX: Error parsing plex.tv response: ' + e)

            file_location = '' if None is ep_obj else ep_obj.location
            host_list = [x.strip() for x in host.split(',')]
            hosts_all = {}
            hosts_match = {}
            hosts_failed = []
            for cur_host in host_list:

                url = 'http://%s/library/sections%s' % (cur_host, token_arg)
                try:
                    xml_tree = ElementTree.parse(urllib.urlopen(url))
                    media_container = xml_tree.getroot()
                except IOError as e:
                    sickrage.srCore.srLogger.warning('PLEX: Error while trying to contact Plex Media Server: {}'.format(e.message))
                    hosts_failed.append(cur_host)
                    continue
                except Exception as e:
                    if 'invalid token' in str(e):
                        sickrage.srCore.srLogger.error('PLEX: Please set TOKEN in Plex settings: ')
                    else:
                        sickrage.srCore.srLogger.error('PLEX: Error while trying to contact Plex Media Server: {}'.format(e.message))
                    continue

                sections = media_container.findall('.//Directory')
                if not sections:
                    sickrage.srCore.srLogger.debug('PLEX: Plex Media Server not running on: ' + cur_host)
                    hosts_failed.append(cur_host)
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

                url = 'http://%s/library/sections/%s/refresh%s' % (cur_host, section_key, token_arg)
                try:
                    force and urllib.urlopen(url)
                    host_list.append(cur_host)
                except Exception as e:
                    sickrage.srCore.srLogger.warning('PLEX: Error updating library section for Plex Media Server: {}'.format(e.message))
                    hosts_failed.append(cur_host)

            if hosts_match:
                sickrage.srCore.srLogger.debug('PLEX: Updating hosts where TV section paths match the downloaded show: ' + ', '.join(
                    set(host_list)))
            else:
                sickrage.srCore.srLogger.debug('PLEX: Updating all hosts with TV sections: ' + ', '.join(set(host_list)))

            return (', '.join(set(hosts_failed)), None)[not len(hosts_failed)]
