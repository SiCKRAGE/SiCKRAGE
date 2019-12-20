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


from urllib.parse import urlencode

import requests

import sickrage
from sickrage.core.websession import WebSession
from sickrage.notifiers import Notifiers


class ProwlNotifier(Notifiers):
    def __init__(self):
        super(ProwlNotifier, self).__init__()
        self.name = 'prowl'

    def test_notify(self, prowl_api, prowl_priority):
        return self._sendProwl(prowl_api, prowl_priority, event="Test",
                               message="Testing Prowl settings from SiCKRAGE", force=True)

    def notify_snatch(self, ep_name):
        if sickrage.app.config.prowl_notify_onsnatch:
            self._sendProwl(prowl_api=None, prowl_priority=None, event=self.notifyStrings[self.NOTIFY_SNATCH],
                            message=ep_name)

    def notify_download(self, ep_name):
        if sickrage.app.config.prowl_notify_ondownload:
            self._sendProwl(prowl_api=None, prowl_priority=None, event=self.notifyStrings[self.NOTIFY_DOWNLOAD],
                            message=ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if sickrage.app.config.prowl_notify_onsubtitledownload:
            self._sendProwl(prowl_api=None, prowl_priority=None,
                            event=self.notifyStrings[self.NOTIFY_SUBTITLE_DOWNLOAD], message=ep_name + ": " + lang)

    def notify_version_update(self, new_version="??"):
        if sickrage.app.config.use_prowl:
            update_text = self.notifyStrings[self.NOTIFY_GIT_UPDATE_TEXT]
            title = self.notifyStrings[self.NOTIFY_GIT_UPDATE]
            self._sendProwl(prowl_api=None, prowl_priority=None,
                            event=title, message=update_text + new_version)

    def _sendProwl(self, prowl_api=None, prowl_priority=None, event=None, message=None, force=False):

        if not sickrage.app.config.use_prowl and not force:
            return False

        if prowl_api is None:
            prowl_api = sickrage.app.config.prowl_api

        if prowl_priority is None:
            prowl_priority = sickrage.app.config.prowl_priority

        title = "SiCKRAGE"

        sickrage.app.log.debug(
            "PROWL: Sending notice with details: event=\"%s\", message=\"%s\", priority=%s, api=%s" % (
                event, message, prowl_priority, prowl_api))

        data = {'apikey': prowl_api,
                'application': title,
                'event': event,
                'description': message,
                'priority': prowl_priority}

        try:
            resp = WebSession().post("https://api.prowlapp.com/publicapi/add",
                                     headers={'Content-type': "application/x-www-form-urlencoded"},
                                     data=urlencode(data))

            if not resp.ok:
                sickrage.app.log.error("Prowl notification failed.")
                return False
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                sickrage.app.log.error("Prowl auth failed: %s" % e.response.text)
                return False

        sickrage.app.log.info("Prowl notifications sent.")
        return True
