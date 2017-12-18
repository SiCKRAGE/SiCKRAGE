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
from sickrage.core.helpers import create_https_certificates, launch_browser
from sickrage.core.webserver.api import ApiHandler, KeyHandler
from sickrage.core.webserver.routes import Route
from sickrage.core.webserver.views import CalendarHandler, LoginHandler, LogoutHandler


class StaticImageHandler(StaticFileHandler):
    def initialize(self, path, default_filename=None):
        super(StaticImageHandler, self).initialize(path, default_filename)

    def get(self, path, include_body=True):
        # image cache check
        self.root = (self.root, os.path.join(sickrage.app.cache_dir, 'images'))[
            os.path.exists(os.path.normpath(os.path.join(sickrage.app.cache_dir, 'images', path)))
        ]

        return super(StaticImageHandler, self).get(path, include_body)


class WebServer(object):
    def __init__(self):
        super(WebServer, self).__init__()
        self.name = "TORNADO"
        self.daemon = True
        self.started = False
        self.video_root = None
        self.api_root = None
        self.app = None
        self.server = None

    def start(self):
        self.started = True

        # load languages
        tornado.locale.load_gettext_translations(sickrage.LOCALE_DIR, 'messages')

        # clear mako cache folder
        mako_cache = os.path.join(sickrage.app.cache_dir, 'mako')
        if os.path.isdir(mako_cache):
            shutil.rmtree(mako_cache)

        # video root
        if sickrage.app.config.root_dirs:
            root_dirs = sickrage.app.config.root_dirs.split('|')
            self.video_root = root_dirs[int(root_dirs[0]) + 1]

        # web root
        if sickrage.app.config.web_root:
            sickrage.app.config.web_root = sickrage.app.config.web_root = (
                '/' + sickrage.app.config.web_root.lstrip('/').strip('/'))

        # api root
        self.api_root = r'%s/api/%s' % (sickrage.app.config.web_root, sickrage.app.config.api_key)

        # tornado setup
        if sickrage.app.config.enable_https:
            # If either the HTTPS certificate or key do not exist, make some self-signed ones.
            if not (
                        sickrage.app.config.https_cert and os.path.exists(
                        sickrage.app.config.https_cert)) or not (
                        sickrage.app.config.https_key and os.path.exists(sickrage.app.config.https_key)):
                if not create_https_certificates(sickrage.app.config.https_cert,
                                                 sickrage.app.config.https_key):
                    sickrage.app.log.info("Unable to create CERT/KEY files, disabling HTTPS")
                    sickrage.app.config.enable_https = False

            if not (os.path.exists(sickrage.app.config.https_cert) and os.path.exists(
                    sickrage.app.config.https_key)):
                sickrage.app.log.warning("Disabled HTTPS because of missing CERT and KEY files")
                sickrage.app.config.enable_https = False

        # Load the app
        self.app = Application(
            [
                # api
                (r'%s(/?.*)' % self.api_root, ApiHandler),

                # redirect to web root
                (r"(?!%s)(.*)" % sickrage.app.config.web_root, RedirectHandler,
                 {"url": "%s/{0}" % sickrage.app.config.web_root}),

                # api key
                (r'%s/getkey(/?.*)' % sickrage.app.config.web_root, KeyHandler),

                # api builder
                (r'%s/api/builder' % sickrage.app.config.web_root, RedirectHandler,
                 {"url": sickrage.app.config.web_root + '/apibuilder/'}),

                # login
                (r'%s/login(/?)' % sickrage.app.config.web_root, LoginHandler),

                # logout
                (r'%s/logout(/?)' % sickrage.app.config.web_root, LogoutHandler),

                # calendar
                (r'%s/calendar' % sickrage.app.config.web_root, CalendarHandler),

                # favicon
                (r'%s/(favicon\.ico)' % sickrage.app.config.web_root, StaticFileHandler,
                 {"path": os.path.join(sickrage.app.config.gui_static_dir, 'images/favicon.ico')}),

                # images
                (r'%s/images/(.*)' % sickrage.app.config.web_root, StaticImageHandler,
                 {"path": os.path.join(sickrage.app.config.gui_static_dir, 'images')}),

                # css
                (r'%s/css/(.*)' % sickrage.app.config.web_root, StaticFileHandler,
                 {"path": os.path.join(sickrage.app.config.gui_static_dir, 'css')}),

                # scss
                (r'%s/scss/(.*)' % sickrage.app.config.web_root, StaticFileHandler,
                 {"path": os.path.join(sickrage.app.config.gui_static_dir, 'scss')}),

                # fonts
                (r'%s/fonts/(.*)' % sickrage.app.config.web_root, StaticFileHandler,
                 {"path": os.path.join(sickrage.app.config.gui_static_dir, 'fonts')}),

                # javascript
                (r'%s/js/(.*)' % sickrage.app.config.web_root, StaticFileHandler,
                 {"path": os.path.join(sickrage.app.config.gui_static_dir, 'js')}),

                # videos
                (r'%s/videos/(.*)' % sickrage.app.config.web_root, StaticFileHandler,
                 {"path": self.video_root}),
            ] + Route.get_routes(sickrage.app.config.web_root),
            debug=True,
            autoreload=False,
            gzip=sickrage.app.config.web_use_gzip,
            xheaders=sickrage.app.config.handle_reverse_proxy,
            cookie_secret=sickrage.app.config.web_cookie_secret,
            login_url='%s/login/' % sickrage.app.config.web_root)

        self.server = HTTPServer(self.app, no_keep_alive=True, io_loop=sickrage.app.io_loop)

        if sickrage.app.config.enable_https: self.server.ssl_options = {
            "certfile": sickrage.app.config.https_cert,
            "keyfile": sickrage.app.config.https_key
        }

        try:
            self.server.listen(sickrage.app.config.web_port, None)

            sickrage.app.log.info(
                "SiCKRAGE :: STARTED")
            sickrage.app.log.info(
                "SiCKRAGE :: VERSION:[{}]".format(sickrage.app.version_updater.version))
            sickrage.app.log.info(
                "SiCKRAGE :: CONFIG:[{}] [v{}]".format(sickrage.app.config_file, sickrage.app.config.config_version))
            sickrage.app.log.info(
                "SiCKRAGE :: URL:[{}://{}:{}/]".format(
                    ('http', 'https')[sickrage.app.config.enable_https],
                    sickrage.app.config.web_host, sickrage.app.config.web_port))

            # launch browser window
            if all([not sickrage.app.no_launch, sickrage.app.config.launch_browser]):
                threading.Thread(None,
                                 lambda: launch_browser(
                                     ('http', 'https')[sickrage.app.config.enable_https],
                                     sickrage.app.config.web_host,
                                     sickrage.app.config.web_port
                                 ), name="LAUNCH-BROWSER").start()
        except socket.error as e:
            sickrage.app.log.warning(e.strerror)
            raise SystemExit

    def shutdown(self):
        if self.started:
            self.started = False
            self.server.close_all_connections()
            self.server.stop()