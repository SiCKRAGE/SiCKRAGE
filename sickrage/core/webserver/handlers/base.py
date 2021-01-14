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
import time
import traceback
import types
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Optional, Awaitable
from urllib.parse import urlparse, urljoin

from jose import ExpiredSignatureError
from keycloak.exceptions import KeycloakClientError
from mako.exceptions import RichTraceback
from tornado import locale
from tornado.web import RequestHandler

import sickrage
from sickrage.core.helpers import is_ip_whitelisted, torrent_webui_url


class BaseHandler(RequestHandler):
    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)

        self.executor = ThreadPoolExecutor(thread_name_prefix='TORNADO-Thread')

        self.startTime = time.time()

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    def get_user_locale(self):
        return locale.get(sickrage.app.config.gui.gui_lang)

    def write_error(self, status_code, **kwargs):
        if "exc_info" in kwargs:
            exc_info = kwargs["exc_info"]
            error = repr(exc_info[1])

            sickrage.app.log.error(error)

            if self.settings.get("debug"):
                trace_info = ''.join([f"{line}<br>" for line in traceback.format_exception(*exc_info)])
                request_info = ''.join([f"<strong>{k}</strong>: {v}<br>" for k, v in self.request.__dict__.items()])

                self.set_header('Content-Type', 'text/html')
                return self.write(f"""<html>
                                 <title>{error}</title>
                                 <body>
                                    <button onclick="window.location='{sickrage.app.config.general.web_root}/logs/';">View Log(Errors)</button>
                                    <button onclick="window.location='{sickrage.app.config.general.web_root}/home/restart?pid={sickrage.app.pid}&force=1';">Restart SiCKRAGE</button>
                                    <button onclick="window.location='{sickrage.app.config.general.web_root}/logout';">Logout</button>
                                    <h2>Error</h2>
                                    <p>{error}</p>
                                    <h2>Traceback</h2>
                                    <p>{trace_info}</p>
                                    <h2>Request Info</h2>
                                    <p>{request_info}</p>
                                 </body>
                               </html>""")

    def get_current_user(self):
        if is_ip_whitelisted(self.request.remote_ip):
            return True
        elif sickrage.app.config.general.sso_auth_enabled and sickrage.app.auth_server.health:
            try:
                access_token = self.get_secure_cookie('_sr_access_token')
                refresh_token = self.get_secure_cookie('_sr_refresh_token')
                if not all([access_token, refresh_token]):
                    return

                certs = sickrage.app.auth_server.certs()
                if not certs:
                    return

                try:
                    return sickrage.app.auth_server.decode_token(access_token.decode("utf-8"), certs)
                except (KeycloakClientError, ExpiredSignatureError):
                    token = sickrage.app.auth_server.refresh_token(refresh_token.decode("utf-8"))
                    if not token:
                        return

                    self.set_secure_cookie('_sr_access_token', token['access_token'])
                    self.set_secure_cookie('_sr_refresh_token', token['refresh_token'])
                    return sickrage.app.auth_server.decode_token(token['access_token'], certs)
            except Exception as e:
                return
        elif sickrage.app.config.general.local_auth_enabled:
            cookie = self.get_secure_cookie('_sr').decode() if self.get_secure_cookie('_sr') else None
            if cookie == sickrage.app.config.general.api_v1_key:
                return True

    def render_string(self, template_name, **kwargs):
        template_kwargs = {
            'title': "",
            'header': "",
            'topmenu': "",
            'submenu': "",
            'controller': "home",
            'action': "index",
            'srPID': sickrage.app.pid,
            'srHttpsEnabled': sickrage.app.config.general.enable_https or bool(self.request.headers.get('X-Forwarded-Proto') == 'https'),
            'srHost': self.request.headers.get('X-Forwarded-Host', self.request.host.split(':')[0]),
            'srHttpPort': self.request.headers.get('X-Forwarded-Port', sickrage.app.config.general.web_port),
            'srHttpsPort': sickrage.app.config.general.web_port,
            'srHandleReverseProxy': sickrage.app.config.general.handle_reverse_proxy,
            'srDefaultPage': sickrage.app.config.general.default_page.value,
            'srWebRoot': sickrage.app.config.general.web_root,
            'srLocale': self.get_user_locale().code,
            'srLocaleDir': sickrage.LOCALE_DIR,
            'srStartTime': self.startTime,
            'makoStartTime': time.time(),
            'overall_stats': None,
            'torrent_webui_url': torrent_webui_url(),
            'application': self.application,
            'request': self.request,
        }

        template_kwargs.update(self.get_template_namespace())
        template_kwargs.update(kwargs)

        try:
            return self.application.settings['templates'][template_name].render_unicode(**template_kwargs)
        except Exception:
            kwargs['title'] = _('HTTP Error 500')
            kwargs['header'] = _('HTTP Error 500')
            kwargs['backtrace'] = RichTraceback()
            template_kwargs.update(kwargs)

            sickrage.app.log.error("%s: %s" % (str(kwargs['backtrace'].error.__class__.__name__), kwargs['backtrace'].error))

            return self.application.settings['templates']['errors/500.mako'].render_unicode(**template_kwargs)

    def render(self, template_name, **kwargs):
        self.write(self.render_string(template_name, **kwargs))

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, PUT, PATCH, DELETE, OPTIONS')
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

    def redirect(self, url, permanent=True, status=None):
        if sickrage.app.config.general.web_root not in url:
            url = urljoin(sickrage.app.config.general.web_root + '/', url.lstrip('/'))
        super(BaseHandler, self).redirect(url, permanent, status)

    def previous_url(self):
        url = urlparse(self.request.headers.get("referer", "/{}/".format(sickrage.app.config.general.default_page.value)))
        return url._replace(scheme="", netloc="").geturl()

    def _genericMessage(self, subject, message):
        return self.render('generic_message.mako',
                           message=message,
                           subject=subject,
                           title="",
                           controller='root',
                           action='genericmessage')

    def get_url(self, url):
        if sickrage.app.config.general.web_root not in url:
            url = urljoin(sickrage.app.config.general.web_root + '/', url.lstrip('/'))
        url = urljoin("{}://{}".format(self.request.protocol, self.request.host), url)
        return url

    def run_async(self, method):
        @functools.wraps(method)
        async def wrapper(self, *args, **kwargs):
            await sickrage.app.wserver.io_loop.run_in_executor(self.executor, functools.partial(method, *args, **kwargs))

        return types.MethodType(wrapper, self)

    def prepare(self):
        method_name = self.request.method.lower()
        method = self.run_async(getattr(self, method_name))
        setattr(self, method_name, method)

    def options(self, *args, **kwargs):
        self.set_status(204)
        self.finish()
