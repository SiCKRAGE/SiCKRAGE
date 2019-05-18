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
from sickrage.core.common import UNAIRED, SKIPPED, statusStrings
from sickrage.core.tv.episode import TVEpisode
from sickrage.core.databases.main import MainDB


@MainDB.with_session
def new_episode_finder(session=None):
    cur_date = datetime.date.today()
    cur_date += datetime.timedelta(days=1)
    cur_time = datetime.datetime.now(sickrage.app.tz)

    for episode_object in session.query(TVEpisode).filter_by(status=UNAIRED).filter(TVEpisode.season > 0, TVEpisode.airdate > datetime.date.min):
        if episode_object.show.paused:
            continue

        air_date = episode_object.airdate
        air_date += datetime.timedelta(days=episode_object.show.search_delay)
        if not cur_date >= air_date:
            continue

        if episode_object.show.airs and episode_object.show.network:
            # This is how you assure it is always converted to local time
            air_time = sickrage.app.tz_updater.parse_date_time(episode_object.airdate,
                                                               episode_object.show.airs,
                                                               episode_object.show.network).astimezone(sickrage.app.tz)

            # filter out any episodes that haven't started airing yet,
            # but set them to the default status while they are airing
            # so they are snatched faster
            if air_time > cur_time:
                continue

        episode_object.status = episode_object.show.default_ep_status if episode_object.season > 0 else SKIPPED
        sickrage.app.log.info('Setting status ({status}) for show airing today: {name} {special}'.format(
            name=episode_object.pretty_name(),
            status=statusStrings[episode_object.status],
            special='(specials are not supported)' if not episode_object.season > 0 else '',
        ))
