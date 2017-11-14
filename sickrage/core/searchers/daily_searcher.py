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
from sickrage.core import findCertainShow, common
from sickrage.core.queues.search import DailySearchQueueItem
from sickrage.core.tv.show.history import FailedHistory
from sickrage.core.updaters import tz_updater


class DailySearcher(object):
    def __init__(self):
        self.name = "DAILYSEARCHER"
        self.lock = threading.Lock()
        self.amActive = False

    def run(self, force=False):
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

        sickrage.app.log.info("Searching for new released episodes")

        curDate = datetime.date.today()
        curDate += datetime.timedelta(days=2)
        if tz_updater.load_network_dict():
            curDate += datetime.timedelta(days=1)

        curTime = datetime.datetime.now(sickrage.app.tz)

        show = None

        episodes = [x['doc'] for x in sickrage.app.main_db.db.all('tv_episodes', with_doc=True)
                    if x['doc']['status'] == common.UNAIRED
                    and x['doc']['season'] > 0
                    and curDate.toordinal() >= x['doc']['airdate'] > 1]

        new_episodes = False
        for episode in episodes:
            if not show or int(episode["showid"]) != show.indexerid:
                show = findCertainShow(sickrage.app.showlist, int(episode["showid"]))

            # for when there is orphaned series in the database but not loaded into our showlist
            if not show or show.paused:
                continue

            if show.airs and show.network:
                # This is how you assure it is always converted to local time
                air_time = tz_updater.parse_date_time(
                    episode['airdate'], show.airs, show.network, dateOnly=True
                ).astimezone(sickrage.app.tz)

                # filter out any episodes that haven't started airing yet,
                # but set them to the default status while they are airing
                # so they are snatched faster
                if air_time > curTime: continue

            ep_obj = show.getEpisode(int(episode['season']), int(episode['episode']))
            with ep_obj.lock:
                ep_obj.status = show.default_ep_status if ep_obj.season else common.SKIPPED
                sickrage.app.log.info('Setting status ({status}) for show airing today: {name} {special}'.format(
                    name=ep_obj.pretty_name(),
                    status=common.statusStrings[ep_obj.status],
                    special='(specials are not supported)' if not ep_obj.season else '',
                ))

                ep_obj.saveToDB()
                new_episodes = True

        if not new_episodes:
            sickrage.app.log.info("No new released episodes found")

        # queue episode for daily search
        sickrage.app.search_queue.put(DailySearchQueueItem())

        self.amActive = False
