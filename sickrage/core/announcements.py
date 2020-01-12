# ##############################################################################
#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#  -
#  This file is part of SiCKRAGE.
#  -
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  -
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
# ##############################################################################


class Announcement(object):
    """
    Represents an announcement.
    """

    def __init__(self, title, description, image, date):
        self.title = title
        self.description = description
        self.image = image
        self.date = date


class Announcements(object):
    """
    Keeps a static list of (announcement) UIErrors to be displayed on the UI and allows
    the list to be cleared.
    """

    def __init__(self):
        self.announcements = []

    def add(self, title, description, image, date):
        self.announcements += [Announcement(title, description, image, date)]

    def clear(self):
        self.announcements = []

    def get(self):
        return self.announcements

    def count(self):
        return len(self.announcements)
