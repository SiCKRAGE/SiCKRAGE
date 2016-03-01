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

import os
import os.path
import platform
import re
import urlparse
import uuid

from configobj import ConfigObj
from datetime import datetime

import sickrage
from core.common import SD, WANTED, SKIPPED
from core.databases import main_db
from core.helpers import backupVersionedFile, decrypt, encrypt, makeDir, generateCookieSecret
from core.nameparser import validator
from core.nameparser.validator import check_force_season_folders
from core.searchers import backlog_searcher
from core.srscheduler import srIntervalTrigger
from providers import NewznabProvider, TorrentRssProvider, GenericProvider


class srConfig(object):
    def __init__(self, config_file):
        self.CONFIG_FILE = os.path.abspath(os.path.join(sickrage.DATA_DIR, config_file))
        self.CONFIG_VERSION = 7
        self.ENCRYPTION_VERSION = 0
        self.ENCRYPTION_SECRET = None
        self.CONFIG_OBJ = None

        self.USER_AGENT = '({};{};{})'.format(platform.system(), platform.release(), str(uuid.uuid1()))
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

        # censored log items
        self.LOG_DIR = None
        self.LOG_FILE = None
        self.LOG_SIZE = 1048576
        self.LOG_NR = 5
        self.SHOWUPDATER = None
        self.SHOWQUEUE = None
        self.SEARCHQUEUE = None
        self.NAMECACHE = None
        self.DAILYSEARCHER = None
        self.BACKLOGSEARCHER = None
        self.PROPERSEARCHER = None
        self.TRAKTSEARCHER = None
        self.SUBTITLESEARCHER = None
        self.VERSION_NOTIFY = False
        self.AUTO_UPDATE = False
        self.NOTIFY_ON_UPDATE = False
        self.GIT_ORG = 'SiCKRAGETV'
        self.GIT_REPO = 'SiCKRAGE'
        self.GITHUB = None
        self.GIT_RESET = True
        self.GIT_REMOTE = None
        self.GIT_REMOTE_URL = None
        self.GIT_USERNAME = None
        self.GIT_PASSWORD = None
        self.GIT_PATH = None
        self.GIT_AUTOISSUES = False
        self.GIT_NEWVER = False
        self.DEVELOPER = False
        self.NEWS_URL = 'http://sickragetv.github.io/news/news.md'
        self.CHANGES_URL = 'http://sickragetv.github.io/news/changes.md'
        self.NEWS_LAST_READ = None
        self.NEWS_LATEST = None
        self.NEWS_UNREAD = False
        self.SOCKET_TIMEOUT = None
        self.WEB_HOST = None
        self.WEB_PORT = None
        self.WEB_LOG = False
        self.WEB_ROOT = None
        self.WEB_USERNAME = None
        self.WEB_PASSWORD = None
        self.WEB_IPV6 = False
        self.WEB_COOKIE_SECRET = None
        self.WEB_USE_GZIP = True
        self.HANDLE_REVERSE_PROXY = False
        self.PROXY_SETTING = None
        self.PROXY_INDEXERS = True
        self.LOCALHOST_IP = None
        self.SSL_VERIFY = True
        self.ENABLE_HTTPS = False
        self.HTTPS_CERT = None
        self.HTTPS_KEY = None
        self.API_KEY = None
        self.API_ROOT = None
        self.INDEXER_DEFAULT_LANGUAGE = None
        self.EP_DEFAULT_DELETED_STATUS = None
        self.LAUNCH_BROWSER = False
        self.CACHE_DIR = None
        self.ROOT_DIRS = None
        self.CPU_PRESET = None
        self.ANON_REDIRECT = None
        self.DOWNLOAD_URL = None
        self.TRASH_REMOVE_SHOW = False
        self.TRASH_ROTATE_LOGS = False
        self.SORT_ARTICLE = False
        self.DEBUG = False
        self.DISPLAY_ALL_SEASONS = True
        self.DEFAULT_PAGE = None
        self.USE_LISTVIEW = False
        self.METADATA_KODI = None
        self.METADATA_KODI_12PLUS = None
        self.METADATA_MEDIABROWSER = None
        self.METADATA_PS3 = None
        self.METADATA_WDTV = None
        self.METADATA_TIVO = None
        self.METADATA_MEDE8ER = None
        self.QUALITY_DEFAULT = None
        self.STATUS_DEFAULT = None
        self.STATUS_DEFAULT_AFTER = None
        self.FLATTEN_FOLDERS_DEFAULT = False
        self.SUBTITLES_DEFAULT = False
        self.INDEXER_DEFAULT = None
        self.INDEXER_TIMEOUT = None
        self.SCENE_DEFAULT = False
        self.ANIME_DEFAULT = False
        self.ARCHIVE_DEFAULT = False
        self.PROVIDER_ORDER = None
        self.NAMING_MULTI_EP = False
        self.NAMING_ANIME_MULTI_EP = False
        self.NAMING_PATTERN = None
        self.NAMING_ABD_PATTERN = None
        self.NAMING_CUSTOM_ABD = False
        self.NAMING_SPORTS_PATTERN = None
        self.NAMING_CUSTOM_SPORTS = False
        self.NAMING_ANIME_PATTERN = None
        self.NAMING_CUSTOM_ANIME = False
        self.NAMING_FORCE_FOLDERS = False
        self.NAMING_STRIP_YEAR = False
        self.NAMING_ANIME = None
        self.USE_NZBS = False
        self.USE_TORRENTS = False
        self.NZB_METHOD = None
        self.NZB_DIR = None
        self.USENET_RETENTION = 500
        self.TORRENT_METHOD = None
        self.TORRENT_DIR = None
        self.DOWNLOAD_PROPERS = False
        self.PROPER_SEARCHER_INTERVAL = None
        self.ALLOW_HIGH_PRIORITY = False
        self.SAB_FORCED = False
        self.RANDOMIZE_PROVIDERS = False
        self.MIN_AUTOPOSTPROCESSOR_FREQ = 1
        self.MIN_NAMECACHE_FREQ = 1
        self.MIN_DAILY_SEARCHER_FREQ = 10
        self.MIN_BACKLOG_SEARCHER_FREQ = 10
        self.MIN_VERSION_UPDATER_FREQ = 1
        self.MIN_SUBTITLE_SEARCHER_FREQ = 1
        self.BACKLOG_DAYS = 7
        self.ADD_SHOWS_WO_DIR = False
        self.CREATE_MISSING_SHOW_DIRS = False
        self.RENAME_EPISODES = False
        self.AIRDATE_EPISODES = False
        self.FILE_TIMESTAMP_TIMEZONE = None
        self.PROCESS_AUTOMATICALLY = False
        self.NO_DELETE = False
        self.KEEP_PROCESSED_DIR = False
        self.PROCESS_METHOD = None
        self.DELRARCONTENTS = False
        self.MOVE_ASSOCIATED_FILES = False
        self.POSTPONE_IF_SYNC_FILES = True
        self.NFO_RENAME = True
        self.TV_DOWNLOAD_DIR = None
        self.UNPACK = False
        self.SKIP_REMOVED_FILES = False
        self.NZBS = False
        self.NZBS_UID = None
        self.NZBS_HASH = None
        self.OMGWTFNZBS = False
        self.OMGWTFNZBS_USERNAME = None
        self.OMGWTFNZBS_APIKEY = None
        self.NEWZBIN = False
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
        self.NZBGET_USE_HTTPS = False
        self.NZBGET_PRIORITY = 100
        self.TORRENT_USERNAME = None
        self.TORRENT_PASSWORD = None
        self.TORRENT_HOST = None
        self.TORRENT_PATH = None
        self.TORRENT_SEED_TIME = None
        self.TORRENT_PAUSED = False
        self.TORRENT_HIGH_BANDWIDTH = False
        self.TORRENT_LABEL = None
        self.TORRENT_LABEL_ANIME = None
        self.TORRENT_VERIFY_CERT = False
        self.TORRENT_RPCURL = None
        self.TORRENT_AUTH_TYPE = None
        self.USE_KODI = False
        self.KODI_ALWAYS_ON = True
        self.KODI_NOTIFY_ONSNATCH = False
        self.KODI_NOTIFY_ONDOWNLOAD = False
        self.KODI_NOTIFY_ONSUBTITLEDOWNLOAD = False
        self.KODI_UPDATE_LIBRARY = False
        self.KODI_UPDATE_FULL = False
        self.KODI_UPDATE_ONLYFIRST = False
        self.KODI_HOST = None
        self.KODI_USERNAME = None
        self.KODI_PASSWORD = None
        self.USE_PLEX = False
        self.PLEX_NOTIFY_ONSNATCH = False
        self.PLEX_NOTIFY_ONDOWNLOAD = False
        self.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD = False
        self.PLEX_UPDATE_LIBRARY = False
        self.PLEX_SERVER_HOST = None
        self.PLEX_SERVER_TOKEN = None
        self.PLEX_HOST = None
        self.PLEX_USERNAME = None
        self.PLEX_PASSWORD = None
        self.USE_PLEX_CLIENT = False
        self.PLEX_CLIENT_USERNAME = None
        self.PLEX_CLIENT_PASSWORD = None
        self.USE_EMBY = False
        self.EMBY_HOST = None
        self.EMBY_APIKEY = None
        self.USE_GROWL = False
        self.GROWL_NOTIFY_ONSNATCH = False
        self.GROWL_NOTIFY_ONDOWNLOAD = False
        self.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD = False
        self.GROWL_HOST = None
        self.GROWL_PASSWORD = None
        self.USE_FREEMOBILE = False
        self.FREEMOBILE_NOTIFY_ONSNATCH = False
        self.FREEMOBILE_NOTIFY_ONDOWNLOAD = False
        self.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD = False
        self.FREEMOBILE_ID = None
        self.FREEMOBILE_APIKEY = None
        self.USE_PROWL = False
        self.PROWL_NOTIFY_ONSNATCH = False
        self.PROWL_NOTIFY_ONDOWNLOAD = False
        self.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD = False
        self.PROWL_API = None
        self.PROWL_PRIORITY = False
        self.USE_TWITTER = False
        self.TWITTER_NOTIFY_ONSNATCH = False
        self.TWITTER_NOTIFY_ONDOWNLOAD = False
        self.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD = False
        self.TWITTER_USERNAME = None
        self.TWITTER_PASSWORD = None
        self.TWITTER_PREFIX = None
        self.TWITTER_DMTO = None
        self.TWITTER_USEDM = False
        self.USE_BOXCAR = False
        self.BOXCAR_NOTIFY_ONSNATCH = False
        self.BOXCAR_NOTIFY_ONDOWNLOAD = False
        self.BOXCAR_NOTIFY_ONSUBTITLEDOWNLOAD = False
        self.BOXCAR_USERNAME = None
        self.BOXCAR_PASSWORD = None
        self.BOXCAR_PREFIX = None
        self.USE_BOXCAR2 = False
        self.BOXCAR2_NOTIFY_ONSNATCH = False
        self.BOXCAR2_NOTIFY_ONDOWNLOAD = False
        self.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD = False
        self.BOXCAR2_ACCESSTOKEN = None
        self.USE_PUSHOVER = False
        self.PUSHOVER_NOTIFY_ONSNATCH = False
        self.PUSHOVER_NOTIFY_ONDOWNLOAD = False
        self.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD = False
        self.PUSHOVER_USERKEY = None
        self.PUSHOVER_APIKEY = None
        self.PUSHOVER_DEVICE = None
        self.PUSHOVER_SOUND = None
        self.USE_LIBNOTIFY = False
        self.LIBNOTIFY_NOTIFY_ONSNATCH = False
        self.LIBNOTIFY_NOTIFY_ONDOWNLOAD = False
        self.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD = False
        self.USE_NMJ = False
        self.NMJ_HOST = None
        self.NMJ_DATABASE = None
        self.NMJ_MOUNT = None
        self.ANIMESUPPORT = False
        self.USE_ANIDB = False
        self.ANIDB_USERNAME = None
        self.ANIDB_PASSWORD = None
        self.ANIDB_USE_MYLIST = False
        self.ADBA_CONNECTION = None
        self.ANIME_SPLIT_HOME = False
        self.USE_SYNOINDEX = False
        self.USE_NMJv2 = False
        self.NMJv2_HOST = None
        self.NMJv2_DATABASE = None
        self.NMJv2_DBLOC = None
        self.USE_SYNOLOGYNOTIFIER = False
        self.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH = False
        self.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD = False
        self.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD = False
        self.USE_TRAKT = False
        self.TRAKT_USERNAME = None
        self.TRAKT_ACCESS_TOKEN = None
        self.TRAKT_REFRESH_TOKEN = None
        self.TRAKT_REMOVE_WATCHLIST = False
        self.TRAKT_REMOVE_SERIESLIST = False
        self.TRAKT_REMOVE_SHOW_FROM_SICKRAGE = False
        self.TRAKT_SYNC_WATCHLIST = False
        self.TRAKT_METHOD_ADD = None
        self.TRAKT_START_PAUSED = False
        self.TRAKT_USE_RECOMMENDED = False
        self.TRAKT_SYNC = False
        self.TRAKT_SYNC_REMOVE = False
        self.TRAKT_DEFAULT_INDEXER = None
        self.TRAKT_TIMEOUT = None
        self.TRAKT_BLACKLIST_NAME = None
        self.USE_PYTIVO = False
        self.PYTIVO_NOTIFY_ONSNATCH = False
        self.PYTIVO_NOTIFY_ONDOWNLOAD = False
        self.PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD = False
        self.PYTIVO_UPDATE_LIBRARY = False
        self.PYTIVO_HOST = None
        self.PYTIVO_SHARE_NAME = None
        self.PYTIVO_TIVO_NAME = None
        self.USE_NMA = False
        self.NMA_NOTIFY_ONSNATCH = False
        self.NMA_NOTIFY_ONDOWNLOAD = False
        self.NMA_NOTIFY_ONSUBTITLEDOWNLOAD = False
        self.NMA_API = None
        self.NMA_PRIORITY = False
        self.USE_PUSHALOT = False
        self.PUSHALOT_NOTIFY_ONSNATCH = False
        self.PUSHALOT_NOTIFY_ONDOWNLOAD = False
        self.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD = False
        self.PUSHALOT_AUTHORIZATIONTOKEN = None
        self.USE_PUSHBULLET = False
        self.PUSHBULLET_NOTIFY_ONSNATCH = False
        self.PUSHBULLET_NOTIFY_ONDOWNLOAD = False
        self.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD = False
        self.PUSHBULLET_API = None
        self.PUSHBULLET_DEVICE = None
        self.USE_EMAIL = False
        self.EMAIL_NOTIFY_ONSNATCH = False
        self.EMAIL_NOTIFY_ONDOWNLOAD = False
        self.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD = False
        self.EMAIL_HOST = None
        self.EMAIL_PORT = 25
        self.EMAIL_TLS = False
        self.EMAIL_USER = None
        self.EMAIL_PASSWORD = None
        self.EMAIL_FROM = None
        self.EMAIL_LIST = None
        self.GUI_NAME = None
        self.GUI_DIR = None
        self.HOME_LAYOUT = None
        self.HISTORY_LAYOUT = None
        self.HISTORY_LIMIT = 0
        self.DISPLAY_SHOW_SPECIALS = False
        self.COMING_EPS_LAYOUT = None
        self.COMING_EPS_DISPLAY_PAUSED = False
        self.COMING_EPS_SORT = None
        self.COMING_EPS_MISSED_RANGE = None
        self.FUZZY_DATING = False
        self.TRIM_ZERO = False
        self.DATE_PRESET = None
        self.TIME_PRESET = None
        self.TIME_PRESET_W_SECONDS = None
        self.TIMEZONE_DISPLAY = None
        self.THEME_NAME = None
        self.POSTER_SORTBY = None
        self.POSTER_SORTDIR = None
        self.FILTER_ROW = True
        self.USE_SUBTITLES = False
        self.SUBTITLES_LANGUAGES = None
        self.SUBTITLES_DIR = None
        self.SUBTITLES_SERVICES_LIST = None
        self.SUBTITLES_SERVICES_ENABLED = None
        self.SUBTITLES_HISTORY = False
        self.EMBEDDED_SUBTITLES_ALL = False
        self.SUBTITLES_HEARING_IMPAIRED = False
        self.SUBTITLES_MULTI = False
        self.SUBTITLES_EXTRA_SCRIPTS = None
        self.ADDIC7ED_USER = None
        self.ADDIC7ED_PASS = None
        self.OPENSUBTITLES_USER = None
        self.OPENSUBTITLES_PASS = None
        self.LEGENDASTV_USER = None
        self.LEGENDASTV_PASS = None
        self.USE_FAILED_DOWNLOADS = False
        self.DELETE_FAILED = False
        self.EXTRA_SCRIPTS = None
        self.REQUIRE_WORDS = None
        self.IGNORE_WORDS = None
        self.IGNORED_SUBS_LIST = None
        self.SYNC_FILES = None
        self.CALENDAR_UNPROTECTED = False
        self.CALENDAR_ICONS = False
        self.NO_RESTART = False
        self.TMDB_API_KEY = 'edc5f123313769de83a71e157758030b'
        self.THETVDB_APITOKEN = None
        self.TRAKT_API_KEY = '5c65f55e11d48c35385d9e8670615763a605fad28374c8ae553a7b7a50651ddd'
        self.TRAKT_API_SECRET = 'b53e32045ac122a445ef163e6d859403301ffe9b17fb8321d428531b69022a82'
        self.TRAKT_PIN_URL = 'https://trakt.tv/pin/4562'
        self.TRAKT_OAUTH_URL = 'https://trakt.tv/'
        self.TRAKT_API_URL = 'https://api-v2launch.trakt.tv/'
        self.FANART_API_KEY = '9b3afaf26f6241bdb57d6cc6bd798da7'
        self.NEWZNAB_DATA = None
        self.TORRENTRSS_DATA = None
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
                sickrage.srLogger.info("Changed https cert path to " + https_cert)
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
                sickrage.srLogger.info("Changed https key path to " + https_key)
            else:
                return False

        return True

    def change_log_dir(self, new_log_dir, new_web_log):
        """
        Change logger directory for application and webserver
    
        :param new_log_dir: Path to new logger directory
        :param new_web_log: Enable/disable web logger
        :return: True on success, False on failure
        """

        web_log = self.checkbox_to_value(new_web_log)

        if self.LOG_DIR != new_log_dir:
            if not makeDir(new_log_dir):
                return False

            self.LOG_DIR = new_log_dir
            self.LOG_FILE = os.path.abspath(os.path.join(self.LOG_DIR, 'sickrage.log'))

            sickrage.srLogger.logFile = self.LOG_FILE
            sickrage.srLogger.logSize = self.LOG_SIZE
            sickrage.srLogger.logNr = self.LOG_NR
            sickrage.srLogger.fileLogging = True
            sickrage.srLogger.debugLogging = self.DEBUG
            sickrage.srLogger.start()

            sickrage.srLogger.info("Initialized new log file in " + self.LOG_DIR)
            if self.WEB_LOG != web_log:
                self.WEB_LOG = web_log

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
                sickrage.srLogger.info("Changed NZB folder to " + nzb_dir)
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
                sickrage.srLogger.info("Changed torrent folder to " + torrent_dir)
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
                sickrage.srLogger.info("Changed TV download folder to " + tv_download_dir)
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

        sickrage.srCore.SCHEDULER.modify_job('POSTPROCESSOR',
                                             trigger=srIntervalTrigger(
                                                 **{'minutes': self.AUTOPOSTPROCESSOR_FREQ,
                                                    'min': self.MIN_AUTOPOSTPROCESSOR_FREQ}))

    def change_daily_searcher_freq(self, freq):
        """
        Change frequency of daily search thread
    
        :param freq: New frequency
        """
        self.DAILY_SEARCHER_FREQ = self.to_int(freq, default=self.DEFAULT_DAILY_SEARCHER_FREQ)
        sickrage.srCore.SCHEDULER.modify_job('DAILYSEARCHER',
                                             trigger=srIntervalTrigger(
                                                 **{'minutes': self.DAILY_SEARCHER_FREQ,
                                                    'min': self.MIN_DAILY_SEARCHER_FREQ}))

    def change_backlog_searcher_freq(self, freq):
        """
        Change frequency of backlog thread
    
        :param freq: New frequency
        """
        self.BACKLOG_SEARCHER_FREQ = self.to_int(freq, default=self.DEFAULT_BACKLOG_SEARCHER_FREQ)
        self.MIN_BACKLOG_SEARCHER_FREQ = backlog_searcher.get_backlog_cycle_time()
        sickrage.srCore.SCHEDULER.modify_job('BACKLOG',
                                             trigger=srIntervalTrigger(
                                                 **{'minutes': self.BACKLOG_SEARCHER_FREQ,
                                                    'min': self.MIN_BACKLOG_SEARCHER_FREQ}))

    def change_updater_freq(self, freq):
        """
        Change frequency of daily updater thread
    
        :param freq: New frequency
        """
        self.VERSION_UPDATER_FREQ = self.to_int(freq, default=self.DEFAULT_VERSION_UPDATE_FREQ)
        sickrage.srCore.SCHEDULER.modify_job('VERSIONUPDATER',
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

        sickrage.srCore.SCHEDULER.modify_job('SHOWUPDATER',
                                             trigger=srIntervalTrigger(
                                                 **{'hours': 1,
                                                    'start_date': datetime.now().replace(
                                                        hour=self.SHOWUPDATE_HOUR)}))

    def change_subtitle_searcher_freq(self, freq):
        """
        Change frequency of subtitle thread
    
        :param freq: New frequency
        """
        self.SUBTITLE_SEARCHER_FREQ = self.to_int(freq, default=self.DEFAULT_SUBTITLE_SEARCHER_FREQ)
        sickrage.srCore.SCHEDULER.modify_job('SUBTITLESEARCHER',
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
        job = sickrage.srCore.SCHEDULER.get_job('PROPERSEARCHER')
        (job.pause, job.resume)[self.DOWNLOAD_PROPERS]()

    def change_use_trakt(self, use_trakt):
        """
        Enable/disable trakt thread
        TODO: Make this return true/false on success/failure
    
        :param use_trakt: New desired state
        """
        self.USE_TRAKT = self.checkbox_to_value(use_trakt)
        job = sickrage.srCore.SCHEDULER.get_job('TRAKTSEARCHER')
        (job.pause, job.resume)[self.USE_TRAKT]()

    def change_use_subtitles(self, use_subtitles):
        """
        Enable/Disable subtitle searcher
        TODO: Make this return true/false on success/failure
    
        :param use_subtitles: New desired state
        """
        self.USE_SUBTITLES = self.checkbox_to_value(use_subtitles)
        job = sickrage.srCore.SCHEDULER.get_job('SUBTITLESEARCHER')
        (job.pause, job.resume)[self.USE_SUBTITLES]()

    def change_process_automatically(self, process_automatically):
        """
        Enable/Disable postprocessor thread
        TODO: Make this return True/False on success/failure
    
        :param process_automatically: New desired state
        """
        self.PROCESS_AUTOMATICALLY = self.checkbox_to_value(process_automatically)
        job = sickrage.srCore.SCHEDULER.get_job('POSTPROCESSOR')
        (job.pause, job.resume)[self.PROCESS_AUTOMATICALLY]()

    def check_section(self, section):
        """ Check if INI section exists, if not create it """

        if section in self.CONFIG_OBJ:
            return True

        self.CONFIG_OBJ[section] = {}

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

    def clean_url(self, url):
        """
        Returns an cleaned url starting with a scheme and folder with trailing /
        or an empty string
        """

        if url and url.strip():

            url = url.strip()

            if '://' not in url:
                url = '//' + url

            scheme, netloc, path, query, fragment = urlparse.urlsplit(url, 'http')

            if not path:
                path += '/'

            cleaned_url = urlparse.urlunsplit((scheme, netloc, path, query, fragment))

        else:
            cleaned_url = ''

        return cleaned_url

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

    def check_setting_int(self, cfg_name, item_name, def_val, silent=True):
        try:
            my_val = self.CONFIG_OBJ[cfg_name][item_name]
            if str(my_val).lower() == "true":
                my_val = 1
            elif str(my_val).lower() == "false":
                my_val = 0

            my_val = int(my_val)

            if str(my_val) == str(None):
                raise
        except Exception:
            my_val = def_val
            try:
                self.CONFIG_OBJ[cfg_name][item_name] = my_val
            except Exception:
                self.CONFIG_OBJ[cfg_name] = {}
                self.CONFIG_OBJ[cfg_name][item_name] = my_val

        if not silent:
            sickrage.srLogger.debug(item_name + " -> " + str(my_val))

        return my_val

    ################################################################################
    # Check_setting_float                                                          #
    ################################################################################

    def check_setting_float(self, cfg_name, item_name, def_val, silent=True):
        try:
            my_val = float(self.CONFIG_OBJ[cfg_name][item_name])
            if str(my_val) == str(None):
                raise
        except Exception:
            my_val = def_val
            try:
                self.CONFIG_OBJ[cfg_name][item_name] = my_val
            except Exception:
                self.CONFIG_OBJ[cfg_name] = {}
                self.CONFIG_OBJ[cfg_name][item_name] = my_val

        if not silent:
            sickrage.srLogger.debug(item_name + " -> " + str(my_val))

        return my_val

    ################################################################################
    # Check_setting_str                                                            #
    ################################################################################

    def check_setting_str(self, cfg_name, item_name, def_val="", silent=True):
        # For passwords you must include the word `password` in the item_name and add `helpers.encrypt(ITEM_NAME, ENCRYPTION_VERSION)` in save_config()
        if bool(item_name.find('password') + 1):
            encryption_version = self.ENCRYPTION_VERSION
        else:
            encryption_version = 0

        try:
            my_val = decrypt(self.CONFIG_OBJ[cfg_name][item_name], encryption_version)
            if str(my_val) == str(None):
                raise
        except Exception:
            my_val = def_val
            try:
                self.CONFIG_OBJ[cfg_name][item_name] = encrypt(my_val, encryption_version)
            except Exception:
                self.CONFIG_OBJ[cfg_name] = {}
                self.CONFIG_OBJ[cfg_name][item_name] = encrypt(my_val, encryption_version)

        censored_regex = re.compile(r"|".join(re.escape(word) for word in ["password", "token", "api"]), re.I)
        if censored_regex.search(item_name) or (cfg_name, item_name) in sickrage.srLogger.censored_items:
            sickrage.srLogger.censored_items[cfg_name, item_name] = my_val

        if not silent:
            print(item_name + " -> " + my_val)

        return my_val

    def load_config(self):
        # Make sure we can write to the config file
        if not os.access(self.CONFIG_FILE, os.W_OK):
            if os.path.isfile(self.CONFIG_FILE):
                raise SystemExit("Config file '" + self.CONFIG_FILE + "' must be writeable.")
            elif not os.access(os.path.dirname(self.CONFIG_FILE), os.W_OK):
                raise SystemExit(
                    "Config file root dir '" + os.path.dirname(self.CONFIG_FILE) + "' must be writeable.")

        # create config object from config file
        self.CONFIG_OBJ = ConfigObj(self.CONFIG_FILE)

        # migrate config settings
        ConfigMigrator(self.CONFIG_OBJ).migrate_config()

        # config sanity check
        self.check_section('General')
        self.check_section('Blackhole')
        self.check_section('Newzbin')
        self.check_section('SABnzbd')
        self.check_section('NZBget')
        self.check_section('KODI')
        self.check_section('PLEX')
        self.check_section('Emby')
        self.check_section('Growl')
        self.check_section('Prowl')
        self.check_section('Twitter')
        self.check_section('Boxcar')
        self.check_section('Boxcar2')
        self.check_section('NMJ')
        self.check_section('NMJv2')
        self.check_section('Synology')
        self.check_section('SynologyNotifier')
        self.check_section('pyTivo')
        self.check_section('NMA')
        self.check_section('Pushalot')
        self.check_section('Pushbullet')
        self.check_section('Subtitles')
        self.check_section('pyTivo')
        self.check_section('theTVDB')
        self.check_section('Trakt')

        # Need to be before any passwords
        self.ENCRYPTION_VERSION = self.check_setting_int(
            'General', 'encryption_version', 0
        )

        self.ENCRYPTION_SECRET = self.check_setting_str(
            'General', 'encryption_secret', generateCookieSecret()
        )

        self.DEBUG = bool(self.check_setting_int('General', 'debug', 0))
        self.DEVELOPER = bool(self.check_setting_int('General', 'developer', 0))

        # logging settings
        self.LOG_NR = self.check_setting_int('General', 'log_nr', 5)
        self.LOG_SIZE = self.check_setting_int('General', 'log_size', 1048576)
        self.LOG_DIR = self.check_setting_str('General', 'log_dir', 'Logs')
        self.LOG_FILE = os.path.abspath(
            os.path.join(self.LOG_DIR, self.check_setting_str('General', 'log_file', 'sickrage.log')))

        # misc settings
        self.GUI_NAME = self.check_setting_str('GUI', 'gui_name', 'slick')
        self.GUI_DIR = os.path.join(sickrage.PROG_DIR, 'core', 'webserver', 'gui', self.GUI_NAME)
        self.THEME_NAME = self.check_setting_str('GUI', 'theme_name', 'dark')
        self.SOCKET_TIMEOUT = self.check_setting_int('General', 'socket_timeout', 30)

        self.DEFAULT_PAGE = self.check_setting_str('General', 'default_page', 'home')

        # git settings
        self.GIT_REMOTE_URL = self.check_setting_str(
            'General', 'git_remote_url',
            'https://github.com/{}/{}.git'.format(self.GIT_ORG, self.GIT_REPO)
        )

        self.GIT_PATH = self.check_setting_str('General', 'git_path', '')
        self.GIT_AUTOISSUES = bool(self.check_setting_int('General', 'git_autoissues', 0))
        self.GIT_USERNAME = self.check_setting_str('General', 'git_username', '')
        self.GIT_PASSWORD = self.check_setting_str('General', 'git_password', '')
        self.GIT_NEWVER = bool(self.check_setting_int('General', 'git_newver', 0))
        self.GIT_RESET = bool(self.check_setting_int('General', 'git_reset', 1))
        self.GIT_REMOTE = self.check_setting_str('General', 'git_remote', 'origin')

        # cache settings
        self.CACHE_DIR = self.check_setting_str('General', 'cache_dir', 'cache')
        if not os.path.isabs(self.CACHE_DIR):
            self.CACHE_DIR = os.path.join(sickrage.DATA_DIR, self.CACHE_DIR)

        # web settings
        self.WEB_PORT = self.check_setting_int('General', 'web_port', 8081)
        self.WEB_HOST = self.check_setting_str('General', 'web_host', '0.0.0.0')
        self.WEB_IPV6 = bool(self.check_setting_int('General', 'web_ipv6', 0))
        self.WEB_ROOT = self.check_setting_str('General', 'web_root', '').rstrip("/")
        self.WEB_LOG = bool(self.check_setting_int('General', 'web_log', 0))
        self.WEB_USERNAME = self.check_setting_str('General', 'web_username', '')
        self.WEB_PASSWORD = self.check_setting_str('General', 'web_password', '')
        self.WEB_COOKIE_SECRET = self.check_setting_str(
            'General', 'web_cookie_secret', generateCookieSecret()
        )
        self.WEB_USE_GZIP = bool(self.check_setting_int('General', 'web_use_gzip', 1))

        self.SSL_VERIFY = bool(self.check_setting_int('General', 'ssl_verify', 1))
        self.LAUNCH_BROWSER = bool(self.check_setting_int('General', 'launch_browser', 1))
        self.INDEXER_DEFAULT_LANGUAGE = self.check_setting_str('General', 'indexerDefaultLang', 'en')
        self.EP_DEFAULT_DELETED_STATUS = self.check_setting_int('General', 'ep_default_deleted_status',
                                                                6)
        self.DOWNLOAD_URL = self.check_setting_str('General', 'download_url', "")
        self.LOCALHOST_IP = self.check_setting_str('General', 'localhost_ip', '')
        self.CPU_PRESET = self.check_setting_str('General', 'cpu_preset', 'NORMAL')
        self.ANON_REDIRECT = self.check_setting_str('General', 'anon_redirect',
                                                    'http://dereferer.org/?')
        self.PROXY_SETTING = self.check_setting_str('General', 'proxy_setting', '')
        self.PROXY_INDEXERS = bool(self.check_setting_int('General', 'proxy_indexers', 1))
        self.TRASH_REMOVE_SHOW = bool(self.check_setting_int('General', 'trash_remove_show', 0))
        self.TRASH_ROTATE_LOGS = bool(self.check_setting_int('General', 'trash_rotate_logs', 0))
        self.SORT_ARTICLE = bool(self.check_setting_int('General', 'sort_article', 0))
        self.API_KEY = self.check_setting_str('General', 'api_key', '')

        if not self.ENABLE_HTTPS:
            self.ENABLE_HTTPS = bool(self.check_setting_int('General', 'enable_https', 0))

        self.HTTPS_CERT = os.path.abspath(
            os.path.join(sickrage.PROG_DIR, self.check_setting_str('General', 'https_cert', 'server.crt')))
        self.HTTPS_KEY = os.path.abspath(
            os.path.join(sickrage.PROG_DIR, self.check_setting_str('General', 'https_key', 'server.key')))

        self.HANDLE_REVERSE_PROXY = bool(self.check_setting_int('General', 'handle_reverse_proxy', 0))

        self.NEWS_LAST_READ = self.check_setting_str('General', 'news_last_read', '1970-01-01')

        # show settings
        self.ROOT_DIRS = self.check_setting_str('General', 'root_dirs', '')
        self.QUALITY_DEFAULT = self.check_setting_int('General', 'quality_default', SD)
        self.STATUS_DEFAULT = self.check_setting_int('General', 'status_default', SKIPPED)
        self.STATUS_DEFAULT_AFTER = self.check_setting_int('General', 'status_default_after', WANTED)
        self.VERSION_NOTIFY = bool(self.check_setting_int('General', 'version_notify', 1))
        self.AUTO_UPDATE = bool(self.check_setting_int('General', 'auto_update', 0))
        self.NOTIFY_ON_UPDATE = bool(self.check_setting_int('General', 'notify_on_update', 1))
        self.FLATTEN_FOLDERS_DEFAULT = bool(
            self.check_setting_int('General', 'flatten_folders_default', 0))
        self.INDEXER_DEFAULT = self.check_setting_int('General', 'indexer_default', 0)
        self.INDEXER_TIMEOUT = self.check_setting_int('General', 'indexer_timeout', 20)
        self.ANIME_DEFAULT = bool(self.check_setting_int('General', 'anime_default', 0))
        self.SCENE_DEFAULT = bool(self.check_setting_int('General', 'scene_default', 0))
        self.ARCHIVE_DEFAULT = bool(self.check_setting_int('General', 'archive_default', 0))

        # naming settings
        self.NAMING_PATTERN = self.check_setting_str('General', 'naming_pattern',
                                                     'Season %0S/%SN - S%0SE%0E - %EN')
        self.NAMING_ABD_PATTERN = self.check_setting_str('General', 'naming_abd_pattern',
                                                         '%SN - %A.D - %EN')
        self.NAMING_CUSTOM_ABD = bool(self.check_setting_int('General', 'naming_custom_abd', 0))
        self.NAMING_SPORTS_PATTERN = self.check_setting_str('General', 'naming_sports_pattern',
                                                            '%SN - %A-D - %EN')
        self.NAMING_ANIME_PATTERN = self.check_setting_str('General', 'naming_anime_pattern',
                                                           'Season %0S/%SN - S%0SE%0E - %EN')
        self.NAMING_ANIME = self.check_setting_int('General', 'naming_anime', 3)
        self.NAMING_CUSTOM_SPORTS = bool(self.check_setting_int('General', 'naming_custom_sports', 0))
        self.NAMING_CUSTOM_ANIME = bool(self.check_setting_int('General', 'naming_custom_anime', 0))
        self.NAMING_MULTI_EP = self.check_setting_int('General', 'naming_multi_ep', 1)
        self.NAMING_ANIME_MULTI_EP = self.check_setting_int('General', 'naming_anime_multi_ep', 1)
        self.NAMING_STRIP_YEAR = bool(self.check_setting_int('General', 'naming_strip_year', 0))

        # provider settings
        self.USE_NZBS = bool(self.check_setting_int('General', 'use_nzbs', 0))
        self.USE_TORRENTS = bool(self.check_setting_int('General', 'use_torrents', 1))
        self.NZB_METHOD = self.check_setting_str('General', 'nzb_method', 'blackhole')
        self.TORRENT_METHOD = self.check_setting_str('General', 'torrent_method', 'blackhole')
        self.DOWNLOAD_PROPERS = bool(self.check_setting_int('General', 'download_propers', 1))
        self.PROPER_SEARCHER_INTERVAL = self.check_setting_str('General', 'check_propers_interval',
                                                               'daily')
        self.RANDOMIZE_PROVIDERS = bool(self.check_setting_int('General', 'randomize_providers', 0))
        self.ALLOW_HIGH_PRIORITY = bool(self.check_setting_int('General', 'allow_high_priority', 1))
        self.SKIP_REMOVED_FILES = bool(self.check_setting_int('General', 'skip_removed_files', 0))
        self.USENET_RETENTION = self.check_setting_int('General', 'usenet_retention', 500)

        # SCHEDULER.settings
        self.AUTOPOSTPROCESSOR_FREQ = self.check_setting_int(
            'General', 'autopostprocessor_frequency', self.DEFAULT_AUTOPOSTPROCESSOR_FREQ
        )

        self.SUBTITLE_SEARCHER_FREQ = self.check_setting_int(
            'Subtitles', 'subtitles_finder_frequency', self.DEFAULT_SUBTITLE_SEARCHER_FREQ
        )

        self.NAMECACHE_FREQ = self.check_setting_int('General', 'namecache_frequency',
                                                     self.DEFAULT_NAMECACHE_FREQ)
        self.DAILY_SEARCHER_FREQ = self.check_setting_int('General', 'dailysearch_frequency',
                                                          self.DEFAULT_DAILY_SEARCHER_FREQ)
        self.BACKLOG_SEARCHER_FREQ = self.check_setting_int('General', 'backlog_frequency',
                                                            self.DEFAULT_BACKLOG_SEARCHER_FREQ)
        self.VERSION_UPDATER_FREQ = self.check_setting_int('General', 'update_frequency',
                                                           self.DEFAULT_VERSION_UPDATE_FREQ)
        self.SHOWUPDATE_HOUR = self.check_setting_int('General', 'showupdate_hour',
                                                      self.DEFAULT_SHOWUPDATE_HOUR)
        self.BACKLOG_DAYS = self.check_setting_int('General', 'backlog_days', 7)

        self.NZB_DIR = self.check_setting_str('Blackhole', 'nzb_dir', '')
        self.TORRENT_DIR = self.check_setting_str('Blackhole', 'torrent_dir', '')

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

        self.NZBS = bool(self.check_setting_int('NZBs', 'nzbs', 0))
        self.NZBS_UID = self.check_setting_str('NZBs', 'nzbs_uid', '')
        self.NZBS_HASH = self.check_setting_str('NZBs', 'nzbs_hash', '')

        self.NEWZBIN = bool(self.check_setting_int('Newzbin', 'newzbin', 0))
        self.NEWZBIN_USERNAME = self.check_setting_str('Newzbin', 'newzbin_username', '')
        self.NEWZBIN_PASSWORD = self.check_setting_str('Newzbin', 'newzbin_password', '')

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

        self.USE_KODI = bool(self.check_setting_int('KODI', 'use_kodi', 0))
        self.KODI_ALWAYS_ON = bool(self.check_setting_int('KODI', 'kodi_always_on', 1))
        self.KODI_NOTIFY_ONSNATCH = bool(self.check_setting_int('KODI', 'kodi_notify_onsnatch', 0))
        self.KODI_NOTIFY_ONDOWNLOAD = bool(self.check_setting_int('KODI', 'kodi_notify_ondownload', 0))
        self.KODI_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            self.check_setting_int('KODI', 'kodi_notify_onsubtitledownload', 0))
        self.KODI_UPDATE_LIBRARY = bool(self.check_setting_int('KODI', 'kodi_update_library', 0))
        self.KODI_UPDATE_FULL = bool(self.check_setting_int('KODI', 'kodi_update_full', 0))
        self.KODI_UPDATE_ONLYFIRST = bool(self.check_setting_int('KODI', 'kodi_update_onlyfirst', 0))
        self.KODI_HOST = self.check_setting_str('KODI', 'kodi_host', '')
        self.KODI_USERNAME = self.check_setting_str('KODI', 'kodi_username', '')
        self.KODI_PASSWORD = self.check_setting_str('KODI', 'kodi_password', '')

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

        self.USE_EMBY = bool(self.check_setting_int('Emby', 'use_emby', 0))
        self.EMBY_HOST = self.check_setting_str('Emby', 'emby_host', '')
        self.EMBY_APIKEY = self.check_setting_str('Emby', 'emby_apikey', '')

        self.USE_GROWL = bool(self.check_setting_int('Growl', 'use_growl', 0))
        self.GROWL_NOTIFY_ONSNATCH = bool(self.check_setting_int('Growl', 'growl_notify_onsnatch', 0))
        self.GROWL_NOTIFY_ONDOWNLOAD = bool(
            self.check_setting_int('Growl', 'growl_notify_ondownload', 0))
        self.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            self.check_setting_int('Growl', 'growl_notify_onsubtitledownload', 0))
        self.GROWL_HOST = self.check_setting_str('Growl', 'growl_host', '')
        self.GROWL_PASSWORD = self.check_setting_str('Growl', 'growl_password', '')

        self.USE_FREEMOBILE = bool(self.check_setting_int('FreeMobile', 'use_freemobile', 0))
        self.FREEMOBILE_NOTIFY_ONSNATCH = bool(
            self.check_setting_int('FreeMobile', 'freemobile_notify_onsnatch', 0))
        self.FREEMOBILE_NOTIFY_ONDOWNLOAD = bool(
            self.check_setting_int('FreeMobile', 'freemobile_notify_ondownload', 0))
        self.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            self.check_setting_int('FreeMobile', 'freemobile_notify_onsubtitledownload', 0))
        self.FREEMOBILE_ID = self.check_setting_str('FreeMobile', 'freemobile_id', '')
        self.FREEMOBILE_APIKEY = self.check_setting_str('FreeMobile', 'freemobile_apikey', '')

        self.USE_PROWL = bool(self.check_setting_int('Prowl', 'use_prowl', 0))
        self.PROWL_NOTIFY_ONSNATCH = bool(self.check_setting_int('Prowl', 'prowl_notify_onsnatch', 0))
        self.PROWL_NOTIFY_ONDOWNLOAD = bool(
            self.check_setting_int('Prowl', 'prowl_notify_ondownload', 0))
        self.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            self.check_setting_int('Prowl', 'prowl_notify_onsubtitledownload', 0))
        self.PROWL_API = self.check_setting_str('Prowl', 'prowl_api', '')
        self.PROWL_PRIORITY = self.check_setting_str('Prowl', 'prowl_priority', "0")

        self.USE_TWITTER = bool(self.check_setting_int('Twitter', 'use_twitter', 0))
        self.TWITTER_NOTIFY_ONSNATCH = bool(
            self.check_setting_int('Twitter', 'twitter_notify_onsnatch', 0))
        self.TWITTER_NOTIFY_ONDOWNLOAD = bool(
            self.check_setting_int('Twitter', 'twitter_notify_ondownload', 0))
        self.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            self.check_setting_int('Twitter', 'twitter_notify_onsubtitledownload', 0))
        self.TWITTER_USERNAME = self.check_setting_str('Twitter', 'twitter_username', '')
        self.TWITTER_PASSWORD = self.check_setting_str('Twitter', 'twitter_password', '')
        self.TWITTER_PREFIX = self.check_setting_str('Twitter', 'twitter_prefix',
                                                     self.GIT_REPO)
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

        self.USE_TRAKT = bool(self.check_setting_int('Trakt', 'use_trakt', 0))
        self.TRAKT_USERNAME = self.check_setting_str('Trakt', 'trakt_username', '')
        self.TRAKT_ACCESS_TOKEN = self.check_setting_str('Trakt', 'trakt_access_token', '')
        self.TRAKT_REFRESH_TOKEN = self.check_setting_str('Trakt', 'trakt_refresh_token', '')
        self.TRAKT_REMOVE_WATCHLIST = bool(self.check_setting_int('Trakt', 'trakt_remove_watchlist', 0))
        self.TRAKT_REMOVE_SERIESLIST = bool(
            self.check_setting_int('Trakt', 'trakt_remove_serieslist', 0))
        self.TRAKT_REMOVE_SHOW_FROM_SICKRAGE = bool(
            self.check_setting_int('Trakt', 'trakt_remove_show_from_sickrage', 0))
        self.TRAKT_SYNC_WATCHLIST = bool(self.check_setting_int('Trakt', 'trakt_sync_watchlist', 0))
        self.TRAKT_METHOD_ADD = self.check_setting_int('Trakt', 'trakt_method_add', 0)
        self.TRAKT_START_PAUSED = bool(self.check_setting_int('Trakt', 'trakt_start_paused', 0))
        self.TRAKT_USE_RECOMMENDED = bool(self.check_setting_int('Trakt', 'trakt_use_recommended', 0))
        self.TRAKT_SYNC = bool(self.check_setting_int('Trakt', 'trakt_sync', 0))
        self.TRAKT_SYNC_REMOVE = bool(self.check_setting_int('Trakt', 'trakt_sync_remove', 0))
        self.TRAKT_DEFAULT_INDEXER = self.check_setting_int('Trakt', 'trakt_default_indexer', 1)
        self.TRAKT_TIMEOUT = self.check_setting_int('Trakt', 'trakt_timeout', 30)
        self.TRAKT_BLACKLIST_NAME = self.check_setting_str('Trakt', 'trakt_blacklist_name', '')

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

        # self.subtitleself.settings        self.USE_SUBTITLES= bool(self.check_setting_int('Subtitles', 'use_subtitles', 0))
        self.SUBTITLES_LANGUAGES = self.check_setting_str('Subtitles', 'subtitles_languages', '').split(
            ',')
        self.SUBTITLES_DIR = self.check_setting_str('Subtitles', 'subtitles_dir', '')
        self.SUBTITLES_SERVICES_LIST = self.check_setting_str('Subtitles', 'SUBTITLES_SERVICES_LIST',
                                                              '').split(
            ',')
        self.SUBTITLES_DEFAULT = bool(self.check_setting_int('Subtitles', 'subtitles_default', 0))
        self.SUBTITLES_HISTORY = bool(self.check_setting_int('Subtitles', 'subtitles_history', 0))
        self.SUBTITLES_HEARING_IMPAIRED = bool(
            self.check_setting_int('Subtitles', 'subtitles_hearing_impaired', 0))
        self.EMBEDDED_SUBTITLES_ALL = bool(
            self.check_setting_int('Subtitles', 'embedded_subtitles_all', 0))
        self.SUBTITLES_MULTI = bool(self.check_setting_int('Subtitles', 'subtitles_multi', 1))
        self.SUBTITLES_SERVICES_ENABLED = [int(x) for x in
                                           self.check_setting_str('Subtitles', 'SUBTITLES_SERVICES_ENABLED',
                                                                  '').split('|') if x]
        self.SUBTITLES_EXTRA_SCRIPTS = [x.strip() for x in
                                        self.check_setting_str('Subtitles', 'subtitles_extra_scripts',
                                                               '').split('|') if x.strip()]

        self.ADDIC7ED_USER = self.check_setting_str('Subtitles', 'addic7ed_username', '')
        self.ADDIC7ED_PASS = self.check_setting_str('Subtitles', 'addic7ed_password', '')

        self.LEGENDASTV_USER = self.check_setting_str('Subtitles', 'legendastv_username', '')
        self.LEGENDASTV_PASS = self.check_setting_str('Subtitles', 'legendastv_password', '')

        self.OPENSUBTITLES_USER = self.check_setting_str('Subtitles', 'opensubtitles_username', '')
        self.OPENSUBTITLES_PASS = self.check_setting_str('Subtitles', 'opensubtitles_password', '')

        self.USE_FAILED_DOWNLOADS = bool(
            self.check_setting_int('FailedDownloads', 'use_failed_downloads', 0))
        self.DELETE_FAILED = bool(self.check_setting_int('FailedDownloads', 'delete_failed', 0))

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

        self.USE_ANIDB = bool(self.check_setting_int('ANIDB', 'use_anidb', 0))
        self.ANIDB_USERNAME = self.check_setting_str('ANIDB', 'anidb_username', '')
        self.ANIDB_PASSWORD = self.check_setting_str('ANIDB', 'anidb_password', '')
        self.ANIDB_USE_MYLIST = bool(self.check_setting_int('ANIDB', 'anidb_use_mylist', 0))

        self.ANIME_SPLIT_HOME = bool(self.check_setting_int('ANIME', 'anime_split_home', 0))

        self.METADATA_KODI = self.check_setting_str('General', 'metadata_kodi', '0|0|0|0|0|0|0|0|0|0')
        self.METADATA_KODI_12PLUS = self.check_setting_str('General', 'metadata_kodi_12plus',
                                                           '0|0|0|0|0|0|0|0|0|0')
        self.METADATA_MEDIABROWSER = self.check_setting_str('General', 'metadata_mediabrowser',
                                                            '0|0|0|0|0|0|0|0|0|0')
        self.METADATA_PS3 = self.check_setting_str('General', 'metadata_ps3', '0|0|0|0|0|0|0|0|0|0')
        self.METADATA_WDTV = self.check_setting_str('General', 'metadata_wdtv', '0|0|0|0|0|0|0|0|0|0')
        self.METADATA_TIVO = self.check_setting_str('General', 'metadata_tivo', '0|0|0|0|0|0|0|0|0|0')
        self.METADATA_MEDE8ER = self.check_setting_str('General', 'metadata_mede8er',
                                                       '0|0|0|0|0|0|0|0|0|0')

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
        self.TIMEZONE_DISPLAY = self.check_setting_str('GUI', 'timezone_display', 'local')
        self.POSTER_SORTBY = self.check_setting_str('GUI', 'poster_sortby', 'name')
        self.POSTER_SORTDIR = self.check_setting_int('GUI', 'poster_sortdir', 1)
        self.FILTER_ROW = bool(self.check_setting_int('GUI', 'filter_row', 1))
        self.DISPLAY_ALL_SEASONS = bool(self.check_setting_int('General', 'display_all_seasons', 1))

        self.NEWZNAB_DATA = self.check_setting_str('Newznab', 'newznab_data',
                                                   NewznabProvider.getDefaultProviders())
        self.TORRENTRSS_DATA = self.check_setting_str('TorrentRss', 'torrentrss_data',
                                                      TorrentRssProvider.getDefaultProviders())

        # init provider info
        sickrage.srCore.newznabProviderList = NewznabProvider.getProviderList(self.NEWZNAB_DATA)
        sickrage.srCore.torrentRssProviderList = TorrentRssProvider.getProviderList(self.TORRENTRSS_DATA)

        self.PROVIDER_ORDER = self.check_setting_str('General', 'provider_order', '').split()

        # TORRENT PROVIDER SETTINGS
        for providerID, providerObj in sickrage.srCore.providersDict[GenericProvider.TORRENT].items():
            providerObj.enabled = bool(self.check_setting_int(providerID.upper(), providerID, 0))

            if hasattr(providerObj, 'api_key'):
                providerObj.api_key = self.check_setting_str(
                    providerID.upper(), providerID + '_api_key', ''
                )

            if hasattr(providerObj, 'hash'):
                providerObj.hash = self.check_setting_str(
                    providerID.upper(), providerID + '_hash', ''
                )

            if hasattr(providerObj, 'digest'):
                providerObj.digest = self.check_setting_str(
                    providerID.upper(), providerID + '_digest', ''
                )

            if hasattr(providerObj, 'username'):
                providerObj.username = self.check_setting_str(
                    providerID.upper(), providerID + '_username', ''
                )

            if hasattr(providerObj, 'password'):
                providerObj.password = self.check_setting_str(
                    providerID.upper(), providerID + '_password', ''
                )

            if hasattr(providerObj, 'passkey'):
                providerObj.passkey = self.check_setting_str(providerID.upper(),
                                                             providerID + '_passkey', '')
            if hasattr(providerObj, 'pin'):
                providerObj.pin = self.check_setting_str(providerID.upper(),
                                                         providerID + '_pin', '')
            if hasattr(providerObj, 'confirmed'):
                providerObj.confirmed = bool(self.check_setting_int(providerID.upper(),
                                                                    providerID + '_confirmed', 1))
            if hasattr(providerObj, 'ranked'):
                providerObj.ranked = bool(self.check_setting_int(providerID.upper(),
                                                                 providerID + '_ranked', 1))

            if hasattr(providerObj, 'engrelease'):
                providerObj.engrelease = bool(self.check_setting_int(providerID.upper(),
                                                                     providerID + '_engrelease', 0))

            if hasattr(providerObj, 'onlyspasearch'):
                providerObj.onlyspasearch = bool(self.check_setting_int(providerID.upper(),
                                                                        providerID + '_onlyspasearch',
                                                                        0))

            if hasattr(providerObj, 'sorting'):
                providerObj.sorting = self.check_setting_str(providerID.upper(),
                                                             providerID + '_sorting', 'seeders')
            if hasattr(providerObj, 'options'):
                providerObj.options = self.check_setting_str(providerID.upper(),
                                                             providerID + '_options', '')
            if hasattr(providerObj, 'ratio'):
                providerObj.ratio = self.check_setting_str(providerID.upper(),
                                                           providerID + '_ratio', '')
            if hasattr(providerObj, 'minseed'):
                providerObj.minseed = self.check_setting_int(providerID.upper(),
                                                             providerID + '_minseed', 1)
            if hasattr(providerObj, 'minleech'):
                providerObj.minleech = self.check_setting_int(providerID.upper(),
                                                              providerID + '_minleech', 0)
            if hasattr(providerObj, 'freeleech'):
                providerObj.freeleech = bool(self.check_setting_int(providerID.upper(),
                                                                    providerID + '_freeleech', 0))
            if hasattr(providerObj, 'search_mode'):
                providerObj.search_mode = self.check_setting_str(providerID.upper(),
                                                                 providerID + '_search_mode',
                                                                 'eponly')
            if hasattr(providerObj, 'search_fallback'):
                providerObj.search_fallback = bool(self.check_setting_int(providerID.upper(),
                                                                          providerID + '_search_fallback',
                                                                          0))

            if hasattr(providerObj, 'enable_daily'):
                providerObj.enable_daily = bool(self.check_setting_int(providerID.upper(),
                                                                       providerID + '_enable_daily',
                                                                       1))

            if hasattr(providerObj, 'enable_backlog') and hasattr(providerObj, 'supportsBacklog'):
                providerObj.enable_backlog = bool(self.check_setting_int(providerID.upper(),
                                                                         providerID + '_enable_backlog',
                                                                         providerObj.supportsBacklog))

            if hasattr(providerObj, 'cat'):
                providerObj.cat = self.check_setting_int(providerID.upper(),
                                                         providerID + '_cat', 0)
            if hasattr(providerObj, 'subtitle'):
                providerObj.subtitle = bool(self.check_setting_int(providerID.upper(),
                                                                   providerID + '_subtitle', 0))

        # NZB PROVIDER SETTINGS
        for providerID, providerObj in sickrage.srCore.providersDict[GenericProvider.NZB].items():
            providerObj.enabled = bool(
                self.check_setting_int(providerID.upper(), providerID, 0))
            if hasattr(providerObj, 'api_key'):
                providerObj.api_key = self.check_setting_str(providerID.upper(),
                                                             providerID + '_api_key', '')
            if hasattr(providerObj, 'username'):
                providerObj.username = self.check_setting_str(providerID.upper(),
                                                              providerID + '_username', '')
            if hasattr(providerObj, 'search_mode'):
                providerObj.search_mode = self.check_setting_str(providerID.upper(),
                                                                 providerID + '_search_mode',
                                                                 'eponly')
            if hasattr(providerObj, 'search_fallback'):
                providerObj.search_fallback = bool(self.check_setting_int(providerID.upper(),
                                                                          providerID + '_search_fallback',
                                                                          0))
            if hasattr(providerObj, 'enable_daily'):
                providerObj.enable_daily = bool(self.check_setting_int(providerID.upper(),
                                                                       providerID + '_enable_daily',
                                                                       1))

            if hasattr(providerObj, 'enable_backlog') and hasattr(providerObj, 'supportsBacklog'):
                providerObj.enable_backlog = bool(self.check_setting_int(providerID.upper(),
                                                                         providerID + '_enable_backlog',
                                                                         providerObj.supportsBacklog))

        return self.save_config()

    def save_config(self):
        sickrage.srLogger.debug("Saving settings to disk")

        new_config = ConfigObj(self.CONFIG_OBJ.filename)

        # For passwords you must include the word `password` in the item_name and add `helpers.encrypt(ITEM_NAME, ENCRYPTION_VERSION)` in save_config()
        new_config[b'General'] = {}
        new_config[b'General'][b'git_autoissues'] = int(self.GIT_AUTOISSUES)
        new_config[b'General'][b'git_username'] = self.GIT_USERNAME
        new_config[b'General'][b'git_password'] = encrypt(self.GIT_PASSWORD, self.ENCRYPTION_VERSION)
        new_config[b'General'][b'git_reset'] = int(self.GIT_RESET)
        new_config[b'General'][b'git_remote'] = self.GIT_REMOTE
        new_config[b'General'][b'git_remote_url'] = self.GIT_REMOTE_URL
        new_config[b'General'][b'git_newver'] = int(self.GIT_NEWVER)
        new_config[b'General'][b'config_version'] = self.CONFIG_VERSION
        new_config[b'General'][b'encryption_version'] = int(self.ENCRYPTION_VERSION)
        new_config[b'General'][b'encryption_secret'] = self.ENCRYPTION_SECRET
        new_config[b'General'][b'log_dir'] = os.path.abspath(
            os.path.join(sickrage.DATA_DIR, self.LOG_DIR or 'Logs'))
        new_config[b'General'][b'log_nr'] = int(self.LOG_NR)
        new_config[b'General'][b'log_size'] = int(self.LOG_SIZE)
        new_config[b'General'][b'socket_timeout'] = self.SOCKET_TIMEOUT
        new_config[b'General'][b'web_port'] = self.WEB_PORT
        new_config[b'General'][b'web_host'] = self.WEB_HOST
        new_config[b'General'][b'web_ipv6'] = int(self.WEB_IPV6)
        new_config[b'General'][b'web_log'] = int(self.WEB_LOG)
        new_config[b'General'][b'web_root'] = self.WEB_ROOT
        new_config[b'General'][b'web_username'] = self.WEB_USERNAME
        new_config[b'General'][b'web_password'] = encrypt(self.WEB_PASSWORD, self.ENCRYPTION_VERSION)
        new_config[b'General'][b'web_cookie_secret'] = self.WEB_COOKIE_SECRET
        new_config[b'General'][b'web_use_gzip'] = int(self.WEB_USE_GZIP)
        new_config[b'General'][b'ssl_verify'] = int(self.SSL_VERIFY)
        new_config[b'General'][b'download_url'] = self.DOWNLOAD_URL
        new_config[b'General'][b'localhost_ip'] = self.LOCALHOST_IP
        new_config[b'General'][b'cpu_preset'] = self.CPU_PRESET
        new_config[b'General'][b'anon_redirect'] = self.ANON_REDIRECT
        new_config[b'General'][b'api_key'] = self.API_KEY
        new_config[b'General'][b'debug'] = int(self.DEBUG)
        new_config[b'General'][b'default_page'] = self.DEFAULT_PAGE
        new_config[b'General'][b'enable_https'] = int(self.ENABLE_HTTPS)
        new_config[b'General'][b'https_cert'] = self.HTTPS_CERT
        new_config[b'General'][b'https_key'] = self.HTTPS_KEY
        new_config[b'General'][b'handle_reverse_proxy'] = int(self.HANDLE_REVERSE_PROXY)
        new_config[b'General'][b'use_nzbs'] = int(self.USE_NZBS)
        new_config[b'General'][b'use_torrents'] = int(self.USE_TORRENTS)
        new_config[b'General'][b'nzb_method'] = self.NZB_METHOD
        new_config[b'General'][b'torrent_method'] = self.TORRENT_METHOD
        new_config[b'General'][b'usenet_retention'] = int(self.USENET_RETENTION)
        new_config[b'General'][b'autopostprocessor_frequency'] = int(self.AUTOPOSTPROCESSOR_FREQ)
        new_config[b'General'][b'dailysearch_frequency'] = int(self.DAILY_SEARCHER_FREQ)
        new_config[b'General'][b'backlog_frequency'] = int(self.BACKLOG_SEARCHER_FREQ)
        new_config[b'General'][b'update_frequency'] = int(self.VERSION_UPDATER_FREQ)
        new_config[b'General'][b'showupdate_hour'] = int(self.SHOWUPDATE_HOUR)
        new_config[b'General'][b'download_propers'] = int(self.DOWNLOAD_PROPERS)
        new_config[b'General'][b'randomize_providers'] = int(self.RANDOMIZE_PROVIDERS)
        new_config[b'General'][b'check_propers_interval'] = self.PROPER_SEARCHER_INTERVAL
        new_config[b'General'][b'allow_high_priority'] = int(self.ALLOW_HIGH_PRIORITY)
        new_config[b'General'][b'skip_removed_files'] = int(self.SKIP_REMOVED_FILES)
        new_config[b'General'][b'quality_default'] = int(self.QUALITY_DEFAULT)
        new_config[b'General'][b'status_default'] = int(self.STATUS_DEFAULT)
        new_config[b'General'][b'status_default_after'] = int(self.STATUS_DEFAULT_AFTER)
        new_config[b'General'][b'flatten_folders_default'] = int(self.FLATTEN_FOLDERS_DEFAULT)
        new_config[b'General'][b'indexer_default'] = int(self.INDEXER_DEFAULT)
        new_config[b'General'][b'indexer_timeout'] = int(self.INDEXER_TIMEOUT)
        new_config[b'General'][b'anime_default'] = int(self.ANIME_DEFAULT)
        new_config[b'General'][b'scene_default'] = int(self.SCENE_DEFAULT)
        new_config[b'General'][b'archive_default'] = int(self.ARCHIVE_DEFAULT)
        new_config[b'General'][b'provider_order'] = ' '.join(self.PROVIDER_ORDER)
        new_config[b'General'][b'version_notify'] = int(self.VERSION_NOTIFY)
        new_config[b'General'][b'auto_update'] = int(self.AUTO_UPDATE)
        new_config[b'General'][b'notify_on_update'] = int(self.NOTIFY_ON_UPDATE)
        new_config[b'General'][b'naming_strip_year'] = int(self.NAMING_STRIP_YEAR)
        new_config[b'General'][b'naming_pattern'] = self.NAMING_PATTERN
        new_config[b'General'][b'naming_custom_abd'] = int(self.NAMING_CUSTOM_ABD)
        new_config[b'General'][b'naming_abd_pattern'] = self.NAMING_ABD_PATTERN
        new_config[b'General'][b'naming_custom_sports'] = int(self.NAMING_CUSTOM_SPORTS)
        new_config[b'General'][b'naming_sports_pattern'] = self.NAMING_SPORTS_PATTERN
        new_config[b'General'][b'naming_custom_anime'] = int(self.NAMING_CUSTOM_ANIME)
        new_config[b'General'][b'naming_anime_pattern'] = self.NAMING_ANIME_PATTERN
        new_config[b'General'][b'naming_multi_ep'] = int(self.NAMING_MULTI_EP)
        new_config[b'General'][b'naming_anime_multi_ep'] = int(self.NAMING_ANIME_MULTI_EP)
        new_config[b'General'][b'naming_anime'] = int(self.NAMING_ANIME)
        new_config[b'General'][b'indexerDefaultLang'] = self.INDEXER_DEFAULT_LANGUAGE
        new_config[b'General'][b'ep_default_deleted_status'] = int(self.EP_DEFAULT_DELETED_STATUS)
        new_config[b'General'][b'launch_browser'] = int(self.LAUNCH_BROWSER)
        new_config[b'General'][b'trash_remove_show'] = int(self.TRASH_REMOVE_SHOW)
        new_config[b'General'][b'trash_rotate_logs'] = int(self.TRASH_ROTATE_LOGS)
        new_config[b'General'][b'sort_article'] = int(self.SORT_ARTICLE)
        new_config[b'General'][b'proxy_setting'] = self.PROXY_SETTING
        new_config[b'General'][b'proxy_indexers'] = int(self.PROXY_INDEXERS)

        new_config[b'General'][b'use_listview'] = int(self.USE_LISTVIEW)
        new_config[b'General'][b'metadata_kodi'] = self.METADATA_KODI
        new_config[b'General'][b'metadata_kodi_12plus'] = self.METADATA_KODI_12PLUS
        new_config[b'General'][b'metadata_mediabrowser'] = self.METADATA_MEDIABROWSER
        new_config[b'General'][b'metadata_ps3'] = self.METADATA_PS3
        new_config[b'General'][b'metadata_wdtv'] = self.METADATA_WDTV
        new_config[b'General'][b'metadata_tivo'] = self.METADATA_TIVO
        new_config[b'General'][b'metadata_mede8er'] = self.METADATA_MEDE8ER

        new_config[b'General'][b'backlog_days'] = int(self.BACKLOG_DAYS)

        new_config[b'General'][b'cache_dir'] = self.CACHE_DIR or 'cache'
        new_config[b'General'][b'root_dirs'] = self.ROOT_DIRS or ''
        new_config[b'General'][b'tv_download_dir'] = self.TV_DOWNLOAD_DIR
        new_config[b'General'][b'keep_processed_dir'] = int(self.KEEP_PROCESSED_DIR)
        new_config[b'General'][b'process_method'] = self.PROCESS_METHOD
        new_config[b'General'][b'del_rar_contents'] = int(self.DELRARCONTENTS)
        new_config[b'General'][b'move_associated_files'] = int(self.MOVE_ASSOCIATED_FILES)
        new_config[b'General'][b'sync_files'] = self.SYNC_FILES
        new_config[b'General'][b'postpone_if_sync_files'] = int(self.POSTPONE_IF_SYNC_FILES)
        new_config[b'General'][b'nfo_rename'] = int(self.NFO_RENAME)
        new_config[b'General'][b'process_automatically'] = int(self.PROCESS_AUTOMATICALLY)
        new_config[b'General'][b'no_delete'] = int(self.NO_DELETE)
        new_config[b'General'][b'unpack'] = int(self.UNPACK)
        new_config[b'General'][b'rename_episodes'] = int(self.RENAME_EPISODES)
        new_config[b'General'][b'airdate_episodes'] = int(self.AIRDATE_EPISODES)
        new_config[b'General'][b'file_timestamp_timezone'] = self.FILE_TIMESTAMP_TIMEZONE
        new_config[b'General'][b'create_missing_show_dirs'] = int(self.CREATE_MISSING_SHOW_DIRS)
        new_config[b'General'][b'add_shows_wo_dir'] = int(self.ADD_SHOWS_WO_DIR)

        new_config[b'General'][b'extra_scripts'] = '|'.join(self.EXTRA_SCRIPTS)
        new_config[b'General'][b'git_path'] = self.GIT_PATH
        new_config[b'General'][b'ignore_words'] = self.IGNORE_WORDS
        new_config[b'General'][b'require_words'] = self.REQUIRE_WORDS
        new_config[b'General'][b'ignored_subs_list'] = self.IGNORED_SUBS_LIST
        new_config[b'General'][b'calendar_unprotected'] = int(self.CALENDAR_UNPROTECTED)
        new_config[b'General'][b'calendar_icons'] = int(self.CALENDAR_ICONS)
        new_config[b'General'][b'no_restart'] = int(self.NO_RESTART)
        new_config[b'General'][b'developer'] = int(self.DEVELOPER)
        new_config[b'General'][b'display_all_seasons'] = int(self.DISPLAY_ALL_SEASONS)
        new_config[b'General'][b'news_last_read'] = self.NEWS_LAST_READ

        new_config[b'Blackhole'] = {}
        new_config[b'Blackhole'][b'nzb_dir'] = self.NZB_DIR
        new_config[b'Blackhole'][b'torrent_dir'] = self.TORRENT_DIR

        new_config[b'NZBs'] = {}
        new_config[b'NZBs'][b'nzbs'] = int(self.NZBS)
        new_config[b'NZBs'][b'nzbs_uid'] = self.NZBS_UID
        new_config[b'NZBs'][b'nzbs_hash'] = self.NZBS_HASH

        new_config[b'Newzbin'] = {}
        new_config[b'Newzbin'][b'newzbin'] = int(self.NEWZBIN)
        new_config[b'Newzbin'][b'newzbin_username'] = self.NEWZBIN_USERNAME
        new_config[b'Newzbin'][b'newzbin_password'] = encrypt(self.NEWZBIN_PASSWORD,
                                                              self.ENCRYPTION_VERSION)

        new_config[b'SABnzbd'] = {}
        new_config[b'SABnzbd'][b'sab_username'] = self.SAB_USERNAME
        new_config[b'SABnzbd'][b'sab_password'] = encrypt(self.SAB_PASSWORD, self.ENCRYPTION_VERSION)
        new_config[b'SABnzbd'][b'sab_apikey'] = self.SAB_APIKEY
        new_config[b'SABnzbd'][b'sab_category'] = self.SAB_CATEGORY
        new_config[b'SABnzbd'][b'sab_category_backlog'] = self.SAB_CATEGORY_BACKLOG
        new_config[b'SABnzbd'][b'sab_category_anime'] = self.SAB_CATEGORY_ANIME
        new_config[b'SABnzbd'][b'sab_category_anime_backlog'] = self.SAB_CATEGORY_ANIME_BACKLOG
        new_config[b'SABnzbd'][b'sab_host'] = self.SAB_HOST
        new_config[b'SABnzbd'][b'sab_forced'] = int(self.SAB_FORCED)

        new_config[b'NZBget'] = {}

        new_config[b'NZBget'][b'nzbget_username'] = self.NZBGET_USERNAME
        new_config[b'NZBget'][b'nzbget_password'] = encrypt(self.NZBGET_PASSWORD,
                                                            self.ENCRYPTION_VERSION)
        new_config[b'NZBget'][b'nzbget_category'] = self.NZBGET_CATEGORY
        new_config[b'NZBget'][b'nzbget_category_backlog'] = self.NZBGET_CATEGORY_BACKLOG
        new_config[b'NZBget'][b'nzbget_category_anime'] = self.NZBGET_CATEGORY_ANIME
        new_config[b'NZBget'][b'nzbget_category_anime_backlog'] = self.NZBGET_CATEGORY_ANIME_BACKLOG
        new_config[b'NZBget'][b'nzbget_host'] = self.NZBGET_HOST
        new_config[b'NZBget'][b'nzbget_use_https'] = int(self.NZBGET_USE_HTTPS)
        new_config[b'NZBget'][b'nzbget_priority'] = self.NZBGET_PRIORITY

        new_config[b'TORRENT'] = {}
        new_config[b'TORRENT'][b'torrent_username'] = self.TORRENT_USERNAME
        new_config[b'TORRENT'][b'torrent_password'] = encrypt(self.TORRENT_PASSWORD,
                                                              self.ENCRYPTION_VERSION)
        new_config[b'TORRENT'][b'torrent_host'] = self.TORRENT_HOST
        new_config[b'TORRENT'][b'torrent_path'] = self.TORRENT_PATH
        new_config[b'TORRENT'][b'torrent_seed_time'] = int(self.TORRENT_SEED_TIME)
        new_config[b'TORRENT'][b'torrent_paused'] = int(self.TORRENT_PAUSED)
        new_config[b'TORRENT'][b'torrent_high_bandwidth'] = int(self.TORRENT_HIGH_BANDWIDTH)
        new_config[b'TORRENT'][b'torrent_label'] = self.TORRENT_LABEL
        new_config[b'TORRENT'][b'torrent_label_anime'] = self.TORRENT_LABEL_ANIME
        new_config[b'TORRENT'][b'torrent_verify_cert'] = int(self.TORRENT_VERIFY_CERT)
        new_config[b'TORRENT'][b'torrent_rpcurl'] = self.TORRENT_RPCURL
        new_config[b'TORRENT'][b'torrent_auth_type'] = self.TORRENT_AUTH_TYPE

        new_config[b'KODI'] = {}
        new_config[b'KODI'][b'use_kodi'] = int(self.USE_KODI)
        new_config[b'KODI'][b'kodi_always_on'] = int(self.KODI_ALWAYS_ON)
        new_config[b'KODI'][b'kodi_notify_onsnatch'] = int(self.KODI_NOTIFY_ONSNATCH)
        new_config[b'KODI'][b'kodi_notify_ondownload'] = int(self.KODI_NOTIFY_ONDOWNLOAD)
        new_config[b'KODI'][b'kodi_notify_onsubtitledownload'] = int(self.KODI_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'KODI'][b'kodi_update_library'] = int(self.KODI_UPDATE_LIBRARY)
        new_config[b'KODI'][b'kodi_update_full'] = int(self.KODI_UPDATE_FULL)
        new_config[b'KODI'][b'kodi_update_onlyfirst'] = int(self.KODI_UPDATE_ONLYFIRST)
        new_config[b'KODI'][b'kodi_host'] = self.KODI_HOST
        new_config[b'KODI'][b'kodi_username'] = self.KODI_USERNAME
        new_config[b'KODI'][b'kodi_password'] = encrypt(self.KODI_PASSWORD, self.ENCRYPTION_VERSION)

        new_config[b'Plex'] = {}
        new_config[b'Plex'][b'use_plex'] = int(self.USE_PLEX)
        new_config[b'Plex'][b'plex_notify_onsnatch'] = int(self.PLEX_NOTIFY_ONSNATCH)
        new_config[b'Plex'][b'plex_notify_ondownload'] = int(self.PLEX_NOTIFY_ONDOWNLOAD)
        new_config[b'Plex'][b'plex_notify_onsubtitledownload'] = int(self.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'Plex'][b'plex_update_library'] = int(self.PLEX_UPDATE_LIBRARY)
        new_config[b'Plex'][b'plex_server_host'] = self.PLEX_SERVER_HOST
        new_config[b'Plex'][b'plex_server_token'] = self.PLEX_SERVER_TOKEN
        new_config[b'Plex'][b'plex_host'] = self.PLEX_HOST
        new_config[b'Plex'][b'plex_username'] = self.PLEX_USERNAME
        new_config[b'Plex'][b'plex_password'] = encrypt(self.PLEX_PASSWORD, self.ENCRYPTION_VERSION)

        new_config[b'Emby'] = {}
        new_config[b'Emby'][b'use_emby'] = int(self.USE_EMBY)
        new_config[b'Emby'][b'emby_host'] = self.EMBY_HOST
        new_config[b'Emby'][b'emby_apikey'] = self.EMBY_APIKEY

        new_config[b'Growl'] = {}
        new_config[b'Growl'][b'use_growl'] = int(self.USE_GROWL)
        new_config[b'Growl'][b'growl_notify_onsnatch'] = int(self.GROWL_NOTIFY_ONSNATCH)
        new_config[b'Growl'][b'growl_notify_ondownload'] = int(self.GROWL_NOTIFY_ONDOWNLOAD)
        new_config[b'Growl'][b'growl_notify_onsubtitledownload'] = int(self.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'Growl'][b'growl_host'] = self.GROWL_HOST
        new_config[b'Growl'][b'growl_password'] = encrypt(self.GROWL_PASSWORD,
                                                          self.ENCRYPTION_VERSION)

        new_config[b'FreeMobile'] = {}
        new_config[b'FreeMobile'][b'use_freemobile'] = int(self.USE_FREEMOBILE)
        new_config[b'FreeMobile'][b'freemobile_notify_onsnatch'] = int(self.FREEMOBILE_NOTIFY_ONSNATCH)
        new_config[b'FreeMobile'][b'freemobile_notify_ondownload'] = int(self.FREEMOBILE_NOTIFY_ONDOWNLOAD)
        new_config[b'FreeMobile'][b'freemobile_notify_onsubtitledownload'] = int(
            self.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'FreeMobile'][b'freemobile_id'] = self.FREEMOBILE_ID
        new_config[b'FreeMobile'][b'freemobile_apikey'] = self.FREEMOBILE_APIKEY

        new_config[b'Prowl'] = {}
        new_config[b'Prowl'][b'use_prowl'] = int(self.USE_PROWL)
        new_config[b'Prowl'][b'prowl_notify_onsnatch'] = int(self.PROWL_NOTIFY_ONSNATCH)
        new_config[b'Prowl'][b'prowl_notify_ondownload'] = int(self.PROWL_NOTIFY_ONDOWNLOAD)
        new_config[b'Prowl'][b'prowl_notify_onsubtitledownload'] = int(self.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'Prowl'][b'prowl_api'] = self.PROWL_API
        new_config[b'Prowl'][b'prowl_priority'] = self.PROWL_PRIORITY

        new_config[b'Twitter'] = {}
        new_config[b'Twitter'][b'use_twitter'] = int(self.USE_TWITTER)
        new_config[b'Twitter'][b'twitter_notify_onsnatch'] = int(self.TWITTER_NOTIFY_ONSNATCH)
        new_config[b'Twitter'][b'twitter_notify_ondownload'] = int(self.TWITTER_NOTIFY_ONDOWNLOAD)
        new_config[b'Twitter'][b'twitter_notify_onsubtitledownload'] = int(
            self.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'Twitter'][b'twitter_username'] = self.TWITTER_USERNAME
        new_config[b'Twitter'][b'twitter_password'] = encrypt(self.TWITTER_PASSWORD,
                                                              self.ENCRYPTION_VERSION)
        new_config[b'Twitter'][b'twitter_prefix'] = self.TWITTER_PREFIX
        new_config[b'Twitter'][b'twitter_dmto'] = self.TWITTER_DMTO
        new_config[b'Twitter'][b'twitter_usedm'] = int(self.TWITTER_USEDM)

        new_config[b'Boxcar'] = {}
        new_config[b'Boxcar'][b'use_boxcar'] = int(self.USE_BOXCAR)
        new_config[b'Boxcar'][b'boxcar_notify_onsnatch'] = int(self.BOXCAR_NOTIFY_ONSNATCH)
        new_config[b'Boxcar'][b'boxcar_notify_ondownload'] = int(self.BOXCAR_NOTIFY_ONDOWNLOAD)
        new_config[b'Boxcar'][b'boxcar_notify_onsubtitledownload'] = int(self.BOXCAR_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'Boxcar'][b'boxcar_username'] = self.BOXCAR_USERNAME

        new_config[b'Boxcar2'] = {}
        new_config[b'Boxcar2'][b'use_boxcar2'] = int(self.USE_BOXCAR2)
        new_config[b'Boxcar2'][b'boxcar2_notify_onsnatch'] = int(self.BOXCAR2_NOTIFY_ONSNATCH)
        new_config[b'Boxcar2'][b'boxcar2_notify_ondownload'] = int(self.BOXCAR2_NOTIFY_ONDOWNLOAD)
        new_config[b'Boxcar2'][b'boxcar2_notify_onsubtitledownload'] = int(
            self.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'Boxcar2'][b'boxcar2_accesstoken'] = self.BOXCAR2_ACCESSTOKEN

        new_config[b'Pushover'] = {}
        new_config[b'Pushover'][b'use_pushover'] = int(self.USE_PUSHOVER)
        new_config[b'Pushover'][b'pushover_notify_onsnatch'] = int(self.PUSHOVER_NOTIFY_ONSNATCH)
        new_config[b'Pushover'][b'pushover_notify_ondownload'] = int(self.PUSHOVER_NOTIFY_ONDOWNLOAD)
        new_config[b'Pushover'][b'pushover_notify_onsubtitledownload'] = int(
            self.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'Pushover'][b'pushover_userkey'] = self.PUSHOVER_USERKEY
        new_config[b'Pushover'][b'pushover_apikey'] = self.PUSHOVER_APIKEY
        new_config[b'Pushover'][b'pushover_device'] = self.PUSHOVER_DEVICE
        new_config[b'Pushover'][b'pushover_sound'] = self.PUSHOVER_SOUND

        new_config[b'Libnotify'] = {}
        new_config[b'Libnotify'][b'use_libnotify'] = int(self.USE_LIBNOTIFY)
        new_config[b'Libnotify'][b'libnotify_notify_onsnatch'] = int(self.LIBNOTIFY_NOTIFY_ONSNATCH)
        new_config[b'Libnotify'][b'libnotify_notify_ondownload'] = int(self.LIBNOTIFY_NOTIFY_ONDOWNLOAD)
        new_config[b'Libnotify'][b'libnotify_notify_onsubtitledownload'] = int(
            self.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD)

        new_config[b'NMJ'] = {}
        new_config[b'NMJ'][b'use_nmj'] = int(self.USE_NMJ)
        new_config[b'NMJ'][b'nmj_host'] = self.NMJ_HOST
        new_config[b'NMJ'][b'nmj_database'] = self.NMJ_DATABASE
        new_config[b'NMJ'][b'nmj_mount'] = self.NMJ_MOUNT

        new_config[b'NMJv2'] = {}
        new_config[b'NMJv2'][b'use_nmjv2'] = int(self.USE_NMJv2)
        new_config[b'NMJv2'][b'nmjv2_host'] = self.NMJv2_HOST
        new_config[b'NMJv2'][b'nmjv2_database'] = self.NMJv2_DATABASE
        new_config[b'NMJv2'][b'nmjv2_dbloc'] = self.NMJv2_DBLOC

        new_config[b'Synology'] = {}
        new_config[b'Synology'][b'use_synoindex'] = int(self.USE_SYNOINDEX)

        new_config[b'SynologyNotifier'] = {}
        new_config[b'SynologyNotifier'][b'use_synologynotifier'] = int(self.USE_SYNOLOGYNOTIFIER)
        new_config[b'SynologyNotifier'][b'synologynotifier_notify_onsnatch'] = int(
            self.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH)
        new_config[b'SynologyNotifier'][b'synologynotifier_notify_ondownload'] = int(
            self.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD)
        new_config[b'SynologyNotifier'][b'synologynotifier_notify_onsubtitledownload'] = int(
            self.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD)

        new_config[b'theTVDB'] = {}
        new_config[b'theTVDB'][b'thetvdb_apitoken'] = self.THETVDB_APITOKEN

        new_config[b'Trakt'] = {}
        new_config[b'Trakt'][b'use_trakt'] = int(self.USE_TRAKT)
        new_config[b'Trakt'][b'trakt_username'] = self.TRAKT_USERNAME
        new_config[b'Trakt'][b'trakt_access_token'] = self.TRAKT_ACCESS_TOKEN
        new_config[b'Trakt'][b'trakt_refresh_token'] = self.TRAKT_REFRESH_TOKEN
        new_config[b'Trakt'][b'trakt_remove_watchlist'] = int(self.TRAKT_REMOVE_WATCHLIST)
        new_config[b'Trakt'][b'trakt_remove_serieslist'] = int(self.TRAKT_REMOVE_SERIESLIST)
        new_config[b'Trakt'][b'trakt_remove_show_from_sickrage'] = int(self.TRAKT_REMOVE_SHOW_FROM_SICKRAGE)
        new_config[b'Trakt'][b'trakt_sync_watchlist'] = int(self.TRAKT_SYNC_WATCHLIST)
        new_config[b'Trakt'][b'trakt_method_add'] = int(self.TRAKT_METHOD_ADD)
        new_config[b'Trakt'][b'trakt_start_paused'] = int(self.TRAKT_START_PAUSED)
        new_config[b'Trakt'][b'trakt_use_recommended'] = int(self.TRAKT_USE_RECOMMENDED)
        new_config[b'Trakt'][b'trakt_sync'] = int(self.TRAKT_SYNC)
        new_config[b'Trakt'][b'trakt_sync_remove'] = int(self.TRAKT_SYNC_REMOVE)
        new_config[b'Trakt'][b'trakt_default_indexer'] = int(self.TRAKT_DEFAULT_INDEXER)
        new_config[b'Trakt'][b'trakt_timeout'] = int(self.TRAKT_TIMEOUT)
        new_config[b'Trakt'][b'trakt_blacklist_name'] = self.TRAKT_BLACKLIST_NAME

        new_config[b'pyTivo'] = {}
        new_config[b'pyTivo'][b'use_pytivo'] = int(self.USE_PYTIVO)
        new_config[b'pyTivo'][b'pytivo_notify_onsnatch'] = int(self.PYTIVO_NOTIFY_ONSNATCH)
        new_config[b'pyTivo'][b'pytivo_notify_ondownload'] = int(self.PYTIVO_NOTIFY_ONDOWNLOAD)
        new_config[b'pyTivo'][b'pytivo_notify_onsubtitledownload'] = int(self.PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'pyTivo'][b'pyTivo_update_library'] = int(self.PYTIVO_UPDATE_LIBRARY)
        new_config[b'pyTivo'][b'pytivo_host'] = self.PYTIVO_HOST
        new_config[b'pyTivo'][b'pytivo_share_name'] = self.PYTIVO_SHARE_NAME
        new_config[b'pyTivo'][b'pytivo_tivo_name'] = self.PYTIVO_TIVO_NAME

        new_config[b'NMA'] = {}
        new_config[b'NMA'][b'use_nma'] = int(self.USE_NMA)
        new_config[b'NMA'][b'nma_notify_onsnatch'] = int(self.NMA_NOTIFY_ONSNATCH)
        new_config[b'NMA'][b'nma_notify_ondownload'] = int(self.NMA_NOTIFY_ONDOWNLOAD)
        new_config[b'NMA'][b'nma_notify_onsubtitledownload'] = int(self.NMA_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'NMA'][b'nma_api'] = self.NMA_API
        new_config[b'NMA'][b'nma_priority'] = self.NMA_PRIORITY

        new_config[b'Pushalot'] = {}
        new_config[b'Pushalot'][b'use_pushalot'] = int(self.USE_PUSHALOT)
        new_config[b'Pushalot'][b'pushalot_notify_onsnatch'] = int(self.PUSHALOT_NOTIFY_ONSNATCH)
        new_config[b'Pushalot'][b'pushalot_notify_ondownload'] = int(self.PUSHALOT_NOTIFY_ONDOWNLOAD)
        new_config[b'Pushalot'][b'pushalot_notify_onsubtitledownload'] = int(
            self.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'Pushalot'][b'pushalot_authorizationtoken'] = self.PUSHALOT_AUTHORIZATIONTOKEN

        new_config[b'Pushbullet'] = {}
        new_config[b'Pushbullet'][b'use_pushbullet'] = int(self.USE_PUSHBULLET)
        new_config[b'Pushbullet'][b'pushbullet_notify_onsnatch'] = int(self.PUSHBULLET_NOTIFY_ONSNATCH)
        new_config[b'Pushbullet'][b'pushbullet_notify_ondownload'] = int(self.PUSHBULLET_NOTIFY_ONDOWNLOAD)
        new_config[b'Pushbullet'][b'pushbullet_notify_onsubtitledownload'] = int(
            self.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'Pushbullet'][b'pushbullet_api'] = self.PUSHBULLET_API
        new_config[b'Pushbullet'][b'pushbullet_device'] = self.PUSHBULLET_DEVICE

        new_config[b'Email'] = {}
        new_config[b'Email'][b'use_email'] = int(self.USE_EMAIL)
        new_config[b'Email'][b'email_notify_onsnatch'] = int(self.EMAIL_NOTIFY_ONSNATCH)
        new_config[b'Email'][b'email_notify_ondownload'] = int(self.EMAIL_NOTIFY_ONDOWNLOAD)
        new_config[b'Email'][b'email_notify_onsubtitledownload'] = int(self.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD)
        new_config[b'Email'][b'email_host'] = self.EMAIL_HOST
        new_config[b'Email'][b'email_port'] = int(self.EMAIL_PORT)
        new_config[b'Email'][b'email_tls'] = int(self.EMAIL_TLS)
        new_config[b'Email'][b'email_user'] = self.EMAIL_USER
        new_config[b'Email'][b'email_password'] = encrypt(self.EMAIL_PASSWORD,
                                                          self.ENCRYPTION_VERSION)
        new_config[b'Email'][b'email_from'] = self.EMAIL_FROM
        new_config[b'Email'][b'email_list'] = self.EMAIL_LIST

        new_config[b'Newznab'] = {}
        new_config[b'Newznab'][b'newznab_data'] = self.NEWZNAB_DATA

        new_config[b'TorrentRss'] = {}
        new_config[b'TorrentRss'][b'torrentrss_data'] = '!!!'.join(
            [x.configStr() for x in sickrage.srCore.torrentRssProviderList])

        new_config[b'GUI'] = {}
        new_config[b'GUI'][b'gui_name'] = self.GUI_NAME
        new_config[b'GUI'][b'theme_name'] = self.THEME_NAME
        new_config[b'GUI'][b'home_layout'] = self.HOME_LAYOUT
        new_config[b'GUI'][b'history_layout'] = self.HISTORY_LAYOUT
        new_config[b'GUI'][b'history_limit'] = self.HISTORY_LIMIT
        new_config[b'GUI'][b'display_show_specials'] = int(self.DISPLAY_SHOW_SPECIALS)
        new_config[b'GUI'][b'coming_eps_layout'] = self.COMING_EPS_LAYOUT
        new_config[b'GUI'][b'coming_eps_display_paused'] = int(self.COMING_EPS_DISPLAY_PAUSED)
        new_config[b'GUI'][b'coming_eps_sort'] = self.COMING_EPS_SORT
        new_config[b'GUI'][b'coming_eps_missed_range'] = int(self.COMING_EPS_MISSED_RANGE)
        new_config[b'GUI'][b'fuzzy_dating'] = int(self.FUZZY_DATING)
        new_config[b'GUI'][b'trim_zero'] = int(self.TRIM_ZERO)
        new_config[b'GUI'][b'date_preset'] = self.DATE_PRESET
        new_config[b'GUI'][b'time_preset'] = self.TIME_PRESET_W_SECONDS
        new_config[b'GUI'][b'timezone_display'] = self.TIMEZONE_DISPLAY
        new_config[b'GUI'][b'poster_sortby'] = self.POSTER_SORTBY
        new_config[b'GUI'][b'poster_sortdir'] = self.POSTER_SORTDIR
        new_config[b'GUI'][b'filter_row'] = int(self.FILTER_ROW)

        new_config[b'Subtitles'] = {}
        new_config[b'Subtitles'][b'use_subtitles'] = int(self.USE_SUBTITLES)
        new_config[b'Subtitles'][b'subtitles_languages'] = ','.join(self.SUBTITLES_LANGUAGES)
        new_config[b'Subtitles'][b'SUBTITLES_SERVICES_LIST'] = ','.join(self.SUBTITLES_SERVICES_LIST)
        new_config[b'Subtitles'][b'SUBTITLES_SERVICES_ENABLED'] = '|'.join(
            [str(x) for x in self.SUBTITLES_SERVICES_ENABLED])
        new_config[b'Subtitles'][b'subtitles_dir'] = self.SUBTITLES_DIR
        new_config[b'Subtitles'][b'subtitles_default'] = int(self.SUBTITLES_DEFAULT)
        new_config[b'Subtitles'][b'subtitles_history'] = int(self.SUBTITLES_HISTORY)
        new_config[b'Subtitles'][b'embedded_subtitles_all'] = int(self.EMBEDDED_SUBTITLES_ALL)
        new_config[b'Subtitles'][b'subtitles_hearing_impaired'] = int(self.SUBTITLES_HEARING_IMPAIRED)
        new_config[b'Subtitles'][b'subtitles_finder_frequency'] = int(self.SUBTITLE_SEARCHER_FREQ)
        new_config[b'Subtitles'][b'subtitles_multi'] = int(self.SUBTITLES_MULTI)
        new_config[b'Subtitles'][b'subtitles_extra_scripts'] = '|'.join(self.SUBTITLES_EXTRA_SCRIPTS)

        new_config[b'Subtitles'][b'addic7ed_username'] = self.ADDIC7ED_USER
        new_config[b'Subtitles'][b'addic7ed_password'] = encrypt(self.ADDIC7ED_PASS,
                                                                 self.ENCRYPTION_VERSION)

        new_config[b'Subtitles'][b'legendastv_username'] = self.LEGENDASTV_USER
        new_config[b'Subtitles'][b'legendastv_password'] = encrypt(self.LEGENDASTV_PASS,
                                                                   self.ENCRYPTION_VERSION)

        new_config[b'Subtitles'][b'opensubtitles_username'] = self.OPENSUBTITLES_USER
        new_config[b'Subtitles'][b'opensubtitles_password'] = encrypt(self.OPENSUBTITLES_PASS,
                                                                      self.ENCRYPTION_VERSION)

        new_config[b'FailedDownloads'] = {}
        new_config[b'FailedDownloads'][b'use_failed_downloads'] = int(self.USE_FAILED_DOWNLOADS)
        new_config[b'FailedDownloads'][b'delete_failed'] = int(self.DELETE_FAILED)

        new_config[b'ANIDB'] = {}
        new_config[b'ANIDB'][b'use_anidb'] = int(self.USE_ANIDB)
        new_config[b'ANIDB'][b'anidb_username'] = self.ANIDB_USERNAME
        new_config[b'ANIDB'][b'anidb_password'] = encrypt(self.ANIDB_PASSWORD,
                                                          self.ENCRYPTION_VERSION)
        new_config[b'ANIDB'][b'anidb_use_mylist'] = int(self.ANIDB_USE_MYLIST)

        new_config[b'ANIME'] = {}
        new_config[b'ANIME'][b'anime_split_home'] = int(self.ANIME_SPLIT_HOME)

        # dynamically save provider settings
        for providerID, providerObj in sickrage.srCore.providersDict[GenericProvider.TORRENT].items():
            new_config[providerID.upper()] = {}
            new_config[providerID.upper()][providerID] = int(providerObj.enabled)
            if hasattr(providerObj, 'digest'):
                new_config[providerID.upper()][
                    providerID + '_digest'] = providerObj.digest
            if hasattr(providerObj, 'hash'):
                new_config[providerID.upper()][
                    providerID + '_hash'] = providerObj.hash
            if hasattr(providerObj, 'api_key'):
                new_config[providerID.upper()][
                    providerID + '_api_key'] = providerObj.api_key
            if hasattr(providerObj, 'username'):
                new_config[providerID.upper()][
                    providerID + '_username'] = providerObj.username
            if hasattr(providerObj, 'password'):
                new_config[providerID.upper()][providerID + '_password'] = encrypt(
                    providerObj.password, self.ENCRYPTION_VERSION)
            if hasattr(providerObj, 'passkey'):
                new_config[providerID.upper()][
                    providerID + '_passkey'] = providerObj.passkey
            if hasattr(providerObj, 'pin'):
                new_config[providerID.upper()][
                    providerID + '_pin'] = providerObj.pin
            if hasattr(providerObj, 'confirmed'):
                new_config[providerID.upper()][providerID + '_confirmed'] = int(
                    providerObj.confirmed)
            if hasattr(providerObj, 'ranked'):
                new_config[providerID.upper()][providerID + '_ranked'] = int(
                    providerObj.ranked)
            if hasattr(providerObj, 'engrelease'):
                new_config[providerID.upper()][providerID + '_engrelease'] = int(
                    providerObj.engrelease)
            if hasattr(providerObj, 'onlyspasearch'):
                new_config[providerID.upper()][providerID + '_onlyspasearch'] = int(
                    providerObj.onlyspasearch)
            if hasattr(providerObj, 'sorting'):
                new_config[providerID.upper()][
                    providerID + '_sorting'] = providerObj.sorting
            if hasattr(providerObj, 'ratio'):
                new_config[providerID.upper()][
                    providerID + '_ratio'] = providerObj.ratio
            if hasattr(providerObj, 'minseed'):
                new_config[providerID.upper()][providerID + '_minseed'] = int(
                    providerObj.minseed)
            if hasattr(providerObj, 'minleech'):
                new_config[providerID.upper()][providerID + '_minleech'] = int(
                    providerObj.minleech)
            if hasattr(providerObj, 'options'):
                new_config[providerID.upper()][
                    providerID + '_options'] = providerObj.options
            if hasattr(providerObj, 'freeleech'):
                new_config[providerID.upper()][providerID + '_freeleech'] = int(
                    providerObj.freeleech)
            if hasattr(providerObj, 'search_mode'):
                new_config[providerID.upper()][
                    providerID + '_search_mode'] = providerObj.search_mode
            if hasattr(providerObj, 'search_fallback'):
                new_config[providerID.upper()][providerID + '_search_fallback'] = int(
                    providerObj.search_fallback)
            if hasattr(providerObj, 'enable_daily'):
                new_config[providerID.upper()][providerID + '_enable_daily'] = int(
                    providerObj.enable_daily)
            if hasattr(providerObj, 'enable_backlog'):
                new_config[providerID.upper()][providerID + '_enable_backlog'] = int(
                    providerObj.enable_backlog)
            if hasattr(providerObj, 'cat'):
                new_config[providerID.upper()][providerID + '_cat'] = int(
                    providerObj.cat)
            if hasattr(providerObj, 'subtitle'):
                new_config[providerID.upper()][providerID + '_subtitle'] = int(
                    providerObj.subtitle)

        for providerID, providerObj in sickrage.srCore.providersDict[GenericProvider.NZB].items():
            new_config[providerID.upper()] = {}
            new_config[providerID.upper()][providerID] = int(providerObj.enabled)

            if hasattr(providerObj, 'api_key'):
                new_config[providerID.upper()][
                    providerID + '_api_key'] = providerObj.api_key
            if hasattr(providerObj, 'username'):
                new_config[providerID.upper()][
                    providerID + '_username'] = providerObj.username
            if hasattr(providerObj, 'search_mode'):
                new_config[providerID.upper()][
                    providerID + '_search_mode'] = providerObj.search_mode
            if hasattr(providerObj, 'search_fallback'):
                new_config[providerID.upper()][providerID + '_search_fallback'] = int(
                    providerObj.search_fallback)
            if hasattr(providerObj, 'enable_daily'):
                new_config[providerID.upper()][providerID + '_enable_daily'] = int(
                    providerObj.enable_daily)
            if hasattr(providerObj, 'enable_backlog'):
                new_config[providerID.upper()][providerID + '_enable_backlog'] = int(
                    providerObj.enable_backlog)

        new_config.write()
        return new_config


class ConfigMigrator(srConfig):
    def __init__(self, config_obj):
        """
        Initializes a config migrator that can take the config from the version indicated in the config
        file up to the latest version
        """
        super(ConfigMigrator, self).__init__(config_obj.filename)
        self.CONFIG_OBJ = config_obj

        # check the version of the config
        self.config_version = self.check_setting_int('General', 'config_version', self.CONFIG_VERSION)
        self.expected_config_version = self.CONFIG_VERSION
        self.migration_names = {
            1: 'Custom naming',
            2: 'Sync backup number with version number',
            3: 'Rename omgwtfnzb variables',
            4: 'Add newznab catIDs',
            5: 'Metadata update',
            6: 'Convert from XBMC to new KODI variables',
            7: 'Use version 2 for password encryption'
        }

    def migrate_config(self):
        """
        Calls each successive migration until the config is the same version as SB expects
        """

        if self.config_version > self.expected_config_version:
            sickrage.srLogger.log_error_and_exit(
                """Your config version (%i) has been incremented past what this version of supports (%i).
                    If you have used other forks or a newer version of  your config file may be unusable due to their modifications.""" %
                (self.config_version, self.expected_config_version)
            )

        self.CONFIG_VERSION = self.config_version

        while self.config_version < self.expected_config_version:
            next_version = self.config_version + 1

            if next_version in self.migration_names:
                migration_name = ': ' + self.migration_names[next_version]
            else:
                migration_name = ''

            sickrage.srLogger.info("Backing up config before upgrade")
            if not backupVersionedFile(self.CONFIG_OBJ.filename, self.config_version):
                sickrage.srLogger.log_error_and_exit("Config backup failed, abort upgrading config")
            else:
                sickrage.srLogger.info("Proceeding with upgrade")

            # do the migration, expect a method named _migrate_v<num>
            sickrage.srLogger.info("Migrating config up to version " + str(next_version) + migration_name)
            getattr(self, '_migrate_v' + str(next_version))()
            self.config_version = next_version

            # save new config after migration
            sickrage.srConfig.CONFIG_VERSION = self.config_version

    # Migration v1: Custom naming
    def _migrate_v1(self):
        """
        Reads in the old naming settings from your config and generates a new config template from them.
        """

        self.NAMING_PATTERN = self._name_to_pattern()
        sickrage.srLogger.info(
            "Based on your old settings I'm setting your new naming pattern to: " + self.NAMING_PATTERN)

        self.NAMING_CUSTOM_ABD = bool(self.check_setting_int('General', 'naming_dates', 0))

        if self.NAMING_CUSTOM_ABD:
            self.NAMING_ABD_PATTERN = self._name_to_pattern(True)
            sickrage.srLogger.info(
                "Adding a custom air-by-date naming pattern to your config: " + self.NAMING_ABD_PATTERN)
        else:
            self.NAMING_ABD_PATTERN = validator.name_abd_presets[0]

        self.NAMING_MULTI_EP = int(
            self.check_setting_int('General', 'NAMING_MULTI_EP_TYPE', 1))

        # see if any of their shows used season folders
        season_folder_shows = main_db.MainDB().select("SELECT * FROM tv_shows WHERE flatten_folders = 0")

        # if any shows had season folders on then prepend season folder to the pattern
        if season_folder_shows:

            old_season_format = self.check_setting_str('General', 'season_folders_format',
                                                       'Season %02d')

            if old_season_format:
                try:
                    new_season_format = old_season_format % 9
                    new_season_format = str(new_season_format).replace('09', '%0S')
                    new_season_format = new_season_format.replace('9', '%S')

                    sickrage.srLogger.info(
                        "Changed season folder format from " + old_season_format + " to " + new_season_format + ", prepending it to your naming config")
                    self.NAMING_PATTERN = new_season_format + os.sep + self.NAMING_PATTERN

                except (TypeError, ValueError):
                    sickrage.srLogger.error("Can't change " + old_season_format + " to new season format")

        # if no shows had it on then don't flatten any shows and don't put season folders in the config
        else:

            sickrage.srLogger.info(
                "No shows were using season folders before so I'm disabling flattening on all shows")

            # don't flatten any shows at all
            main_db.MainDB().action("UPDATE tv_shows SET flatten_folders = 0")

        self.NAMING_FORCE_FOLDERS = check_force_season_folders()

    def _name_to_pattern(self, abd=False):

        # get the old settings from the file
        use_periods = bool(self.check_setting_int('General', 'naming_use_periods', 0))
        ep_type = self.check_setting_int('General', 'NAMING_EP_TYPE', 0)
        sep_type = self.check_setting_int('General', 'NAMING_SEP_TYPE', 0)
        use_quality = bool(self.check_setting_int('General', 'naming_quality', 0))

        use_show_name = bool(self.check_setting_int('General', 'naming_show_name', 1))
        use_ep_name = bool(self.check_setting_int('General', 'naming_ep_name', 1))

        # make the presets into templates
        naming_ep_type = ("%Sx%0E",
                          "s%0Se%0E",
                          "S%0SE%0E",
                          "%0Sx%0E")
        naming_sep_type = (" - ", " ")

        # set up our data to use
        if use_periods:
            show_name = '%S.N'
            ep_name = '%E.N'
            ep_quality = '%Q.N'
            abd_string = '%A.D'
        else:
            show_name = '%SN'
            ep_name = '%EN'
            ep_quality = '%QN'
            abd_string = '%A-D'

        if abd:
            ep_string = abd_string
        else:
            ep_string = naming_ep_type[ep_type]

        finalName = ""

        # start with the show name
        if use_show_name:
            finalName += show_name + naming_sep_type[sep_type]

        # add the season/ep stuff
        finalName += ep_string

        # add the episode name
        if use_ep_name:
            finalName += naming_sep_type[sep_type] + ep_name

        # add the quality
        if use_quality:
            finalName += naming_sep_type[sep_type] + ep_quality

        if use_periods:
            finalName = re.sub(r"\s+", ".", finalName)

        return finalName

    # Migration v2: Dummy migration to sync backup number with config version number
    def _migrate_v2(self):
        return

    # Migration v2: Rename omgwtfnzb variables
    def _migrate_v3(self):
        """
        Reads in the old naming settings from your config and generates a new config template from them.
        """
        # get the old settings from the file and store them in the new variable names
        self.OMGWTFNZBS_USERNAME = self.check_setting_str('omgwtfnzbs', 'omgwtfnzbs_uid',
                                                          '')
        self.OMGWTFNZBS_APIKEY = self.check_setting_str('omgwtfnzbs', 'omgwtfnzbs_key', '')

    # Migration v4: Add default newznab catIDs
    def _migrate_v4(self):
        """ Update newznab providers so that the category IDs can be set independently via the config """

        new_newznab_data = []
        old_newznab_data = self.check_setting_str('Newznab', 'newznab_data', '')

        if old_newznab_data:
            old_newznab_data_list = old_newznab_data.split("!!!")

            for cur_provider_data in old_newznab_data_list:
                try:
                    name, url, key, enabled = cur_provider_data.split("|")
                except ValueError:
                    sickrage.srLogger.error(
                        "Skipping Newznab provider string: '" + cur_provider_data + "', incorrect format")
                    continue

                if name == 'Sick Beard Index':
                    key = '0'

                if name == 'NZBs.org':
                    catIDs = '5030,5040,5060,5070,5090'
                else:
                    catIDs = '5030,5040,5060'

                cur_provider_data_list = [name, url, key, catIDs, enabled]
                new_newznab_data.append("|".join(cur_provider_data_list))

            self.NEWZNAB_DATA = "!!!".join(new_newznab_data)

    # Migration v5: Metadata upgrade
    def _migrate_v5(self):
        """ Updates metadata values to the new format """

        """ Quick overview of what the upgrade does:

        new | old | description (new)
        ----+-----+--------------------
          1 |  1  | show metadata
          2 |  2  | episode metadata
          3 |  4  | show fanart
          4 |  3  | show poster
          5 |  -  | show banner
          6 |  5  | episode thumb
          7 |  6  | season poster
          8 |  -  | season banner
          9 |  -  | season all poster
         10 |  -  | season all banner

        Note that the ini places start at 1 while the list index starts at 0.
        old format: 0|0|0|0|0|0 -- 6 places
        new format: 0|0|0|0|0|0|0|0|0|0 -- 10 places

        Drop the use of use_banner option.
        Migrate the poster override to just using the banner option (applies to xbmc only).
        """

        metadata_xbmc = self.check_setting_str('General', 'metadata_xbmc', '0|0|0|0|0|0')
        metadata_xbmc_12plus = self.check_setting_str('General', 'metadata_xbmc_12plus',
                                                      '0|0|0|0|0|0')
        metadata_mediabrowser = self.check_setting_str('General', 'metadata_mediabrowser',
                                                       '0|0|0|0|0|0')
        metadata_ps3 = self.check_setting_str('General', 'metadata_ps3', '0|0|0|0|0|0')
        metadata_wdtv = self.check_setting_str('General', 'metadata_wdtv', '0|0|0|0|0|0')
        metadata_tivo = self.check_setting_str('General', 'metadata_tivo', '0|0|0|0|0|0')
        metadata_mede8er = self.check_setting_str('General', 'metadata_mede8er', '0|0|0|0|0|0')

        use_banner = bool(self.check_setting_int('General', 'use_banner', 0))

        def _migrate_metadata(metadata, metadata_name, use_banner):
            cur_metadata = metadata.split('|')
            # if target has the old number of values, do upgrade
            if len(cur_metadata) == 6:
                sickrage.srLogger.info("Upgrading " + metadata_name + " metadata, old value: " + metadata)
                cur_metadata.insert(4, '0')
                cur_metadata.append('0')
                cur_metadata.append('0')
                cur_metadata.append('0')
                # swap show fanart, show poster
                cur_metadata[3], cur_metadata[2] = cur_metadata[2], cur_metadata[3]
                # if user was using use_banner to override the poster, instead enable the banner option and deactivate poster
                if metadata_name == 'XBMC' and use_banner:
                    cur_metadata[4], cur_metadata[3] = cur_metadata[3], '0'
                # write new format
                metadata = '|'.join(cur_metadata)
                sickrage.srLogger.info("Upgrading " + metadata_name + " metadata, new value: " + metadata)

            elif len(cur_metadata) == 10:

                metadata = '|'.join(cur_metadata)
                sickrage.srLogger.info("Keeping " + metadata_name + " metadata, value: " + metadata)

            else:
                sickrage.srLogger.error(
                    "Skipping " + metadata_name + " metadata: '" + metadata + "', incorrect format")
                metadata = '0|0|0|0|0|0|0|0|0|0'
                sickrage.srLogger.info("Setting " + metadata_name + " metadata, new value: " + metadata)

            return metadata

        self.METADATA_XBMC = _migrate_metadata(metadata_xbmc, 'XBMC', use_banner)
        self.METADATA_XBMC_12PLUS = _migrate_metadata(metadata_xbmc_12plus, 'XBMC 12+', use_banner)
        self.METADATA_MEDIABROWSER = _migrate_metadata(metadata_mediabrowser, 'MediaBrowser', use_banner)
        self.METADATA_PS3 = _migrate_metadata(metadata_ps3, 'PS3', use_banner)
        self.METADATA_WDTV = _migrate_metadata(metadata_wdtv, 'WDTV', use_banner)
        self.METADATA_TIVO = _migrate_metadata(metadata_tivo, 'TIVO', use_banner)
        self.METADATA_MEDE8ER = _migrate_metadata(metadata_mede8er, 'Mede8er', use_banner)

    # Migration v6: Convert from XBMC to KODI variables
    def _migrate_v6(self):
        self.USE_KODI = bool(self.check_setting_int('XBMC', 'use_xbmc', 0))
        self.KODI_ALWAYS_ON = bool(self.check_setting_int('XBMC', 'xbmc_always_on', 1))
        self.KODI_NOTIFY_ONSNATCH = bool(
            self.check_setting_int('XBMC', 'xbmc_notify_onsnatch', 0))
        self.KODI_NOTIFY_ONDOWNLOAD = bool(
            self.check_setting_int('XBMC', 'xbmc_notify_ondownload', 0))
        self.KODI_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            self.check_setting_int('XBMC', 'xbmc_notify_onsubtitledownload', 0))
        self.KODI_UPDATE_LIBRARY = bool(
            self.check_setting_int('XBMC', 'xbmc_update_library', 0))
        self.KODI_UPDATE_FULL = bool(self.check_setting_int('XBMC', 'xbmc_update_full', 0))
        self.KODI_UPDATE_ONLYFIRST = bool(
            self.check_setting_int('XBMC', 'xbmc_update_onlyfirst', 0))
        self.KODI_HOST = self.check_setting_str('XBMC', 'xbmc_host', '')
        self.KODI_USERNAME = self.check_setting_str('XBMC', 'xbmc_username', '')
        self.KODI_PASSWORD = self.check_setting_str('XBMC', 'xbmc_password', '')
        self.METADATA_KODI = self.check_setting_str('General', 'metadata_xbmc',
                                                    '0|0|0|0|0|0|0|0|0|0')
        self.METADATA_KODI_12PLUS = self.check_setting_str('General',
                                                           'metadata_xbmc_12plus',
                                                           '0|0|0|0|0|0|0|0|0|0')

    # Migration v6: Use version 2 for password encryption
    def _migrate_v7(self):
        self.ENCRYPTION_VERSION = 2
