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

from tornado.ioloop import IOLoop

import sickrage
from sickrage.core.tv.episode.helpers import find_episode
from sickrage.core.tv.show.helpers import find_show
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
        if self.amActive or not sickrage.app.config.use_failed_snatcher and not force:
            return

        self.amActive = True

        # set thread name
        threading.currentThread().setName(self.name)

        # trim failed download history
        FailedHistory.trim_history()

        sickrage.app.log.info("Searching for failed snatches")

        failed_snatches = False

        for snatched_episode_obj in [x for x in self.snatched_episodes() if
                                     (x.showid, x.episode_id) not in self.downloaded_releases()]:

            episode_obj = find_episode(snatched_episode_obj.showid, snatched_episode_obj.episode_id)
            if episode_obj.show.paused:
                continue

            cur_status, cur_quality = Quality.split_composite_status(episode_obj.status)
            if cur_status not in {SNATCHED, SNATCHED_BEST, SNATCHED_PROPER}:
                continue

            sickrage.app.io_loop.add_callback(sickrage.app.search_queue.put,
                                              FailedQueueItem(episode_obj.showid, [episode_obj.episode_id], True))

            failed_snatches = True

        if not failed_snatches:
            sickrage.app.log.info("No failed snatches found")

        self.amActive = False

    @MainDB.with_session
    def snatched_episodes(self, session=None):
        return (x for x in session.query(MainDB.History).filter(
            MainDB.History.action.in_(Quality.SNATCHED + Quality.SNATCHED_BEST + Quality.SNATCHED_PROPER),
            24 >= int((datetime.datetime.now() - datetime.datetime.strptime(MainDB.History.date,
                                                                            History.date_format)).total_seconds() / 3600) >= sickrage.app.config.failed_snatch_age))

    @MainDB.with_session
    def downloaded_releases(self, session=None):
        return ((x.showid, x.episode_id) for x in
                session.query(MainDB.History).filter(MainDB.History.action.in_(Quality.DOWNLOADED)))
