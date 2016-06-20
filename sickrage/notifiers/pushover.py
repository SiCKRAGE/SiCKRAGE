# Author: Marvin Pinto <me@marvinp.ca>
# Author: Dennis Lutter <lad1337@gmail.com>
# Author: Aaron Bieber <deftly@gmail.com>
# URL: http://github.com/SiCKRAGETV/SickRage/
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

import httplib
import time
import urllib
import urllib2

import sickrage
from sickrage.core.common import NOTIFY_GIT_UPDATE, NOTIFY_GIT_UPDATE_TEXT, \
    notifyStrings, NOTIFY_SNATCH, NOTIFY_DOWNLOAD, NOTIFY_SUBTITLE_DOWNLOAD
from sickrage.notifiers import srNotifiers

API_URL = "https://api.pushover.net/1/messages.json"


# pylint: disable=W0232
class PushoverNotifier(srNotifiers):
    def test_notify(self, userKey=None, apiKey=None):
        return self._notifyPushover("This is a test notification from SiCKRAGE", 'Test', userKey=userKey, apiKey=apiKey,
                                    force=True)

    def _sendPushover(self, msg, title, sound=None, userKey=None, apiKey=None):
        """
        Sends a pushover notification to the address provided

        msg: The message to send (unicode)
        title: The title of the message
        sound: The notification sound to use
        userKey: The pushover user id to send the message to (or to subscribe with)
        apiKey: The pushover api key to use
        returns: True if the message succeeded, False otherwise
        """

        if userKey is None:
            userKey = sickrage.srCore.srConfig.PUSHOVER_USERKEY

        if apiKey is None:
            apiKey = sickrage.srCore.srConfig.PUSHOVER_APIKEY

        if sound is None:
            sound = sickrage.srCore.srConfig.PUSHOVER_SOUND

        sickrage.srCore.srLogger.debug("Pushover API KEY in use: " + apiKey)

        # build up the URL and parameters
        msg = msg.strip()

        # send the request to pushover
        try:
            if sickrage.srCore.srConfig.PUSHOVER_SOUND != "default":
                args = {"token": apiKey,
                        "user": userKey,
                        "title": title.encode('utf-8'),
                        "message": msg.encode('utf-8'),
                        "timestamp": int(time.time()),
                        "retry": 60,
                        "expire": 3600,
                        "sound": sound,
                        }
            else:
                # sound is default, so don't send it
                args = {"token": apiKey,
                        "user": userKey,
                        "title": title.encode('utf-8'),
                        "message": msg.encode('utf-8'),
                        "timestamp": int(time.time()),
                        "retry": 60,
                        "expire": 3600,
                        }

            if sickrage.srCore.srConfig.PUSHOVER_DEVICE:
                args["device"] = sickrage.srCore.srConfig.PUSHOVER_DEVICE

            conn = httplib.HTTPSConnection("api.pushover.net:443")
            conn.request("POST", "/1/messages.json",
                         urllib.urlencode(args), {"Content-type": "application/x-www-form-urlencoded"})

        except urllib2.HTTPError as e:
            # if we get an error back that doesn't have an error code then who knows what's really happening
            if not hasattr(e, 'code'):
                sickrage.srCore.srLogger.error("Pushover notification failed.{}".format(e.message))
                return False
            else:
                sickrage.srCore.srLogger.error("Pushover notification failed. Error code: " + str(e.code))

            # HTTP status 404 if the provided email address isn't a Pushover user.
            if e.code == 404:
                sickrage.srCore.srLogger.warning("Username is wrong/not a pushover email. Pushover will send an email to it")
                return False

            # For HTTP status code 401's, it is because you are passing in either an invalid token, or the user has not added your service.
            elif e.code == 401:

                # HTTP status 401 if the user doesn't have the service added
                subscribeNote = self._sendPushover(msg, title, sound=sound, userKey=userKey, apiKey=apiKey)
                if subscribeNote:
                    sickrage.srCore.srLogger.debug("Subscription sent")
                    return True
                else:
                    sickrage.srCore.srLogger.error("Subscription could not be sent")
                    return False

            # If you receive an HTTP status code of 400, it is because you failed to send the proper parameters
            elif e.code == 400:
                sickrage.srCore.srLogger.error("Wrong data sent to pushover")
                return False

            # If you receive a HTTP status code of 429, it is because the message limit has been reached (free limit is 7,500)
            elif e.code == 429:
                sickrage.srCore.srLogger.error("Pushover API message limit reached - try a different API key")
                return False

        sickrage.srCore.srLogger.info("Pushover notification successful.")
        return True

    def _notify_snatch(self, ep_name, title=notifyStrings[NOTIFY_SNATCH]):
        if sickrage.srCore.srConfig.PUSHOVER_NOTIFY_ONSNATCH:
            self._notifyPushover(title, ep_name)

    def _notify_download(self, ep_name, title=notifyStrings[NOTIFY_DOWNLOAD]):
        if sickrage.srCore.srConfig.PUSHOVER_NOTIFY_ONDOWNLOAD:
            self._notifyPushover(title, ep_name)

    def _notify_subtitle_download(self, ep_name, lang, title=notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD]):
        if sickrage.srCore.srConfig.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notifyPushover(title, ep_name + ": " + lang)

    def _notify_version_update(self, new_version="??"):
        if sickrage.srCore.srConfig.USE_PUSHOVER:
            update_text = notifyStrings[NOTIFY_GIT_UPDATE_TEXT]
            title = notifyStrings[NOTIFY_GIT_UPDATE]
            self._notifyPushover(title, update_text + new_version)

    def _notifyPushover(self, title, message, sound=None, userKey=None, apiKey=None, force=False):
        """
        Sends a pushover notification based on the provided info or SR config

        title: The title of the notification to send
        message: The message string to send
        sound: The notification sound to use
        userKey: The userKey to send the notification to
        apiKey: The apiKey to use to send the notification
        force: Enforce sending, for instance for testing
        """

        if not sickrage.srCore.srConfig.USE_PUSHOVER and not force:
            sickrage.srCore.srLogger.debug("Notification for Pushover not enabled, skipping this notification")
            return False

        sickrage.srCore.srLogger.debug("Sending notification for " + message)

        return self._sendPushover(message, title, sound=sound, userKey=userKey, apiKey=apiKey)
