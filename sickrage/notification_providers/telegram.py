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

import sickrage
from sickrage.core.websession import WebSession
from sickrage.notification_providers import NotificationProvider


class TelegramNotification(NotificationProvider):
    """
    A notifier for Telegram
    """

    def __init__(self):
        super(TelegramNotification, self).__init__()
        self.name = 'telegram'

    def test_notify(self, id=None, api_key=None):
        """
        Send a test notification
        :param id: The Telegram user/group id to send the message to
        :param api_key: Your Telegram bot API token
        :returns: the notification
        """
        return self._notify_telegram('Test', 'This is a test notification from SickRage', id, api_key, force=True)

    def _send_telegram_msg(self, title, msg, id=None, api_key=None):
        """
        Sends a Telegram notification

        :param title: The title of the notification to send
        :param msg: The message string to send
        :param id: The Telegram user/group id to send the message to
        :param api_key: Your Telegram bot API token

        :returns: True if the message succeeded, False otherwise
        """
        id = sickrage.app.config.telegram.user_id or id
        api_key = sickrage.app.config.telegram.apikey or api_key

        payload = {'chat_id': id, 'text': '{} : {}'.format(title, msg)}

        telegram_api = 'https://api.telegram.org/bot{}/{}'

        try:
            resp = WebSession().post(telegram_api.format(api_key, 'sendMessage'), json=payload).json()
            success = resp['ok']
            message = 'Telegram message sent successfully.' if success else '{} {}'.format(resp['error_code'], resp['description'])
        except Exception as e:
            success = False
            message = 'Error while sending Telegram message: {} '.format(e)

        sickrage.app.log.info(message)
        return success, message

    def notify_snatch(self, ep_name, title=None):
        """
        Sends a Telegram notification when an episode is snatched

        :param ep_name: The name of the episode snatched
        :param title: The title of the notification to send
        """
        if not title:
            title = self.notifyStrings[self.NOTIFY_SNATCH]

        if sickrage.app.config.telegram.notify_on_snatch:
            self._notify_telegram(title, ep_name)

    def notify_download(self, ep_name, title=None):
        """
        Sends a Telegram notification when an episode is downloaded

        :param ep_name: The name of the episode downloaded
        :param title: The title of the notification to send
        """
        if not title:
            title = self.notifyStrings[self.NOTIFY_DOWNLOAD]

        if sickrage.app.config.telegram.notify_on_download:
            self._notify_telegram(title, ep_name)

    def notify_subtitle_download(self, ep_name, lang, title=None):
        """
        Sends a Telegram notification when subtitles for an episode are downloaded

        :param ep_name: The name of the episode subtitles were downloaded for
        :param lang: The language of the downloaded subtitles
        :param title: The title of the notification to send
        """
        if not title:
            title = self.notifyStrings[self.NOTIFY_SUBTITLE_DOWNLOAD]

        if sickrage.app.config.telegram.notify_on_subtitle_download:
            self._notify_telegram(title, '{}: {}'.format(ep_name, lang))

    def notify_version_update(self, new_version='??'):
        """
        Sends a Telegram notification for git updates

        :param new_version: The new version available from git
        """
        if sickrage.app.config.telegram.enable:
            update_text = self.notifyStrings[self.NOTIFY_GIT_UPDATE_TEXT]
            title = self.notifyStrings[self.NOTIFY_GIT_UPDATE]
            self._notify_telegram(title, update_text + new_version)

    def notify_login(self, ipaddress=''):
        """
        Sends a Telegram notification on login

        :param ipaddress: The ip address the login is originating from
        """
        if sickrage.app.config.telegram.enable:
            update_text = self.notifyStrings[self.NOTIFY_LOGIN_TEXT]
            title = self.notifyStrings[self.NOTIFY_LOGIN]
            self._notify_telegram(title, update_text.format(ipaddress))

    def _notify_telegram(self, title, message, id=None, api_key=None, force=False):
        """
        Sends a Telegram notification

        :param title: The title of the notification to send
        :param message: The message string to send
        :param id: The Telegram user/group id to send the message to
        :param api_key: Your Telegram bot API token
        :param force: Enforce sending, for instance for testing

        :returns: the message to send
        """

        if not (force or sickrage.app.config.telegram.enable):
            sickrage.app.log.debug('Notification for Telegram not enabled, skipping this notification')
            return False, 'Disabled'

        sickrage.app.log.debug('Sending a Telegram message for {}'.format(message))

        return self._send_telegram_msg(title, message, id, api_key)
