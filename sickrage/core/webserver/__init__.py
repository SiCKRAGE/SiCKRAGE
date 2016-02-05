#!/usr/bin/env python2

# Author: echel0n <sickrage.tv@gmail.com>
# URL: http://www.github.com/sickragetv/sickrage/
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import os
import threading
import webbrowser

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application, RedirectHandler, StaticFileHandler

import sickrage
from core.helpers import create_https_certificates, generateApiKey
from core.webserver.api import ApiHandler, KeyHandler
from core.webserver.routes import Route
from core.webserver.views import CalendarHandler, LoginHandler, LogoutHandler


def launch_browser(protocol=None, startport=None, web_root=None):
    browserurl = '{}://localhost:{}{}/home/'.format(protocol or 'http', startport or 8081, web_root or '/')

    try:
        print("Launching browser window")

        try:
            webbrowser.open(browserurl, 2, 1)
        except webbrowser.Error:
            webbrowser.open(browserurl, 1, 1)
    except webbrowser.Error:
        print("Unable to launch a browser")


class StaticImageHandler(StaticFileHandler):
    def initialize(self, path, default_filename=None):
        super(StaticImageHandler, self).initialize(path, default_filename)

    def get(self, path, include_body=True):
        # image cache check
        self.root = (self.root, os.path.join(sickrage.srCore.CONFIG.CACHE_DIR, 'images'))[
            os.path.exists(os.path.normpath(os.path.join(sickrage.srCore.CONFIG.CACHE_DIR, 'images', path)))
        ]

        # image css check
        self.root = (self.root, os.path.join(sickrage.srCore.CONFIG.GUI_DIR, 'css', 'lib', 'images'))[
            os.path.exists(os.path.normpath(os.path.join(sickrage.srCore.CONFIG.GUI_DIR, 'css', 'lib', 'images', path)))
        ]

        return super(StaticImageHandler, self).get(path, include_body)


class srWebServer(object):
    def __init__(self):
        self.io_loop = IOLoop.instance()
        self.running = True
        self.restart = False
        self.open_browser = False

        self.port = sickrage.srCore.CONFIG.WEB_PORT
        self.host = sickrage.srCore.CONFIG.WEB_HOST

        # video root
        if sickrage.srCore.CONFIG.ROOT_DIRS:
            root_dirs = sickrage.srCore.CONFIG.ROOT_DIRS.split('|')
            self.video_root = root_dirs[int(root_dirs[0]) + 1]
        else:
            self.video_root = None

        # web root
        if sickrage.srCore.CONFIG.WEB_ROOT:
            sickrage.srCore.CONFIG.WEB_ROOT = sickrage.srCore.CONFIG.WEB_ROOT = ('/' + sickrage.srCore.CONFIG.WEB_ROOT.lstrip('/').strip('/'))

        # api root
        if not sickrage.srCore.CONFIG.API_KEY:
            sickrage.srCore.CONFIG.API_KEY = generateApiKey()
        self.api_root = r'%s/api/%s' % (sickrage.srCore.CONFIG.WEB_ROOT, sickrage.srCore.CONFIG.API_KEY)

        # tornado setup
        if sickrage.srCore.CONFIG.ENABLE_HTTPS:
            # If either the HTTPS certificate or key do not exist, make some self-signed ones.
            if not (sickrage.srCore.CONFIG.HTTPS_CERT and os.path.exists(sickrage.srCore.CONFIG.HTTPS_CERT)) or not (
                        sickrage.srCore.CONFIG.HTTPS_KEY and os.path.exists(sickrage.srCore.CONFIG.HTTPS_KEY)):
                if not create_https_certificates(sickrage.srCore.CONFIG.HTTPS_CERT, sickrage.srCore.CONFIG.HTTPS_KEY):
                    sickrage.srCore.LOGGER.info("Unable to create CERT/KEY files, disabling HTTPS")
                    sickrage.srCore.CONFIG.ENABLE_HTTPS = False

            if not (os.path.exists(sickrage.srCore.CONFIG.HTTPS_CERT) and os.path.exists(sickrage.srCore.CONFIG.HTTPS_KEY)):
                sickrage.srCore.LOGGER.warning("Disabled HTTPS because of missing CERT and KEY files")
                sickrage.srCore.CONFIG.ENABLE_HTTPS = False

        # Load the app
        self.app = Application([],
                               debug=sickrage.srCore.CONFIG.DEBUG,
                               autoreload=False,
                               gzip=sickrage.srCore.CONFIG.WEB_USE_GZIP,
                               xheaders=sickrage.srCore.CONFIG.HANDLE_REVERSE_PROXY,
                               cookie_secret=sickrage.srCore.CONFIG.WEB_COOKIE_SECRET,
                               login_url='%s/login/' % sickrage.srCore.CONFIG.WEB_ROOT,
                               )

        # Main Handlers
        self.app.add_handlers('.*$', [
            # webapi handler
            (r'%s(/?.*)' % self.api_root, ApiHandler),

            # webapi key retrieval
            (r'%s/getkey(/?.*)' % sickrage.srCore.CONFIG.WEB_ROOT, KeyHandler),

            # webapi builder redirect
            (r'%s/api/builder' % sickrage.srCore.CONFIG.WEB_ROOT, RedirectHandler,
             {"url": sickrage.srCore.CONFIG.WEB_ROOT + '/apibuilder/'}),

            # webui login/logout handlers
            (r'%s/login(/?)' % sickrage.srCore.CONFIG.WEB_ROOT, LoginHandler),
            (r'%s/logout(/?)' % sickrage.srCore.CONFIG.WEB_ROOT, LogoutHandler),

            # webui handlers
        ] + Route.get_routes(sickrage.srCore.CONFIG.WEB_ROOT))

        # Web calendar handler (Needed because option Unprotected calendar)
        self.app.add_handlers('.*$', [
            (r'%s/calendar' % sickrage.srCore.CONFIG.WEB_ROOT, CalendarHandler),
        ])

        # Static File Handlers
        self.app.add_handlers(".*$", [
            # favicon
            (r'%s/(favicon\.ico)' % sickrage.srCore.CONFIG.WEB_ROOT, StaticFileHandler,
             {"path": os.path.join(sickrage.srCore.CONFIG.GUI_DIR, 'images/ico/favicon.ico')}),

            # images
            (r'%s.*?/images/(.*)' % sickrage.srCore.CONFIG.WEB_ROOT, StaticImageHandler,
             {"path": os.path.join(sickrage.srCore.CONFIG.GUI_DIR, 'images')}),

            # css
            (r'%s/css/(.*)' % sickrage.srCore.CONFIG.WEB_ROOT, StaticFileHandler,
             {"path": os.path.join(sickrage.srCore.CONFIG.GUI_DIR, 'css')}),

            # javascript
            (r'%s/js/(.*)' % sickrage.srCore.CONFIG.WEB_ROOT, StaticFileHandler,
             {"path": os.path.join(sickrage.srCore.CONFIG.GUI_DIR, 'js')}),

            # videos
        ] + [(r'%s/videos/(.*)' % sickrage.srCore.CONFIG.WEB_ROOT, StaticFileHandler,
              {"path": self.video_root})])

    def start(self):
        threading.currentThread().setName("TORNADO")

        try:
            self.server = HTTPServer(self.app)
            if sickrage.srCore.CONFIG.ENABLE_HTTPS:
                self.server.ssl_options = {"certfile": sickrage.srCore.CONFIG.HTTPS_CERT, "keyfile": sickrage.srCore.CONFIG.HTTPS_KEY}
            self.server.listen(self.port, self.host)

            # launch browser window
            if self.open_browser:
                threading.Thread(None, lambda: launch_browser(('http', 'https')[sickrage.srCore.CONFIG.ENABLE_HTTPS],
                                                              sickrage.srCore.CONFIG.WEB_PORT, sickrage.srCore.CONFIG.WEB_ROOT)).start()

            from core.helpers import get_lan_ip
            sickrage.srCore.CONFIG.STARTED = True
            print("SiCKRAGE STARTED :: VERSION:[{}] CONFIG:[{}] URL:[{}://{}:{}/]".format(
                sickrage.srCore.VERSION,
                sickrage.srCore.CONFIG_FILE,
                ('http', 'https')[sickrage.srCore.CONFIG.ENABLE_HTTPS],
                get_lan_ip(),
                sickrage.srCore.CONFIG.WEB_PORT)
            )

            self.io_loop.start()
        except (KeyboardInterrupt, SystemExit) as e:
            sickrage.srCore.LOGGER.info('PERFORMING SHUTDOWN')
        except Exception as e:
            sickrage.srCore.LOGGER.info("TORNADO failed to start: {}".format(e.message))
        finally:
            self.server_shutdown()
            sickrage.srCore.LOGGER.shutdown()

    @staticmethod
    def remove_pid_file():
        try:
            if os.path.exists(sickrage.srCore.CONFIG.PIDFILE):
                os.remove(sickrage.srCore.CONFIG.PIDFILE)
        except (IOError, OSError):
            pass

    def server_restart(self):
        sickrage.srCore.LOGGER.info('PERFORMING RESTART')
        import tornado.autoreload
        tornado.autoreload.add_reload_hook(self.server_shutdown)
        tornado.autoreload.start()
        tornado.autoreload._reload()

    def server_shutdown(self):
        self.server.stop()
        if self.running:
            self.io_loop.stop()

        # shutdown sickrage
        if sickrage.srCore.STARTED:
            sickrage.srCore.halt()
            sickrage.srCore.save_all()

        if sickrage.srCore.CONFIG.DAEMONIZE and sickrage.srCore.CONFIG.PIDFILE:
            self.remove_pid_file()

        sickrage.srCore.LOGGER.info('SHUTDOWN/RESTART COMPLETED!')
