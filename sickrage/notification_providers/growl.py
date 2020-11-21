# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.



import socket

import gntp
import gntp.core

import sickrage
from sickrage.notification_providers import NotificationProvider


class GrowlNotification(NotificationProvider):
    sr_logo_url = 'https://www.sickrage.ca/favicon.ico'

    def __init__(self):
        super(GrowlNotification, self).__init__()
        self.name = 'growl'

    def test_notify(self, host, password):
        self._sendRegistration(host, password, 'Test')
        return self._sendGrowl("Test Growl", "Testing Growl settings from SiCKRAGE", "Test", host, password,
                               force=True)

    def notify_snatch(self, ep_name):
        if sickrage.app.config.growl.notify_on_snatch:
            self._sendGrowl(self.notifyStrings[self.NOTIFY_SNATCH], ep_name)

    def notify_download(self, ep_name):
        if sickrage.app.config.growl.notify_on_download:
            self._sendGrowl(self.notifyStrings[self.NOTIFY_DOWNLOAD], ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if sickrage.app.config.growl.notify_on_subtitle_download:
            self._sendGrowl(self.notifyStrings[self.NOTIFY_SUBTITLE_DOWNLOAD], ep_name + ": " + lang)

    def notify_version_update(self, new_version="??"):
        if sickrage.app.config.growl.enable:
            update_text = self.notifyStrings[self.NOTIFY_GIT_UPDATE_TEXT]
            title = self.notifyStrings[self.NOTIFY_GIT_UPDATE]
            self._sendGrowl(title, update_text + new_version)

    def _send_growl(self, options, message=None):

        # Send Notification
        notice = gntp.core.GNTPNotice()

        # Required
        notice.add_header('Application-Name', options['app'])
        notice.add_header('Notification-Name', options['name'])
        notice.add_header('Notification-Title', options['title'])

        if options['password']:
            notice.set_password(options['password'])

        # Optional
        if options['sticky']:
            notice.add_header('Notification-Sticky', options['sticky'])
        if options['priority']:
            notice.add_header('Notification-Priority', options['priority'])
        if options['icon']:
            notice.add_header('Notification-Icon', self.sr_logo_url)

        if message:
            notice.add_header('Notification-Text', message)

        response = self._send(options['host'], options['port'], notice.encode(), options['debug'])
        if isinstance(response, gntp.core.GNTPOK): return True
        return False

    def _send(self, host, port, data, debug=False):
        if debug: print('<Sending>\n', data, '\n</Sending>')

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.send(data)
        response = gntp.core.parse_gntp(s.recv(1024))
        s.close()

        if debug: print('<Recieved>\n', response, '\n</Recieved>')

        return response

    def _sendGrowl(self, title="SiCKRAGE Notification", message=None, name=None, host=None, password=None,
                   force=False):
        if not sickrage.app.config.growl.enable and not force:
            return False

        if name is None:
            name = title

        if host is None:
            hostParts = sickrage.app.config.growl.host.split(':')
        else:
            hostParts = host.split(':')

        if len(hostParts) != 2 or hostParts[1] == '':
            port = 23053
        else:
            port = int(hostParts[1])

        growlHosts = [(hostParts[0], port)]

        opts = {'name': name, 'title': title, 'app': 'SiCKRAGE', 'sticky': None, 'priority': None, 'debug': False}

        if password is None:
            opts['password'] = sickrage.app.config.growl.password
        else:
            opts['password'] = password

        opts['icon'] = True

        for pc in growlHosts:
            opts['host'] = pc[0]
            opts['port'] = pc[1]
            sickrage.app.log.debug(
                "GROWL: Sending message '" + message + "' to " + opts['host'] + ":" + str(opts['port']))
            try:
                if self._send_growl(opts, message):
                    return True
                else:
                    if self._sendRegistration(host, password, 'SiCKRAGE'):
                        return self._send_growl(opts, message)
                    else:
                        return False
            except Exception as e:
                sickrage.app.log.warning(
                    "GROWL: Unable to send growl to " + opts['host'] + ":" + str(opts['port']) + " - {}".format(
                        e))
                return False

    def _sendRegistration(self, host=None, password=None, name='SiCKRAGE Notification'):
        opts = {}

        if host is None:
            hostParts = sickrage.app.config.growl.host.split(':')
        else:
            hostParts = host.split(':')

        if len(hostParts) != 2 or hostParts[1] == '':
            port = 23053
        else:
            port = int(hostParts[1])

        opts['host'] = hostParts[0]
        opts['port'] = port

        if password is None:
            opts['password'] = sickrage.app.config.growl.password
        else:
            opts['password'] = password

        opts['app'] = 'SiCKRAGE'
        opts['debug'] = False

        # Send Registration
        register = gntp.core.GNTPRegister()
        register.add_header('Application-Name', opts['app'])
        register.add_header('Application-Icon', self.sr_logo_url)

        register.add_notification('Test', True)
        register.add_notification(self.notifyStrings[self.NOTIFY_SNATCH], True)
        register.add_notification(self.notifyStrings[self.NOTIFY_DOWNLOAD], True)
        register.add_notification(self.notifyStrings[self.NOTIFY_GIT_UPDATE], True)

        if opts['password']:
            register.set_password(opts['password'])

        try:
            return self._send(opts['host'], opts['port'], register.encode(), opts['debug'])
        except Exception as e:
            sickrage.app.log.warning(
                "GROWL: Unable to send growl to " + opts['host'] + ":" + str(opts['port']) + " - {}".format(e))
            return False
