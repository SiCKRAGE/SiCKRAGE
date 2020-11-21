# Author: Sebastien Erard <sebastien_erard@hotmail.com>
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import os
import subprocess

import sickrage
from sickrage.notification_providers import NotificationProvider


class SynologyIndexNotification(NotificationProvider):
    def __init__(self):
        super(SynologyIndexNotification, self).__init__()
        self.name = 'synoindex'

    def notify_snatch(self, ep_name):
        pass

    def notify_download(self, ep_name):
        pass

    def notify_subtitle_download(self, ep_name, lang):
        pass

    def notify_version_update(self, new_version):
        pass

    def moveFolder(self, old_path, new_path):
        self.moveObject(old_path, new_path)

    def moveFile(self, old_file, new_file):
        self.moveObject(old_file, new_file)

    def moveObject(self, old_path, new_path):
        if sickrage.app.config.synology.enable_index:
            synoindex_cmd = ['/usr/syno/bin/synoindex', '-N', os.path.abspath(new_path),
                             os.path.abspath(old_path)]
            sickrage.app.log.debug("Executing command " + str(synoindex_cmd))
            sickrage.app.log.debug("Absolute path to command: " + os.path.abspath(synoindex_cmd[0]))
            try:
                p = subprocess.Popen(synoindex_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     cwd=sickrage.PROG_DIR)
                out, err = p.communicate()
                sickrage.app.log.debug("Script result: " + str(out))
            except OSError as e:
                sickrage.app.log.warning("Unable to run synoindex: {}".format(e))

    def deleteFolder(self, cur_path):
        self.makeObject('-D', cur_path)

    def addFolder(self, cur_path):
        self.makeObject('-A', cur_path)

    def deleteFile(self, cur_file):
        self.makeObject('-d', cur_file)

    def addFile(self, cur_file):
        self.makeObject('-a', cur_file)

    def makeObject(self, cmd_arg, cur_path):
        if sickrage.app.config.synology.enable_index:
            synoindex_cmd = ['/usr/syno/bin/synoindex', cmd_arg, os.path.abspath(cur_path)]
            sickrage.app.log.debug("Executing command " + str(synoindex_cmd))
            sickrage.app.log.debug("Absolute path to command: " + os.path.abspath(synoindex_cmd[0]))
            try:
                p = subprocess.Popen(synoindex_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     cwd=sickrage.PROG_DIR)
                out, err = p.communicate()
                sickrage.app.log.debug("Script result: " + str(out))
            except OSError as e:
                sickrage.app.log.warning("Unable to run synoindex: {}".format(e))
