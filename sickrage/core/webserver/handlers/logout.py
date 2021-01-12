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


import sickrage
from sickrage.core.webserver.handlers.base import BaseHandler


class LogoutHandler(BaseHandler):
    def get(self, *args, **kwargs):
        logout_uri = sickrage.app.auth_server.get_url('end_session_endpoint') if sickrage.app.config.general.sso_auth_enabled else ""
        redirect_uri = "{}://{}{}/login".format(self.request.protocol, self.request.host, sickrage.app.config.general.web_root)

        self.clear_cookie('_sr')
        self.clear_cookie('_sr_access_token')
        self.clear_cookie('_sr_refresh_token')

        if logout_uri:
            return super(BaseHandler, self).redirect('{}?redirect_uri={}'.format(logout_uri, redirect_uri))
        else:
            return super(BaseHandler, self).redirect('{}'.format(redirect_uri))
