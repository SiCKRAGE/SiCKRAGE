# Author: Maciej Olesinski (https://github.com/molesinski/)
# Based on prowl.py by Nic Wolfe <nic@wolfeden.ca>
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

from __future__ import unicode_literals

import socket
from httplib import HTTPException, HTTPSConnection
from ssl import SSLError
from urllib import urlencode

import sickrage
from sickrage.core.common import notifyStrings, NOTIFY_SNATCH, NOTIFY_DOWNLOAD, NOTIFY_SUBTITLE_DOWNLOAD, \
    NOTIFY_GIT_UPDATE_TEXT, NOTIFY_GIT_UPDATE
from sickrage.notifiers import srNotifiers


class PushalotNotifier(srNotifiers):
    def test_notify(self, pushalot_authorizationtoken):
        return self._sendPushalot(pushalot_authorizationtoken, event="Test",
                                  message="Testing Pushalot settings from SiCKRAGE", force=True)

    def _notify_snatch(self, ep_name):
        if sickrage.srCore.srConfig.PUSHALOT_NOTIFY_ONSNATCH:
            self._sendPushalot(pushalot_authorizationtoken=sickrage.srCore.srConfig.PUSHALOT_AUTHORIZATIONTOKEN,
                               event=notifyStrings[NOTIFY_SNATCH],
                               message=ep_name)

    def _notify_download(self, ep_name):
        if sickrage.srCore.srConfig.PUSHALOT_NOTIFY_ONDOWNLOAD:
            self._sendPushalot(pushalot_authorizationtoken=sickrage.srCore.srConfig.PUSHALOT_AUTHORIZATIONTOKEN,
                               event=notifyStrings[NOTIFY_DOWNLOAD],
                               message=ep_name)

    def _notify_subtitle_download(self, ep_name, lang):
        if sickrage.srCore.srConfig.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._sendPushalot(pushalot_authorizationtoken=sickrage.srCore.srConfig.PUSHALOT_AUTHORIZATIONTOKEN,
                               event=notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD],
                               message=ep_name + ": " + lang)

    def _notify_version_update(self, new_version="??"):
        if sickrage.srCore.srConfig.USE_PUSHALOT:
            update_text = notifyStrings[NOTIFY_GIT_UPDATE_TEXT]
            title = notifyStrings[NOTIFY_GIT_UPDATE]
            self._sendPushalot(pushalot_authorizationtoken=sickrage.srCore.srConfig.PUSHALOT_AUTHORIZATIONTOKEN,
                               event=title,
                               message=update_text + new_version)

    def _sendPushalot(self, pushalot_authorizationtoken=None, event=None, message=None, force=False):

        if not sickrage.srCore.srConfig.USE_PUSHALOT and not force:
            return False

        sickrage.srCore.srLogger.debug("Pushalot event: " + event)
        sickrage.srCore.srLogger.debug("Pushalot message: " + message)
        sickrage.srCore.srLogger.debug("Pushalot api: " + pushalot_authorizationtoken)

        http_handler = HTTPSConnection("pushalot.com")

        data = {'AuthorizationToken': pushalot_authorizationtoken,
                'Title': event.encode('utf-8'),
                'Body': message.encode('utf-8')}

        try:
            http_handler.request("POST",
                                 "/api/sendmessage",
                                 headers={'Content-type': "application/x-www-form-urlencoded"},
                                 body=urlencode(data))
        except (SSLError, HTTPException, socket.error):
            sickrage.srCore.srLogger.error("Pushalot notification failed.")
            return False
        response = http_handler.getresponse()
        request_status = response.status

        if request_status == 200:
            sickrage.srCore.srLogger.debug("Pushalot notifications sent.")
            return True
        elif request_status == 410:
            sickrage.srCore.srLogger.error("Pushalot auth failed: %s" % response.reason)
            return False
        else:
            sickrage.srCore.srLogger.error("Pushalot notification failed.")
            return False
