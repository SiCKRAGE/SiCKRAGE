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
import logging
import os
import sys
import threading
import time
import traceback

__all__ = [
    'srCore',
    'PROG_DIR',
    'DATA_DIR',
    'DEVELOPER',
    'SYS_ENCODING',
    'PIDFILE'
]

status = None
srCore = None

PROG_DIR = os.path.abspath(os.path.dirname(__file__))

SYS_ENCODING = None
DEBUG = None
WEB_PORT = None
DEVELOPER = None
DAEMONIZE = None
NOLAUNCH = None
QUITE = None
DATA_DIR = None
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
    subprocess.call([sys.executable, file_name] + ([], ['--user'])[all([not isElevatedUser(), not isVirtualEnv()])])

    print("Cleaning up downloaded pip files")
    os.remove(file_name)


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


def install_requirements(restart=False):
    logging.captureWarnings(True)

    # install pip package manager
    install_pip()

    from pip.commands.install import InstallCommand
    from pip.download import PipSession
    from pip.req import parse_requirements

    # print("Installing SiCKRAGE requirement packages")
    # pip.main(['install', '-r', '{}'.format(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'requirements.txt'))] + ([], ['--user'])[all([not isElevatedUser(), not isVirtualEnv()])])

    for r in parse_requirements(
            os.path.join(os.path.abspath(os.path.dirname(__file__)), 'requirements.txt'),
            session=PipSession()):

        req_options, req_args = InstallCommand().parse_args([r.req.project_name])
        req_options.use_user_site = all([not isElevatedUser(), not isVirtualEnv()])
        req_options.cache_dir = None
        req_options.upgrade = True
        req_options.quiet = 1

        try:
            print("Checking SiCKRAGE requirements package: {}".format(r.req.project_name))
            req_options.ignore_dependencies = True
            InstallCommand().run(req_options, req_args)
            req_options.ignore_dependencies = False
            InstallCommand().run(req_options, req_args)
        except Exception:
            continue

    # restart sickrage silently
    if restart:
        os.execl(sys.executable, sys.executable, *sys.argv)

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
                            default=os.path.abspath(os.path.join(os.path.expanduser("~"), '.sickrage')),
                            help='Overrides data folder for database, configfile, cache, logfiles (full path)')
        parser.add_argument('--config',
                            default=os.path.abspath(os.path.join(os.path.expanduser("~"), '.sickrage', 'config.ini')),
                            help='Overrides config filename (full path including filename)')
        parser.add_argument('--pidfile',
                            default='sickrage.pid',
                            help='Creates a pidfile (full path including filename)')
        parser.add_argument('--nolaunch',
                            action='store_true',
                            help='Suppress launching web browser on startup')
        parser.add_argument('--requirements',
                            action='store_true',
                            help='Installs requirements and exits')

        args = parser.parse_args()

        # install requirements
        if args.requirements:
            install_requirements()
            sys.exit()

        # Quite
        QUITE = args.quite

        # Override default/configured port
        WEB_PORT = int(args.port)

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

        # import core
        from sickrage import core

        # main app loop
        while True:
            # start core
            srCore = core.Core()
            srCore.start()
    except ImportError:
        if DEBUG:
            traceback.print_exc()

        if not DEVELOPER:
            # install required packages
            install_requirements(restart=True)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        traceback.print_exc()
        if srCore:
            srCore.srLogger.debug(traceback.format_exc())
        status = e.message
    finally:
        if srCore:
            srCore.shutdown(status)


if __name__ == '__main__':
    main()
