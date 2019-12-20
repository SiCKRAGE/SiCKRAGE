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
from sickrage.notifiers import Notifiers


class DiscordNotifier(Notifiers):
    def __init__(self):
        super(DiscordNotifier, self).__init__()
        self.name = 'discord'

    def notify_snatch(self, ep_name):
        if sickrage.app.config.discord_notify_onsnatch:
            self._notify_discord(self.notifyStrings[self.NOTIFY_SNATCH] + ': ' + ep_name)

    def notify_download(self, ep_name):
        if sickrage.app.config.discord_notify_ondownload:
            self._notify_discord(self.notifyStrings[self.NOTIFY_DOWNLOAD] + ': ' + ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if sickrage.app.config.discord_notify_onsubtitledownload:
            self._notify_discord(self.notifyStrings[self.NOTIFY_SUBTITLE_DOWNLOAD] + ' ' + ep_name + ": " + lang)

    def notify_version_update(self, new_version="??"):
        if sickrage.app.config.use_discord:
            update_text = self.notifyStrings[self.NOTIFY_GIT_UPDATE_TEXT]
            title = self.notifyStrings[self.NOTIFY_GIT_UPDATE]
            self._notify_discord(title + " - " + update_text + new_version)

    def mass_notify_login(self, ipaddress=""):
        if sickrage.app.config.use_discord:
            update_text = self.notifyStrings[self.NOTIFY_LOGIN_TEXT]
            title = self.notifyStrings[self.NOTIFY_LOGIN]
            self._notify_discord(title + " - " + update_text.format(ipaddress))

    def test_notify(self):
        return self._notify_discord("This is a test notification from SickRage", force=True)

    def _send_discord(self, message=None):
        discord_webhook = sickrage.app.config.discord_webhook
        discord_name = sickrage.app.config.discord_name
        avatar_icon = sickrage.app.config.discord_avatar_url
        discord_tts = bool(sickrage.app.config.discord_tts)

        sickrage.app.log.info("Sending discord message: " + message)
        sickrage.app.log.info("Sending discord message  to url: " + discord_webhook)

        headers = {"Content-Type": "application/json"}

        try:
            requests.post(discord_webhook, data=json.dumps(dict(content=message,
                                                                username=discord_name,
                                                                avatar_url=avatar_icon,
                                                                tts=discord_tts)), headers=headers)
        except Exception as e:
            sickrage.app.log.warning("Unable to send Discord message: {}".format(e))
            return False

        return True

    def _notify_discord(self, message='', force=False):
        if not sickrage.app.config.use_discord and not force:
            return False

        return self._send_discord(message)
