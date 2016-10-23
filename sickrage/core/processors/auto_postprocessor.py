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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import os.path
import threading

import sickrage
from sickrage.core.process_tv import processDir


class srPostProcessor(object):
    def __init__(self, *args, **kwargs):
        self.name = "POSTPROCESSOR"
        self.lock = threading.Lock()
        self.amActive = False

    def run(self, force=False):
        """
        Runs the postprocessor
        :param force: Forces postprocessing run (reserved for future use)
        :return: Returns when done without a return state/code
        """

        if self.amActive:
            return

        self.amActive = True

        # set thread name
        threading.currentThread().setName(self.name)

        if not os.path.isdir(sickrage.srCore.srConfig.TV_DOWNLOAD_DIR):
            sickrage.srCore.srLogger.error("Automatic post-processing attempted but dir " + sickrage.srCore.srConfig.TV_DOWNLOAD_DIR + " doesn't exist")
            self.amActive = False
            return

        if not os.path.isabs(sickrage.srCore.srConfig.TV_DOWNLOAD_DIR):
            sickrage.srCore.srLogger.error(
                    "Automatic post-processing attempted but dir " + sickrage.srCore.srConfig.TV_DOWNLOAD_DIR + " is relative (and probably not what you really want to process)")
            self.amActive = False
            return

        processDir(sickrage.srCore.srConfig.TV_DOWNLOAD_DIR)

        self.amActive = False

    def __del__(self):
        pass
