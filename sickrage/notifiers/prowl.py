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

from __future__ import unicode_literals

import socket
from httplib import HTTPException, HTTPSConnection
from urllib import urlencode

import sickrage
from requests.exceptions import SSLError
from sickrage.core.common import notifyStrings, NOTIFY_SNATCH, NOTIFY_DOWNLOAD, NOTIFY_SUBTITLE_DOWNLOAD, \
    NOTIFY_GIT_UPDATE_TEXT, NOTIFY_GIT_UPDATE
from sickrage.notifiers import srNotifiers

class ProwlNotifier(srNotifiers):
    def test_notify(self, prowl_api, prowl_priority):
        return self._sendProwl(prowl_api, prowl_priority, event="Test",
                               message="Testing Prowl settings from SiCKRAGE", force=True)

    def _notify_snatch(self, ep_name):
        if sickrage.srCore.srConfig.PROWL_NOTIFY_ONSNATCH:
            self._sendProwl(prowl_api=None, prowl_priority=None, event=notifyStrings[NOTIFY_SNATCH],
                            message=ep_name)

    def _notify_download(self, ep_name):
        if sickrage.srCore.srConfig.PROWL_NOTIFY_ONDOWNLOAD:
            self._sendProwl(prowl_api=None, prowl_priority=None, event=notifyStrings[NOTIFY_DOWNLOAD],
                            message=ep_name)

    def _notify_subtitle_download(self, ep_name, lang):
        if sickrage.srCore.srConfig.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._sendProwl(prowl_api=None, prowl_priority=None,
                            event=notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD], message=ep_name + ": " + lang)

    def _notify_version_update(self, new_version="??"):
        if sickrage.srCore.srConfig.USE_PROWL:
            update_text = notifyStrings[NOTIFY_GIT_UPDATE_TEXT]
            title = notifyStrings[NOTIFY_GIT_UPDATE]
            self._sendProwl(prowl_api=None, prowl_priority=None,
                            event=title, message=update_text + new_version)

    def _sendProwl(self, prowl_api=None, prowl_priority=None, event=None, message=None, force=False):

        if not sickrage.srCore.srConfig.USE_PROWL and not force:
            return False

        if prowl_api is None:
            prowl_api = sickrage.srCore.srConfig.PROWL_API

        if prowl_priority is None:
            prowl_priority = sickrage.srCore.srConfig.PROWL_PRIORITY

        title = "SiCKRAGE"

        sickrage.srCore.srLogger.debug("PROWL: Sending notice with details: event=\"%s\", message=\"%s\", priority=%s, api=%s" % (
        event, message, prowl_priority, prowl_api))

        http_handler = HTTPSConnection("api.prowlapp.com")

        data = {'apikey': prowl_api,
                'application': title,
                'event': event,
                'description': message.encode('utf-8'),
                'priority': prowl_priority}

        try:
            http_handler.request("POST",
                                 "/publicapi/add",
                                 headers={'Content-type': "application/x-www-form-urlencoded"},
                                 body=urlencode(data))
        except (SSLError, HTTPException, socket.error):
            sickrage.srCore.srLogger.error("Prowl notification failed.")
            return False
        response = http_handler.getresponse()
        request_status = response.status

        if request_status == 200:
            sickrage.srCore.srLogger.info("Prowl notifications sent.")
            return True
        elif request_status == 401:
            sickrage.srCore.srLogger.error("Prowl auth failed: %s" % response.reason)
            return False
        else:
            sickrage.srCore.srLogger.error("Prowl notification failed.")
            return False
