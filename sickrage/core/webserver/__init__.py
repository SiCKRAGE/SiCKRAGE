# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
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
import shutil
import socket
import threading

import tornado.locale
from tornado.httpserver import HTTPServer
from tornado.web import Application, RedirectHandler, StaticFileHandler

import sickrage
from sickrage.core.helpers import create_https_certificates, generateApiKey, launch_browser
from sickrage.core.webserver.api import ApiHandler, KeyHandler
from sickrage.core.webserver.routes import Route
from sickrage.core.webserver.views import CalendarHandler, LoginHandler, LogoutHandler


class StaticImageHandler(StaticFileHandler):
    def initialize(self, path, default_filename=None):
        super(StaticImageHandler, self).initialize(path, default_filename)

    def get(self, path, include_body=True):
        # image cache check
        self.root = (self.root, os.path.join(sickrage.CACHE_DIR, 'images'))[
            os.path.exists(os.path.normpath(os.path.join(sickrage.CACHE_DIR, 'images', path)))
        ]

        return super(StaticImageHandler, self).get(path, include_body)


class srWebServer(threading.Thread):
    def __init__(self):
        super(srWebServer, self).__init__(name="TORNADO")
        self.daemon = True
        self.started = False
        self.video_root = None
        self.api_root = None
        self.app = None
        self.server = None

    def run(self):
        self.started = True

        # load languages
        tornado.locale.load_gettext_translations(sickrage.LOCALE_DIR, 'messages')

        # clear mako cache folder
        mako_cache = os.path.join(sickrage.CACHE_DIR, 'mako')
        if os.path.isdir(mako_cache):
            shutil.rmtree(mako_cache)

        # video root
        if sickrage.srCore.srConfig.ROOT_DIRS:
            root_dirs = sickrage.srCore.srConfig.ROOT_DIRS.split('|')
            self.video_root = root_dirs[int(root_dirs[0]) + 1]

        # web root
        if sickrage.srCore.srConfig.WEB_ROOT:
            sickrage.srCore.srConfig.WEB_ROOT = sickrage.srCore.srConfig.WEB_ROOT = (
                '/' + sickrage.srCore.srConfig.WEB_ROOT.lstrip('/').strip('/'))

        # api root
        if not sickrage.srCore.srConfig.API_KEY:
            sickrage.srCore.srConfig.API_KEY = generateApiKey()
        self.api_root = r'%s/api/%s' % (sickrage.srCore.srConfig.WEB_ROOT, sickrage.srCore.srConfig.API_KEY)

        # tornado setup
        if sickrage.srCore.srConfig.ENABLE_HTTPS:
            # If either the HTTPS certificate or key do not exist, make some self-signed ones.
            if not (
                        sickrage.srCore.srConfig.HTTPS_CERT and os.path.exists(
                        sickrage.srCore.srConfig.HTTPS_CERT)) or not (
                        sickrage.srCore.srConfig.HTTPS_KEY and os.path.exists(sickrage.srCore.srConfig.HTTPS_KEY)):
                if not create_https_certificates(sickrage.srCore.srConfig.HTTPS_CERT,
                                                 sickrage.srCore.srConfig.HTTPS_KEY):
                    sickrage.srCore.srLogger.info("Unable to create CERT/KEY files, disabling HTTPS")
                    sickrage.srCore.srConfig.ENABLE_HTTPS = False

            if not (os.path.exists(sickrage.srCore.srConfig.HTTPS_CERT) and os.path.exists(
                    sickrage.srCore.srConfig.HTTPS_KEY)):
                sickrage.srCore.srLogger.warning("Disabled HTTPS because of missing CERT and KEY files")
                sickrage.srCore.srConfig.ENABLE_HTTPS = False

        # Load the app
        self.app = Application(
            [
                # api
                (r'%s(/?.*)' % self.api_root, ApiHandler),

                # redirect to web root
                (r"(?!%s)(.*)" % sickrage.srCore.srConfig.WEB_ROOT, RedirectHandler,
                 {"url": "%s/{0}" % sickrage.srCore.srConfig.WEB_ROOT}),

                # api key
                (r'%s/getkey(/?.*)' % sickrage.srCore.srConfig.WEB_ROOT, KeyHandler),

                # api builder
                (r'%s/api/builder' % sickrage.srCore.srConfig.WEB_ROOT, RedirectHandler,
                 {"url": sickrage.srCore.srConfig.WEB_ROOT + '/apibuilder/'}),

                # login
                (r'%s/login(/?)' % sickrage.srCore.srConfig.WEB_ROOT, LoginHandler),

                # logout
                (r'%s/logout(/?)' % sickrage.srCore.srConfig.WEB_ROOT, LogoutHandler),

                # calendar
                (r'%s/calendar' % sickrage.srCore.srConfig.WEB_ROOT, CalendarHandler),

                # favicon
                (r'%s/(favicon\.ico)' % sickrage.srCore.srConfig.WEB_ROOT, StaticFileHandler,
                 {"path": os.path.join(sickrage.srCore.srConfig.GUI_STATIC_DIR, 'images/ico/favicon.ico')}),

                # images
                (r'%s/images/(.*)' % sickrage.srCore.srConfig.WEB_ROOT, StaticImageHandler,
                 {"path": os.path.join(sickrage.srCore.srConfig.GUI_STATIC_DIR, 'images')}),

                # css
                (r'%s/css/(.*)' % sickrage.srCore.srConfig.WEB_ROOT, StaticFileHandler,
                 {"path": os.path.join(sickrage.srCore.srConfig.GUI_STATIC_DIR, 'css')}),

                # scss
                (r'%s/scss/(.*)' % sickrage.srCore.srConfig.WEB_ROOT, StaticFileHandler,
                 {"path": os.path.join(sickrage.srCore.srConfig.GUI_STATIC_DIR, 'scss')}),

                # fonts
                (r'%s/fonts/(.*)' % sickrage.srCore.srConfig.WEB_ROOT, StaticFileHandler,
                 {"path": os.path.join(sickrage.srCore.srConfig.GUI_STATIC_DIR, 'fonts')}),

                # javascript
                (r'%s/js/(.*)' % sickrage.srCore.srConfig.WEB_ROOT, StaticFileHandler,
                 {"path": os.path.join(sickrage.srCore.srConfig.GUI_STATIC_DIR, 'js')}),

                # videos
                (r'%s/videos/(.*)' % sickrage.srCore.srConfig.WEB_ROOT, StaticFileHandler,
                 {"path": self.video_root}),
            ] + Route.get_routes(sickrage.srCore.srConfig.WEB_ROOT),
            debug=True,
            autoreload=False,
            gzip=sickrage.srCore.srConfig.WEB_USE_GZIP,
            xheaders=sickrage.srCore.srConfig.HANDLE_REVERSE_PROXY,
            cookie_secret=sickrage.srCore.srConfig.WEB_COOKIE_SECRET,
            login_url='%s/login/' % sickrage.srCore.srConfig.WEB_ROOT)

        self.server = HTTPServer(self.app, no_keep_alive=True)

        if sickrage.srCore.srConfig.ENABLE_HTTPS: self.server.ssl_options = {
            "certfile": sickrage.srCore.srConfig.HTTPS_CERT,
            "keyfile": sickrage.srCore.srConfig.HTTPS_KEY
        }

        try:
            self.server.listen(sickrage.WEB_PORT or sickrage.srCore.srConfig.WEB_PORT, None)

            sickrage.srCore.srLogger.info(
                "SiCKRAGE :: STARTED")
            sickrage.srCore.srLogger.info(
                "SiCKRAGE :: VERSION:[{}]".format(sickrage.srCore.VERSIONUPDATER.version))
            sickrage.srCore.srLogger.info(
                "SiCKRAGE :: CONFIG:[{}] [v{}]".format(sickrage.CONFIG_FILE, sickrage.srCore.srConfig.CONFIG_VERSION))
            sickrage.srCore.srLogger.info(
                "SiCKRAGE :: URL:[{}://{}:{}/]".format(
                    ('http', 'https')[sickrage.srCore.srConfig.ENABLE_HTTPS],
                    sickrage.srCore.srConfig.WEB_HOST, sickrage.srCore.srConfig.WEB_PORT))

            # launch browser window
            if all([not sickrage.NOLAUNCH, sickrage.srCore.srConfig.LAUNCH_BROWSER]):
                threading.Thread(None,
                                 lambda: launch_browser(
                                     ('http', 'https')[sickrage.srCore.srConfig.ENABLE_HTTPS],
                                     sickrage.srCore.srConfig.WEB_HOST,
                                     sickrage.srCore.srConfig.WEB_PORT
                                 ), name="LAUNCH-BROWSER").start()

            sickrage.io_loop.start()
        except socket.error as e:
            sickrage.srCore.srLogger.warning(e.strerror)
            raise SystemExit

    def shutdown(self):
        if self.started:
            self.started = False
            self.server.close_all_connections()
            self.server.stop()
            sickrage.io_loop.stop()
