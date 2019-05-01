# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
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

from sqlalchemy import orm

import sickrage
from sickrage.core.common import Quality, DOWNLOADED, SNATCHED, SNATCHED_PROPER, WANTED
from sickrage.core.databases.main import MainDB
from sickrage.core.queues.search import BacklogQueueItem
from sickrage.core.searchers import new_episode_finder
from sickrage.core.tv.show.helpers import find_show, get_show_list


class BacklogSearcher(object):
    def __init__(self, *args, **kwargs):
        self.name = "BACKLOG"
        self.lock = threading.Lock()
        self.cycleTime = 21 / 60 / 24
        self.amActive = False
        self.amPaused = False
        self.amWaiting = False
        self.forced = False

    def run(self, force=False):
        if self.amActive or sickrage.app.developer and not force:
            return

        # set thread name
        threading.currentThread().setName(self.name)

        # set cycle time
        self.cycleTime = sickrage.app.config.backlog_searcher_freq / 60 / 24

        try:
            self.forced = force
            self.search_backlog()
        finally:
            self.amActive = False

    def am_running(self):
        sickrage.app.log.debug("amWaiting: " + str(self.amWaiting) + ", amActive: " + str(self.amActive))
        return (not self.amWaiting) and self.amActive

    def search_backlog(self, which_shows=None):
        if self.amActive:
            sickrage.app.log.debug("Backlog is still running, not starting it again")
            return

        self.amActive = True
        self.amPaused = False

        show_list = which_shows or get_show_list()
        cur_date = datetime.date.today().toordinal()
        from_date = datetime.date.fromordinal(1)

        if not which_shows and self.forced:
            sickrage.app.log.info("Running limited backlog on missed episodes " + str(
                sickrage.app.config.backlog_days) + " day(s) old")
            from_date = datetime.date.today() - datetime.timedelta(days=sickrage.app.config.backlog_days)
        else:
            sickrage.app.log.info('Running full backlog search on missed episodes for selected shows')

        # go through non air-by-date shows and see if they need any episodes
        for curShow in show_list:
            if curShow.paused:
                sickrage.app.log.debug("Skipping search for {} because the show is paused".format(curShow.name))
                continue

            episode_ids = self._get_episode_ids(curShow, from_date)
            if episode_ids:
                sickrage.app.io_loop.add_callback(sickrage.app.search_queue.put, BacklogQueueItem(curShow.indexer_id,
                                                                                                  episode_ids))
            else:
                sickrage.app.log.debug("Nothing needs to be downloaded for {}, skipping".format(curShow.name))

            # don't consider this an actual backlog search if we only did recent eps
            # or if we only did certain shows
            if from_date == datetime.date.fromordinal(1) and not which_shows:
                self._set_last_backlog_search(curShow, cur_date)

        self.amActive = False

    @staticmethod
    def _get_episode_ids(show, from_date):
        any_qualities, best_qualities = Quality.split_quality(show.quality)

        sickrage.app.log.debug("Seeing if we need anything that's older then today from {}".format(show.name))

        # check through the list of statuses to see if we want any
        wanted = []
        for ep_obj in show.episodes:
            if not ep_obj.season > 0 or not datetime.date.today().toordinal() > ep_obj.airdate > from_date.toordinal():
                continue

            cur_status, cur_quality = Quality.split_composite_status(int(ep_obj.status or -1))

            # if we need a better one then say yes
            if cur_status not in {WANTED, DOWNLOADED, SNATCHED, SNATCHED_PROPER}:
                continue

            if cur_status != WANTED:
                if best_qualities:
                    if cur_quality in best_qualities:
                        continue
                    elif cur_quality != Quality.UNKNOWN and cur_quality > max(best_qualities):
                        continue
                else:
                    if cur_quality in any_qualities:
                        continue
                    elif cur_quality != Quality.UNKNOWN and cur_quality > max(any_qualities):
                        continue

            # skip upgrading quality of downloaded episodes if enabled
            if cur_status == DOWNLOADED and show.skip_downloaded:
                continue

            wanted.append(ep_obj.indexer_id)

        return wanted

    @staticmethod
    def _get_last_backlog_search(show):
        sickrage.app.log.debug("Retrieving the last check time from the DB")

        try:
            return int(show.last_backlog_search)
        except orm.exc.NoResultFound:
            return 1

    @staticmethod
    def _set_last_backlog_search(show, when):
        sickrage.app.log.debug("Setting the last backlog in the DB to {}".format(when))

        try:
            show.last_backlog_search = when
        except orm.exc.NoResultFound:
            pass
