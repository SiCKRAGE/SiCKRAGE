# Author: Nyaran <nyayukko@gmail.com>
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

import os
import subprocess

import sickrage
from sickrage.core.common import notifyStrings, NOTIFY_SNATCH, NOTIFY_DOWNLOAD, NOTIFY_SUBTITLE_DOWNLOAD, \
    NOTIFY_GIT_UPDATE_TEXT, NOTIFY_GIT_UPDATE
from sickrage.notifiers import srNotifiers


class synologyNotifier(srNotifiers):
    def _notify_snatch(self, ep_name):
        if sickrage.srCore.srConfig.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH:
            self._send_synologyNotifier(ep_name, notifyStrings[NOTIFY_SNATCH])

    def _notify_download(self, ep_name):
        if sickrage.srCore.srConfig.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD:
            self._send_synologyNotifier(ep_name, notifyStrings[NOTIFY_DOWNLOAD])

    def _notify_subtitle_download(self, ep_name, lang):
        if sickrage.srCore.srConfig.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._send_synologyNotifier(ep_name + ": " + lang, notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD])

    def _notify_version_update(self, new_version="??"):
        if sickrage.srCore.srConfig.USE_SYNOLOGYNOTIFIER:
            update_text = notifyStrings[NOTIFY_GIT_UPDATE_TEXT]
            title = notifyStrings[NOTIFY_GIT_UPDATE]
            self._send_synologyNotifier(update_text + new_version, title)

    def _send_synologyNotifier(self, message, title):
        synodsmnotify_cmd = ["/usr/syno/bin/synodsmnotify", "@administrators", title, message]
        sickrage.srCore.srLogger.info("Executing command " + str(synodsmnotify_cmd))
        sickrage.srCore.srLogger.debug("Absolute path to command: " + os.path.abspath(synodsmnotify_cmd[0]))
        try:
            p = subprocess.Popen(synodsmnotify_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 cwd=sickrage.PROG_DIR)
            out, err = p.communicate()  # @UnusedVariable
            sickrage.srCore.srLogger.debug("Script result: " + str(out))
        except OSError as e:
            sickrage.srCore.srLogger.info("Unable to run synodsmnotify: {}".format(e.message))
