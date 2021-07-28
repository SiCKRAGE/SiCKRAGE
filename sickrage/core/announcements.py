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
import functools
import threading

from sqlalchemy import orm

import sickrage
from sickrage.core.databases.cache import CacheDB


class Announcement(object):
    """
    Represents an announcement.
    """

    def __init__(self, title, description, image, date, ahash):
        self.title = title
        self.description = description
        self.image = image
        self.date = date
        self.ahash = ahash

    @property
    def seen(self):
        session = sickrage.app.cache_db.session()
        try:
            announcement = session.query(CacheDB.Announcements).filter_by(hash=self.ahash).one()
            return True if announcement.seen else False
        except orm.exc.NoResultFound:
            pass

    @seen.setter
    def seen(self, value):
        session = sickrage.app.cache_db.session()
        try:
            announcement = session.query(CacheDB.Announcements).filter_by(hash=self.ahash).one()
            announcement.seen = value
        except orm.exc.NoResultFound:
            pass


class Announcements(object):
    """
    Keeps a static list of (announcement) UIErrors to be displayed on the UI and allows
    the list to be cleared.
    """

    def __init__(self):
        self.name = "ANNOUNCEMENTS"
        self.running = False
        self._announcements = {}

    def add(self, ahash, title, description, image, date):
        session = sickrage.app.cache_db.session()
        self._announcements[ahash] = Announcement(title, description, image, date, ahash)
        if not session.query(CacheDB.Announcements).filter_by(hash=ahash).count():
            sickrage.app.log.debug('Adding new announcement to Web-UI')
            session.add(CacheDB.Announcements(**{'hash': ahash}))
            session.commit()

    def clear(self, ahash=None):
        session = sickrage.app.cache_db.session()

        if not ahash:
            self._announcements.clear()
            session.query(CacheDB.Announcements).delete()
            session.commit()
        else:
            if ahash in self._announcements:
                del self._announcements[ahash]
            session.query(CacheDB.Announcements).filter_by(hash=ahash).delete()
            session.commit()

    def get_all(self):
        return sorted(self._announcements.values(), key=lambda k: k.date)

    def get(self, ahash):
        return self._announcements.get(ahash)

    def count(self):
        session = sickrage.app.cache_db.session()
        return session.query(CacheDB.Announcements).filter(CacheDB.Announcements.seen is False).count()
