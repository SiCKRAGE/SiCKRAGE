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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import datetime
import os
import threading
import time

import sickrage
from CodernityDB.database import RecordNotFound
from sickrage.core.databases.cache import CacheDB
from sickrage.core.exceptions import CantRefreshShowException, CantUpdateShowException
from sickrage.core.ui import ProgressIndicators, QueueProgressIndicator
from sickrage.indexers import srIndexerApi


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

        update_timestamp = time.mktime(datetime.datetime.now().timetuple())

        try:
            dbData = CacheDB().db.get('lastUpdate', 'theTVDB', with_doc=True)['doc']
            last_update = dbData['time']
        except RecordNotFound:
            last_update = time.mktime(datetime.datetime.min.timetuple())
            dbData = CacheDB().db.insert({
                '_t': 'lastUpdate',
                'provider': 'theTVDB',
                'time': long(last_update)
            })

        # get indexer updated show ids
        updated_shows = srIndexerApi().indexer(**srIndexerApi().api_params.copy()).updated(long(last_update))

        # start update process
        piList = []
        for curShow in sickrage.srCore.SHOWLIST:
            try:
                curShow.nextEpisode()

                if not os.path.isdir(curShow.location):
                    continue

                if curShow.indexerid in set(d["id"] for d in updated_shows or {}):
                    piList.append(sickrage.srCore.SHOWQUEUE.updateShow(curShow, True))
                elif datetime.date.fromordinal(curShow.last_refresh) > datetime.timedelta(days=1):
                    piList.append(sickrage.srCore.SHOWQUEUE.refreshShow(curShow, False))
            except (CantUpdateShowException, CantRefreshShowException):
                continue

        ProgressIndicators.setIndicator('dailyShowUpdates', QueueProgressIndicator("Daily Show Updates", piList))

        dbData['time'] = long(update_timestamp)
        CacheDB().db.update(dbData)

        self.amActive = False
