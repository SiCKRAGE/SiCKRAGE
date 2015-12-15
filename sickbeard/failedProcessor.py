# Author: Tyler Fenby <tylerfenby@gmail.com>
# URL: https://sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
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


import sickbeard
import logging
from sickbeard import show_name_helpers
from sickbeard import search_queue
from sickbeard.name_parser.parser import NameParser, InvalidNameException, InvalidShowException
from sickrage.helper.exceptions import FailedPostProcessingFailedException


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

        releaseName = show_name_helpers.determineReleaseName(self.dir_name, self.nzb_name)
        if releaseName is None:
            self._log("Warning: unable to find a valid release name.", logging.WARNING)
            raise FailedPostProcessingFailedException()

        try:
            parser = NameParser(False)
            parsed = parser.parse(releaseName)
        except InvalidNameException:
            self._log("Error: release name is invalid: " + releaseName, logging.DEBUG)
            raise FailedPostProcessingFailedException()
        except InvalidShowException:
            self._log("Error: unable to parse release name " + releaseName + " into a valid show", logging.DEBUG)
            raise FailedPostProcessingFailedException()

        logging.debug("name_parser info: ")
        logging.debug(" - " + str(parsed.series_name))
        logging.debug(" - " + str(parsed.season_number))
        logging.debug(" - " + str(parsed.episode_numbers))
        logging.debug(" - " + str(parsed.extra_info))
        logging.debug(" - " + str(parsed.release_group))
        logging.debug(" - " + str(parsed.air_date))

        for episode in parsed.episode_numbers:
            segment = parsed.show.getEpisode(parsed.season_number, episode)

            cur_failed_queue_item = search_queue.FailedQueueItem(parsed.show, [segment])
            sickbeard.searchQueueScheduler.action.add_item(cur_failed_queue_item)

        return True

    def _log(self, message, level=logging.INFO):
        """Log to regular logfile and save for return for PP script log"""
        logging.log(level, message)
        self.log += message + "\n"
