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
import json

import sickrage
from sickrage.core.webserver.handlers.base import BaseHandler
from sickrage.libs.trakt.interfaces.base import authenticated


class AnnouncementsHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        return self.render('announcements.mako',
                           announcements=sickrage.app.announcements.get_all(),
                           title=_('Announcements'),
                           header=_('Announcements'),
                           topmenu='announcements',
                           controller='root',
                           action='announcements')


class MarkAnnouncementSeenHandler(BaseHandler):
    @authenticated
    def post(self, *args, **kwargs):
        ahash = self.get_argument('ahash')

        announcement = sickrage.app.announcements.get(ahash)
        if announcement:
            announcement.seen = True

        return self.write(json.dumps({'success': True}))


class AnnouncementCountHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        return self.write(json.dumps({'count': sickrage.app.announcements.count()}))
