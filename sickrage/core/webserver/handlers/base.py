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
import os
import threading
import time
import traceback
from abc import ABC
from urllib.parse import urlparse, urljoin

from jose import ExpiredSignatureError
from keycloak.exceptions import KeycloakClientError
from mako.exceptions import RichTraceback
from mako.lookup import TemplateLookup
from tornado import locale
from tornado.web import RequestHandler

import sickrage
from sickrage.core import helpers


class BaseHandler(RequestHandler, ABC):
    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)
        self.startTime = time.time()

        # template settings
        self.mako_lookup = TemplateLookup(
            directories=[sickrage.app.config.gui_views_dir],
            module_directory=os.path.join(sickrage.app.cache_dir, 'mako'),
            filesystem_checks=True,
            strict_undefined=True,
            input_encoding='utf-8',
            output_encoding='utf-8',
            encoding_errors='replace'
        )

    def get_user_locale(self):
        return locale.get(sickrage.app.config.gui_lang)

    def write_error(self, status_code, **kwargs):
        # handle 404 http errors
        if status_code == 404:
            url = self.request.uri
            if sickrage.app.config.web_root and self.request.uri.startswith(sickrage.app.config.web_root):
                url = url[len(sickrage.app.config.web_root) + 1:]

            if url[:3] != 'api':
                self.render('/errors/404.mako', title=_('HTTP Error 404'), header=_('HTTP Error 404'))
            else:
                self.write('Wrong API key used')
        elif self.settings.get("debug") and "exc_info" in kwargs:
            exc_info = kwargs["exc_info"]
            trace_info = ''.join(["%s<br>" % line for line in traceback.format_exception(*exc_info)])
            request_info = ''.join(["<strong>%s</strong>: %s<br>" % (k, self.request.__dict__[k]) for k in self.request.__dict__.keys()])
            error = exc_info[1]

            sickrage.app.log.error(error)

            self.set_header('Content-Type', 'text/html')
            self.write("""<html>
                             <title>{error}</title>
                             <body>
                                <button onclick="window.location='{webroot}/logs/';">View Log(Errors)</button>
                                <button onclick="window.location='{webroot}/home/restart?pid={pid}&force=1';">Restart SiCKRAGE</button>
                                <button onclick="window.location='{webroot}/logout';">Logout</button>
                                <h2>Error</h2>
                                <p>{error}</p>
                                <h2>Traceback</h2>
                                <p>{traceback}</p>
                                <h2>Request Info</h2>
                                <p>{request}</p>
                             </body>
                           </html>""".format(pid=sickrage.app.pid,
                                             error=error,
                                             traceback=trace_info,
                                             request=request_info,
                                             webroot=sickrage.app.config.web_root))

    def get_current_user(self):
        try:
            access_token = self.get_secure_cookie('_sr_access_token')
            refresh_token = self.get_secure_cookie('_sr_refresh_token')
            if not all([access_token, refresh_token]):
                return

            try:
                return sickrage.app.oidc_client.decode_token(access_token.decode("utf-8"), sickrage.app.oidc_client.certs())
            except (KeycloakClientError, ExpiredSignatureError):
                token = sickrage.app.oidc_client.refresh_token(refresh_token.decode("utf-8"))
                self.set_secure_cookie('_sr_access_token', token['access_token'])
                self.set_secure_cookie('_sr_refresh_token', token['refresh_token'])
                return sickrage.app.oidc_client.decode_token(token['access_token'], sickrage.app.oidc_client.certs())
        except Exception as e:
            sickrage.app.log.debug('{!r}'.format(e))
            pass

    def render_string(self, template_name, **kwargs):
        template_kwargs = {
            'title': "",
            'header': "",
            'topmenu': "",
            'submenu': "",
            'controller': "home",
            'action': "index",
            'srPID': sickrage.app.pid,
            'srHttpsEnabled': sickrage.app.config.enable_https or bool(self.request.headers.get('X-Forwarded-Proto') == 'https'),
            'srHost': self.request.headers.get('X-Forwarded-Host', self.request.host.split(':')[0]),
            'srHttpPort': self.request.headers.get('X-Forwarded-Port', sickrage.app.config.web_port),
            'srHttpsPort': sickrage.app.config.web_port,
            'srHandleReverseProxy': sickrage.app.config.handle_reverse_proxy,
            'srThemeName': sickrage.app.config.theme_name,
            'srDefaultPage': sickrage.app.config.default_page,
            'srWebRoot': sickrage.app.config.web_root,
            'srLocale': self.get_user_locale().code,
            'srLocaleDir': sickrage.LOCALE_DIR,
            'srStartTime': self.startTime,
            'makoStartTime': time.time(),
            'overall_stats': None,
            'torrent_webui_url': helpers.torrent_webui_url(),
            'application': self.application,
            'request': self.request,
        }

        template_kwargs.update(self.get_template_namespace())
        template_kwargs.update(kwargs)

        try:
            return self.mako_lookup.get_template(template_name).render_unicode(**template_kwargs)
        except Exception:
            kwargs['title'] = _('HTTP Error 500')
            kwargs['header'] = _('HTTP Error 500')
            kwargs['backtrace'] = RichTraceback()
            template_kwargs.update(kwargs)

            sickrage.app.log.error("%s: %s" % (str(kwargs['backtrace'].error.__class__.__name__), kwargs['backtrace'].error))

            return self.mako_lookup.get_template('/errors/500.mako').render_unicode(**template_kwargs)

    def render(self, template_name, **kwargs):
        return self.write(self.render_string(template_name, **kwargs))

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

    def redirect(self, url, permanent=True, status=None):
        if sickrage.app.config.web_root not in url:
            url = urljoin(sickrage.app.config.web_root + '/', url.lstrip('/'))
        super(BaseHandler, self).redirect(url, permanent, status)

    def previous_url(self):
        url = urlparse(self.request.headers.get("referer", "/{}/".format(sickrage.app.config.default_page)))
        return url._replace(scheme="", netloc="").geturl()

    def _genericMessage(self, subject, message):
        return self.render(
            "/generic_message.mako",
            message=message,
            subject=subject,
            title="",
            controller='root',
            action='genericmessage'
        )

    def get_url(self, url):
        if sickrage.app.config.web_root not in url:
            url = urljoin(sickrage.app.config.web_root + '/', url.lstrip('/'))
        url = urljoin("{}://{}".format(self.request.protocol, self.request.host), url)
        return url

    def run_task(self, f, *args, **kwargs):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            threading.currentThread().setName('TORNADO')
            return f(*args, **kwargs)

        return sickrage.app.io_loop.run_in_executor(None, functools.partial(wrapper, *args, **kwargs))
