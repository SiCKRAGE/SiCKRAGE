# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
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


from urllib.parse import urlencode

import requests

import sickrage
from sickrage.core.websession import WebSession
from sickrage.notification_providers import NotificationProvider


class PushalotNotification(NotificationProvider):
    def __init__(self):
        super(PushalotNotification, self).__init__()
        self.name = 'pushalot'

    def test_notify(self, pushalot_authorizationtoken):
        return self._sendPushalot(pushalot_authorizationtoken, event="Test",
                                  message="Testing Pushalot settings from SiCKRAGE", force=True)

    def notify_snatch(self, ep_name):
        if sickrage.app.config.pushalot.notify_on_snatch:
            self._sendPushalot(pushalot_authorizationtoken=sickrage.app.config.pushalot.auth_token,
                               event=self.notifyStrings[self.NOTIFY_SNATCH],
                               message=ep_name)

    def notify_download(self, ep_name):
        if sickrage.app.config.pushalot.notify_on_download:
            self._sendPushalot(pushalot_authorizationtoken=sickrage.app.config.pushalot.auth_token,
                               event=self.notifyStrings[self.NOTIFY_DOWNLOAD],
                               message=ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if sickrage.app.config.pushalot.notify_on_subtitle_download:
            self._sendPushalot(pushalot_authorizationtoken=sickrage.app.config.pushalot.auth_token,
                               event=self.notifyStrings[self.NOTIFY_SUBTITLE_DOWNLOAD],
                               message=ep_name + ": " + lang)

    def notify_version_update(self, new_version="??"):
        if sickrage.app.config.pushalot.enable:
            update_text = self.notifyStrings[self.NOTIFY_GIT_UPDATE_TEXT]
            title = self.notifyStrings[self.NOTIFY_GIT_UPDATE]
            self._sendPushalot(pushalot_authorizationtoken=sickrage.app.config.pushalot.auth_token,
                               event=title,
                               message=update_text + new_version)

    def _sendPushalot(self, pushalot_authorizationtoken=None, event=None, message=None, force=False):
        if not sickrage.app.config.pushalot.enable and not force:
            return False

        sickrage.app.log.debug("Pushalot event: " + event)
        sickrage.app.log.debug("Pushalot message: " + message)
        sickrage.app.log.debug("Pushalot api: " + pushalot_authorizationtoken)

        data = {'AuthorizationToken': pushalot_authorizationtoken,
                'Title': event,
                'Body': message}

        try:
            WebSession().post("https://pushalot.com/api/sendmessage",
                              headers={'Content-type': "application/x-www-form-urlencoded"},
                              data=urlencode(data))
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 410:
                sickrage.app.log.warning("Pushalot auth failed: %s" % e.response.text)
                return False

            sickrage.app.log.error("Pushalot notification failed.")
            return False

        sickrage.app.log.debug("Pushalot notifications sent.")
        return True
