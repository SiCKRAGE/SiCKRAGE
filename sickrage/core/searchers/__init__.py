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

import sickrage
import sickrage.core.tv.show.helpers
from sickrage.core import helpers
from sickrage.core.common import UNAIRED, SKIPPED, statusStrings
from sickrage.core.databases.main import MainDB


def new_episode_finder():
    curDate = datetime.date.today()
    curDate += datetime.timedelta(days=1)
    curTime = datetime.datetime.now(sickrage.app.tz)

    show = None

    for episode in MainDB.TVEpisode.query.filter_by(status=UNAIRED).filter(MainDB.TVEpisode.season > 0,
                                                                 MainDB.TVEpisode.airdate > 1):

        if not show or int(episode.showid) != show.indexerid:
            show = sickrage.core.tv.show.helpers.find_show(int(episode.showid))

        # for when there is orphaned series in the database but not loaded into our showlist
        if not show or show.paused:
            continue

        air_date = datetime.date.fromordinal(episode.airdate)
        air_date += datetime.timedelta(days=show.search_delay)
        if not curDate.toordinal() >= air_date.toordinal():
            continue

        if show.airs and show.network:
            # This is how you assure it is always converted to local time
            air_time = sickrage.app.tz_updater.parse_date_time(episode.airdate,
                                                               show.airs, show.network).astimezone(sickrage.app.tz)

            # filter out any episodes that haven't started airing yet,
            # but set them to the default status while they are airing
            # so they are snatched faster
            if air_time > curTime:
                continue

        ep_obj = show.get_episode(int(episode.season), int(episode.episode))
        with ep_obj.lock:
            ep_obj.status = show.default_ep_status if ep_obj.season else SKIPPED
            sickrage.app.log.info('Setting status ({status}) for show airing today: {name} {special}'.format(
                name=ep_obj.pretty_name(),
                status=statusStrings[ep_obj.status],
                special='(specials are not supported)' if not ep_obj.season else '',
            ))

            ep_obj.save_to_db()
