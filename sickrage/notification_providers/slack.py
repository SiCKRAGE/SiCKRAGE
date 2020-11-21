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


import json

import requests

import sickrage
from sickrage.notification_providers import NotificationProvider


class SlackNotification(NotificationProvider):
    def __init__(self):
        super(SlackNotification, self).__init__()
        self.name = 'slack'

    def notify_snatch(self, ep_name):
        if sickrage.app.config.slack.notify_on_snatch:
            self._notify_slack(self.notifyStrings[self.NOTIFY_SNATCH] + ': ' + ep_name)

    def notify_download(self, ep_name):
        if sickrage.app.config.slack.notify_on_download:
            self._notify_slack(self.notifyStrings[self.NOTIFY_DOWNLOAD] + ': ' + ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if sickrage.app.config.slack.notify_on_subtitle_download:
            self._notify_slack(self.notifyStrings[self.NOTIFY_SUBTITLE_DOWNLOAD] + ' ' + ep_name + ": " + lang)

    def notify_version_update(self, new_version="??"):
        if sickrage.app.config.slack.enable:
            update_text = self.notifyStrings[self.NOTIFY_GIT_UPDATE_TEXT]
            title = self.notifyStrings[self.NOTIFY_GIT_UPDATE]
            self._notify_slack(title + " - " + update_text + new_version)

    def notify_login(self, ipaddress=""):
        if sickrage.app.config.slack.enable:
            update_text = self.notifyStrings[self.NOTIFY_LOGIN_TEXT]
            title = self.notifyStrings[self.NOTIFY_LOGIN]
            self._notify_slack(title + " - " + update_text.format(ipaddress))

    def test_notify(self):
        return self._notify_slack("This is a test notification from SiCKRAGE", force=True)

    def _send_slack(self, message=None):
        sickrage.app.log.info("Sending slack message: " + message)
        sickrage.app.log.info("Sending slack message  to url: " + sickrage.app.config.slack.webhook)

        headers = {"Content-Type": "application/json"}
        try:
            requests.post(sickrage.app.config.slack.webhook,
                          data=json.dumps(dict(text=message, username="SiCKRAGE")),
                          headers=headers)
        except Exception as e:
            sickrage.app.log.error("Error Sending Slack message: {}".format(e))
            return False

        return True

    def _notify_slack(self, message='', force=False):
        if not sickrage.app.config.slack.enable and not force:
            return False

        return self._send_slack(message)
