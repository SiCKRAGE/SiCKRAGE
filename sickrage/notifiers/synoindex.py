# Author: Sebastien Erard <sebastien_erard@hotmail.com>
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import os
import subprocess

import sickrage
from sickrage.notifiers import srNotifiers


class synoIndexNotifier(srNotifiers):
    def _notify_snatch(self, ep_name):
        pass

    def _notify_download(self, ep_name):
        pass

    def _notify_subtitle_download(self, ep_name, lang):
        pass

    def _notify_version_update(self, new_version):
        pass

    def moveFolder(self, old_path, new_path):
        self.moveObject(old_path, new_path)

    def moveFile(self, old_file, new_file):
        self.moveObject(old_file, new_file)

    def moveObject(self, old_path, new_path):
        if sickrage.srCore.srConfig.USE_SYNOINDEX:
            synoindex_cmd = ['/usr/syno/bin/synoindex', '-N', os.path.abspath(new_path),
                             os.path.abspath(old_path)]
            sickrage.srCore.srLogger.debug("Executing command " + str(synoindex_cmd))
            sickrage.srCore.srLogger.debug("Absolute path to command: " + os.path.abspath(synoindex_cmd[0]))
            try:
                p = subprocess.Popen(synoindex_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     cwd=sickrage.PROG_DIR)
                out, err = p.communicate()  # @UnusedVariable
                sickrage.srCore.srLogger.debug("Script result: " + str(out))
            except OSError as e:
                sickrage.srCore.srLogger.error("Unable to run synoindex: {}".format(e.message))

    def deleteFolder(self, cur_path):
        self.makeObject('-D', cur_path)

    def addFolder(self, cur_path):
        self.makeObject('-A', cur_path)

    def deleteFile(self, cur_file):
        self.makeObject('-d', cur_file)

    def addFile(self, cur_file):
        self.makeObject('-a', cur_file)

    def makeObject(self, cmd_arg, cur_path):
        if sickrage.srCore.srConfig.USE_SYNOINDEX:
            synoindex_cmd = ['/usr/syno/bin/synoindex', cmd_arg, os.path.abspath(cur_path)]
            sickrage.srCore.srLogger.debug("Executing command " + str(synoindex_cmd))
            sickrage.srCore.srLogger.debug("Absolute path to command: " + os.path.abspath(synoindex_cmd[0]))
            try:
                p = subprocess.Popen(synoindex_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     cwd=sickrage.PROG_DIR)
                out, err = p.communicate()  # @UnusedVariable
                sickrage.srCore.srLogger.debug("Script result: " + str(out))
            except OSError as e:
                sickrage.srCore.srLogger.error("Unable to run synoindex: {}".format(e.message))
