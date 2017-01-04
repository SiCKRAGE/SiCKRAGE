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

from __future__ import print_function, unicode_literals, with_statement

import argparse
import atexit
import codecs
import io
import locale
import os
import site
import sys
import threading
import time
import traceback
from signal import SIGTERM

__all__ = [
    'srCore',
    'PROG_DIR',
    'DATA_DIR',
    'CONFIG_FILE'
    'DEVELOPER',
    'SYS_ENCODING',
    'PID_FILE'
]

restart = True
srCore = None
daemon = None

MAIN_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
PROG_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
REQS_FILE = os.path.abspath(os.path.join(MAIN_DIR, 'requirements.txt'))

SYS_ENCODING = None
DEBUG = None
WEB_PORT = None
DEVELOPER = None
DAEMONIZE = None
NOLAUNCH = None
QUITE = None
MODULE_DIR = None
DATA_DIR = None
CONFIG_FILE = None
PID_FILE = None

# fix threading time bug
time.strptime("2012", "%Y")

# set thread name
threading.currentThread().setName('MAIN')


class Daemon(object):
    """
    Usage: subclass the Daemon class
    """

    def __init__(self, pidfile):
        self.stdin = getattr(os, 'devnull', '/dev/null')
        self.stdout = getattr(os, 'devnull', '/dev/null')
        self.stderr = getattr(os, 'devnull', '/dev/null')
        self.pidfile = pidfile

    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        print("Daemonized successfully, pid %s" % os.getpid())

        # redirect standard file descriptors
        sys.stdin = sys.__stdin__
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        file(self.pidfile, 'w+').write("%s\n" % pid)

    def delpid(self):
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        # Start the daemon
        self.daemonize()

    def stop(self):
        """
        Stop the daemon
        """

        # Get the pid from the pidfile
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return  # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                self.delpid()
            else:
                sys.exit(1)


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


def check_requirements():
    # sickrage requires python 2.7+
    if sys.version_info < (2, 7):
        sys.exit("Sorry, SiCKRAGE requires Python 2.7+")

    # Check if lxml is available
    try:
        from lxml import etree
    except:
        print(
            'LXML not available, please install for better/faster scraping support: `http://lxml.de/installation.html`')

    try:
        import OpenSSL

        v = OpenSSL.__version__
        v_needed = '0.15'

        if not v >= v_needed:
            print('OpenSSL installed but {} is needed while {} is installed. Run `pip install -U pyopenssl`'.format(
                v_needed, v))
    except:
        print(
            'OpenSSL not available, please install for better requests validation: `https://pyopenssl.readthedocs.org/en/latest/install.html`')


def version():
    # Get the version number
    with io.open(os.path.abspath(os.path.join(os.path.dirname(__file__), 'version.txt'))) as f:
        return f.read()


def main():
    global srCore, daemon, SYS_ENCODING, MAIN_DIR, PROG_DIR, DATA_DIR, CONFIG_FILE, PID_FILE, DEVELOPER, \
        DEBUG, DAEMONIZE, WEB_PORT, NOLAUNCH, QUITE

    try:
        from sickrage import core

        print("..::[ SiCKRAGE ]::..")

        # sickrage startup options
        parser = argparse.ArgumentParser(prog='sickrage')
        parser.add_argument('-v', '--version',
                            action='version',
                            version='%(prog)s {}'.format(version()))
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
                            help='Overrides data folder for database, config, cache and logs (specify full path)')
        parser.add_argument('--config',
                            default='config.ini',
                            help='Overrides config filename (specify full path and filename if outside datadir path)')
        parser.add_argument('--pidfile',
                            default='sickrage.pid',
                            help='Creates a PID file (specify full path and filename if outside datadir path)')
        parser.add_argument('--nolaunch',
                            action='store_true',
                            help='Suppress launching web browser on startup')

        # Parse startup args
        args = parser.parse_args()
        QUITE = args.quite
        WEB_PORT = int(args.port)
        NOLAUNCH = args.nolaunch
        DEVELOPER = args.dev
        DEBUG = args.debug
        DAEMONIZE = (False, args.daemon)[not sys.platform == 'win32']
        DATA_DIR = os.path.abspath(os.path.expanduser(args.datadir))
        CONFIG_FILE = args.config
        PID_FILE = args.pidfile

        if not os.path.isabs(CONFIG_FILE):
            CONFIG_FILE = os.path.abspath(os.path.join(DATA_DIR, CONFIG_FILE))

        if not os.path.abspath(PID_FILE):
            PID_FILE = os.path.abspath(os.path.join(DATA_DIR, PID_FILE))

        # check lib requirements
        check_requirements()

        # add sickrage module to python system path
        if not (PROG_DIR in sys.path):
            sys.path, remainder = sys.path[:1], sys.path[1:]
            site.addsitedir(PROG_DIR)
            sys.path.extend(remainder)

        # set locale encoding
        SYS_ENCODING = encodingInit()

        if DEVELOPER:
            print("!!! DEVELOPER MODE ENABLED !!!")

        if DEBUG:
            print("!!! DEBUG MODE ENABLED !!!")

        # Make sure that we can create the data dir
        if not os.access(DATA_DIR, os.F_OK):
            try:
                os.makedirs(DATA_DIR, 0o744)
            except os.error:
                sys.exit("Unable to create data directory '" + DATA_DIR + "'")

        # Make sure we can write to the data dir
        if not os.access(DATA_DIR, os.W_OK):
            sys.exit("Data directory must be writeable '" + DATA_DIR + "'")

        # daemonize if requested
        if DAEMONIZE:
            NOLAUNCH = False
            QUITE = False
            daemon = Daemon(PID_FILE)
            daemon.daemonize()

        # main app loop
        while restart:
            srCore = core.Core()
            srCore.start()
            srCore.shutdown()
    except (SystemExit, KeyboardInterrupt):
        try:
            srCore.shutdown()
        except:
            pass
    except ImportError:
        traceback.print_exc()
        if os.path.isfile(REQS_FILE):
            print("Failed to import required libs, please run 'pip install -r {}' from console".format(REQS_FILE))
    except:
        traceback.print_exc()

if __name__ == '__main__':
    main()
