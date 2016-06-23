# Author: echel0n <echel0n@sickrage.ca>
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
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import datetime
import threading

import sickrage
from sickrage.core.common import UNAIRED, SKIPPED, statusStrings, WANTED
from sickrage.core.databases import main_db
from sickrage.core.exceptions import MultipleShowObjectsException
from sickrage.core.helpers import findCertainShow
from sickrage.core.queues.search import DailySearchQueueItem
from sickrage.core.tv.show.history import FailedHistory
from sickrage.core.updaters import tz_updater


class srDailySearcher(object):
    def __init__(self, *args, **kwargs):
        self.name = "DAILYSEARCHER"
        self.lock = threading.Lock()
        self.amActive = False

    def run(self, force=False):
        """
        Runs the daily searcher, queuing selected episodes for search
        :param force: Force search
        """
        if self.amActive:
            return

        self.amActive = True

        # set thread name
        threading.currentThread().setName(self.name)


        # trim failed download history
        if sickrage.srCore.srConfig.USE_FAILED_DOWNLOADS:
            FailedHistory.trimHistory()

        sickrage.srCore.srLogger.info("Searching for new released episodes ...")

        curDate = (datetime.date.today() + datetime.timedelta(days=2)).toordinal()
        if tz_updater.load_network_dict():
            curDate = (datetime.date.today() + datetime.timedelta(days=1)).toordinal()

        curTime = datetime.datetime.now(tz_updater.sr_timezone)
        sqlResults = main_db.MainDB().select(
            "SELECT * FROM tv_episodes WHERE status in (?,?) AND season > 0 AND (airdate <= ? AND airdate > 1)",
            [UNAIRED, WANTED, curDate])

        show = None
        sql_l = []
        for sqlEp in sqlResults:
            try:
                if not show or int(sqlEp["showid"]) != show.indexerid:
                    show = findCertainShow(sickrage.srCore.SHOWLIST, int(sqlEp["showid"]))

                # for when there is orphaned series in the database but not loaded into our showlist
                if not show or show.paused:
                    continue

            except MultipleShowObjectsException:
                sickrage.srCore.srLogger.info("ERROR: expected to find a single show matching " + str(sqlEp['showid']))
                continue

            if show.airs and show.network:
                # This is how you assure it is always converted to local time
                air_time = tz_updater.parse_date_time(sqlEp['airdate'], show.airs, show.network, dateOnly=True).astimezone(tz_updater.sr_timezone)

                # filter out any episodes that haven't started airing yet,
                # but set them to the default status while they are airing
                # so they are snatched faster
                if air_time > curTime:
                    continue

            ep = show.getEpisode(int(sqlEp["season"]), int(sqlEp["episode"]))
            with ep.lock:
                if ep.season == 0:
                    sickrage.srCore.srLogger.info(
                        "New episode " + ep.prettyName() + " airs today, setting status to SKIPPED because is a special season")
                    ep.status = SKIPPED
                else:
                    sickrage.srCore.srLogger.info("New episode %s airs today, setting to default episode status for this show: %s" % (
                        ep.prettyName(), statusStrings[ep.show.default_ep_status]))
                    ep.status = ep.show.default_ep_status

                sql_q = ep.saveToDB(False)
                if sql_q:
                    sql_l.append(sql_q)

        if len(sql_l) > 0:
            main_db.MainDB().mass_upsert(sql_l)
            del sql_l
        else:
            sickrage.srCore.srLogger.info("No new released episodes found ...")

        # queue episode for daily search
        sickrage.srCore.SEARCHQUEUE.put(DailySearchQueueItem())

        self.amActive = False
