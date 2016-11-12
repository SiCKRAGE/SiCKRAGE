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

import datetime
import threading

import sickrage
from sickrage.core.common import Quality, DOWNLOADED, SNATCHED, SNATCHED_PROPER, WANTED
from sickrage.core.queues.search import BacklogQueueItem
from sickrage.core.ui import ProgressIndicator


class srBacklogSearcher(object):
    def __init__(self, *args, **kwargs):
        self.name = "BACKLOG"
        self.lock = threading.Lock()
        self._lastBacklog = None
        self.cycleTime = 21 / 60 / 24
        self.amActive = False
        self.amPaused = False
        self.amWaiting = False
        self._resetPI()

    def run(self, force=False):
        if self.amActive:
            return

        # set thread name
        threading.currentThread().setName(self.name)

        # set cycle time
        self.cycleTime = sickrage.srCore.srConfig.BACKLOG_SEARCHER_FREQ / 60 / 24

        try:
            self.searchBacklog()
        finally:
            self.amActive = False

    def forceSearch(self):
        self._set_lastBacklog(1)
        self.lastRun = datetime.datetime.fromordinal(1)

    def nextRun(self):
        if self._lastBacklog <= 1:
            return datetime.date.today()
        else:
            return datetime.date.fromordinal(self._lastBacklog + self.cycleTime)

    def _resetPI(self):
        self.percentDone = 0
        self.currentSearchInfo = {'title': 'Initializing'}

    def getProgressIndicator(self):
        if self.amActive:
            return ProgressIndicator(self.percentDone, self.currentSearchInfo)
        else:
            return None

    def am_running(self):
        sickrage.srCore.srLogger.debug("amWaiting: " + str(self.amWaiting) + ", amActive: " + str(self.amActive))
        return (not self.amWaiting) and self.amActive

    def searchBacklog(self, which_shows=None):

        if self.amActive:
            sickrage.srCore.srLogger.debug("Backlog is still running, not starting it again")
            return

        self.amActive = True
        self.amPaused = False

        if which_shows:
            show_list = which_shows
        else:
            show_list = sickrage.srCore.SHOWLIST

        self._lastBacklog = self._get_lastBacklog()

        curDate = datetime.date.today().toordinal()
        fromDate = datetime.date.fromordinal(1)

        if not which_shows and not ((curDate - self._lastBacklog) >= self.cycleTime):
            sickrage.srCore.srLogger.info(
                "Running limited backlog on missed episodes " + str(
                    sickrage.srCore.srConfig.BACKLOG_DAYS) + " day(s) and older only")
            fromDate = datetime.date.today() - datetime.timedelta(days=sickrage.srCore.srConfig.BACKLOG_DAYS)

        # go through non air-by-date shows and see if they need any episodes
        for curShow in show_list:

            if curShow.paused:
                continue

            segments = self._get_segments(curShow, fromDate)

            for season, segment in segments.items():
                self.currentSearchInfo = {'title': curShow.name + " Season " + str(season)}
                sickrage.srCore.SEARCHQUEUE.put(BacklogQueueItem(curShow, segment))  # @UndefinedVariable
            else:
                sickrage.srCore.srLogger.debug(
                    "Nothing needs to be downloaded for {show_name}, skipping".format(show_name=curShow.name))

        # don't consider this an actual backlog search if we only did recent eps
        # or if we only did certain shows
        if fromDate == datetime.date.fromordinal(1) and not which_shows:
            self._set_lastBacklog(curDate)

        self.amActive = False
        self._resetPI()

    def _get_lastBacklog(self):

        sickrage.srCore.srLogger.debug("Retrieving the last check time from the DB")

        dbData = [x['doc'] for x in sickrage.srCore.mainDB.db.all('info', with_doc=True)]

        if len(dbData) == 0:
            lastBacklog = 1
        elif dbData[0]["last_backlog"] is None or dbData[0]["last_backlog"] == "":
            lastBacklog = 1
        else:
            lastBacklog = int(dbData[0]["last_backlog"])
            if lastBacklog > datetime.date.today().toordinal():
                lastBacklog = 1

        return lastBacklog

    def _get_segments(self, show, fromDate):
        if show.paused:
            sickrage.srCore.srLogger.debug(
                "Skipping backlog for {show_name} because the show is paused".format(show_name=show.name))
            return {}

        anyQualities, bestQualities = Quality.splitQuality(show.quality)  # @UnusedVariable

        sickrage.srCore.srLogger.debug("Seeing if we need anything from {}".format(show.name))

        # check through the list of statuses to see if we want any
        wanted = {}
        for result in [x['doc'] for x in sickrage.srCore.mainDB.db.get_many('tv_episodes', show.indexerid, with_doc=True)
                       if x['doc']['season'] > 0 and x['doc']['airdate'] > fromDate.toordinal()]:
            curCompositeStatus = int(result["status"] or -1)
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
                epObj = show.getEpisode(int(result["season"]), int(result["episode"]))

                # only fetch if not archive on first match, or if show is lowest than the lower expected quality
                if (epObj.show.archive_firstmatch == 0 or curQuality < lowestBestQuality):
                    if epObj.season not in wanted:
                        wanted[epObj.season] = [epObj]
                    else:
                        wanted[epObj.season].append(epObj)

        return wanted

    @classmethod
    def _set_lastBacklog(self, when):

        sickrage.srCore.srLogger.debug("Setting the last backlog in the DB to " + str(when))

        dbData = [x['doc'] for x in sickrage.srCore.mainDB.db.all('info', with_doc=True)]
        if len(dbData) == 0:
            sickrage.srCore.mainDB.db.insert({
                '_t': 'info',
                'last_backlog': str(when),
                'last_indexer': 0
            })
        else:
            dbData[0]['last_backlog'] = str(when)
            sickrage.srCore.mainDB.db.update(dbData[0])


def get_backlog_cycle_time():
    cycletime = sickrage.srCore.srConfig.DAILY_SEARCHER_FREQ * 4
    return max([cycletime, 30])
