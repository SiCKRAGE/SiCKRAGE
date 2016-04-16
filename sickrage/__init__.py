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

from __future__ import print_function, unicode_literals, with_statement

import argparse
import codecs
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
    'srWebSession',
    'PROG_DIR',
    'DATA_DIR',
    'DEVELOPER',
    'SYS_ENCODING',
    'PIDFILE'
]

status = None
srCore = None
srLogger = None
srConfig = None
srScheduler = None
srWebServer = None
srWebSession = None

PROG_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.abspath(os.path.join(os.path.expanduser("~"), '.sickrage'))

SYS_ENCODING = None
DEBUG = None
WEB_PORT = None
DEVELOPER = None
DAEMONIZE = None
NOLAUNCH = None
QUITE = None
CONFIG_FILE = None
PIDFILE = None

# fix threading time bug
time.strptime("2012", "%Y")

# set thread name
threading.currentThread().setName('MAIN')


def print_logo():
    from pyfiglet import print_figlet
    print_figlet('SiCKRAGE', font='doom')


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


def install_requirements(upgrade=False):
    from pip.commands.install import InstallCommand, InstallationError

    requirements = [os.path.abspath(os.path.join(os.path.dirname(__file__), 'requirements.txt'))]
    options = InstallCommand().parse_args([])[0]
    options.use_user_site = all([not isElevatedUser(), not isVirtualEnv()])
    options.requirements = requirements
    options.cache_dir = None
    options.upgrade = upgrade
    options.quiet = 1
    options.pre = True

    # install/upgrade all requirements for sickrage
    print("Installing SiCKRAGE requirement packages, please stand by ...")

    attempts = 0
    while attempts < 3:
        try:
            options.ignore_dependencies = True
            InstallCommand().run(options, [])

            if not upgrade and attempts < 1:
                options.ignore_dependencies = False
                InstallCommand().run(options, [])

            # finished
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
    except OSError as e:
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
    except OSError as e:
        sys.stderr.write("Fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)

    print("Daemonized successfully, pid %s" % os.getpid())

    if sys.platform != 'darwin':
        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = io.open(stdin, 'r')
        so = io.open(stdout, 'a+')
        se = io.open(stderr, 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

    # Write the PID file
    import atexit
    atexit.register(lambda: delpid(pidfile))
    io.open(pidfile, 'w+').write("%s\n" % str(os.getpid()))

def delpid(pidfile):
    # Removes the PID file
    if pidfile and os.path.exists(pidfile):
        os.remove(pidfile)

def pid_exists(pid):
    """Check whether pid exists in the current process table."""
    if pid < 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError as e:
        return False
    else:
        return True

def main():
    global srCore, status, SYS_ENCODING, PROG_DIR, DATA_DIR, CONFIG_FILE, PIDFILE, DEVELOPER, DEBUG, DAEMONIZE, WEB_PORT, NOLAUNCH, QUITE

    # sickrage requires python 2.7+
    if sys.version_info < (2, 7):
        sys.exit("Sorry, SiCKRAGE requires Python 2.7+")

    # add sickrage module to python system path
    path = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
    if path not in sys.path:
        sys.path.insert(0, path)

    # set locale encoding
    SYS_ENCODING = encodingInit()

    try:
        # print logo
        print_logo()

        # sickrage startup options
        parser = argparse.ArgumentParser(prog='sickrage')
        parser.add_argument('-v', '--version',
                            action='version',
                            version='%(prog)s 8.0')
        parser.add_argument('-d', '--daemon',
                            action='store_true',
                            help='Run as a daemon (*NIX ONLY)')
        parser.add_argument('-q', '--quite',
                            action='store_true',
                            help='Disables logging to CONSOLE')
        parser.add_argument('-p', '--port',
                            default=8081,
                            type=int,
                            help='Override default/configured port to listen on')
        parser.add_argument('--dev',
                            action='store_true',
                            help='Enable developer mode')
        parser.add_argument('--debug',
                            action='store_true',
                            help='Enable debugging')
        parser.add_argument('--datadir',
                            default=DATA_DIR,
                            help='Overrides data folder for database, configfile, cache, logfiles (full path)')
        parser.add_argument('--config',
                            default='config.ini',
                            help='Overrides config filename (full path including filename)')
        parser.add_argument('--pidfile',
                            default='sickrage.pid',
                            help='Creates a pidfile (full path including filename)')
        parser.add_argument('--nolaunch',
                            action='store_true',
                            help='Suppress launching web browser on startup')

        args = parser.parse_args()

        # Quite
        QUITE = args.quite

        # Override default/configured port
        WEB_PORT = args.port

        # Launch browser
        NOLAUNCH = args.nolaunch

        DEVELOPER = args.dev
        if DEVELOPER:
            print("!!! DEVELOPER MODE ENABLED !!!")

        DEBUG = args.debug
        if DEBUG:
            print("!!! DEBUG MODE ENABLED !!!")

        # Specify folder to use as the data dir
        DATA_DIR = os.path.abspath(os.path.expanduser(args.datadir))
        CONFIG_FILE = os.path.abspath(os.path.expanduser(args.config))

        # Make sure that we can create the data dir
        if not os.access(DATA_DIR, os.F_OK):
            try:
                os.makedirs(DATA_DIR, 0o744)
            except os.error:
                sys.exit("Unable to create data directory '" + DATA_DIR + "'")

        # Make sure we can write to the data dir
        if not os.access(DATA_DIR, os.W_OK):
            sys.exit("Data directory must be writeable '" + DATA_DIR + "'")

        # Pidfile for daemon
        PIDFILE = os.path.abspath(os.path.join(DATA_DIR, args.pidfile))
        if os.path.exists(PIDFILE):
            if pid_exists(int(io.open(PIDFILE).read())):
                sys.exit("PID file: " + PIDFILE + " already exists. Exiting.")

            # remove stale pidfile
            delpid(PIDFILE)

        # daemonize if requested
        DAEMONIZE = (False, args.daemon)[not sys.platform == 'win32']
        if DAEMONIZE:
            NOLAUNCH = False
            QUITE = False
            daemonize(PIDFILE)

        # main app loop
        while True:
            from .core import Core
            srCore = Core()
            srCore.start()
    except ImportError as e:
        if DEBUG:
            traceback.print_exc()

        if not DEVELOPER:
            # install pip package manager
            install_pip()

            # install required packages
            install_requirements()

            # restart sickrage silently
            os.execl(sys.executable, sys.executable, *sys.argv)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        traceback.print_exc()
        status = e.message
    finally:
        if srCore:
            srCore.shutdown(status)

if __name__ == '__main__':
    main()
