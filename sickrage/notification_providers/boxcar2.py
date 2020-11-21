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
from urllib.parse import urlencode

import requests
from requests import RequestException

import sickrage
from sickrage.core.websession import WebSession
from sickrage.notification_providers import NotificationProvider

API_URL = "https://new.boxcar.io/api/notifications"


class Boxcar2Notification(NotificationProvider):
    def __init__(self):
        super(Boxcar2Notification, self).__init__()
        self.name = 'boxcar2'

    def test_notify(self, accesstoken, title="SiCKRAGE : Test"):
        return self._sendBoxcar2("This is a test notification from SiCKRAGE", title, accesstoken)

    def _sendBoxcar2(self, msg, title, accesstoken):
        """
        Sends a boxcar2 notification to the address provided

        msg: The message to send
        title: The title of the message
        accesstoken: to send to this device

        returns: True if the message succeeded, False otherwise
        """

        # build up the URL and parameters more info goes here -
        # https://boxcar.uservoice.com/knowledgebase/articles/306788-how-to-send-your-boxcar-account-a-notification
        msg = msg.strip()

        data = urlencode({
            'user_credentials': accesstoken,
            'notification[title]': "SiCKRAGE : " + title + ' : ' + msg,
            'notification[long_message]': msg,
            'notification[sound]': "notifier-2"
        })

        try:
            # send the request to boxcar2
            WebSession().get(API_URL, data=data, timeout=120)
        except requests.exceptions.HTTPError as e:
            # if we get an error back that doesn't have an error code then who knows what's really happening
            sickrage.app.log.warning("Boxcar2 notification failed. Error code: {}".format(e.response.status_code))

            # HTTP status 404
            if e.response.status_code == 404:
                sickrage.app.log.warning("Access token is invalid. Check it.")
                return False

            # If you receive an HTTP status code of 400, it is because you failed to send the proper parameters
            elif e.response.status_code == 400:
                sickrage.app.log.warning("Wrong data send to boxcar2")
                return False

            sickrage.app.log.error("Boxcar2 notification failed.")
            return False

        sickrage.app.log.debug("Boxcar2 notification successful.")
        return True

    def notify_snatch(self, ep_name, title=None):
        if not title:
            title = self.notifyStrings[self.NOTIFY_SNATCH]

        if sickrage.app.config.boxcar2.notify_on_snatch:
            self._notifyBoxcar2(title, ep_name)

    def notify_download(self, ep_name, title=None):
        if not title:
            title = self.notifyStrings[self.NOTIFY_DOWNLOAD]

        if sickrage.app.config.boxcar2.notify_on_download:
            self._notifyBoxcar2(title, ep_name)

    def notify_subtitle_download(self, ep_name, lang, title=None):
        if not title:
            title = self.notifyStrings[self.NOTIFY_SUBTITLE_DOWNLOAD]

        if sickrage.app.config.boxcar2.notify_on_subtitle_download:
            self._notifyBoxcar2(title, ep_name + ": " + lang)

    def notify_version_update(self, new_version="??"):
        if sickrage.app.config.boxcar2.enable:
            update_text = self.notifyStrings[self.NOTIFY_GIT_UPDATE_TEXT]
            title = self.notifyStrings[self.NOTIFY_GIT_UPDATE]
            self._notifyBoxcar2(title, update_text + new_version)

    def _notifyBoxcar2(self, title, message, accesstoken=None):
        """
        Sends a boxcar2 notification based on the provided info or SB config

        title: The title of the notification to send
        message: The message string to send
        accesstoken: to send to this device
        """

        if not sickrage.app.config.boxcar2.enable:
            sickrage.app.log.debug("Notification for Boxcar2 not enabled, skipping this notification")
            return False

        # if no username was given then use the one from the config
        if not accesstoken:
            accesstoken = sickrage.app.config.boxcar2.access_token

        sickrage.app.log.debug("Sending notification for " + message)

        self._sendBoxcar2(message, title, accesstoken)
        return True
