# Author: Nyaran <nyayukko@gmail.com>
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


import os
import subprocess

import sickrage
from sickrage.notification_providers import NotificationProvider


class SynologyNotification(NotificationProvider):
    def __init__(self):
        super(SynologyNotification, self).__init__()
        self.name = 'synology'

    def notify_snatch(self, ep_name):
        if sickrage.app.config.synology.notify_on_snatch:
            self._send_synology_notification(ep_name, self.notifyStrings[self.NOTIFY_SNATCH])

    def notify_download(self, ep_name):
        if sickrage.app.config.synology.notify_on_download:
            self._send_synology_notification(ep_name, self.notifyStrings[self.NOTIFY_DOWNLOAD])

    def notify_subtitle_download(self, ep_name, lang):
        if sickrage.app.config.synology.notify_on_subtitle_download:
            self._send_synology_notification(ep_name + ": " + lang, self.notifyStrings[self.NOTIFY_SUBTITLE_DOWNLOAD])

    def notify_version_update(self, new_version="??"):
        if sickrage.app.config.synology.enable_notifications:
            update_text = self.notifyStrings[self.NOTIFY_GIT_UPDATE_TEXT]
            title = self.notifyStrings[self.NOTIFY_GIT_UPDATE]
            self._send_synology_notification(update_text + new_version, title)

    def _send_synology_notification(self, message, title):
        synodsmnotify_cmd = ["/usr/syno/bin/synodsmnotify", "@administrators", title, message]
        sickrage.app.log.info("Executing command " + str(synodsmnotify_cmd))
        sickrage.app.log.debug("Absolute path to command: " + os.path.abspath(synodsmnotify_cmd[0]))
        try:
            p = subprocess.Popen(synodsmnotify_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 cwd=sickrage.PROG_DIR)
            out, err = p.communicate()
            sickrage.app.log.debug("Script result: " + str(out))
        except OSError as e:
            sickrage.app.log.info("Unable to run synodsmnotify: {}".format(e))
