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
import six
from configobj import ConfigObj

import sickrage
from sickrage.core.classes import srIntervalTrigger
from sickrage.core.common import SD, WANTED, SKIPPED, Quality
from sickrage.core.helpers import backupVersionedFile, makeDir, generateCookieSecret, autoType, get_lan_ip, extractZip, \
    try_int


class srConfig(object):
    def __init__(self):
        self.loaded = False

        self.DEBUG = False
        self.DEVELOPER = False

        self.CONFIG_OBJ = None
        self.CONFIG_VERSION = 11
        self.ENCRYPTION_VERSION = 0
        self.ENCRYPTION_SECRET = generateCookieSecret()

        self.LAST_DB_COMPACT = 0

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
        self.VERSION_NOTIFY = True
        self.AUTO_UPDATE = True
        self.NOTIFY_ON_UPDATE = True
        self.NOTIFY_ON_LOGIN = False
        self.PIP_PATH = ""
        self.GIT_RESET = True
        self.GIT_USERNAME = ""
        self.GIT_PASSWORD = ""
        self.GIT_PATH = ""
        self.GIT_AUTOISSUES = False
        self.GIT_NEWVER = False
        self.CHANGES_URL = 'https://git.sickrage.ca/SiCKRAGE/sickrage/raw/master/changelog.md'
        self.SOCKET_TIMEOUT = 30
        self.WEB_HOST = get_lan_ip()
        self.WEB_PORT = 8081
        self.WEB_LOG = False
        self.WEB_ROOT = ""
        self.WEB_USERNAME = ""
        self.WEB_PASSWORD = ""
        self.WEB_IPV6 = False
        self.WEB_COOKIE_SECRET = generateCookieSecret()
        self.WEB_USE_GZIP = True
        self.HANDLE_REVERSE_PROXY = False
        self.PROXY_SETTING = ""
        self.PROXY_INDEXERS = True
        self.SSL_VERIFY = True
        self.ENABLE_HTTPS = False
        self.HTTPS_CERT = os.path.abspath(os.path.join(sickrage.PROG_DIR, 'server.crt'))
        self.HTTPS_KEY = os.path.abspath(os.path.join(sickrage.PROG_DIR, 'server.key'))
        self.API_KEY = ""
        self.API_ROOT = None
        self.INDEXER_DEFAULT_LANGUAGE = 'en'
        self.EP_DEFAULT_DELETED_STATUS = 6
        self.LAUNCH_BROWSER = False
        self.SHOWUPDATE_STALE = True
        self.ROOT_DIRS = ""
        self.CPU_PRESET = "NORMAL"
        self.ANON_REDIRECT = 'http://nullrefer.com/?'
        self.DOWNLOAD_URL = ""
        self.TRASH_REMOVE_SHOW = False
        self.TRASH_ROTATE_LOGS = False
        self.SORT_ARTICLE = False
        self.DISPLAY_ALL_SEASONS = True
        self.DEFAULT_PAGE = "home"
        self.USE_LISTVIEW = False

        self.QUALITY_DEFAULT = SD
        self.STATUS_DEFAULT = SKIPPED
        self.STATUS_DEFAULT_AFTER = WANTED
        self.FLATTEN_FOLDERS_DEFAULT = False
        self.SUBTITLES_DEFAULT = False
        self.INDEXER_DEFAULT = 0
        self.INDEXER_TIMEOUT = 120
        self.SCENE_DEFAULT = False
        self.ANIME_DEFAULT = False
        self.ARCHIVE_DEFAULT = False
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
        self.ENABLE_RSS_CACHE = True
        self.ENABLE_RSS_CACHE_VALID_SHOWS = False
        self.PROPER_SEARCHER_INTERVAL = None
        self.ALLOW_HIGH_PRIORITY = False
        self.SAB_FORCED = False
        self.RANDOMIZE_PROVIDERS = False
        self.MIN_AUTOPOSTPROCESSOR_FREQ = 1
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
        self.TORRENT_TRACKERS = "udp://coppersurfer.tk:6969/announce," \
                                "udp://open.demonii.com:1337," \
                                "udp://exodus.desync.com:6969," \
                                "udp://9.rarbg.me:2710/announce," \
                                "udp://glotorrents.pw:6969/announce," \
                                "udp://tracker.openbittorrent.com:80/announce," \
                                "udp://9.rarbg.to:2710/announce"
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
        self.FREEMOBILE_ID = ""
        self.FREEMOBILE_APIKEY = ""
        self.USE_TELEGRAM = False
        self.TELEGRAM_NOTIFY_ONSNATCH = False
        self.TELEGRAM_NOTIFY_ONDOWNLOAD = False
        self.TELEGRAM_NOTIFY_ONSUBTITLEDOWNLOAD = False
        self.TELEGRAM_ID = ""
        self.TELEGRAM_APIKEY = ""
        self.USE_PROWL = False
        self.PROWL_NOTIFY_ONSNATCH = False
        self.PROWL_NOTIFY_ONDOWNLOAD = False
        self.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD = False
        self.PROWL_API = None
        self.PROWL_PRIORITY = 0
        self.USE_TWITTER = False
        self.TWITTER_NOTIFY_ONSNATCH = False
        self.TWITTER_NOTIFY_ONDOWNLOAD = False
        self.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD = False
        self.TWITTER_USERNAME = None
        self.TWITTER_PASSWORD = None
        self.TWITTER_PREFIX = None
        self.TWITTER_DMTO = None
        self.TWITTER_USEDM = False
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
        self.USE_SLACK = False
        self.SLACK_NOTIFY_ONSNATCH = None
        self.SLACK_NOTIFY_ONDOWNLOAD = None
        self.SLACK_NOTIFY_ONSUBTITLEDOWNLOAD = None
        self.SLACK_WEBHOOK = ""
        self.USE_DISCORD = False
        self.DISCORD_NOTIFY_ONSNATCH = False
        self.DISCORD_NOTIFY_ONDOWNLOAD = False
        self.DISCORD_NOTIFY_ONSUBTITLEDOWNLOAD = False
        self.DISCORD_WEBHOOK = ""
        self.DISCORD_NAME = None
        self.DISCORD_AVATAR_URL = None
        self.DISCORD_TTS = False
        self.USE_TRAKT = False
        self.TRAKT_USERNAME = ""
        self.TRAKT_OAUTH_TOKEN = ""
        self.TRAKT_REMOVE_WATCHLIST = False
        self.TRAKT_REMOVE_SERIESLIST = False
        self.TRAKT_REMOVE_SHOW_FROM_SICKRAGE = False
        self.TRAKT_SYNC_WATCHLIST = False
        self.TRAKT_METHOD_ADD = False
        self.TRAKT_START_PAUSED = False
        self.TRAKT_USE_RECOMMENDED = False
        self.TRAKT_SYNC = False
        self.TRAKT_SYNC_REMOVE = False
        self.TRAKT_DEFAULT_INDEXER = 1
        self.TRAKT_TIMEOUT = 30
        self.TRAKT_BLACKLIST_NAME = ""
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
        self.NMA_PRIORITY = 0
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
        self.GUI_NAME = 'default'
        self.GUI_DIR = os.path.join(sickrage.PROG_DIR, 'core', 'webserver', 'gui', self.GUI_NAME)
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
        self.ITASA_USER = None
        self.ITASA_PASS = None
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

        self.QUALITY_SIZES = None

        self.CUSTOM_PROVIDERS = None

        self.GIT_REMOTE = "origin"
        self.GIT_REMOTE_URL = "https://git.sickrage.ca/SiCKRAGE/sickrage"

        self.RANDOM_USER_AGENT = False

        self.FANART_BACKGROUND = True
        self.FANART_BACKGROUND_OPACITY = 0.4

        self.UNRAR_TOOL = rarfile.UNRAR_TOOL
        self.UNRAR_ALT_TOOL = rarfile.ALT_TOOL

    @property
    def defaults(self):
        return {
            'Providers': {
                'custom_providers': '',
                'providers_order': []
            },
            'NZBs': {
                'nzbs': False,
                'nzbs_uid': '',
                'nzbs_hash': ''
            },
            'Growl': {
                'growl_host': '',
                'use_growl': False,
                'growl_notify_ondownload': False,
                'growl_notify_onsubtitledownload': False,
                'growl_notify_onsnatch': False,
                'growl_password': ''
            },
            'Slack': {
                'slack_notify_onsnatch': False,
                'slack_notify_ondownload': False,
                'slack_notify_onsubtitledownload': False,
                'use_slack': False,
                'slack_webhook': ''
            },
            'TELEGRAM': {
                'telegram_notify_ondownload': False,
                'telegram_apikey': '',
                'telegram_id': '',
                'use_telegram': False,
                'telegram_notify_onsnatch': False,
                'telegram_notify_onsubtitledownload': False
            },
            'GUI': {
                'coming_eps_display_paused': False,
                'display_show_specials': True,
                'gui_name': 'default',
                'history_limit': '100',
                'poster_sortdir': 1,
                'coming_eps_missed_range': 7,
                'date_preset': '%x',
                'fuzzy_dating': False,
                'fanart_background': True,
                'home_layout': 'poster',
                'coming_eps_layout': 'banner',
                'coming_eps_sort': 'date',
                'poster_sortby': 'name',
                'time_preset': '%I:%M:%S%p',
                'trim_zero': False,
                'fanart_background_opacity': 0.4,
                'history_layout': 'detailed',
                'filter_row': True,
                'timezone_display': 'local',
                'theme_name': 'dark'
            },
            'NMA': {
                'nma_notify_onsubtitledownload': False,
                'use_nma': False,
                'nma_notify_onsnatch': False,
                'nma_priority': '0',
                'nma_api': '',
                'nma_notify_ondownload': False
            },
            'Prowl': {
                'prowl_notify_ondownload': False,
                'prowl_api': '',
                'prowl_priority': '0',
                'prowl_notify_onsubtitledownload': False,
                'prowl_notify_onsnatch': False,
                'use_prowl': False
            },
            'Synology': {
                'use_synoindex': False
            },
            'Newzbin': {
                'newzbin': False,
                'newzbin_password': '',
                'newzbin_username': ''
            },
            'Trakt': {
                'trakt_remove_serieslist': False,
                'trakt_remove_show_from_sickrage': False,
                'trakt_use_recommended': False,
                'trakt_sync': False,
                'use_trakt': False,
                'trakt_blacklist_name': '',
                'trakt_start_paused': False,
                'trakt_sync_remove': False,
                'trakt_username': '',
                'trakt_oauth_token': '',
                'trakt_method_add': 0,
                'trakt_remove_watchlist': False,
                'trakt_sync_watchlist': False,
                'trakt_timeout': 30,
                'trakt_default_indexer': 1
            },
            'NMJv2': {
                'nmjv2_dbloc': '',
                'nmjv2_database': '',
                'nmjv2_host': '',
                'use_nmjv2': False
            },
            'SABnzbd': {
                'sab_forced': False,
                'sab_category': 'tv',
                'sab_apikey': '',
                'sab_category_anime': 'anime',
                'sab_category_backlog': 'tv',
                'sab_host': '',
                'sab_password': '',
                'sab_username': '',
                'sab_category_anime_backlog': 'anime'
            },
            'Plex': {
                'plex_update_library': False,
                'plex_server_host': '',
                'plex_host': '',
                'plex_password': '',
                'plex_notify_onsubtitledownload': False,
                'plex_notify_onsnatch': False,
                'plex_username': '',
                'plex_notify_ondownload': False,
                'plex_server_token': '',
                'use_plex': False,
                'use_plex_client': False,
                'plex_client_username': '',
                'plex_client_password': ''
            },
            'TORRENT': {
                'torrent_verify_cert': False,
                'torrent_paused': False,
                'torrent_host': '',
                'torrent_trackers': 'udp://coppersurfer.tk:6969/announce,'
                                    'udp://open.demonii.com:1337,'
                                    'udp://exodus.desync.com:6969,'
                                    'udp://9.rarbg.me:2710/announce,'
                                    'udp://glotorrents.pw:6969/announce,'
                                    'udp://tracker.openbittorrent.com:80/announce,'
                                    'udp://9.rarbg.to:2710/announce',
                'torrent_label_anime': '',
                'torrent_path': '',
                'torrent_auth_type': '',
                'torrent_rpcurl': 'transmission',
                'torrent_username': '',
                'torrent_label': '',
                'torrent_password': '',
                'torrent_high_bandwidth': False,
                'torrent_seed_time': 0
            },
            'Pushalot': {
                'pushalot_notify_onsubtitledownload': False,
                'pushalot_authorizationtoken': '',
                'pushalot_notify_onsnatch': False,
                'pushalot_notify_ondownload': False,
                'use_pushalot': False
            },
            'Pushover': {
                'pushover_notify_ondownload': False,
                'pushover_sound': 'pushover',
                'use_pushover': False,
                'pushover_notify_onsubtitledownload': False,
                'pushover_device': '',
                'pushover_apikey': '',
                'pushover_userkey': '',
                'pushover_notify_onsnatch': False
            },
            'Email': {
                'email_notify_onsnatch': False,
                'email_list': '',
                'email_password': '',
                'email_tls': False,
                'use_email': False,
                'email_notify_ondownload': False,
                'email_port': 25,
                'email_notify_onsubtitledownload': False,
                'email_user': '',
                'email_from': '',
                'email_host': ''
            },
            'KODI': {
                'kodi_update_onlyfirst': False,
                'kodi_notify_onsnatch': False,
                'kodi_notify_ondownload': False,
                'kodi_host': '',
                'kodi_username': '',
                'kodi_always_on': True,
                'kodi_update_library': False,
                'use_kodi': False,
                'kodi_password': '',
                'kodi_update_full': False,
                'kodi_notify_onsubtitledownload': False
            },
            'Quality': {
                'sizes': Quality.qualitySizes
            },
            'FreeMobile': {
                'freemobile_notify_onsnatch': False,
                'freemobile_notify_onsubtitledownload': False,
                'freemobile_notify_ondownload': False,
                'freemobile_apikey': '',
                'freemobile_id': '',
                'use_freemobile': False
            },
            'Discord': {
                'discord_notify_onsubtitledownload': False,
                'discord_notify_ondownload': False,
                'discord_notify_onsnatch': False,
                'discord_webhook': '',
                'use_discord': False,
                'discord_name': '',
                'discord_avatar_url': '',
                'discord_tts': False
            },
            'SynologyNotifier': {
                'synologynotifier_notify_onsnatch': False,
                'synologynotifier_notify_ondownload': False,
                'use_synologynotifier': False,
                'synologynotifier_notify_onsubtitledownload': False
            },
            'ANIDB': {
                'anidb_use_mylist': False,
                'use_anidb': False,
                'anidb_password': '',
                'anidb_username': ''
            },
            'Blackhole': {
                'nzb_dir': '',
                'torrent_dir': ''
            },
            'General': {
                'log_size': 1048576,
                'calendar_unprotected': False,
                'https_key': os.path.abspath(os.path.join(sickrage.PROG_DIR, 'server.key')),
                'allow_high_priority': True,
                'developer': True,
                'anon_redirect': 'http://nullrefer.com/?',
                'indexer_timeout': 120,
                'web_use_gzip': True,
                'dailysearch_frequency': 40,
                'ignore_words': 'german,french,core2hd,dutch,swedish,reenc,MrLss',
                'api_key': '',
                'check_propers_interval': 'daily',
                'nzb_method': 'blackhole',
                'web_cookie_secret': generateCookieSecret(),
                'ssl_verify': True,
                'encryption_secret': generateCookieSecret(),
                'version_notify': True,
                'web_root': '',
                'add_shows_wo_dir': False,
                'debug': True,
                'indexer_default': 0,
                'use_torrents': True,
                'display_all_seasons': True,
                'usenet_retention': 500,
                'download_propers': True,
                'pip_path': 'pip',
                'del_rar_contents': False,
                'process_method': 'copy',
                'file_timestamp_timezone': 'network',
                'auto_update': True,
                'tv_download_dir': '',
                'naming_custom_abd': False,
                'archive_default': False,
                'naming_sports_pattern': '%SN - %A-D - %EN',
                'create_missing_show_dirs': False,
                'trash_rotate_logs': False,
                'airdate_episodes': False,
                'notify_on_update': True,
                'https_cert': os.path.abspath(os.path.join(sickrage.PROG_DIR, 'server.crt')),
                'git_autoissues': False,
                'backlog_days': 7,
                'root_dirs': '',
                'naming_pattern': 'Season %0S/%SN - S%0SE%0E - %EN',
                'sort_article': False,
                'handle_reverse_proxy': False,
                'web_username': '',
                'postpone_if_sync_files': True,
                'cpu_preset': 'NORMAL',
                'nfo_rename': True,
                'naming_anime_multi_ep': 1,
                'use_nzbs': False,
                'web_ipv6': False,
                'anime_default': False,
                'default_page': 'home',
                'update_frequency': 1,
                'download_url': '',
                'encryption_version': 0,
                'showupdate_hour': 3,
                'enable_rss_cache': True,
                'enable_rss_cache_valid_shows': False,
                'status_default': 5,
                'naming_anime': 3,
                'naming_custom_sports': False,
                'naming_anime_pattern': 'Season %0S/%SN - S%0SE%0E - %EN',
                'naming_custom_anime': False,
                'randomize_providers': False,
                'web_host': '192.168.1.203',
                'config_version': 11,
                'process_automatically': False,
                'git_path': 'git',
                'sync_files': '!sync,lftp-pget-status,part,bts,!qb',
                'web_port': 8081,
                'launch_browser': False,
                'unpack': False,
                'move_associated_files': False,
                'naming_multi_ep': 1,
                'random_user_agent': False,
                'torrent_method': 'blackhole',
                'use_listview': False,
                'trash_remove_show': False,
                'enable_https': False,
                'no_delete': False,
                'naming_abd_pattern': '%SN - %A.D - %EN',
                'socket_timeout': 30,
                'proxy_setting': '',
                'backlog_frequency': 21,
                'notify_on_login': False,
                'rename_episodes': True,
                'quality_default': 3,
                'git_username': '',
                'extra_scripts': '',
                'flatten_folders_default': False,
                'indexerDefaultLang': 'en',
                'autopostprocessor_frequency': 10,
                'showupdate_stale': True,
                'git_password': '',
                'ep_default_deleted_status': 6,
                'no_restart': False,
                'require_words': '',
                'naming_strip_year': False,
                'proxy_indexers': True,
                'web_log': False,
                'log_nr': 5,
                'git_newver': False,
                'git_reset': True,
                'web_password': '',
                'scene_default': False,
                'skip_removed_files': False,
                'status_default_after': 3,
                'last_db_compact': 0,
                'ignored_subs_list': 'dk,fin,heb,kor,nor,nordic,pl,swe',
                'calendar_icons': False,
                'keep_processed_dir': True
            },
            'NZBget': {
                'nzbget_host': '',
                'nzbget_category_anime': 'anime',
                'nzbget_use_https': False,
                'nzbget_password': 'tegbzn6789',
                'nzbget_category': 'tv',
                'nzbget_priority': 100,
                'nzbget_category_anime_backlog': 'anime',
                'nzbget_username': 'nzbget',
                'nzbget_category_backlog': 'tv'
            },
            'Emby': {
                'use_emby': False,
                'emby_apikey': '',
                'emby_host': ''
            },
            'pyTivo': {
                'pytivo_share_name': '',
                'pytivo_notify_ondownload': False,
                'pytivo_tivo_name': '',
                'pytivo_notify_onsnatch': False,
                'pytivo_host': '',
                'pytivo_notify_onsubtitledownload': False,
                'pyTivo_update_library': False,
                'use_pytivo': False
            },
            'theTVDB': {
                'thetvdb_apitoken': ''
            },
            'Pushbullet': {
                'pushbullet_device': '',
                'use_pushbullet': False,
                'pushbullet_notify_ondownload': False,
                'pushbullet_notify_onsubtitledownload': False,
                'pushbullet_notify_onsnatch': False,
                'pushbullet_api': ''
            },
            'Libnotify': {
                'libnotify_notify_onsubtitledownload': False,
                'libnotify_notify_onsnatch': False,
                'libnotify_notify_ondownload': False,
                'use_libnotify': False
            },
            'Boxcar2': {
                'use_boxcar2': False,
                'boxcar2_notify_onsnatch': False,
                'boxcar2_notify_ondownload': False,
                'boxcar2_accesstoken': '',
                'boxcar2_notify_onsubtitledownload': False
            },
            'FailedDownloads': {
                'use_failed_downloads': False,
                'delete_failed': False
            },
            'NMJ': {
                'nmj_host': '',
                'nmj_mount': '',
                'use_nmj': False,
                'nmj_database': ''
            },
            'Twitter': {
                'twitter_username': '',
                'use_twitter': False,
                'twitter_password': '',
                'twitter_notify_ondownload': False,
                'twitter_notify_onsubtitledownload': False,
                'twitter_notify_onsnatch': False,
                'twitter_prefix': 'SiCKRAGE',
                'twitter_dmto': '',
                'twitter_usedm': False
            },
            'Twilio': {
                'use_twilio': False,
                'twilio_notify_onsnatch': False,
                'twilio_notify_ondownload': False,
                'twilio_notify_onsubtitledownload': False,
                'twilio_phone_sid': '',
                'twilio_account_sid': '',
                'twilio_auth_token': '',
                'twilio_to_number': '',
            },
            'Subtitles': {
                'itasa_password': '',
                'opensubtitles_username': '',
                'subtitles_services_list': '',
                'subtitles_history': False,
                'legendastv_password': '',
                'subtitles_hearing_impaired': False,
                'addic7ed_password': '',
                'subtitles_languages': '',
                'embedded_subtitles_all': False,
                'subtitles_finder_frequency': 1,
                'subtitles_default': False,
                'subtitles_multi': True,
                'subtitles_services_enabled': '',
                'itasa_username': '',
                'subtitles_dir': '',
                'addic7ed_username': '',
                'opensubtitles_password': '',
                'subtitles_extra_scripts': '',
                'use_subtitles': False,
                'legendastv_username': ''
            },
            'ANIME': {
                'anime_split_home': False
            }
        }

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
            if self.UNPACK:
                sickrage.srCore.srLogger.info('Disabling UNPACK setting because no unrar is installed.')
                self.UNPACK = False

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
        self.AUTOPOSTPROCESSOR_FREQ = try_int(freq, self.DEFAULT_AUTOPOSTPROCESSOR_FREQ)

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
        self.DAILY_SEARCHER_FREQ = try_int(freq, self.DEFAULT_DAILY_SEARCHER_FREQ)
        sickrage.srCore.srScheduler.modify_job('DAILYSEARCHER',
                                               trigger=srIntervalTrigger(
                                                   **{'minutes': self.DAILY_SEARCHER_FREQ,
                                                      'min': self.MIN_DAILY_SEARCHER_FREQ}))

    def change_backlog_searcher_freq(self, freq):
        """
        Change frequency of backlog thread

        :param freq: New frequency
        """
        self.BACKLOG_SEARCHER_FREQ = try_int(freq, self.DEFAULT_BACKLOG_SEARCHER_FREQ)
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
        self.VERSION_UPDATER_FREQ = try_int(freq, self.DEFAULT_VERSION_UPDATE_FREQ)
        sickrage.srCore.srScheduler.modify_job('VERSIONUPDATER',
                                               trigger=srIntervalTrigger(
                                                   **{'hours': self.VERSION_UPDATER_FREQ,
                                                      'min': self.MIN_VERSION_UPDATER_FREQ}))

    def change_showupdate_hour(self, freq):
        """
        Change frequency of show updater thread

        :param freq: New frequency
        """
        self.SHOWUPDATE_HOUR = try_int(freq, self.DEFAULT_SHOWUPDATE_HOUR)
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
        self.SUBTITLE_SEARCHER_FREQ = try_int(freq, self.DEFAULT_SUBTITLE_SEARCHER_FREQ)
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

    def checkbox_to_value(self, option, value_on=True, value_off=False):
        """
        Turns checkbox option 'on' or 'true' to value_on (1)
        any other value returns value_off (0)
        """

        if isinstance(option, list):
            option = option[-1]
        if isinstance(option, six.string_types):
            option = six.text_type(option).strip().lower()

        if option in (True, 'on', 'true', value_on) or try_int(option) > 0:
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
    # check_setting_int                                                            #
    ################################################################################
    def check_setting_int(self, section, key, def_val=None, silent=True):
        def_val = def_val if def_val is not None else self.defaults[section][key]

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
    # check_setting_float                                                          #
    ################################################################################
    def check_setting_float(self, section, key, def_val=None, silent=True):
        def_val = def_val if def_val is not None else self.defaults[section][key]

        try:
            my_val = float(self.CONFIG_OBJ.get(section, {section: key}).get(key, def_val))
        except Exception:
            my_val = def_val

        if not silent:
            sickrage.srCore.srLogger.debug(section + " -> " + str(my_val))

        return my_val

    ################################################################################
    # check_setting_str                                                            #
    ################################################################################
    def check_setting_str(self, section, key, def_val=None, silent=True, censor=False):
        def_val = def_val if def_val is not None else self.defaults[section][key]

        my_val = self.CONFIG_OBJ.get(section, {section: key}).get(key, def_val)

        if censor or (section, key) in sickrage.srCore.srLogger.CENSORED_ITEMS:
            sickrage.srCore.srLogger.CENSORED_ITEMS[section, key] = my_val

        if not silent:
            sickrage.srCore.srLogger.debug(key + " -> " + my_val)

        return my_val

    ################################################################################
    # check_setting_pickle                                                           #
    ################################################################################
    def check_setting_pickle(self, section, key, def_val=None, silent=True):
        def_val = def_val if def_val is not None else self.defaults[section][key]

        try:
            my_val = pickle.loads(self.CONFIG_OBJ.get(section, {section: key}).get(key, def_val))
        except Exception:
            my_val = def_val

        if not silent:
            print(key + " -> " + my_val)

        return my_val

    ################################################################################
    # check_setting_bool                                                           #
    ################################################################################
    def check_setting_bool(self, section, key, def_val=None, silent=True):
        def_val = def_val if def_val is not None else self.defaults[section][key]

        try:
            my_val = self.checkbox_to_value(self.CONFIG_OBJ.get(section, {section: key}).get(key, def_val))
        except Exception:
            my_val = bool(def_val)

        if not silent:
            print(key + " -> " + my_val)

        return my_val

    def load(self, defaults=False):
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

        # use defaults
        if defaults: self.CONFIG_OBJ.clear()

        # decrypt settings
        self.ENCRYPTION_VERSION = self.check_setting_int('General', 'encryption_version')
        self.ENCRYPTION_SECRET = self.check_setting_str('General', 'encryption_secret', censor=True)
        self.CONFIG_OBJ.walk(self.decrypt)

        # migrate config
        self.CONFIG_OBJ = ConfigMigrator(self.CONFIG_OBJ).migrate_config()

        # GENERAL SETTINGS
        self.DEBUG = sickrage.DEBUG or self.check_setting_bool('General', 'debug')
        self.DEVELOPER = sickrage.DEVELOPER or self.check_setting_bool('General', 'developer')
        self.LAST_DB_COMPACT = self.check_setting_int('General', 'last_db_compact')
        self.LOG_NR = self.check_setting_int('General', 'log_nr')
        self.LOG_SIZE = self.check_setting_int('General', 'log_size')
        self.SOCKET_TIMEOUT = self.check_setting_int('General', 'socket_timeout')
        self.DEFAULT_PAGE = self.check_setting_str('General', 'default_page')
        self.PIP_PATH = self.check_setting_str('General', 'pip_path')
        self.GIT_PATH = self.check_setting_str('General', 'git_path')
        self.GIT_AUTOISSUES = self.check_setting_bool('General', 'git_autoissues')
        self.GIT_USERNAME = self.check_setting_str('General', 'git_username', censor=True)
        self.GIT_PASSWORD = self.check_setting_str('General', 'git_password', censor=True)
        self.GIT_NEWVER = self.check_setting_bool('General', 'git_newver')
        self.GIT_RESET = self.check_setting_bool('General', 'git_reset')
        self.WEB_PORT = self.check_setting_int('General', 'web_port')
        self.WEB_HOST = self.check_setting_str('General', 'web_host')
        self.WEB_IPV6 = self.check_setting_bool('General', 'web_ipv6')
        self.WEB_ROOT = self.check_setting_str('General', 'web_root').rstrip("/")
        self.WEB_LOG = self.check_setting_bool('General', 'web_log')
        self.WEB_USERNAME = self.check_setting_str('General', 'web_username', censor=True)
        self.WEB_PASSWORD = self.check_setting_str('General', 'web_password', censor=True)
        self.WEB_COOKIE_SECRET = self.check_setting_str('General', 'web_cookie_secret')
        self.WEB_USE_GZIP = self.check_setting_bool('General', 'web_use_gzip')
        self.SSL_VERIFY = self.check_setting_bool('General', 'ssl_verify')
        self.LAUNCH_BROWSER = self.check_setting_bool('General', 'launch_browser')
        self.INDEXER_DEFAULT_LANGUAGE = self.check_setting_str('General', 'indexerDefaultLang')
        self.EP_DEFAULT_DELETED_STATUS = self.check_setting_int('General', 'ep_default_deleted_status')
        self.DOWNLOAD_URL = self.check_setting_str('General', 'download_url')
        self.CPU_PRESET = self.check_setting_str('General', 'cpu_preset')
        self.ANON_REDIRECT = self.check_setting_str('General', 'anon_redirect')
        self.PROXY_SETTING = self.check_setting_str('General', 'proxy_setting')
        self.PROXY_INDEXERS = self.check_setting_bool('General', 'proxy_indexers')
        self.TRASH_REMOVE_SHOW = self.check_setting_bool('General', 'trash_remove_show')
        self.TRASH_ROTATE_LOGS = self.check_setting_bool('General', 'trash_rotate_logs')
        self.SORT_ARTICLE = self.check_setting_bool('General', 'sort_article')
        self.API_KEY = self.check_setting_str('General', 'api_key', censor=True)
        self.ENABLE_HTTPS = self.check_setting_bool('General', 'enable_https')
        self.HTTPS_CERT = self.check_setting_str('General', 'https_cert')
        self.HTTPS_KEY = self.check_setting_str('General', 'https_key')
        self.HANDLE_REVERSE_PROXY = self.check_setting_bool('General', 'handle_reverse_proxy')
        self.ROOT_DIRS = self.check_setting_str('General', 'root_dirs')
        self.QUALITY_DEFAULT = self.check_setting_int('General', 'quality_default')
        self.STATUS_DEFAULT = self.check_setting_int('General', 'status_default')
        self.STATUS_DEFAULT_AFTER = self.check_setting_int('General', 'status_default_after')
        self.VERSION_NOTIFY = self.check_setting_bool('General', 'version_notify')
        self.AUTO_UPDATE = self.check_setting_bool('General', 'auto_update')
        self.NOTIFY_ON_UPDATE = self.check_setting_bool('General', 'notify_on_update')
        self.NOTIFY_ON_LOGIN = self.check_setting_bool('General', 'notify_on_login')
        self.FLATTEN_FOLDERS_DEFAULT = self.check_setting_bool('General', 'flatten_folders_default')
        self.INDEXER_DEFAULT = self.check_setting_int('General', 'indexer_default')
        self.INDEXER_TIMEOUT = self.check_setting_int('General', 'indexer_timeout')
        self.ANIME_DEFAULT = self.check_setting_bool('General', 'anime_default')
        self.SCENE_DEFAULT = self.check_setting_bool('General', 'scene_default')
        self.ARCHIVE_DEFAULT = self.check_setting_bool('General', 'archive_default')
        self.NAMING_PATTERN = self.check_setting_str('General', 'naming_pattern')
        self.NAMING_ABD_PATTERN = self.check_setting_str('General', 'naming_abd_pattern')
        self.NAMING_CUSTOM_ABD = self.check_setting_bool('General', 'naming_custom_abd')
        self.NAMING_SPORTS_PATTERN = self.check_setting_str('General', 'naming_sports_pattern')
        self.NAMING_ANIME_PATTERN = self.check_setting_str('General', 'naming_anime_pattern')
        self.NAMING_ANIME = self.check_setting_int('General', 'naming_anime')
        self.NAMING_CUSTOM_SPORTS = self.check_setting_bool('General', 'naming_custom_sports')
        self.NAMING_CUSTOM_ANIME = self.check_setting_bool('General', 'naming_custom_anime')
        self.NAMING_MULTI_EP = self.check_setting_int('General', 'naming_multi_ep')
        self.NAMING_ANIME_MULTI_EP = self.check_setting_int('General', 'naming_anime_multi_ep')
        self.NAMING_STRIP_YEAR = self.check_setting_bool('General', 'naming_strip_year')
        self.USE_NZBS = self.check_setting_bool('General', 'use_nzbs')
        self.USE_TORRENTS = self.check_setting_bool('General', 'use_torrents')
        self.NZB_METHOD = self.check_setting_str('General', 'nzb_method')
        self.TORRENT_METHOD = self.check_setting_str('General', 'torrent_method')
        self.DOWNLOAD_PROPERS = self.check_setting_bool('General', 'download_propers')
        self.ENABLE_RSS_CACHE = self.check_setting_bool('General', 'enable_rss_cache')
        self.ENABLE_RSS_CACHE_VALID_SHOWS = self.check_setting_bool('General', 'enable_rss_cache_valid_shows')
        self.PROPER_SEARCHER_INTERVAL = self.check_setting_str('General', 'check_propers_interval')
        self.RANDOMIZE_PROVIDERS = self.check_setting_bool('General', 'randomize_providers')
        self.ALLOW_HIGH_PRIORITY = self.check_setting_bool('General', 'allow_high_priority')
        self.SKIP_REMOVED_FILES = self.check_setting_bool('General', 'skip_removed_files')
        self.USENET_RETENTION = self.check_setting_int('General', 'usenet_retention')
        self.DAILY_SEARCHER_FREQ = self.check_setting_int('General', 'dailysearch_frequency')
        self.BACKLOG_SEARCHER_FREQ = self.check_setting_int('General', 'backlog_frequency')
        self.VERSION_UPDATER_FREQ = self.check_setting_int('General', 'update_frequency')
        self.SHOWUPDATE_STALE = self.check_setting_bool('General', 'showupdate_stale')
        self.SHOWUPDATE_HOUR = self.check_setting_int('General', 'showupdate_hour')
        self.BACKLOG_DAYS = self.check_setting_int('General', 'backlog_days')
        self.AUTOPOSTPROCESSOR_FREQ = self.check_setting_int('General', 'autopostprocessor_frequency')
        self.TV_DOWNLOAD_DIR = self.check_setting_str('General', 'tv_download_dir')
        self.PROCESS_AUTOMATICALLY = self.check_setting_bool('General', 'process_automatically')
        self.NO_DELETE = self.check_setting_bool('General', 'no_delete')
        self.UNPACK = self.check_setting_bool('General', 'unpack')
        self.RENAME_EPISODES = self.check_setting_bool('General', 'rename_episodes')
        self.AIRDATE_EPISODES = self.check_setting_bool('General', 'airdate_episodes')
        self.FILE_TIMESTAMP_TIMEZONE = self.check_setting_str('General', 'file_timestamp_timezone')
        self.KEEP_PROCESSED_DIR = self.check_setting_bool('General', 'keep_processed_dir')
        self.PROCESS_METHOD = self.check_setting_str('General', 'process_method')
        self.DELRARCONTENTS = self.check_setting_bool('General', 'del_rar_contents')
        self.MOVE_ASSOCIATED_FILES = self.check_setting_bool('General', 'move_associated_files')
        self.POSTPONE_IF_SYNC_FILES = self.check_setting_bool('General', 'postpone_if_sync_files')
        self.SYNC_FILES = self.check_setting_str('General', 'sync_files')
        self.NFO_RENAME = self.check_setting_bool('General', 'nfo_rename')
        self.CREATE_MISSING_SHOW_DIRS = self.check_setting_bool('General', 'create_missing_show_dirs')
        self.ADD_SHOWS_WO_DIR = self.check_setting_bool('General', 'add_shows_wo_dir')
        self.REQUIRE_WORDS = self.check_setting_str('General', 'require_words')
        self.IGNORE_WORDS = self.check_setting_str('General', 'ignore_words')
        self.IGNORED_SUBS_LIST = self.check_setting_str('General', 'ignored_subs_list')
        self.CALENDAR_UNPROTECTED = self.check_setting_bool('General', 'calendar_unprotected')
        self.CALENDAR_ICONS = self.check_setting_bool('General', 'calendar_icons')
        self.NO_RESTART = self.check_setting_bool('General', 'no_restart')
        self.EXTRA_SCRIPTS = [x.strip() for x in self.check_setting_str('General', 'extra_scripts').split('|') if
                              x.strip()]
        self.USE_LISTVIEW = self.check_setting_bool('General', 'use_listview')
        self.DISPLAY_ALL_SEASONS = self.check_setting_bool('General', 'display_all_seasons')
        self.RANDOM_USER_AGENT = self.check_setting_bool('General', 'random_user_agent')

        # GUI SETTINGS
        self.GUI_NAME = self.check_setting_str('GUI', 'gui_name')
        self.THEME_NAME = self.check_setting_str('GUI', 'theme_name')
        self.FANART_BACKGROUND = self.check_setting_bool('GUI', 'fanart_background')
        self.FANART_BACKGROUND_OPACITY = self.check_setting_float('GUI', 'fanart_background_opacity')
        self.HOME_LAYOUT = self.check_setting_str('GUI', 'home_layout')
        self.HISTORY_LAYOUT = self.check_setting_str('GUI', 'history_layout')
        self.HISTORY_LIMIT = self.check_setting_str('GUI', 'history_limit')
        self.DISPLAY_SHOW_SPECIALS = self.check_setting_bool('GUI', 'display_show_specials')
        self.COMING_EPS_LAYOUT = self.check_setting_str('GUI', 'coming_eps_layout')
        self.COMING_EPS_DISPLAY_PAUSED = self.check_setting_bool('GUI', 'coming_eps_display_paused')
        self.COMING_EPS_SORT = self.check_setting_str('GUI', 'coming_eps_sort')
        self.COMING_EPS_MISSED_RANGE = self.check_setting_int('GUI', 'coming_eps_missed_range')
        self.FUZZY_DATING = self.check_setting_bool('GUI', 'fuzzy_dating')
        self.TRIM_ZERO = self.check_setting_bool('GUI', 'trim_zero')
        self.DATE_PRESET = self.check_setting_str('GUI', 'date_preset')
        self.TIME_PRESET_W_SECONDS = self.check_setting_str('GUI', 'time_preset')
        self.TIME_PRESET = self.TIME_PRESET_W_SECONDS.replace(":%S", "")
        self.TIMEZONE_DISPLAY = self.check_setting_str('GUI', 'timezone_display')
        self.POSTER_SORTBY = self.check_setting_str('GUI', 'poster_sortby')
        self.POSTER_SORTDIR = self.check_setting_int('GUI', 'poster_sortdir')
        self.FILTER_ROW = self.check_setting_bool('GUI', 'filter_row')

        # BLACKHOLE SETTINGS
        self.NZB_DIR = self.check_setting_str('Blackhole', 'nzb_dir')
        self.TORRENT_DIR = self.check_setting_str('Blackhole', 'torrent_dir')

        # NZBS SETTINGS
        self.NZBS = self.check_setting_bool('NZBs', 'nzbs')
        self.NZBS_UID = self.check_setting_str('NZBs', 'nzbs_uid')
        self.NZBS_HASH = self.check_setting_str('NZBs', 'nzbs_hash', censor=True)

        # NEWZBIN SETTINGS
        self.NEWZBIN = self.check_setting_bool('Newzbin', 'newzbin')
        self.NEWZBIN_USERNAME = self.check_setting_str('Newzbin', 'newzbin_username', censor=True)
        self.NEWZBIN_PASSWORD = self.check_setting_str('Newzbin', 'newzbin_password', censor=True)

        # SABNZBD SETTINGS
        self.SAB_USERNAME = self.check_setting_str('SABnzbd', 'sab_username', censor=True)
        self.SAB_PASSWORD = self.check_setting_str('SABnzbd', 'sab_password', censor=True)
        self.SAB_APIKEY = self.check_setting_str('SABnzbd', 'sab_apikey', censor=True)
        self.SAB_CATEGORY = self.check_setting_str('SABnzbd', 'sab_category')
        self.SAB_CATEGORY_BACKLOG = self.check_setting_str('SABnzbd', 'sab_category_backlog')
        self.SAB_CATEGORY_ANIME = self.check_setting_str('SABnzbd', 'sab_category_anime')
        self.SAB_CATEGORY_ANIME_BACKLOG = self.check_setting_str('SABnzbd', 'sab_category_anime_backlog')
        self.SAB_HOST = self.check_setting_str('SABnzbd', 'sab_host')
        self.SAB_FORCED = self.check_setting_bool('SABnzbd', 'sab_forced')

        # NZBGET SETTINGS
        self.NZBGET_USERNAME = self.check_setting_str('NZBget', 'nzbget_username', censor=True)
        self.NZBGET_PASSWORD = self.check_setting_str('NZBget', 'nzbget_password', censor=True)
        self.NZBGET_CATEGORY = self.check_setting_str('NZBget', 'nzbget_category')
        self.NZBGET_CATEGORY_BACKLOG = self.check_setting_str('NZBget', 'nzbget_category_backlog')
        self.NZBGET_CATEGORY_ANIME = self.check_setting_str('NZBget', 'nzbget_category_anime')
        self.NZBGET_CATEGORY_ANIME_BACKLOG = self.check_setting_str('NZBget', 'nzbget_category_anime_backlog')
        self.NZBGET_HOST = self.check_setting_str('NZBget', 'nzbget_host')
        self.NZBGET_USE_HTTPS = self.check_setting_bool('NZBget', 'nzbget_use_https')
        self.NZBGET_PRIORITY = self.check_setting_int('NZBget', 'nzbget_priority')

        # TORRENT SETTINGS
        self.TORRENT_USERNAME = self.check_setting_str('TORRENT', 'torrent_username', censor=True)
        self.TORRENT_PASSWORD = self.check_setting_str('TORRENT', 'torrent_password', censor=True)
        self.TORRENT_HOST = self.check_setting_str('TORRENT', 'torrent_host')
        self.TORRENT_PATH = self.check_setting_str('TORRENT', 'torrent_path')
        self.TORRENT_SEED_TIME = self.check_setting_int('TORRENT', 'torrent_seed_time')
        self.TORRENT_PAUSED = self.check_setting_bool('TORRENT', 'torrent_paused')
        self.TORRENT_HIGH_BANDWIDTH = self.check_setting_bool('TORRENT', 'torrent_high_bandwidth')
        self.TORRENT_LABEL = self.check_setting_str('TORRENT', 'torrent_label')
        self.TORRENT_LABEL_ANIME = self.check_setting_str('TORRENT', 'torrent_label_anime')
        self.TORRENT_VERIFY_CERT = self.check_setting_bool('TORRENT', 'torrent_verify_cert')
        self.TORRENT_RPCURL = self.check_setting_str('TORRENT', 'torrent_rpcurl')
        self.TORRENT_AUTH_TYPE = self.check_setting_str('TORRENT', 'torrent_auth_type')
        self.TORRENT_TRACKERS = self.check_setting_str('TORRENT', 'torrent_trackers')

        # KODI SETTINGS
        self.USE_KODI = self.check_setting_bool('KODI', 'use_kodi')
        self.KODI_ALWAYS_ON = self.check_setting_bool('KODI', 'kodi_always_on')
        self.KODI_NOTIFY_ONSNATCH = self.check_setting_bool('KODI', 'kodi_notify_onsnatch')
        self.KODI_NOTIFY_ONDOWNLOAD = self.check_setting_bool('KODI', 'kodi_notify_ondownload')
        self.KODI_NOTIFY_ONSUBTITLEDOWNLOAD = self.check_setting_bool('KODI', 'kodi_notify_onsubtitledownload')
        self.KODI_UPDATE_LIBRARY = self.check_setting_bool('KODI', 'kodi_update_library')
        self.KODI_UPDATE_FULL = self.check_setting_bool('KODI', 'kodi_update_full')
        self.KODI_UPDATE_ONLYFIRST = self.check_setting_bool('KODI', 'kodi_update_onlyfirst')
        self.KODI_HOST = self.check_setting_str('KODI', 'kodi_host')
        self.KODI_USERNAME = self.check_setting_str('KODI', 'kodi_username', censor=True)
        self.KODI_PASSWORD = self.check_setting_str('KODI', 'kodi_password', censor=True)

        # PLEX SETTINGS
        self.USE_PLEX = self.check_setting_bool('Plex', 'use_plex')
        self.PLEX_NOTIFY_ONSNATCH = self.check_setting_bool('Plex', 'plex_notify_onsnatch')
        self.PLEX_NOTIFY_ONDOWNLOAD = self.check_setting_bool('Plex', 'plex_notify_ondownload')
        self.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD = self.check_setting_bool('Plex', 'plex_notify_onsubtitledownload')
        self.PLEX_UPDATE_LIBRARY = self.check_setting_bool('Plex', 'plex_update_library')
        self.PLEX_SERVER_HOST = self.check_setting_str('Plex', 'plex_server_host')
        self.PLEX_SERVER_TOKEN = self.check_setting_str('Plex', 'plex_server_token', censor=True)
        self.PLEX_HOST = self.check_setting_str('Plex', 'plex_host')
        self.PLEX_USERNAME = self.check_setting_str('Plex', 'plex_username', censor=True)
        self.PLEX_PASSWORD = self.check_setting_str('Plex', 'plex_password', censor=True)
        self.USE_PLEX_CLIENT = self.check_setting_bool('Plex', 'use_plex_client')
        self.PLEX_CLIENT_USERNAME = self.check_setting_str('Plex', 'plex_client_username', censor=True)
        self.PLEX_CLIENT_PASSWORD = self.check_setting_str('Plex', 'plex_client_password', censor=True)

        # EMBY SETTINGS
        self.USE_EMBY = self.check_setting_bool('Emby', 'use_emby')
        self.EMBY_HOST = self.check_setting_str('Emby', 'emby_host')
        self.EMBY_APIKEY = self.check_setting_str('Emby', 'emby_apikey', censor=True)

        # GROWL SETTINGS
        self.USE_GROWL = self.check_setting_bool('Growl', 'use_growl')
        self.GROWL_NOTIFY_ONSNATCH = self.check_setting_bool('Growl', 'growl_notify_onsnatch')
        self.GROWL_NOTIFY_ONDOWNLOAD = self.check_setting_bool('Growl', 'growl_notify_ondownload')
        self.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD = self.check_setting_bool('Growl', 'growl_notify_onsubtitledownload')
        self.GROWL_HOST = self.check_setting_str('Growl', 'growl_host')
        self.GROWL_PASSWORD = self.check_setting_str('Growl', 'growl_password', censor=True)

        # FREEMOBILE SETTINGS
        self.USE_FREEMOBILE = self.check_setting_bool('FreeMobile', 'use_freemobile')
        self.FREEMOBILE_NOTIFY_ONSNATCH = self.check_setting_bool('FreeMobile', 'freemobile_notify_onsnatch')
        self.FREEMOBILE_NOTIFY_ONDOWNLOAD = self.check_setting_bool('FreeMobile', 'freemobile_notify_ondownload')
        self.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD = self.check_setting_bool('FreeMobile',
                                                                            'freemobile_notify_onsubtitledownload')
        self.FREEMOBILE_ID = self.check_setting_str('FreeMobile', 'freemobile_id')
        self.FREEMOBILE_APIKEY = self.check_setting_str('FreeMobile', 'freemobile_apikey', censor=True)

        # TELEGRAM SETTINGS
        self.USE_TELEGRAM = self.check_setting_bool('TELEGRAM', 'use_telegram')
        self.TELEGRAM_NOTIFY_ONSNATCH = self.check_setting_bool('TELEGRAM', 'telegram_notify_onsnatch')
        self.TELEGRAM_NOTIFY_ONDOWNLOAD = self.check_setting_bool('TELEGRAM', 'telegram_notify_ondownload')
        self.TELEGRAM_NOTIFY_ONSUBTITLEDOWNLOAD = self.check_setting_bool('TELEGRAM',
                                                                          'telegram_notify_onsubtitledownload')
        self.TELEGRAM_ID = self.check_setting_str('TELEGRAM', 'telegram_id')
        self.TELEGRAM_APIKEY = self.check_setting_str('TELEGRAM', 'telegram_apikey', censor=True)

        # PROWL SETTINGS
        self.USE_PROWL = self.check_setting_bool('Prowl', 'use_prowl')
        self.PROWL_NOTIFY_ONSNATCH = self.check_setting_bool('Prowl', 'prowl_notify_onsnatch')
        self.PROWL_NOTIFY_ONDOWNLOAD = self.check_setting_bool('Prowl', 'prowl_notify_ondownload')
        self.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD = self.check_setting_bool('Prowl', 'prowl_notify_onsubtitledownload')
        self.PROWL_API = self.check_setting_str('Prowl', 'prowl_api', censor=True)
        self.PROWL_PRIORITY = self.check_setting_str('Prowl', 'prowl_priority')

        # TWITTER SETTINGS
        self.USE_TWITTER = self.check_setting_bool('Twitter', 'use_twitter')
        self.TWITTER_NOTIFY_ONSNATCH = self.check_setting_bool('Twitter', 'twitter_notify_onsnatch')
        self.TWITTER_NOTIFY_ONDOWNLOAD = self.check_setting_bool('Twitter', 'twitter_notify_ondownload')
        self.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD = self.check_setting_bool('Twitter', 'twitter_notify_onsubtitledownload')
        self.TWITTER_USERNAME = self.check_setting_str('Twitter', 'twitter_username', censor=True)
        self.TWITTER_PASSWORD = self.check_setting_str('Twitter', 'twitter_password', censor=True)
        self.TWITTER_PREFIX = self.check_setting_str('Twitter', 'twitter_prefix', 'SiCKRAGE')
        self.TWITTER_DMTO = self.check_setting_str('Twitter', 'twitter_dmto')
        self.TWITTER_USEDM = self.check_setting_bool('Twitter', 'twitter_usedm')

        self.USE_TWILIO = self.check_setting_bool('Twilio', 'use_twilio')
        self.TWILIO_NOTIFY_ONSNATCH = self.check_setting_bool('Twilio', 'twilio_notify_onsnatch')
        self.TWILIO_NOTIFY_ONDOWNLOAD = self.check_setting_bool('Twilio', 'twilio_notify_ondownload')
        self.TWILIO_NOTIFY_ONSUBTITLEDOWNLOAD = self.check_setting_bool('Twilio', 'twilio_notify_onsubtitledownload')
        self.TWILIO_PHONE_SID = self.check_setting_str('Twilio', 'twilio_phone_sid', censor=True)
        self.TWILIO_ACCOUNT_SID = self.check_setting_str('Twilio', 'twilio_account_sid', censor=True)
        self.TWILIO_AUTH_TOKEN = self.check_setting_str('Twilio', 'twilio_auth_token', censor=True)
        self.TWILIO_TO_NUMBER = self.check_setting_str('Twilio', 'twilio_to_number', censor=True)

        self.USE_BOXCAR2 = self.check_setting_bool('Boxcar2', 'use_boxcar2')
        self.BOXCAR2_NOTIFY_ONSNATCH = self.check_setting_bool('Boxcar2', 'boxcar2_notify_onsnatch')
        self.BOXCAR2_NOTIFY_ONDOWNLOAD = self.check_setting_bool('Boxcar2', 'boxcar2_notify_ondownload')
        self.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD = self.check_setting_bool('Boxcar2', 'boxcar2_notify_onsubtitledownload')
        self.BOXCAR2_ACCESSTOKEN = self.check_setting_str('Boxcar2', 'boxcar2_accesstoken', censor=True)

        self.USE_PUSHOVER = self.check_setting_bool('Pushover', 'use_pushover')
        self.PUSHOVER_NOTIFY_ONSNATCH = self.check_setting_bool('Pushover', 'pushover_notify_onsnatch')
        self.PUSHOVER_NOTIFY_ONDOWNLOAD = self.check_setting_bool('Pushover', 'pushover_notify_ondownload')
        self.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD = self.check_setting_bool('Pushover',
                                                                          'pushover_notify_onsubtitledownload')
        self.PUSHOVER_USERKEY = self.check_setting_str('Pushover', 'pushover_userkey', censor=True)
        self.PUSHOVER_APIKEY = self.check_setting_str('Pushover', 'pushover_apikey', censor=True)
        self.PUSHOVER_DEVICE = self.check_setting_str('Pushover', 'pushover_device')
        self.PUSHOVER_SOUND = self.check_setting_str('Pushover', 'pushover_sound', 'pushover')

        self.USE_LIBNOTIFY = self.check_setting_bool('Libnotify', 'use_libnotify')
        self.LIBNOTIFY_NOTIFY_ONSNATCH = self.check_setting_bool('Libnotify', 'libnotify_notify_onsnatch')
        self.LIBNOTIFY_NOTIFY_ONDOWNLOAD = self.check_setting_bool('Libnotify', 'libnotify_notify_ondownload')
        self.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD = self.check_setting_bool('Libnotify',
                                                                           'libnotify_notify_onsubtitledownload')

        self.USE_NMJ = self.check_setting_bool('NMJ', 'use_nmj')
        self.NMJ_HOST = self.check_setting_str('NMJ', 'nmj_host')
        self.NMJ_DATABASE = self.check_setting_str('NMJ', 'nmj_database')
        self.NMJ_MOUNT = self.check_setting_str('NMJ', 'nmj_mount')

        self.USE_NMJv2 = self.check_setting_bool('NMJv2', 'use_nmjv2')
        self.NMJv2_HOST = self.check_setting_str('NMJv2', 'nmjv2_host')
        self.NMJv2_DATABASE = self.check_setting_str('NMJv2', 'nmjv2_database')
        self.NMJv2_DBLOC = self.check_setting_str('NMJv2', 'nmjv2_dbloc')

        self.USE_SYNOINDEX = self.check_setting_bool('Synology', 'use_synoindex')

        self.USE_SYNOLOGYNOTIFIER = self.check_setting_bool('SynologyNotifier', 'use_synologynotifier')
        self.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH = self.check_setting_bool('SynologyNotifier',
                                                                        'synologynotifier_notify_onsnatch')
        self.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD = self.check_setting_bool('SynologyNotifier',
                                                                          'synologynotifier_notify_ondownload')
        self.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD = self.check_setting_bool('SynologyNotifier',
                                                                                  'synologynotifier_notify_onsubtitledownload')

        self.THETVDB_APITOKEN = self.check_setting_str('theTVDB', 'thetvdb_apitoken', censor=True)

        self.USE_SLACK = self.check_setting_bool('Slack', 'use_slack')
        self.SLACK_NOTIFY_ONSNATCH = self.check_setting_bool('Slack', 'slack_notify_onsnatch')
        self.SLACK_NOTIFY_ONDOWNLOAD = self.check_setting_bool('Slack', 'slack_notify_ondownload')
        self.SLACK_NOTIFY_ONSUBTITLEDOWNLOAD = self.check_setting_bool('Slack', 'slack_notify_onsubtitledownload')
        self.SLACK_WEBHOOK = self.check_setting_str('Slack', 'slack_webhook')

        self.USE_DISCORD = self.check_setting_bool('Discord', 'use_discord')
        self.DISCORD_NOTIFY_ONSNATCH = self.check_setting_bool('Discord', 'discord_notify_onsnatch')
        self.DISCORD_NOTIFY_ONDOWNLOAD = self.check_setting_bool('Discord', 'discord_notify_ondownload')
        self.DISCORD_NOTIFY_ONSUBTITLEDOWNLOAD = self.check_setting_bool('Discord', 'discord_notify_onsubtitledownload')
        self.DISCORD_WEBHOOK = self.check_setting_str('Discord', 'discord_webhook')
        self.DISCORD_AVATAR_URL = self.check_setting_str('Discord', 'discord_avatar_url')
        self.DISCORD_NAME = self.check_setting_str('Discord', 'discord_name')
        self.DISCORD_TTS = self.check_setting_bool('Discord', 'discord_tts')

        self.USE_TRAKT = self.check_setting_bool('Trakt', 'use_trakt')
        self.TRAKT_USERNAME = self.check_setting_str('Trakt', 'trakt_username', censor=True)
        self.TRAKT_OAUTH_TOKEN = self.check_setting_pickle('Trakt', 'trakt_oauth_token')
        self.TRAKT_REMOVE_WATCHLIST = self.check_setting_bool('Trakt', 'trakt_remove_watchlist')
        self.TRAKT_REMOVE_SERIESLIST = self.check_setting_bool('Trakt', 'trakt_remove_serieslist')
        self.TRAKT_REMOVE_SHOW_FROM_SICKRAGE = self.check_setting_bool('Trakt', 'trakt_remove_show_from_sickrage')
        self.TRAKT_SYNC_WATCHLIST = self.check_setting_bool('Trakt', 'trakt_sync_watchlist')
        self.TRAKT_METHOD_ADD = self.check_setting_int('Trakt', 'trakt_method_add')
        self.TRAKT_START_PAUSED = self.check_setting_bool('Trakt', 'trakt_start_paused')
        self.TRAKT_USE_RECOMMENDED = self.check_setting_bool('Trakt', 'trakt_use_recommended')
        self.TRAKT_SYNC = self.check_setting_bool('Trakt', 'trakt_sync')
        self.TRAKT_SYNC_REMOVE = self.check_setting_bool('Trakt', 'trakt_sync_remove')
        self.TRAKT_DEFAULT_INDEXER = self.check_setting_int('Trakt', 'trakt_default_indexer')
        self.TRAKT_TIMEOUT = self.check_setting_int('Trakt', 'trakt_timeout')
        self.TRAKT_BLACKLIST_NAME = self.check_setting_str('Trakt', 'trakt_blacklist_name')

        self.USE_PYTIVO = self.check_setting_bool('pyTivo', 'use_pytivo')
        self.PYTIVO_NOTIFY_ONSNATCH = self.check_setting_bool('pyTivo', 'pytivo_notify_onsnatch')
        self.PYTIVO_NOTIFY_ONDOWNLOAD = self.check_setting_bool('pyTivo', 'pytivo_notify_ondownload')
        self.PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD = self.check_setting_bool('pyTivo', 'pytivo_notify_onsubtitledownload')
        self.PYTIVO_UPDATE_LIBRARY = self.check_setting_bool('pyTivo', 'pyTivo_update_library')
        self.PYTIVO_HOST = self.check_setting_str('pyTivo', 'pytivo_host')
        self.PYTIVO_SHARE_NAME = self.check_setting_str('pyTivo', 'pytivo_share_name')
        self.PYTIVO_TIVO_NAME = self.check_setting_str('pyTivo', 'pytivo_tivo_name')

        self.USE_NMA = self.check_setting_bool('NMA', 'use_nma')
        self.NMA_NOTIFY_ONSNATCH = self.check_setting_bool('NMA', 'nma_notify_onsnatch')
        self.NMA_NOTIFY_ONDOWNLOAD = self.check_setting_bool('NMA', 'nma_notify_ondownload')
        self.NMA_NOTIFY_ONSUBTITLEDOWNLOAD = self.check_setting_bool('NMA', 'nma_notify_onsubtitledownload')
        self.NMA_API = self.check_setting_str('NMA', 'nma_api', censor=True)
        self.NMA_PRIORITY = self.check_setting_str('NMA', 'nma_priority')

        self.USE_PUSHALOT = self.check_setting_bool('Pushalot', 'use_pushalot')
        self.PUSHALOT_NOTIFY_ONSNATCH = self.check_setting_bool('Pushalot', 'pushalot_notify_onsnatch')
        self.PUSHALOT_NOTIFY_ONDOWNLOAD = self.check_setting_bool('Pushalot', 'pushalot_notify_ondownload')
        self.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD = self.check_setting_bool('Pushalot',
                                                                          'pushalot_notify_onsubtitledownload')
        self.PUSHALOT_AUTHORIZATIONTOKEN = self.check_setting_str('Pushalot', 'pushalot_authorizationtoken',
                                                                  censor=True)

        self.USE_PUSHBULLET = self.check_setting_bool('Pushbullet', 'use_pushbullet')
        self.PUSHBULLET_NOTIFY_ONSNATCH = self.check_setting_bool('Pushbullet', 'pushbullet_notify_onsnatch')
        self.PUSHBULLET_NOTIFY_ONDOWNLOAD = self.check_setting_bool('Pushbullet', 'pushbullet_notify_ondownload')
        self.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD = self.check_setting_bool('Pushbullet',
                                                                            'pushbullet_notify_onsubtitledownload')
        self.PUSHBULLET_API = self.check_setting_str('Pushbullet', 'pushbullet_api', censor=True)
        self.PUSHBULLET_DEVICE = self.check_setting_str('Pushbullet', 'pushbullet_device')

        self.USE_EMAIL = self.check_setting_bool('Email', 'use_email')
        self.EMAIL_NOTIFY_ONSNATCH = self.check_setting_bool('Email', 'email_notify_onsnatch')
        self.EMAIL_NOTIFY_ONDOWNLOAD = self.check_setting_bool('Email', 'email_notify_ondownload')
        self.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD = self.check_setting_bool('Email', 'email_notify_onsubtitledownload')
        self.EMAIL_HOST = self.check_setting_str('Email', 'email_host')
        self.EMAIL_PORT = self.check_setting_int('Email', 'email_port')
        self.EMAIL_TLS = self.check_setting_bool('Email', 'email_tls')
        self.EMAIL_USER = self.check_setting_str('Email', 'email_user', censor=True)
        self.EMAIL_PASSWORD = self.check_setting_str('Email', 'email_password', censor=True)
        self.EMAIL_FROM = self.check_setting_str('Email', 'email_from')
        self.EMAIL_LIST = self.check_setting_str('Email', 'email_list')

        # SUBTITLE SETTINGS
        self.USE_SUBTITLES = self.check_setting_bool('Subtitles', 'use_subtitles')
        self.SUBTITLES_LANGUAGES = self.check_setting_str('Subtitles', 'subtitles_languages').split(',')
        self.SUBTITLES_DIR = self.check_setting_str('Subtitles', 'subtitles_dir')
        self.SUBTITLES_SERVICES_LIST = self.check_setting_str('Subtitles', 'subtitles_services_list').split(',')
        self.SUBTITLES_DEFAULT = self.check_setting_bool('Subtitles', 'subtitles_default')
        self.SUBTITLES_HISTORY = self.check_setting_bool('Subtitles', 'subtitles_history')
        self.SUBTITLES_HEARING_IMPAIRED = self.check_setting_bool('Subtitles', 'subtitles_hearing_impaired')
        self.EMBEDDED_SUBTITLES_ALL = self.check_setting_bool('Subtitles', 'embedded_subtitles_all')
        self.SUBTITLES_MULTI = self.check_setting_bool('Subtitles', 'subtitles_multi')
        self.SUBTITLES_SERVICES_ENABLED = [int(x) for x in
                                           self.check_setting_str('Subtitles', 'subtitles_services_enabled').split('|')
                                           if x]
        self.SUBTITLES_EXTRA_SCRIPTS = [x.strip() for x in
                                        self.check_setting_str('Subtitles', 'subtitles_extra_scripts').split('|') if
                                        x.strip()]
        self.ADDIC7ED_USER = self.check_setting_str('Subtitles', 'addic7ed_username', censor=True)
        self.ADDIC7ED_PASS = self.check_setting_str('Subtitles', 'addic7ed_password', censor=True)
        self.LEGENDASTV_USER = self.check_setting_str('Subtitles', 'legendastv_username', censor=True)
        self.LEGENDASTV_PASS = self.check_setting_str('Subtitles', 'legendastv_password', censor=True)
        self.ITASA_USER = self.check_setting_str('Subtitles', 'itasa_username', censor=True)
        self.ITASA_PASS = self.check_setting_str('Subtitles', 'itasa_password', censor=True)
        self.OPENSUBTITLES_USER = self.check_setting_str('Subtitles', 'opensubtitles_username', censor=True)
        self.OPENSUBTITLES_PASS = self.check_setting_str('Subtitles', 'opensubtitles_password', censor=True)
        self.SUBTITLE_SEARCHER_FREQ = self.check_setting_int('Subtitles', 'subtitles_finder_frequency')

        # FAILED DOWNLOAD SETTINGS
        self.USE_FAILED_DOWNLOADS = self.check_setting_bool('FailedDownloads', 'use_failed_downloads')
        self.DELETE_FAILED = self.check_setting_bool('FailedDownloads', 'delete_failed')

        # ANIDB SETTINGS
        self.USE_ANIDB = self.check_setting_bool('ANIDB', 'use_anidb')
        self.ANIDB_USERNAME = self.check_setting_str('ANIDB', 'anidb_username', censor=True)
        self.ANIDB_PASSWORD = self.check_setting_str('ANIDB', 'anidb_password', censor=True)
        self.ANIDB_USE_MYLIST = self.check_setting_bool('ANIDB', 'anidb_use_mylist')
        self.ANIME_SPLIT_HOME = self.check_setting_bool('ANIME', 'anime_split_home')

        self.QUALITY_SIZES = self.check_setting_pickle('Quality', 'sizes')

        self.CUSTOM_PROVIDERS = self.check_setting_str('Providers', 'custom_providers')

        sickrage.srCore.providersDict.load()
        for providerID, providerObj in sickrage.srCore.providersDict.all().items():
            providerSettings = self.check_setting_str('Providers', providerID, '') or {}
            for k, v in providerSettings.items():
                providerSettings[k] = autoType(v)

            [providerObj.__dict__.update({x: providerSettings[x]}) for x in
             set(providerObj.__dict__).intersection(providerSettings)]

        # order providers
        sickrage.srCore.providersDict.provider_order = self.check_setting_str('Providers', 'providers_order')

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

        new_config = ConfigObj(sickrage.CONFIG_FILE, indent_type='  ', encoding='utf8')
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
                'enable_rss_cache_valid_shows': int(self.ENABLE_RSS_CACHE_VALID_SHOWS),
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
                'notify_on_login': int(self.NOTIFY_ON_LOGIN),
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
            'TELEGRAM': {
                'use_telegram': int(self.USE_TELEGRAM),
                'telegram_notify_onsnatch': int(self.TELEGRAM_NOTIFY_ONSNATCH),
                'telegram_notify_ondownload': int(self.TELEGRAM_NOTIFY_ONDOWNLOAD),
                'telegram_notify_onsubtitledownload': int(self.TELEGRAM_NOTIFY_ONSUBTITLEDOWNLOAD),
                'telegram_id': self.TELEGRAM_ID,
                'telegram_apikey': self.TELEGRAM_APIKEY,
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
            'Twilio': {
                'use_twilio': int(self.USE_TWILIO),
                'twilio_notify_onsnatch': int(self.TWILIO_NOTIFY_ONSNATCH),
                'twilio_notify_ondownload': int(self.TWILIO_NOTIFY_ONDOWNLOAD),
                'twilio_notify_onsubtitledownload': int(self.TWILIO_NOTIFY_ONSUBTITLEDOWNLOAD),
                'twilio_phone_sid': self.TWILIO_PHONE_SID,
                'twilio_account_sid': self.TWILIO_ACCOUNT_SID,
                'twilio_auth_token': self.TWILIO_AUTH_TOKEN,
                'twilio_to_number': self.TWILIO_TO_NUMBER,
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
            'Slack': {
                'use_slack': int(self.USE_SLACK),
                'slack_notify_onsnatch': int(self.SLACK_NOTIFY_ONSNATCH),
                'slack_notify_ondownload': int(self.SLACK_NOTIFY_ONDOWNLOAD),
                'slack_notify_onsubtitledownload': int(self.SLACK_NOTIFY_ONSUBTITLEDOWNLOAD),
                'slack_webhook': self.SLACK_WEBHOOK
            },
            'Discord': {
                'use_discord': int(self.USE_DISCORD),
                'discord_notify_onsnatch': int(self.DISCORD_NOTIFY_ONSNATCH),
                'discord_notify_ondownload': int(self.DISCORD_NOTIFY_ONDOWNLOAD),
                'discord_notify_onsubtitledownload': int(self.DISCORD_NOTIFY_ONSUBTITLEDOWNLOAD),
                'discord_webhook': self.DISCORD_WEBHOOK,
                'discord_name': self.DISCORD_NAME,
                'discord_avatar_url': self.DISCORD_AVATAR_URL,
                'discord_tts': int(self.DISCORD_TTS)
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
