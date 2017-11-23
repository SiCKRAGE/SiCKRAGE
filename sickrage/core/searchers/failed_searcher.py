# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
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
from sickrage.core import findCertainShow
from sickrage.core.common import Quality
from sickrage.core.queues.search import FailedQueueItem
from sickrage.core.tv.episode import TVEpisode
from sickrage.core.tv.show.history import FailedHistory, History


class FailedSearcher(object):
    def __init__(self):
        self.name = "FAILEDSEARCHER"
        self.lock = threading.Lock()
        self.amActive = False

    def run(self, force=False):
        return

        """
        Runs the daily searcher, queuing selected episodes for search
        :param force: Force search
        """
        if self.amActive or sickrage.app.developer and not force:
            return

        self.amActive = True

        # set thread name
        threading.currentThread().setName(self.name)

        # trim failed download history
        if sickrage.app.config.use_failed_downloads:
            FailedHistory.trimHistory()

        sickrage.app.log.info("Searching for failed snatches")

        curDate = datetime.datetime.now()
        curDate += datetime.timedelta(hours=1)

        show = None

        episodes = [x['doc'] for x in sickrage.app.main_db.db.all('history', with_doc=True)
                    if x['doc']['action'] in Quality.SNATCHED + Quality.SNATCHED_BEST + Quality.SNATCHED_PROPER
                    and curDate.strftime(History.date_format) >= x['doc']['date'] > 1]

        failed_snatches = False
        for episode in episodes:
            failed_snatches = True
            if not show or int(episode["showid"]) != show.indexerid:
                show = findCertainShow(sickrage.app.showlist, int(episode["showid"]))

            ep_obj = show.getEpisode(int(episode['season']), int(episode['episode']))
            if isinstance(ep_obj, TVEpisode):
                # put it on the queue
                sickrage.app.search_queue.put(FailedQueueItem(show, [ep_obj], True))

        if not failed_snatches:
            sickrage.app.log.info("No failed snatches found")

        self.amActive = False
