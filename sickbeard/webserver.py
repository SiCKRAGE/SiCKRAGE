# -*- coding: utf-8 -*-

# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import logging
import os
import signal

import tornado
import tornado.autoreload
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application, StaticFileHandler, RedirectHandler

import helpers
import sickbeard
import sickbeard.core
from sickbeard.helpers import create_https_certificates, generateApiKey
from webapi import ApiHandler, KeyHandler
from webroutes import route
from webviews import LoginHandler, LogoutHandler, CalendarHandler

class StaticImageHandler(StaticFileHandler):
    def initialize(self, path, default_filename=None):
        super(StaticImageHandler, self).initialize(path, default_filename)

    def get(self, path, include_body=True):
        # image cache check
        self.root = (self.root, os.path.join(sickbeard.CACHE_DIR, 'images'))[
            os.path.exists(os.path.normpath(os.path.join(sickbeard.CACHE_DIR, 'images', path)))
        ]

        return super(StaticImageHandler, self).get(path, include_body)


class SRWebServer(object):
    def __init__(self, **kwargs):
        self.running = True
        self.io_loop = IOLoop.instance()

        self.options = {}
        self.options.setdefault('port', 8081)
        self.options.setdefault('host', '0.0.0.0')
        self.options.setdefault('log_dir', None)
        self.options.setdefault('username', '')
        self.options.setdefault('password', '')
        self.options.setdefault('web_root', '/')
        self.options.setdefault('stop_timeout', 3)
        self.options.update(kwargs)

        # video root
        if sickbeard.ROOT_DIRS:
            root_dirs = sickbeard.ROOT_DIRS.split('|')
            self.video_root = root_dirs[int(root_dirs[0]) + 1]
        else:
            self.video_root = None

        # web root
        if self.options[b'web_root']:
            sickbeard.WEB_ROOT = self.options[b'web_root'] = ('/' + self.options[b'web_root'].lstrip('/').strip('/'))

        # api root
        if not sickbeard.API_KEY:
            sickbeard.API_KEY = generateApiKey()
        self.options[b'api_root'] = r'%s/api/%s' % (sickbeard.WEB_ROOT, sickbeard.API_KEY)

        # tornado setup
        self.enable_https = self.options[b'enable_https']
        self.https_cert = self.options[b'https_cert']
        self.https_key = self.options[b'https_key']

        if self.enable_https:
            # If either the HTTPS certificate or key do not exist, make some self-signed ones.
            if not (self.https_cert and os.path.exists(self.https_cert)) or not (
                        self.https_key and os.path.exists(self.https_key)):
                if not create_https_certificates(self.https_cert, self.https_key):
                    logging.info("Unable to create CERT/KEY files, disabling HTTPS")
                    sickbeard.ENABLE_HTTPS = False
                    self.enable_https = False

            if not (os.path.exists(self.https_cert) and os.path.exists(self.https_key)):
                logging.warning("Disabled HTTPS because of missing CERT and KEY files")
                sickbeard.ENABLE_HTTPS = False
                self.enable_https = False

        # Load the app
        self.app = Application([],
                               debug=sickbeard.DEBUG,
                               autoreload=False,
                               gzip=sickbeard.WEB_USE_GZIP,
                               xheaders=sickbeard.HANDLE_REVERSE_PROXY,
                               cookie_secret=sickbeard.WEB_COOKIE_SECRET,
                               login_url='%s/login/' % self.options[b'web_root'],
                               )

        # Main Handlers
        self.app.add_handlers('.*$', [
            # webapi handler
            (r'%s(/?.*)' % self.options[b'api_root'], ApiHandler),

            # webapi key retrieval
            (r'%s/getkey(/?.*)' % self.options[b'web_root'], KeyHandler),

            # webapi builder redirect
            (r'%s/api/builder' % self.options[b'web_root'], RedirectHandler,
             {"url": self.options[b'web_root'] + '/apibuilder/'}),

            # webui login/logout handlers
            (r'%s/login(/?)' % self.options[b'web_root'], LoginHandler),
            (r'%s/logout(/?)' % self.options[b'web_root'], LogoutHandler),

            # webui handlers
        ] + route.get_routes(self.options[b'web_root']))

        # Web calendar handler (Needed because option Unprotected calendar)
        self.app.add_handlers('.*$', [
            (r'%s/calendar' % self.options[b'web_root'], CalendarHandler),
        ])

        # Static File Handlers
        self.app.add_handlers(".*$", [
            # favicon
            (r'%s/(favicon\.ico)' % self.options[b'web_root'], StaticFileHandler,
             {"path": os.path.join(self.options[b'gui_root'], 'images/ico/favicon.ico')}),

            # images
            (r'%s.*?/images/(.*)' % self.options[b'web_root'], StaticImageHandler,
             {"path": os.path.join(self.options[b'gui_root'], 'images')}),

            # css
            (r'%s/css/(.*)' % self.options[b'web_root'], StaticFileHandler,
             {"path": os.path.join(self.options[b'gui_root'], 'css')}),

            # javascript
            (r'%s/js/(.*)' % self.options[b'web_root'], StaticFileHandler,
             {"path": os.path.join(self.options[b'gui_root'], 'js')}),

            # videos
        ] + [(r'%s/videos/(.*)' % self.options[b'web_root'], StaticFileHandler,
              {"path": self.video_root})])

        # daemonize sickrage
        if sickbeard.DAEMONIZE:
            import daemon
            ctx = daemon.DaemonContext()
            ctx.open()

        # write sickrage pidfile
        if sickbeard.CREATEPID:
            with file(sickbeard.PIDFILE, 'w+') as pf:
                pf.write(str(os.getpid()))

    def start(self):
        try:
            self.server = HTTPServer(self.app)
            if self.enable_https:
                self.server.ssl_options = {"certfile": self.https_cert, "keyfile": self.https_key}
            self.server.listen(self.options[b'port'], self.options[b'host'])

            logging.info(
                    "Starting SiCKRAGE web server on [{}://{}:{}/]".format(
                            ('http', 'https')[self.enable_https], helpers.get_lan_ip(), self.options[b'port']
                    ))

            # callback to fire sickrage threads
            self.io_loop.add_callback(sickbeard.core.start)

            # start IOLoop
            self.io_loop.start()
        except KeyboardInterrupt:
            self.server_shutdown()
        except Exception as e:
            logging.info("Tornado failed to start: {}".format(e))
        finally:
            logging.info("SiCKRAGE has shutdown!")

    @staticmethod
    def remove_pid_file():
        try:
            if os.path.exists(sickbeard.PIDFILE):
                os.remove(sickbeard.PIDFILE)
        except (IOError, OSError):
            pass

    def server_restart(self):
        logging.info('SiCKRAGE is restarting!')
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        tornado.autoreload.add_reload_hook(self.server_shutdown)
        tornado.autoreload.start()
        tornado.autoreload._reload()

    def server_shutdown(self):
        # shutdown tornado
        self.server.stop()
        if self.running:
            logging.info('TORNADO is now shutting down!')
            self.io_loop.stop()

        # if run as daemon delete the pidfile
        if sickbeard.DAEMONIZE and sickbeard.PIDFILE:
            self.remove_pid_file()

        # shutdown sickrage
        if sickbeard.STARTED:
            logging.info('SiCKRAGE is now shutting down!')
            sickbeard.core.halt()
            sickbeard.core.saveall()

        # shutown logging
        logging.shutdown()