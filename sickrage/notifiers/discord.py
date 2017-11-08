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

import json

import requests
import six

import sickrage
from sickrage.notifiers import Notifiers


class DiscordNotifier(Notifiers):
    def __init__(self):
        super(DiscordNotifier, self).__init__()
        self.name = 'discord'

    def _notify_snatch(self, ep_name):
        if sickrage.app.config.DISCORD_NOTIFY_ONSNATCH:
            self._notify_discord(self.notifyStrings[self.NOTIFY_SNATCH] + ': ' + ep_name)

    def _notify_download(self, ep_name):
        if sickrage.app.config.DISCORD_NOTIFY_ONDOWNLOAD:
            self._notify_discord(self.notifyStrings[self.NOTIFY_DOWNLOAD] + ': ' + ep_name)

    def _notify_subtitle_download(self, ep_name, lang):
        if sickrage.app.config.DISCORD_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notify_discord(self.notifyStrings[self.NOTIFY_SUBTITLE_DOWNLOAD] + ' ' + ep_name + ": " + lang)

    def _notify_version_update(self, new_version="??"):
        if sickrage.app.config.USE_DISCORD:
            update_text = self.notifyStrings[self.NOTIFY_GIT_UPDATE_TEXT]
            title = self.notifyStrings[self.NOTIFY_GIT_UPDATE]
            self._notify_discord(title + " - " + update_text + new_version)

    def notify_login(self, ipaddress=""):
        if sickrage.app.config.USE_DISCORD:
            update_text = self.notifyStrings[self.NOTIFY_LOGIN_TEXT]
            title = self.notifyStrings[self.NOTIFY_LOGIN]
            self._notify_discord(title + " - " + update_text.format(ipaddress))

    def test_notify(self):
        return self._notify_discord("This is a test notification from SickRage", force=True)

    def _send_discord(self, message=None):
        discord_webhook = sickrage.app.config.DISCORD_WEBHOOK
        discord_name = sickrage.app.config.DISCORD_NAME
        avatar_icon = sickrage.app.config.DISCORD_AVATAR_URL
        discord_tts = bool(sickrage.app.config.DISCORD_TTS)

        sickrage.app.log.info("Sending discord message: " + message)
        sickrage.app.log.info("Sending discord message  to url: " + discord_webhook)

        if isinstance(message, six.text_type):
            message = message.encode('utf-8')

        headers = {"Content-Type": "application/json"}
        try:
            r = requests.post(discord_webhook, data=json.dumps(dict(content=message,
                                                                    username=discord_name,
                                                                    avatar_url=avatar_icon,
                                                                    tts=discord_tts)), headers=headers)
            r.raise_for_status()
        except Exception as e:
            sickrage.app.log.error("Error Sending Discord message: " + e.message)
            return False

        return True

    def _notify_discord(self, message='', force=False):
        if not sickrage.app.config.USE_DISCORD and not force:
            return False

        return self._send_discord(message)
