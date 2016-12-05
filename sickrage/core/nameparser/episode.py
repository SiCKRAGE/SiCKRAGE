
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import datetime

from sickrage.core.common import Quality, DOWNLOADED
from sickrage.core.nameparser.show import Show
from sickrage.core.tv.episode import TVEpisode

class Episode(TVEpisode):
    def __init__(self, season, episode, absolute_number, name):
        self._name = name
        self._season = season
        self._episode = episode
        self._absolute_number = absolute_number
        self._airdate = datetime.date(2010, 3, 9)
        self._status = Quality.compositeStatus(DOWNLOADED, Quality.SDTV)
        self._release_name = 'Show.Name.S02E03.HDTV.XviD-RLSGROUP'
        self._release_group = 'RLSGROUP'
        self._is_proper = True

        self.show = Show()
        self.scene_season = season
        self.scene_episode = episode
        self.scene_absolute_number = absolute_number
        self.relatedEps = []
