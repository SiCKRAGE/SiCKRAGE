# Author: echel0n <sickrage.tv@gmail.com>
# URL: http://github.com/SiCKRAGETV/SickRage/
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

import threading

from datetime import datetime, date, timedelta

import sickrage
from core.common import Quality, DOWNLOADED, SNATCHED, SNATCHED_PROPER, WANTED
from core.databases import main_db
from core.queues.search import BacklogQueueItem
from core.ui import ProgressIndicator


class srBacklogSearcher(object):
    def __init__(self, *args, **kwargs):
        self.name = "BACKLOG"
        self.lock = threading.Lock()
        self._lastBacklog = self._get_lastBacklog()
        self.cycleTime = sickrage.srConfig.BACKLOG_SEARCHER_FREQ / 60 / 24
        self.amActive = False
        self.amPaused = False
        self.amWaiting = False
        self._resetPI()

    def run(self, force=False):
        if self.amActive:
            return

        try:
            self.searchBacklog()
        finally:
            self.amActive = False

    def forceSearch(self):
        self._set_lastBacklog(1)
        self.lastRun = datetime.fromordinal(1)

    def nextRun(self):
        if self._lastBacklog <= 1:
            return date.today()
        else:
            return date.fromordinal(self._lastBacklog + self.cycleTime)

    def _resetPI(self):
        self.percentDone = 0
        self.currentSearchInfo = {'title': 'Initializing'}

    def getProgressIndicator(self):
        if self.amActive:
            return ProgressIndicator(self.percentDone, self.currentSearchInfo)
        else:
            return None

    def am_running(self):
        sickrage.srLogger.debug("amWaiting: " + str(self.amWaiting) + ", amActive: " + str(self.amActive))
        return (not self.amWaiting) and self.amActive

    def searchBacklog(self, which_shows=None):

        if self.amActive:
            sickrage.srLogger.debug("Backlog is still running, not starting it again")
            return

        self.amActive = True
        self.amPaused = False

        if which_shows:
            show_list = which_shows
        else:
            show_list = sickrage.srCore.SHOWLIST

        self._get_lastBacklog()

        curDate = date.today().toordinal()
        fromDate = date.fromordinal(1)

        if not which_shows and not ((curDate - self._lastBacklog) >= self.cycleTime):
            sickrage.srLogger.info(
                    "Running limited backlog on missed episodes " + str(
                            sickrage.srConfig.BACKLOG_DAYS) + " day(s) and older only")
            fromDate = date.today() - timedelta(days=sickrage.srConfig.BACKLOG_DAYS)

        # go through non air-by-date shows and see if they need any episodes
        for curShow in show_list:

            if curShow.paused:
                continue

            segments = self._get_segments(curShow, fromDate)

            for season, segment in segments.iteritems():
                self.currentSearchInfo = {'title': curShow.name + " Season " + str(season)}
                sickrage.srCore.SEARCHQUEUE.add_item(BacklogQueueItem(curShow, segment))  # @UndefinedVariable
            else:
                sickrage.srLogger.debug("Nothing needs to be downloaded for {show_name}, skipping".format(show_name=curShow.name))

        # don't consider this an actual backlog search if we only did recent eps
        # or if we only did certain shows
        if fromDate == date.fromordinal(1) and not which_shows:
            self._set_lastBacklog(curDate)

        self.amActive = False
        self._resetPI()

    def _get_lastBacklog(self):

        sickrage.srLogger.debug("Retrieving the last check time from the DB")

        sqlResults = main_db.MainDB().select("SELECT * FROM info")

        if len(sqlResults) == 0:
            lastBacklog = 1
        elif sqlResults[0][b"last_backlog"] is None or sqlResults[0][b"last_backlog"] == "":
            lastBacklog = 1
        else:
            lastBacklog = int(sqlResults[0][b"last_backlog"])
            if lastBacklog > date.today().toordinal():
                lastBacklog = 1

        self._lastBacklog = lastBacklog
        return self._lastBacklog

    def _get_segments(self, show, fromDate):
        if show.paused:
            sickrage.srLogger.debug("Skipping backlog for {show_name} because the show is paused".format(show_name=show.name))
            return {}

        anyQualities, bestQualities = Quality.splitQuality(show.quality)  # @UnusedVariable

        sickrage.srLogger.debug("Seeing if we need anything from {show_name}".format(show_name=show.name))

        sqlResults = main_db.MainDB().select(
            "SELECT status, season, episode FROM tv_episodes WHERE season > 0 AND airdate > ? AND showid = ?",
            [fromDate.toordinal(), show.indexerid])

        # check through the list of statuses to see if we want any
        wanted = {}
        for result in sqlResults:
            curCompositeStatus = int(result[b"status"] or -1)
            curStatus, curQuality = Quality.splitCompositeStatus(curCompositeStatus)

            if bestQualities:
                highestBestQuality = max(bestQualities)
                lowestBestQuality = min(bestQualities)
            else:
                highestBestQuality = 0
                lowestBestQuality = 0

            # if we need a better one then say yes
            if (curStatus in (DOWNLOADED, SNATCHED,
                              SNATCHED_PROPER) and curQuality < highestBestQuality) or curStatus == WANTED:
                epObj = show.getEpisode(int(result[b"season"]), int(result[b"episode"]))

                # only fetch if not archive on first match, or if show is lowest than the lower expected quality
                if (epObj.show.archive_firstmatch == 0 or curQuality < lowestBestQuality):
                    if epObj.season not in wanted:
                        wanted[epObj.season] = [epObj]
                    else:
                        wanted[epObj.season].append(epObj)

        return wanted

    @classmethod
    def _set_lastBacklog(self, when):

        sickrage.srLogger.debug("Setting the last backlog in the DB to " + str(when))

        sqlResults = main_db.MainDB().select("SELECT * FROM info")

        if len(sqlResults) == 0:
            main_db.MainDB().action("INSERT INTO info (last_backlog, last_indexer) VALUES (?,?)", [str(when), 0])
        else:
            main_db.MainDB().action("UPDATE info SET last_backlog=" + str(when))


def get_backlog_cycle_time():
    cycletime = sickrage.srConfig.DAILY_SEARCHER_FREQ * 2 + 7
    return max([cycletime, 720])
