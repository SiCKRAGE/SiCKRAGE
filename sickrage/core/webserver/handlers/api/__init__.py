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
import traceback

import sentry_sdk
from apispec import APISpec
from apispec.exceptions import APISpecError
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.tornado import TornadoPlugin
from tornado.escape import to_basestring
from tornado.web import HTTPError

import sickrage
from sickrage.core.enums import UserPermission
from sickrage.core.helpers import get_external_ip, get_internal_ip
from sickrage.core.webserver.handlers.base import BaseHandler


class APIBaseHandler(BaseHandler):
    def prepare(self):
        super(APIBaseHandler, self).prepare()

        method_name = self.request.method.lower()
        if method_name == 'options':
            return

        certs = sickrage.app.auth_server.certs()
        auth_header = self.request.headers.get('Authorization')

        if auth_header:
            if 'bearer' in auth_header.lower():
                try:
                    token = auth_header.strip('Bearer').strip()
                    decoded_token = sickrage.app.auth_server.decode_token(token, certs)

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
                        return self.send_error(401, error='user is not authorized')

                    if sickrage.app.config.general.enable_sickrage_api and not sickrage.app.api.token:
                        exchanged_token = sickrage.app.auth_server.token_exchange(token)
                        if exchanged_token:
                            sickrage.app.api.token = exchanged_token

                    internal_connections = f"{self.request.protocol}://{get_internal_ip()}:{sickrage.app.config.general.web_port}{sickrage.app.config.general.web_root}"
                    external_connections = f"{self.request.protocol}://{get_external_ip()}:{sickrage.app.config.general.web_port}{sickrage.app.config.general.web_root}"
                    connections = ','.join([internal_connections, external_connections])

                    if sickrage.app.config.general.server_id and not sickrage.app.api.account.update_server(sickrage.app.config.general.server_id, connections):
                        sickrage.app.config.general.server_id = ''

                    if not sickrage.app.config.general.server_id:
                        server_id = sickrage.app.api.account.register_server(connections)
                        if server_id:
                            sickrage.app.config.general.server_id = server_id
                            sentry_sdk.set_tag('server_id', sickrage.app.config.general.server_id)
                            sickrage.app.config.save()

                    self.current_user = decoded_token
                except Exception:
                    return self.send_error(401, error='failed to decode token')
            else:
                return self.send_error(401, error='invalid authorization request')
        else:
            return self.send_error(401, error='authorization header missing')

    def get_current_user(self):
        return self.current_user

    def write_error(self, status_code, **kwargs):
        self.set_header('Content-Type', 'application/json')
        self.set_status(status_code)

        if status_code == 500:
            excp = kwargs['exc_info'][1]
            tb = kwargs['exc_info'][2]
            stack = traceback.extract_tb(tb)
            clean_stack = [i for i in stack if i[0][-6:] != 'gen.py' and i[0][-13:] != 'concurrent.py']
            error_msg = '{}\n  Exception: {}'.format(''.join(traceback.format_list(clean_stack)), excp)
        else:
            error_msg = kwargs.get('reason', '') or kwargs.get('error', '') or kwargs.get('errors', '')

        sickrage.app.log.error(error_msg)

        self.write_json({'error': error_msg})

    def set_default_headers(self):
        super(APIBaseHandler, self).set_default_headers()
        self.set_header('Content-Type', 'application/json')

    def write_json(self, response):
        self.write(json.dumps(response))

    def _validate_schema(self, schema, arguments):
        return schema().validate({k: to_basestring(v[0]) if len(v) <= 1 else to_basestring(v) for k, v in arguments.items()})

    def _parse_value(self, value, func):
        if value is not None:
            try:
                return func(value)
            except ValueError:
                raise HTTPError(400, f'Invalid value {value!r}')

    def _parse_boolean(self, value):
        if isinstance(value, str):
            return value.lower() == 'true'
        return self._parse_value(value, bool)

    def generate_swagger_json(self, handlers, api_version):
        """Automatically generates Swagger spec file based on RequestHandler
        docstrings and returns it.
        """

        spec = APISpec(
            title="SiCKRAGE App API",
            version=api_version,
            openapi_version="3.0.2",
            info={'description': "Documentation for SiCKRAGE App API"},
            plugins=[TornadoPlugin(), MarshmallowPlugin()],
        )

        for handler in handlers:
            try:
                spec.path(urlspec=handler)
            except APISpecError:
                pass

        return spec.to_dict()


class ApiPingHandler(APIBaseHandler):
    def get(self):
        return self.write_json({'message': 'pong'})


class ApiSwaggerDotJsonHandler(APIBaseHandler):
    def initialize(self, api_handlers, api_version):
        super(ApiSwaggerDotJsonHandler, self).initialize()
        self.api_handlers = sickrage.app.wserver.handlers[api_handlers]
        self.api_version = api_version

    def get(self):
        """ Get swagger.json """
        return self.write_json(self.generate_swagger_json(self.api_handlers, self.api_version))
