# ##############################################################################
#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#  -
#  This file is part of SiCKRAGE.
#  -
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  -
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
# ##############################################################################


import threading

import sickrage


class AutoPostProcessor(object):
    def __init__(self):
        self.name = "POSTPROCESSOR"
        self.lock = threading.Lock()
        self.amActive = False

    def run(self, force=False):
        """
        Runs the postprocessor
        :param force: Forces postprocessing run (reserved for future use)
        :return: Returns when done without a return state/code
        """

        if self.amActive or (not sickrage.app.config.process_automatically) and not force:
            return

        self.amActive = True

        sickrage.app.io_loop.add_callback(sickrage.app.postprocessor_queue.put, sickrage.app.config.tv_download_dir, force=force)

        self.amActive = False
