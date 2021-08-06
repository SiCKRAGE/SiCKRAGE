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
import functools
import json
import traceback
import types
from concurrent.futures.thread import ThreadPoolExecutor

import bleach
import sentry_sdk
from apispec import APISpec
from apispec.exceptions import APISpecError
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.tornado import TornadoPlugin
from tornado.escape import to_basestring
from tornado.ioloop import IOLoop
from tornado.web import HTTPError
from tornado.web import RequestHandler

import sickrage
from sickrage.core.enums import UserPermission
from sickrage.core.helpers import get_internal_ip


class APIBaseHandler(RequestHandler):
    def __init__(self, application, request, api_version='', **kwargs):
        super(APIBaseHandler, self).__init__(application, request, **kwargs)
        self.executor = ThreadPoolExecutor(thread_name_prefix=f'API{api_version}-Thread')

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
                        return self._unauthorized(error='user is not authorized')

                    if not sickrage.app.api.token:
                        exchanged_token = sickrage.app.auth_server.token_exchange(token)
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

                    method = self.run_async(getattr(self, method_name))
                    setattr(self, method_name, method)
                except Exception:
                    return self._unauthorized(error='failed to decode token')
            else:
                return self._unauthorized(error='invalid authorization request')
        else:
            return self._unauthorized(error='authorization header missing')

    def run_async(self, method):
        @functools.wraps(method)
        async def wrapper(self, *args, **kwargs):
            resp = await IOLoop.current().run_in_executor(self.executor, functools.partial(method, *args, **kwargs))
            self.finish(resp)

        return types.MethodType(wrapper, self)

    def get_current_user(self):
        auth_header = self.request.headers.get('Authorization')
        if 'bearer' in auth_header.lower():
            certs = sickrage.app.auth_server.certs()
            token = auth_header.strip('Bearer').strip()
            decoded_token = sickrage.app.auth_server.decode_token(token, certs)
            if sickrage.app.config.user.sub_id == decoded_token.get('sub'):
                return decoded_token

    def write_error(self, status_code, **kwargs):
        if status_code == 500:
            excp = kwargs['exc_info'][1]
            tb = kwargs['exc_info'][2]
            stack = traceback.extract_tb(tb)
            clean_stack = [i for i in stack if i[0][-6:] != 'gen.py' and i[0][-13:] != 'concurrent.py']
            error_msg = '{}\n  Exception: {}'.format(''.join(traceback.format_list(clean_stack)), excp)
        else:
            error_msg = kwargs.get('reason', '') or kwargs.get('error', '') or kwargs.get('errors', '')

        sickrage.app.log.error(error_msg)

        return self.finish(self.json_response(error=error_msg, status=status_code))

    def set_default_headers(self):
        self.set_header('X-SiCKRAGE-Server', sickrage.version())
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With, X-SiCKRAGE-Server")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, PUT, PATCH, DELETE, OPTIONS')
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

    def options(self, *args, **kwargs):
        self._no_content()

    def json_response(self, data=None, error=None, status=200):
        self.set_header('Content-Type', 'application/json')

        self.set_status(status)

        if error is not None:
            return json.dumps({'error': error})

        if data is not None:
            return json.dumps(data)

        return None

    def _no_content(self):
        return self.json_response(status=204)

    def _unauthorized(self, error):
        return self.json_response(error=error, status=401)

    def _bad_request(self, error):
        return self.json_response(error=error, status=400)

    def _not_found(self, error):
        return self.json_response(error=error, status=404)

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

    def get_argument(self, *args, **kwargs):
        value = super(APIBaseHandler, self).get_argument(*args, **kwargs)

        try:
            return bleach.clean(value)
        except TypeError:
            return value


class ApiProfileHandler(APIBaseHandler):
    def get(self):
        return self.json_response(self.current_user)


class ApiPingHandler(APIBaseHandler):
    def get(self):
        return self.json_response({'message': 'pong'})


class ApiSwaggerDotJsonHandler(APIBaseHandler):
    def initialize(self, api_handlers, api_version):
        super(ApiSwaggerDotJsonHandler, self).initialize()
        self.api_handlers = sickrage.app.wserver.handlers[api_handlers]
        self.api_version = api_version

    def get(self):
        """ Get swagger.json """
        return self.json_response(self.generate_swagger_json(self.api_handlers, self.api_version))
