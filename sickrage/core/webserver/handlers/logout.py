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
from urllib.parse import urlencode

import sickrage
from sickrage.core.webserver.handlers.base import BaseHandler


class LogoutHandler(BaseHandler):
    def get(self, *args, **kwargs):
        logout_uri = sickrage.app.auth_server.get_url('end_session_endpoint') if sickrage.app.config.general.sso_auth_enabled else ""
        redirect_uri = f"{self.request.protocol}://{self.request.host}{sickrage.app.config.general.web_root}/login"

        self.clear_cookie('_sr')
        self.clear_cookie('_sr_access_token')
        self.clear_cookie('_sr_refresh_token')

        if logout_uri:
            # logout_args = {
            #     'post_logout_redirect_uri': redirect_uri,
            #     'id_token_hint': sickrage.app.api.token['access_token'],
            #     'state': sickrage.app.api.token['session_state'],
            # }
            #
            # return self.redirect(f'{logout_uri}?{urlencode(logout_args)}', add_web_root=False)
            return self.redirect(f'{logout_uri}', add_web_root=False)
        else:
            return self.redirect(f'{redirect_uri}', add_web_root=False)
