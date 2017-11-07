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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, unicode_literals

import re

from twilio.base.exceptions import TwilioRestException
from twilio.rest import TwilioRestClient

import sickrage
from sickrage.notifiers import srNotifiers


class TwilioNotifier(srNotifiers):
    number_regex = re.compile(r'^\+1-\d{3}-\d{3}-\d{4}$')
    account_regex = re.compile(r'^AC[a-z0-9]{32}$')
    auth_regex = re.compile(r'^[a-z0-9]{32}$')
    phone_regex = re.compile(r'^PN[a-z0-9]{32}$')

    def __init__(self):
        super(TwilioNotifier, self).__init__()
        self.name = 'twilio'

    @property
    def number(self):
        return self.client.phone_numbers.get(sickrage.app.config.TWILIO_PHONE_SID)

    @property
    def client(self):
        return TwilioRestClient(sickrage.app.config.TWILIO_ACCOUNT_SID,
                                sickrage.app.config.TWILIO_AUTH_TOKEN)

    def _notify_snatch(self, ep_name):
        if sickrage.app.config.TWILIO_NOTIFY_ONSNATCH:
            self._notifyTwilio(self.notifyStrings[self.NOTIFY_SNATCH] + ': ' + ep_name)

    def _notify_download(self, ep_name):
        if sickrage.app.config.TWILIO_NOTIFY_ONDOWNLOAD:
            self._notifyTwilio(self.notifyStrings[self.NOTIFY_DOWNLOAD] + ': ' + ep_name)

    def _notify_subtitle_download(self, ep_name, lang):
        if sickrage.app.config.TWILIO_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notifyTwilio(self.notifyStrings[self.NOTIFY_SUBTITLE_DOWNLOAD] + ' ' + ep_name + ': ' + lang)

    def _notify_git_update(self, new_version):
        if sickrage.app.config.USE_TWILIO:
            update_text = self.notifyStrings[self.NOTIFY_GIT_UPDATE_TEXT]
            self._notifyTwilio(update_text + new_version)

    def _notify_login(self, ipaddress=""):
        if sickrage.app.config.USE_TWILIO:
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
        if not (sickrage.app.config.USE_TWILIO or force or self.number_regex.match(
                sickrage.app.config.TWILIO_TO_NUMBER)):
            return False

        sickrage.app.log.debug('Sending Twilio SMS: ' + message)

        try:
            self.client.messages.create(
                body=message,
                to=sickrage.app.config.TWILIO_TO_NUMBER,
                from_=self.number.phone_number,
            )
        except TwilioRestException as e:
            sickrage.app.log.error('Twilio notification failed:' + e.message)

            if allow_raise:
                raise e

        return True
