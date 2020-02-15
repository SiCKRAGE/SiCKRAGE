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
import re
from abc import ABC

import sickrage
from sickrage.core.webserver.handlers.base import BaseHandler


class LoginHandler(BaseHandler, ABC):
    def get(self, *args, **kwargs):
        code = self.get_argument('code', None)

        redirect_uri = "{}://{}{}/login".format(self.request.protocol, self.request.host, sickrage.app.config.web_root)

        if code:
            try:
                token = sickrage.app.oidc_client.authorization_code(code, redirect_uri)
                decoded_token = sickrage.app.oidc_client.decode_token(token['access_token'], sickrage.app.oidc_client.certs())

                self.set_secure_cookie('_sr_access_token', token['access_token'])
                self.set_secure_cookie('_sr_refresh_token', token['refresh_token'])

                if not decoded_token.get('sub'):
                    return self.redirect('/logout')

                if not sickrage.app.config.sub_id:
                    sickrage.app.config.sub_id = decoded_token.get('sub')
                    sickrage.app.config.save()

                if sickrage.app.config.sub_id != decoded_token.get('sub'):
                    if sickrage.app.api.token:
                        allowed_usernames = sickrage.app.api.allowed_usernames()['data']
                        if not decoded_token['preferred_username'] in allowed_usernames:
                            sickrage.app.log.debug("USERNAME:{} IP:{} - WEB-UI ACCESS DENIED".format(decoded_token['preferred_username'], self.request.remote_ip))
                            return self.redirect('/logout')
                    else:
                        return self.redirect('/logout')
                else:
                    if sickrage.app.api.token:
                        sickrage.app.api.logout()
                    sickrage.app.api.token = token
            except Exception as e:
                sickrage.app.log.debug('{!r}'.format(e))
                return self.redirect('/logout')

            if not re.match(r'[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}', sickrage.app.config.app_id or ""):
                sickrage.app.config.app_id = sickrage.app.api.account.register_app_id()
                sickrage.app.config.save()

            redirect_uri = self.get_argument('next', "/{}/".format(sickrage.app.config.default_page))
            return self.redirect("{}".format(redirect_uri))
        else:
            authorization_url = sickrage.app.oidc_client.authorization_url(redirect_uri=redirect_uri, scope="profile email offline_access")
            return super(BaseHandler, self).redirect(authorization_url)
