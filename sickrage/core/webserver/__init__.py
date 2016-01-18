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
import subprocess
import sys
import threading
import webbrowser

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application, RedirectHandler, StaticFileHandler

import sickrage
from sickrage.core.helpers import create_https_certificates, generateApiKey
from sickrage.core.webserver.api import ApiHandler, KeyHandler
from sickrage.core.webserver.routes import route
from sickrage.core.webserver.views import CalendarHandler, LoginHandler, LogoutHandler


def launch_browser(protocol='http', startport=8081, web_root='/'):
    url = '{}://localhost:{}{}/home/'.format(protocol, startport, web_root)

    try:
        if sys.platform=='darwin':
            subprocess.Popen(['open', url])
        else:
            webbrowser.open_new_tab(url)
    except OSError:
        print 'Please open a browser on: '+url


class StaticImageHandler(StaticFileHandler):
    def initialize(self, path, default_filename=None):
        super(StaticImageHandler, self).initialize(path, default_filename)

    def get(self, path, include_body=True):
        # image cache check
        self.root = (self.root, os.path.join(sickrage.CACHE_DIR, 'images'))[
            os.path.exists(os.path.normpath(os.path.join(sickrage.CACHE_DIR, 'images', path)))
        ]

        # image css check
        self.root = (self.root, os.path.join(sickrage.GUI_DIR, 'css', 'lib', 'images'))[
            os.path.exists(os.path.normpath(os.path.join(sickrage.GUI_DIR, 'css', 'lib', 'images', path)))
        ]

        return super(StaticImageHandler, self).get(path, include_body)


class SRWebServer(object):
    def __init__(self, **kwargs):
        self.running = True
        self.restart = False
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
        if sickrage.ROOT_DIRS:
            root_dirs = sickrage.ROOT_DIRS.split('|')
            self.video_root = root_dirs[int(root_dirs[0]) + 1]
        else:
            self.video_root = None

        # web root
        if self.options[b'web_root']:
            sickrage.WEB_ROOT = self.options[b'web_root'] = ('/' + self.options[b'web_root'].lstrip('/').strip('/'))

        # api root
        if not sickrage.API_KEY:
            sickrage.API_KEY = generateApiKey()
        self.options[b'api_root'] = r'%s/api/%s' % (sickrage.WEB_ROOT, sickrage.API_KEY)

        # tornado setup
        self.enable_https = self.options[b'enable_https']
        self.https_cert = self.options[b'https_cert']
        self.https_key = self.options[b'https_key']

        if self.enable_https:
            # If either the HTTPS certificate or key do not exist, make some self-signed ones.
            if not (self.https_cert and os.path.exists(self.https_cert)) or not (
                        self.https_key and os.path.exists(self.https_key)):
                if not create_https_certificates(self.https_cert, self.https_key):
                    sickrage.LOGGER.info("Unable to create CERT/KEY files, disabling HTTPS")
                    sickrage.ENABLE_HTTPS = False
                    self.enable_https = False

            if not (os.path.exists(self.https_cert) and os.path.exists(self.https_key)):
                sickrage.LOGGER.warning("Disabled HTTPS because of missing CERT and KEY files")
                sickrage.ENABLE_HTTPS = False
                self.enable_https = False

        # Load the app
        self.app = Application([],
                               debug=sickrage.DEBUG,
                               autoreload=False,
                               gzip=sickrage.WEB_USE_GZIP,
                               xheaders=sickrage.HANDLE_REVERSE_PROXY,
                               cookie_secret=sickrage.WEB_COOKIE_SECRET,
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
        if sickrage.DAEMONIZE:
            import daemon
            ctx = daemon.DaemonContext()
            ctx.initgroups = False
            ctx.open()

        # write sickrage pidfile
        sickrage.PID = os.getpid()
        if sickrage.CREATEPID:
            with file(sickrage.PIDFILE, 'w+') as pf:
                pf.write(str(sickrage.PID))

        self.io_loop.add_callback(sickrage.Scheduler.start)

    def start(self):
        threading.currentThread().setName("TORNADO")

        try:
            self.server = HTTPServer(self.app)
            if self.enable_https:
                self.server.ssl_options = {"certfile": self.https_cert, "keyfile": self.https_key}
            self.server.listen(self.options[b'port'], self.options[b'host'])

            # start tornado web server
            from sickrage.core.helpers import get_lan_ip
            sickrage.LOGGER.info("Starting SiCKRAGE web server on [{}://{}:{}/]".format(
                            ('http', 'https')[sickrage.ENABLE_HTTPS], get_lan_ip(), sickrage.WEB_PORT))

            # launch browser window
            if sickrage.LAUNCH_BROWSER and not any([sickrage.WEB_NOLAUNCH, sickrage.DAEMONIZE]):
                sickrage.LOGGER.info("Launching browser window")
                threading.Thread(None, lambda: launch_browser(('http', 'https')[sickrage.ENABLE_HTTPS], sickrage.WEB_PORT, sickrage.WEB_ROOT)).start()

            sickrage.STARTED = True
            self.io_loop.start()
        except (KeyboardInterrupt, SystemExit) as e:
            sickrage.LOGGER.info('PERFORMING SHUTDOWN')
        except Exception as e:
            sickrage.LOGGER.info("TORNADO failed to start: {}".format(e))
        finally:
            self.server_shutdown()
            sickrage.LOGGER.shutdown()


    @staticmethod
    def remove_pid_file():
        try:
            if os.path.exists(sickrage.PIDFILE):
                os.remove(sickrage.PIDFILE)
        except (IOError, OSError):
            pass

    def server_restart(self):
        sickrage.LOGGER.info('PERFORMING RESTART')
        import tornado.autoreload
        tornado.autoreload.add_reload_hook(self.server_shutdown)
        tornado.autoreload.start()
        tornado.autoreload._reload()

    def server_shutdown(self):
        self.server.stop()
        if self.running:
            self.io_loop.stop()

        # shutdown sickrage
        if sickrage.STARTED:
            sickrage.core.halt()
            sickrage.core.saveall()

        if sickrage.DAEMONIZE and sickrage.PIDFILE:
            self.remove_pid_file()

        sickrage.LOGGER.info('SHUTDOWN/RESTART COMPLETED!')