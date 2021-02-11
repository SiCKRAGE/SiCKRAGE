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


import tornado.web

import sickrage
from sickrage.core.webserver.handlers.base import BaseHandler


class NotFoundHandler(BaseHandler):
    def prepare(self):
        if sickrage.app.config.general.web_root:
            if not self.request.uri.startswith(sickrage.app.config.general.web_root):
                return self.redirect(self.request.uri)

        if self.request.uri[len(sickrage.app.config.general.web_root) + 1:][:3] != 'api':
            raise tornado.web.HTTPError(
                status_code=404,
                reason="You have reached this page by accident, please check the url."
            )

        raise tornado.web.HTTPError(
            status_code=401,
            reason="Wrong API key used."
        )
