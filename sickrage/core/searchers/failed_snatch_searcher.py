# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import datetime
import threading

import sickrage
from sickrage.core import findCertainShow
from sickrage.core.common import Quality, SNATCHED, SNATCHED_BEST, SNATCHED_PROPER
from sickrage.core.databases.main import MainDB
from sickrage.core.queues.search import FailedQueueItem
from sickrage.core.tv.episode import TVEpisode
from sickrage.core.tv.show.history import FailedHistory, History


class FailedSnatchSearcher(object):
    def __init__(self):
        self.name = "FAILEDSNATCHSEARCHER"
        self.lock = threading.Lock()
        self.amActive = False

    def run(self, force=False):
        """
        Runs the failed searcher, queuing selected episodes for search that have failed to snatch
        :param force: Force search
        """
        if self.amActive or (not sickrage.app.config.use_failed_snatcher or sickrage.app.developer) and not force:
            return

        self.amActive = True

        # set thread name
        threading.currentThread().setName(self.name)

        # trim failed download history
        FailedHistory.trimHistory()

        sickrage.app.log.info("Searching for failed snatches")

        show = None
        failed_snatches = False

        snatched_episodes = (x for x in MainDB.History.query.filter(
            MainDB.History.action.in_(Quality.SNATCHED + Quality.SNATCHED_BEST + Quality.SNATCHED_PROPER),
            24 >= int((datetime.datetime.now() -
                       datetime.datetime.strptime(
                           MainDB.History.date,
                           History.date_format)).total_seconds() / 3600
                      ) >= sickrage.app.config.failed_snatch_age))

        downloaded_releases = ((x.showid, x.season, x.episode) for x in
                               MainDB.History.query.filter(MainDB.History.action.in_(Quality.DOWNLOADED)))

        episodes = [x for x in snatched_episodes if (x.showid, x.season, x.episode) not in downloaded_releases]

        for episode in episodes:
            failed_snatches = True
            if not show or int(episode.showid) != show.indexerid:
                show = findCertainShow(int(episode.showid))

            # for when there is orphaned series in the database but not loaded into our showlist
            if not show or show.paused:
                continue

            ep_obj = show.get_episode(int(episode.season), int(episode.episode))
            if isinstance(ep_obj, TVEpisode):
                curStatus, curQuality = Quality.split_composite_status(ep_obj.status)
                if curStatus not in {SNATCHED, SNATCHED_BEST, SNATCHED_PROPER}:
                    continue

                # put it on the queue
                sickrage.app.search_queue.put(FailedQueueItem(show, [ep_obj], True))

        if not failed_snatches:
            sickrage.app.log.info("No failed snatches found")

        self.amActive = False
