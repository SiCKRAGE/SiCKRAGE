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
    def prepare(self, *args, **kwargs):
        logout_uri = sickrage.app.oidc_client.get_url('end_session_endpoint')
        redirect_uri = "{}://{}{}/login".format(self.request.protocol, self.request.host, sickrage.app.config.web_root)

        if self.get_secure_cookie('sr_refresh_token'):
            sickrage.app.oidc_client.logout(self.get_secure_cookie('sr_refresh_token'))

        self.clear_all_cookies()

        return super(BaseHandler, self).redirect('{}?redirect_uri={}'.format(logout_uri, redirect_uri))
