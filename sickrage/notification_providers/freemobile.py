# Author: Marvin Pinto <me@marvinp.ca>
# Author: Dennis Lutter <lad1337@gmail.com>
# Author: Aaron Bieber <deftly@gmail.com>
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
from urllib import parse

import requests

import sickrage
from sickrage.core.websession import WebSession
from sickrage.notification_providers import NotificationProvider


class FreeMobileNotification(NotificationProvider):
    def __init__(self):
        super(FreeMobileNotification, self).__init__()
        self.name = 'freemobile'

    def test_notify(self, id=None, apiKey=None):
        return self._notifyFreeMobile('Test', "This is a test notification from SiCKRAGE", id, apiKey, force=True)

    def _sendFreeMobileSMS(self, title, msg, id=None, apiKey=None):
        """
        Sends a SMS notification

        msg: The message to send (unicode)
        title: The title of the message
        userKey: The pushover user id to send the message to (or to subscribe with)

        returns: True if the message succeeded, False otherwise
        """

        if id is None:
            id = sickrage.app.config.freemobile.user_id

        if apiKey is None:
            apiKey = sickrage.app.config.freemobile.apikey

        sickrage.app.log.debug("Free Mobile in use with API KEY: " + apiKey)

        # build up the URL and parameters
        msg = msg.strip()
        msg_quoted = parse.quote(title + ": " + msg)
        URL = "https://smsapi.free-mobile.fr/sendmsg?user=" + id + "&pass=" + apiKey + "&msg=" + msg_quoted

        # send the request to Free Mobile
        try:
            WebSession().get(URL)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                message = "Missing parameter(s)."
                sickrage.app.log.error(message)
                return False, message
            if e.response.status_code == 402:
                message = "Too much SMS sent in a short time."
                sickrage.app.log.error(message)
                return False, message
            if e.response.status_code == 403:
                message = "API service isn't enabled in your account or ID / API key is incorrect."
                sickrage.app.log.error(message)
                return False, message
            if e.response.status_code == 500:
                message = "Server error. Please retry in few moment."
                sickrage.app.log.error(message)
                return False, message

            message = "Error while sending SMS: {}".format(e)
            sickrage.app.log.error(message)
            return False, message

        message = "Free Mobile SMS successful."
        sickrage.app.log.info(message)
        return True, message

    def notify_snatch(self, ep_name, title=None):
        if not title:
            title = self.notifyStrings[self.NOTIFY_SNATCH]

        if sickrage.app.config.freemobile.notify_on_snatch:
            self._notifyFreeMobile(title, ep_name)

    def notify_download(self, ep_name, title=None):
        if not title:
            title = self.notifyStrings[self.NOTIFY_DOWNLOAD]

        if sickrage.app.config.freemobile.notify_on_download:
            self._notifyFreeMobile(title, ep_name)

    def notify_subtitle_download(self, ep_name, lang, title=None):
        if not title:
            title = self.notifyStrings[self.NOTIFY_SUBTITLE_DOWNLOAD]

        if sickrage.app.config.freemobile.notify_on_subtitle_download:
            self._notifyFreeMobile(title, ep_name + ": " + lang)

    def notify_version_update(self, new_version="??"):
        if sickrage.app.config.freemobile.enable:
            update_text = self.notifyStrings[self.NOTIFY_GIT_UPDATE_TEXT]
            title = self.notifyStrings[self.NOTIFY_GIT_UPDATE]
            self._notifyFreeMobile(title, update_text + new_version)

    def _notifyFreeMobile(self, title, message, id=None, apiKey=None, force=False):
        """
        Sends a SMS notification

        title: The title of the notification to send
        message: The message string to send
        id: Your Free Mobile customer ID
        apikey: Your Free Mobile API key
        force: Enforce sending, for instance for testing
        """

        if not sickrage.app.config.freemobile.enable and not force:
            sickrage.app.log.debug("Notification for Free Mobile not enabled, skipping this notification")
            return False, "Disabled"

        sickrage.app.log.debug("Sending a SMS for " + message)

        return self._sendFreeMobileSMS(title, message, id, apiKey)
