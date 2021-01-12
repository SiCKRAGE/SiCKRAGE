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

import sentry_sdk
from tornado.web import authenticated

import sickrage
from sickrage.core.enums import UserPermission
from sickrage.core.helpers import get_internal_ip, get_external_ip
from sickrage.core.webserver.handlers.base import BaseHandler


class AccountLinkHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        code = self.get_argument('code', None)

        redirect_uri = "{}://{}{}/account/link".format(self.request.protocol, self.request.host, sickrage.app.config.general.web_root)

        if code:
            token = sickrage.app.auth_server.authorization_code(code, redirect_uri)
            if not token:
                return self.redirect('/account/link')

            certs = sickrage.app.auth_server.certs()
            if not certs:
                return self.redirect('/account/link')

            decoded_token = sickrage.app.auth_server.decode_token(token['access_token'], certs)
            if not decoded_token:
                return self.redirect('/account/link')

            # if sickrage.app.api.token:
            #     sickrage.app.api.logout()

            exchanged_token = sickrage.app.auth_server.token_exchange(token['access_token'])
            if exchanged_token:
                sickrage.app.api.token = exchanged_token

            sickrage.app.config.general.enable_sickrage_api = True

            if not sickrage.app.config.user.sub_id:
                sickrage.app.config.user.sub_id = decoded_token.get('sub_id')
                sickrage.app.config.user.username = decoded_token.get('preferred_username')
                sickrage.app.config.user.email = decoded_token.get('email')
                sickrage.app.config.user.permissions = UserPermission.SUPERUSER

                sentry_sdk.set_user({
                    'id': sickrage.app.config.user.sub_id,
                    'username': sickrage.app.config.user.username,
                    'email': sickrage.app.config.user.email
                })

            if not sickrage.app.config.general.server_id:
                internal_connections = "{}://{}:{}{}".format(self.request.protocol,
                                                             get_internal_ip(),
                                                             sickrage.app.config.general.web_port,
                                                             sickrage.app.config.general.web_root)

                external_connections = "{}://{}:{}{}".format(self.request.protocol,
                                                             get_external_ip(),
                                                             sickrage.app.config.general.web_port,
                                                             sickrage.app.config.general.web_root)

                connections = ','.join([internal_connections, external_connections])

                server_id = sickrage.app.api.account.register_server(connections)
                if server_id:
                    sickrage.app.config.general.server_id = server_id
                    sentry_sdk.set_tag('server_id', sickrage.app.config.general.server_id)

            sickrage.app.config.save(mark_dirty=True)

            sickrage.app.alerts.message(_('Linked SiCKRAGE account to SiCKRAGE API'))
        else:
            authorization_url = sickrage.app.auth_server.authorization_url(redirect_uri=redirect_uri, scope="profile email")
            if authorization_url:
                return super(BaseHandler, self).redirect(authorization_url)

        return self.redirect('/account/link')


class AccountUnlinkHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        if not sickrage.app.config.general.server_id or sickrage.app.api.account.unregister_server(sickrage.app.config.general.server_id):
            if not sickrage.app.config.general.sso_auth_enabled:
                sickrage.app.config.reset_encryption()
                sickrage.app.config.general.server_id = ""
                sickrage.app.config.user.sub_id = ""

            del sickrage.app.api.token

            sickrage.app.config.general.enable_sickrage_api = False
            sickrage.app.config.save()

            sickrage.app.alerts.message(_('Unlinked SiCKRAGE account from SiCKRAGE API'))


class AccountIsLinkedHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        return self.write(json.dumps({'linked': ('true', 'false')[not sickrage.app.api.userinfo]}))
