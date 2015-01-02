# Author: Marvin Pinto <me@marvinp.ca>
# Author: Dennis Lutter <lad1337@gmail.com>
# Author: Aaron Bieber <deftly@gmail.com>
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.
import httplib
import urllib, urllib2
import time
import string

import sickbeard
from sickbeard import logger
from sickbeard.common import notifyStrings, NOTIFY_SNATCH, NOTIFY_DOWNLOAD, NOTIFY_SUBTITLE_DOWNLOAD, NOTIFY_GIT_UPDATE, NOTIFY_GIT_UPDATE_TEXT
from sickbeard.exceptions import ex

class CustomAPINotifier:
    def test_notify(self, url=None):
        return self._notifyCustomAPI('Test', "This is a test notification from SickRage", url, force=True)

    def _sendNotification(self, title, msg, url=None):
        """
        Sends a notification
        
        msg: The message to send (unicode)
        title: The title of the message
        userKey: The pushover user id to send the message to (or to subscribe with)
        
        returns: True if the message succeeded, False otherwise
        """

        if url == None:
            url = sickbeard.CUSTOMAPI_URL

        # build up the URL and parameters

        msg = msg.strip()
        url = string.replace(url, "%message%", urllib2.quote(title + ": " + msg))
        logger.log("Custom API in use with folling URL: " + url, logger.DEBUG)
        
        req = urllib2.Request(url)
        # send the request to your custom API
        try:
            reponse = urllib2.urlopen(req)
        except IOError, e:
            message = 'Failed to open "%s".' % url
            if hasattr(e,'code'):
                message = 'Failed to open with error code: %s' % e.code
            
            return False, message
                    
        message = "Notification sent successful."
        logger.log(message, logger.INFO)
        return True, message

    def notify_snatch(self, ep_name, title=notifyStrings[NOTIFY_SNATCH]):
        if sickbeard.CUSTOMAPI_NOTIFY_ONSNATCH:
            self._notifyCustomAPI(title, ep_name)

    def notify_download(self, ep_name, title=notifyStrings[NOTIFY_DOWNLOAD]):
        if sickbeard.CUSTOMAPI_NOTIFY_ONDOWNLOAD:
            self._notifyCustomAPI(title, ep_name)

    def notify_subtitle_download(self, ep_name, lang, title=notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD]):
        if sickbeard.CUSTOMAPI_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notifyCustomAPI(title, ep_name + ": " + lang)
            
    def notify_git_update(self, new_version = "??"):
        if sickbeard.USE_CUSTOMAPI:
            update_text=notifyStrings[NOTIFY_GIT_UPDATE_TEXT]
            title=notifyStrings[NOTIFY_GIT_UPDATE]
            self._notifyCustomAPI(title, update_text + new_version) 

    def _notifyCustomAPI(self, title, message, url=None, force=False):
        """
        Send a notification

        title: The title of the notification to send
        message: The message string to send
        url: the URL of your API
        force: Enforce sending, for instance for testing
        """

        if not sickbeard.USE_CUSTOMAPI and not force:
            logger.log("Notification for Custom API is not enabled, skipping this notification", logger.DEBUG)
            return False

        logger.log("Sending a notification for " + message, logger.DEBUG)

        return self._sendNotification(title, message, url)


notifier = CustomAPINotifier
