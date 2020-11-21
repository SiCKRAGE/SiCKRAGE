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


class TwilioNotification(NotificationProvider):
    number_regex = re.compile(r'^\+1-\d{3}-\d{3}-\d{4}$')
    account_regex = re.compile(r'^AC[a-z0-9]{32}$')
    auth_regex = re.compile(r'^[a-z0-9]{32}$')
    phone_regex = re.compile(r'^PN[a-z0-9]{32}$')

    def __init__(self):
        super(TwilioNotification, self).__init__()
        self.name = 'twilio'

    @property
    def number(self):
        return self.client.phone_numbers.get(sickrage.app.config.twilio.phone_sid)

    @property
    def client(self):
        return TwilioRestClient(sickrage.app.config.twilio.account_sid,
                                sickrage.app.config.twilio.auth_token)

    def notify_snatch(self, ep_name):
        if sickrage.app.config.twilio.notify_on_snatch:
            self._notifyTwilio(self.notifyStrings[self.NOTIFY_SNATCH] + ': ' + ep_name)

    def notify_download(self, ep_name):
        if sickrage.app.config.twilio.notify_on_download:
            self._notifyTwilio(self.notifyStrings[self.NOTIFY_DOWNLOAD] + ': ' + ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if sickrage.app.config.twilio.notify_on_subtitle_download:
            self._notifyTwilio(self.notifyStrings[self.NOTIFY_SUBTITLE_DOWNLOAD] + ' ' + ep_name + ': ' + lang)

    def notify_version_update(self, new_version):
        if sickrage.app.config.twilio.enable:
            update_text = self.notifyStrings[self.NOTIFY_GIT_UPDATE_TEXT]
            self._notifyTwilio(update_text + new_version)

    def notify_login(self, ipaddress=""):
        if sickrage.app.config.twilio.enable:
            update_text = self.notifyStrings[self.NOTIFY_LOGIN_TEXT]
            title = self.notifyStrings[self.NOTIFY_LOGIN]
            self._notifyTwilio(title + " - " + update_text.format(ipaddress))

    def test_notify(self):
        try:
            if not self.number.capabilities['sms']:
                return False

            return self._notifyTwilio('This is a test notification from SickRage', force=True, allow_raise=True)
        except TwilioRestException:
            return False

    def _notifyTwilio(self, message='', force=False, allow_raise=False):
        if not (sickrage.app.config.twilio.enable or force or self.number_regex.match(
                sickrage.app.config.twilio.to_number)):
            return False

        sickrage.app.log.debug('Sending Twilio SMS: ' + message)

        try:
            self.client.messages.create(
                body=message,
                to=sickrage.app.config.twilio.to_number,
                from_=self.number.phone_number,
            )
        except TwilioRestException as e:
            sickrage.app.log.error('Twilio notification failed: {}'.format(e))

            if allow_raise:
                raise e

        return True
