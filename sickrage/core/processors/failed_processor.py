

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

from __future__ import print_function, unicode_literals

import sickrage
from sickrage.core.exceptions import FailedPostProcessingFailedException
from sickrage.core.helpers import show_names
from sickrage.core.nameparser import InvalidNameException, InvalidShowException, \
    NameParser
from sickrage.core.queues.search import FailedQueueItem


class FailedProcessor(object):
    """Take appropriate action when a download fails to complete"""

    def __init__(self, dirName, nzbName):
        """
        :param dirName: Full path to the folder of the failed download
        :param nzbName: Full name of the nzb file that failed
        """
        self.dir_name = dirName
        self.nzb_name = nzbName

        self.log = ""

    def process(self):
        """
        Do the actual work

        :return: True
        """
        self._log("Failed download detected: (" + str(self.nzb_name) + ", " + str(self.dir_name) + ")")

        releaseName = show_names.determineReleaseName(self.dir_name, self.nzb_name)
        if releaseName is None:
            self._log("Warning: unable to find a valid release name.", sickrage.srCore.srLogger.WARNING)
            raise FailedPostProcessingFailedException()

        try:
            parser = NameParser(False)
            parsed = parser.parse(releaseName)
        except InvalidNameException:
            self._log("Error: release name is invalid: " + releaseName, sickrage.srCore.srLogger.DEBUG)
            raise FailedPostProcessingFailedException()
        except InvalidShowException:
            self._log("Error: unable to parse release name " + releaseName + " into a valid show",
                      sickrage.srCore.srLogger.DEBUG)
            raise FailedPostProcessingFailedException()

        sickrage.srCore.srLogger.debug("name_parser info: ")
        sickrage.srCore.srLogger.debug(" - " + str(parsed.series_name))
        sickrage.srCore.srLogger.debug(" - " + str(parsed.season_number))
        sickrage.srCore.srLogger.debug(" - " + str(parsed.episode_numbers))
        sickrage.srCore.srLogger.debug(" - " + str(parsed.extra_info))
        sickrage.srCore.srLogger.debug(" - " + str(parsed.release_group))
        sickrage.srCore.srLogger.debug(" - " + str(parsed.air_date))

        for episode in parsed.episode_numbers:
            sickrage.srCore.SEARCHQUEUE.put(
                FailedQueueItem(parsed.show, [parsed.show.getEpisode(parsed.season_number, episode)]))

        return True

    def _log(self, message, level=None):
        """Log to regular logfile and save for return for PP script log"""
        sickrage.srCore.srLogger.log(level or sickrage.srCore.srLogger.INFO, message)
        self.log += message + "\n"
