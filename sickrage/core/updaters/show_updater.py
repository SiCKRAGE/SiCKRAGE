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
import threading
import time

from CodernityDB.database import RecordNotFound

import sickrage
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

        update_timestamp = long(time.mktime(datetime.datetime.now().timetuple()))

        try:
            dbData = sickrage.srCore.cacheDB.db.get('lastUpdate', 'theTVDB', with_doc=True)['doc']
            last_update = long(dbData['time'])
        except RecordNotFound:
            last_update = long(time.mktime(datetime.datetime.min.timetuple()))
            dbData = sickrage.srCore.cacheDB.db.insert({
                '_t': 'lastUpdate',
                'provider': 'theTVDB',
                'time': long(last_update)
            })

        # get indexer updated show ids
        updated_shows = set(d["id"] for d in
                            srIndexerApi().indexer(**srIndexerApi().api_params.copy()).updated(long(last_update)) or {})

        # start update process
        pi_list = []
        for curShow in sickrage.srCore.SHOWLIST:
            try:
                curShow.nextEpisode()

                if curShow.indexerid in updated_shows:
                    pi_list.append(sickrage.srCore.SHOWQUEUE.updateShow(curShow, True))
                else:
                    pi_list.append(sickrage.srCore.SHOWQUEUE.refreshShow(curShow, False))
            except (CantUpdateShowException, CantRefreshShowException) as e:
                sickrage.srCore.srLogger.debug("Automatic update failed: {}".format(e.message))

        ProgressIndicators.setIndicator('dailyShowUpdates', QueueProgressIndicator("Daily Show Updates", pi_list))

        dbData['time'] = long(update_timestamp)
        sickrage.srCore.cacheDB.db.update(dbData)

        self.amActive = False
