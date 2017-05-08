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

import threading

import sickrage
from sickrage.core.queues.search import DailySearchQueueItem
from sickrage.core.tv.show.history import FailedHistory


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
        if self.amActive or sickrage.DEVELOPER and not force:
            return

        self.amActive = True

        # set thread name
        threading.currentThread().setName(self.name)

        # trim failed download history
        if sickrage.srCore.srConfig.USE_FAILED_DOWNLOADS:
            FailedHistory.trimHistory()

        # queue episode for daily search
        sickrage.srCore.SEARCHQUEUE.put(DailySearchQueueItem())

        self.amActive = False
