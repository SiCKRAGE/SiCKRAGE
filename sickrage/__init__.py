# ##############################################################################
#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#  -
#  This file is part of SiCKRAGE.
#  -
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  -
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
# ##############################################################################

__version__ = "10.0.72.dev0"
__install_type__ = ""

import sys

# sickrage requires python 3.6+
if sys.version_info < (3, 6, 0):
    sys.exit("Sorry, SiCKRAGE requires Python 3.6+")

import argparse
import atexit
import gettext
import multiprocessing
import os
import pathlib
import re
import site
import subprocess
import threading
import time
import traceback
import pkg_resources

# pywin32 for windows service
try:
    import win32api
    import win32serviceutil
    import win32evtlogutil
    import win32event
    import win32service
    import win32ts
    import servicemanager
    from win32com.shell import shell, shellcon
except ImportError:
    if __install_type__ == 'windows':
        sys.exit("Sorry, SiCKRAGE requires Python module PyWin32.")

from signal import SIGTERM

app = None

MAIN_DIR = os.path.abspath(os.path.realpath(os.path.expanduser(os.path.dirname(os.path.dirname(__file__)))))
PROG_DIR = os.path.abspath(os.path.realpath(os.path.expanduser(os.path.dirname(__file__))))
LOCALE_DIR = os.path.join(PROG_DIR, 'locale')
CHANGELOG_FILE = os.path.join(MAIN_DIR, 'CHANGELOG.md')
REQS_FILE = os.path.join(MAIN_DIR, 'requirements.txt')
CHECKSUM_FILE = os.path.join(PROG_DIR, 'checksums.md5')
AUTO_PROCESS_TV_CFG_FILE = os.path.join(*[PROG_DIR, 'autoProcessTV', 'autoProcessTV.cfg'])

# add sickrage libs path to python system path
LIBS_DIR = os.path.join(PROG_DIR, 'libs')
if not (LIBS_DIR in sys.path) and not getattr(sys, 'frozen', False):
    sys.path, remainder = sys.path[:1], sys.path[1:]
    site.addsitedir(LIBS_DIR)
    sys.path.extend(remainder)

# set system default language
gettext.install('messages', LOCALE_DIR, codeset='UTF-8', names=["ngettext"])

if __install_type__ == 'windows':
    class SiCKRAGEService(win32serviceutil.ServiceFramework):
        _svc_name_ = "SiCKRAGE"
        _svc_display_name_ = "SiCKRAGE"
        _svc_description_ = (
            "Automated video library manager for TV shows. "
            'Set to "automatic" to start the service at system startup. '
            "You may need to login with a real user account when you need "
            "access to network shares."
        )

        if hasattr(sys, "frozen"):
            _exe_name_ = "SiCKRAGE.exe"

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

        def SvcDoRun(self):
            msg = "SiCKRAGE-service %s" % __version__
            self.Logger(servicemanager.PYS_SERVICE_STARTED, msg + " has started")
            start()
            self.Logger(servicemanager.PYS_SERVICE_STOPPED, msg + " has stopped")

        def SvcStop(self):
            if app:
                app.shutdown()

            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.hWaitStop)

        def Logger(self, state, msg):
            win32evtlogutil.ReportEvent(
                self._svc_display_name_, state, 0, servicemanager.EVENTLOG_INFORMATION_TYPE, (self._svc_name_, msg)
            )


class Daemon(object):
    """
    Usage: subclass the Daemon class
    """

    def __init__(self, pidfile, working_dir="/"):
        self.stdin = getattr(os, 'devnull', '/dev/null')
        self.stdout = getattr(os, 'devnull', '/dev/null')
        self.stderr = getattr(os, 'devnull', '/dev/null')
        self.pidfile = pidfile
        self.working_dir = working_dir
        self.pid = None

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
                os._exit(0)
        except OSError as e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                os._exit(0)
        except OSError as e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdin = sys.__stdin__
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.stdin, 'r')
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)
        self.pid = os.getpid()
        open(self.pidfile, 'w+').write("%s\n" % self.pid)

    def delpid(self):
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = open(self.pidfile, 'r')
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
            pf = open(self.pidfile, 'r')
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
        except OSError as err:
            err = str(err)
            if err.find("No such process") > 0:
                self.delpid()
            else:
                sys.exit(1)


def version():
    # Return the version number
    return __version__


def install_type():
    # Return the install type
    if not __install_type__ and os.path.isdir(os.path.join(MAIN_DIR, '.git')):
        return 'git'
    else:
        return __install_type__ or 'source'


def changelog():
    # Return contents of CHANGELOG.md
    with open(CHANGELOG_FILE) as f:
        return f.read()


def check_requirements():
    if os.path.exists(REQS_FILE):
        with open(REQS_FILE) as f:
            for line in f.readlines():
                try:
                    req_name, req_version = line.strip().split('==', 1)
                    if 'python_version' in req_version:
                        m = re.search('(\d+.\d+.\d+).*(\d+.\d+)', req_version)
                        req_version = m.group(1)
                        python_version = m.group(2)
                        python_version_major = int(python_version.split('.')[0])
                        python_version_minor = int(python_version.split('.')[1])
                        if sys.version_info.major == python_version_major and sys.version_info.minor != python_version_minor:
                            continue

                    if not pkg_resources.get_distribution(req_name).version == req_version:
                        print('Updating requirement {} to {}'.format(req_name, req_version))
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-deps", "--no-cache-dir", line.strip()])
                except pkg_resources.DistributionNotFound:
                    print('Installing requirement {}'.format(line.strip()))
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-deps", "--no-cache-dir", line.strip()])
                except ValueError:
                    continue


def verify_checksums(remove_unverified=False):
    valid_files = []
    exempt_files = [pathlib.Path(__file__), pathlib.Path(CHECKSUM_FILE), pathlib.Path(AUTO_PROCESS_TV_CFG_FILE)]

    if not os.path.exists(CHECKSUM_FILE):
        return

    with open(CHECKSUM_FILE, "rb") as fp:
        for line in fp.readlines():
            file, checksum = line.decode().strip().split(' = ')
            full_filename = pathlib.Path(MAIN_DIR).joinpath(file)
            valid_files.append(full_filename)

    for root, dirs, files in os.walk(PROG_DIR):
        for file in files:
            full_filename = pathlib.Path(root).joinpath(file)

            if full_filename in exempt_files or full_filename.suffix == '.pyc':
                continue

            if full_filename not in valid_files and PROG_DIR in str(full_filename):
                try:
                    if remove_unverified:
                        print('Found unverified file {}, removed!'.format(full_filename))
                        full_filename.unlink()
                    else:
                        print('Found unverified file {}, you should delete this file manually!'.format(full_filename))
                except OSError:
                    print('Unable to delete unverified filename {} during checksum verification, you should delete this file manually!'.format(full_filename))


def handle_windows_service():
    if hasattr(sys, "frozen") and win32ts.ProcessIdToSessionId(win32api.GetCurrentProcessId()) == 0:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(SiCKRAGEService)
        servicemanager.StartServiceCtrlDispatcher()
        return True

    if len(sys.argv) > 1 and sys.argv[1] in ("install", "update", "remove", "start", "stop", "restart", "debug"):
        win32serviceutil.HandleCommandLine(SiCKRAGEService)
        del sys.argv[1]
        return True


def main():
    multiprocessing.freeze_support()

    # set thread name
    threading.current_thread().name = 'MAIN'

    # fix threading time bug
    time.strptime("2012", "%Y")

    if __install_type__ == 'windows':
        if not handle_windows_service():
            start()
    else:
        start()


def start():
    global app

    parser = argparse.ArgumentParser(
        prog='sickrage',
        description='Automated video library manager for TV shows'
    )

    parser.add_argument('-v', '--version',
                        action='version',
                        version=version())
    parser.add_argument('-d', '--daemon',
                        action='store_true',
                        help='Run as a daemon (*NIX ONLY)')
    parser.add_argument('-q', '--quiet',
                        action='store_true',
                        help='Disables logging to CONSOLE')
    parser.add_argument('-p', '--port',
                        default=0,
                        type=int,
                        help='Override default/configured port to listen on')
    parser.add_argument('-H', '--host',
                        default='',
                        help='Override default/configured host to listen on')
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
    parser.add_argument('--no_clean',
                        action='store_true',
                        help='Suppress cleanup of files not present in checksum.md5')
    parser.add_argument('--nolaunch',
                        action='store_true',
                        help='Suppress launching web browser on startup')
    parser.add_argument('--disable_updates',
                        action='store_true',
                        help='Disable application updates')
    parser.add_argument('--web_root',
                        default='',
                        type=str,
                        help='Overrides URL web root')
    parser.add_argument('--db_type',
                        default='sqlite',
                        help='Database type: sqlite or mysql')
    parser.add_argument('--db_prefix',
                        default='sickrage',
                        help='Database prefix you want prepended to database table names')
    parser.add_argument('--db_host',
                        default='localhost',
                        help='Database hostname (not used for sqlite)')
    parser.add_argument('--db_port',
                        default='3306',
                        help='Database port number (not used for sqlite)')
    parser.add_argument('--db_username',
                        default='sickrage',
                        help='Database username (not used for sqlite)')
    parser.add_argument('--db_password',
                        default='sickrage',
                        help='Database password (not used for sqlite)')

    # Parse startup args
    args = parser.parse_args()

    # check requirements
    # if install_type() not in ['windows', 'synology', 'docker', 'qnap', 'readynas', 'pip']:
    #     check_requirements()

    # verify file checksums, remove unverified files
    # verify_checksums(remove_unverified=not args.no_clean)

    try:
        from sickrage.core import Core
        app = Core()
    except ImportError:
        sys.exit("Sorry, SiCKRAGE requirements need to be installed.")

    try:
        app.quiet = args.quiet
        app.web_host = args.host
        app.web_port = int(args.port)
        app.web_root = args.web_root.lstrip('/').rstrip('/')
        app.no_launch = args.nolaunch
        app.disable_updates = args.disable_updates
        app.developer = args.dev
        app.db_type = args.db_type
        app.db_prefix = args.db_prefix
        app.db_host = args.db_host
        app.db_port = args.db_port
        app.db_username = args.db_username
        app.db_password = args.db_password
        app.debug = args.debug
        app.data_dir = os.path.abspath(os.path.realpath(os.path.expanduser(args.datadir)))
        app.cache_dir = os.path.abspath(os.path.realpath(os.path.join(app.data_dir, 'cache')))
        app.config_file = args.config
        daemonize = (False, args.daemon)[not sys.platform == 'win32']
        pid_file = args.pidfile

        if not os.path.isabs(app.config_file):
            app.config_file = os.path.join(app.data_dir, app.config_file)

        if not os.path.isabs(pid_file):
            pid_file = os.path.join(app.data_dir, pid_file)

        # add sickrage module to python system path
        if not (PROG_DIR in sys.path) and not getattr(sys, 'frozen', False):
            sys.path, remainder = sys.path[:1], sys.path[1:]
            site.addsitedir(PROG_DIR)
            sys.path.extend(remainder)

        # Make sure that we can create the data dir
        if not os.access(app.data_dir, os.F_OK):
            try:
                os.makedirs(app.data_dir, 0o744)
            except os.error:
                sys.exit("Unable to create data directory '" + app.data_dir + "'")

        # Make sure we can write to the data dir
        if not os.access(app.data_dir, os.W_OK):
            sys.exit("Data directory must be writeable '" + app.data_dir + "'")

        # Make sure that we can create the cache dir
        if not os.access(app.cache_dir, os.F_OK):
            try:
                os.makedirs(app.cache_dir, 0o744)
            except os.error:
                sys.exit("Unable to create cache directory '" + app.cache_dir + "'")

        # Make sure we can write to the cache dir
        if not os.access(app.cache_dir, os.W_OK):
            sys.exit("Cache directory must be writeable '" + app.cache_dir + "'")

        # daemonize if requested
        if daemonize:
            app.no_launch = True
            app.quiet = True
            app.daemon = Daemon(pid_file, app.data_dir)
            app.daemon.daemonize()
            app.pid = app.daemon.pid

        app.start()

        from tornado.ioloop import IOLoop
        IOLoop.current().start()
    except (SystemExit, KeyboardInterrupt):
        if app:
            app.shutdown()
    except Exception as e:
        try:
            # attempt to send exception to sentry
            import sentry_sdk
            sentry_sdk.capture_exception(e)
        except ImportError:
            pass

        traceback.print_exc()


if __name__ == '__main__':
    main()
