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
import re
from abc import ABC

import sickrage
from sickrage.core.helpers import is_ip_whitelisted, get_internal_ip, get_external_ip
from sickrage.core.webserver.handlers.base import BaseHandler


class LoginHandler(BaseHandler, ABC):
    async def get(self, *args, **kwargs):
        if is_ip_whitelisted(self.request.remote_ip):
            return self.redirect("{}".format(self.get_argument('next', "/{}/".format(sickrage.app.config.default_page))))
        elif sickrage.app.config.sso_auth_enabled and sickrage.app.auth_server.health:
            await self.run_in_executor(self.handle_sso_auth_get)
        elif sickrage.app.config.local_auth_enabled:
            await self.run_in_executor(self.handle_local_auth_get)
        else:
            return self.render('login_failed.mako',
                               topmenu="system",
                               header="SiCKRAGE Login Failed",
                               title="SiCKRAGE Login Failed",
                               controller='root',
                               action='login')

    async def post(self, *args, **kwargs):
        if sickrage.app.config.local_auth_enabled:
            await self.run_in_executor(self.handle_local_auth_post)

    def handle_sso_auth_get(self):
        code = self.get_argument('code', None)

        redirect_uri = "{}://{}{}/login".format(self.request.protocol, self.request.host, sickrage.app.config.web_root)

        if code:
            try:
                token = sickrage.app.auth_server.authorization_code(code, redirect_uri)
                if not token:
                    return self.redirect('/logout')

                certs = sickrage.app.auth_server.certs()
                if not certs:
                    return self.redirect('/logout')

                decoded_token = sickrage.app.auth_server.decode_token(token['access_token'], certs)
                if not decoded_token:
                    return self.redirect('/logout')

                if not decoded_token.get('sub'):
                    return self.redirect('/logout')

                self.set_secure_cookie('_sr_access_token', token['access_token'])
                self.set_secure_cookie('_sr_refresh_token', token['refresh_token'])

                if not sickrage.app.config.sub_id:
                    sickrage.app.config.sub_id = decoded_token.get('sub')
                    sickrage.app.config.save()

                if sickrage.app.config.sub_id != decoded_token.get('sub'):
                    if sickrage.app.api.token:
                        allowed_usernames = sickrage.app.api.allowed_usernames()['data']
                        if not decoded_token.get('preferred_username') in allowed_usernames:
                            sickrage.app.log.debug(
                                "USERNAME:{} IP:{} - WEB-UI ACCESS DENIED".format(decoded_token.get('preferred_username'), self.request.remote_ip))
                            return self.redirect('/logout')
                    else:
                        return self.redirect('/logout')
                elif sickrage.app.config.enable_sickrage_api:
                    if sickrage.app.api.token:
                        sickrage.app.api.logout()
                    sickrage.app.api.token = token
            except Exception as e:
                sickrage.app.log.debug('{!r}'.format(e))
                return self.redirect('/logout')

            internal_connections = "{}://{}:{}{}".format(self.request.protocol,
                                                         get_internal_ip(),
                                                         sickrage.app.config.web_port,
                                                         sickrage.app.config.web_root)

            external_connections = "{}://{}:{}{}".format(self.request.protocol,
                                                         get_external_ip(),
                                                         sickrage.app.config.web_port,
                                                         sickrage.app.config.web_root)

            connections = ','.join([internal_connections, external_connections])

            if not re.match(r'[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}', sickrage.app.config.server_id or ""):
                server_id = sickrage.app.api.account.register_server(connections)
                if server_id:
                    sickrage.app.config.server_id = server_id
                    sickrage.app.config.save()
            else:
                sickrage.app.api.account.update_server(sickrage.app.config.server_id, connections)

            redirect_uri = self.get_argument('next', "/{}/".format(sickrage.app.config.default_page))
            return self.redirect("{}".format(redirect_uri))
        else:
            authorization_url = sickrage.app.auth_server.authorization_url(redirect_uri=redirect_uri, scope="profile email offline_access")
            if authorization_url:
                return super(BaseHandler, self).redirect(authorization_url)

        return self.redirect('/logout')

    def handle_local_auth_get(self):
        return self.render('login.mako',
                           topmenu="system",
                           header="SiCKRAGE Login",
                           title="SiCKRAGE Login",
                           controller='root',
                           action='login')

    def handle_local_auth_post(self):
        username = self.get_argument('username', '')
        password = self.get_argument('password', '')
        remember_me = self.get_argument('remember_me', None)

        if username == sickrage.app.config.web_username and password == sickrage.app.config.web_password:
            self.set_secure_cookie('_sr', sickrage.app.config.api_key, expires_days=30 if remember_me else 1)
            return self.redirect("{}".format(self.get_argument('next', "/{}/".format(sickrage.app.config.default_page))))

        return self.redirect("/login")
