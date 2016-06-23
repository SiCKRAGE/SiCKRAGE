#!/usr/bin/env python2
# Author: echel0n <echel0n@sickrage.ca>
# URL: https://git.sickrage.ca
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

class Show(object):
    def __init__(self):
        self.name = "Show Name"
        self.genre = "Comedy"
        self.indexerid = 00001
        self.air_by_date = 0
        self.sports = 0
        self.anime = 0
        self.scene = 0

    def _is_anime(self):
        """
        Find out if show is anime
        :return: True if show is anime, False if not
        """
        if self.anime > 0:
            return True
        else:
            return False

    is_anime = property(_is_anime)

    def _is_sports(self):
        """
        Find out if show is sports
        :return: True if show is sports, False if not
        """
        if self.sports > 0:
            return True
        else:
            return False

    is_sports = property(_is_sports)

    def _is_scene(self):
        """
        Find out if show is scene numbering
        :return: True if show is scene numbering, False if not
        """
        if self.scene > 0:
            return True
        else:
            return False

    is_scene = property(_is_scene)
