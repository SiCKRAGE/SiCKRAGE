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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import datetime
import threading
import time

from sqlalchemy import orm

import sickrage
from sickrage.core.databases.cache import CacheDB
from sickrage.core.enums import SeriesProviderID
from sickrage.core.exceptions import CantRefreshShowException, CantUpdateShowException
from sickrage.core.tv.show.helpers import get_show_list


class ShowUpdater(object):
    def __init__(self):
        self.name = "SHOWUPDATER"
        self.lock = threading.Lock()
        self.running = False

    def task(self, force=False):
        if self.running and not force:
            return

        try:
            self.running = True

            # set thread name
            threading.currentThread().setName(self.name)

            session = sickrage.app.cache_db.session()

            update_timestamp = int(time.mktime(datetime.datetime.now().timetuple()))

            try:
                dbData = session.query(CacheDB.LastUpdate).filter_by(provider='theTVDB').one()
                last_update = int(dbData.time)
            except orm.exc.NoResultFound:
                last_update = update_timestamp
                dbData = CacheDB.LastUpdate(**{
                    'provider': 'theTVDB',
                    'time': 0
                })
                session.add(dbData)
            finally:
                session.commit()

            # get list of updated series from a series provider
            updated_shows = set()
            for series_provider_id in SeriesProviderID:
                resp = sickrage.app.series_providers[series_provider_id].updated(last_update)
                if resp:
                    for series in resp:
                        updated_shows.add(series['id'])

            # start update process
            pi_list = []
            for show_obj in get_show_list():
                if show_obj.paused:
                    sickrage.app.log.info('Show update skipped, show: {} is paused.'.format(show_obj.name))
                    continue

                if show_obj.status == 'Ended':
                    if not sickrage.app.config.general.show_update_stale:
                        sickrage.app.log.info('Show update skipped, show: {} status is ended.'.format(show_obj.name))
                        continue
                    elif not (datetime.datetime.now() - show_obj.last_update).days >= 90:
                        sickrage.app.log.info('Show update skipped, show: {} status is ended and recently updated.'.format(show_obj.name))
                        continue

                try:
                    if show_obj.series_id in updated_shows:
                        pi_list.append(sickrage.app.show_queue.refresh_show(show_obj.series_id, show_obj.series_provider_id, force=False))
                    elif (datetime.datetime.now() - show_obj.last_update).days >= 7:
                        pi_list.append(sickrage.app.show_queue.update_show(show_obj.series_id, show_obj.series_provider_id, force=False))
                except (CantUpdateShowException, CantRefreshShowException) as e:
                    sickrage.app.log.debug("Automatic update failed: {}".format(e))

            # ProgressIndicators.setIndicator('dailyShowUpdates', QueueProgressIndicator("Daily Show Updates", pi_list))

            dbData.time = update_timestamp
            session.commit()
        finally:
            self.running = False
