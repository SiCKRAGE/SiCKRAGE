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

from __future__ import unicode_literals, with_statement

import codecs
import getopt
import io
import locale
import os
import sys
import threading
import time
import traceback

__all__ = [
    'srCore',
    'srLogger',
    'srConfig',
    'srScheduler',
    'srWebServer',
    'PROG_DIR',
    'DATA_DIR',
    'DEVELOPER',
    'SYS_ENCODING'
]

SYS_ENCODING = "UTF-8"

DEVELOPER = False

PROG_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.abspath(os.path.join(os.path.expanduser("~"), '.sickrage'))

srCore = None
srLogger = None
srConfig = None
srScheduler = None
srWebServer = None

# fix threading time bug
time.strptime("2012", "%Y")

# set thread name
threading.currentThread().setName('MAIN')


def print_logo():
    from colorama import init
    from termcolor import cprint
    from pyfiglet import figlet_format

    init(strip=not sys.stdout.isatty())  # strip colors if stdout is redirected
    cprint(figlet_format('SiCKRAGE', font='doom'))


def encodingInit():
    # map the following codecs to utf-8
    codecs.register(lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)
    codecs.register(lambda name: codecs.lookup('utf-8') if name == 'cp1252' else None)

    # get locale encoding
    try:
        locale.setlocale(locale.LC_ALL, "")
        encoding = locale.getpreferredencoding()
    except (locale.Error, IOError):
        encoding = None

    # enforce UTF-8
    if not encoding or codecs.lookup(encoding).name == 'ascii':
        encoding = 'UTF-8'

    # wrap i/o in unicode
    sys.stdout = codecs.getwriter(encoding)(sys.stdout)
    sys.stdin = codecs.getreader(encoding)(sys.stdin)

    return encoding


def isElevatedUser():
    try:
        return os.getuid() == 0
    except AttributeError:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0


def isVirtualEnv():
    return hasattr(sys, 'real_prefix')


def install_pip():
    print("Downloading pip ...")
    import urllib2

    url = "https://bootstrap.pypa.io/get-pip.py"
    file_name = os.path.abspath(os.path.join(os.path.dirname(__file__), url.split('/')[-1]))
    u = urllib2.urlopen(url)
    with io.open(file_name, 'wb') as f:
        block_sz = 8192
        while True:
            buf = u.read(block_sz)
            if not buf:
                break
            f.write(buf)

    print("Installing pip ...")
    import subprocess
    subprocess.call([sys.executable, file_name] + ([], ['--user'])[all([isElevatedUser(), not isVirtualEnv()])])

    print("Cleaning up downloaded pip files")
    os.remove(file_name)


def install_requirements(pkg=None):
    from pip.commands.install import InstallCommand, InstallationError

    requirements = [os.path.abspath(os.path.join(os.path.dirname(__file__), 'requirements.txt'))]
    options = InstallCommand().parse_args([])[0]
    options.use_user_site = all([not isElevatedUser(), not isVirtualEnv()])
    options.requirements = requirements
    options.cache_dir = None
    options.upgrade = True
    options.quiet = 1
    options.pre = True

    # install/upgrade all requirements for sickrage
    print("Installing SiCKRAGE requirement packages, please stand by ...")

    attempts = 0
    while attempts < 3:
        try:
            options.ignore_dependencies = True
            InstallCommand().run(options, [])
            options.ignore_dependencies = False
            InstallCommand().run(options, [])
            return
        except InstallationError:
            options.ignore_installed = True
            attempts += 1
        except Exception as e:
            attempts += 1

    # failed to install requirements
    sys.exit(traceback.print_exc())


def daemonize(pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
    try:
        pid = os.fork()
        if pid > 0:
            # Exit from first parent
            sys.exit(0)
    except OSError, e:
        sys.stderr.write("Fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)

    # Decouple from parent environment
    os.chdir("/")
    os.setsid()
    os.umask(0)

    # Second fork
    try:
        pid = os.fork()
        if pid > 0:
            # Exit from second parent
            sys.exit(0)
    except OSError, e:
        sys.stderr.write("Fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)

    if sys.platform != 'darwin':  # This block breaks on OS X
        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(stdin, 'r')
        so = file(stdout, 'a+')
        se = file(stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

    # Write the PID file
    import atexit
    atexit.register(lambda: delpid(pidfile))
    file(pidfile, 'w+').write("%s\n" % str(os.getpid()))


def delpid(pidfile):
    # Removes the PID file
    if os.path.exists(pidfile):
        os.remove(pidfile)


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
    help_msg += "                --debug             Enable debugging\n"

    return help_msg


def main():
    global srCore, PROG_DIR, DATA_DIR, SYS_ENCODING, DEVELOPER

    # sickrage requires python 2.7+
    if sys.version_info < (2, 7):
        sys.exit("Sorry, SiCKRAGE requires Python 2.7+")

    # add sickrage module to python system path
    path = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
    if path not in sys.path:
        sys.path.insert(0, path)

    # setup locale system encoding
    SYS_ENCODING = encodingInit()

    try:
        # print logo
        print_logo()

        # defaults
        SYS_ENCODING = None
        PIDFILE = None
        DAEMONIZE = False
        WEB_PORT = 8081
        LAUNCH_BROWSER = True
        DEBUG = False
        CONFIG_FILE = "config.ini"
        CONSOLE = not hasattr(sys, "frozen")

        # sickrage startup options
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
             'debug']
        )

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
            if o in ('--nolaunch',):
                LAUNCH_BROWSER = False

            # Override default/configured port
            if o in ('-p', '--port'):
                try:
                    WEB_PORT = int(a)
                except ValueError:
                    sys.exit("Port: " + str(a) + " is not a number. Exiting.")

            # Run as a double forked daemon
            if o in ('-d', '--daemon'):
                DAEMONIZE = (False, True)[not sys.platform == 'win32']
                LAUNCH_BROWSER = False
                CONSOLE = False

            # Write a pidfile if requested
            if o in ('--pidfile',):
                PIDFILE = str(a)

                # If the pidfile already exists, sickrage may still be running, so exit
                if os.path.exists(PIDFILE):
                    sys.exit("PID file: " + PIDFILE + " already exists. Exiting.")

            # Specify folder to use as the data dir
            if o in ('--datadir',):
                DATA_DIR = os.path.abspath(os.path.expanduser(a))

            # Specify folder to load the config file from
            if o in ('--config',):
                CONFIG_FILE = os.path.abspath(os.path.expanduser(a))

            # Install ssl packages from requirements folder
            if o in ('--debug',):
                print("!!! DEBUGGING MODE ENABLED !!!")
                DEBUG = True

        # daemonize sickrage ?
        if DAEMONIZE:
            if not PIDFILE:
                os.path.abspath(os.path.join(DATA_DIR, 'sickrage.pid'))
            daemonize(PIDFILE)

        # Make sure that we can create the data dir
        if not os.access(DATA_DIR, os.F_OK):
            try:
                os.makedirs(DATA_DIR, 0o744)
            except os.error:
                sys.exit("Unable to create data directory '" + DATA_DIR + "'")

        # Make sure we can write to the data dir
        if not os.access(DATA_DIR, os.W_OK):
            sys.exit("Data directory must be writeable '" + DATA_DIR + "'")

        # restart loop, breaks if shutdown
        while True:
            from . import core
            srCore = core.srCore(CONFIG_FILE, CONSOLE, DEBUG, WEB_PORT, LAUNCH_BROWSER)
            srCore.start()
    except ImportError as e:
        # install pip package manager
        install_pip()

        # install required packages
        install_requirements()

        # restart sickrage silently
        os.execl(sys.executable, sys.executable, *sys.argv)
    except KeyboardInterrupt:
        if srCore:
            srCore.shutdown()
    except Exception as e:
        if srCore:
            srCore.shutdown(status=str(e))


if __name__ == '__main__':
    main()
