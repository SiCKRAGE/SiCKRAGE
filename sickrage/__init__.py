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

from sickrage.requirements import install_pip, install_reqs

__all__ = ["main"]

import ctypes
import getopt
import os
import platform
import sys
import threading
import traceback
import uuid

USER_AGENT = 'SiCKRAGE/({};{};{})'.format(platform.system(), platform.release(), str(uuid.uuid1()))

INDEXER_API = None

INITIALIZED = False
STARTED = False

# This is the version of the config we EXPECT to find
CFG = None
CONFIG_FILE = None
CONFIG_VERSION = 7

# Default encryption version (0 for None)
ENCRYPTION_VERSION = 0
ENCRYPTION_SECRET = None

MY_FULLNAME = None
APP_NAME = None
ROOT_DIR = None
PROG_DIR = None
DATA_DIR = None
MY_ARGS = None
GUI_DIR = None
SYS_ENCODING = None
CREATEPID = False
PIDFILE = None
DAEMON = None
DAEMONIZE = False
NO_RESIZE = False
PID = None

# logging
LOGGER = None
LOG_DIR = None
LOG_FILE = None
LOG_SIZE = 1048576
LOG_NR = 5

# scheduler
Scheduler = None

# app updater
VERSIONUPDATER = None

# show lists
showList = None

# queues
SHOWUPDATER = None
SHOWQUEUE = None
SEARCHQUEUE = None

# caches
NAMECACHE = None

# searchers
DAILYSEARCHER = None
BACKLOGSEARCHER = None
PROPERSEARCHER = None
TRAKTSEARCHER = None
SUBTITLESEARCHER = None

# provider lists/dicts
providersDict = None
newznabProviderList = None
torrentRssProviderList = None
metadataProvideDict = None

NEWEST_VERSION = None
NEWEST_VERSION_STRING = None
VERSION_NOTIFY = False
AUTO_UPDATE = False
NOTIFY_ON_UPDATE = False

# github settings
GIT_ORG = 'SiCKRAGETV'
GIT_REPO = 'SiCKRAGE'
GITHUB = None
GIT_RESET = True
GIT_REMOTE = None
GIT_REMOTE_URL = None
GIT_USERNAME = None
GIT_PASSWORD = None
GIT_PATH = None
GIT_AUTOISSUES = False
GIT_NEWVER = False
DEVELOPER = False
CUR_COMMIT_BRANCH = None
CUR_COMMIT_HASH = None
VERSION = None

# news
NEWS_URL = 'http://sickragetv.github.io/sickrage-news/news.md'
NEWS_LAST_READ = None
NEWS_LATEST = None
NEWS_UNREAD = False

SOCKET_TIMEOUT = None

WEB_PORT = None
WEB_LOG = False
WEB_ROOT = None
WEB_USERNAME = None
WEB_PASSWORD = None
WEB_HOST = None
WEB_IPV6 = False
WEB_COOKIE_SECRET = None
WEB_USE_GZIP = True
WEB_SERVER = None
WEB_NOLAUNCH = False

# proxy
HANDLE_REVERSE_PROXY = False
PROXY_SETTING = None
PROXY_INDEXERS = True
LOCALHOST_IP = None

# ssl
SSL_VERIFY = True
ENABLE_HTTPS = False
HTTPS_CERT = None
HTTPS_KEY = None

# api
API_KEY = None
API_ROOT = None

INDEXER_DEFAULT_LANGUAGE = None
EP_DEFAULT_DELETED_STATUS = None
LAUNCH_BROWSER = False
CACHE_DIR = None
ACTUAL_CACHE_DIR = None
ROOT_DIRS = None
CPU_PRESET = None
ANON_REDIRECT = None
DOWNLOAD_URL = None
TRASH_REMOVE_SHOW = False
TRASH_ROTATE_LOGS = False
SORT_ARTICLE = False
DEBUG = False
DISPLAY_ALL_SEASONS = True
DEFAULT_PAGE = None

# metadata
USE_LISTVIEW = False
METADATA_KODI = None
METADATA_KODI_12PLUS = None
METADATA_MEDIABROWSER = None
METADATA_PS3 = None
METADATA_WDTV = None
METADATA_TIVO = None
METADATA_MEDE8ER = None

QUALITY_DEFAULT = None
STATUS_DEFAULT = None
STATUS_DEFAULT_AFTER = None
FLATTEN_FOLDERS_DEFAULT = False
SUBTITLES_DEFAULT = False
INDEXER_DEFAULT = None
INDEXER_TIMEOUT = None
SCENE_DEFAULT = False
ANIME_DEFAULT = False
ARCHIVE_DEFAULT = False
PROVIDER_ORDER = None

# naming
NAMING_MULTI_EP = False
NAMING_ANIME_MULTI_EP = False
NAMING_PATTERN = None
NAMING_ABD_PATTERN = None
NAMING_CUSTOM_ABD = False
NAMING_SPORTS_PATTERN = None
NAMING_CUSTOM_SPORTS = False
NAMING_ANIME_PATTERN = None
NAMING_CUSTOM_ANIME = False
NAMING_FORCE_FOLDERS = False
NAMING_STRIP_YEAR = False
NAMING_ANIME = None
NAMING_EP_TYPE = None
SPORTS_EP_TYPE = None
NAMING_EP_TYPE_TEXT = None
NAMING_MULTI_EP_TYPE = None
NAMING_MULTI_EP_TYPE_TEXT = None
NAMING_SEP_TYPE = None
NAMING_SEP_TYPE_TEXT = None

USE_NZBS = False
USE_TORRENTS = False

NZB_METHOD = None
NZB_DIR = None
USENET_RETENTION = 500
TORRENT_METHOD = None
TORRENT_DIR = None
DOWNLOAD_PROPERS = False
PROPER_SEARCHER_INTERVAL = None
ALLOW_HIGH_PRIORITY = False
SAB_FORCED = False
RANDOMIZE_PROVIDERS = False

AUTOPOSTPROCESSOR_FREQ = DEFAULT_AUTOPOSTPROCESSOR_FREQ = 10
NAMECACHE_FREQ = DEFAULT_NAMECACHE_FREQ = 10
DAILY_SEARCHER_FREQ = DEFAULT_DAILY_SEARCHER_FREQ = 40
BACKLOG_SEARCHER_FREQ = DEFAULT_BACKLOG_SEARCHER_FREQ = 21
VERSION_UPDATER_FREQ = DEFAULT_VERSION_UPDATE_FREQ = 1
SUBTITLE_SEARCHER_FREQ = DEFAULT_SUBTITLE_SEARCHER_FREQ = 1
SHOWUPDATE_HOUR = DEFAULT_SHOWUPDATE_HOUR = 3

MIN_AUTOPOSTPROCESSOR_FREQ = 1
MIN_NAMECACHE_FREQ = 1
MIN_DAILY_SEARCHER_FREQ = 10
MIN_BACKLOG_SEARCHER_FREQ = 10
MIN_VERSION_UPDATER_FREQ = 1
MIN_SUBTITLE_SEARCHER_FREQ = 1

BACKLOG_DAYS = 7

ADD_SHOWS_WO_DIR = False
CREATE_MISSING_SHOW_DIRS = False
RENAME_EPISODES = False
AIRDATE_EPISODES = False
FILE_TIMESTAMP_TIMEZONE = None
PROCESS_AUTOMATICALLY = False
NO_DELETE = False
KEEP_PROCESSED_DIR = False
PROCESS_METHOD = None
DELRARCONTENTS = False
MOVE_ASSOCIATED_FILES = False
POSTPONE_IF_SYNC_FILES = True
NFO_RENAME = True
TV_DOWNLOAD_DIR = None
UNPACK = False
SKIP_REMOVED_FILES = False

NZBS = False
NZBS_UID = None
NZBS_HASH = None

OMGWTFNZBS = False
OMGWTFNZBS_USERNAME = None
OMGWTFNZBS_APIKEY = None

NEWZBIN = False
NEWZBIN_USERNAME = None
NEWZBIN_PASSWORD = None

SAB_USERNAME = None
SAB_PASSWORD = None
SAB_APIKEY = None
SAB_CATEGORY = None
SAB_CATEGORY_BACKLOG = None
SAB_CATEGORY_ANIME = None
SAB_CATEGORY_ANIME_BACKLOG = None
SAB_HOST = None

NZBGET_USERNAME = None
NZBGET_PASSWORD = None
NZBGET_CATEGORY = None
NZBGET_CATEGORY_BACKLOG = None
NZBGET_CATEGORY_ANIME = None
NZBGET_CATEGORY_ANIME_BACKLOG = None
NZBGET_HOST = None
NZBGET_USE_HTTPS = False
NZBGET_PRIORITY = 100

TORRENT_USERNAME = None
TORRENT_PASSWORD = None
TORRENT_HOST = None
TORRENT_PATH = None
TORRENT_SEED_TIME = None
TORRENT_PAUSED = False
TORRENT_HIGH_BANDWIDTH = False
TORRENT_LABEL = None
TORRENT_LABEL_ANIME = None
TORRENT_VERIFY_CERT = False
TORRENT_RPCURL = None
TORRENT_AUTH_TYPE = None

USE_KODI = False
KODI_ALWAYS_ON = True
KODI_NOTIFY_ONSNATCH = False
KODI_NOTIFY_ONDOWNLOAD = False
KODI_NOTIFY_ONSUBTITLEDOWNLOAD = False
KODI_UPDATE_LIBRARY = False
KODI_UPDATE_FULL = False
KODI_UPDATE_ONLYFIRST = False
KODI_HOST = None
KODI_USERNAME = None
KODI_PASSWORD = None

USE_PLEX = False
PLEX_NOTIFY_ONSNATCH = False
PLEX_NOTIFY_ONDOWNLOAD = False
PLEX_NOTIFY_ONSUBTITLEDOWNLOAD = False
PLEX_UPDATE_LIBRARY = False
PLEX_SERVER_HOST = None
PLEX_SERVER_TOKEN = None
PLEX_HOST = None
PLEX_USERNAME = None
PLEX_PASSWORD = None
USE_PLEX_CLIENT = False
PLEX_CLIENT_USERNAME = None
PLEX_CLIENT_PASSWORD = None

USE_EMBY = False
EMBY_HOST = None
EMBY_APIKEY = None

USE_GROWL = False
GROWL_NOTIFY_ONSNATCH = False
GROWL_NOTIFY_ONDOWNLOAD = False
GROWL_NOTIFY_ONSUBTITLEDOWNLOAD = False
GROWL_HOST = None
GROWL_PASSWORD = None

USE_FREEMOBILE = False
FREEMOBILE_NOTIFY_ONSNATCH = False
FREEMOBILE_NOTIFY_ONDOWNLOAD = False
FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD = False
FREEMOBILE_ID = None
FREEMOBILE_APIKEY = None

USE_PROWL = False
PROWL_NOTIFY_ONSNATCH = False
PROWL_NOTIFY_ONDOWNLOAD = False
PROWL_NOTIFY_ONSUBTITLEDOWNLOAD = False
PROWL_API = None
PROWL_PRIORITY = False

USE_TWITTER = False
TWITTER_NOTIFY_ONSNATCH = False
TWITTER_NOTIFY_ONDOWNLOAD = False
TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD = False
TWITTER_USERNAME = None
TWITTER_PASSWORD = None
TWITTER_PREFIX = None
TWITTER_DMTO = None
TWITTER_USEDM = False

USE_BOXCAR = False
BOXCAR_NOTIFY_ONSNATCH = False
BOXCAR_NOTIFY_ONDOWNLOAD = False
BOXCAR_NOTIFY_ONSUBTITLEDOWNLOAD = False
BOXCAR_USERNAME = None
BOXCAR_PASSWORD = None
BOXCAR_PREFIX = None

USE_BOXCAR2 = False
BOXCAR2_NOTIFY_ONSNATCH = False
BOXCAR2_NOTIFY_ONDOWNLOAD = False
BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD = False
BOXCAR2_ACCESSTOKEN = None

USE_PUSHOVER = False
PUSHOVER_NOTIFY_ONSNATCH = False
PUSHOVER_NOTIFY_ONDOWNLOAD = False
PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD = False
PUSHOVER_USERKEY = None
PUSHOVER_APIKEY = None
PUSHOVER_DEVICE = None
PUSHOVER_SOUND = None

USE_LIBNOTIFY = False
LIBNOTIFY_NOTIFY_ONSNATCH = False
LIBNOTIFY_NOTIFY_ONDOWNLOAD = False
LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD = False

USE_NMJ = False
NMJ_HOST = None
NMJ_DATABASE = None
NMJ_MOUNT = None

ANIMESUPPORT = False
USE_ANIDB = False
ANIDB_USERNAME = None
ANIDB_PASSWORD = None
ANIDB_USE_MYLIST = False
ADBA_CONNECTION = None
ANIME_SPLIT_HOME = False

USE_SYNOINDEX = False

USE_NMJv2 = False
NMJv2_HOST = None
NMJv2_DATABASE = None
NMJv2_DBLOC = None

USE_SYNOLOGYNOTIFIER = False
SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH = False
SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD = False
SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD = False

USE_TRAKT = False
TRAKT_USERNAME = None
TRAKT_ACCESS_TOKEN = None
TRAKT_REFRESH_TOKEN = None
TRAKT_REMOVE_WATCHLIST = False
TRAKT_REMOVE_SERIESLIST = False
TRAKT_REMOVE_SHOW_FROM_SICKRAGE = False
TRAKT_SYNC_WATCHLIST = False
TRAKT_METHOD_ADD = None
TRAKT_START_PAUSED = False
TRAKT_USE_RECOMMENDED = False
TRAKT_SYNC = False
TRAKT_SYNC_REMOVE = False
TRAKT_DEFAULT_INDEXER = None
TRAKT_TIMEOUT = None
TRAKT_BLACKLIST_NAME = None

USE_PYTIVO = False
PYTIVO_NOTIFY_ONSNATCH = False
PYTIVO_NOTIFY_ONDOWNLOAD = False
PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD = False
PYTIVO_UPDATE_LIBRARY = False
PYTIVO_HOST = None
PYTIVO_SHARE_NAME = None
PYTIVO_TIVO_NAME = None

USE_NMA = False
NMA_NOTIFY_ONSNATCH = False
NMA_NOTIFY_ONDOWNLOAD = False
NMA_NOTIFY_ONSUBTITLEDOWNLOAD = False
NMA_API = None
NMA_PRIORITY = False

USE_PUSHALOT = False
PUSHALOT_NOTIFY_ONSNATCH = False
PUSHALOT_NOTIFY_ONDOWNLOAD = False
PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD = False
PUSHALOT_AUTHORIZATIONTOKEN = None

USE_PUSHBULLET = False
PUSHBULLET_NOTIFY_ONSNATCH = False
PUSHBULLET_NOTIFY_ONDOWNLOAD = False
PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD = False
PUSHBULLET_API = None
PUSHBULLET_DEVICE = None

USE_EMAIL = False
EMAIL_NOTIFY_ONSNATCH = False
EMAIL_NOTIFY_ONDOWNLOAD = False
EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD = False
EMAIL_HOST = None
EMAIL_PORT = 25
EMAIL_TLS = False
EMAIL_USER = None
EMAIL_PASSWORD = None
EMAIL_FROM = None
EMAIL_LIST = None

GUI_NAME = None
HOME_LAYOUT = None
HISTORY_LAYOUT = None
HISTORY_LIMIT = 0
DISPLAY_SHOW_SPECIALS = False
COMING_EPS_LAYOUT = None
COMING_EPS_DISPLAY_PAUSED = False
COMING_EPS_SORT = None
COMING_EPS_MISSED_RANGE = None
FUZZY_DATING = False
TRIM_ZERO = False
DATE_PRESET = None
TIME_PRESET = None
TIME_PRESET_W_SECONDS = None
TIMEZONE_DISPLAY = None
THEME_NAME = None
POSTER_SORTBY = None
POSTER_SORTDIR = None
FILTER_ROW = True

USE_SUBTITLES = False
SUBTITLES_LANGUAGES = None
SUBTITLES_DIR = None
SUBTITLES_SERVICES_LIST = None
SUBTITLES_SERVICES_ENABLED = None
SUBTITLES_HISTORY = False
EMBEDDED_SUBTITLES_ALL = False
SUBTITLES_HEARING_IMPAIRED = False
SUBTITLES_MULTI = False
SUBTITLES_EXTRA_SCRIPTS = None

ADDIC7ED_USER = None
ADDIC7ED_PASS = None

OPENSUBTITLES_USER = None
OPENSUBTITLES_PASS = None

LEGENDASTV_USER = None
LEGENDASTV_PASS = None

USE_FAILED_DOWNLOADS = False
DELETE_FAILED = False

EXTRA_SCRIPTS = None

REQUIRE_WORDS = None
IGNORE_WORDS = None
IGNORED_SUBS_LIST = None
SYNC_FILES = None

CALENDAR_UNPROTECTED = False
CALENDAR_ICONS = False
NO_RESTART = False

TMDB_API_KEY = 'edc5f123313769de83a71e157758030b'
# TRAKT_API_KEY = 'd4161a7a106424551add171e5470112e4afdaf2438e6ef2fe0548edc75924868'

THETVDB_APITOKEN = None

TRAKT_API_KEY = '5c65f55e11d48c35385d9e8670615763a605fad28374c8ae553a7b7a50651ddd'
TRAKT_API_SECRET = 'b53e32045ac122a445ef163e6d859403301ffe9b17fb8321d428531b69022a82'
TRAKT_PIN_URL = 'https://trakt.tv/pin/4562'
TRAKT_OAUTH_URL = 'https://trakt.tv/'
TRAKT_API_URL = 'https://api-v2launch.trakt.tv/'

FANART_API_KEY = '9b3afaf26f6241bdb57d6cc6bd798da7'

NOTIFIERS = None
NEWZNAB_DATA = None
TORRENTRSS_DATA = None

SHOWS_RECENT = []
CENSOREDITEMS = {}

def root_check():
    try:
        return not os.getuid() == 0
    except AttributeError:
        return not ctypes.windll.shell32.IsUserAnAdmin() != 0

def help_message():
    """
    LOGGER.info help message for commandline options
    """

    help_msg = "\n"
    help_msg += "Usage: " + APP_NAME + " <option> <another option>\n"
    help_msg += "\n"
    help_msg += "Options:\n"
    help_msg += "\n"
    help_msg += "    -h          --help              LOGGER.infos this message\n"
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
    help_msg += "                                    Default: " + PROG_DIR + "\n"
    help_msg += "                --config=<path>     Override config filename (full path including filename)\n"
    help_msg += "                                    to load configuration from \n"
    help_msg += "                                    Default: config.ini in " + PROG_DIR + " or --datadir location\n"
    help_msg += "                --noresize          Prevent resizing of the banner/posters even if PIL is installed\n"
    help_msg += "                --install-optional  Install optional pacakges from requirements folder\n"
    help_msg += "                --ssl               Enables ssl/https\n"
    help_msg += "                --user              Install pacakges from requirements folder as non-root user\n"

    return help_msg


def main():
    global APP_NAME, MY_FULLNAME, NO_RESIZE, MY_ARGS, WEB_PORT, WEB_NOLAUNCH, CREATEPID, DAEMONIZE, PIDFILE, \
        ROOT_DIR, PROG_DIR, DATA_DIR, CONFIG_FILE, WEB_SERVER, VERSIONUPDATER, DEVELOPER, LOGGER, ENABLE_HTTPS

    if sys.version_info < (2, 7):
        print("Sorry, SiCKRAGE requires Python 2.7+")
        sys.exit(1)

    # set thread name
    threading.currentThread().setName('MAIN')

    APP_NAME = 'SiCKRAGE'
    DATA_DIR = ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    PROG_DIR = os.path.abspath(os.path.dirname(__file__))
    MY_ARGS = sys.argv[1:]

    consoleLogging = (not hasattr(sys, "frozen")) or (APP_NAME.lower().find('-console') > 0)

    # defaults
    INSTALL_OPTIONAL = False

    # auto-detect user rights
    USER = root_check()

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
                 'ssl'
                 'user']
        )
    except getopt.GetoptError:
        sys.exit(help_message())

    for o, a in opts:
        # help message
        if o in ('-h', '--help'):
            sys.exit(help_message())

        # For now we'll just silence the logging
        if o in ('-q', '--quiet'):
            consoleLogging = False

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
            consoleLogging = False

            if sys.platform == 'win32' or sys.platform == 'darwin':
                DAEMONIZE = False

        # Write a pidfile if requested
        if o in ('--pidfile',):
            CREATEPID = True
            PIDFILE = str(a)

            # If the pidfile already exists, sickrage may still be running, so exit
            if os.path.exists(PIDFILE):
                sys.exit("PID file: " + PIDFILE + " already exists. Exiting.")

        # Specify folder to load the config file from
        if o in ('--config',):
            CONFIG_FILE = os.path.abspath(a)

        # Specify folder to use as the data dir
        if o in ('--datadir',):
            DATA_DIR = os.path.abspath(a)

        # Prevent resizing of the banner/posters even if PIL is installed
        if o in ('--noresize',):
            NO_RESIZE = True

        # Install optional packages from requirements folder
        if o in ('--install-optional',):
            INSTALL_OPTIONAL = True

        # Install ssl packages from requirements folder
        if o in ('--ssl',):
            ENABLE_HTTPS = True

        # Installs packages for non-root users
        if o in ('--user',):
            USER = True


    # install/upgrade pip and ssl contexts for required/optional imports
    if not DEVELOPER:
        # install pip package manager
        install_pip(user=USER)

        # install required packages
        install_reqs(optional=INSTALL_OPTIONAL, ssl=ENABLE_HTTPS, user=USER)

    # init logging
    from sickrage.core.srlogger import srLogger
    LOGGER = srLogger(consoleLogging=consoleLogging)

    # The pidfile is only useful in daemon mode, make sure we can write the file properly
    if CREATEPID:
        if DAEMONIZE:
            pid_dir = os.path.dirname(PIDFILE)
            if not os.access(pid_dir, os.F_OK):
                sys.exit("PID dir: " + pid_dir + " doesn't exist. Exiting.")
            if not os.access(pid_dir, os.W_OK):
                sys.exit("PID dir: " + pid_dir + " must be writable (write permissions). Exiting.")

        else:
            CREATEPID = False
            LOGGER.info("Not running in daemon mode. PID file creation disabled.\n")

    # If they don't specify a config file then put it in the data dir
    if not CONFIG_FILE:
        CONFIG_FILE = os.path.join(DATA_DIR, "config.ini")

    # Make sure that we can create the data dir
    if not os.access(DATA_DIR, os.F_OK):
        try:
            os.makedirs(DATA_DIR, 0o744)
        except os.error:
            raise SystemExit("Unable to create datadir '" + DATA_DIR + "'")

    # Make sure we can write to the data dir
    if not os.access(DATA_DIR, os.W_OK):
        raise SystemExit("Datadir must be writeable '" + DATA_DIR + "'")

    # Make sure we can write to the config file
    if not os.access(CONFIG_FILE, os.W_OK):
        if os.path.isfile(CONFIG_FILE):
            raise SystemExit("Config file '" + CONFIG_FILE + "' must be writeable.")
        elif not os.access(os.path.dirname(CONFIG_FILE), os.W_OK):
            raise SystemExit(
                    "Config file root dir '" + os.path.dirname(CONFIG_FILE) + "' must be writeable.")

    try:
        # initialize and startup sickrage
        from sickrage import core
        if core.initialize():
            WEB_SERVER.start()
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback)
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        sys.exit(1)
    sys.exit(0)
