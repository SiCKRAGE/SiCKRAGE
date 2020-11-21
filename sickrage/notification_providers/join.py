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



import urllib

from six.moves import urllib

import sickrage
from sickrage.notification_providers import NotificationProvider


class JoinNotification(NotificationProvider):
    def __init__(self):
        super(JoinNotification, self).__init__()
        self.name = 'join'

    def test_notify(self, id=None, api_key=None):
        """
        Send a test notification
        :param id: The Device ID
        :param api_key: The User's API Key
        :returns: the notification
        """
        return self._notify_join('Test', 'This is a test notification from SiCKRAGE', id, api_key, force=True)

    def _send_join_msg(self, title, msg, id=None, api_key=None):
        """
        Sends a Join notification
        :param title: The title of the notification to send
        :param msg: The message string to send
        :param id: The Device ID
        :param api_key: The User's API Key
        :returns: True if the message succeeded, False otherwise
        """
        id = sickrage.app.config.join_app.user_id if id is None else id
        api_key = sickrage.app.config.join_app.apikey if api_key is None else api_key

        sickrage.app.log.debug('Join in use with device ID: {}'.format(id))

        message = '{} : {}'.format(title.encode(), msg.encode())

        params = {
            "apikey": api_key,
            "deviceId": id,
            "title": title,
            "text": message,
            "icon": "'https://www.sickrage.ca/favicon.ico'"
        }

        payload = urllib.parse.urlencode(params)
        join_api = 'https://joinjoaomgcd.appspot.com/_ah/api/messaging/v1/sendPush?' + payload
        sickrage.app.log.debug('Join url in use : {}'.format(join_api))
        success = False
        try:
            urllib.request.urlopen(join_api)
            message = 'Join message sent successfully.'
            sickrage.app.log.debug('Join message returned : {}'.format(message))
            success = True
        except Exception as e:
            message = 'Error while sending Join message: {} '.format(e)
        finally:
            sickrage.app.log.info(message)
            return success, message

    def notify_snatch(self, ep_name, title=NotificationProvider):
        """
        Sends a Join notification when an episode is snatched
        :param ep_name: The name of the episode snatched
        :param title: The title of the notification to send
        """
        if not title:
            title = self.notifyStrings[self.NOTIFY_SNATCH]

        if sickrage.app.config.join_app.notify_on_snatch:
            self._notify_join(title, ep_name)

    def notify_download(self, ep_name, title=None):
        """
        Sends a Join notification when an episode is downloaded
        :param ep_name: The name of the episode downloaded
        :param title: The title of the notification to send
        """
        if not title:
            title = self.notifyStrings[self.NOTIFY_DOWNLOAD]

        if sickrage.app.config.join_app.notify_on_download:
            self._notify_join(title, ep_name)

    def notify_subtitle_download(self, ep_name, lang, title=None):
        """
        Sends a Join notification when subtitles for an episode are downloaded
        :param ep_name: The name of the episode subtitles were downloaded for
        :param lang: The language of the downloaded subtitles
        :param title: The title of the notification to send
        """
        if not title:
            title = self.notifyStrings[self.NOTIFY_SUBTITLE_DOWNLOAD]

        if sickrage.app.config.join_app.notify_on_subtitle_download:
            self._notify_join(title, '{}: {}'.format(ep_name, lang))

    def notify_version_update(self, new_version='??'):
        """
        Sends a Join notification for git updates
        :param new_version: The new version available from git
        """
        if sickrage.app.config.join_app.enable:
            update_text = self.notifyStrings[self.NOTIFY_GIT_UPDATE_TEXT]
            title = self.notifyStrings[self.NOTIFY_GIT_UPDATE]
            self._notify_join(title, update_text + new_version)

    def notify_login(self, ipaddress=''):
        """
        Sends a Join notification on login
        :param ipaddress: The IP address the login is originating from
        """
        if sickrage.app.config.join_app.enable:
            update_text = self.notifyStrings[self.NOTIFY_LOGIN_TEXT]
            title = self.notifyStrings[self.NOTIFY_LOGIN]
            self._notify_join(title, update_text.format(ipaddress))

    def _notify_join(self, title, message, id=None, api_key=None, force=False):
        """
        Sends a Join notification
        :param title: The title of the notification to send
        :param message: The message string to send
        :param id: The Device ID
        :param api_key: The User's API Key
        :param force: Enforce sending, for instance for testing
        :returns: the message to send
        """

        if not (force or sickrage.app.config.join_app.enable):
            sickrage.app.log.debug('Notification for Join not enabled, skipping this notification')
            return False, 'Disabled'

        sickrage.app.log.debug('Sending a Join message for {}'.format(message))

        return self._send_join_msg(title, message, id, api_key)
