# Author: echel0n <echel0n@sickrage.ca>
# URL: http://github.com/SiCKRAGETV/SickRage/
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

import sickrage
from sickrage.core.databases import cache_db
from sickrage.core.exceptions import CantRefreshShowException, \
    CantUpdateShowException
from sickrage.core.tv.show.history import FailedHistory
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

        sqlResult = cache_db.CacheDB().select('SELECT `time` FROM lastUpdate WHERE provider = ?', ['theTVDB'])
        if sqlResult:
            last_update = sqlResult[0]['time']
        else:
            last_update = time.mktime(datetime.datetime.min.timetuple())
            cache_db.CacheDB().action('INSERT INTO lastUpdate (provider, `time`) VALUES (?, ?)',
                                      ['theTVDB', long(last_update)])

        if sickrage.srCore.srConfig.USE_FAILED_DOWNLOADS:
            FailedHistory.trimHistory()

        # get indexer updated show ids
        updated_shows = srIndexerApi(1).indexer(**srIndexerApi(1).api_params.copy()).updated(long(last_update))

        # start update process
        piList = []
        for curShow in sickrage.srCore.SHOWLIST:
            try:
                curShow.nextEpisode()
                if curShow.indexerid in set(d["id"] for d in updated_shows or {}):
                    piList.append(sickrage.srCore.SHOWQUEUE.updateShow(curShow, True))
                else:
                    piList.append(sickrage.srCore.SHOWQUEUE.refreshShow(curShow, False))
            except (CantUpdateShowException, CantRefreshShowException) as e:
                continue

        ProgressIndicators.setIndicator('dailyShowUpdates', QueueProgressIndicator("Daily Show Updates", piList))

        cache_db.CacheDB().action('UPDATE lastUpdate SET `time` = ? WHERE provider=?',
                                  [long(update_timestamp), 'theTVDB'])

        self.amActive = False
