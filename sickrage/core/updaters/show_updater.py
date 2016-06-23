# Author: echel0n <echel0n@sickrage.ca>
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import datetime
import threading

import sickrage
from sickrage.core.databases import main_db
from sickrage.core.exceptions import CantRefreshShowException, \
    CantUpdateShowException
from sickrage.core.tv.show.history import FailedHistory
from sickrage.core.ui import ProgressIndicators, QueueProgressIndicator


class srShowUpdater(object):
    def __init__(self):
        self.name = "SHOWUPDATER"
        self.lock = threading.Lock()
        self.amActive = False

    def run(self, force=False):
        if self.amActive:
            return

        self.amActive = True

        # set thread name
        threading.currentThread().setName(self.name)

        piList = []
        stale_should_update = []

        update_datetime = datetime.datetime.now()
        update_date = update_datetime.date()

        if sickrage.srCore.srConfig.USE_FAILED_DOWNLOADS:
            FailedHistory.trimHistory()

        if sickrage.srCore.srConfig.SHOWUPDATE_STALE:
            # select 10 'Ended' tv_shows updated more than 90 days ago to include in this update
            stale_update_date = (update_date - datetime.timedelta(days=90)).toordinal()

            # last_update_date <= 90 days, sorted ASC because dates are ordinal
            sql_result = main_db.MainDB().select(
                    "SELECT indexer_id FROM tv_shows WHERE status = 'Ended' AND last_update_indexer <= ? ORDER BY last_update_indexer ASC LIMIT 10;",
                    [stale_update_date])

            # list of stale shows
            [stale_should_update.append(int(cur_result['indexer_id'])) for cur_result in sql_result]

        # start update process
        sickrage.srCore.srLogger.info("Performing daily updates for all shows")
        for curShow in sickrage.srCore.SHOWLIST:
            try:
                # get next episode airdate
                curShow.nextEpisode()

                # if should_update returns True (not 'Ended') or show is selected stale 'Ended' then update, otherwise just refresh
                if curShow.should_update(update_date=update_date) or curShow.indexerid in stale_should_update:
                    try:
                        piList.append(
                                sickrage.srCore.SHOWQUEUE.updateShow(curShow, True))
                    except CantUpdateShowException as e:
                        sickrage.srCore.srLogger.debug("Unable to update show: {}".format(e.message))
                else:
                    piList.append(
                            sickrage.srCore.SHOWQUEUE.refreshShow(curShow, True))

            except (CantUpdateShowException, CantRefreshShowException) as e:
                sickrage.srCore.srLogger.error("Daily show update failed: {}".format(e.message))

        ProgressIndicators.setIndicator('dailyShowUpdates', QueueProgressIndicator("Daily Show Updates", piList))

        sickrage.srCore.srLogger.info("Completed daily updates for all shows")

        self.amActive = False