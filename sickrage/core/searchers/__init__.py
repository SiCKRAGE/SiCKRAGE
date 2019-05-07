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

    for episode in session.query(TVEpisode).filter_by(status=UNAIRED).filter(TVEpisode.season > 0, TVEpisode.airdate > datetime.date.min):
        if episode.show.paused:
            continue

        air_date = episode.airdate
        air_date += datetime.timedelta(days=episode.show.search_delay)
        if not cur_date >= air_date:
            continue

        if episode.show.airs and episode.show.network:
            # This is how you assure it is always converted to local time
            air_time = sickrage.app.tz_updater.parse_date_time(episode.airdate,
                                                               episode.show.airs,
                                                               episode.show.network).astimezone(sickrage.app.tz)

            # filter out any episodes that haven't started airing yet,
            # but set them to the default status while they are airing
            # so they are snatched faster
            if air_time > cur_time:
                continue

        episode.status = episode.show.default_ep_status if episode.ep_obj.season > 0 else SKIPPED
        sickrage.app.log.info('Setting status ({status}) for show airing today: {name} {special}'.format(
            name=episode.pretty_name(),
            status=statusStrings[episode.status],
            special='(specials are not supported)' if not episode.season > 0 else '',
        ))
