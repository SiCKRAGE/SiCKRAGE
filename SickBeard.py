#!/usr/bin/env python2
# -*- coding: utf-8 -*-
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

from __future__ import print_function, unicode_literals

import getopt
import os
import sys
import threading
import traceback


class SickRage(object):
    def __init__(self):
        from time import strptime
        strptime("2012", "%Y")

        threading.currentThread().name = 'MAIN'

        # daemon constants
        sickbeard.DAEMONIZE = False
        sickbeard.CREATEPID = False
        sickbeard.PIDFILE = ''

        # webserver constants
        sickbeard.WEB_NOLAUNCH = False

        # do some preliminary stuff
        sickbeard.MY_FULLNAME = os.path.normpath(os.path.abspath(__file__))
        sickbeard.MY_NAME = os.path.basename(sickbeard.MY_FULLNAME)
        sickbeard.PROG_DIR = os.path.dirname(sickbeard.MY_FULLNAME)
        sickbeard.DATA_DIR = sickbeard.PROG_DIR
        sickbeard.MY_ARGS = sys.argv[1:]

        # Need console logging for SickBeard.py and SickBeard-console.exe
        self.consoleLogging = (not hasattr(sys, "frozen")) or (sickbeard.MY_NAME.lower().find('-console') > 0)

        try:
            self.opts, _ = getopt.getopt(
                    sys.argv[1:], "hqdp::",
                    ['help', 'quiet', 'nolaunch', 'daemon', 'pidfile=', 'port=', 'datadir=', 'config=', 'noresize']
            )
        except getopt.GetoptError:
            sys.exit(self.help_message())

        for o, a in self.opts:
            # Prints help message
            if o in ('-h', '--help'):
                sys.exit(self.help_message())

            # For now we'll just silence the logging
            if o in ('-q', '--quiet'):
                self.consoleLogging = False

            # Suppress launching web browser
            # Needed for OSes without default browser assigned
            # Prevent duplicate browser window when restarting in the app
            if o in ('--nolaunch',):
                sickbeard.WEB_NOLAUNCH = True

            # Override default/configured port
            if o in ('-p', '--port'):
                try:
                    sickbeard.WEB_PORT = int(a)
                except ValueError:
                    sys.exit("Port: " + str(a) + " is not a number. Exiting.")

            # Run as a double forked daemon
            if o in ('-d', '--daemon'):
                sickbeard.DAEMONIZE = True
                sickbeard.WEB_NOLAUNCH = True
                self.consoleLogging = False

                if sys.platform == 'win32' or sys.platform == 'darwin':
                    sickbeard.DAEMONIZE = False

            # Write a pidfile if requested
            if o in ('--pidfile',):
                sickbeard.CREATEPID = True
                sickbeard.PIDFILE = str(a)

                # If the pidfile already exists, sickbeard may still be running, so exit
                if os.path.exists(sickbeard.PIDFILE):
                    sys.exit("PID file: " + sickbeard.PIDFILE + " already exists. Exiting.")

            # Specify folder to load the config file from
            if o in ('--config',):
                sickbeard.CONFIG_FILE = os.path.abspath(a)

            # Specify folder to use as the data dir
            if o in ('--datadir',):
                sickbeard.DATA_DIR = os.path.abspath(a)

            # Prevent resizing of the banner/posters even if PIL is installed
            if o in ('--noresize',):
                sickbeard.NO_RESIZE = True

    def help_message(self):
        """
        print help message for commandline options
        """

        help_msg = "\n"
        help_msg += "Usage: " + sickbeard.MY_FULLNAME + " <option> <another option>\n"
        help_msg += "\n"
        help_msg += "Options:\n"
        help_msg += "\n"
        help_msg += "    -h          --help              Prints this message\n"
        help_msg += "    -q          --quiet             Disables logging to console\n"
        help_msg += "                --nolaunch          Suppress launching web browser on startup\n"

        if sys.platform == 'win32' or sys.platform == 'darwin':
            help_msg += "    -d          --daemon            Running as real daemon is not supported on Windows\n"
            help_msg += "                                    On Windows and MAC, --daemon is substituted with: --quiet --nolaunch\n"
        else:
            help_msg += "    -d          --daemon            Run as double forked daemon (includes options --quiet --nolaunch)\n"
            help_msg += "                --pidfile=<path>    Combined with --daemon creates a pidfile (full path including filename)\n"

        help_msg += "    -p <port>   --port=<port>       Override default/configured port to listen on\n"
        help_msg += "                --datadir=<path>    Override folder (full path) as location for\n"
        help_msg += "                                    storing database, configfile, cache, logfiles \n"
        help_msg += "                                    Default: " + sickbeard.PROG_DIR + "\n"
        help_msg += "                --config=<path>     Override config filename (full path including filename)\n"
        help_msg += "                                    to load configuration from \n"
        help_msg += "                                    Default: config.ini in " + sickbeard.PROG_DIR + " or --datadir location\n"
        help_msg += "                --noresize          Prevent resizing of the banner/posters even if PIL is installed\n"

        return help_msg

    def start(self):
        from sickrage.helper import encoding
        encoding.encodingInit()

        # The pidfile is only useful in daemon mode, make sure we can write the file properly
        if sickbeard.CREATEPID:
            if sickbeard.DAEMONIZE:
                pid_dir = os.path.dirname(sickbeard.PIDFILE)
                if not os.access(pid_dir, os.F_OK):
                    sys.exit("PID dir: " + pid_dir + " doesn't exist. Exiting.")
                if not os.access(pid_dir, os.W_OK):
                    sys.exit("PID dir: " + pid_dir + " must be writable (write permissions). Exiting.")

            else:
                sickbeard.CREATEPID = False
                if self.consoleLogging:
                    sys.stdout.write("Not running in daemon mode. PID file creation disabled.\n")

        # If they don't specify a config file then put it in the data dir
        if not sickbeard.CONFIG_FILE:
            sickbeard.CONFIG_FILE = os.path.join(sickbeard.DATA_DIR, "config.ini")

        # Make sure that we can create the data dir
        if not os.access(sickbeard.DATA_DIR, os.F_OK):
            try:
                os.makedirs(sickbeard.DATA_DIR, 0o744)
            except os.error:
                raise SystemExit("Unable to create datadir '" + sickbeard.DATA_DIR + "'")

        # Make sure we can write to the data dir
        if not os.access(sickbeard.DATA_DIR, os.W_OK):
            raise SystemExit("Datadir must be writeable '" + sickbeard.DATA_DIR + "'")

        # Make sure we can write to the config file
        if not os.access(sickbeard.CONFIG_FILE, os.W_OK):
            if os.path.isfile(sickbeard.CONFIG_FILE):
                raise SystemExit("Config file '" + sickbeard.CONFIG_FILE + "' must be writeable.")
            elif not os.access(os.path.dirname(sickbeard.CONFIG_FILE), os.W_OK):
                raise SystemExit(
                        "Config file root dir '" + os.path.dirname(sickbeard.CONFIG_FILE) + "' must be writeable.")

        # initialize and startup sickrage
        if sickbeard.core.initialize(self.consoleLogging):
            sickbeard.WEB_SERVER.start()


def install_pip():
    print("Downloading pip ...")
    import urllib2

    url = "https://bootstrap.pypa.io/get-pip.py"
    file_name = url.split('/')[-1]
    u = urllib2.urlopen(url)
    f = open(file_name, 'wb')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print("Downloading: %s Bytes: %s" % (file_name, file_size))
    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break
        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8) * (len(status) + 1)
        print(status),
    f.close()
    print("Installing pip ...")
    import subprocess
    subprocess.call([sys.executable, 'get-pip.py'])

    import os
    print("Cleaning up downloaded pip files")
    os.remove("get-pip.py")

if __name__ == "__main__":
    if sys.version_info < (2, 7):
        print("Sorry, SiCKRAGE requires Python 2.7+")
        sys.exit(1)

    try:
        # append app main folder to system path
        sys.path.append(os.path.join(os.path.dirname(__file__), 'sickbeard'))

        try:
            import pip

            print("Upgrading pip ...")
            pip.main(['install', '-q', '-U', 'pip'])
        except ImportError:
            install_pip()
            import pip

        print("Installing/Upgrading SiCKRAGE required libs, please stand by ...")
        pip.main(['install', '-q', '-U', '-r', os.path.join(os.path.dirname(__file__), 'requirements.txt')])

        print("Installing/Upgrading SiCKRAGE optional libs, please stand by ...")
        try:
            pip.main(
                    ['install', '-q', '-U', '-r', os.path.join(os.path.dirname(__file__), 'requirements-optional.txt')])
        except:
            pass

        # start main thread
        import sickbeard
        import sickbeard.core

        SickRage().start()
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback)
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        sys.exit(1)
    sys.exit(0)
