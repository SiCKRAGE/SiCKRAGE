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

import ctypes
import getopt
import os
import sys
import threading
import time
import traceback

from requirements import install_pip, install_requirements

time.strptime("2012", "%Y")
srCore = None


def root_check():
    try:
        return not os.getuid() == 0
    except AttributeError:
        return not ctypes.windll.shell32.IsUserAnAdmin() != 0


def help_message(prog_dir):
    """
    LOGGER.info help message for commandline options
    """

    help_msg = "\n"
    help_msg += "Usage: SiCKRAGE <option> <another option>\n"
    help_msg += "\n"
    help_msg += "Options:\n"
    help_msg += "\n"
    help_msg += "    -h          --help              LOGGER.infos this message\n"
    help_msg += "    -q          --quiet             Disables logging to CONSOLE\n"
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
    help_msg += "                                    Default: " + prog_dir + "\n"
    help_msg += "                --config=<path>     Override config filename (full path including filename)\n"
    help_msg += "                                    to load configuration from \n"
    help_msg += "                                    Default: config.ini in " + prog_dir + " or --datadir location\n"
    help_msg += "                --noresize          Prevent resizing of the banner/posters even if PIL is installed\n"
    help_msg += "                --install-optional  Install optional pacakges from requirements folder\n"
    help_msg += "                --ssl               Enables ssl/https\n"
    help_msg += "                --debug             Enable debugging\n"

    return help_msg


def main():
    global srCore

    if sys.version_info < (2, 7):
        print("Sorry, SiCKRAGE requires Python 2.7+")
        sys.exit(1)

    # add sickrage module to python system path
    path = os.path.dirname(os.path.realpath(__file__))
    if path not in sys.path:
        sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

    # set thread name
    threading.currentThread().setName('MAIN')

    PROG_DIR = os.path.abspath(os.path.dirname(__file__))
    DATA_DIR = PROG_DIR

    APP_NAME = 'SiCKRAGE'
    CONFIG_FILE = "config.ini"

    try:
        opts, _ = getopt.getopt(
            sys.argv[1:], "hqdp::",
            ['help',
             'dev',
             'quiet',
             'nolaunch',
             'daemon',
             'pidfile=',
             'port=',
             'datadir=',
             'config=',
             'noresize',
             'install-optional',
             'ssl',
             'debug']
        )
    except getopt.GetoptError:
        sys.exit(help_message(PROG_DIR))

    # defaults
    PIDFILE = None
    CREATEPID = False
    DEVELOPER = False
    DAEMONIZE = False
    WEB_PORT = 8081
    INSTALL_OPTIONAL = False
    WEB_NOLAUNCH = False
    NO_RESIZE = False
    SSL = False
    DEBUG = False

    CONSOLE = not hasattr(sys, "frozen")

    for o, a in opts:
        # help message
        if o in ('-h', '--help'):
            sys.exit(help_message(PROG_DIR))

        # For now we'll just silence the logging
        if o in ('-q', '--quiet'):
            CONSOLE = False

        # developer mode
        if o in ('--dev',):
            print("!!! DEVELOPER MODE ENABLED !!!")
            DEVELOPER = True

        # Suppress launching web browser
        # Needed for OSes without default browser assigned
        # Prevent duplicate browser window when restarting in the app
        if o in ('--nolaunch',):
            WEB_NOLAUNCH = True

        # Override default/configured port
        if o in ('-p', '--port'):
            try:
                WEB_PORT = int(a)
            except ValueError:
                sys.exit("Port: " + str(a) + " is not a number. Exiting.")

        # Run as a double forked daemon
        if o in ('-d', '--daemon'):
            DAEMONIZE = True
            WEB_NOLAUNCH = True
            CONSOLE = False

            if sys.platform == 'win32' or sys.platform == 'darwin':
                DAEMONIZE = False

        # Write a pidfile if requested
        if o in ('--pidfile',):
            CREATEPID = True
            PIDFILE = str(a)

            # If the pidfile already exists, sickrage may still be running, so exit
            if os.path.exists(PIDFILE):
                sys.exit("PID file: " + PIDFILE + " already exists. Exiting.")

        # Specify folder to use as the data dir
        if o in ('--datadir',):
            DATA_DIR = os.path.abspath(a)

        # Specify folder to load the config file from
        if o in ('--config',):
            CONFIG_FILE = os.path.abspath(a)

        # Prevent resizing of the banner/posters even if PIL is installed
        if o in ('--noresize',):
            NO_RESIZE = True

        # Install optional packages from requirements folder
        if o in ('--install-optional',):
            INSTALL_OPTIONAL = True

        # Install ssl packages from requirements folder
        if o in ('--ssl',):
            SSL = True

        # Install ssl packages from requirements folder
        if o in ('--debug',):
            print("!!! DEBUGGING MODE ENABLED !!!")
            DEBUG = True

    # install/upgrade pip and ssl contexts for required/optional imports
    if not DEVELOPER:
        REQS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'requirements'))

        # install pip package manager
        install_pip(path=REQS_DIR, user=root_check())

        # install required packages
        install_requirements(path=REQS_DIR, optional=INSTALL_OPTIONAL, ssl=SSL, user=root_check())

    try:
        # daemonize sickrage
        if DAEMONIZE:
            import daemon
            ctx = daemon.DaemonContext()
            ctx.initgroups = False
            ctx.open()
        else:
            CREATEPID = False

        # create pid file
        PID = os.getpid()
        if CREATEPID:
            pid_dir = os.path.dirname(PIDFILE)
            if not os.access(pid_dir, os.F_OK):
                sys.exit("PID dir: " + pid_dir + " doesn't exist. Exiting.")
            if not os.access(pid_dir, os.W_OK):
                sys.exit("PID dir: " + pid_dir + " must be writable (write permissions). Exiting.")

            with file(PIDFILE, 'w+') as pf:
                pf.write(str(PID))

        import core
        print("SiCKRAGE INITIALIZING ...")
        srCore = core.srCore(CONFIG_FILE, PROG_DIR, DATA_DIR, PID)
        srCore.start(CONSOLE, DEBUG)
        srCore.WEBSERVER.open_browser = (True, False)[WEB_NOLAUNCH]
        srCore.WEBSERVER.port = (srCore.CONFIG.WEB_PORT, WEB_PORT)[WEB_PORT != srCore.CONFIG.WEB_PORT]
        srCore.WEBSERVER.start()
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback)
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
