from __future__ import unicode_literals

import os
import threading
import sickbeard

from sickbeard.webserve import LoginHandler, LogoutHandler, CalendarHandler
from sickbeard.webapi import ApiHandler, KeyHandler
import logging
from sickbeard.helpers import create_https_certificates, generateApiKey
from tornado.web import Application, StaticFileHandler, RedirectHandler
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.routes import route

from sickrage.helper.encoding import ek

class StaticImageHandler(StaticFileHandler):

    def initialize(self, path, default_filename=None):
        super(StaticImageHandler, self).initialize(path, default_filename)

    def get(self, path, include_body=True):
        # image cache check
        self.root = (self.root, os.path.join(sickbeard.CACHE_DIR, 'images'))[
            os.path.exists(os.path.normpath(os.path.join(sickbeard.CACHE_DIR, 'images', path)))
        ]

        return super(StaticImageHandler, self).get(path, include_body)

class SRWebServer(threading.Thread):
    def __init__(self, options={}, io_loop=None):
        threading.Thread.__init__(self)
        self.name = "TORNADO"
        self.alive = True

        self.io_loop = io_loop or IOLoop.current()

        self.options = options
        self.options.setdefault('port', 8081)
        self.options.setdefault('host', '0.0.0.0')
        self.options.setdefault('log_dir', None)
        self.options.setdefault('username', '')
        self.options.setdefault('password', '')
        self.options.setdefault('web_root', '/')
        assert isinstance(self.options[b'port'], int)
        assert 'gui_root' in self.options

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
            if not (self.https_cert and ek(os.path.exists, self.https_cert)) or not (
                        self.https_key and ek(os.path.exists, self.https_key)):
                if not create_https_certificates(self.https_cert, self.https_key):
                    logging.info("Unable to create CERT/KEY files, disabling HTTPS")
                    sickbeard.ENABLE_HTTPS = False
                    self.enable_https = False

            if not (os.path.exists(self.https_cert) and ek(os.path.exists, self.https_key)):
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
             {"path": ek(os.path.join, self.options[b'gui_root'], 'images/ico/favicon.ico')}),

            # images
            (r'%s.*?/images/(.*)' % self.options[b'web_root'], StaticImageHandler,
             {"path": ek(os.path.join, self.options[b'gui_root'], 'images')}),

            # css
            (r'%s/css/(.*)' % self.options[b'web_root'], StaticFileHandler,
             {"path": ek(os.path.join, self.options[b'gui_root'], 'css')}),

            # javascript
            (r'%s/js/(.*)' % self.options[b'web_root'], StaticFileHandler,
             {"path": ek(os.path.join, self.options[b'gui_root'], 'js')}),

            # videos
        ] + [(r'%s/videos/(.*)' % self.options[b'web_root'], StaticFileHandler,
              {"path": self.video_root})])

    def run(self):
        protocol = 'http'
        self.server = HTTPServer(self.app)

        if self.enable_https:
            protocol = 'https'
            self.server.ssl_options={"certfile": self.https_cert, "keyfile": self.https_key}

        logging.info("Starting SiCKRAGE web server on [{}://{}:{}/]".format(protocol, self.options[b'host'],
                                                                           self.options[b'port']))

        try:
            self.server.listen(self.options[b'port'], self.options[b'host'])
        except:
            logging.info("Could not start webserver on port %s, already in use!" % self.options[b'port'])
            os._exit(1)

        if sickbeard.LAUNCH_BROWSER and not sickbeard.DAEMONIZE:
            self.io_loop.add_callback(sickbeard.launchBrowser, protocol, sickbeard.WEB_PORT, sickbeard.WEB_ROOT)

        try:
            self.io_loop.start()
            self.io_loop.close(True)
        except (IOError, ValueError):
            pass

    def shutDown(self):
        self.alive = False
        self.io_loop.stop()
