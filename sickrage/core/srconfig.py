# Author: echel0n <tv@gmail.com>
# URL: https://tv
# Git: https://github.com/V/git
#
# This file is part of 
#
# is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with   If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import base64
import datetime
import os
import os.path
import pickle
import re
import sys
import uuid
from itertools import izip, cycle

import rarfile
from configobj import ConfigObj

import sickrage
from sickrage.core.classes import srIntervalTrigger
from sickrage.core.common import SD, WANTED, SKIPPED, Quality
from sickrage.core.helpers import backupVersionedFile, makeDir, generateCookieSecret, autoType, get_lan_ip, extractZip


class srConfig(object):
    def __init__(self):
        self.loaded = False

        self.DEBUG = 0
        self.DEVELOPER = 0

        self.CONFIG_OBJ = None
        self.CONFIG_VERSION = 11
        self.ENCRYPTION_VERSION = 0
        self.ENCRYPTION_SECRET = generateCookieSecret()

        self.LAST_DB_COMPACT = 0

        self.CENSORED_ITEMS = {}

        self.NAMING_EP_TYPE = ("%(seasonnumber)dx%(episodenumber)02d",
                               "s%(seasonnumber)02de%(episodenumber)02d",
                               "S%(seasonnumber)02dE%(episodenumber)02d",
                               "%(seasonnumber)02dx%(episodenumber)02d")
        self.SPORTS_EP_TYPE = ("%(seasonnumber)dx%(episodenumber)02d",
                               "s%(seasonnumber)02de%(episodenumber)02d",
                               "S%(seasonnumber)02dE%(episodenumber)02d",
                               "%(seasonnumber)02dx%(episodenumber)02d")
        self.NAMING_EP_TYPE_TEXT = ("1x02", "s01e02", "S01E02", "01x02")
        self.NAMING_MULTI_EP_TYPE = {0: ["-%(episodenumber)02d"] * len(self.NAMING_EP_TYPE),
                                     1: [" - " + x for x in self.NAMING_EP_TYPE],
                                     2: [x + "%(episodenumber)02d" for x in ("x", "e", "E", "x")]}
        self.NAMING_MULTI_EP_TYPE_TEXT = ("extend", "duplicate", "repeat")
        self.NAMING_SEP_TYPE = (" - ", " ")
        self.NAMING_SEP_TYPE_TEXT = (" - ", "space")

        self.LOG_DIR = os.path.abspath(os.path.join(sickrage.DATA_DIR, 'logs'))
        self.LOG_FILE = os.path.abspath(os.path.join(self.LOG_DIR, 'sickrage.log'))
        self.LOG_SIZE = 1048576
        self.LOG_NR = 5
        self.VERSION_NOTIFY = 1
        self.AUTO_UPDATE = 1
        self.NOTIFY_ON_UPDATE = 1
        self.PIP_PATH = "pip"
        self.GIT_RESET = 1
        self.GIT_USERNAME = ""
        self.GIT_PASSWORD = ""
        self.GIT_PATH = "git"
        self.GIT_AUTOISSUES = 0
        self.GIT_NEWVER = 0
        self.CHANGES_URL = 'https://git.sickrage.ca/SiCKRAGE/sickrage/raw/master/changelog.md'
        self.SOCKET_TIMEOUT = 30
        self.WEB_HOST = get_lan_ip()
        self.WEB_PORT = 8081
        self.WEB_LOG = 0
        self.WEB_ROOT = ""
        self.WEB_USERNAME = ""
        self.WEB_PASSWORD = ""
        self.WEB_IPV6 = 0
        self.WEB_COOKIE_SECRET = generateCookieSecret()
        self.WEB_USE_GZIP = 1
        self.HANDLE_REVERSE_PROXY = 0
        self.PROXY_SETTING = ""
        self.PROXY_INDEXERS = 1
        self.SSL_VERIFY = 1
        self.ENABLE_HTTPS = 0
        self.HTTPS_CERT = os.path.abspath(os.path.join(sickrage.PROG_DIR, 'server.crt'))
        self.HTTPS_KEY = os.path.abspath(os.path.join(sickrage.PROG_DIR, 'server.key'))
        self.API_KEY = ""
        self.API_ROOT = None
        self.INDEXER_DEFAULT_LANGUAGE = 'en'
        self.EP_DEFAULT_DELETED_STATUS = 6
        self.LAUNCH_BROWSER = 0
        self.SHOWUPDATE_STALE = 1
        self.ROOT_DIRS = ""
        self.CPU_PRESET = "NORMAL"
        self.ANON_REDIRECT = 'http://nullrefer.com/?'
        self.DOWNLOAD_URL = ""
        self.TRASH_REMOVE_SHOW = 0
        self.TRASH_ROTATE_LOGS = 0
        self.SORT_ARTICLE = 0
        self.DISPLAY_ALL_SEASONS = 1
        self.DEFAULT_PAGE = "home"
        self.USE_LISTVIEW = 0

        self.QUALITY_DEFAULT = SD
        self.STATUS_DEFAULT = SKIPPED
        self.STATUS_DEFAULT_AFTER = WANTED
        self.FLATTEN_FOLDERS_DEFAULT = 0
        self.SUBTITLES_DEFAULT = 0
        self.INDEXER_DEFAULT = 0
        self.INDEXER_TIMEOUT = 120
        self.SCENE_DEFAULT = 0
        self.ANIME_DEFAULT = 0
        self.ARCHIVE_DEFAULT = 0
        self.NAMING_MULTI_EP = 0
        self.NAMING_ANIME_MULTI_EP = 0
        self.NAMING_PATTERN = None
        self.NAMING_ABD_PATTERN = None
        self.NAMING_CUSTOM_ABD = 0
        self.NAMING_SPORTS_PATTERN = None
        self.NAMING_CUSTOM_SPORTS = 0
        self.NAMING_ANIME_PATTERN = None
        self.NAMING_CUSTOM_ANIME = 0
        self.NAMING_FORCE_FOLDERS = 0
        self.NAMING_STRIP_YEAR = 0
        self.NAMING_ANIME = None
        self.USE_NZBS = 0
        self.USE_TORRENTS = 0
        self.NZB_METHOD = None
        self.NZB_DIR = None
        self.USENET_RETENTION = 500
        self.TORRENT_METHOD = None
        self.TORRENT_DIR = None
        self.DOWNLOAD_PROPERS = 0
        self.ENABLE_RSS_CACHE = 1
        self.PROPER_SEARCHER_INTERVAL = None
        self.ALLOW_HIGH_PRIORITY = 0
        self.SAB_FORCED = 0
        self.RANDOMIZE_PROVIDERS = 0
        self.MIN_AUTOPOSTPROCESSOR_FREQ = 1
        self.MIN_NAMECACHE_FREQ = 1
        self.MIN_DAILY_SEARCHER_FREQ = 10
        self.MIN_BACKLOG_SEARCHER_FREQ = 10
        self.MIN_VERSION_UPDATER_FREQ = 1
        self.MIN_SUBTITLE_SEARCHER_FREQ = 1
        self.BACKLOG_DAYS = 7
        self.ADD_SHOWS_WO_DIR = 0
        self.CREATE_MISSING_SHOW_DIRS = 0
        self.RENAME_EPISODES = 0
        self.AIRDATE_EPISODES = 0
        self.FILE_TIMESTAMP_TIMEZONE = None
        self.PROCESS_AUTOMATICALLY = 0
        self.NO_DELETE = 0
        self.KEEP_PROCESSED_DIR = 0
        self.PROCESS_METHOD = None
        self.DELRARCONTENTS = 0
        self.MOVE_ASSOCIATED_FILES = 0
        self.POSTPONE_IF_SYNC_FILES = 1
        self.NFO_RENAME = 1
        self.TV_DOWNLOAD_DIR = None
        self.UNPACK = 0
        self.SKIP_REMOVED_FILES = 0
        self.NZBS = 0
        self.NZBS_UID = None
        self.NZBS_HASH = None
        self.OMGWTFNZBS = 0
        self.NEWZBIN = 0
        self.NEWZBIN_USERNAME = None
        self.NEWZBIN_PASSWORD = None
        self.SAB_USERNAME = None
        self.SAB_PASSWORD = None
        self.SAB_APIKEY = None
        self.SAB_CATEGORY = None
        self.SAB_CATEGORY_BACKLOG = None
        self.SAB_CATEGORY_ANIME = None
        self.SAB_CATEGORY_ANIME_BACKLOG = None
        self.SAB_HOST = None
        self.NZBGET_USERNAME = None
        self.NZBGET_PASSWORD = None
        self.NZBGET_CATEGORY = None
        self.NZBGET_CATEGORY_BACKLOG = None
        self.NZBGET_CATEGORY_ANIME = None
        self.NZBGET_CATEGORY_ANIME_BACKLOG = None
        self.NZBGET_HOST = None
        self.NZBGET_USE_HTTPS = 0
        self.NZBGET_PRIORITY = 100
        self.TORRENT_USERNAME = None
        self.TORRENT_PASSWORD = None
        self.TORRENT_HOST = None
        self.TORRENT_PATH = None
        self.TORRENT_SEED_TIME = None
        self.TORRENT_PAUSED = 0
        self.TORRENT_HIGH_BANDWIDTH = 0
        self.TORRENT_LABEL = None
        self.TORRENT_LABEL_ANIME = None
        self.TORRENT_VERIFY_CERT = 0
        self.TORRENT_RPCURL = None
        self.TORRENT_AUTH_TYPE = None
        self.TORRENT_TRACKERS = "udp://coppersurfer.tk:6969/announce," \
                                "udp://open.demonii.com:1337," \
                                "udp://exodus.desync.com:6969," \
                                "udp://9.rarbg.me:2710/announce," \
                                "udp://glotorrents.pw:6969/announce," \
                                "udp://tracker.openbittorrent.com:80/announce," \
                                "udp://9.rarbg.to:2710/announce"
        self.USE_KODI = 0
        self.KODI_ALWAYS_ON = 1
        self.KODI_NOTIFY_ONSNATCH = 0
        self.KODI_NOTIFY_ONDOWNLOAD = 0
        self.KODI_NOTIFY_ONSUBTITLEDOWNLOAD = 0
        self.KODI_UPDATE_LIBRARY = 0
        self.KODI_UPDATE_FULL = 0
        self.KODI_UPDATE_ONLYFIRST = 0
        self.KODI_HOST = None
        self.KODI_USERNAME = None
        self.KODI_PASSWORD = None
        self.USE_PLEX = 0
        self.PLEX_NOTIFY_ONSNATCH = 0
        self.PLEX_NOTIFY_ONDOWNLOAD = 0
        self.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD = 0
        self.PLEX_UPDATE_LIBRARY = 0
        self.PLEX_SERVER_HOST = None
        self.PLEX_SERVER_TOKEN = None
        self.PLEX_HOST = None
        self.PLEX_USERNAME = None
        self.PLEX_PASSWORD = None
        self.USE_PLEX_CLIENT = 0
        self.PLEX_CLIENT_USERNAME = None
        self.PLEX_CLIENT_PASSWORD = None
        self.USE_EMBY = 0
        self.EMBY_HOST = None
        self.EMBY_APIKEY = None
        self.USE_GROWL = 0
        self.GROWL_NOTIFY_ONSNATCH = 0
        self.GROWL_NOTIFY_ONDOWNLOAD = 0
        self.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD = 0
        self.GROWL_HOST = None
        self.GROWL_PASSWORD = None
        self.USE_FREEMOBILE = 0
        self.FREEMOBILE_NOTIFY_ONSNATCH = 0
        self.FREEMOBILE_NOTIFY_ONDOWNLOAD = 0
        self.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD = 0
        self.FREEMOBILE_ID = None
        self.FREEMOBILE_APIKEY = None
        self.USE_PROWL = 0
        self.PROWL_NOTIFY_ONSNATCH = 0
        self.PROWL_NOTIFY_ONDOWNLOAD = 0
        self.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD = 0
        self.PROWL_API = None
        self.PROWL_PRIORITY = 0
        self.USE_TWITTER = 0
        self.TWITTER_NOTIFY_ONSNATCH = 0
        self.TWITTER_NOTIFY_ONDOWNLOAD = 0
        self.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD = 0
        self.TWITTER_USERNAME = None
        self.TWITTER_PASSWORD = None
        self.TWITTER_PREFIX = None
        self.TWITTER_DMTO = None
        self.TWITTER_USEDM = 0
        self.USE_BOXCAR = 0
        self.BOXCAR_NOTIFY_ONSNATCH = 0
        self.BOXCAR_NOTIFY_ONDOWNLOAD = 0
        self.BOXCAR_NOTIFY_ONSUBTITLEDOWNLOAD = 0
        self.BOXCAR_USERNAME = None
        self.BOXCAR_PASSWORD = None
        self.BOXCAR_PREFIX = None
        self.USE_BOXCAR2 = 0
        self.BOXCAR2_NOTIFY_ONSNATCH = 0
        self.BOXCAR2_NOTIFY_ONDOWNLOAD = 0
        self.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD = 0
        self.BOXCAR2_ACCESSTOKEN = None
        self.USE_PUSHOVER = 0
        self.PUSHOVER_NOTIFY_ONSNATCH = 0
        self.PUSHOVER_NOTIFY_ONDOWNLOAD = 0
        self.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD = 0
        self.PUSHOVER_USERKEY = None
        self.PUSHOVER_APIKEY = None
        self.PUSHOVER_DEVICE = None
        self.PUSHOVER_SOUND = None
        self.USE_LIBNOTIFY = 0
        self.LIBNOTIFY_NOTIFY_ONSNATCH = 0
        self.LIBNOTIFY_NOTIFY_ONDOWNLOAD = 0
        self.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD = 0
        self.USE_NMJ = 0
        self.NMJ_HOST = None
        self.NMJ_DATABASE = None
        self.NMJ_MOUNT = None
        self.ANIMESUPPORT = 0
        self.USE_ANIDB = 0
        self.ANIDB_USERNAME = None
        self.ANIDB_PASSWORD = None
        self.ANIDB_USE_MYLIST = 0
        self.ANIME_SPLIT_HOME = 0
        self.USE_SYNOINDEX = 0
        self.USE_NMJv2 = 0
        self.NMJv2_HOST = None
        self.NMJv2_DATABASE = None
        self.NMJv2_DBLOC = None
        self.USE_SYNOLOGYNOTIFIER = 0
        self.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH = 0
        self.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD = 0
        self.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD = 0
        self.USE_TRAKT = 0
        self.TRAKT_USERNAME = ""
        self.TRAKT_OAUTH_TOKEN = ""
        self.TRAKT_REMOVE_WATCHLIST = 0
        self.TRAKT_REMOVE_SERIESLIST = 0
        self.TRAKT_REMOVE_SHOW_FROM_SICKRAGE = 0
        self.TRAKT_SYNC_WATCHLIST = 0
        self.TRAKT_METHOD_ADD = 0
        self.TRAKT_START_PAUSED = 0
        self.TRAKT_USE_RECOMMENDED = 0
        self.TRAKT_SYNC = 0
        self.TRAKT_SYNC_REMOVE = 0
        self.TRAKT_DEFAULT_INDEXER = 1
        self.TRAKT_TIMEOUT = 30
        self.TRAKT_BLACKLIST_NAME = ""
        self.USE_PYTIVO = 0
        self.PYTIVO_NOTIFY_ONSNATCH = 0
        self.PYTIVO_NOTIFY_ONDOWNLOAD = 0
        self.PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD = 0
        self.PYTIVO_UPDATE_LIBRARY = 0
        self.PYTIVO_HOST = None
        self.PYTIVO_SHARE_NAME = None
        self.PYTIVO_TIVO_NAME = None
        self.USE_NMA = 0
        self.NMA_NOTIFY_ONSNATCH = 0
        self.NMA_NOTIFY_ONDOWNLOAD = 0
        self.NMA_NOTIFY_ONSUBTITLEDOWNLOAD = 0
        self.NMA_API = None
        self.NMA_PRIORITY = 0
        self.USE_PUSHALOT = 0
        self.PUSHALOT_NOTIFY_ONSNATCH = 0
        self.PUSHALOT_NOTIFY_ONDOWNLOAD = 0
        self.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD = 0
        self.PUSHALOT_AUTHORIZATIONTOKEN = None
        self.USE_PUSHBULLET = 0
        self.PUSHBULLET_NOTIFY_ONSNATCH = 0
        self.PUSHBULLET_NOTIFY_ONDOWNLOAD = 0
        self.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD = 0
        self.PUSHBULLET_API = None
        self.PUSHBULLET_DEVICE = None
        self.USE_EMAIL = 0
        self.EMAIL_NOTIFY_ONSNATCH = 0
        self.EMAIL_NOTIFY_ONDOWNLOAD = 0
        self.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD = 0
        self.EMAIL_HOST = None
        self.EMAIL_PORT = 25
        self.EMAIL_TLS = 0
        self.EMAIL_USER = None
        self.EMAIL_PASSWORD = None
        self.EMAIL_FROM = None
        self.EMAIL_LIST = None
        self.GUI_NAME = 'default'
        self.GUI_DIR = os.path.join(sickrage.PROG_DIR, 'core', 'webserver', 'gui', self.GUI_NAME)
        self.HOME_LAYOUT = None
        self.HISTORY_LAYOUT = None
        self.HISTORY_LIMIT = 0
        self.DISPLAY_SHOW_SPECIALS = 0
        self.COMING_EPS_LAYOUT = None
        self.COMING_EPS_DISPLAY_PAUSED = 0
        self.COMING_EPS_SORT = None
        self.COMING_EPS_MISSED_RANGE = None
        self.FUZZY_DATING = 0
        self.TRIM_ZERO = 0
        self.DATE_PRESET = None
        self.TIME_PRESET = None
        self.TIME_PRESET_W_SECONDS = None
        self.TIMEZONE_DISPLAY = None
        self.THEME_NAME = None
        self.POSTER_SORTBY = None
        self.POSTER_SORTDIR = None
        self.FILTER_ROW = 1
        self.USE_SUBTITLES = 0
        self.SUBTITLES_LANGUAGES = None
        self.SUBTITLES_DIR = None
        self.SUBTITLES_SERVICES_LIST = None
        self.SUBTITLES_SERVICES_ENABLED = None
        self.SUBTITLES_HISTORY = 0
        self.EMBEDDED_SUBTITLES_ALL = 0
        self.SUBTITLES_HEARING_IMPAIRED = 0
        self.SUBTITLES_MULTI = 0
        self.SUBTITLES_EXTRA_SCRIPTS = None
        self.ADDIC7ED_USER = None
        self.ADDIC7ED_PASS = None
        self.OPENSUBTITLES_USER = None
        self.OPENSUBTITLES_PASS = None
        self.LEGENDASTV_USER = None
        self.LEGENDASTV_PASS = None
        self.ITASA_USER = None
        self.ITASA_PASS = None
        self.USE_FAILED_DOWNLOADS = 0
        self.DELETE_FAILED = 0
        self.EXTRA_SCRIPTS = None
        self.REQUIRE_WORDS = None
        self.IGNORE_WORDS = None
        self.IGNORED_SUBS_LIST = None
        self.SYNC_FILES = None
        self.CALENDAR_UNPROTECTED = 0
        self.CALENDAR_ICONS = 0
        self.NO_RESTART = 0
        self.THETVDB_APITOKEN = None
        self.TRAKT_API_KEY = '5c65f55e11d48c35385d9e8670615763a605fad28374c8ae553a7b7a50651ddd'
        self.TRAKT_API_SECRET = 'b53e32045ac122a445ef163e6d859403301ffe9b17fb8321d428531b69022a82'
        self.TRAKT_APP_ID = '4562'
        self.TRAKT_OAUTH_URL = 'https://trakt.tv/'
        self.TRAKT_API_URL = 'https://api.trakt.tv/'
        self.FANART_API_KEY = '9b3afaf26f6241bdb57d6cc6bd798da7'
        self.SHOWS_RECENT = []

        self.DEFAULT_AUTOPOSTPROCESSOR_FREQ = 10
        self.AUTOPOSTPROCESSOR_FREQ = None

        self.DEFAULT_NAMECACHE_FREQ = 10
        self.NAMECACHE_FREQ = None

        self.DEFAULT_DAILY_SEARCHER_FREQ = 40
        self.DAILY_SEARCHER_FREQ = None

        self.DEFAULT_BACKLOG_SEARCHER_FREQ = 21
        self.BACKLOG_SEARCHER_FREQ = None

        self.DEFAULT_VERSION_UPDATE_FREQ = 1
        self.VERSION_UPDATER_FREQ = None

        self.DEFAULT_SUBTITLE_SEARCHER_FREQ = 1
        self.SUBTITLE_SEARCHER_FREQ = None

        self.DEFAULT_SHOWUPDATE_HOUR = 3
        self.SHOWUPDATE_HOUR = None

        self.QUALITY_SIZES = Quality.qualitySizes

        self.CUSTOM_PROVIDERS = None

        self.GIT_REMOTE = "origin"
        self.GIT_REMOTE_URL = "https://git.sickrage.ca/SiCKRAGE/sickrage"

        self.RANDOM_USER_AGENT = 0

        self.FANART_BACKGROUND = 1
        self.FANART_BACKGROUND_OPACITY = 0.4

        self.UNRAR_TOOL = rarfile.UNRAR_TOOL
        self.UNRAR_ALT_TOOL = rarfile.ALT_TOOL

    def change_unrar_tool(self, unrar_tool, unrar_alt_tool):
        # Check for failed unrar attempt, and remove it
        # Must be done before unrar is ever called or the self-extractor opens and locks startup
        bad_unrar = os.path.join(sickrage.DATA_DIR, 'unrar.exe')
        if os.path.exists(bad_unrar) and os.path.getsize(bad_unrar) == 447440:
            try:
                os.remove(bad_unrar)
            except OSError as e:
                sickrage.srCore.srLogger.warning(
                    "Unable to delete bad unrar.exe file {}: {}. You should delete it manually".format(bad_unrar,
                                                                                                       e.strerror))

        try:
            rarfile.custom_check(unrar_tool)
        except (rarfile.RarCannotExec, rarfile.RarExecError, OSError, IOError):
            # Let's just return right now if the defaults work
            try:

                test = rarfile._check_unrar_tool()
                if test:
                    # These must always be set to something before returning
                    self.UNRAR_TOOL = rarfile.UNRAR_TOOL
                    self.ALT_UNRAR_TOOL = rarfile.ALT_TOOL
                    return True
            except (rarfile.RarCannotExec, rarfile.RarExecError, OSError, IOError):
                pass

            if sys.platform == 'win32':
                # Look for WinRAR installations
                found = False
                winrar_path = 'WinRAR\\UnRAR.exe'
                # Make a set of unique paths to check from existing environment variables
                check_locations = {
                    os.path.join(location, winrar_path) for location in (
                    os.environ.get("ProgramW6432"), os.environ.get("ProgramFiles(x86)"),
                    os.environ.get("ProgramFiles"), re.sub(r'\s?\(x86\)', '', os.environ["ProgramFiles"])
                ) if location
                }
                check_locations.add(os.path.join(sickrage.PROG_DIR, 'unrar\\unrar.exe'))

                for check in check_locations:
                    if os.path.isfile(check):
                        # Can use it?
                        try:
                            rarfile.custom_check(check)
                            unrar_tool = check
                            found = True
                            break
                        except (rarfile.RarCannotExec, rarfile.RarExecError, OSError, IOError):
                            found = False

                # Download
                if not found:
                    sickrage.srCore.srLogger.info('Trying to download unrar.exe and set the path')
                    unrar_dir = os.path.join(sickrage.PROG_DIR, 'unrar')
                    unrar_zip = os.path.join(unrar_dir, 'unrar_win.zip')

                    if (sickrage.srCore.srWebSession.download(
                            "https://sickrage.ca/downloads/unrar_win.zip", filename=unrar_zip,
                    ) and extractZip(archive=unrar_zip, targetDir=unrar_dir)):
                        try:
                            os.remove(unrar_zip)
                        except OSError as e:
                            sickrage.srCore.srLogger.info(
                                "Unable to delete downloaded file {}: {}. You may delete it manually".format(unrar_zip,
                                                                                                             e.strerror))

                        check = os.path.join(unrar_dir, "unrar.exe")
                        try:
                            rarfile.custom_check(check)
                            unrar_tool = check
                            sickrage.srCore.srLogger.info('Successfully downloaded unrar.exe and set as unrar tool')
                        except (rarfile.RarCannotExec, rarfile.RarExecError, OSError, IOError):
                            sickrage.srCore.srLogger.info(
                                'Sorry, unrar was not set up correctly. Try installing WinRAR and make sure it is on the system PATH')
                    else:
                        sickrage.srCore.srLogger.info('Unable to download unrar.exe')

        # These must always be set to something before returning
        self.UNRAR_TOOL = rarfile.UNRAR_TOOL = rarfile.ORIG_UNRAR_TOOL = unrar_tool
        self.UNRAR_ALT_TOOL = rarfile.ALT_TOOL = unrar_alt_tool

        try:
            rarfile._check_unrar_tool()
            return True
        except (rarfile.RarCannotExec, rarfile.RarExecError, OSError, IOError):
            if self.UNPACK == 1:
                sickrage.srCore.srLogger.info('Disabling UNPACK setting because no unrar is installed.')
                self.UNPACK = 0

    def change_https_cert(self, https_cert):
        """
        Replace HTTPS Certificate file path

        :param https_cert: path to the new certificate file
        :return: True on success, False on failure
        """

        if https_cert == '':
            self.HTTPS_CERT = ''
            return True

        if os.path.normpath(self.HTTPS_CERT) != os.path.normpath(https_cert):
            if makeDir(os.path.dirname(os.path.abspath(https_cert))):
                self.HTTPS_CERT = os.path.normpath(https_cert)
                sickrage.srCore.srLogger.info("Changed https cert path to " + https_cert)
            else:
                return False

        return True

    def change_https_key(self, https_key):
        """
        Replace HTTPS Key file path

        :param https_key: path to the new key file
        :return: True on success, False on failure
        """
        if https_key == '':
            self.HTTPS_KEY = ''
            return True

        if os.path.normpath(self.HTTPS_KEY) != os.path.normpath(https_key):
            if makeDir(os.path.dirname(os.path.abspath(https_key))):
                self.HTTPS_KEY = os.path.normpath(https_key)
                sickrage.srCore.srLogger.info("Changed https key path to " + https_key)
            else:
                return False

        return True

    def change_nzb_dir(self, nzb_dir):
        """
        Change NZB Folder

        :param nzb_dir: New NZB Folder location
        :return: True on success, False on failure
        """
        if nzb_dir == '':
            self.NZB_DIR = ''
            return True

        if os.path.normpath(self.NZB_DIR) != os.path.normpath(nzb_dir):
            if makeDir(nzb_dir):
                self.NZB_DIR = os.path.normpath(nzb_dir)
                sickrage.srCore.srLogger.info("Changed NZB folder to " + nzb_dir)
            else:
                return False

        return True

    def change_torrent_dir(self, torrent_dir):
        """
        Change torrent directory

        :param torrent_dir: New torrent directory
        :return: True on success, False on failure
        """
        if torrent_dir == '':
            self.TORRENT_DIR = ''
            return True

        if os.path.normpath(self.TORRENT_DIR) != os.path.normpath(torrent_dir):
            if makeDir(torrent_dir):
                self.TORRENT_DIR = os.path.normpath(torrent_dir)
                sickrage.srCore.srLogger.info("Changed torrent folder to " + torrent_dir)
            else:
                return False

        return True

    def change_tv_download_dir(self, tv_download_dir):
        """
        Change TV_DOWNLOAD directory (used by postprocessor)

        :param tv_download_dir: New tv download directory
        :return: True on success, False on failure
        """
        if tv_download_dir == '':
            self.TV_DOWNLOAD_DIR = ''
            return True

        if os.path.normpath(self.TV_DOWNLOAD_DIR) != os.path.normpath(tv_download_dir):
            if makeDir(tv_download_dir):
                self.TV_DOWNLOAD_DIR = os.path.normpath(tv_download_dir)
                sickrage.srCore.srLogger.info("Changed TV download folder to " + tv_download_dir)
            else:
                return False

        return True

    def change_autopostprocessor_freq(self, freq):
        """
        Change frequency of automatic postprocessing thread
        TODO: Make all thread frequency changers in config.py return True/False status

        :param freq: New frequency
        """
        self.AUTOPOSTPROCESSOR_FREQ = self.to_int(freq, default=self.DEFAULT_AUTOPOSTPROCESSOR_FREQ)

        if self.AUTOPOSTPROCESSOR_FREQ < self.MIN_AUTOPOSTPROCESSOR_FREQ:
            self.AUTOPOSTPROCESSOR_FREQ = self.MIN_AUTOPOSTPROCESSOR_FREQ

        sickrage.srCore.srScheduler.modify_job('POSTPROCESSOR',
                                               trigger=srIntervalTrigger(
                                                   **{'minutes': self.AUTOPOSTPROCESSOR_FREQ,
                                                      'min': self.MIN_AUTOPOSTPROCESSOR_FREQ}))

    def change_daily_searcher_freq(self, freq):
        """
        Change frequency of daily search thread

        :param freq: New frequency
        """
        self.DAILY_SEARCHER_FREQ = self.to_int(freq, default=self.DEFAULT_DAILY_SEARCHER_FREQ)
        sickrage.srCore.srScheduler.modify_job('DAILYSEARCHER',
                                               trigger=srIntervalTrigger(
                                                   **{'minutes': self.DAILY_SEARCHER_FREQ,
                                                      'min': self.MIN_DAILY_SEARCHER_FREQ}))

    def change_backlog_searcher_freq(self, freq):
        """
        Change frequency of backlog thread

        :param freq: New frequency
        """
        self.BACKLOG_SEARCHER_FREQ = self.to_int(freq, default=self.DEFAULT_BACKLOG_SEARCHER_FREQ)
        self.MIN_BACKLOG_SEARCHER_FREQ = sickrage.srCore.BACKLOGSEARCHER.get_backlog_cycle_time()
        sickrage.srCore.srScheduler.modify_job('BACKLOG',
                                               trigger=srIntervalTrigger(
                                                   **{'minutes': self.BACKLOG_SEARCHER_FREQ,
                                                      'min': self.MIN_BACKLOG_SEARCHER_FREQ}))

    def change_updater_freq(self, freq):
        """
        Change frequency of version updater thread

        :param freq: New frequency
        """
        self.VERSION_UPDATER_FREQ = self.to_int(freq, default=self.DEFAULT_VERSION_UPDATE_FREQ)
        sickrage.srCore.srScheduler.modify_job('VERSIONUPDATER',
                                               trigger=srIntervalTrigger(
                                                   **{'hours': self.VERSION_UPDATER_FREQ,
                                                      'min': self.MIN_VERSION_UPDATER_FREQ}))

    def change_showupdate_hour(self, freq):
        """
        Change frequency of show updater thread

        :param freq: New frequency
        """
        self.SHOWUPDATE_HOUR = self.to_int(freq, default=self.DEFAULT_SHOWUPDATE_HOUR)
        if self.SHOWUPDATE_HOUR < 0 or self.SHOWUPDATE_HOUR > 23:
            self.SHOWUPDATE_HOUR = 0

        sickrage.srCore.srScheduler.modify_job('SHOWUPDATER',
                                               trigger=srIntervalTrigger(
                                                   **{'hours': 1,
                                                      'start_date': datetime.datetime.now().replace(
                                                          hour=self.SHOWUPDATE_HOUR)}))

    def change_subtitle_searcher_freq(self, freq):
        """
        Change frequency of subtitle thread

        :param freq: New frequency
        """
        self.SUBTITLE_SEARCHER_FREQ = self.to_int(freq, default=self.DEFAULT_SUBTITLE_SEARCHER_FREQ)
        sickrage.srCore.srScheduler.modify_job('SUBTITLESEARCHER',
                                               trigger=srIntervalTrigger(
                                                   **{'hours': self.SUBTITLE_SEARCHER_FREQ,
                                                      'min': self.MIN_SUBTITLE_SEARCHER_FREQ}))

    def change_version_notify(self, version_notify):
        """
        Change frequency of versioncheck thread

        :param version_notify: New frequency
        """
        self.VERSION_NOTIFY = self.checkbox_to_value(version_notify)
        if not self.VERSION_NOTIFY:
            sickrage.srCore.NEWEST_VERSION_STRING = None

    def change_download_propers(self, download_propers):
        """
        Enable/Disable proper download thread
        TODO: Make this return True/False on success/failure

        :param download_propers: New desired state
        """
        self.DOWNLOAD_PROPERS = self.checkbox_to_value(download_propers)
        job = sickrage.srCore.srScheduler.get_job('PROPERSEARCHER')
        (job.pause, job.resume)[self.DOWNLOAD_PROPERS]()

    def change_use_trakt(self, use_trakt):
        """
        Enable/disable trakt thread
        TODO: Make this return true/false on success/failure

        :param use_trakt: New desired state
        """
        self.USE_TRAKT = self.checkbox_to_value(use_trakt)
        job = sickrage.srCore.srScheduler.get_job('TRAKTSEARCHER')
        (job.pause, job.resume)[self.USE_TRAKT]()

    def change_use_subtitles(self, use_subtitles):
        """
        Enable/Disable subtitle searcher
        TODO: Make this return true/false on success/failure

        :param use_subtitles: New desired state
        """
        self.USE_SUBTITLES = self.checkbox_to_value(use_subtitles)
        job = sickrage.srCore.srScheduler.get_job('SUBTITLESEARCHER')
        (job.pause, job.resume)[self.USE_SUBTITLES]()

    def change_process_automatically(self, process_automatically):
        """
        Enable/Disable postprocessor thread
        TODO: Make this return True/False on success/failure

        :param process_automatically: New desired state
        """
        self.PROCESS_AUTOMATICALLY = self.checkbox_to_value(process_automatically)
        job = sickrage.srCore.srScheduler.get_job('POSTPROCESSOR')
        (job.pause, job.resume)[self.PROCESS_AUTOMATICALLY]()

    def checkbox_to_value(self, option, value_on=1, value_off=0):
        """
        Turns checkbox option 'on' or 'true' to value_on (1)
        any other value returns value_off (0)
        """

        if isinstance(option, list):
            option = option[-1]

        if option == 'on' or option == 'true':
            return value_on

        return value_off

    def clean_host(self, host, default_port=None):
        """
        Returns host or host:port or empty string from a given url or host
        If no port is found and default_port is given use host:default_port
        """

        host = host.strip()

        if host:

            match_host_port = re.search(r'(?:http.*://)?(?P<host>[^:/]+).?(?P<port>[0-9]*).*', host)

            cleaned_host = match_host_port.group('host')
            cleaned_port = match_host_port.group('port')

            if cleaned_host:

                if cleaned_port:
                    host = cleaned_host + ':' + cleaned_port

                elif default_port:
                    host = cleaned_host + ':' + str(default_port)

                else:
                    host = cleaned_host

            else:
                host = ''

        return host

    def clean_hosts(self, hosts, default_port=None):
        """
        Returns list of cleaned hosts by Config.clean_host

        :param hosts: list of hosts
        :param default_port: default port to use
        :return: list of cleaned hosts
        """
        cleaned_hosts = []

        for cur_host in [x.strip() for x in hosts.split(",")]:
            if cur_host:
                cleaned_host = self.clean_host(cur_host, default_port)
                if cleaned_host:
                    cleaned_hosts.append(cleaned_host)

        if cleaned_hosts:
            cleaned_hosts = ",".join(cleaned_hosts)

        else:
            cleaned_hosts = ''

        return cleaned_hosts

    def to_int(self, val, default=0):
        """ Return int value of val or default on error """

        try:
            val = int(val)
        except Exception:
            val = default

        return val

    ################################################################################
    # Check_setting_int                                                            #
    ################################################################################

    def minimax(self, val, default, low, high):
        """ Return value forced within range """

        val = self.to_int(val, default=default)

        if val < low:
            return low
        if val > high:
            return high

        return val

    ################################################################################
    # Check_setting_int                                                            #
    ################################################################################

    def check_setting_int(self, section, key, def_val, silent=True):
        my_val = self.CONFIG_OBJ.get(section, {section: key}).get(key, def_val)
        if str(my_val).lower() == "true":
            my_val = 1
        elif str(my_val).lower() == "false":
            my_val = 0

        try:
            my_val = int(my_val)
        except Exception:
            my_val = def_val

        if not silent:
            sickrage.srCore.srLogger.debug(key + " -> " + str(my_val))

        return my_val

    ################################################################################
    # Check_setting_float                                                          #
    ################################################################################

    def check_setting_float(self, section, key, def_val, silent=True):
        try:
            my_val = float(self.CONFIG_OBJ.get(section, {section: key}).get(key, def_val))
        except Exception:
            my_val = def_val

        if not silent:
            sickrage.srCore.srLogger.debug(section + " -> " + str(my_val))

        return my_val

    ################################################################################
    # Check_setting_str                                                            #
    ################################################################################
    def check_setting_str(self, section, key, def_val="", silent=True):
        my_val = self.CONFIG_OBJ.get(section, {section: key}).get(key, def_val)

        if my_val:
            censored_regex = re.compile(r"|".join(re.escape(word) for word in ["password", "token", "api"]), re.I)
            if censored_regex.search(key) or (section, key) in self.CENSORED_ITEMS:
                self.CENSORED_ITEMS[section, key] = my_val

        if not silent:
            print(key + " -> " + my_val)

        return my_val

    ################################################################################
    # Check_setting_pickle                                                           #
    ################################################################################
    def check_setting_pickle(self, section, key, def_val="", silent=True):
        my_val = self.CONFIG_OBJ.get(section, {section: key}).get(key, def_val)

        if my_val:
            censored_regex = re.compile(r"|".join(re.escape(word) for word in ["password", "token", "api"]), re.I)
            if censored_regex.search(key) or (section, key) in self.CENSORED_ITEMS:
                self.CENSORED_ITEMS[section, key] = my_val

        if not silent:
            print(key + " -> " + my_val)

        try:
            my_val = pickle.loads(my_val)
        except (KeyError, TypeError):
            my_val = pickle.loads(pickle.dumps(def_val))
        except ValueError:
            pass

        return my_val

    def load(self):
        # Make sure we can write to the config file
        if not os.path.isabs(sickrage.CONFIG_FILE):
            sickrage.CONFIG_FILE = os.path.abspath(os.path.join(sickrage.DATA_DIR, sickrage.CONFIG_FILE))

        if not os.access(sickrage.CONFIG_FILE, os.W_OK):
            if os.path.isfile(sickrage.CONFIG_FILE):
                raise SystemExit("Config file '" + sickrage.CONFIG_FILE + "' must be writeable.")
            elif not os.access(os.path.dirname(sickrage.CONFIG_FILE), os.W_OK):
                raise SystemExit(
                    "Config file root dir '" + os.path.dirname(sickrage.CONFIG_FILE) + "' must be writeable.")

        # load config
        self.CONFIG_OBJ = ConfigObj(sickrage.CONFIG_FILE)

        # decrypt settings
        self.ENCRYPTION_VERSION = self.check_setting_int('General', 'encryption_version', self.ENCRYPTION_VERSION)
        self.ENCRYPTION_SECRET = self.check_setting_str('General', 'encryption_secret', self.ENCRYPTION_SECRET)
        self.CONFIG_OBJ.walk(self.decrypt)

        # migrate config
        self.CONFIG_OBJ = ConfigMigrator(self.CONFIG_OBJ).migrate_config()

        # GENERAL SETTINGS
        self.DEBUG = sickrage.DEBUG or bool(self.check_setting_int('General', 'debug', self.DEBUG))
        self.DEVELOPER = sickrage.DEVELOPER or bool(self.check_setting_int('General', 'developer', self.DEVELOPER))
        self.LAST_DB_COMPACT = self.check_setting_int('General', 'last_db_compact', self.LAST_DB_COMPACT)
        self.LOG_NR = self.check_setting_int('General', 'log_nr', self.LOG_NR)
        self.LOG_SIZE = self.check_setting_int('General', 'log_size', self.LOG_SIZE)
        self.SOCKET_TIMEOUT = self.check_setting_int('General', 'socket_timeout', self.SOCKET_TIMEOUT)
        self.DEFAULT_PAGE = self.check_setting_str('General', 'default_page', self.DEFAULT_PAGE)
        self.PIP_PATH = self.check_setting_str('General', 'pip_path', self.PIP_PATH)
        self.GIT_PATH = self.check_setting_str('General', 'git_path', self.GIT_PATH)
        self.GIT_AUTOISSUES = bool(self.check_setting_int('General', 'git_autoissues', self.GIT_AUTOISSUES))
        self.GIT_USERNAME = self.check_setting_str('General', 'git_username', self.GIT_USERNAME)
        self.GIT_PASSWORD = self.check_setting_str('General', 'git_password', self.GIT_PASSWORD)
        self.GIT_NEWVER = bool(self.check_setting_int('General', 'git_newver', self.GIT_NEWVER))
        self.GIT_RESET = bool(self.check_setting_int('General', 'git_reset', self.GIT_RESET))
        self.WEB_PORT = self.check_setting_int('General', 'web_port', self.WEB_PORT)
        self.WEB_HOST = self.check_setting_str('General', 'web_host', self.WEB_HOST)
        self.WEB_IPV6 = bool(self.check_setting_int('General', 'web_ipv6', self.WEB_IPV6))
        self.WEB_ROOT = self.check_setting_str('General', 'web_root', '').rstrip("/")
        self.WEB_LOG = bool(self.check_setting_int('General', 'web_log', self.WEB_LOG))
        self.WEB_USERNAME = self.check_setting_str('General', 'web_username', self.WEB_USERNAME)
        self.WEB_PASSWORD = self.check_setting_str('General', 'web_password', self.WEB_PASSWORD)
        self.WEB_COOKIE_SECRET = self.check_setting_str('General', 'web_cookie_secret', self.WEB_COOKIE_SECRET)
        self.WEB_USE_GZIP = bool(self.check_setting_int('General', 'web_use_gzip', self.WEB_USE_GZIP))
        self.SSL_VERIFY = bool(self.check_setting_int('General', 'ssl_verify', self.SSL_VERIFY))
        self.LAUNCH_BROWSER = bool(self.check_setting_int('General', 'launch_browser', self.LAUNCH_BROWSER))
        self.INDEXER_DEFAULT_LANGUAGE = self.check_setting_str('General', 'indexerDefaultLang',
                                                               self.INDEXER_DEFAULT_LANGUAGE)
        self.EP_DEFAULT_DELETED_STATUS = self.check_setting_int('General', 'ep_default_deleted_status',
                                                                self.EP_DEFAULT_DELETED_STATUS)
        self.DOWNLOAD_URL = self.check_setting_str('General', 'download_url', self.DOWNLOAD_URL)
        self.CPU_PRESET = self.check_setting_str('General', 'cpu_preset', self.CPU_PRESET)
        self.ANON_REDIRECT = self.check_setting_str('General', 'anon_redirect', self.ANON_REDIRECT)
        self.PROXY_SETTING = self.check_setting_str('General', 'proxy_setting', self.PROXY_SETTING)
        self.PROXY_INDEXERS = bool(self.check_setting_int('General', 'proxy_indexers', self.PROXY_INDEXERS))
        self.TRASH_REMOVE_SHOW = bool(self.check_setting_int('General', 'trash_remove_show', self.TRASH_REMOVE_SHOW))
        self.TRASH_ROTATE_LOGS = bool(self.check_setting_int('General', 'trash_rotate_logs', self.TRASH_ROTATE_LOGS))
        self.SORT_ARTICLE = bool(self.check_setting_int('General', 'sort_article', self.SORT_ARTICLE))
        self.API_KEY = self.check_setting_str('General', 'api_key', self.API_KEY)
        self.ENABLE_HTTPS = bool(self.check_setting_int('General', 'enable_https', self.ENABLE_HTTPS))
        self.HTTPS_CERT = self.check_setting_str('General', 'https_cert', self.HTTPS_CERT)
        self.HTTPS_KEY = self.check_setting_str('General', 'https_key', self.HTTPS_KEY)
        self.HANDLE_REVERSE_PROXY = bool(
            self.check_setting_int('General', 'handle_reverse_proxy', self.HANDLE_REVERSE_PROXY))
        self.ROOT_DIRS = self.check_setting_str('General', 'root_dirs', self.ROOT_DIRS)
        self.QUALITY_DEFAULT = self.check_setting_int('General', 'quality_default', self.QUALITY_DEFAULT)
        self.STATUS_DEFAULT = self.check_setting_int('General', 'status_default', self.STATUS_DEFAULT)
        self.STATUS_DEFAULT_AFTER = self.check_setting_int('General', 'status_default_after', self.STATUS_DEFAULT_AFTER)
        self.VERSION_NOTIFY = bool(self.check_setting_int('General', 'version_notify', self.VERSION_NOTIFY))
        self.AUTO_UPDATE = bool(self.check_setting_int('General', 'auto_update', self.AUTO_UPDATE))
        self.NOTIFY_ON_UPDATE = bool(self.check_setting_int('General', 'notify_on_update', self.NOTIFY_ON_UPDATE))
        self.FLATTEN_FOLDERS_DEFAULT = bool(
            self.check_setting_int('General', 'flatten_folders_default', self.FLATTEN_FOLDERS_DEFAULT))
        self.INDEXER_DEFAULT = self.check_setting_int('General', 'indexer_default', self.INDEXER_DEFAULT)
        self.INDEXER_TIMEOUT = self.check_setting_int('General', 'indexer_timeout', self.INDEXER_TIMEOUT)
        self.ANIME_DEFAULT = bool(self.check_setting_int('General', 'anime_default', 0))
        self.SCENE_DEFAULT = bool(self.check_setting_int('General', 'scene_default', 0))
        self.ARCHIVE_DEFAULT = bool(self.check_setting_int('General', 'archive_default', 0))
        self.NAMING_PATTERN = self.check_setting_str('General', 'naming_pattern', 'Season %0S/%SN - S%0SE%0E - %EN')
        self.NAMING_ABD_PATTERN = self.check_setting_str('General', 'naming_abd_pattern', '%SN - %A.D - %EN')
        self.NAMING_CUSTOM_ABD = bool(self.check_setting_int('General', 'naming_custom_abd', 0))
        self.NAMING_SPORTS_PATTERN = self.check_setting_str('General', 'naming_sports_pattern', '%SN - %A-D - %EN')
        self.NAMING_ANIME_PATTERN = self.check_setting_str('General', 'naming_anime_pattern',
                                                           'Season %0S/%SN - S%0SE%0E - %EN')
        self.NAMING_ANIME = self.check_setting_int('General', 'naming_anime', 3)
        self.NAMING_CUSTOM_SPORTS = bool(self.check_setting_int('General', 'naming_custom_sports', 0))
        self.NAMING_CUSTOM_ANIME = bool(self.check_setting_int('General', 'naming_custom_anime', 0))
        self.NAMING_MULTI_EP = self.check_setting_int('General', 'naming_multi_ep', 1)
        self.NAMING_ANIME_MULTI_EP = self.check_setting_int('General', 'naming_anime_multi_ep', 1)
        self.NAMING_STRIP_YEAR = bool(self.check_setting_int('General', 'naming_strip_year', 0))
        self.USE_NZBS = bool(self.check_setting_int('General', 'use_nzbs', 0))
        self.USE_TORRENTS = bool(self.check_setting_int('General', 'use_torrents', 1))
        self.NZB_METHOD = self.check_setting_str('General', 'nzb_method', 'blackhole')
        self.TORRENT_METHOD = self.check_setting_str('General', 'torrent_method', 'blackhole')
        self.DOWNLOAD_PROPERS = bool(self.check_setting_int('General', 'download_propers', 1))
        self.ENABLE_RSS_CACHE = bool(self.check_setting_int('General', 'enable_rss_cache', 1))
        self.PROPER_SEARCHER_INTERVAL = self.check_setting_str('General', 'check_propers_interval', 'daily')
        self.RANDOMIZE_PROVIDERS = bool(self.check_setting_int('General', 'randomize_providers', 0))
        self.ALLOW_HIGH_PRIORITY = bool(self.check_setting_int('General', 'allow_high_priority', 1))
        self.SKIP_REMOVED_FILES = bool(self.check_setting_int('General', 'skip_removed_files', 0))
        self.USENET_RETENTION = self.check_setting_int('General', 'usenet_retention', 500)
        self.NAMECACHE_FREQ = self.check_setting_int('General', 'namecache_frequency', self.DEFAULT_NAMECACHE_FREQ)
        self.DAILY_SEARCHER_FREQ = self.check_setting_int('General', 'dailysearch_frequency',
                                                          self.DEFAULT_DAILY_SEARCHER_FREQ)
        self.BACKLOG_SEARCHER_FREQ = self.check_setting_int('General', 'backlog_frequency',
                                                            self.DEFAULT_BACKLOG_SEARCHER_FREQ)
        self.VERSION_UPDATER_FREQ = self.check_setting_int('General', 'update_frequency',
                                                           self.DEFAULT_VERSION_UPDATE_FREQ)
        self.SHOWUPDATE_STALE = bool(self.check_setting_int('General', 'showupdate_stale', 1))
        self.SHOWUPDATE_HOUR = self.check_setting_int('General', 'showupdate_hour', self.DEFAULT_SHOWUPDATE_HOUR)
        self.BACKLOG_DAYS = self.check_setting_int('General', 'backlog_days', 7)
        self.AUTOPOSTPROCESSOR_FREQ = self.check_setting_int(
            'General', 'autopostprocessor_frequency', self.DEFAULT_AUTOPOSTPROCESSOR_FREQ
        )
        self.TV_DOWNLOAD_DIR = self.check_setting_str('General', 'tv_download_dir', '')
        self.PROCESS_AUTOMATICALLY = bool(self.check_setting_int('General', 'process_automatically', 0))
        self.NO_DELETE = bool(self.check_setting_int('General', 'no_delete', 0))
        self.UNPACK = bool(self.check_setting_int('General', 'unpack', 0))
        self.RENAME_EPISODES = bool(self.check_setting_int('General', 'rename_episodes', 1))
        self.AIRDATE_EPISODES = bool(self.check_setting_int('General', 'airdate_episodes', 0))
        self.FILE_TIMESTAMP_TIMEZONE = self.check_setting_str('General', 'file_timestamp_timezone',
                                                              'network')
        self.KEEP_PROCESSED_DIR = bool(self.check_setting_int('General', 'keep_processed_dir', 1))
        self.PROCESS_METHOD = self.check_setting_str('General', 'process_method',
                                                     'copy' if self.KEEP_PROCESSED_DIR else'move')
        self.DELRARCONTENTS = bool(self.check_setting_int('General', 'del_rar_contents', 0))
        self.MOVE_ASSOCIATED_FILES = bool(self.check_setting_int('General', 'move_associated_files', 0))
        self.POSTPONE_IF_SYNC_FILES = bool(
            self.check_setting_int('General', 'postpone_if_sync_files', 1))
        self.SYNC_FILES = self.check_setting_str('General', 'sync_files',
                                                 '!sync,lftp-pget-status,part,bts,!qb')
        self.NFO_RENAME = bool(self.check_setting_int('General', 'nfo_rename', 1))
        self.CREATE_MISSING_SHOW_DIRS = bool(
            self.check_setting_int('General', 'create_missing_show_dirs', 0))
        self.ADD_SHOWS_WO_DIR = bool(self.check_setting_int('General', 'add_shows_wo_dir', 0))
        self.REQUIRE_WORDS = self.check_setting_str('General', 'require_words', '')
        self.IGNORE_WORDS = self.check_setting_str('General', 'ignore_words',
                                                   'german,french,core2hd,dutch,swedish,reenc,MrLss')
        self.IGNORED_SUBS_LIST = self.check_setting_str('General', 'ignored_subs_list',
                                                        'dk,fin,heb,kor,nor,nordic,pl,swe')
        self.CALENDAR_UNPROTECTED = bool(self.check_setting_int('General', 'calendar_unprotected', 0))
        self.CALENDAR_ICONS = bool(self.check_setting_int('General', 'calendar_icons', 0))
        self.NO_RESTART = bool(self.check_setting_int('General', 'no_restart', 0))
        self.EXTRA_SCRIPTS = [x.strip() for x in
                              self.check_setting_str('General', 'extra_scripts', '').split('|') if x.strip()]
        self.USE_LISTVIEW = bool(self.check_setting_int('General', 'use_listview', 0))
        self.DISPLAY_ALL_SEASONS = bool(self.check_setting_int('General', 'display_all_seasons', 1))
        self.RANDOM_USER_AGENT = bool(self.check_setting_int('General', 'random_user_agent', self.RANDOM_USER_AGENT))

        # GUI SETTINGS
        self.GUI_NAME = self.check_setting_str('GUI', 'gui_name', self.GUI_NAME)
        self.THEME_NAME = self.check_setting_str('GUI', 'theme_name', 'dark')
        self.FANART_BACKGROUND = bool(self.check_setting_int('GUI', 'fanart_background', self.FANART_BACKGROUND))
        self.FANART_BACKGROUND_OPACITY = self.check_setting_float('GUI', 'fanart_background_opacity',
                                                                  self.FANART_BACKGROUND_OPACITY)
        self.HOME_LAYOUT = self.check_setting_str('GUI', 'home_layout', 'poster')
        self.HISTORY_LAYOUT = self.check_setting_str('GUI', 'history_layout', 'detailed')
        self.HISTORY_LIMIT = self.check_setting_str('GUI', 'history_limit', '100')
        self.DISPLAY_SHOW_SPECIALS = bool(self.check_setting_int('GUI', 'display_show_specials', 1))
        self.COMING_EPS_LAYOUT = self.check_setting_str('GUI', 'coming_eps_layout', 'banner')
        self.COMING_EPS_DISPLAY_PAUSED = bool(
            self.check_setting_int('GUI', 'coming_eps_display_paused', 0))
        self.COMING_EPS_SORT = self.check_setting_str('GUI', 'coming_eps_sort', 'date')
        self.COMING_EPS_MISSED_RANGE = self.check_setting_int('GUI', 'coming_eps_missed_range', 7)
        self.FUZZY_DATING = bool(self.check_setting_int('GUI', 'fuzzy_dating', 0))
        self.TRIM_ZERO = bool(self.check_setting_int('GUI', 'trim_zero', 0))
        self.DATE_PRESET = self.check_setting_str('GUI', 'date_preset', '%x')
        self.TIME_PRESET_W_SECONDS = self.check_setting_str('GUI', 'time_preset', '%I:%M:%S%p')
        self.TIME_PRESET = self.TIME_PRESET_W_SECONDS.replace(":%S", "")
        self.TIMEZONE_DISPLAY = self.check_setting_str('GUI', 'timezone_display', 'local')
        self.POSTER_SORTBY = self.check_setting_str('GUI', 'poster_sortby', 'name')
        self.POSTER_SORTDIR = self.check_setting_int('GUI', 'poster_sortdir', 1)
        self.FILTER_ROW = bool(self.check_setting_int('GUI', 'filter_row', 1))

        # BLACKHOLE SETTINGS
        self.NZB_DIR = self.check_setting_str('Blackhole', 'nzb_dir', '')
        self.TORRENT_DIR = self.check_setting_str('Blackhole', 'torrent_dir', '')

        # NZBS SETTINGS
        self.NZBS = bool(self.check_setting_int('NZBs', 'nzbs', 0))
        self.NZBS_UID = self.check_setting_str('NZBs', 'nzbs_uid', '')
        self.NZBS_HASH = self.check_setting_str('NZBs', 'nzbs_hash', '')

        # NEWZBIN SETTINGS
        self.NEWZBIN = bool(self.check_setting_int('Newzbin', 'newzbin', 0))
        self.NEWZBIN_USERNAME = self.check_setting_str('Newzbin', 'newzbin_username', '')
        self.NEWZBIN_PASSWORD = self.check_setting_str('Newzbin', 'newzbin_password', '')

        # SABNZBD SETTINGS
        self.SAB_USERNAME = self.check_setting_str('SABnzbd', 'sab_username', '')
        self.SAB_PASSWORD = self.check_setting_str('SABnzbd', 'sab_password', '')
        self.SAB_APIKEY = self.check_setting_str('SABnzbd', 'sab_apikey', '')
        self.SAB_CATEGORY = self.check_setting_str('SABnzbd', 'sab_category', 'tv')
        self.SAB_CATEGORY_BACKLOG = self.check_setting_str('SABnzbd', 'sab_category_backlog',
                                                           self.SAB_CATEGORY)
        self.SAB_CATEGORY_ANIME = self.check_setting_str('SABnzbd', 'sab_category_anime', 'anime')
        self.SAB_CATEGORY_ANIME_BACKLOG = self.check_setting_str('SABnzbd',
                                                                 'sab_category_anime_backlog',
                                                                 self.SAB_CATEGORY_ANIME)
        self.SAB_HOST = self.check_setting_str('SABnzbd', 'sab_host', '')
        self.SAB_FORCED = bool(self.check_setting_int('SABnzbd', 'sab_forced', 0))

        # NZBGET SETTINGS
        self.NZBGET_USERNAME = self.check_setting_str('NZBget', 'nzbget_username', 'nzbget')
        self.NZBGET_PASSWORD = self.check_setting_str('NZBget', 'nzbget_password', 'tegbzn6789')
        self.NZBGET_CATEGORY = self.check_setting_str('NZBget', 'nzbget_category', 'tv')
        self.NZBGET_CATEGORY_BACKLOG = self.check_setting_str('NZBget', 'nzbget_category_backlog',
                                                              self.NZBGET_CATEGORY)
        self.NZBGET_CATEGORY_ANIME = self.check_setting_str('NZBget', 'nzbget_category_anime', 'anime')
        self.NZBGET_CATEGORY_ANIME_BACKLOG = self.check_setting_str(
            'NZBget', 'nzbget_category_anime_backlog', self.NZBGET_CATEGORY_ANIME)
        self.NZBGET_HOST = self.check_setting_str('NZBget', 'nzbget_host', '')
        self.NZBGET_USE_HTTPS = bool(self.check_setting_int('NZBget', 'nzbget_use_https', 0))
        self.NZBGET_PRIORITY = self.check_setting_int('NZBget', 'nzbget_priority', 100)

        # TORRENT SETTINGS
        self.TORRENT_USERNAME = self.check_setting_str('TORRENT', 'torrent_username', '')
        self.TORRENT_PASSWORD = self.check_setting_str('TORRENT', 'torrent_password', '')
        self.TORRENT_HOST = self.check_setting_str('TORRENT', 'torrent_host', '')
        self.TORRENT_PATH = self.check_setting_str('TORRENT', 'torrent_path', '')
        self.TORRENT_SEED_TIME = self.check_setting_int('TORRENT', 'torrent_seed_time', 0)
        self.TORRENT_PAUSED = bool(self.check_setting_int('TORRENT', 'torrent_paused', 0))
        self.TORRENT_HIGH_BANDWIDTH = bool(
            self.check_setting_int('TORRENT', 'torrent_high_bandwidth', 0))
        self.TORRENT_LABEL = self.check_setting_str('TORRENT', 'torrent_label', '')
        self.TORRENT_LABEL_ANIME = self.check_setting_str('TORRENT', 'torrent_label_anime', '')
        self.TORRENT_VERIFY_CERT = bool(self.check_setting_int('TORRENT', 'torrent_verify_cert', 0))
        self.TORRENT_RPCURL = self.check_setting_str('TORRENT', 'torrent_rpcurl', 'transmission')
        self.TORRENT_AUTH_TYPE = self.check_setting_str('TORRENT', 'torrent_auth_type', '')
        self.TORRENT_TRACKERS = self.check_setting_str('TORRENT', 'torrent_trackers', self.TORRENT_TRACKERS)

        # KODI SETTINGS
        self.USE_KODI = bool(self.check_setting_int('KODI', 'use_kodi', 0))
        self.KODI_ALWAYS_ON = bool(self.check_setting_int('KODI', 'kodi_always_on', 1))
        self.KODI_NOTIFY_ONSNATCH = bool(self.check_setting_int('KODI', 'kodi_notify_onsnatch', 0))
        self.KODI_NOTIFY_ONDOWNLOAD = bool(self.check_setting_int('KODI', 'kodi_notify_ondownload', 0))
        self.KODI_NOTIFY_ONSUBTITLEDOWNLOAD = bool(self.check_setting_int('KODI', 'kodi_notify_onsubtitledownload', 0))
        self.KODI_UPDATE_LIBRARY = bool(self.check_setting_int('KODI', 'kodi_update_library', 0))
        self.KODI_UPDATE_FULL = bool(self.check_setting_int('KODI', 'kodi_update_full', 0))
        self.KODI_UPDATE_ONLYFIRST = bool(self.check_setting_int('KODI', 'kodi_update_onlyfirst', 0))
        self.KODI_HOST = self.check_setting_str('KODI', 'kodi_host', '')
        self.KODI_USERNAME = self.check_setting_str('KODI', 'kodi_username', '')
        self.KODI_PASSWORD = self.check_setting_str('KODI', 'kodi_password', '')

        # PLEX SETTINGS
        self.USE_PLEX = bool(self.check_setting_int('Plex', 'use_plex', 0))
        self.PLEX_NOTIFY_ONSNATCH = bool(self.check_setting_int('Plex', 'plex_notify_onsnatch', 0))
        self.PLEX_NOTIFY_ONDOWNLOAD = bool(self.check_setting_int('Plex', 'plex_notify_ondownload', 0))
        self.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            self.check_setting_int('Plex', 'plex_notify_onsubtitledownload', 0))
        self.PLEX_UPDATE_LIBRARY = bool(self.check_setting_int('Plex', 'plex_update_library', 0))
        self.PLEX_SERVER_HOST = self.check_setting_str('Plex', 'plex_server_host', '')
        self.PLEX_SERVER_TOKEN = self.check_setting_str('Plex', 'plex_server_token', '')
        self.PLEX_HOST = self.check_setting_str('Plex', 'plex_host', '')
        self.PLEX_USERNAME = self.check_setting_str('Plex', 'plex_username', '')
        self.PLEX_PASSWORD = self.check_setting_str('Plex', 'plex_password', '')
        self.USE_PLEX_CLIENT = bool(self.check_setting_int('Plex', 'use_plex_client', 0))
        self.PLEX_CLIENT_USERNAME = self.check_setting_str('Plex', 'plex_client_username', '')
        self.PLEX_CLIENT_PASSWORD = self.check_setting_str('Plex', 'plex_client_password', '')

        # EMBY SETTINGS
        self.USE_EMBY = bool(self.check_setting_int('Emby', 'use_emby', 0))
        self.EMBY_HOST = self.check_setting_str('Emby', 'emby_host', '')
        self.EMBY_APIKEY = self.check_setting_str('Emby', 'emby_apikey', '')

        # GROWL SETTINGS
        self.USE_GROWL = bool(self.check_setting_int('Growl', 'use_growl', 0))
        self.GROWL_NOTIFY_ONSNATCH = bool(self.check_setting_int('Growl', 'growl_notify_onsnatch', 0))
        self.GROWL_NOTIFY_ONDOWNLOAD = bool(
            self.check_setting_int('Growl', 'growl_notify_ondownload', 0))
        self.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            self.check_setting_int('Growl', 'growl_notify_onsubtitledownload', 0))
        self.GROWL_HOST = self.check_setting_str('Growl', 'growl_host', '')
        self.GROWL_PASSWORD = self.check_setting_str('Growl', 'growl_password', '')

        # FREEMOBILE SETTINGS
        self.USE_FREEMOBILE = bool(self.check_setting_int('FreeMobile', 'use_freemobile', 0))
        self.FREEMOBILE_NOTIFY_ONSNATCH = bool(
            self.check_setting_int('FreeMobile', 'freemobile_notify_onsnatch', 0))
        self.FREEMOBILE_NOTIFY_ONDOWNLOAD = bool(
            self.check_setting_int('FreeMobile', 'freemobile_notify_ondownload', 0))
        self.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            self.check_setting_int('FreeMobile', 'freemobile_notify_onsubtitledownload', 0))
        self.FREEMOBILE_ID = self.check_setting_str('FreeMobile', 'freemobile_id', '')
        self.FREEMOBILE_APIKEY = self.check_setting_str('FreeMobile', 'freemobile_apikey', '')

        # PROWL SETTINGS
        self.USE_PROWL = bool(self.check_setting_int('Prowl', 'use_prowl', 0))
        self.PROWL_NOTIFY_ONSNATCH = bool(self.check_setting_int('Prowl', 'prowl_notify_onsnatch', 0))
        self.PROWL_NOTIFY_ONDOWNLOAD = bool(
            self.check_setting_int('Prowl', 'prowl_notify_ondownload', 0))
        self.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            self.check_setting_int('Prowl', 'prowl_notify_onsubtitledownload', 0))
        self.PROWL_API = self.check_setting_str('Prowl', 'prowl_api', '')
        self.PROWL_PRIORITY = self.check_setting_str('Prowl', 'prowl_priority', "0")

        # TWITTER SETTINGS
        self.USE_TWITTER = bool(self.check_setting_int('Twitter', 'use_twitter', 0))
        self.TWITTER_NOTIFY_ONSNATCH = bool(
            self.check_setting_int('Twitter', 'twitter_notify_onsnatch', 0))
        self.TWITTER_NOTIFY_ONDOWNLOAD = bool(
            self.check_setting_int('Twitter', 'twitter_notify_ondownload', 0))
        self.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            self.check_setting_int('Twitter', 'twitter_notify_onsubtitledownload', 0))
        self.TWITTER_USERNAME = self.check_setting_str('Twitter', 'twitter_username', '')
        self.TWITTER_PASSWORD = self.check_setting_str('Twitter', 'twitter_password', '')
        self.TWITTER_PREFIX = self.check_setting_str('Twitter', 'twitter_prefix', 'SiCKRAGE')
        self.TWITTER_DMTO = self.check_setting_str('Twitter', 'twitter_dmto', '')
        self.TWITTER_USEDM = bool(self.check_setting_int('Twitter', 'twitter_usedm', 0))

        self.USE_BOXCAR = bool(self.check_setting_int('Boxcar', 'use_boxcar', 0))
        self.BOXCAR_NOTIFY_ONSNATCH = bool(
            self.check_setting_int('Boxcar', 'boxcar_notify_onsnatch', 0))
        self.BOXCAR_NOTIFY_ONDOWNLOAD = bool(
            self.check_setting_int('Boxcar', 'boxcar_notify_ondownload', 0))
        self.BOXCAR_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            self.check_setting_int('Boxcar', 'boxcar_notify_onsubtitledownload', 0))
        self.BOXCAR_USERNAME = self.check_setting_str('Boxcar', 'boxcar_username', '')

        self.USE_BOXCAR2 = bool(self.check_setting_int('Boxcar2', 'use_boxcar2', 0))
        self.BOXCAR2_NOTIFY_ONSNATCH = bool(
            self.check_setting_int('Boxcar2', 'boxcar2_notify_onsnatch', 0))
        self.BOXCAR2_NOTIFY_ONDOWNLOAD = bool(
            self.check_setting_int('Boxcar2', 'boxcar2_notify_ondownload', 0))
        self.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            self.check_setting_int('Boxcar2', 'boxcar2_notify_onsubtitledownload', 0))
        self.BOXCAR2_ACCESSTOKEN = self.check_setting_str('Boxcar2', 'boxcar2_accesstoken', '')

        self.USE_PUSHOVER = bool(self.check_setting_int('Pushover', 'use_pushover', 0))
        self.PUSHOVER_NOTIFY_ONSNATCH = bool(
            self.check_setting_int('Pushover', 'pushover_notify_onsnatch', 0))
        self.PUSHOVER_NOTIFY_ONDOWNLOAD = bool(
            self.check_setting_int('Pushover', 'pushover_notify_ondownload', 0))
        self.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            self.check_setting_int('Pushover', 'pushover_notify_onsubtitledownload', 0))
        self.PUSHOVER_USERKEY = self.check_setting_str('Pushover', 'pushover_userkey', '')
        self.PUSHOVER_APIKEY = self.check_setting_str('Pushover', 'pushover_apikey', '')
        self.PUSHOVER_DEVICE = self.check_setting_str('Pushover', 'pushover_device', '')
        self.PUSHOVER_SOUND = self.check_setting_str('Pushover', 'pushover_sound', 'pushover')

        self.USE_LIBNOTIFY = bool(self.check_setting_int('Libnotify', 'use_libnotify', 0))
        self.LIBNOTIFY_NOTIFY_ONSNATCH = bool(
            self.check_setting_int('Libnotify', 'libnotify_notify_onsnatch', 0))
        self.LIBNOTIFY_NOTIFY_ONDOWNLOAD = bool(
            self.check_setting_int('Libnotify', 'libnotify_notify_ondownload', 0))
        self.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            self.check_setting_int('Libnotify', 'libnotify_notify_onsubtitledownload', 0))

        self.USE_NMJ = bool(self.check_setting_int('NMJ', 'use_nmj', 0))
        self.NMJ_HOST = self.check_setting_str('NMJ', 'nmj_host', '')
        self.NMJ_DATABASE = self.check_setting_str('NMJ', 'nmj_database', '')
        self.NMJ_MOUNT = self.check_setting_str('NMJ', 'nmj_mount', '')

        self.USE_NMJv2 = bool(self.check_setting_int('NMJv2', 'use_nmjv2', 0))
        self.NMJv2_HOST = self.check_setting_str('NMJv2', 'nmjv2_host', '')
        self.NMJv2_DATABASE = self.check_setting_str('NMJv2', 'nmjv2_database', '')
        self.NMJv2_DBLOC = self.check_setting_str('NMJv2', 'nmjv2_dbloc', '')

        self.USE_SYNOINDEX = bool(self.check_setting_int('Synology', 'use_synoindex', 0))

        self.USE_SYNOLOGYNOTIFIER = bool(
            self.check_setting_int('SynologyNotifier', 'use_synologynotifier', 0))
        self.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH = bool(
            self.check_setting_int('SynologyNotifier', 'synologynotifier_notify_onsnatch', 0))
        self.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD = bool(
            self.check_setting_int('SynologyNotifier', 'synologynotifier_notify_ondownload', 0))
        self.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            self.check_setting_int('SynologyNotifier', 'synologynotifier_notify_onsubtitledownload', 0))

        self.THETVDB_APITOKEN = self.check_setting_str('theTVDB', 'thetvdb_apitoken', '')

        self.USE_TRAKT = bool(self.check_setting_int('Trakt', 'use_trakt', self.USE_TRAKT))
        self.TRAKT_USERNAME = self.check_setting_str('Trakt', 'trakt_username', self.TRAKT_USERNAME)
        self.TRAKT_OAUTH_TOKEN = self.check_setting_pickle('Trakt', 'trakt_oauth_token', self.TRAKT_OAUTH_TOKEN)
        self.TRAKT_REMOVE_WATCHLIST = bool(
            self.check_setting_int('Trakt', 'trakt_remove_watchlist', self.TRAKT_REMOVE_WATCHLIST))
        self.TRAKT_REMOVE_SERIESLIST = bool(
            self.check_setting_int('Trakt', 'trakt_remove_serieslist', self.TRAKT_REMOVE_SERIESLIST))
        self.TRAKT_REMOVE_SHOW_FROM_SICKRAGE = bool(
            self.check_setting_int('Trakt', 'trakt_remove_show_from_sickrage', self.TRAKT_REMOVE_SHOW_FROM_SICKRAGE))
        self.TRAKT_SYNC_WATCHLIST = bool(
            self.check_setting_int('Trakt', 'trakt_sync_watchlist', self.TRAKT_SYNC_WATCHLIST))
        self.TRAKT_METHOD_ADD = self.check_setting_int('Trakt', 'trakt_method_add', self.TRAKT_METHOD_ADD)
        self.TRAKT_START_PAUSED = bool(self.check_setting_int('Trakt', 'trakt_start_paused', self.TRAKT_START_PAUSED))
        self.TRAKT_USE_RECOMMENDED = bool(
            self.check_setting_int('Trakt', 'trakt_use_recommended', self.TRAKT_USE_RECOMMENDED))
        self.TRAKT_SYNC = bool(self.check_setting_int('Trakt', 'trakt_sync', self.TRAKT_SYNC))
        self.TRAKT_SYNC_REMOVE = bool(self.check_setting_int('Trakt', 'trakt_sync_remove', self.TRAKT_SYNC_REMOVE))
        self.TRAKT_DEFAULT_INDEXER = self.check_setting_int('Trakt', 'trakt_default_indexer',
                                                            self.TRAKT_DEFAULT_INDEXER)
        self.TRAKT_TIMEOUT = self.check_setting_int('Trakt', 'trakt_timeout', self.TRAKT_TIMEOUT)
        self.TRAKT_BLACKLIST_NAME = self.check_setting_str('Trakt', 'trakt_blacklist_name', self.TRAKT_BLACKLIST_NAME)

        self.USE_PYTIVO = bool(self.check_setting_int('pyTivo', 'use_pytivo', 0))
        self.PYTIVO_NOTIFY_ONSNATCH = bool(
            self.check_setting_int('pyTivo', 'pytivo_notify_onsnatch', 0))
        self.PYTIVO_NOTIFY_ONDOWNLOAD = bool(
            self.check_setting_int('pyTivo', 'pytivo_notify_ondownload', 0))
        self.PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            self.check_setting_int('pyTivo', 'pytivo_notify_onsubtitledownload', 0))
        self.PYTIVO_UPDATE_LIBRARY = bool(self.check_setting_int('pyTivo', 'pyTivo_update_library', 0))
        self.PYTIVO_HOST = self.check_setting_str('pyTivo', 'pytivo_host', '')
        self.PYTIVO_SHARE_NAME = self.check_setting_str('pyTivo', 'pytivo_share_name', '')
        self.PYTIVO_TIVO_NAME = self.check_setting_str('pyTivo', 'pytivo_tivo_name', '')

        self.USE_NMA = bool(self.check_setting_int('NMA', 'use_nma', 0))
        self.NMA_NOTIFY_ONSNATCH = bool(self.check_setting_int('NMA', 'nma_notify_onsnatch', 0))
        self.NMA_NOTIFY_ONDOWNLOAD = bool(self.check_setting_int('NMA', 'nma_notify_ondownload', 0))
        self.NMA_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            self.check_setting_int('NMA', 'nma_notify_onsubtitledownload', 0))
        self.NMA_API = self.check_setting_str('NMA', 'nma_api', '')
        self.NMA_PRIORITY = self.check_setting_str('NMA', 'nma_priority', "0")

        self.USE_PUSHALOT = bool(self.check_setting_int('Pushalot', 'use_pushalot', 0))
        self.PUSHALOT_NOTIFY_ONSNATCH = bool(
            self.check_setting_int('Pushalot', 'pushalot_notify_onsnatch', 0))
        self.PUSHALOT_NOTIFY_ONDOWNLOAD = bool(
            self.check_setting_int('Pushalot', 'pushalot_notify_ondownload', 0))
        self.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            self.check_setting_int('Pushalot', 'pushalot_notify_onsubtitledownload', 0))
        self.PUSHALOT_AUTHORIZATIONTOKEN = self.check_setting_str('Pushalot',
                                                                  'pushalot_authorizationtoken', '')

        self.USE_PUSHBULLET = bool(self.check_setting_int('Pushbullet', 'use_pushbullet', 0))
        self.PUSHBULLET_NOTIFY_ONSNATCH = bool(
            self.check_setting_int('Pushbullet', 'pushbullet_notify_onsnatch', 0))
        self.PUSHBULLET_NOTIFY_ONDOWNLOAD = bool(
            self.check_setting_int('Pushbullet', 'pushbullet_notify_ondownload', 0))
        self.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            self.check_setting_int('Pushbullet', 'pushbullet_notify_onsubtitledownload', 0))
        self.PUSHBULLET_API = self.check_setting_str('Pushbullet', 'pushbullet_api', '')
        self.PUSHBULLET_DEVICE = self.check_setting_str('Pushbullet', 'pushbullet_device', '')

        # self.emailself.notifyself.settings        self.USE_EMAIL= bool(self.check_setting_int('Email', 'use_email', 0))
        self.EMAIL_NOTIFY_ONSNATCH = bool(self.check_setting_int('Email', 'email_notify_onsnatch', 0))
        self.EMAIL_NOTIFY_ONDOWNLOAD = bool(
            self.check_setting_int('Email', 'email_notify_ondownload', 0))
        self.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            self.check_setting_int('Email', 'email_notify_onsubtitledownload', 0))
        self.EMAIL_HOST = self.check_setting_str('Email', 'email_host', '')
        self.EMAIL_PORT = self.check_setting_int('Email', 'email_port', 25)
        self.EMAIL_TLS = bool(self.check_setting_int('Email', 'email_tls', 0))
        self.EMAIL_USER = self.check_setting_str('Email', 'email_user', '')
        self.EMAIL_PASSWORD = self.check_setting_str('Email', 'email_password', '')
        self.EMAIL_FROM = self.check_setting_str('Email', 'email_from', '')
        self.EMAIL_LIST = self.check_setting_str('Email', 'email_list', '')

        # SUBTITLE SETTINGS
        self.USE_SUBTITLES = bool(self.check_setting_int('Subtitles', 'use_subtitles', 0))
        self.SUBTITLES_LANGUAGES = self.check_setting_str('Subtitles', 'subtitles_languages', '').split(',')
        self.SUBTITLES_DIR = self.check_setting_str('Subtitles', 'subtitles_dir', '')
        self.SUBTITLES_SERVICES_LIST = self.check_setting_str('Subtitles', 'subtitles_services_list', '').split(',')
        self.SUBTITLES_DEFAULT = bool(self.check_setting_int('Subtitles', 'subtitles_default', 0))
        self.SUBTITLES_HISTORY = bool(self.check_setting_int('Subtitles', 'subtitles_history', 0))
        self.SUBTITLES_HEARING_IMPAIRED = bool(
            self.check_setting_int('Subtitles', 'subtitles_hearing_impaired', 0))
        self.EMBEDDED_SUBTITLES_ALL = bool(
            self.check_setting_int('Subtitles', 'embedded_subtitles_all', 0))
        self.SUBTITLES_MULTI = bool(self.check_setting_int('Subtitles', 'subtitles_multi', 1))
        self.SUBTITLES_SERVICES_ENABLED = [int(x) for x in
                                           self.check_setting_str('Subtitles', 'subtitles_services_enabled',
                                                                  '').split('|') if x]
        self.SUBTITLES_EXTRA_SCRIPTS = [x.strip() for x in
                                        self.check_setting_str('Subtitles', 'subtitles_extra_scripts',
                                                               '').split('|') if x.strip()]
        self.ADDIC7ED_USER = self.check_setting_str('Subtitles', 'addic7ed_username', '')
        self.ADDIC7ED_PASS = self.check_setting_str('Subtitles', 'addic7ed_password', '')
        self.LEGENDASTV_USER = self.check_setting_str('Subtitles', 'legendastv_username', '')
        self.LEGENDASTV_PASS = self.check_setting_str('Subtitles', 'legendastv_password', '')
        self.ITASA_USER = self.check_setting_str('Subtitles', 'itasa_username', '')
        self.ITASA_PASS = self.check_setting_str('Subtitles', 'itasa_password', '')
        self.OPENSUBTITLES_USER = self.check_setting_str('Subtitles', 'opensubtitles_username', '')
        self.OPENSUBTITLES_PASS = self.check_setting_str('Subtitles', 'opensubtitles_password', '')
        self.SUBTITLE_SEARCHER_FREQ = self.check_setting_int(
            'Subtitles', 'subtitles_finder_frequency', self.DEFAULT_SUBTITLE_SEARCHER_FREQ
        )

        # FAILED DOWNLOAD SETTINGS
        self.USE_FAILED_DOWNLOADS = bool(self.check_setting_int('FailedDownloads', 'use_failed_downloads', 0))
        self.DELETE_FAILED = bool(self.check_setting_int('FailedDownloads', 'delete_failed', 0))

        # ANIDB SETTINGS
        self.USE_ANIDB = bool(self.check_setting_int('ANIDB', 'use_anidb', 0))
        self.ANIDB_USERNAME = self.check_setting_str('ANIDB', 'anidb_username', '')
        self.ANIDB_PASSWORD = self.check_setting_str('ANIDB', 'anidb_password', '')
        self.ANIDB_USE_MYLIST = bool(self.check_setting_int('ANIDB', 'anidb_use_mylist', 0))
        self.ANIME_SPLIT_HOME = bool(self.check_setting_int('ANIME', 'anime_split_home', 0))

        self.QUALITY_SIZES = self.check_setting_pickle('Quality', 'sizes', self.QUALITY_SIZES)

        self.CUSTOM_PROVIDERS = self.check_setting_str('Providers', 'custom_providers', '')

        sickrage.srCore.providersDict.load()
        for providerID, providerObj in sickrage.srCore.providersDict.all().items():
            providerSettings = self.check_setting_str('Providers', providerID) or {}
            for k, v in providerSettings.items():
                providerSettings[k] = autoType(v)

            [providerObj.__dict__.update({x: providerSettings[x]}) for x in
             set(providerObj.__dict__).intersection(providerSettings)]

        # order providers
        sickrage.srCore.providersDict.provider_order = self.check_setting_str('Providers', 'providers_order', [])

        for metadataProviderID, metadataProviderObj in sickrage.srCore.metadataProvidersDict.items():
            metadataProviderObj.set_config(
                self.check_setting_str('MetadataProviders', metadataProviderID, '0|0|0|0|0|0|0|0|0|0|0')
            )

        # mark config settings loaded
        self.loaded = True

        # save config settings
        self.save()

    def save(self):
        # dont bother saving settings if there not loaded
        if not self.loaded:
            return

        new_config = ConfigObj(sickrage.CONFIG_FILE, indent_type='  ')
        new_config.clear()

        sickrage.srCore.srLogger.debug("Saving all settings to disk")

        new_config.update({
            'General': {
                'config_version': self.CONFIG_VERSION,
                'encryption_version': int(self.ENCRYPTION_VERSION),
                'encryption_secret': self.ENCRYPTION_SECRET,
                'last_db_compact': self.LAST_DB_COMPACT,
                'git_autoissues': int(self.GIT_AUTOISSUES),
                'git_username': self.GIT_USERNAME,
                'git_password': self.GIT_PASSWORD,
                'git_reset': int(self.GIT_RESET),
                'git_newver': int(self.GIT_NEWVER),
                'log_nr': int(self.LOG_NR),
                'log_size': int(self.LOG_SIZE),
                'socket_timeout': self.SOCKET_TIMEOUT,
                'web_port': self.WEB_PORT,
                'web_host': self.WEB_HOST,
                'web_ipv6': int(self.WEB_IPV6),
                'web_log': int(self.WEB_LOG),
                'web_root': self.WEB_ROOT,
                'web_username': self.WEB_USERNAME,
                'web_password': self.WEB_PASSWORD,
                'web_cookie_secret': self.WEB_COOKIE_SECRET,
                'web_use_gzip': int(self.WEB_USE_GZIP),
                'ssl_verify': int(self.SSL_VERIFY),
                'download_url': self.DOWNLOAD_URL,
                'cpu_preset': self.CPU_PRESET,
                'anon_redirect': self.ANON_REDIRECT,
                'api_key': self.API_KEY,
                'debug': int(self.DEBUG),
                'default_page': self.DEFAULT_PAGE,
                'enable_https': int(self.ENABLE_HTTPS),
                'https_cert': self.HTTPS_CERT,
                'https_key': self.HTTPS_KEY,
                'handle_reverse_proxy': int(self.HANDLE_REVERSE_PROXY),
                'use_nzbs': int(self.USE_NZBS),
                'use_torrents': int(self.USE_TORRENTS),
                'nzb_method': self.NZB_METHOD,
                'torrent_method': self.TORRENT_METHOD,
                'usenet_retention': int(self.USENET_RETENTION),
                'autopostprocessor_frequency': int(self.AUTOPOSTPROCESSOR_FREQ),
                'dailysearch_frequency': int(self.DAILY_SEARCHER_FREQ),
                'backlog_frequency': int(self.BACKLOG_SEARCHER_FREQ),
                'update_frequency': int(self.VERSION_UPDATER_FREQ),
                'showupdate_hour': int(self.SHOWUPDATE_HOUR),
                'showupdate_stale': int(self.SHOWUPDATE_STALE),
                'download_propers': int(self.DOWNLOAD_PROPERS),
                'enable_rss_cache': int(self.ENABLE_RSS_CACHE),
                'randomize_providers': int(self.RANDOMIZE_PROVIDERS),
                'check_propers_interval': self.PROPER_SEARCHER_INTERVAL,
                'allow_high_priority': int(self.ALLOW_HIGH_PRIORITY),
                'skip_removed_files': int(self.SKIP_REMOVED_FILES),
                'quality_default': int(self.QUALITY_DEFAULT),
                'status_default': int(self.STATUS_DEFAULT),
                'status_default_after': int(self.STATUS_DEFAULT_AFTER),
                'flatten_folders_default': int(self.FLATTEN_FOLDERS_DEFAULT),
                'indexer_default': int(self.INDEXER_DEFAULT),
                'indexer_timeout': int(self.INDEXER_TIMEOUT),
                'anime_default': int(self.ANIME_DEFAULT),
                'scene_default': int(self.SCENE_DEFAULT),
                'archive_default': int(self.ARCHIVE_DEFAULT),
                'version_notify': int(self.VERSION_NOTIFY),
                'auto_update': int(self.AUTO_UPDATE),
                'notify_on_update': int(self.NOTIFY_ON_UPDATE),
                'naming_strip_year': int(self.NAMING_STRIP_YEAR),
                'naming_pattern': self.NAMING_PATTERN,
                'naming_custom_abd': int(self.NAMING_CUSTOM_ABD),
                'naming_abd_pattern': self.NAMING_ABD_PATTERN,
                'naming_custom_sports': int(self.NAMING_CUSTOM_SPORTS),
                'naming_sports_pattern': self.NAMING_SPORTS_PATTERN,
                'naming_custom_anime': int(self.NAMING_CUSTOM_ANIME),
                'naming_anime_pattern': self.NAMING_ANIME_PATTERN,
                'naming_multi_ep': int(self.NAMING_MULTI_EP),
                'naming_anime_multi_ep': int(self.NAMING_ANIME_MULTI_EP),
                'naming_anime': int(self.NAMING_ANIME),
                'indexerDefaultLang': self.INDEXER_DEFAULT_LANGUAGE,
                'ep_default_deleted_status': int(self.EP_DEFAULT_DELETED_STATUS),
                'launch_browser': int(self.LAUNCH_BROWSER),
                'trash_remove_show': int(self.TRASH_REMOVE_SHOW),
                'trash_rotate_logs': int(self.TRASH_ROTATE_LOGS),
                'sort_article': int(self.SORT_ARTICLE),
                'proxy_setting': self.PROXY_SETTING,
                'proxy_indexers': int(self.PROXY_INDEXERS),
                'use_listview': int(self.USE_LISTVIEW),
                'backlog_days': int(self.BACKLOG_DAYS),
                'root_dirs': self.ROOT_DIRS,
                'tv_download_dir': self.TV_DOWNLOAD_DIR,
                'keep_processed_dir': int(self.KEEP_PROCESSED_DIR),
                'process_method': self.PROCESS_METHOD,
                'del_rar_contents': int(self.DELRARCONTENTS),
                'move_associated_files': int(self.MOVE_ASSOCIATED_FILES),
                'sync_files': self.SYNC_FILES,
                'postpone_if_sync_files': int(self.POSTPONE_IF_SYNC_FILES),
                'nfo_rename': int(self.NFO_RENAME),
                'process_automatically': int(self.PROCESS_AUTOMATICALLY),
                'no_delete': int(self.NO_DELETE),
                'unpack': int(self.UNPACK),
                'rename_episodes': int(self.RENAME_EPISODES),
                'airdate_episodes': int(self.AIRDATE_EPISODES),
                'file_timestamp_timezone': self.FILE_TIMESTAMP_TIMEZONE,
                'create_missing_show_dirs': int(self.CREATE_MISSING_SHOW_DIRS),
                'add_shows_wo_dir': int(self.ADD_SHOWS_WO_DIR),
                'extra_scripts': '|'.join(self.EXTRA_SCRIPTS),
                'pip_path': self.PIP_PATH,
                'git_path': self.GIT_PATH,
                'ignore_words': self.IGNORE_WORDS,
                'require_words': self.REQUIRE_WORDS,
                'ignored_subs_list': self.IGNORED_SUBS_LIST,
                'calendar_unprotected': int(self.CALENDAR_UNPROTECTED),
                'calendar_icons': int(self.CALENDAR_ICONS),
                'no_restart': int(self.NO_RESTART),
                'developer': int(self.DEVELOPER),
                'display_all_seasons': int(self.DISPLAY_ALL_SEASONS),
                'random_user_agent': int(self.RANDOM_USER_AGENT),
            },
            'GUI': {
                'gui_name': self.GUI_NAME,
                'theme_name': self.THEME_NAME,
                'home_layout': self.HOME_LAYOUT,
                'history_layout': self.HISTORY_LAYOUT,
                'history_limit': self.HISTORY_LIMIT,
                'display_show_specials': int(self.DISPLAY_SHOW_SPECIALS),
                'coming_eps_layout': self.COMING_EPS_LAYOUT,
                'coming_eps_display_paused': int(self.COMING_EPS_DISPLAY_PAUSED),
                'coming_eps_sort': self.COMING_EPS_SORT,
                'coming_eps_missed_range': int(self.COMING_EPS_MISSED_RANGE),
                'fuzzy_dating': int(self.FUZZY_DATING),
                'trim_zero': int(self.TRIM_ZERO),
                'date_preset': self.DATE_PRESET,
                'time_preset': self.TIME_PRESET_W_SECONDS,
                'timezone_display': self.TIMEZONE_DISPLAY,
                'poster_sortby': self.POSTER_SORTBY,
                'poster_sortdir': self.POSTER_SORTDIR,
                'filter_row': int(self.FILTER_ROW),
                'fanart_background': int(self.FANART_BACKGROUND),
                'fanart_background_opacity': self.FANART_BACKGROUND_OPACITY,
            },
            'Blackhole': {
                'nzb_dir': self.NZB_DIR,
                'torrent_dir': self.TORRENT_DIR,
            },
            'NZBs': {
                'nzbs': int(self.NZBS),
                'nzbs_uid': self.NZBS_UID,
                'nzbs_hash': self.NZBS_HASH,
            },
            'Newzbin': {
                'newzbin': int(self.NEWZBIN),
                'newzbin_username': self.NEWZBIN_USERNAME,
                'newzbin_password': self.NEWZBIN_PASSWORD,
            },
            'SABnzbd': {
                'sab_username': self.SAB_USERNAME,
                'sab_password': self.SAB_PASSWORD,
                'sab_apikey': self.SAB_APIKEY,
                'sab_category': self.SAB_CATEGORY,
                'sab_category_backlog': self.SAB_CATEGORY_BACKLOG,
                'sab_category_anime': self.SAB_CATEGORY_ANIME,
                'sab_category_anime_backlog': self.SAB_CATEGORY_ANIME_BACKLOG,
                'sab_host': self.SAB_HOST,
                'sab_forced': int(self.SAB_FORCED),
            },
            'NZBget': {
                'nzbget_username': self.NZBGET_USERNAME,
                'nzbget_password': self.NZBGET_PASSWORD,
                'nzbget_category': self.NZBGET_CATEGORY,
                'nzbget_category_backlog': self.NZBGET_CATEGORY_BACKLOG,
                'nzbget_category_anime': self.NZBGET_CATEGORY_ANIME,
                'nzbget_category_anime_backlog': self.NZBGET_CATEGORY_ANIME_BACKLOG,
                'nzbget_host': self.NZBGET_HOST,
                'nzbget_use_https': int(self.NZBGET_USE_HTTPS),
                'nzbget_priority': self.NZBGET_PRIORITY,
            },
            'TORRENT': {
                'torrent_username': self.TORRENT_USERNAME,
                'torrent_password': self.TORRENT_PASSWORD,
                'torrent_host': self.TORRENT_HOST,
                'torrent_path': self.TORRENT_PATH,
                'torrent_seed_time': int(self.TORRENT_SEED_TIME),
                'torrent_paused': int(self.TORRENT_PAUSED),
                'torrent_high_bandwidth': int(self.TORRENT_HIGH_BANDWIDTH),
                'torrent_label': self.TORRENT_LABEL,
                'torrent_label_anime': self.TORRENT_LABEL_ANIME,
                'torrent_verify_cert': int(self.TORRENT_VERIFY_CERT),
                'torrent_rpcurl': self.TORRENT_RPCURL,
                'torrent_auth_type': self.TORRENT_AUTH_TYPE,
                'torrent_trackers': self.TORRENT_TRACKERS,
            },
            'KODI': {
                'use_kodi': int(self.USE_KODI),
                'kodi_always_on': int(self.KODI_ALWAYS_ON),
                'kodi_notify_onsnatch': int(self.KODI_NOTIFY_ONSNATCH),
                'kodi_notify_ondownload': int(self.KODI_NOTIFY_ONDOWNLOAD),
                'kodi_notify_onsubtitledownload': int(self.KODI_NOTIFY_ONSUBTITLEDOWNLOAD),
                'kodi_update_library': int(self.KODI_UPDATE_LIBRARY),
                'kodi_update_full': int(self.KODI_UPDATE_FULL),
                'kodi_update_onlyfirst': int(self.KODI_UPDATE_ONLYFIRST),
                'kodi_host': self.KODI_HOST,
                'kodi_username': self.KODI_USERNAME,
                'kodi_password': self.KODI_PASSWORD,
            },
            'Plex': {
                'use_plex': int(self.USE_PLEX),
                'plex_notify_onsnatch': int(self.PLEX_NOTIFY_ONSNATCH),
                'plex_notify_ondownload': int(self.PLEX_NOTIFY_ONDOWNLOAD),
                'plex_notify_onsubtitledownload': int(self.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD),
                'plex_update_library': int(self.PLEX_UPDATE_LIBRARY),
                'plex_server_host': self.PLEX_SERVER_HOST,
                'plex_server_token': self.PLEX_SERVER_TOKEN,
                'plex_host': self.PLEX_HOST,
                'plex_username': self.PLEX_USERNAME,
                'plex_password': self.PLEX_PASSWORD,
            },
            'Emby': {
                'use_emby': int(self.USE_EMBY),
                'emby_host': self.EMBY_HOST,
                'emby_apikey': self.EMBY_APIKEY,
            },
            'Growl': {
                'use_growl': int(self.USE_GROWL),
                'growl_notify_onsnatch': int(self.GROWL_NOTIFY_ONSNATCH),
                'growl_notify_ondownload': int(self.GROWL_NOTIFY_ONDOWNLOAD),
                'growl_notify_onsubtitledownload': int(self.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD),
                'growl_host': self.GROWL_HOST,
                'growl_password': self.GROWL_PASSWORD,
            },
            'FreeMobile': {
                'use_freemobile': int(self.USE_FREEMOBILE),
                'freemobile_notify_onsnatch': int(self.FREEMOBILE_NOTIFY_ONSNATCH),
                'freemobile_notify_ondownload': int(self.FREEMOBILE_NOTIFY_ONDOWNLOAD),
                'freemobile_notify_onsubtitledownload': int(self.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD),
                'freemobile_id': self.FREEMOBILE_ID,
                'freemobile_apikey': self.FREEMOBILE_APIKEY,
            },
            'Prowl': {
                'use_prowl': int(self.USE_PROWL),
                'prowl_notify_onsnatch': int(self.PROWL_NOTIFY_ONSNATCH),
                'prowl_notify_ondownload': int(self.PROWL_NOTIFY_ONDOWNLOAD),
                'prowl_notify_onsubtitledownload': int(self.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD),
                'prowl_api': self.PROWL_API,
                'prowl_priority': self.PROWL_PRIORITY,
            },

            'Twitter': {
                'use_twitter': int(self.USE_TWITTER),
                'twitter_notify_onsnatch': int(self.TWITTER_NOTIFY_ONSNATCH),
                'twitter_notify_ondownload': int(self.TWITTER_NOTIFY_ONDOWNLOAD),
                'twitter_notify_onsubtitledownload': int(self.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD),
                'twitter_username': self.TWITTER_USERNAME,
                'twitter_password': self.TWITTER_PASSWORD,
                'twitter_prefix': self.TWITTER_PREFIX,
                'twitter_dmto': self.TWITTER_DMTO,
                'twitter_usedm': int(self.TWITTER_USEDM),
            },
            'Boxcar': {
                'use_boxcar': int(self.USE_BOXCAR),
                'boxcar_notify_onsnatch': int(self.BOXCAR_NOTIFY_ONSNATCH),
                'boxcar_notify_ondownload': int(self.BOXCAR_NOTIFY_ONDOWNLOAD),
                'boxcar_notify_onsubtitledownload': int(self.BOXCAR_NOTIFY_ONSUBTITLEDOWNLOAD),
                'boxcar_username': self.BOXCAR_USERNAME,

            },
            'Boxcar2': {
                'use_boxcar2': int(self.USE_BOXCAR2),
                'boxcar2_notify_onsnatch': int(self.BOXCAR2_NOTIFY_ONSNATCH),
                'boxcar2_notify_ondownload': int(self.BOXCAR2_NOTIFY_ONDOWNLOAD),
                'boxcar2_notify_onsubtitledownload': int(self.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD),
                'boxcar2_accesstoken': self.BOXCAR2_ACCESSTOKEN,
            },
            'Pushover': {
                'use_pushover': int(self.USE_PUSHOVER),
                'pushover_notify_onsnatch': int(self.PUSHOVER_NOTIFY_ONSNATCH),
                'pushover_notify_ondownload': int(self.PUSHOVER_NOTIFY_ONDOWNLOAD),
                'pushover_notify_onsubtitledownload': int(self.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD),
                'pushover_userkey': self.PUSHOVER_USERKEY,
                'pushover_apikey': self.PUSHOVER_APIKEY,
                'pushover_device': self.PUSHOVER_DEVICE,
                'pushover_sound': self.PUSHOVER_SOUND,
            },
            'Libnotify': {
                'use_libnotify': int(self.USE_LIBNOTIFY),
                'libnotify_notify_onsnatch': int(self.LIBNOTIFY_NOTIFY_ONSNATCH),
                'libnotify_notify_ondownload': int(self.LIBNOTIFY_NOTIFY_ONDOWNLOAD),
                'libnotify_notify_onsubtitledownload': int(self.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD)
            },
            'NMJ': {
                'use_nmj': int(self.USE_NMJ),
                'nmj_host': self.NMJ_HOST,
                'nmj_database': self.NMJ_DATABASE,
                'nmj_mount': self.NMJ_MOUNT,
            },
            'NMJv2': {
                'use_nmjv2': int(self.USE_NMJv2),
                'nmjv2_host': self.NMJv2_HOST,
                'nmjv2_database': self.NMJv2_DATABASE,
                'nmjv2_dbloc': self.NMJv2_DBLOC,
            },
            'Synology': {
                'use_synoindex': int(self.USE_SYNOINDEX),
            },
            'SynologyNotifier': {
                'use_synologynotifier': int(self.USE_SYNOLOGYNOTIFIER),
                'synologynotifier_notify_onsnatch': int(self.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH),
                'synologynotifier_notify_ondownload': int(self.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD),
                'synologynotifier_notify_onsubtitledownload': int(self.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD),
            },
            'theTVDB': {
                'thetvdb_apitoken': self.THETVDB_APITOKEN,
            },
            'Trakt': {
                'use_trakt': int(self.USE_TRAKT),
                'trakt_username': self.TRAKT_USERNAME,
                'trakt_oauth_token': pickle.dumps(self.TRAKT_OAUTH_TOKEN),
                'trakt_remove_watchlist': int(self.TRAKT_REMOVE_WATCHLIST),
                'trakt_remove_serieslist': int(self.TRAKT_REMOVE_SERIESLIST),
                'trakt_remove_show_from_sickrage': int(self.TRAKT_REMOVE_SHOW_FROM_SICKRAGE),
                'trakt_sync_watchlist': int(self.TRAKT_SYNC_WATCHLIST),
                'trakt_method_add': int(self.TRAKT_METHOD_ADD),
                'trakt_start_paused': int(self.TRAKT_START_PAUSED),
                'trakt_use_recommended': int(self.TRAKT_USE_RECOMMENDED),
                'trakt_sync': int(self.TRAKT_SYNC),
                'trakt_sync_remove': int(self.TRAKT_SYNC_REMOVE),
                'trakt_default_indexer': int(self.TRAKT_DEFAULT_INDEXER),
                'trakt_timeout': int(self.TRAKT_TIMEOUT),
                'trakt_blacklist_name': self.TRAKT_BLACKLIST_NAME,
            },
            'pyTivo': {
                'use_pytivo': int(self.USE_PYTIVO),
                'pytivo_notify_onsnatch': int(self.PYTIVO_NOTIFY_ONSNATCH),
                'pytivo_notify_ondownload': int(self.PYTIVO_NOTIFY_ONDOWNLOAD),
                'pytivo_notify_onsubtitledownload': int(self.PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD),
                'pyTivo_update_library': int(self.PYTIVO_UPDATE_LIBRARY),
                'pytivo_host': self.PYTIVO_HOST,
                'pytivo_share_name': self.PYTIVO_SHARE_NAME,
                'pytivo_tivo_name': self.PYTIVO_TIVO_NAME,
            },
            'NMA': {
                'use_nma': int(self.USE_NMA),
                'nma_notify_onsnatch': int(self.NMA_NOTIFY_ONSNATCH),
                'nma_notify_ondownload': int(self.NMA_NOTIFY_ONDOWNLOAD),
                'nma_notify_onsubtitledownload': int(self.NMA_NOTIFY_ONSUBTITLEDOWNLOAD),
                'nma_api': self.NMA_API,
                'nma_priority': self.NMA_PRIORITY,
            },
            'Pushalot': {
                'use_pushalot': int(self.USE_PUSHALOT),
                'pushalot_notify_onsnatch': int(self.PUSHALOT_NOTIFY_ONSNATCH),
                'pushalot_notify_ondownload': int(self.PUSHALOT_NOTIFY_ONDOWNLOAD),
                'pushalot_notify_onsubtitledownload': int(self.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD),
                'pushalot_authorizationtoken': self.PUSHALOT_AUTHORIZATIONTOKEN,
            },
            'Pushbullet': {
                'use_pushbullet': int(self.USE_PUSHBULLET),
                'pushbullet_notify_onsnatch': int(self.PUSHBULLET_NOTIFY_ONSNATCH),
                'pushbullet_notify_ondownload': int(self.PUSHBULLET_NOTIFY_ONDOWNLOAD),
                'pushbullet_notify_onsubtitledownload': int(self.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD),
                'pushbullet_api': self.PUSHBULLET_API,
                'pushbullet_device': self.PUSHBULLET_DEVICE,
            },
            'Email': {
                'use_email': int(self.USE_EMAIL),
                'email_notify_onsnatch': int(self.EMAIL_NOTIFY_ONSNATCH),
                'email_notify_ondownload': int(self.EMAIL_NOTIFY_ONDOWNLOAD),
                'email_notify_onsubtitledownload': int(self.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD),
                'email_host': self.EMAIL_HOST,
                'email_port': int(self.EMAIL_PORT),
                'email_tls': int(self.EMAIL_TLS),
                'email_user': self.EMAIL_USER,
                'email_password': self.EMAIL_PASSWORD,
                'email_from': self.EMAIL_FROM,
                'email_list': self.EMAIL_LIST,
            },
            'Subtitles': {
                'use_subtitles': int(self.USE_SUBTITLES),
                'subtitles_languages': ','.join(self.SUBTITLES_LANGUAGES),
                'subtitles_services_list': ','.join(self.SUBTITLES_SERVICES_LIST),
                'subtitles_services_enabled': '|'.join([str(x) for x in self.SUBTITLES_SERVICES_ENABLED]),
                'subtitles_dir': self.SUBTITLES_DIR,
                'subtitles_default': int(self.SUBTITLES_DEFAULT),
                'subtitles_history': int(self.SUBTITLES_HISTORY),
                'embedded_subtitles_all': int(self.EMBEDDED_SUBTITLES_ALL),
                'subtitles_hearing_impaired': int(self.SUBTITLES_HEARING_IMPAIRED),
                'subtitles_finder_frequency': int(self.SUBTITLE_SEARCHER_FREQ),
                'subtitles_multi': int(self.SUBTITLES_MULTI),
                'subtitles_extra_scripts': '|'.join(self.SUBTITLES_EXTRA_SCRIPTS),
                'addic7ed_username': self.ADDIC7ED_USER,
                'addic7ed_password': self.ADDIC7ED_PASS,
                'legendastv_username': self.LEGENDASTV_USER,
                'legendastv_password': self.LEGENDASTV_PASS,
                'itasa_username': self.ITASA_USER,
                'itasa_password': self.ITASA_PASS,
                'opensubtitles_username': self.OPENSUBTITLES_USER,
                'opensubtitles_password': self.OPENSUBTITLES_PASS,
            },
            'FailedDownloads': {
                'use_failed_downloads': int(self.USE_FAILED_DOWNLOADS),
                'delete_failed': int(self.DELETE_FAILED),
            },
            'ANIDB': {
                'use_anidb': int(self.USE_ANIDB),
                'anidb_username': self.ANIDB_USERNAME,
                'anidb_password': self.ANIDB_PASSWORD,
                'anidb_use_mylist': int(self.ANIDB_USE_MYLIST),
            },
            'ANIME': {
                'anime_split_home': int(self.ANIME_SPLIT_HOME),
            },
            'Quality': {
                'sizes': pickle.dumps(self.QUALITY_SIZES),
            },
            'Providers': {
                'providers_order': sickrage.srCore.providersDict.provider_order,
                'custom_providers': self.CUSTOM_PROVIDERS,
            },
            'MetadataProviders': {}
        })

        provider_keys = ['enabled', 'confirmed', 'ranked', 'engrelease', 'onlyspasearch', 'sorting', 'options', 'ratio',
                         'minseed', 'minleech', 'freeleech', 'search_mode', 'search_fallback', 'enable_daily', 'key',
                         'enable_backlog', 'cat', 'subtitle', 'api_key', 'hash', 'digest', 'username', 'password',
                         'passkey', 'pin', 'reject_m2ts', 'enable_cookies', 'cookies']

        for providerID, providerObj in sickrage.srCore.providersDict.all().items():
            new_config['Providers'][providerID] = dict(
                [(x, providerObj.__dict__[x]) for x in provider_keys if hasattr(providerObj, x)])

        for metadataProviderID, metadataProviderObj in sickrage.srCore.metadataProvidersDict.items():
            new_config['MetadataProviders'][metadataProviderID] = metadataProviderObj.get_config()

        # encrypt settings
        new_config.walk(self.encrypt)
        new_config.write()

    def encrypt(self, section, key, _decrypt=False):
        """
        :rtype: basestring
        """

        if key in ['config_version', 'encryption_version', 'encryption_secret']:
            pass
        else:
            try:
                if self.ENCRYPTION_VERSION == 1:
                    unique_key1 = hex(uuid.getnode() ** 2)

                    if _decrypt:
                        section[key] = ''.join(
                            chr(ord(x) ^ ord(y)) for (x, y) in
                            izip(base64.decodestring(section[key]), cycle(unique_key1)))
                    else:
                        section[key] = base64.encodestring(
                            ''.join(chr(ord(x) ^ ord(y)) for (x, y) in izip(section[key], cycle(unique_key1)))).strip()
                elif self.ENCRYPTION_VERSION == 2:
                    if _decrypt:
                        section[key] = ''.join(chr(ord(x) ^ ord(y)) for (x, y) in
                                               izip(base64.decodestring(section[key]),
                                                    cycle(sickrage.srCore.srConfig.ENCRYPTION_SECRET)))
                    else:
                        section[key] = base64.encodestring(
                            ''.join(chr(ord(x) ^ ord(y)) for (x, y) in izip(section[key], cycle(
                                sickrage.srCore.srConfig.ENCRYPTION_SECRET)))).strip()
            except:
                pass

    def decrypt(self, section, key):
        return self.encrypt(section, key, _decrypt=True)


class ConfigMigrator(srConfig):
    def __init__(self, configobj):
        """
        Initializes a config migrator that can take the config from the version indicated in the config
        file up to the latest version
        """
        super(ConfigMigrator, self).__init__()
        self.CONFIG_OBJ = configobj

        # check the version of the config
        self.config_version = self.check_setting_int('General', 'config_version', self.CONFIG_VERSION)
        self.expected_config_version = self.CONFIG_VERSION

        self.migration_names = {
            1: 'Sync backup number with version number',
            2: 'Sync backup number with version number',
            3: 'Sync backup number with version number',
            4: 'Sync backup number with version number',
            5: 'Sync backup number with version number',
            6: 'Sync backup number with version number',
            7: 'Sync backup number with version number',
            8: 'Use version 2 for password encryption',
            9: 'Rename slick gui template name to default',
            10: 'Add enabled attribute to metadata settings',
            11: 'Rename all metadata settings'
        }

    def migrate_config(self):
        """
        Calls each successive migration until the config is the same version as SB expects
        """

        if self.config_version > self.expected_config_version:
            sickrage.srCore.srLogger.error(
                """Your config version (%i) has been incremented past what this version of supports (%i).
                    If you have used other forks or a newer version of  your config file may be unusable due to their modifications.""" %
                (self.config_version, self.expected_config_version)
            )
            sys.exit(1)

        self.CONFIG_VERSION = self.config_version

        while self.config_version < self.expected_config_version:
            next_version = self.config_version + 1

            if next_version in self.migration_names:
                migration_name = ': ' + self.migration_names[next_version]
            else:
                migration_name = ''

            sickrage.srCore.srLogger.info("Backing up config before upgrade")
            if not backupVersionedFile(sickrage.CONFIG_FILE, self.config_version):
                sickrage.srCore.srLogger.exit("Config backup failed, abort upgrading config")
                sys.exit(1)
            else:
                sickrage.srCore.srLogger.info("Proceeding with upgrade")

            # do the migration, expect a method named _migrate_v<num>
            sickrage.srCore.srLogger.info("Migrating config up to version " + str(next_version) + migration_name)
            self.CONFIG_OBJ = getattr(self, '_migrate_v' + str(next_version))()
            self.config_version = next_version

            # update config version to newest
            self.CONFIG_VERSION = self.config_version

        return self.CONFIG_OBJ

    # Migration v1: Dummy migration to sync backup number with config version number
    def _migrate_v1(self):
        return self.CONFIG_OBJ

    # Migration v2: Dummy migration to sync backup number with config version number
    def _migrate_v2(self):
        return self.CONFIG_OBJ

    # Migration v3: Dummy migration to sync backup number with config version number
    def _migrate_v3(self):
        return self.CONFIG_OBJ

    # Migration v4: Dummy migration to sync backup number with config version number
    def _migrate_v4(self):
        return self.CONFIG_OBJ

    # Migration v5: Dummy migration to sync backup number with config version number
    def _migrate_v5(self):
        return self.CONFIG_OBJ

    # Migration v6: Dummy migration to sync backup number with config version number
    def _migrate_v6(self):
        return self.CONFIG_OBJ

    # Migration v6: Dummy migration to sync backup number with config version number
    def _migrate_v7(self):
        return self.CONFIG_OBJ

    # Migration v8: Use version 2 for password encryption
    def _migrate_v8(self):
        self.CONFIG_OBJ['General']['encryption_version'] = 2
        return self.CONFIG_OBJ

    # Migration v9: Rename gui template name from slick to default
    def _migrate_v9(self):
        self.CONFIG_OBJ['GUI']['gui_name'] = 'default'
        return self.CONFIG_OBJ

    # Migration v10: Metadata upgrade to add enabled attribute
    def _migrate_v10(self):
        """
        Updates metadata values to the new format
        Quick overview of what the upgrade does:

        new | old | description (new)
        ----+-----+--------------------
          1 |  1  | show metadata
          2 |  2  | episode metadata
          3 |  3  | show fanart
          4 |  4  | show poster
          5 |  5  | show banner
          6 |  6  | episode thumb
          7 |  7  | season poster
          8 |  8  | season banner
          9 |  9  | season all poster
         10 |  10 | season all banner
         11 |  -  | enabled

        Note that the ini places start at 1 while the list index starts at 0.
        old format: 0|0|0|0|0|0|0|0|0|0 -- 10 places
        new format: 0|0|0|0|0|0|0|0|0|0|0 -- 11 places
        """

        metadata_kodi = self.check_setting_str('General', 'metadata_kodi', '0|0|0|0|0|0|0|0|0|0|0')
        metadata_kodi_12plus = self.check_setting_str('General', 'metadata_kodi_12plus', '0|0|0|0|0|0|0|0|0|0|0')
        metadata_mediabrowser = self.check_setting_str('General', 'metadata_mediabrowser', '0|0|0|0|0|0|0|0|0|0|0')
        metadata_ps3 = self.check_setting_str('General', 'metadata_ps3', '0|0|0|0|0|0|0|0|0|0|0')
        metadata_wdtv = self.check_setting_str('General', 'metadata_wdtv', '0|0|0|0|0|0|0|0|0|0|0')
        metadata_tivo = self.check_setting_str('General', 'metadata_tivo', '0|0|0|0|0|0|0|0|0|0|0')
        metadata_mede8er = self.check_setting_str('General', 'metadata_mede8er', '0|0|0|0|0|0|0|0|0|0|0')

        def _migrate_metadata(metadata):
            cur_metadata = metadata.split('|')

            # if target has the old number of values, do upgrade
            if len(cur_metadata) == 10:
                # write new format
                cur_metadata.append('0')
                metadata = '|'.join(cur_metadata)
            elif len(cur_metadata) == 11:
                metadata = '|'.join(cur_metadata)
            else:
                metadata = '0|0|0|0|0|0|0|0|0|0|0'

            return metadata

        self.CONFIG_OBJ['General']['metadata_kodi'] = _migrate_metadata(metadata_kodi)
        self.CONFIG_OBJ['General']['metadata_kodi_12plus'] = _migrate_metadata(metadata_kodi_12plus)
        self.CONFIG_OBJ['General']['metadata_mediabrowser'] = _migrate_metadata(metadata_mediabrowser)
        self.CONFIG_OBJ['General']['metadata_ps3'] = _migrate_metadata(metadata_ps3)
        self.CONFIG_OBJ['General']['metadata_wdtv'] = _migrate_metadata(metadata_wdtv)
        self.CONFIG_OBJ['General']['metadata_tivo'] = _migrate_metadata(metadata_tivo)
        self.CONFIG_OBJ['General']['metadata_mede8er'] = _migrate_metadata(metadata_mede8er)

        return self.CONFIG_OBJ

    # Migration v11: Renames metadata setting keys
    def _migrate_v11(self):
        """
        Renames metadata setting keys
        """

        metadata_kodi = self.check_setting_str('General', 'metadata_kodi', '0|0|0|0|0|0|0|0|0|0|0')
        metadata_kodi_12plus = self.check_setting_str('General', 'metadata_kodi_12plus', '0|0|0|0|0|0|0|0|0|0|0')
        metadata_mediabrowser = self.check_setting_str('General', 'metadata_mediabrowser', '0|0|0|0|0|0|0|0|0|0|0')
        metadata_ps3 = self.check_setting_str('General', 'metadata_ps3', '0|0|0|0|0|0|0|0|0|0|0')
        metadata_wdtv = self.check_setting_str('General', 'metadata_wdtv', '0|0|0|0|0|0|0|0|0|0|0')
        metadata_tivo = self.check_setting_str('General', 'metadata_tivo', '0|0|0|0|0|0|0|0|0|0|0')
        metadata_mede8er = self.check_setting_str('General', 'metadata_mede8er', '0|0|0|0|0|0|0|0|0|0|0')

        self.CONFIG_OBJ['MetadataProviders'] = {}
        self.CONFIG_OBJ['MetadataProviders']['kodi'] = metadata_kodi
        self.CONFIG_OBJ['MetadataProviders']['kodi_12plus'] = metadata_kodi_12plus
        self.CONFIG_OBJ['MetadataProviders']['mediabrowser'] = metadata_mediabrowser
        self.CONFIG_OBJ['MetadataProviders']['sony_ps3'] = metadata_ps3
        self.CONFIG_OBJ['MetadataProviders']['wdtv'] = metadata_wdtv
        self.CONFIG_OBJ['MetadataProviders']['tivo'] = metadata_tivo
        self.CONFIG_OBJ['MetadataProviders']['mede8er'] = metadata_mede8er

        return self.CONFIG_OBJ
