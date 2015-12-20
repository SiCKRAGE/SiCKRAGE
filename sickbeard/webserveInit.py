from __future__ import unicode_literals

import os
import sys
import time
import signal
import logging
import threading
import subprocess

import sickbeard
from sickbeard.webserve import LoginHandler, LogoutHandler, CalendarHandler, tornado
from sickbeard.webapi import ApiHandler, KeyHandler
from sickbeard.helpers import create_https_certificates, generateApiKey
from sickrage.helper.encoding import ek

import tornado.autoreload
from tornado.web import Application, StaticFileHandler, RedirectHandler
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.routes import route


class SRWebServer(object):
    def __init__(self, on_stop_request=lambda: None, on_ioloop_stop=lambda: None, **kwargs):
        #threading.Thread.name = self.name = "TORNADO"
        #self.alive = True

        self.io_loop = IOLoop.current()
        self.on_stop_request= on_stop_request
        self.on_ioloop_stop = on_ioloop_stop

        # signal handlers
        signal.signal(signal.SIGTERM, self.sigterm_handler)
        signal.signal(signal.SIGINT, self.sigterm_handler)

        self.options = {}
        self.options.setdefault('port', 8081)
        self.options.setdefault('host', '0.0.0.0')
        self.options.setdefault('log_dir', None)
        self.options.setdefault('username', '')
        self.options.setdefault('password', '')
        self.options.setdefault('web_root', '/')
        self.options.setdefault('stop_timeout', 3)
        self.options.update(kwargs)

        assert isinstance(self.options[b'port'], int)
        assert 'data_root' in self.options

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
             {"path": ek(os.path.join, self.options[b'data_root'], 'images/ico/favicon.ico')}),

            # images
            (r'%s/images/(.*)' % self.options[b'web_root'], StaticFileHandler,
             {"path": ek(os.path.join, self.options[b'data_root'], 'images')}),

            # cached images
            (r'%s/cache/images/(.*)' % self.options[b'web_root'], StaticFileHandler,
             {"path": ek(os.path.join, sickbeard.CACHE_DIR, 'images')}),

            # css
            (r'%s/css/(.*)' % self.options[b'web_root'], StaticFileHandler,
             {"path": ek(os.path.join, self.options[b'data_root'], 'css')}),

            # javascript
            (r'%s/js/(.*)' % self.options[b'web_root'], StaticFileHandler,
             {"path": ek(os.path.join, self.options[b'data_root'], 'js')}),

            # videos
        ] + [(r'%s/videos/(.*)' % self.options[b'web_root'], StaticFileHandler,
              {"path": self.video_root})])

    def start(self):
        protocol = 'http' if not sickbeard.ENABLE_HTTPS else 'https'

        try:
            # Clean up after update
            if sickbeard.GIT_NEWVER:
                toclean = ek(os.path.join, sickbeard.CACHE_DIR, 'mako')
                for root, dirs, files in ek(os.walk, toclean, topdown=False):
                    for name in files:
                        ek(os.remove, ek(os.path.join, root, name))
                    for name in dirs:
                        ek(os.rmdir, ek(os.path.join, root, name))
                sickbeard.GIT_NEWVER = False

            self.server = HTTPServer(self.app)
            if protocol == 'https':
                self.server.ssl_options={"certfile": self.https_cert, "keyfile": self.https_key}
            self.server.listen(self.options[b'port'], self.options[b'host'])

            self.io_loop = IOLoop.instance()
            tornado.autoreload.start(self.io_loop, 1000)
            tornado.autoreload.add_reload_hook(self.server_shutdown)

            # Launch browser
            if sickbeard.LAUNCH_BROWSER and not any([self.options[b'nolaunch'],self.options[b'daemonize']]):
                sickbeard.launchBrowser(protocol, self.options[b'port'], self.options[b'web_root'])

            logging.info(
                    "Starting SiCKRAGE web server on [{}://{}:{}/]".format(
                            protocol,self.options[b'host'],self.options[b'port']
            ))

            # callback to fire sickrage threads
            self.io_loop.add_callback(sickbeard.start)

            # start IOLoop
            self.io_loop.start()
        except Exception:
            logging.info("Tornado failed to start on port %s, already in use!" % self.options[b'port'])

    @staticmethod
    def ioloop_is_running():
        return IOLoop.instance()._running

    def remove_pid_file(self):
        try:
            if ek(os.path.exists, sickbeard.PIDFILE):
                ek(os.remove, sickbeard.PIDFILE)
        except (IOError, OSError):
            return False
        return True

    def sigterm_handler(self, signum, frame):
        logging.info("Signal %i caught, saving and exiting..." % int(signum))
        self.io_loop.add_callback_from_signal(self.server_shutdown)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)

    def server_shutdown(self):
        self.server.stop()
        if self.ioloop_is_running():
            logging.info('Tornado web server shutting down in %s seconds', self.options[b'stop_timeout'])

            def ioloop_stop(self):
                if self.ioloop_is_running():
                    IOLoop.instance().stop()
                    self.on_ioloop_stop()

            IOLoop.instance().add_timeout(time.time() + self.options[b'stop_timeout'], ioloop_stop)

        # if run as daemon delete the pidfile
        if self.options[b'daemonize'] and self.options[b'pidfile']:
            self.remove_pid_file()

        sickbeard.halt()
        sickbeard.saveAll()
        logging.shutdown()