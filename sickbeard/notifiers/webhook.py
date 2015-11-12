# Author: Rafael Silva <rpluto@gmail.com>
# Author: Marvin Pinto <me@marvinp.ca>
# Author: Dennis Lutter <lad1337@gmail.com>
# URL: http://code.google.com/p/sickbeard/
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

import urllib, urllib2

import sickbeard

from sickbeard import logger
from sickbeard.common import notifyStrings, NOTIFY_SNATCH, NOTIFY_DOWNLOAD, NOTIFY_SUBTITLE_DOWNLOAD, NOTIFY_GIT_UPDATE, NOTIFY_GIT_UPDATE_TEXT
from sickrage.helper.exceptions import ex

class Webhook:
    def test_notify(self, accesstoken, title="SickRage : Test"):
        return self._sendWebhook("This is a test notification from SickRage", title, accesstoken)

    def _sendWebhook(self, msg, title, accesstoken):
        """
        Sends a JSON object to a specified URL

        msg: The message to send
        title: The title of the message
        accesstoken: to send to this device

        returns: True if the message succeeded, False otherwise
        """

        # build up the URL and parameters
        msg = msg.strip()
        curUrl = API_URL

        data = urllib.urlencode({
                'user_credentials': accesstoken,
                'notification[title]': "SickRage : " + title + ' : ' + msg,
                'notification[long_message]': msg,
                'notification[sound]': "notifier-2"
            })

        # send the webhook to the URL provided
        try:
            req = urllib2.Request(curUrl)
            handle = urllib2.urlopen(req, data,timeout=60)
            handle.close()

        except Exception as e:
            # if we get an error back that doesn't have an error code then who knows what's really happening
            if not hasattr(e, 'code'):
                logger.log("The Webhook notification failed." + ex(e), logger.ERROR)
                return False
            else:
                logger.log("The Webhook notification failed. Error code: " + str(e.code), logger.WARNING)

            # HTTP status 404
            if e.code == 404:
                logger.log("Access token is invalid. Check it.", logger.WARNING)
                return False

            # If you receive an HTTP status code of 400, it is because you failed to send the proper parameters
            elif e.code == 400:
                logger.log("Wrong data send to webhook", logger.ERROR)
                return False

        logger.log("Webhook notification successful.", logger.DEBUG)
        return True

    def notify_snatch(self, ep_name, title=notifyStrings[NOTIFY_SNATCH]):
        if sickbeard.WEBHOOK_NOTIFY_ONSNATCH:
            self._notifyWebhook(title, ep_name)


    def notify_download(self, ep_name, title=notifyStrings[NOTIFY_DOWNLOAD]):
        if sickbeard.WEBHOOK_NOTIFY_ONDOWNLOAD:
            self._notifyWebhook(title, ep_name)

    def notify_subtitle_download(self, ep_name, lang, title=notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD]):
        if sickbeard.WEBHOOK_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notifyWebhook(title, ep_name + ": " + lang)

    def notify_git_update(self, new_version = "??"):
        if sickbeard.USE_WEBHOOK:
            update_text=notifyStrings[NOTIFY_GIT_UPDATE_TEXT]
            title=notifyStrings[NOTIFY_GIT_UPDATE]
            self._notifyWebhook(title, update_text + new_version)

    def _notifyWebhook(self, title, message, accesstoken=None):
        """
        Sends a webhook notification based on the provided info or SR config

        title: The title of the notification to send
        message: The message string to send
        accesstoken: to send to this device
        """

        if not sickbeard.USE_WEBHOOK:
            logger.log("Notification for webhook not enabled, skipping this notification", logger.DEBUG)
            return False

        # if no username was given then use the one from the config
        if not accesstoken:
            accesstoken = sickbeard.WEBHOOK_ACCESSTOKEN

        logger.log("Sending notification for " + message, logger.DEBUG)

        self._sendWebhook(message, title, accesstoken)
        return True


notifier = WebhookNotifier
