# Author: echel0n <sickrage.tv@gmail.com>
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
from sickrage.core.common import UNAIRED, SKIPPED, statusStrings
from sickrage.core.databases import main_db
from sickrage.core.exceptions import MultipleShowObjectsException
from sickrage.core.helpers import findCertainShow
from sickrage.core.queues.search import DailySearchQueueItem
from sickrage.core.tv.show.history import FailedHistory
from sickrage.core.updaters import tz_updater


class DailySearcher(object):
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

        # trim failed download history
        if sickrage.USE_FAILED_DOWNLOADS:
            FailedHistory.trimHistory()

        sickrage.LOGGER.info("Searching for new released episodes ...")

        if tz_updater.network_dict:
            curDate = (datetime.date.today() + datetime.timedelta(days=1)).toordinal()
        else:
            curDate = (datetime.date.today() + datetime.timedelta(days=2)).toordinal()

        curTime = datetime.datetime.now(tz_updater.sr_timezone)

        sqlResults = main_db.MainDB().select(
                "SELECT * FROM tv_episodes WHERE status = ? AND season > 0 AND (airdate <= ? AND airdate > 1)",
                [UNAIRED, curDate])

        sql_l = []
        show = None

        for sqlEp in sqlResults:
            try:
                if not show or int(sqlEp[b"showid"]) != show.indexerid:
                    show = findCertainShow(sickrage.showList, int(sqlEp[b"showid"]))

                # for when there is orphaned series in the database but not loaded into our showlist
                if not show or show.paused:
                    continue

            except MultipleShowObjectsException:
                sickrage.LOGGER.info("ERROR: expected to find a single show matching " + str(sqlEp[b'showid']))
                continue

            if show.airs and show.network:
                # This is how you assure it is always converted to local time
                air_time = tz_updater.parse_date_time(sqlEp[b'airdate'], show.airs, show.network).astimezone(
                        tz_updater.sr_timezone)

                # filter out any episodes that haven't started airing yet,
                # but set them to the default status while they are airing
                # so they are snatched faster
                if air_time > curTime:
                    continue

            ep = show.getEpisode(int(sqlEp[b"season"]), int(sqlEp[b"episode"]))
            with ep.lock:
                if ep.season == 0:
                    sickrage.LOGGER.info(
                            "New episode " + ep.prettyName() + " airs today, setting status to SKIPPED because is a special season")
                    ep.status = SKIPPED
                else:
                    sickrage.LOGGER.info("New episode %s airs today, setting to default episode status for this show: %s" % (
                        ep.prettyName(), statusStrings[ep.show.default_ep_status]))
                    ep.status = ep.show.default_ep_status

                sql_l.append(ep.get_sql())

        if len(sql_l) > 0:
            main_db.MainDB().mass_action(sql_l)
        else:
            sickrage.LOGGER.info("No new released episodes found ...")

        # queue episode for daily search
        dailysearch_queue_item = DailySearchQueueItem()
        sickrage.SEARCHQUEUE.add_item(dailysearch_queue_item)

        self.amActive = False
