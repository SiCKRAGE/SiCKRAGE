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
from abc import ABC

import sickrage
from sickrage.core import AccountAPI
from sickrage.core.api import API
from sickrage.core.webserver.handlers.base import BaseHandler


class LoginHandler(BaseHandler, ABC):
    def prepare(self, *args, **kwargs):
        code = self.get_argument('code', None)

        redirect_uri = "{}://{}{}/login".format(self.request.protocol, self.request.host, sickrage.app.config.web_root)

        if code:
            try:
                token = sickrage.app.oidc_client.authorization_code(code, redirect_uri)
                userinfo = sickrage.app.oidc_client.userinfo(token['access_token'])

                self.set_secure_cookie('sr_access_token', token['access_token'])
                self.set_secure_cookie('sr_refresh_token', token['refresh_token'])

                if not userinfo.get('sub'):
                    return self.redirect('/logout')

                if not sickrage.app.config.sub_id:
                    sickrage.app.config.sub_id = userinfo.get('sub')
                    sickrage.app.config.save()
                elif sickrage.app.config.sub_id != userinfo.get('sub'):
                    if API().token:
                        allowed_usernames = API().allowed_usernames()['data']
                        if not userinfo['preferred_username'] in allowed_usernames:
                            sickrage.app.log.debug("USERNAME:{} IP:{} - ACCESS DENIED".format(userinfo['preferred_username'], self.request.remote_ip))
                            return self.redirect('/logout')
                    else:
                        return self.redirect('/logout')

                if not API().token:
                    API().exchange_token(token)
            except Exception as e:
                return self.redirect('/logout')

            if not sickrage.app.config.app_id:
                sickrage.app.config.app_id = AccountAPI().register_app_id()
                sickrage.app.config.save()

            redirect_uri = self.get_argument('next', "/{}/".format(sickrage.app.config.default_page))
            return self.redirect("{}".format(redirect_uri))
        else:
            authorization_url = sickrage.app.oidc_client.authorization_url(redirect_uri=redirect_uri)
            return super(BaseHandler, self).redirect(authorization_url)