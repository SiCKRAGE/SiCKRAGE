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



import re

from twilio.base.exceptions import TwilioRestException
from twilio.rest import TwilioRestClient

import sickrage
from sickrage.notification_providers import NotificationProvider


class AlexaNotification(NotificationProvider):
    def __init__(self):
        super(AlexaNotification, self).__init__()
        self.name = 'alexa'

    def notify_snatch(self, ep_name):
        if sickrage.app.config.alexa.notify_on_snatch:
            self._notify_alexa(self.notifyStrings[self.NOTIFY_SNATCH] + ': ' + ep_name)

    def notify_download(self, ep_name):
        if sickrage.app.config.alexa.notify_on_download:
            self._notify_alexa(self.notifyStrings[self.NOTIFY_DOWNLOAD] + ': ' + ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if sickrage.app.config.alexa.notify_on_subtitle_download:
            self._notify_alexa(self.notifyStrings[self.NOTIFY_SUBTITLE_DOWNLOAD] + ' ' + ep_name + ': ' + lang)

    def notify_version_update(self, new_version):
        if sickrage.app.config.alexa.enable:
            update_text = self.notifyStrings[self.NOTIFY_GIT_UPDATE_TEXT]
            self._notify_alexa(update_text + new_version)

    def notify_login(self, ipaddress=""):
        if sickrage.app.config.alexa.enable:
            update_text = self.notifyStrings[self.NOTIFY_LOGIN_TEXT]
            title = self.notifyStrings[self.NOTIFY_LOGIN]
            self._notify_alexa(title + " - " + update_text.format(ipaddress))

    def test_notify(self):
        if self._notify_alexa('This is a test notification', force=True):
            return True

    def _notify_alexa(self, message='', force=False):
        if not (sickrage.app.config.twilio.enable or force):
            return False

        sickrage.app.log.debug('Sending Alexa Notification: ' + message)
        if not sickrage.app.api.alexa.send_notification(message):
            sickrage.app.log.error('Alexa notification failed')
            return False

        return True
