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

import sentry_sdk
from jose import ExpiredSignatureError, JWTError

import sickrage
from sickrage.core.enums import UserPermission
from sickrage.core.helpers import is_ip_whitelisted, get_internal_ip
from sickrage.core.webserver.handlers.base import BaseHandler


class LoginHandler(BaseHandler):
    def get(self, *args, **kwargs):
        if is_ip_whitelisted(self.request.remote_ip):
            return self.redirect("{}".format(self.get_argument('next', "/{}/".format(sickrage.app.config.general.default_page.value))))
        elif 'Authorization' in self.request.headers:
            return self.handle_jwt_auth_get()
        elif sickrage.app.config.general.sso_auth_enabled and sickrage.app.auth_server.health:
            return self.handle_sso_auth_get()
        elif sickrage.app.config.general.local_auth_enabled:
            return self.handle_local_auth_get()
        else:
            return self.render('login_failed.mako',
                               topmenu="system",
                               header="SiCKRAGE Login Failed",
                               title="SiCKRAGE Login Failed",
                               controller='root',
                               action='login')

    def post(self, *args, **kwargs):
        if sickrage.app.config.general.local_auth_enabled:
            return self.handle_local_auth_post()

    def handle_jwt_auth_get(self):
        certs = sickrage.app.auth_server.certs()
        auth_token = self.request.headers['Authorization'].strip('Bearer').strip()

        try:
            decoded_token = sickrage.app.auth_server.decode_token(auth_token, certs)
        except ExpiredSignatureError:
            self.set_status(401)
            return {'error': 'Token expired'}
        except JWTError as e:
            self.set_status(401)
            return {'error': f'Improper JWT token supplied, {e!r}'}

        if not sickrage.app.config.user.sub_id:
            sickrage.app.config.user.sub_id = decoded_token.get('sub')
            sickrage.app.config.save(mark_dirty=True)

        if sickrage.app.config.user.sub_id == decoded_token.get('sub'):
            save_config = False
            if not sickrage.app.config.user.username:
                sickrage.app.config.user.username = decoded_token.get('preferred_username')
                save_config = True

            if not sickrage.app.config.user.email:
                sickrage.app.config.user.email = decoded_token.get('email')
                save_config = True

            if not sickrage.app.config.user.permissions == UserPermission.SUPERUSER:
                sickrage.app.config.user.permissions = UserPermission.SUPERUSER
                save_config = True

            if save_config:
                sickrage.app.config.save()

        if sickrage.app.config.user.sub_id == decoded_token.get('sub'):
            sentry_sdk.set_user({
                'id': sickrage.app.config.user.sub_id,
                'username': sickrage.app.config.user.username,
                'email': sickrage.app.config.user.email
            })

        if sickrage.app.config.user.sub_id != decoded_token.get('sub'):
            return

        if not sickrage.app.api.token:
            exchanged_token = sickrage.app.auth_server.token_exchange(auth_token)
            if exchanged_token:
                sickrage.app.api.token = exchanged_token

        if not sickrage.app.config.general.server_id:
            server_id = sickrage.app.api.server.register_server(
                ip_addresses=','.join([get_internal_ip()]),
                web_protocol=self.request.protocol,
                web_port=sickrage.app.config.general.web_port,
                web_root=sickrage.app.config.general.web_root,
                server_version=sickrage.version()
            )

            if server_id:
                sickrage.app.config.general.server_id = server_id
                sickrage.app.config.save()

        if sickrage.app.config.general.server_id:
            sentry_sdk.set_tag('server_id', sickrage.app.config.general.server_id)

    def handle_sso_auth_get(self):
        code = self.get_argument('code', None)

        redirect_uri = f"{self.request.protocol}://{self.request.host}{sickrage.app.config.general.web_root}/login"

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

                if not sickrage.app.config.user.sub_id:
                    sickrage.app.config.user.sub_id = decoded_token.get('sub')
                    sickrage.app.config.save(mark_dirty=True)

                if sickrage.app.config.user.sub_id == decoded_token.get('sub'):
                    save_config = False
                    if not sickrage.app.config.user.username:
                        sickrage.app.config.user.username = decoded_token.get('preferred_username')
                        save_config = True

                    if not sickrage.app.config.user.email:
                        sickrage.app.config.user.email = decoded_token.get('email')
                        save_config = True

                    if not sickrage.app.config.user.permissions == UserPermission.SUPERUSER:
                        sickrage.app.config.user.permissions = UserPermission.SUPERUSER
                        save_config = True

                    if save_config:
                        sickrage.app.config.save()

                if sickrage.app.config.user.sub_id == decoded_token.get('sub'):
                    sentry_sdk.set_user({
                        'id': sickrage.app.config.user.sub_id,
                        'username': sickrage.app.config.user.username,
                        'email': sickrage.app.config.user.email
                    })

                if sickrage.app.config.user.sub_id != decoded_token.get('sub'):
                    if sickrage.app.api.token:
                        allowed_usernames = sickrage.app.api.allowed_usernames()['data']
                        if not decoded_token.get('preferred_username') in allowed_usernames:
                            sickrage.app.log.debug(
                                "USERNAME:{} IP:{} - WEB-UI ACCESS DENIED".format(decoded_token.get('preferred_username'), self.request.remote_ip))
                            return self.redirect('/logout')
                    else:
                        return self.redirect('/logout')
                elif not sickrage.app.api.token:
                    exchanged_token = sickrage.app.auth_server.token_exchange(token['access_token'])
                    if exchanged_token:
                        sickrage.app.api.token = exchanged_token
            except Exception as e:
                sickrage.app.log.debug('{!r}'.format(e))
                return self.redirect('/logout')

            if not sickrage.app.config.general.server_id:
                server_id = sickrage.app.api.server.register_server(
                    ip_addresses=','.join([get_internal_ip()]),
                    web_protocol=self.request.protocol,
                    web_port=sickrage.app.config.general.web_port,
                    web_root=sickrage.app.config.general.web_root,
                    server_version=sickrage.version()
                )

                if server_id:
                    sickrage.app.config.general.server_id = server_id
                    sickrage.app.config.save()

            if sickrage.app.config.general.server_id:
                sentry_sdk.set_tag('server_id', sickrage.app.config.general.server_id)

            redirect_uri = self.get_argument('next', "/{}/".format(sickrage.app.config.general.default_page.value))
            return self.redirect("{}".format(redirect_uri))
        else:
            authorization_url = sickrage.app.auth_server.authorization_url(redirect_uri=redirect_uri, scope="profile email")
            if authorization_url:
                return self.redirect(authorization_url, add_web_root=False)

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

        if username == sickrage.app.config.user.username and password == sickrage.app.config.user.password:
            self.set_secure_cookie('_sr', sickrage.app.config.general.api_v1_key, expires_days=30 if remember_me else 1)
            return self.redirect("{}".format(self.get_argument('next', "/{}/".format(sickrage.app.config.general.default_page.value))))

        return self.redirect("/login")
