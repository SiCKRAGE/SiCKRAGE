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
from sickrage.core.common import Quality, EpisodeStatus
from sickrage.core.databases.main import MainDB
from sickrage.core.helpers import flatten
from sickrage.core.queues.search import FailedSearchTask
from sickrage.core.tv.show.helpers import find_show
from sickrage.core.tv.show.history import FailedHistory


class FailedSnatchSearcher(object):
    def __init__(self):
        self.name = "FAILEDSNATCHSEARCHER"
        self.lock = threading.Lock()
        self.running = False

    def task(self, force=False):
        """
        Runs the failed searcher, queuing selected episodes for search that have failed to snatch
        :param force: Force search
        """
        if self.running or not sickrage.app.config.failed_snatches.enable and not force:
            return

        try:
            self.running = True

            # set thread name
            threading.currentThread().setName(self.name)

            # trim failed download history
            FailedHistory.trim_history()

            sickrage.app.log.info("Searching for failed snatches")

            failed_snatches = False

            for snatched_episode_obj in [x for x in self.snatched_episodes() if (x.series_id, x.season, x.episode) not in self.downloaded_releases()]:
                show_object = find_show(snatched_episode_obj.series_id, snatched_episode_obj.series_provider_id)
                episode_object = show_object.get_episode(snatched_episode_obj.season, snatched_episode_obj.episode)
                if episode_object.show.paused:
                    continue

                cur_status, cur_quality = Quality.split_composite_status(episode_object.status)
                if cur_status not in {EpisodeStatus.SNATCHED, EpisodeStatus.SNATCHED_BEST, EpisodeStatus.SNATCHED_PROPER}:
                    continue

                sickrage.app.search_queue.put(FailedSearchTask(show_object.series_id,
                                                               show_object.series_provider_id,
                                                               episode_object.season,
                                                               episode_object.episode,
                                                               True))

                failed_snatches = True

            if not failed_snatches:
                sickrage.app.log.info("No failed snatches found")
        finally:
            self.running = False

    def snatched_episodes(self):
        session = sickrage.app.main_db.session()
        return (x for x in
                session.query(MainDB.History).filter(MainDB.History.action.in_(flatten(
                    [EpisodeStatus.composites(EpisodeStatus.SNATCHED), EpisodeStatus.composites(EpisodeStatus.SNATCHED_BEST),
                     EpisodeStatus.composites(EpisodeStatus.SNATCHED_PROPER)]))) if
                24 >= (datetime.datetime.now() - x.date).days >= sickrage.app.config.failed_snatches.age)

    def downloaded_releases(self):
        session = sickrage.app.main_db.session()
        return ((x.series_id, x.season, x.episode) for x in
                session.query(MainDB.History).filter(MainDB.History.action.in_(EpisodeStatus.composites(EpisodeStatus.DOWNLOADED))))
