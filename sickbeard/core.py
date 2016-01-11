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

from __future__ import unicode_literals

import datetime
import logging
import os
import re
import shutil
import socket
import sys
import threading
import traceback
import webbrowser

import configobj
from attrdict import AttrDict

import auto_postprocessor
import sickbeard
from backlog_searcher import get_backlog_cycle_time, BacklogSearcher
from common import SD, WANTED, SKIPPED
from config import CheckSection, check_setting_int, check_setting_str
from config import ConfigMigrator
from daily_searcher import DailySearcher
from databases import mainDB, cache_db, failed_db
from db import DBConnection, sanityCheckDatabase, upgradeDatabase, restoreDB
from helpers import generateCookieSecret, encrypt, removetree, findCertainShow, makeDir
from indexers import indexer_api
from logger import SRLogger
from metadata import ps3, mediabrowser, get_metadata_generator_dict, wdtv, tivo, kodi_12plus, kodi, mede8er
from name_cache import nameCache
from naming import check_force_season_folders
from network_timezones import update_network_dict
from notifiers.boxcar import BoxcarNotifier
from notifiers.boxcar2 import Boxcar2Notifier
from notifiers.emailnotify import EmailNotifier
from notifiers.emby import EMBYNotifier
from notifiers.freemobile import FreeMobileNotifier
from notifiers.growl import GrowlNotifier
from notifiers.kodi import KODINotifier
from notifiers.libnotify import LibnotifyNotifier
from notifiers.nma import NMA_Notifier
from notifiers.nmj import NMJNotifier
from notifiers.nmjv2 import NMJv2Notifier
from notifiers.plex import PLEXNotifier
from notifiers.prowl import ProwlNotifier
from notifiers.pushalot import PushalotNotifier
from notifiers.pushbullet import PushbulletNotifier
from notifiers.pushover import PushoverNotifier
from notifiers.pytivo import pyTivoNotifier
from notifiers.synoindex import synoIndexNotifier
from notifiers.synologynotifier import synologyNotifier
from notifiers.trakt import TraktNotifier
from notifiers.tweet import TwitterNotifier
from proper_searcher import ProperSearcher
from providers import NewznabProvider, NZBProvider, GenericProvider, TorrentProvider
from providers import TorrentRssProvider
from scheduler import Scheduler, SRIntervalTrigger
from search_queue import SearchQueue
from show_queue import ShowQueue
from show_updater import ShowUpdater
from subtitle_searcher import SubtitleSearcher
from trakt_searcher import TraktSearcher
from tv import TVShow
from updater import Updater
from webserver import SRWebServer

def initialize(console_logging=True):
    if not sickbeard.INITIALIZED:
        with threading.Lock():
            # initialize notifiers
            sickbeard.NOTIFIERS = AttrDict(
                    libnotify=LibnotifyNotifier(),
                    kodi_notifier=KODINotifier(),
                    plex_notifier=PLEXNotifier(),
                    emby_notifier=EMBYNotifier(),
                    nmj_notifier=NMJNotifier(),
                    nmjv2_notifier=NMJv2Notifier(),
                    synoindex_notifier=synoIndexNotifier(),
                    synology_notifier=synologyNotifier(),
                    pytivo_notifier=pyTivoNotifier(),
                    growl_notifier=GrowlNotifier(),
                    prowl_notifier=ProwlNotifier(),
                    libnotify_notifier=LibnotifyNotifier(),
                    pushover_notifier=PushoverNotifier(),
                    boxcar_notifier=BoxcarNotifier(),
                    boxcar2_notifier=Boxcar2Notifier(),
                    nma_notifier=NMA_Notifier(),
                    pushalot_notifier=PushalotNotifier(),
                    pushbullet_notifier=PushbulletNotifier(),
                    freemobile_notifier=FreeMobileNotifier(),
                    twitter_notifier=TwitterNotifier(),
                    trakt_notifier=TraktNotifier(),
                    email_notifier=EmailNotifier(),
            )

            # Check if we need to perform a restore first
            os.chdir(sickbeard.DATA_DIR)
            restore_dir = os.path.join(sickbeard.DATA_DIR, 'restore')
            if os.path.exists(restore_dir):
                success = restoreDB(restore_dir, sickbeard.DATA_DIR)
                if console_logging:
                    sys.stdout.write(
                            "Restore: restoring DB and config.ini %s!\n" % ("FAILED", "SUCCESSFUL")[success])

            # init config file
            load_config(sickbeard.CONFIG_FILE, True)

            # init logger
            SRLogger.logNr = sickbeard.LOG_NR
            SRLogger.logSize = sickbeard.LOG_SIZE
            SRLogger.logFile = sickbeard.LOG_FILE
            SRLogger.debugLogging = sickbeard.DEBUG
            SRLogger.consoleLogging = console_logging

            SRLogger.fileLogging = True
            if not makeDir(sickbeard.LOG_DIR):
                sys.stderr.write("!!! No log folder, logging to screen only!\n")
                SRLogger.fileLogging = False

            SRLogger.initialize()

            # set indexerApi
            sickbeard.indexerApi = indexer_api.indexerApi

            # set socket timeout
            socket.setdefaulttimeout(sickbeard.SOCKET_TIMEOUT)

            # init updater
            sickbeard.UPDATER = Updater()

            # initialize the main SB database
            upgradeDatabase(DBConnection(), mainDB.InitialSchema)

            # initialize the cache database
            upgradeDatabase(DBConnection('cache.db'), cache_db.InitialSchema)

            # initialize the failed downloads database
            upgradeDatabase(DBConnection('failed.db'), failed_db.InitialSchema)

            # fix up any db problems
            sanityCheckDatabase(DBConnection(), mainDB.MainSanityCheck)

            if sickbeard.DEFAULT_PAGE not in ('home', 'schedule', 'history', 'news', 'IRC'):
                sickbeard.DEFAULT_PAGE = 'home'

            if not makeDir(sickbeard.CACHE_DIR):
                logging.error("!!! Creating local cache dir failed")
                sickbeard.CACHE_DIR = None

            # Check if we need to perform a restore of the cache folder
            try:
                restore_dir = os.path.join(sickbeard.DATA_DIR, 'restore')
                if os.path.exists(restore_dir) and os.path.exists(os.path.join(restore_dir, 'cache')):
                    def restore_cache(srcdir, dstdir):
                        def path_leaf(path):
                            head, tail = os.path.split(path)
                            return tail or os.path.basename(head)

                        try:
                            if os.path.isdir(dstdir):
                                bakfilename = '{0}-{1}'.format(path_leaf(dstdir),
                                                               datetime.datetime.strftime(datetime.date.now(),
                                                                                          '%Y%m%d_%H%M%S'))
                                shutil.move(dstdir, os.path.join(os.path.dirname(dstdir), bakfilename))

                            shutil.move(srcdir, dstdir)
                            logging.info("Restore: restoring cache successful")
                        except Exception as E:
                            logging.error("Restore: restoring cache failed: {0}".format(E))

                    restore_cache(os.path.join(restore_dir, 'cache'), sickbeard.CACHE_DIR)
            except Exception as e:
                logging.error("Restore: restoring cache failed: {0}".format(e))
            finally:
                if os.path.exists(os.path.join(sickbeard.DATA_DIR, 'restore')):
                    try:
                        removetree(os.path.join(sickbeard.DATA_DIR, 'restore'))
                    except Exception as e:
                        logging.error("Restore: Unable to remove the restore directory: {0}".format(e))

                    for cleanupDir in ['mako', 'sessions', 'indexers']:
                        try:
                            removetree(os.path.join(sickbeard.CACHE_DIR, cleanupDir))
                        except Exception as e:
                            logging.warning(
                                    "Restore: Unable to remove the cache/{0} directory: {1}".format(cleanupDir, e))

            if sickbeard.WEB_PORT < 21 or sickbeard.WEB_PORT > 65535:
                sickbeard.WEB_PORT = 8081

            if not sickbeard.WEB_COOKIE_SECRET:
                sickbeard.WEB_COOKIE_SECRET = generateCookieSecret()

            # attempt to help prevent users from breaking links by using a bad url
            if not sickbeard.ANON_REDIRECT.endswith('?'):
                sickbeard.ANON_REDIRECT = ''

            if not re.match(r'\d+\|[^|]+(?:\|[^|]+)*', sickbeard.ROOT_DIRS):
                sickbeard.ROOT_DIRS = ''

            sickbeard.NAMING_FORCE_FOLDERS = check_force_season_folders()
            if sickbeard.NZB_METHOD not in ('blackhole', 'sabnzbd', 'nzbget'):
                sickbeard.NZB_METHOD = 'blackhole'

            if not sickbeard.PROVIDER_ORDER:
                sickbeard.PROVIDER_ORDER = sickbeard.providersDict[GenericProvider.NZB].keys() + \
                                           sickbeard.providersDict[GenericProvider.TORRENT].keys()

            if sickbeard.TORRENT_METHOD not in (
                    'blackhole', 'utorrent', 'transmission', 'deluge', 'deluged', 'download_station', 'rtorrent',
                    'qbittorrent', 'mlnet'):
                sickbeard.TORRENT_METHOD = 'blackhole'

            if sickbeard.PROPER_SEARCHER_INTERVAL not in ('15m', '45m', '90m', '4h', 'daily'):
                sickbeard.PROPER_SEARCHER_INTERVAL = 'daily'

            if sickbeard.AUTOPOSTPROCESSOR_FREQ < sickbeard.MIN_AUTOPOSTPROCESSOR_FREQ:
                sickbeard.AUTOPOSTPROCESSOR_FREQ = sickbeard.MIN_AUTOPOSTPROCESSOR_FREQ

            if sickbeard.NAMECACHE_FREQ < sickbeard.MIN_NAMECACHE_FREQ:
                sickbeard.NAMECACHE_FREQ = sickbeard.MIN_NAMECACHE_FREQ

            if sickbeard.DAILY_SEARCHER_FREQ < sickbeard.MIN_DAILY_SEARCHER_FREQ:
                sickbeard.DAILY_SEARCHER_FREQ = sickbeard.MIN_DAILY_SEARCHER_FREQ

            sickbeard.MIN_BACKLOG_SEARCHER_FREQ = get_backlog_cycle_time()
            if sickbeard.BACKLOG_SEARCHER_FREQ < sickbeard.MIN_BACKLOG_SEARCHER_FREQ:
                sickbeard.BACKLOG_SEARCHER_FREQ = sickbeard.MIN_BACKLOG_SEARCHER_FREQ

            if sickbeard.UPDATER_FREQ < sickbeard.MIN_UPDATER_FREQ:
                sickbeard.UPDATER_FREQ = sickbeard.MIN_UPDATER_FREQ

            if sickbeard.SHOWUPDATE_HOUR > 23:
                sickbeard.SHOWUPDATE_HOUR = 0
            elif sickbeard.SHOWUPDATE_HOUR < 0:
                sickbeard.SHOWUPDATE_HOUR = 0

            if sickbeard.SUBTITLE_SEARCHER_FREQ < sickbeard.MIN_SUBTITLE_SEARCHER_FREQ:
                sickbeard.SUBTITLE_SEARCHER_FREQ = sickbeard.MIN_SUBTITLE_SEARCHER_FREQ

            sickbeard.NEWS_LATEST = sickbeard.NEWS_LAST_READ

            if sickbeard.SUBTITLES_LANGUAGES[0] == '':
                sickbeard.SUBTITLES_LANGUAGES = []

            sickbeard.TIME_PRESET = sickbeard.TIME_PRESET_W_SECONDS.replace(":%S", "")

            # initialize metadata_providers
            sickbeard.metadataProvideDict = get_metadata_generator_dict()
            for cur_metadata_tuple in [(sickbeard.METADATA_KODI, kodi),
                                       (sickbeard.METADATA_KODI_12PLUS, kodi_12plus),
                                       (sickbeard.METADATA_MEDIABROWSER, mediabrowser),
                                       (sickbeard.METADATA_PS3, ps3),
                                       (sickbeard.METADATA_WDTV, wdtv),
                                       (sickbeard.METADATA_TIVO, tivo),
                                       (sickbeard.METADATA_MEDE8ER, mede8er)]:
                (cur_metadata_config, cur_metadata_class) = cur_metadata_tuple
                tmp_provider = cur_metadata_class.metadata_class()
                tmp_provider.set_config(cur_metadata_config)

                sickbeard.metadataProvideDict[tmp_provider.name] = tmp_provider

            # init caches
            sickbeard.nameCache = nameCache()

            # init queues
            sickbeard.showQueue = ShowQueue()
            sickbeard.searchQueue = SearchQueue()

            # load data for shows from database
            sickbeard.showList = load_shows()

            # init searchers
            sickbeard.dailySearcher = DailySearcher()
            sickbeard.backlogSearcher = BacklogSearcher()
            sickbeard.properSearcher = ProperSearcher()
            sickbeard.traktSearcher = TraktSearcher()
            sickbeard.subtitleSearcher = SubtitleSearcher()

            # init scheduler
            sickbeard.SCHEDULER = Scheduler()

            # add version checker job to scheduler
            sickbeard.SCHEDULER.add_job(
                    sickbeard.UPDATER.run,
                    SRIntervalTrigger(
                            **{'hours': sickbeard.UPDATER_FREQ, 'min': sickbeard.MIN_UPDATER_FREQ}),
                    name="UPDATER",
                    id="UPDATER",
                    replace_existing=True
            )

            # add network timezones updater job to scheduler
            sickbeard.SCHEDULER.add_job(
                    update_network_dict,
                    SRIntervalTrigger(**{'days': 1}),
                    name="TZUPDATER",
                    id="TZUPDATER",
                    replace_existing=True
            )

            # add namecache updater job to scheduler
            sickbeard.SCHEDULER.add_job(
                    sickbeard.nameCache.run,
                    SRIntervalTrigger(
                            **{'minutes': sickbeard.NAMECACHE_FREQ, 'min': sickbeard.MIN_NAMECACHE_FREQ}),
                    name="NAMECACHE",
                    id="NAMECACHE",
                    replace_existing=True
            )

            # add show queue job to scheduler
            sickbeard.SCHEDULER.add_job(
                    sickbeard.showQueue.run,
                    SRIntervalTrigger(**{'seconds': 3}),
                    name="SHOWQUEUE",
                    id="SHOWQUEUE",
                    replace_existing=True
            )

            # add search queue job to scheduler
            sickbeard.SCHEDULER.add_job(
                    sickbeard.searchQueue.run,
                    SRIntervalTrigger(**{'seconds': 1}),
                    name="SEARCHQUEUE",
                    id="SEARCHQUEUE",
                    replace_existing=True
            )

            # add show updater job to scheduler
            sickbeard.SCHEDULER.add_job(
                    ShowUpdater().run,
                    SRIntervalTrigger(
                            **{'hours': 1,
                               'start_date': datetime.datetime.now().replace(hour=sickbeard.SHOWUPDATE_HOUR)}),
                    name="SHOWUPDATER",
                    id="SHOWUPDATER",
                    replace_existing=True
            )

            # add daily search job to scheduler
            sickbeard.SCHEDULER.add_job(
                    sickbeard.dailySearcher.run,
                    SRIntervalTrigger(
                            **{'minutes': sickbeard.DAILY_SEARCHER_FREQ, 'min': sickbeard.MIN_DAILY_SEARCHER_FREQ}),
                    name="DAILYSEARCHER",
                    id="DAILYSEARCHER",
                    replace_existing=True
            )

            # add backlog search job to scheduler
            sickbeard.SCHEDULER.add_job(
                    sickbeard.backlogSearcher.run,
                    SRIntervalTrigger(
                            **{'minutes': sickbeard.BACKLOG_SEARCHER_FREQ,
                               'min': sickbeard.MIN_BACKLOG_SEARCHER_FREQ}),
                    name="BACKLOG",
                    id="BACKLOG",
                    replace_existing=True
            )

            # add auto-postprocessing job to scheduler
            job = sickbeard.SCHEDULER.add_job(
                    auto_postprocessor.PostProcessor().run,
                    SRIntervalTrigger(**{'minutes': sickbeard.AUTOPOSTPROCESSOR_FREQ,
                                         'min': sickbeard.MIN_AUTOPOSTPROCESSOR_FREQ}),
                    name="POSTPROCESSOR",
                    id="POSTPROCESSOR",
                    replace_existing=True
            )
            (job.pause, job.resume)[sickbeard.PROCESS_AUTOMATICALLY]()

            # add find propers job to scheduler
            job = sickbeard.SCHEDULER.add_job(
                    sickbeard.properSearcher.run,
                    SRIntervalTrigger(**{
                        'minutes': {'15m': 15, '45m': 45, '90m': 90, '4h': 4 * 60, 'daily': 24 * 60}[
                            sickbeard.PROPER_SEARCHER_INTERVAL]}),
                    name="PROPERSEARCHER",
                    id="PROPERSEARCHER",
                    replace_existing=True
            )
            (job.pause, job.resume)[sickbeard.DOWNLOAD_PROPERS]()

            # add trakt.tv checker job to scheduler
            job = sickbeard.SCHEDULER.add_job(
                    sickbeard.traktSearcher.run,
                    SRIntervalTrigger(**{'hours': 1}),
                    name="TRAKTSEARCHER",
                    id="TRAKTSEARCHER",
                    replace_existing=True,
            )
            (job.pause, job.resume)[sickbeard.USE_TRAKT]()

            # add subtitles finder job to scheduler
            job = sickbeard.SCHEDULER.add_job(
                    sickbeard.subtitleSearcher.run,
                    SRIntervalTrigger(**{'hours': sickbeard.SUBTITLE_SEARCHER_FREQ}),
                    name="SUBTITLESEARCHER",
                    id="SUBTITLESEARCHER",
                    replace_existing=True
            )
            (job.pause, job.resume)[sickbeard.USE_SUBTITLES]()

            # initialize web server
            sickbeard.WEB_SERVER = SRWebServer(**{
                'port': int(sickbeard.WEB_PORT),
                'host': sickbeard.WEB_HOST,
                'data_root': sickbeard.DATA_DIR,
                'gui_root': sickbeard.GUI_DIR,
                'web_root': sickbeard.WEB_ROOT,
                'log_dir': sickbeard.WEB_LOG or sickbeard.LOG_DIR,
                'username': sickbeard.WEB_USERNAME,
                'password': sickbeard.WEB_PASSWORD,
                'enable_https': sickbeard.ENABLE_HTTPS,
                'handle_reverse_proxy': sickbeard.HANDLE_REVERSE_PROXY,
                'https_cert': os.path.join(sickbeard.PROG_DIR, sickbeard.HTTPS_CERT),
                'https_key': os.path.join(sickbeard.PROG_DIR, sickbeard.HTTPS_KEY),
                'daemonize': sickbeard.DAEMONIZE,
                'pidfile': sickbeard.PIDFILE,
                'stop_timeout': 3,
                'nolaunch': sickbeard.WEB_NOLAUNCH
            })

            sickbeard.INITIALIZED = True
            return True


def start():
    logging.info("Starting SiCKRAGE:[{}] CONFIG:[{}]".format(sickbeard.GIT_BRANCH, sickbeard.CONFIG_FILE))

    if sickbeard.INITIALIZED and not sickbeard.STARTED:
        with threading.Lock():
            # start scheduler
            logging.info("Starting SiCKRAGE scheduler service")
            sickbeard.SCHEDULER.start()

            # Launch browser
            if sickbeard.LAUNCH_BROWSER and not any([sickbeard.WEB_NOLAUNCH, sickbeard.DAEMONIZE]):
                launch_browser(('http', 'https')[sickbeard.ENABLE_HTTPS], sickbeard.WEB_PORT,
                               sickbeard.WEB_ROOT)

            sickbeard.STARTED = True
            return True


def halt():
    if sickbeard.INITIALIZED and sickbeard.STARTED:
        with threading.Lock():
            logging.info("Aborting all threads")

            # shutdown scheduler
            logging.info("Shutting down scheduler service")
            sickbeard.SCHEDULER.shutdown()

            if sickbeard.ADBA_CONNECTION:
                logging.info("Loggging out ANIDB connection")
                sickbeard.ADBA_CONNECTION.logout()

            sickbeard.STARTED = False
            return True


def load_shows():
    """
    Populates the showlist with shows from the database
    """

    showlist = []
    for sqlShow in DBConnection().select("SELECT * FROM tv_shows"):
        try:
            curshow = TVShow(int(sqlShow[b"indexer"]), int(sqlShow[b"indexer_id"]))
            logging.debug("Loading data for show: [{}]".format(curshow.name))
            sickbeard.nameCache.buildNameCache(curshow)
            curshow.nextEpisode()
            showlist += [curshow]
        except Exception as e:
            logging.error("There was an error creating the show in {}: {}".format(sqlShow[b"location"], e))
            logging.debug(traceback.format_exc())
            continue

    return showlist


def saveall():
    # write all shows
    logging.info("Saving all shows to the database")
    for show in sickbeard.showList:
        show.saveToDB()

    # save config
    logging.info("Saving config file to disk")
    save_config(sickbeard.CONFIG_FILE)


def load_config(cfgfile, defaults=False):
    # load config and use defaults if requested
    if not os.path.isfile(cfgfile):
        if not defaults:
            raise configobj.ConfigObjError
        cfgobj = configobj.ConfigObj(cfgfile)
    else:
        cfgobj = ConfigMigrator(configobj.ConfigObj(cfgfile)).migrate_config()

    # config sanity check
    CheckSection(cfgobj, 'General')
    CheckSection(cfgobj, 'Blackhole')
    CheckSection(cfgobj, 'Newzbin')
    CheckSection(cfgobj, 'SABnzbd')
    CheckSection(cfgobj, 'NZBget')
    CheckSection(cfgobj, 'KODI')
    CheckSection(cfgobj, 'PLEX')
    CheckSection(cfgobj, 'Emby')
    CheckSection(cfgobj, 'Growl')
    CheckSection(cfgobj, 'Prowl')
    CheckSection(cfgobj, 'Twitter')
    CheckSection(cfgobj, 'Boxcar')
    CheckSection(cfgobj, 'Boxcar2')
    CheckSection(cfgobj, 'NMJ')
    CheckSection(cfgobj, 'NMJv2')
    CheckSection(cfgobj, 'Synology')
    CheckSection(cfgobj, 'SynologyNotifier')
    CheckSection(cfgobj, 'pyTivo')
    CheckSection(cfgobj, 'NMA')
    CheckSection(cfgobj, 'Pushalot')
    CheckSection(cfgobj, 'Pushbullet')
    CheckSection(cfgobj, 'Subtitles')
    CheckSection(cfgobj, 'pyTivo')
    CheckSection(cfgobj, 'theTVDB')
    CheckSection(cfgobj, 'Trakt')

    # Need to be before any passwords
    sickbeard.ENCRYPTION_VERSION = check_setting_int(
            cfgobj, 'General', 'encryption_version', 0
    )

    sickbeard.ENCRYPTION_SECRET = check_setting_str(
            cfgobj, 'General', 'encryption_secret', generateCookieSecret(), censor_log=True
    )

    sickbeard.DEBUG = bool(check_setting_int(cfgobj, 'General', 'debug', 0))
    sickbeard.DEVELOPER = bool(check_setting_int(cfgobj, 'General', 'developer', 0))

    # logging settings
    sickbeard.LOG_DIR = os.path.normpath(
            os.path.join(sickbeard.DATA_DIR, check_setting_str(cfgobj, 'General', 'log_dir', 'Logs'))
    )

    sickbeard.LOG_NR = check_setting_int(cfgobj, 'General', 'log_nr', 5)
    sickbeard.LOG_SIZE = check_setting_int(cfgobj, 'General', 'log_size', 1048576)

    sickbeard.LOG_FILE = check_setting_str(
            cfgobj, 'General', 'log_file', os.path.join(sickbeard.LOG_DIR, 'sickrage.log')
    )

    # misc settings
    sickbeard.GUI_NAME = check_setting_str(cfgobj, 'GUI', 'gui_name', 'slick')
    sickbeard.GUI_DIR = os.path.join(sickbeard.PROG_DIR, 'gui', sickbeard.GUI_NAME)
    sickbeard.THEME_NAME = check_setting_str(cfgobj, 'GUI', 'theme_name', 'dark')
    sickbeard.SOCKET_TIMEOUT = check_setting_int(cfgobj, 'General', 'socket_timeout', 30)

    sickbeard.DEFAULT_PAGE = check_setting_str(cfgobj, 'General', 'default_page', 'home')

    # git settings
    sickbeard.GIT_REMOTE_URL = check_setting_str(
            cfgobj, 'General', 'git_remote_url',
            'https://github.com/{}/{}.git'.format(sickbeard.GIT_ORG, sickbeard.GIT_REPO)
    )
    sickbeard.GIT_PATH = check_setting_str(cfgobj, 'General', 'git_path', '')
    sickbeard.GIT_AUTOISSUES = bool(check_setting_int(cfgobj, 'General', 'git_autoissues', 0))
    sickbeard.GIT_USERNAME = check_setting_str(cfgobj, 'General', 'git_username', '')
    sickbeard.GIT_PASSWORD = check_setting_str(cfgobj, 'General', 'git_password', '', censor_log=True)
    sickbeard.GIT_NEWVER = bool(check_setting_int(cfgobj, 'General', 'git_newver', 0))
    sickbeard.GIT_RESET = bool(check_setting_int(cfgobj, 'General', 'git_reset', 1))
    sickbeard.GIT_BRANCH = check_setting_str(cfgobj, 'General', 'branch', '')
    sickbeard.GIT_REMOTE = check_setting_str(cfgobj, 'General', 'git_remote', 'origin')
    sickbeard.CUR_COMMIT_HASH = check_setting_str(cfgobj, 'General', 'cur_commit_hash', '')
    sickbeard.CUR_COMMIT_BRANCH = check_setting_str(cfgobj, 'General', 'cur_commit_branch', '')

    # cache settings
    sickbeard.CACHE_DIR = check_setting_str(cfgobj, 'General', 'cache_dir', 'cache')
    if not os.path.isabs(sickbeard.CACHE_DIR):
        sickbeard.CACHE_DIR = os.path.join(sickbeard.DATA_DIR, sickbeard.CACHE_DIR)

    # web settings
    sickbeard.WEB_PORT = check_setting_int(cfgobj, 'General', 'web_port', 8081)
    sickbeard.WEB_HOST = check_setting_str(cfgobj, 'General', 'web_host', '0.0.0.0')
    sickbeard.WEB_IPV6 = bool(check_setting_int(cfgobj, 'General', 'web_ipv6', 0))
    sickbeard.WEB_ROOT = check_setting_str(cfgobj, 'General', 'web_root', '').rstrip("/")
    sickbeard.WEB_LOG = bool(check_setting_int(cfgobj, 'General', 'web_log', 0))
    sickbeard.WEB_USERNAME = check_setting_str(cfgobj, 'General', 'web_username', '', censor_log=True)
    sickbeard.WEB_PASSWORD = check_setting_str(cfgobj, 'General', 'web_password', '', censor_log=True)
    sickbeard.WEB_COOKIE_SECRET = check_setting_str(
            cfgobj, 'General', 'web_cookie_secret', generateCookieSecret(), censor_log=True
    )
    sickbeard.WEB_USE_GZIP = bool(check_setting_int(cfgobj, 'General', 'web_use_gzip', 1))

    sickbeard.SSL_VERIFY = bool(check_setting_int(cfgobj, 'General', 'ssl_verify', 1))
    sickbeard.LAUNCH_BROWSER = bool(check_setting_int(cfgobj, 'General', 'launch_browser', 1))
    sickbeard.INDEXER_DEFAULT_LANGUAGE = check_setting_str(cfgobj, 'General', 'indexerDefaultLang', 'en')
    sickbeard.EP_DEFAULT_DELETED_STATUS = check_setting_int(cfgobj, 'General', 'ep_default_deleted_status', 6)
    sickbeard.DOWNLOAD_URL = check_setting_str(cfgobj, 'General', 'download_url', "")
    sickbeard.LOCALHOST_IP = check_setting_str(cfgobj, 'General', 'localhost_ip', '')
    sickbeard.CPU_PRESET = check_setting_str(cfgobj, 'General', 'cpu_preset', 'NORMAL')
    sickbeard.ANON_REDIRECT = check_setting_str(cfgobj, 'General', 'anon_redirect', 'http://dereferer.org/?')
    sickbeard.PROXY_SETTING = check_setting_str(cfgobj, 'General', 'proxy_setting', '')
    sickbeard.PROXY_INDEXERS = bool(check_setting_int(cfgobj, 'General', 'proxy_indexers', 1))
    sickbeard.TRASH_REMOVE_SHOW = bool(check_setting_int(cfgobj, 'General', 'trash_remove_show', 0))
    sickbeard.TRASH_ROTATE_LOGS = bool(check_setting_int(cfgobj, 'General', 'trash_rotate_logs', 0))
    sickbeard.SORT_ARTICLE = bool(check_setting_int(cfgobj, 'General', 'sort_article', 0))
    sickbeard.API_KEY = check_setting_str(cfgobj, 'General', 'api_key', '', censor_log=True)
    sickbeard.ENABLE_HTTPS = bool(check_setting_int(cfgobj, 'General', 'enable_https', 0))
    sickbeard.HTTPS_CERT = check_setting_str(cfgobj, 'General', 'https_cert', 'server.crt')
    sickbeard.HTTPS_KEY = check_setting_str(cfgobj, 'General', 'https_key', 'server.key')
    sickbeard.HANDLE_REVERSE_PROXY = bool(check_setting_int(cfgobj, 'General', 'handle_reverse_proxy', 0))
    sickbeard.NEWS_LAST_READ = check_setting_str(cfgobj, 'General', 'news_last_read', '1970-01-01')

    # show settings
    sickbeard.ROOT_DIRS = check_setting_str(cfgobj, 'General', 'root_dirs', '')
    sickbeard.QUALITY_DEFAULT = check_setting_int(cfgobj, 'General', 'quality_default', SD)
    sickbeard.STATUS_DEFAULT = check_setting_int(cfgobj, 'General', 'status_default', SKIPPED)
    sickbeard.STATUS_DEFAULT_AFTER = check_setting_int(cfgobj, 'General', 'status_default_after', WANTED)
    sickbeard.VERSION_NOTIFY = bool(check_setting_int(cfgobj, 'General', 'version_notify', 1))
    sickbeard.AUTO_UPDATE = bool(check_setting_int(cfgobj, 'General', 'auto_update', 0))
    sickbeard.NOTIFY_ON_UPDATE = bool(check_setting_int(cfgobj, 'General', 'notify_on_update', 1))
    sickbeard.FLATTEN_FOLDERS_DEFAULT = bool(check_setting_int(cfgobj, 'General', 'flatten_folders_default', 0))
    sickbeard.INDEXER_DEFAULT = check_setting_int(cfgobj, 'General', 'indexer_default', 0)
    sickbeard.INDEXER_TIMEOUT = check_setting_int(cfgobj, 'General', 'indexer_timeout', 20)
    sickbeard.ANIME_DEFAULT = bool(check_setting_int(cfgobj, 'General', 'anime_default', 0))
    sickbeard.SCENE_DEFAULT = bool(check_setting_int(cfgobj, 'General', 'scene_default', 0))
    sickbeard.ARCHIVE_DEFAULT = bool(check_setting_int(cfgobj, 'General', 'archive_default', 0))

    # naming settings
    sickbeard.NAMING_PATTERN = check_setting_str(cfgobj, 'General', 'naming_pattern',
                                                 'Season %0S/%SN - S%0SE%0E - %EN')
    sickbeard.NAMING_ABD_PATTERN = check_setting_str(cfgobj, 'General', 'naming_abd_pattern', '%SN - %A.D - %EN')
    sickbeard.NAMING_CUSTOM_ABD = bool(check_setting_int(cfgobj, 'General', 'naming_custom_abd', 0))
    sickbeard.NAMING_SPORTS_PATTERN = check_setting_str(cfgobj, 'General', 'naming_sports_pattern',
                                                        '%SN - %A-D - %EN')
    sickbeard.NAMING_ANIME_PATTERN = check_setting_str(cfgobj, 'General', 'naming_anime_pattern',
                                                       'Season %0S/%SN - S%0SE%0E - %EN')
    sickbeard.NAMING_ANIME = check_setting_int(cfgobj, 'General', 'naming_anime', 3)
    sickbeard.NAMING_CUSTOM_SPORTS = bool(check_setting_int(cfgobj, 'General', 'naming_custom_sports', 0))
    sickbeard.NAMING_CUSTOM_ANIME = bool(check_setting_int(cfgobj, 'General', 'naming_custom_anime', 0))
    sickbeard.NAMING_MULTI_EP = check_setting_int(cfgobj, 'General', 'naming_multi_ep', 1)
    sickbeard.NAMING_ANIME_MULTI_EP = check_setting_int(cfgobj, 'General', 'naming_anime_multi_ep', 1)
    sickbeard.NAMING_STRIP_YEAR = bool(check_setting_int(cfgobj, 'General', 'naming_strip_year', 0))

    # provider settings
    sickbeard.USE_NZBS = bool(check_setting_int(cfgobj, 'General', 'use_nzbs', 0))
    sickbeard.USE_TORRENTS = bool(check_setting_int(cfgobj, 'General', 'use_torrents', 1))
    sickbeard.NZB_METHOD = check_setting_str(cfgobj, 'General', 'nzb_method', 'blackhole')
    sickbeard.TORRENT_METHOD = check_setting_str(cfgobj, 'General', 'torrent_method', 'blackhole')
    sickbeard.DOWNLOAD_PROPERS = bool(check_setting_int(cfgobj, 'General', 'download_propers', 1))
    sickbeard.PROPER_SEARCHER_INTERVAL = check_setting_str(cfgobj, 'General', 'check_propers_interval', 'daily')
    sickbeard.RANDOMIZE_PROVIDERS = bool(check_setting_int(cfgobj, 'General', 'randomize_providers', 0))
    sickbeard.ALLOW_HIGH_PRIORITY = bool(check_setting_int(cfgobj, 'General', 'allow_high_priority', 1))
    sickbeard.SKIP_REMOVED_FILES = bool(check_setting_int(cfgobj, 'General', 'skip_removed_files', 0))
    sickbeard.USENET_RETENTION = check_setting_int(cfgobj, 'General', 'usenet_retention', 500)

    # scheduler settings
    sickbeard.AUTOPOSTPROCESSOR_FREQ = check_setting_int(
            cfgobj, 'General', 'autopostprocessor_frequency', sickbeard.DEFAULT_AUTOPOSTPROCESSOR_FREQ
    )

    sickbeard.SUBTITLE_SEARCHER_FREQ = check_setting_int(
            cfgobj, 'Subtitles', 'subtitles_finder_frequency', sickbeard.DEFAULT_SUBTITLE_SEARCHER_FREQ
    )

    sickbeard.NAMECACHE_FREQ = check_setting_int(cfgobj, 'General', 'namecache_frequency',
                                                 sickbeard.DEFAULT_NAMECACHE_FREQ)
    sickbeard.DAILY_SEARCHER_FREQ = check_setting_int(cfgobj, 'General', 'dailysearch_frequency',
                                                      sickbeard.DEFAULT_DAILY_SEARCHER_FREQ)
    sickbeard.BACKLOG_SEARCHER_FREQ = check_setting_int(cfgobj, 'General', 'backlog_frequency',
                                                        sickbeard.DEFAULT_BACKLOG_SEARCHER_FREQ)
    sickbeard.UPDATER_FREQ = check_setting_int(cfgobj, 'General', 'update_frequency', sickbeard.DEFAULT_UPDATE_FREQ)
    sickbeard.SHOWUPDATE_HOUR = check_setting_int(cfgobj, 'General', 'showupdate_hour',
                                                  sickbeard.DEFAULT_SHOWUPDATE_HOUR)
    sickbeard.BACKLOG_DAYS = check_setting_int(cfgobj, 'General', 'backlog_days', 7)

    sickbeard.NZB_DIR = check_setting_str(cfgobj, 'Blackhole', 'nzb_dir', '')
    sickbeard.TORRENT_DIR = check_setting_str(cfgobj, 'Blackhole', 'torrent_dir', '')

    sickbeard.TV_DOWNLOAD_DIR = check_setting_str(cfgobj, 'General', 'tv_download_dir', '')
    sickbeard.PROCESS_AUTOMATICALLY = bool(check_setting_int(cfgobj, 'General', 'process_automatically', 0))
    sickbeard.NO_DELETE = bool(check_setting_int(cfgobj, 'General', 'no_delete', 0))
    sickbeard.UNPACK = bool(check_setting_int(cfgobj, 'General', 'unpack', 0))
    sickbeard.RENAME_EPISODES = bool(check_setting_int(cfgobj, 'General', 'rename_episodes', 1))
    sickbeard.AIRDATE_EPISODES = bool(check_setting_int(cfgobj, 'General', 'airdate_episodes', 0))
    sickbeard.FILE_TIMESTAMP_TIMEZONE = check_setting_str(cfgobj, 'General', 'file_timestamp_timezone', 'network')
    sickbeard.KEEP_PROCESSED_DIR = bool(check_setting_int(cfgobj, 'General', 'keep_processed_dir', 1))
    sickbeard.PROCESS_METHOD = check_setting_str(cfgobj, 'General', 'process_method',
                                                 'copy' if sickbeard.KEEP_PROCESSED_DIR else 'move')
    sickbeard.DELRARCONTENTS = bool(check_setting_int(cfgobj, 'General', 'del_rar_contents', 0))
    sickbeard.MOVE_ASSOCIATED_FILES = bool(check_setting_int(cfgobj, 'General', 'move_associated_files', 0))
    sickbeard.POSTPONE_IF_SYNC_FILES = bool(check_setting_int(cfgobj, 'General', 'postpone_if_sync_files', 1))
    sickbeard.SYNC_FILES = check_setting_str(cfgobj, 'General', 'sync_files', '!sync,lftp-pget-status,part,bts,!qb')
    sickbeard.NFO_RENAME = bool(check_setting_int(cfgobj, 'General', 'nfo_rename', 1))
    sickbeard.CREATE_MISSING_SHOW_DIRS = bool(check_setting_int(cfgobj, 'General', 'create_missing_show_dirs', 0))
    sickbeard.ADD_SHOWS_WO_DIR = bool(check_setting_int(cfgobj, 'General', 'add_shows_wo_dir', 0))

    sickbeard.NZBS = bool(check_setting_int(cfgobj, 'NZBs', 'nzbs', 0))
    sickbeard.NZBS_UID = check_setting_str(cfgobj, 'NZBs', 'nzbs_uid', '', censor_log=True)
    sickbeard.NZBS_HASH = check_setting_str(cfgobj, 'NZBs', 'nzbs_hash', '', censor_log=True)

    sickbeard.NEWZBIN = bool(check_setting_int(cfgobj, 'Newzbin', 'newzbin', 0))
    sickbeard.NEWZBIN_USERNAME = check_setting_str(cfgobj, 'Newzbin', 'newzbin_username', '', censor_log=True)
    sickbeard.NEWZBIN_PASSWORD = check_setting_str(cfgobj, 'Newzbin', 'newzbin_password', '', censor_log=True)

    sickbeard.SAB_USERNAME = check_setting_str(cfgobj, 'SABnzbd', 'sab_username', '', censor_log=True)
    sickbeard.SAB_PASSWORD = check_setting_str(cfgobj, 'SABnzbd', 'sab_password', '', censor_log=True)
    sickbeard.SAB_APIKEY = check_setting_str(cfgobj, 'SABnzbd', 'sab_apikey', '', censor_log=True)
    sickbeard.SAB_CATEGORY = check_setting_str(cfgobj, 'SABnzbd', 'sab_category', 'tv')
    sickbeard.SAB_CATEGORY_BACKLOG = check_setting_str(cfgobj, 'SABnzbd', 'sab_category_backlog',
                                                       sickbeard.SAB_CATEGORY)
    sickbeard.SAB_CATEGORY_ANIME = check_setting_str(cfgobj, 'SABnzbd', 'sab_category_anime', 'anime')
    sickbeard.SAB_CATEGORY_ANIME_BACKLOG = check_setting_str(cfgobj, 'SABnzbd', 'sab_category_anime_backlog',
                                                             sickbeard.SAB_CATEGORY_ANIME)
    sickbeard.SAB_HOST = check_setting_str(cfgobj, 'SABnzbd', 'sab_host', '')
    sickbeard.SAB_FORCED = bool(check_setting_int(cfgobj, 'SABnzbd', 'sab_forced', 0))

    sickbeard.NZBGET_USERNAME = check_setting_str(cfgobj, 'NZBget', 'nzbget_username', 'nzbget', censor_log=True)
    sickbeard.NZBGET_PASSWORD = check_setting_str(cfgobj, 'NZBget', 'nzbget_password', 'tegbzn6789',
                                                  censor_log=True)
    sickbeard.NZBGET_CATEGORY = check_setting_str(cfgobj, 'NZBget', 'nzbget_category', 'tv')
    sickbeard.NZBGET_CATEGORY_BACKLOG = check_setting_str(cfgobj, 'NZBget', 'nzbget_category_backlog',
                                                          sickbeard.NZBGET_CATEGORY)
    sickbeard.NZBGET_CATEGORY_ANIME = check_setting_str(cfgobj, 'NZBget', 'nzbget_category_anime', 'anime')
    sickbeard.NZBGET_CATEGORY_ANIME_BACKLOG = check_setting_str(
            cfgobj, 'NZBget', 'nzbget_category_anime_backlog', sickbeard.NZBGET_CATEGORY_ANIME
    )
    sickbeard.NZBGET_HOST = check_setting_str(cfgobj, 'NZBget', 'nzbget_host', '')
    sickbeard.NZBGET_USE_HTTPS = bool(check_setting_int(cfgobj, 'NZBget', 'nzbget_use_https', 0))
    sickbeard.NZBGET_PRIORITY = check_setting_int(cfgobj, 'NZBget', 'nzbget_priority', 100)

    sickbeard.TORRENT_USERNAME = check_setting_str(cfgobj, 'TORRENT', 'torrent_username', '', censor_log=True)
    sickbeard.TORRENT_PASSWORD = check_setting_str(cfgobj, 'TORRENT', 'torrent_password', '', censor_log=True)
    sickbeard.TORRENT_HOST = check_setting_str(cfgobj, 'TORRENT', 'torrent_host', '')
    sickbeard.TORRENT_PATH = check_setting_str(cfgobj, 'TORRENT', 'torrent_path', '')
    sickbeard.TORRENT_SEED_TIME = check_setting_int(cfgobj, 'TORRENT', 'torrent_seed_time', 0)
    sickbeard.TORRENT_PAUSED = bool(check_setting_int(cfgobj, 'TORRENT', 'torrent_paused', 0))
    sickbeard.TORRENT_HIGH_BANDWIDTH = bool(check_setting_int(cfgobj, 'TORRENT', 'torrent_high_bandwidth', 0))
    sickbeard.TORRENT_LABEL = check_setting_str(cfgobj, 'TORRENT', 'torrent_label', '')
    sickbeard.TORRENT_LABEL_ANIME = check_setting_str(cfgobj, 'TORRENT', 'torrent_label_anime', '')
    sickbeard.TORRENT_VERIFY_CERT = bool(check_setting_int(cfgobj, 'TORRENT', 'torrent_verify_cert', 0))
    sickbeard.TORRENT_RPCURL = check_setting_str(cfgobj, 'TORRENT', 'torrent_rpcurl', 'transmission')
    sickbeard.TORRENT_AUTH_TYPE = check_setting_str(cfgobj, 'TORRENT', 'torrent_auth_type', '')

    sickbeard.USE_KODI = bool(check_setting_int(cfgobj, 'KODI', 'use_kodi', 0))
    sickbeard.KODI_ALWAYS_ON = bool(check_setting_int(cfgobj, 'KODI', 'kodi_always_on', 1))
    sickbeard.KODI_NOTIFY_ONSNATCH = bool(check_setting_int(cfgobj, 'KODI', 'kodi_notify_onsnatch', 0))
    sickbeard.KODI_NOTIFY_ONDOWNLOAD = bool(check_setting_int(cfgobj, 'KODI', 'kodi_notify_ondownload', 0))
    sickbeard.KODI_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            check_setting_int(cfgobj, 'KODI', 'kodi_notify_onsubtitledownload', 0))
    sickbeard.KODI_UPDATE_LIBRARY = bool(check_setting_int(cfgobj, 'KODI', 'kodi_update_library', 0))
    sickbeard.KODI_UPDATE_FULL = bool(check_setting_int(cfgobj, 'KODI', 'kodi_update_full', 0))
    sickbeard.KODI_UPDATE_ONLYFIRST = bool(check_setting_int(cfgobj, 'KODI', 'kodi_update_onlyfirst', 0))
    sickbeard.KODI_HOST = check_setting_str(cfgobj, 'KODI', 'kodi_host', '')
    sickbeard.KODI_USERNAME = check_setting_str(cfgobj, 'KODI', 'kodi_username', '', censor_log=True)
    sickbeard.KODI_PASSWORD = check_setting_str(cfgobj, 'KODI', 'kodi_password', '', censor_log=True)

    sickbeard.USE_PLEX = bool(check_setting_int(cfgobj, 'Plex', 'use_plex', 0))
    sickbeard.PLEX_NOTIFY_ONSNATCH = bool(check_setting_int(cfgobj, 'Plex', 'plex_notify_onsnatch', 0))
    sickbeard.PLEX_NOTIFY_ONDOWNLOAD = bool(check_setting_int(cfgobj, 'Plex', 'plex_notify_ondownload', 0))
    sickbeard.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            check_setting_int(cfgobj, 'Plex', 'plex_notify_onsubtitledownload', 0))
    sickbeard.PLEX_UPDATE_LIBRARY = bool(check_setting_int(cfgobj, 'Plex', 'plex_update_library', 0))
    sickbeard.PLEX_SERVER_HOST = check_setting_str(cfgobj, 'Plex', 'plex_server_host', '')
    sickbeard.PLEX_SERVER_TOKEN = check_setting_str(cfgobj, 'Plex', 'plex_server_token', '')
    sickbeard.PLEX_HOST = check_setting_str(cfgobj, 'Plex', 'plex_host', '')
    sickbeard.PLEX_USERNAME = check_setting_str(cfgobj, 'Plex', 'plex_username', '', censor_log=True)
    sickbeard.PLEX_PASSWORD = check_setting_str(cfgobj, 'Plex', 'plex_password', '', censor_log=True)
    sickbeard.USE_PLEX_CLIENT = bool(check_setting_int(cfgobj, 'Plex', 'use_plex_client', 0))
    sickbeard.PLEX_CLIENT_USERNAME = check_setting_str(cfgobj, 'Plex', 'plex_client_username', '', censor_log=True)
    sickbeard.PLEX_CLIENT_PASSWORD = check_setting_str(cfgobj, 'Plex', 'plex_client_password', '', censor_log=True)

    sickbeard.USE_EMBY = bool(check_setting_int(cfgobj, 'Emby', 'use_emby', 0))
    sickbeard.EMBY_HOST = check_setting_str(cfgobj, 'Emby', 'emby_host', '')
    sickbeard.EMBY_APIKEY = check_setting_str(cfgobj, 'Emby', 'emby_apikey', '')

    sickbeard.USE_GROWL = bool(check_setting_int(cfgobj, 'Growl', 'use_growl', 0))
    sickbeard.GROWL_NOTIFY_ONSNATCH = bool(check_setting_int(cfgobj, 'Growl', 'growl_notify_onsnatch', 0))
    sickbeard.GROWL_NOTIFY_ONDOWNLOAD = bool(check_setting_int(cfgobj, 'Growl', 'growl_notify_ondownload', 0))
    sickbeard.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            check_setting_int(cfgobj, 'Growl', 'growl_notify_onsubtitledownload', 0))
    sickbeard.GROWL_HOST = check_setting_str(cfgobj, 'Growl', 'growl_host', '')
    sickbeard.GROWL_PASSWORD = check_setting_str(cfgobj, 'Growl', 'growl_password', '', censor_log=True)

    sickbeard.USE_FREEMOBILE = bool(check_setting_int(cfgobj, 'FreeMobile', 'use_freemobile', 0))
    sickbeard.FREEMOBILE_NOTIFY_ONSNATCH = bool(
            check_setting_int(cfgobj, 'FreeMobile', 'freemobile_notify_onsnatch', 0))
    sickbeard.FREEMOBILE_NOTIFY_ONDOWNLOAD = bool(
            check_setting_int(cfgobj, 'FreeMobile', 'freemobile_notify_ondownload', 0))
    sickbeard.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            check_setting_int(cfgobj, 'FreeMobile', 'freemobile_notify_onsubtitledownload', 0))
    sickbeard.FREEMOBILE_ID = check_setting_str(cfgobj, 'FreeMobile', 'freemobile_id', '')
    sickbeard.FREEMOBILE_APIKEY = check_setting_str(cfgobj, 'FreeMobile', 'freemobile_apikey', '')

    sickbeard.USE_PROWL = bool(check_setting_int(cfgobj, 'Prowl', 'use_prowl', 0))
    sickbeard.PROWL_NOTIFY_ONSNATCH = bool(check_setting_int(cfgobj, 'Prowl', 'prowl_notify_onsnatch', 0))
    sickbeard.PROWL_NOTIFY_ONDOWNLOAD = bool(check_setting_int(cfgobj, 'Prowl', 'prowl_notify_ondownload', 0))
    sickbeard.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            check_setting_int(cfgobj, 'Prowl', 'prowl_notify_onsubtitledownload', 0))
    sickbeard.PROWL_API = check_setting_str(cfgobj, 'Prowl', 'prowl_api', '', censor_log=True)
    sickbeard.PROWL_PRIORITY = check_setting_str(cfgobj, 'Prowl', 'prowl_priority', "0")

    sickbeard.USE_TWITTER = bool(check_setting_int(cfgobj, 'Twitter', 'use_twitter', 0))
    sickbeard.TWITTER_NOTIFY_ONSNATCH = bool(check_setting_int(cfgobj, 'Twitter', 'twitter_notify_onsnatch', 0))
    sickbeard.TWITTER_NOTIFY_ONDOWNLOAD = bool(check_setting_int(cfgobj, 'Twitter', 'twitter_notify_ondownload', 0))
    sickbeard.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            check_setting_int(cfgobj, 'Twitter', 'twitter_notify_onsubtitledownload', 0))
    sickbeard.TWITTER_USERNAME = check_setting_str(cfgobj, 'Twitter', 'twitter_username', '', censor_log=True)
    sickbeard.TWITTER_PASSWORD = check_setting_str(cfgobj, 'Twitter', 'twitter_password', '', censor_log=True)
    sickbeard.TWITTER_PREFIX = check_setting_str(cfgobj, 'Twitter', 'twitter_prefix', sickbeard.GIT_REPO)
    sickbeard.TWITTER_DMTO = check_setting_str(cfgobj, 'Twitter', 'twitter_dmto', '')
    sickbeard.TWITTER_USEDM = bool(check_setting_int(cfgobj, 'Twitter', 'twitter_usedm', 0))

    sickbeard.USE_BOXCAR = bool(check_setting_int(cfgobj, 'Boxcar', 'use_boxcar', 0))
    sickbeard.BOXCAR_NOTIFY_ONSNATCH = bool(check_setting_int(cfgobj, 'Boxcar', 'boxcar_notify_onsnatch', 0))
    sickbeard.BOXCAR_NOTIFY_ONDOWNLOAD = bool(check_setting_int(cfgobj, 'Boxcar', 'boxcar_notify_ondownload', 0))
    sickbeard.BOXCAR_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            check_setting_int(cfgobj, 'Boxcar', 'boxcar_notify_onsubtitledownload', 0))
    sickbeard.BOXCAR_USERNAME = check_setting_str(cfgobj, 'Boxcar', 'boxcar_username', '', censor_log=True)

    sickbeard.USE_BOXCAR2 = bool(check_setting_int(cfgobj, 'Boxcar2', 'use_boxcar2', 0))
    sickbeard.BOXCAR2_NOTIFY_ONSNATCH = bool(check_setting_int(cfgobj, 'Boxcar2', 'boxcar2_notify_onsnatch', 0))
    sickbeard.BOXCAR2_NOTIFY_ONDOWNLOAD = bool(check_setting_int(cfgobj, 'Boxcar2', 'boxcar2_notify_ondownload', 0))
    sickbeard.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            check_setting_int(cfgobj, 'Boxcar2', 'boxcar2_notify_onsubtitledownload', 0))
    sickbeard.BOXCAR2_ACCESSTOKEN = check_setting_str(cfgobj, 'Boxcar2', 'boxcar2_accesstoken', '', censor_log=True)

    sickbeard.USE_PUSHOVER = bool(check_setting_int(cfgobj, 'Pushover', 'use_pushover', 0))
    sickbeard.PUSHOVER_NOTIFY_ONSNATCH = bool(check_setting_int(cfgobj, 'Pushover', 'pushover_notify_onsnatch', 0))
    sickbeard.PUSHOVER_NOTIFY_ONDOWNLOAD = bool(
            check_setting_int(cfgobj, 'Pushover', 'pushover_notify_ondownload', 0))
    sickbeard.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            check_setting_int(cfgobj, 'Pushover', 'pushover_notify_onsubtitledownload', 0))
    sickbeard.PUSHOVER_USERKEY = check_setting_str(cfgobj, 'Pushover', 'pushover_userkey', '', censor_log=True)
    sickbeard.PUSHOVER_APIKEY = check_setting_str(cfgobj, 'Pushover', 'pushover_apikey', '', censor_log=True)
    sickbeard.PUSHOVER_DEVICE = check_setting_str(cfgobj, 'Pushover', 'pushover_device', '')
    sickbeard.PUSHOVER_SOUND = check_setting_str(cfgobj, 'Pushover', 'pushover_sound', 'pushover')

    sickbeard.USE_LIBNOTIFY = bool(check_setting_int(cfgobj, 'Libnotify', 'use_libnotify', 0))
    sickbeard.LIBNOTIFY_NOTIFY_ONSNATCH = bool(
            check_setting_int(cfgobj, 'Libnotify', 'libnotify_notify_onsnatch', 0))
    sickbeard.LIBNOTIFY_NOTIFY_ONDOWNLOAD = bool(
            check_setting_int(cfgobj, 'Libnotify', 'libnotify_notify_ondownload', 0))
    sickbeard.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            check_setting_int(cfgobj, 'Libnotify', 'libnotify_notify_onsubtitledownload', 0))

    sickbeard.USE_NMJ = bool(check_setting_int(cfgobj, 'NMJ', 'use_nmj', 0))
    sickbeard.NMJ_HOST = check_setting_str(cfgobj, 'NMJ', 'nmj_host', '')
    sickbeard.NMJ_DATABASE = check_setting_str(cfgobj, 'NMJ', 'nmj_database', '')
    sickbeard.NMJ_MOUNT = check_setting_str(cfgobj, 'NMJ', 'nmj_mount', '')

    sickbeard.USE_NMJv2 = bool(check_setting_int(cfgobj, 'NMJv2', 'use_nmjv2', 0))
    sickbeard.NMJv2_HOST = check_setting_str(cfgobj, 'NMJv2', 'nmjv2_host', '')
    sickbeard.NMJv2_DATABASE = check_setting_str(cfgobj, 'NMJv2', 'nmjv2_database', '')
    sickbeard.NMJv2_DBLOC = check_setting_str(cfgobj, 'NMJv2', 'nmjv2_dbloc', '')

    sickbeard.USE_SYNOINDEX = bool(check_setting_int(cfgobj, 'Synology', 'use_synoindex', 0))

    sickbeard.USE_SYNOLOGYNOTIFIER = bool(check_setting_int(cfgobj, 'SynologyNotifier', 'use_synologynotifier', 0))
    sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH = bool(
            check_setting_int(cfgobj, 'SynologyNotifier', 'synologynotifier_notify_onsnatch', 0))
    sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD = bool(
            check_setting_int(cfgobj, 'SynologyNotifier', 'synologynotifier_notify_ondownload', 0))
    sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            check_setting_int(cfgobj, 'SynologyNotifier', 'synologynotifier_notify_onsubtitledownload', 0))

    sickbeard.THETVDB_APITOKEN = check_setting_str(cfgobj, 'theTVDB', 'thetvdb_apitoken', '', censor_log=True)

    sickbeard.USE_TRAKT = bool(check_setting_int(cfgobj, 'Trakt', 'use_trakt', 0))
    sickbeard.TRAKT_USERNAME = check_setting_str(cfgobj, 'Trakt', 'trakt_username', '', censor_log=True)
    sickbeard.TRAKT_ACCESS_TOKEN = check_setting_str(cfgobj, 'Trakt', 'trakt_access_token', '', censor_log=True)
    sickbeard.TRAKT_REFRESH_TOKEN = check_setting_str(cfgobj, 'Trakt', 'trakt_refresh_token', '', censor_log=True)
    sickbeard.TRAKT_REMOVE_WATCHLIST = bool(check_setting_int(cfgobj, 'Trakt', 'trakt_remove_watchlist', 0))
    sickbeard.TRAKT_REMOVE_SERIESLIST = bool(check_setting_int(cfgobj, 'Trakt', 'trakt_remove_serieslist', 0))
    sickbeard.TRAKT_REMOVE_SHOW_FROM_SICKRAGE = bool(
            check_setting_int(cfgobj, 'Trakt', 'trakt_remove_show_from_sickrage', 0))
    sickbeard.TRAKT_SYNC_WATCHLIST = bool(check_setting_int(cfgobj, 'Trakt', 'trakt_sync_watchlist', 0))
    sickbeard.TRAKT_METHOD_ADD = check_setting_int(cfgobj, 'Trakt', 'trakt_method_add', 0)
    sickbeard.TRAKT_START_PAUSED = bool(check_setting_int(cfgobj, 'Trakt', 'trakt_start_paused', 0))
    sickbeard.TRAKT_USE_RECOMMENDED = bool(check_setting_int(cfgobj, 'Trakt', 'trakt_use_recommended', 0))
    sickbeard.TRAKT_SYNC = bool(check_setting_int(cfgobj, 'Trakt', 'trakt_sync', 0))
    sickbeard.TRAKT_SYNC_REMOVE = bool(check_setting_int(cfgobj, 'Trakt', 'trakt_sync_remove', 0))
    sickbeard.TRAKT_DEFAULT_INDEXER = check_setting_int(cfgobj, 'Trakt', 'trakt_default_indexer', 1)
    sickbeard.TRAKT_TIMEOUT = check_setting_int(cfgobj, 'Trakt', 'trakt_timeout', 30)
    sickbeard.TRAKT_BLACKLIST_NAME = check_setting_str(cfgobj, 'Trakt', 'trakt_blacklist_name', '')

    sickbeard.USE_PYTIVO = bool(check_setting_int(cfgobj, 'pyTivo', 'use_pytivo', 0))
    sickbeard.PYTIVO_NOTIFY_ONSNATCH = bool(check_setting_int(cfgobj, 'pyTivo', 'pytivo_notify_onsnatch', 0))
    sickbeard.PYTIVO_NOTIFY_ONDOWNLOAD = bool(check_setting_int(cfgobj, 'pyTivo', 'pytivo_notify_ondownload', 0))
    sickbeard.PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            check_setting_int(cfgobj, 'pyTivo', 'pytivo_notify_onsubtitledownload', 0))
    sickbeard.PYTIVO_UPDATE_LIBRARY = bool(check_setting_int(cfgobj, 'pyTivo', 'pyTivo_update_library', 0))
    sickbeard.PYTIVO_HOST = check_setting_str(cfgobj, 'pyTivo', 'pytivo_host', '')
    sickbeard.PYTIVO_SHARE_NAME = check_setting_str(cfgobj, 'pyTivo', 'pytivo_share_name', '')
    sickbeard.PYTIVO_TIVO_NAME = check_setting_str(cfgobj, 'pyTivo', 'pytivo_tivo_name', '')

    sickbeard.USE_NMA = bool(check_setting_int(cfgobj, 'NMA', 'use_nma', 0))
    sickbeard.NMA_NOTIFY_ONSNATCH = bool(check_setting_int(cfgobj, 'NMA', 'nma_notify_onsnatch', 0))
    sickbeard.NMA_NOTIFY_ONDOWNLOAD = bool(check_setting_int(cfgobj, 'NMA', 'nma_notify_ondownload', 0))
    sickbeard.NMA_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            check_setting_int(cfgobj, 'NMA', 'nma_notify_onsubtitledownload', 0))
    sickbeard.NMA_API = check_setting_str(cfgobj, 'NMA', 'nma_api', '', censor_log=True)
    sickbeard.NMA_PRIORITY = check_setting_str(cfgobj, 'NMA', 'nma_priority', "0")

    sickbeard.USE_PUSHALOT = bool(check_setting_int(cfgobj, 'Pushalot', 'use_pushalot', 0))
    sickbeard.PUSHALOT_NOTIFY_ONSNATCH = bool(check_setting_int(cfgobj, 'Pushalot', 'pushalot_notify_onsnatch', 0))
    sickbeard.PUSHALOT_NOTIFY_ONDOWNLOAD = bool(
            check_setting_int(cfgobj, 'Pushalot', 'pushalot_notify_ondownload', 0))
    sickbeard.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            check_setting_int(cfgobj, 'Pushalot', 'pushalot_notify_onsubtitledownload', 0))
    sickbeard.PUSHALOT_AUTHORIZATIONTOKEN = check_setting_str(cfgobj, 'Pushalot', 'pushalot_authorizationtoken', '',
                                                              censor_log=True)

    sickbeard.USE_PUSHBULLET = bool(check_setting_int(cfgobj, 'Pushbullet', 'use_pushbullet', 0))
    sickbeard.PUSHBULLET_NOTIFY_ONSNATCH = bool(
            check_setting_int(cfgobj, 'Pushbullet', 'pushbullet_notify_onsnatch', 0))
    sickbeard.PUSHBULLET_NOTIFY_ONDOWNLOAD = bool(
            check_setting_int(cfgobj, 'Pushbullet', 'pushbullet_notify_ondownload', 0))
    sickbeard.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            check_setting_int(cfgobj, 'Pushbullet', 'pushbullet_notify_onsubtitledownload', 0))
    sickbeard.PUSHBULLET_API = check_setting_str(cfgobj, 'Pushbullet', 'pushbullet_api', '', censor_log=True)
    sickbeard.PUSHBULLET_DEVICE = check_setting_str(cfgobj, 'Pushbullet', 'pushbullet_device', '')

    # email notify settings
    sickbeard.USE_EMAIL = bool(check_setting_int(cfgobj, 'Email', 'use_email', 0))
    sickbeard.EMAIL_NOTIFY_ONSNATCH = bool(check_setting_int(cfgobj, 'Email', 'email_notify_onsnatch', 0))
    sickbeard.EMAIL_NOTIFY_ONDOWNLOAD = bool(check_setting_int(cfgobj, 'Email', 'email_notify_ondownload', 0))
    sickbeard.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            check_setting_int(cfgobj, 'Email', 'email_notify_onsubtitledownload', 0))
    sickbeard.EMAIL_HOST = check_setting_str(cfgobj, 'Email', 'email_host', '')
    sickbeard.EMAIL_PORT = check_setting_int(cfgobj, 'Email', 'email_port', 25)
    sickbeard.EMAIL_TLS = bool(check_setting_int(cfgobj, 'Email', 'email_tls', 0))
    sickbeard.EMAIL_USER = check_setting_str(cfgobj, 'Email', 'email_user', '', censor_log=True)
    sickbeard.EMAIL_PASSWORD = check_setting_str(cfgobj, 'Email', 'email_password', '', censor_log=True)
    sickbeard.EMAIL_FROM = check_setting_str(cfgobj, 'Email', 'email_from', '')
    sickbeard.EMAIL_LIST = check_setting_str(cfgobj, 'Email', 'email_list', '')

    # subtitle settings
    sickbeard.USE_SUBTITLES = bool(check_setting_int(cfgobj, 'Subtitles', 'use_subtitles', 0))
    sickbeard.SUBTITLES_LANGUAGES = check_setting_str(cfgobj, 'Subtitles', 'subtitles_languages', '').split(',')
    sickbeard.SUBTITLES_DIR = check_setting_str(cfgobj, 'Subtitles', 'subtitles_dir', '')
    sickbeard.SUBTITLES_SERVICES_LIST = check_setting_str(cfgobj, 'Subtitles', 'SUBTITLES_SERVICES_LIST', '').split(
            ',')
    sickbeard.SUBTITLES_DEFAULT = bool(check_setting_int(cfgobj, 'Subtitles', 'subtitles_default', 0))
    sickbeard.SUBTITLES_HISTORY = bool(check_setting_int(cfgobj, 'Subtitles', 'subtitles_history', 0))
    sickbeard.SUBTITLES_HEARING_IMPAIRED = bool(
            check_setting_int(cfgobj, 'Subtitles', 'subtitles_hearing_impaired', 0))
    sickbeard.EMBEDDED_SUBTITLES_ALL = bool(check_setting_int(cfgobj, 'Subtitles', 'embedded_subtitles_all', 0))
    sickbeard.SUBTITLES_MULTI = bool(check_setting_int(cfgobj, 'Subtitles', 'subtitles_multi', 1))
    sickbeard.SUBTITLES_SERVICES_ENABLED = [int(x) for x in
                                            check_setting_str(cfgobj, 'Subtitles', 'SUBTITLES_SERVICES_ENABLED',
                                                              '').split(
                                                    '|')
                                            if x]
    sickbeard.SUBTITLES_EXTRA_SCRIPTS = [x.strip() for x in
                                         check_setting_str(cfgobj, 'Subtitles', 'subtitles_extra_scripts',
                                                           '').split('|') if
                                         x.strip()]

    sickbeard.ADDIC7ED_USER = check_setting_str(cfgobj, 'Subtitles', 'addic7ed_username', '', censor_log=True)
    sickbeard.ADDIC7ED_PASS = check_setting_str(cfgobj, 'Subtitles', 'addic7ed_password', '', censor_log=True)

    sickbeard.LEGENDASTV_USER = check_setting_str(cfgobj, 'Subtitles', 'legendastv_username', '', censor_log=True)
    sickbeard.LEGENDASTV_PASS = check_setting_str(cfgobj, 'Subtitles', 'legendastv_password', '', censor_log=True)

    sickbeard.OPENSUBTITLES_USER = check_setting_str(cfgobj, 'Subtitles', 'opensubtitles_username', '',
                                                     censor_log=True)
    sickbeard.OPENSUBTITLES_PASS = check_setting_str(cfgobj, 'Subtitles', 'opensubtitles_password', '',
                                                     censor_log=True)

    sickbeard.USE_FAILED_DOWNLOADS = bool(check_setting_int(cfgobj, 'FailedDownloads', 'use_failed_downloads', 0))
    sickbeard.DELETE_FAILED = bool(check_setting_int(cfgobj, 'FailedDownloads', 'delete_failed', 0))

    sickbeard.REQUIRE_WORDS = check_setting_str(cfgobj, 'General', 'require_words', '')
    sickbeard.IGNORE_WORDS = check_setting_str(cfgobj, 'General', 'ignore_words',
                                               'german,french,core2hd,dutch,swedish,reenc,MrLss')
    sickbeard.IGNORED_SUBS_LIST = check_setting_str(cfgobj, 'General', 'ignored_subs_list',
                                                    'dk,fin,heb,kor,nor,nordic,pl,swe')

    sickbeard.CALENDAR_UNPROTECTED = bool(check_setting_int(cfgobj, 'General', 'calendar_unprotected', 0))
    sickbeard.CALENDAR_ICONS = bool(check_setting_int(cfgobj, 'General', 'calendar_icons', 0))

    sickbeard.NO_RESTART = bool(check_setting_int(cfgobj, 'General', 'no_restart', 0))
    sickbeard.EXTRA_SCRIPTS = [x.strip() for x in
                               check_setting_str(cfgobj, 'General', 'extra_scripts', '').split('|') if
                               x.strip()]
    sickbeard.USE_LISTVIEW = bool(check_setting_int(cfgobj, 'General', 'use_listview', 0))

    sickbeard.USE_ANIDB = bool(check_setting_int(cfgobj, 'ANIDB', 'use_anidb', 0))
    sickbeard.ANIDB_USERNAME = check_setting_str(cfgobj, 'ANIDB', 'anidb_username', '', censor_log=True)
    sickbeard.ANIDB_PASSWORD = check_setting_str(cfgobj, 'ANIDB', 'anidb_password', '', censor_log=True)
    sickbeard.ANIDB_USE_MYLIST = bool(check_setting_int(cfgobj, 'ANIDB', 'anidb_use_mylist', 0))

    sickbeard.ANIME_SPLIT_HOME = bool(check_setting_int(cfgobj, 'ANIME', 'anime_split_home', 0))

    sickbeard.METADATA_KODI = check_setting_str(cfgobj, 'General', 'metadata_kodi', '0|0|0|0|0|0|0|0|0|0')
    sickbeard.METADATA_KODI_12PLUS = check_setting_str(cfgobj, 'General', 'metadata_kodi_12plus',
                                                       '0|0|0|0|0|0|0|0|0|0')
    sickbeard.METADATA_MEDIABROWSER = check_setting_str(cfgobj, 'General', 'metadata_mediabrowser',
                                                        '0|0|0|0|0|0|0|0|0|0')
    sickbeard.METADATA_PS3 = check_setting_str(cfgobj, 'General', 'metadata_ps3', '0|0|0|0|0|0|0|0|0|0')
    sickbeard.METADATA_WDTV = check_setting_str(cfgobj, 'General', 'metadata_wdtv', '0|0|0|0|0|0|0|0|0|0')
    sickbeard.METADATA_TIVO = check_setting_str(cfgobj, 'General', 'metadata_tivo', '0|0|0|0|0|0|0|0|0|0')
    sickbeard.METADATA_MEDE8ER = check_setting_str(cfgobj, 'General', 'metadata_mede8er', '0|0|0|0|0|0|0|0|0|0')

    sickbeard.HOME_LAYOUT = check_setting_str(cfgobj, 'GUI', 'home_layout', 'poster')
    sickbeard.HISTORY_LAYOUT = check_setting_str(cfgobj, 'GUI', 'history_layout', 'detailed')
    sickbeard.HISTORY_LIMIT = check_setting_str(cfgobj, 'GUI', 'history_limit', '100')
    sickbeard.DISPLAY_SHOW_SPECIALS = bool(check_setting_int(cfgobj, 'GUI', 'display_show_specials', 1))
    sickbeard.COMING_EPS_LAYOUT = check_setting_str(cfgobj, 'GUI', 'coming_eps_layout', 'banner')
    sickbeard.COMING_EPS_DISPLAY_PAUSED = bool(check_setting_int(cfgobj, 'GUI', 'coming_eps_display_paused', 0))
    sickbeard.COMING_EPS_SORT = check_setting_str(cfgobj, 'GUI', 'coming_eps_sort', 'date')
    sickbeard.COMING_EPS_MISSED_RANGE = check_setting_int(cfgobj, 'GUI', 'coming_eps_missed_range', 7)
    sickbeard.FUZZY_DATING = bool(check_setting_int(cfgobj, 'GUI', 'fuzzy_dating', 0))
    sickbeard.TRIM_ZERO = bool(check_setting_int(cfgobj, 'GUI', 'trim_zero', 0))
    sickbeard.DATE_PRESET = check_setting_str(cfgobj, 'GUI', 'date_preset', '%x')
    sickbeard.TIME_PRESET_W_SECONDS = check_setting_str(cfgobj, 'GUI', 'time_preset', '%I:%M:%S %p')
    sickbeard.TIMEZONE_DISPLAY = check_setting_str(cfgobj, 'GUI', 'timezone_display', 'local')
    sickbeard.POSTER_SORTBY = check_setting_str(cfgobj, 'GUI', 'poster_sortby', 'name')
    sickbeard.POSTER_SORTDIR = check_setting_int(cfgobj, 'GUI', 'poster_sortdir', 1)
    sickbeard.FILTER_ROW = bool(check_setting_int(cfgobj, 'GUI', 'filter_row', 1))
    sickbeard.DISPLAY_ALL_SEASONS = bool(check_setting_int(cfgobj, 'General', 'display_all_seasons', 1))

    sickbeard.NEWZNAB_DATA = check_setting_str(cfgobj, 'Newznab', 'newznab_data',
                                               NewznabProvider.getDefaultProviders())
    sickbeard.TORRENTRSS_DATA = check_setting_str(cfgobj, 'TorrentRss', 'torrentrss_data',
                                                  TorrentRssProvider.getDefaultProviders())

    # NEWZNAB PROVIDER LIST
    sickbeard.newznabProviderList = NewznabProvider.getProviderList(sickbeard.NEWZNAB_DATA)

    # TORRENT RSS PROVIDER LIST
    sickbeard.torrentRssProviderList = TorrentRssProvider.getProviderList(sickbeard.TORRENTRSS_DATA)

    # NZB AND TORRENT PROVIDER DICT
    sickbeard.providersDict = {
        GenericProvider.NZB: {p.id: p for p in NZBProvider.getProviderList()},
        GenericProvider.TORRENT: {p.id: p for p in TorrentProvider.getProviderList()},
    }

    sickbeard.PROVIDER_ORDER = check_setting_str(cfgobj, 'General', 'provider_order', '').split()

    # TORRENT PROVIDER SETTINGS
    for providerID, providerObj in sickbeard.providersDict[TorrentProvider.type].items():
        providerObj.enabled = bool(check_setting_int(cfgobj, providerID.upper(), providerID, 0))

        if hasattr(providerObj, 'api_key'):
            providerObj.api_key = check_setting_str(
                    cfgobj, providerID.upper(), providerID + '_api_key', '', censor_log=True
            )

        if hasattr(providerObj, 'hash'):
            providerObj.hash = check_setting_str(
                    cfgobj, providerID.upper(), providerID + '_hash', '', censor_log=True
            )

        if hasattr(providerObj, 'digest'):
            providerObj.digest = check_setting_str(
                    cfgobj, providerID.upper(), providerID + '_digest', '', censor_log=True
            )

        if hasattr(providerObj, 'username'):
            providerObj.username = check_setting_str(
                    cfgobj, providerID.upper(), providerID + '_username', '', censor_log=True
            )

        if hasattr(providerObj, 'password'):
            providerObj.password = check_setting_str(
                    cfgobj, providerID.upper(), providerID + '_password', '', censor_log=True
            )

        if hasattr(providerObj, 'passkey'):
            providerObj.passkey = check_setting_str(cfgobj, providerID.upper(),
                                                    providerID + '_passkey', '',
                                                    censor_log=True)
        if hasattr(providerObj, 'pin'):
            providerObj.pin = check_setting_str(cfgobj, providerID.upper(),
                                                providerID + '_pin', '', censor_log=True)
        if hasattr(providerObj, 'confirmed'):
            providerObj.confirmed = bool(check_setting_int(cfgobj, providerID.upper(),
                                                           providerID + '_confirmed', 1))
        if hasattr(providerObj, 'ranked'):
            providerObj.ranked = bool(check_setting_int(cfgobj, providerID.upper(),
                                                        providerID + '_ranked', 1))

        if hasattr(providerObj, 'engrelease'):
            providerObj.engrelease = bool(check_setting_int(cfgobj, providerID.upper(),
                                                            providerID + '_engrelease', 0))

        if hasattr(providerObj, 'onlyspasearch'):
            providerObj.onlyspasearch = bool(check_setting_int(cfgobj, providerID.upper(),
                                                               providerID + '_onlyspasearch',
                                                               0))

        if hasattr(providerObj, 'sorting'):
            providerObj.sorting = check_setting_str(cfgobj, providerID.upper(),
                                                    providerID + '_sorting', 'seeders')
        if hasattr(providerObj, 'options'):
            providerObj.options = check_setting_str(cfgobj, providerID.upper(),
                                                    providerID + '_options', '')
        if hasattr(providerObj, 'ratio'):
            providerObj.ratio = check_setting_str(cfgobj, providerID.upper(),
                                                  providerID + '_ratio', '')
        if hasattr(providerObj, 'minseed'):
            providerObj.minseed = check_setting_int(cfgobj, providerID.upper(),
                                                    providerID + '_minseed', 1)
        if hasattr(providerObj, 'minleech'):
            providerObj.minleech = check_setting_int(cfgobj, providerID.upper(),
                                                     providerID + '_minleech', 0)
        if hasattr(providerObj, 'freeleech'):
            providerObj.freeleech = bool(check_setting_int(cfgobj, providerID.upper(),
                                                           providerID + '_freeleech', 0))
        if hasattr(providerObj, 'search_mode'):
            providerObj.search_mode = check_setting_str(cfgobj, providerID.upper(),
                                                        providerID + '_search_mode',
                                                        'eponly')
        if hasattr(providerObj, 'search_fallback'):
            providerObj.search_fallback = bool(check_setting_int(cfgobj, providerID.upper(),
                                                                 providerID + '_search_fallback',
                                                                 0))

        if hasattr(providerObj, 'enable_daily'):
            providerObj.enable_daily = bool(check_setting_int(cfgobj, providerID.upper(),
                                                              providerID + '_enable_daily',
                                                              1))

        if hasattr(providerObj, 'enable_backlog') and hasattr(providerObj, 'supportsBacklog'):
            providerObj.enable_backlog = bool(check_setting_int(cfgobj, providerID.upper(),
                                                                providerID + '_enable_backlog',
                                                                providerObj.supportsBacklog))

        if hasattr(providerObj, 'cat'):
            providerObj.cat = check_setting_int(cfgobj, providerID.upper(),
                                                providerID + '_cat', 0)
        if hasattr(providerObj, 'subtitle'):
            providerObj.subtitle = bool(check_setting_int(cfgobj, providerID.upper(),
                                                          providerID + '_subtitle', 0))

    # NZB PROVIDER SETTINGS
    for providerID, providerObj in sickbeard.providersDict[NZBProvider.type].items():
        providerObj.enabled = bool(
                check_setting_int(cfgobj, providerID.upper(), providerID, 0))
        if hasattr(providerObj, 'api_key'):
            providerObj.api_key = check_setting_str(cfgobj, providerID.upper(),
                                                    providerID + '_api_key', '', censor_log=True)
        if hasattr(providerObj, 'username'):
            providerObj.username = check_setting_str(cfgobj, providerID.upper(),
                                                     providerID + '_username', '', censor_log=True)
        if hasattr(providerObj, 'search_mode'):
            providerObj.search_mode = check_setting_str(cfgobj, providerID.upper(),
                                                        providerID + '_search_mode',
                                                        'eponly')
        if hasattr(providerObj, 'search_fallback'):
            providerObj.search_fallback = bool(check_setting_int(cfgobj, providerID.upper(),
                                                                 providerID + '_search_fallback',
                                                                 0))
        if hasattr(providerObj, 'enable_daily'):
            providerObj.enable_daily = bool(check_setting_int(cfgobj, providerID.upper(),
                                                              providerID + '_enable_daily',
                                                              1))

        if hasattr(providerObj, 'enable_backlog') and hasattr(providerObj, 'supportsBacklog'):
            providerObj.enable_backlog = bool(check_setting_int(cfgobj, providerID.upper(),
                                                                providerID + '_enable_backlog',
                                                                providerObj.supportsBacklog))

    return save_config(cfgfile)


def save_config(cfgfile):
    new_config = configobj.ConfigObj(cfgfile)

    # For passwords you must include the word `password` in the item_name and add `helpers.encrypt(ITEM_NAME, ENCRYPTION_VERSION)` in save_config()
    new_config[b'General'] = {}
    new_config[b'General'][b'git_autoissues'] = int(sickbeard.GIT_AUTOISSUES)
    new_config[b'General'][b'git_username'] = sickbeard.GIT_USERNAME
    new_config[b'General'][b'git_password'] = encrypt(sickbeard.GIT_PASSWORD, sickbeard.ENCRYPTION_VERSION)
    new_config[b'General'][b'git_reset'] = int(sickbeard.GIT_RESET)
    new_config[b'General'][b'branch'] = sickbeard.GIT_BRANCH
    new_config[b'General'][b'git_remote'] = sickbeard.GIT_REMOTE
    new_config[b'General'][b'git_remote_url'] = sickbeard.GIT_REMOTE_URL
    new_config[b'General'][b'cur_commit_hash'] = sickbeard.CUR_COMMIT_HASH
    new_config[b'General'][b'cur_commit_branch'] = sickbeard.CUR_COMMIT_BRANCH
    new_config[b'General'][b'git_newver'] = int(sickbeard.GIT_NEWVER)
    new_config[b'General'][b'config_version'] = sickbeard.CONFIG_VERSION
    new_config[b'General'][b'encryption_version'] = int(sickbeard.ENCRYPTION_VERSION)
    new_config[b'General'][b'encryption_secret'] = sickbeard.ENCRYPTION_SECRET
    new_config[b'General'][b'log_dir'] = sickbeard.LOG_DIR or 'Logs'
    new_config[b'General'][b'log_nr'] = int(sickbeard.LOG_NR)
    new_config[b'General'][b'log_size'] = int(sickbeard.LOG_SIZE)
    new_config[b'General'][b'socket_timeout'] = sickbeard.SOCKET_TIMEOUT
    new_config[b'General'][b'web_port'] = sickbeard.WEB_PORT
    new_config[b'General'][b'web_host'] = sickbeard.WEB_HOST
    new_config[b'General'][b'web_ipv6'] = int(sickbeard.WEB_IPV6)
    new_config[b'General'][b'web_log'] = int(sickbeard.WEB_LOG)
    new_config[b'General'][b'web_root'] = sickbeard.WEB_ROOT
    new_config[b'General'][b'web_username'] = sickbeard.WEB_USERNAME
    new_config[b'General'][b'web_password'] = encrypt(sickbeard.WEB_PASSWORD, sickbeard.ENCRYPTION_VERSION)
    new_config[b'General'][b'web_cookie_secret'] = sickbeard.WEB_COOKIE_SECRET
    new_config[b'General'][b'web_use_gzip'] = int(sickbeard.WEB_USE_GZIP)
    new_config[b'General'][b'ssl_verify'] = int(sickbeard.SSL_VERIFY)
    new_config[b'General'][b'download_url'] = sickbeard.DOWNLOAD_URL
    new_config[b'General'][b'localhost_ip'] = sickbeard.LOCALHOST_IP
    new_config[b'General'][b'cpu_preset'] = sickbeard.CPU_PRESET
    new_config[b'General'][b'anon_redirect'] = sickbeard.ANON_REDIRECT
    new_config[b'General'][b'api_key'] = sickbeard.API_KEY
    new_config[b'General'][b'debug'] = int(sickbeard.DEBUG)
    new_config[b'General'][b'default_page'] = sickbeard.DEFAULT_PAGE
    new_config[b'General'][b'enable_https'] = int(sickbeard.ENABLE_HTTPS)
    new_config[b'General'][b'https_cert'] = sickbeard.HTTPS_CERT
    new_config[b'General'][b'https_key'] = sickbeard.HTTPS_KEY
    new_config[b'General'][b'handle_reverse_proxy'] = int(sickbeard.HANDLE_REVERSE_PROXY)
    new_config[b'General'][b'use_nzbs'] = int(sickbeard.USE_NZBS)
    new_config[b'General'][b'use_torrents'] = int(sickbeard.USE_TORRENTS)
    new_config[b'General'][b'nzb_method'] = sickbeard.NZB_METHOD
    new_config[b'General'][b'torrent_method'] = sickbeard.TORRENT_METHOD
    new_config[b'General'][b'usenet_retention'] = int(sickbeard.USENET_RETENTION)
    new_config[b'General'][b'autopostprocessor_frequency'] = int(sickbeard.AUTOPOSTPROCESSOR_FREQ)
    new_config[b'General'][b'dailysearch_frequency'] = int(sickbeard.DAILY_SEARCHER_FREQ)
    new_config[b'General'][b'backlog_frequency'] = int(sickbeard.BACKLOG_SEARCHER_FREQ)
    new_config[b'General'][b'update_frequency'] = int(sickbeard.UPDATER_FREQ)
    new_config[b'General'][b'showupdate_hour'] = int(sickbeard.SHOWUPDATE_HOUR)
    new_config[b'General'][b'download_propers'] = int(sickbeard.DOWNLOAD_PROPERS)
    new_config[b'General'][b'randomize_providers'] = int(sickbeard.RANDOMIZE_PROVIDERS)
    new_config[b'General'][b'check_propers_interval'] = sickbeard.PROPER_SEARCHER_INTERVAL
    new_config[b'General'][b'allow_high_priority'] = int(sickbeard.ALLOW_HIGH_PRIORITY)
    new_config[b'General'][b'skip_removed_files'] = int(sickbeard.SKIP_REMOVED_FILES)
    new_config[b'General'][b'quality_default'] = int(sickbeard.QUALITY_DEFAULT)
    new_config[b'General'][b'status_default'] = int(sickbeard.STATUS_DEFAULT)
    new_config[b'General'][b'status_default_after'] = int(sickbeard.STATUS_DEFAULT_AFTER)
    new_config[b'General'][b'flatten_folders_default'] = int(sickbeard.FLATTEN_FOLDERS_DEFAULT)
    new_config[b'General'][b'indexer_default'] = int(sickbeard.INDEXER_DEFAULT)
    new_config[b'General'][b'indexer_timeout'] = int(sickbeard.INDEXER_TIMEOUT)
    new_config[b'General'][b'anime_default'] = int(sickbeard.ANIME_DEFAULT)
    new_config[b'General'][b'scene_default'] = int(sickbeard.SCENE_DEFAULT)
    new_config[b'General'][b'archive_default'] = int(sickbeard.ARCHIVE_DEFAULT)
    new_config[b'General'][b'provider_order'] = ' '.join(sickbeard.PROVIDER_ORDER)
    new_config[b'General'][b'version_notify'] = int(sickbeard.VERSION_NOTIFY)
    new_config[b'General'][b'auto_update'] = int(sickbeard.AUTO_UPDATE)
    new_config[b'General'][b'notify_on_update'] = int(sickbeard.NOTIFY_ON_UPDATE)
    new_config[b'General'][b'naming_strip_year'] = int(sickbeard.NAMING_STRIP_YEAR)
    new_config[b'General'][b'naming_pattern'] = sickbeard.NAMING_PATTERN
    new_config[b'General'][b'naming_custom_abd'] = int(sickbeard.NAMING_CUSTOM_ABD)
    new_config[b'General'][b'naming_abd_pattern'] = sickbeard.NAMING_ABD_PATTERN
    new_config[b'General'][b'naming_custom_sports'] = int(sickbeard.NAMING_CUSTOM_SPORTS)
    new_config[b'General'][b'naming_sports_pattern'] = sickbeard.NAMING_SPORTS_PATTERN
    new_config[b'General'][b'naming_custom_anime'] = int(sickbeard.NAMING_CUSTOM_ANIME)
    new_config[b'General'][b'naming_anime_pattern'] = sickbeard.NAMING_ANIME_PATTERN
    new_config[b'General'][b'naming_multi_ep'] = int(sickbeard.NAMING_MULTI_EP)
    new_config[b'General'][b'naming_anime_multi_ep'] = int(sickbeard.NAMING_ANIME_MULTI_EP)
    new_config[b'General'][b'naming_anime'] = int(sickbeard.NAMING_ANIME)
    new_config[b'General'][b'indexerDefaultLang'] = sickbeard.INDEXER_DEFAULT_LANGUAGE
    new_config[b'General'][b'ep_default_deleted_status'] = int(sickbeard.EP_DEFAULT_DELETED_STATUS)
    new_config[b'General'][b'launch_browser'] = int(sickbeard.LAUNCH_BROWSER)
    new_config[b'General'][b'trash_remove_show'] = int(sickbeard.TRASH_REMOVE_SHOW)
    new_config[b'General'][b'trash_rotate_logs'] = int(sickbeard.TRASH_ROTATE_LOGS)
    new_config[b'General'][b'sort_article'] = int(sickbeard.SORT_ARTICLE)
    new_config[b'General'][b'proxy_setting'] = sickbeard.PROXY_SETTING
    new_config[b'General'][b'proxy_indexers'] = int(sickbeard.PROXY_INDEXERS)

    new_config[b'General'][b'use_listview'] = int(sickbeard.USE_LISTVIEW)
    new_config[b'General'][b'metadata_kodi'] = sickbeard.METADATA_KODI
    new_config[b'General'][b'metadata_kodi_12plus'] = sickbeard.METADATA_KODI_12PLUS
    new_config[b'General'][b'metadata_mediabrowser'] = sickbeard.METADATA_MEDIABROWSER
    new_config[b'General'][b'metadata_ps3'] = sickbeard.METADATA_PS3
    new_config[b'General'][b'metadata_wdtv'] = sickbeard.METADATA_WDTV
    new_config[b'General'][b'metadata_tivo'] = sickbeard.METADATA_TIVO
    new_config[b'General'][b'metadata_mede8er'] = sickbeard.METADATA_MEDE8ER

    new_config[b'General'][b'backlog_days'] = int(sickbeard.BACKLOG_DAYS)

    new_config[b'General'][b'cache_dir'] = sickbeard.ACTUAL_CACHE_DIR if sickbeard.ACTUAL_CACHE_DIR else 'cache'
    new_config[b'General'][b'root_dirs'] = sickbeard.ROOT_DIRS if sickbeard.ROOT_DIRS else ''
    new_config[b'General'][b'tv_download_dir'] = sickbeard.TV_DOWNLOAD_DIR
    new_config[b'General'][b'keep_processed_dir'] = int(sickbeard.KEEP_PROCESSED_DIR)
    new_config[b'General'][b'process_method'] = sickbeard.PROCESS_METHOD
    new_config[b'General'][b'del_rar_contents'] = int(sickbeard.DELRARCONTENTS)
    new_config[b'General'][b'move_associated_files'] = int(sickbeard.MOVE_ASSOCIATED_FILES)
    new_config[b'General'][b'sync_files'] = sickbeard.SYNC_FILES
    new_config[b'General'][b'postpone_if_sync_files'] = int(sickbeard.POSTPONE_IF_SYNC_FILES)
    new_config[b'General'][b'nfo_rename'] = int(sickbeard.NFO_RENAME)
    new_config[b'General'][b'process_automatically'] = int(sickbeard.PROCESS_AUTOMATICALLY)
    new_config[b'General'][b'no_delete'] = int(sickbeard.NO_DELETE)
    new_config[b'General'][b'unpack'] = int(sickbeard.UNPACK)
    new_config[b'General'][b'rename_episodes'] = int(sickbeard.RENAME_EPISODES)
    new_config[b'General'][b'airdate_episodes'] = int(sickbeard.AIRDATE_EPISODES)
    new_config[b'General'][b'file_timestamp_timezone'] = sickbeard.FILE_TIMESTAMP_TIMEZONE
    new_config[b'General'][b'create_missing_show_dirs'] = int(sickbeard.CREATE_MISSING_SHOW_DIRS)
    new_config[b'General'][b'add_shows_wo_dir'] = int(sickbeard.ADD_SHOWS_WO_DIR)

    new_config[b'General'][b'extra_scripts'] = '|'.join(sickbeard.EXTRA_SCRIPTS)
    new_config[b'General'][b'git_path'] = sickbeard.GIT_PATH
    new_config[b'General'][b'ignore_words'] = sickbeard.IGNORE_WORDS
    new_config[b'General'][b'require_words'] = sickbeard.REQUIRE_WORDS
    new_config[b'General'][b'ignored_subs_list'] = sickbeard.IGNORED_SUBS_LIST
    new_config[b'General'][b'calendar_unprotected'] = int(sickbeard.CALENDAR_UNPROTECTED)
    new_config[b'General'][b'calendar_icons'] = int(sickbeard.CALENDAR_ICONS)
    new_config[b'General'][b'no_restart'] = int(sickbeard.NO_RESTART)
    new_config[b'General'][b'developer'] = int(sickbeard.DEVELOPER)
    new_config[b'General'][b'display_all_seasons'] = int(sickbeard.DISPLAY_ALL_SEASONS)
    new_config[b'General'][b'news_last_read'] = sickbeard.NEWS_LAST_READ

    new_config[b'Blackhole'] = {}
    new_config[b'Blackhole'][b'nzb_dir'] = sickbeard.NZB_DIR
    new_config[b'Blackhole'][b'torrent_dir'] = sickbeard.TORRENT_DIR

    new_config[b'NZBs'] = {}
    new_config[b'NZBs'][b'nzbs'] = int(sickbeard.NZBS)
    new_config[b'NZBs'][b'nzbs_uid'] = sickbeard.NZBS_UID
    new_config[b'NZBs'][b'nzbs_hash'] = sickbeard.NZBS_HASH

    new_config[b'Newzbin'] = {}
    new_config[b'Newzbin'][b'newzbin'] = int(sickbeard.NEWZBIN)
    new_config[b'Newzbin'][b'newzbin_username'] = sickbeard.NEWZBIN_USERNAME
    new_config[b'Newzbin'][b'newzbin_password'] = encrypt(sickbeard.NEWZBIN_PASSWORD,
                                                          sickbeard.ENCRYPTION_VERSION)

    new_config[b'SABnzbd'] = {}
    new_config[b'SABnzbd'][b'sab_username'] = sickbeard.SAB_USERNAME
    new_config[b'SABnzbd'][b'sab_password'] = encrypt(sickbeard.SAB_PASSWORD, sickbeard.ENCRYPTION_VERSION)
    new_config[b'SABnzbd'][b'sab_apikey'] = sickbeard.SAB_APIKEY
    new_config[b'SABnzbd'][b'sab_category'] = sickbeard.SAB_CATEGORY
    new_config[b'SABnzbd'][b'sab_category_backlog'] = sickbeard.SAB_CATEGORY_BACKLOG
    new_config[b'SABnzbd'][b'sab_category_anime'] = sickbeard.SAB_CATEGORY_ANIME
    new_config[b'SABnzbd'][b'sab_category_anime_backlog'] = sickbeard.SAB_CATEGORY_ANIME_BACKLOG
    new_config[b'SABnzbd'][b'sab_host'] = sickbeard.SAB_HOST
    new_config[b'SABnzbd'][b'sab_forced'] = int(sickbeard.SAB_FORCED)

    new_config[b'NZBget'] = {}

    new_config[b'NZBget'][b'nzbget_username'] = sickbeard.NZBGET_USERNAME
    new_config[b'NZBget'][b'nzbget_password'] = encrypt(sickbeard.NZBGET_PASSWORD,
                                                        sickbeard.ENCRYPTION_VERSION)
    new_config[b'NZBget'][b'nzbget_category'] = sickbeard.NZBGET_CATEGORY
    new_config[b'NZBget'][b'nzbget_category_backlog'] = sickbeard.NZBGET_CATEGORY_BACKLOG
    new_config[b'NZBget'][b'nzbget_category_anime'] = sickbeard.NZBGET_CATEGORY_ANIME
    new_config[b'NZBget'][b'nzbget_category_anime_backlog'] = sickbeard.NZBGET_CATEGORY_ANIME_BACKLOG
    new_config[b'NZBget'][b'nzbget_host'] = sickbeard.NZBGET_HOST
    new_config[b'NZBget'][b'nzbget_use_https'] = int(sickbeard.NZBGET_USE_HTTPS)
    new_config[b'NZBget'][b'nzbget_priority'] = sickbeard.NZBGET_PRIORITY

    new_config[b'TORRENT'] = {}
    new_config[b'TORRENT'][b'torrent_username'] = sickbeard.TORRENT_USERNAME
    new_config[b'TORRENT'][b'torrent_password'] = encrypt(sickbeard.TORRENT_PASSWORD,
                                                          sickbeard.ENCRYPTION_VERSION)
    new_config[b'TORRENT'][b'torrent_host'] = sickbeard.TORRENT_HOST
    new_config[b'TORRENT'][b'torrent_path'] = sickbeard.TORRENT_PATH
    new_config[b'TORRENT'][b'torrent_seed_time'] = int(sickbeard.TORRENT_SEED_TIME)
    new_config[b'TORRENT'][b'torrent_paused'] = int(sickbeard.TORRENT_PAUSED)
    new_config[b'TORRENT'][b'torrent_high_bandwidth'] = int(sickbeard.TORRENT_HIGH_BANDWIDTH)
    new_config[b'TORRENT'][b'torrent_label'] = sickbeard.TORRENT_LABEL
    new_config[b'TORRENT'][b'torrent_label_anime'] = sickbeard.TORRENT_LABEL_ANIME
    new_config[b'TORRENT'][b'torrent_verify_cert'] = int(sickbeard.TORRENT_VERIFY_CERT)
    new_config[b'TORRENT'][b'torrent_rpcurl'] = sickbeard.TORRENT_RPCURL
    new_config[b'TORRENT'][b'torrent_auth_type'] = sickbeard.TORRENT_AUTH_TYPE

    new_config[b'KODI'] = {}
    new_config[b'KODI'][b'use_kodi'] = int(sickbeard.USE_KODI)
    new_config[b'KODI'][b'kodi_always_on'] = int(sickbeard.KODI_ALWAYS_ON)
    new_config[b'KODI'][b'kodi_notify_onsnatch'] = int(sickbeard.KODI_NOTIFY_ONSNATCH)
    new_config[b'KODI'][b'kodi_notify_ondownload'] = int(sickbeard.KODI_NOTIFY_ONDOWNLOAD)
    new_config[b'KODI'][b'kodi_notify_onsubtitledownload'] = int(sickbeard.KODI_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config[b'KODI'][b'kodi_update_library'] = int(sickbeard.KODI_UPDATE_LIBRARY)
    new_config[b'KODI'][b'kodi_update_full'] = int(sickbeard.KODI_UPDATE_FULL)
    new_config[b'KODI'][b'kodi_update_onlyfirst'] = int(sickbeard.KODI_UPDATE_ONLYFIRST)
    new_config[b'KODI'][b'kodi_host'] = sickbeard.KODI_HOST
    new_config[b'KODI'][b'kodi_username'] = sickbeard.KODI_USERNAME
    new_config[b'KODI'][b'kodi_password'] = encrypt(sickbeard.KODI_PASSWORD, sickbeard.ENCRYPTION_VERSION)

    new_config[b'Plex'] = {}
    new_config[b'Plex'][b'use_plex'] = int(sickbeard.USE_PLEX)
    new_config[b'Plex'][b'plex_notify_onsnatch'] = int(sickbeard.PLEX_NOTIFY_ONSNATCH)
    new_config[b'Plex'][b'plex_notify_ondownload'] = int(sickbeard.PLEX_NOTIFY_ONDOWNLOAD)
    new_config[b'Plex'][b'plex_notify_onsubtitledownload'] = int(sickbeard.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config[b'Plex'][b'plex_update_library'] = int(sickbeard.PLEX_UPDATE_LIBRARY)
    new_config[b'Plex'][b'plex_server_host'] = sickbeard.PLEX_SERVER_HOST
    new_config[b'Plex'][b'plex_server_token'] = sickbeard.PLEX_SERVER_TOKEN
    new_config[b'Plex'][b'plex_host'] = sickbeard.PLEX_HOST
    new_config[b'Plex'][b'plex_username'] = sickbeard.PLEX_USERNAME
    new_config[b'Plex'][b'plex_password'] = encrypt(sickbeard.PLEX_PASSWORD, sickbeard.ENCRYPTION_VERSION)

    new_config[b'Emby'] = {}
    new_config[b'Emby'][b'use_emby'] = int(sickbeard.USE_EMBY)
    new_config[b'Emby'][b'emby_host'] = sickbeard.EMBY_HOST
    new_config[b'Emby'][b'emby_apikey'] = sickbeard.EMBY_APIKEY

    new_config[b'Growl'] = {}
    new_config[b'Growl'][b'use_growl'] = int(sickbeard.USE_GROWL)
    new_config[b'Growl'][b'growl_notify_onsnatch'] = int(sickbeard.GROWL_NOTIFY_ONSNATCH)
    new_config[b'Growl'][b'growl_notify_ondownload'] = int(sickbeard.GROWL_NOTIFY_ONDOWNLOAD)
    new_config[b'Growl'][b'growl_notify_onsubtitledownload'] = int(sickbeard.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config[b'Growl'][b'growl_host'] = sickbeard.GROWL_HOST
    new_config[b'Growl'][b'growl_password'] = encrypt(sickbeard.GROWL_PASSWORD,
                                                      sickbeard.ENCRYPTION_VERSION)

    new_config[b'FreeMobile'] = {}
    new_config[b'FreeMobile'][b'use_freemobile'] = int(sickbeard.USE_FREEMOBILE)
    new_config[b'FreeMobile'][b'freemobile_notify_onsnatch'] = int(sickbeard.FREEMOBILE_NOTIFY_ONSNATCH)
    new_config[b'FreeMobile'][b'freemobile_notify_ondownload'] = int(sickbeard.FREEMOBILE_NOTIFY_ONDOWNLOAD)
    new_config[b'FreeMobile'][b'freemobile_notify_onsubtitledownload'] = int(
            sickbeard.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config[b'FreeMobile'][b'freemobile_id'] = sickbeard.FREEMOBILE_ID
    new_config[b'FreeMobile'][b'freemobile_apikey'] = sickbeard.FREEMOBILE_APIKEY

    new_config[b'Prowl'] = {}
    new_config[b'Prowl'][b'use_prowl'] = int(sickbeard.USE_PROWL)
    new_config[b'Prowl'][b'prowl_notify_onsnatch'] = int(sickbeard.PROWL_NOTIFY_ONSNATCH)
    new_config[b'Prowl'][b'prowl_notify_ondownload'] = int(sickbeard.PROWL_NOTIFY_ONDOWNLOAD)
    new_config[b'Prowl'][b'prowl_notify_onsubtitledownload'] = int(sickbeard.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config[b'Prowl'][b'prowl_api'] = sickbeard.PROWL_API
    new_config[b'Prowl'][b'prowl_priority'] = sickbeard.PROWL_PRIORITY

    new_config[b'Twitter'] = {}
    new_config[b'Twitter'][b'use_twitter'] = int(sickbeard.USE_TWITTER)
    new_config[b'Twitter'][b'twitter_notify_onsnatch'] = int(sickbeard.TWITTER_NOTIFY_ONSNATCH)
    new_config[b'Twitter'][b'twitter_notify_ondownload'] = int(sickbeard.TWITTER_NOTIFY_ONDOWNLOAD)
    new_config[b'Twitter'][b'twitter_notify_onsubtitledownload'] = int(sickbeard.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config[b'Twitter'][b'twitter_username'] = sickbeard.TWITTER_USERNAME
    new_config[b'Twitter'][b'twitter_password'] = encrypt(sickbeard.TWITTER_PASSWORD,
                                                          sickbeard.ENCRYPTION_VERSION)
    new_config[b'Twitter'][b'twitter_prefix'] = sickbeard.TWITTER_PREFIX
    new_config[b'Twitter'][b'twitter_dmto'] = sickbeard.TWITTER_DMTO
    new_config[b'Twitter'][b'twitter_usedm'] = int(sickbeard.TWITTER_USEDM)

    new_config[b'Boxcar'] = {}
    new_config[b'Boxcar'][b'use_boxcar'] = int(sickbeard.USE_BOXCAR)
    new_config[b'Boxcar'][b'boxcar_notify_onsnatch'] = int(sickbeard.BOXCAR_NOTIFY_ONSNATCH)
    new_config[b'Boxcar'][b'boxcar_notify_ondownload'] = int(sickbeard.BOXCAR_NOTIFY_ONDOWNLOAD)
    new_config[b'Boxcar'][b'boxcar_notify_onsubtitledownload'] = int(sickbeard.BOXCAR_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config[b'Boxcar'][b'boxcar_username'] = sickbeard.BOXCAR_USERNAME

    new_config[b'Boxcar2'] = {}
    new_config[b'Boxcar2'][b'use_boxcar2'] = int(sickbeard.USE_BOXCAR2)
    new_config[b'Boxcar2'][b'boxcar2_notify_onsnatch'] = int(sickbeard.BOXCAR2_NOTIFY_ONSNATCH)
    new_config[b'Boxcar2'][b'boxcar2_notify_ondownload'] = int(sickbeard.BOXCAR2_NOTIFY_ONDOWNLOAD)
    new_config[b'Boxcar2'][b'boxcar2_notify_onsubtitledownload'] = int(sickbeard.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config[b'Boxcar2'][b'boxcar2_accesstoken'] = sickbeard.BOXCAR2_ACCESSTOKEN

    new_config[b'Pushover'] = {}
    new_config[b'Pushover'][b'use_pushover'] = int(sickbeard.USE_PUSHOVER)
    new_config[b'Pushover'][b'pushover_notify_onsnatch'] = int(sickbeard.PUSHOVER_NOTIFY_ONSNATCH)
    new_config[b'Pushover'][b'pushover_notify_ondownload'] = int(sickbeard.PUSHOVER_NOTIFY_ONDOWNLOAD)
    new_config[b'Pushover'][b'pushover_notify_onsubtitledownload'] = int(
            sickbeard.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config[b'Pushover'][b'pushover_userkey'] = sickbeard.PUSHOVER_USERKEY
    new_config[b'Pushover'][b'pushover_apikey'] = sickbeard.PUSHOVER_APIKEY
    new_config[b'Pushover'][b'pushover_device'] = sickbeard.PUSHOVER_DEVICE
    new_config[b'Pushover'][b'pushover_sound'] = sickbeard.PUSHOVER_SOUND

    new_config[b'Libnotify'] = {}
    new_config[b'Libnotify'][b'use_libnotify'] = int(sickbeard.USE_LIBNOTIFY)
    new_config[b'Libnotify'][b'libnotify_notify_onsnatch'] = int(sickbeard.LIBNOTIFY_NOTIFY_ONSNATCH)
    new_config[b'Libnotify'][b'libnotify_notify_ondownload'] = int(sickbeard.LIBNOTIFY_NOTIFY_ONDOWNLOAD)
    new_config[b'Libnotify'][b'libnotify_notify_onsubtitledownload'] = int(
            sickbeard.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD)

    new_config[b'NMJ'] = {}
    new_config[b'NMJ'][b'use_nmj'] = int(sickbeard.USE_NMJ)
    new_config[b'NMJ'][b'nmj_host'] = sickbeard.NMJ_HOST
    new_config[b'NMJ'][b'nmj_database'] = sickbeard.NMJ_DATABASE
    new_config[b'NMJ'][b'nmj_mount'] = sickbeard.NMJ_MOUNT

    new_config[b'NMJv2'] = {}
    new_config[b'NMJv2'][b'use_nmjv2'] = int(sickbeard.USE_NMJv2)
    new_config[b'NMJv2'][b'nmjv2_host'] = sickbeard.NMJv2_HOST
    new_config[b'NMJv2'][b'nmjv2_database'] = sickbeard.NMJv2_DATABASE
    new_config[b'NMJv2'][b'nmjv2_dbloc'] = sickbeard.NMJv2_DBLOC

    new_config[b'Synology'] = {}
    new_config[b'Synology'][b'use_synoindex'] = int(sickbeard.USE_SYNOINDEX)

    new_config[b'SynologyNotifier'] = {}
    new_config[b'SynologyNotifier'][b'use_synologynotifier'] = int(sickbeard.USE_SYNOLOGYNOTIFIER)
    new_config[b'SynologyNotifier'][b'synologynotifier_notify_onsnatch'] = int(
            sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH)
    new_config[b'SynologyNotifier'][b'synologynotifier_notify_ondownload'] = int(
            sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD)
    new_config[b'SynologyNotifier'][b'synologynotifier_notify_onsubtitledownload'] = int(
            sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD)

    new_config[b'theTVDB'] = {}
    new_config[b'theTVDB'][b'thetvdb_apitoken'] = sickbeard.THETVDB_APITOKEN

    new_config[b'Trakt'] = {}
    new_config[b'Trakt'][b'use_trakt'] = int(sickbeard.USE_TRAKT)
    new_config[b'Trakt'][b'trakt_username'] = sickbeard.TRAKT_USERNAME
    new_config[b'Trakt'][b'trakt_access_token'] = sickbeard.TRAKT_ACCESS_TOKEN
    new_config[b'Trakt'][b'trakt_refresh_token'] = sickbeard.TRAKT_REFRESH_TOKEN
    new_config[b'Trakt'][b'trakt_remove_watchlist'] = int(sickbeard.TRAKT_REMOVE_WATCHLIST)
    new_config[b'Trakt'][b'trakt_remove_serieslist'] = int(sickbeard.TRAKT_REMOVE_SERIESLIST)
    new_config[b'Trakt'][b'trakt_remove_show_from_sickrage'] = int(sickbeard.TRAKT_REMOVE_SHOW_FROM_SICKRAGE)
    new_config[b'Trakt'][b'trakt_sync_watchlist'] = int(sickbeard.TRAKT_SYNC_WATCHLIST)
    new_config[b'Trakt'][b'trakt_method_add'] = int(sickbeard.TRAKT_METHOD_ADD)
    new_config[b'Trakt'][b'trakt_start_paused'] = int(sickbeard.TRAKT_START_PAUSED)
    new_config[b'Trakt'][b'trakt_use_recommended'] = int(sickbeard.TRAKT_USE_RECOMMENDED)
    new_config[b'Trakt'][b'trakt_sync'] = int(sickbeard.TRAKT_SYNC)
    new_config[b'Trakt'][b'trakt_sync_remove'] = int(sickbeard.TRAKT_SYNC_REMOVE)
    new_config[b'Trakt'][b'trakt_default_indexer'] = int(sickbeard.TRAKT_DEFAULT_INDEXER)
    new_config[b'Trakt'][b'trakt_timeout'] = int(sickbeard.TRAKT_TIMEOUT)
    new_config[b'Trakt'][b'trakt_blacklist_name'] = sickbeard.TRAKT_BLACKLIST_NAME

    new_config[b'pyTivo'] = {}
    new_config[b'pyTivo'][b'use_pytivo'] = int(sickbeard.USE_PYTIVO)
    new_config[b'pyTivo'][b'pytivo_notify_onsnatch'] = int(sickbeard.PYTIVO_NOTIFY_ONSNATCH)
    new_config[b'pyTivo'][b'pytivo_notify_ondownload'] = int(sickbeard.PYTIVO_NOTIFY_ONDOWNLOAD)
    new_config[b'pyTivo'][b'pytivo_notify_onsubtitledownload'] = int(sickbeard.PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config[b'pyTivo'][b'pyTivo_update_library'] = int(sickbeard.PYTIVO_UPDATE_LIBRARY)
    new_config[b'pyTivo'][b'pytivo_host'] = sickbeard.PYTIVO_HOST
    new_config[b'pyTivo'][b'pytivo_share_name'] = sickbeard.PYTIVO_SHARE_NAME
    new_config[b'pyTivo'][b'pytivo_tivo_name'] = sickbeard.PYTIVO_TIVO_NAME

    new_config[b'NMA'] = {}
    new_config[b'NMA'][b'use_nma'] = int(sickbeard.USE_NMA)
    new_config[b'NMA'][b'nma_notify_onsnatch'] = int(sickbeard.NMA_NOTIFY_ONSNATCH)
    new_config[b'NMA'][b'nma_notify_ondownload'] = int(sickbeard.NMA_NOTIFY_ONDOWNLOAD)
    new_config[b'NMA'][b'nma_notify_onsubtitledownload'] = int(sickbeard.NMA_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config[b'NMA'][b'nma_api'] = sickbeard.NMA_API
    new_config[b'NMA'][b'nma_priority'] = sickbeard.NMA_PRIORITY

    new_config[b'Pushalot'] = {}
    new_config[b'Pushalot'][b'use_pushalot'] = int(sickbeard.USE_PUSHALOT)
    new_config[b'Pushalot'][b'pushalot_notify_onsnatch'] = int(sickbeard.PUSHALOT_NOTIFY_ONSNATCH)
    new_config[b'Pushalot'][b'pushalot_notify_ondownload'] = int(sickbeard.PUSHALOT_NOTIFY_ONDOWNLOAD)
    new_config[b'Pushalot'][b'pushalot_notify_onsubtitledownload'] = int(
            sickbeard.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config[b'Pushalot'][b'pushalot_authorizationtoken'] = sickbeard.PUSHALOT_AUTHORIZATIONTOKEN

    new_config[b'Pushbullet'] = {}
    new_config[b'Pushbullet'][b'use_pushbullet'] = int(sickbeard.USE_PUSHBULLET)
    new_config[b'Pushbullet'][b'pushbullet_notify_onsnatch'] = int(sickbeard.PUSHBULLET_NOTIFY_ONSNATCH)
    new_config[b'Pushbullet'][b'pushbullet_notify_ondownload'] = int(sickbeard.PUSHBULLET_NOTIFY_ONDOWNLOAD)
    new_config[b'Pushbullet'][b'pushbullet_notify_onsubtitledownload'] = int(
            sickbeard.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config[b'Pushbullet'][b'pushbullet_api'] = sickbeard.PUSHBULLET_API
    new_config[b'Pushbullet'][b'pushbullet_device'] = sickbeard.PUSHBULLET_DEVICE

    new_config[b'Email'] = {}
    new_config[b'Email'][b'use_email'] = int(sickbeard.USE_EMAIL)
    new_config[b'Email'][b'email_notify_onsnatch'] = int(sickbeard.EMAIL_NOTIFY_ONSNATCH)
    new_config[b'Email'][b'email_notify_ondownload'] = int(sickbeard.EMAIL_NOTIFY_ONDOWNLOAD)
    new_config[b'Email'][b'email_notify_onsubtitledownload'] = int(sickbeard.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config[b'Email'][b'email_host'] = sickbeard.EMAIL_HOST
    new_config[b'Email'][b'email_port'] = int(sickbeard.EMAIL_PORT)
    new_config[b'Email'][b'email_tls'] = int(sickbeard.EMAIL_TLS)
    new_config[b'Email'][b'email_user'] = sickbeard.EMAIL_USER
    new_config[b'Email'][b'email_password'] = encrypt(sickbeard.EMAIL_PASSWORD,
                                                      sickbeard.ENCRYPTION_VERSION)
    new_config[b'Email'][b'email_from'] = sickbeard.EMAIL_FROM
    new_config[b'Email'][b'email_list'] = sickbeard.EMAIL_LIST

    new_config[b'Newznab'] = {}
    new_config[b'Newznab'][b'newznab_data'] = sickbeard.NEWZNAB_DATA

    new_config[b'TorrentRss'] = {}
    new_config[b'TorrentRss'][b'torrentrss_data'] = '!!!'.join(
            [x.configStr() for x in sickbeard.torrentRssProviderList])

    new_config[b'GUI'] = {}
    new_config[b'GUI'][b'gui_name'] = sickbeard.GUI_NAME
    new_config[b'GUI'][b'theme_name'] = sickbeard.THEME_NAME
    new_config[b'GUI'][b'home_layout'] = sickbeard.HOME_LAYOUT
    new_config[b'GUI'][b'history_layout'] = sickbeard.HISTORY_LAYOUT
    new_config[b'GUI'][b'history_limit'] = sickbeard.HISTORY_LIMIT
    new_config[b'GUI'][b'display_show_specials'] = int(sickbeard.DISPLAY_SHOW_SPECIALS)
    new_config[b'GUI'][b'coming_eps_layout'] = sickbeard.COMING_EPS_LAYOUT
    new_config[b'GUI'][b'coming_eps_display_paused'] = int(sickbeard.COMING_EPS_DISPLAY_PAUSED)
    new_config[b'GUI'][b'coming_eps_sort'] = sickbeard.COMING_EPS_SORT
    new_config[b'GUI'][b'coming_eps_missed_range'] = int(sickbeard.COMING_EPS_MISSED_RANGE)
    new_config[b'GUI'][b'fuzzy_dating'] = int(sickbeard.FUZZY_DATING)
    new_config[b'GUI'][b'trim_zero'] = int(sickbeard.TRIM_ZERO)
    new_config[b'GUI'][b'date_preset'] = sickbeard.DATE_PRESET
    new_config[b'GUI'][b'time_preset'] = sickbeard.TIME_PRESET_W_SECONDS
    new_config[b'GUI'][b'timezone_display'] = sickbeard.TIMEZONE_DISPLAY
    new_config[b'GUI'][b'poster_sortby'] = sickbeard.POSTER_SORTBY
    new_config[b'GUI'][b'poster_sortdir'] = sickbeard.POSTER_SORTDIR
    new_config[b'GUI'][b'filter_row'] = int(sickbeard.FILTER_ROW)

    new_config[b'Subtitles'] = {}
    new_config[b'Subtitles'][b'use_subtitles'] = int(sickbeard.USE_SUBTITLES)
    new_config[b'Subtitles'][b'subtitles_languages'] = ','.join(sickbeard.SUBTITLES_LANGUAGES)
    new_config[b'Subtitles'][b'SUBTITLES_SERVICES_LIST'] = ','.join(sickbeard.SUBTITLES_SERVICES_LIST)
    new_config[b'Subtitles'][b'SUBTITLES_SERVICES_ENABLED'] = '|'.join(
            [str(x) for x in sickbeard.SUBTITLES_SERVICES_ENABLED])
    new_config[b'Subtitles'][b'subtitles_dir'] = sickbeard.SUBTITLES_DIR
    new_config[b'Subtitles'][b'subtitles_default'] = int(sickbeard.SUBTITLES_DEFAULT)
    new_config[b'Subtitles'][b'subtitles_history'] = int(sickbeard.SUBTITLES_HISTORY)
    new_config[b'Subtitles'][b'embedded_subtitles_all'] = int(sickbeard.EMBEDDED_SUBTITLES_ALL)
    new_config[b'Subtitles'][b'subtitles_hearing_impaired'] = int(sickbeard.SUBTITLES_HEARING_IMPAIRED)
    new_config[b'Subtitles'][b'subtitles_finder_frequency'] = int(sickbeard.SUBTITLE_SEARCHER_FREQ)
    new_config[b'Subtitles'][b'subtitles_multi'] = int(sickbeard.SUBTITLES_MULTI)
    new_config[b'Subtitles'][b'subtitles_extra_scripts'] = '|'.join(sickbeard.SUBTITLES_EXTRA_SCRIPTS)

    new_config[b'Subtitles'][b'addic7ed_username'] = sickbeard.ADDIC7ED_USER
    new_config[b'Subtitles'][b'addic7ed_password'] = encrypt(sickbeard.ADDIC7ED_PASS,
                                                             sickbeard.ENCRYPTION_VERSION)

    new_config[b'Subtitles'][b'legendastv_username'] = sickbeard.LEGENDASTV_USER
    new_config[b'Subtitles'][b'legendastv_password'] = encrypt(sickbeard.LEGENDASTV_PASS,
                                                               sickbeard.ENCRYPTION_VERSION)

    new_config[b'Subtitles'][b'opensubtitles_username'] = sickbeard.OPENSUBTITLES_USER
    new_config[b'Subtitles'][b'opensubtitles_password'] = encrypt(sickbeard.OPENSUBTITLES_PASS,
                                                                  sickbeard.ENCRYPTION_VERSION)

    new_config[b'FailedDownloads'] = {}
    new_config[b'FailedDownloads'][b'use_failed_downloads'] = int(sickbeard.USE_FAILED_DOWNLOADS)
    new_config[b'FailedDownloads'][b'delete_failed'] = int(sickbeard.DELETE_FAILED)

    new_config[b'ANIDB'] = {}
    new_config[b'ANIDB'][b'use_anidb'] = int(sickbeard.USE_ANIDB)
    new_config[b'ANIDB'][b'anidb_username'] = sickbeard.ANIDB_USERNAME
    new_config[b'ANIDB'][b'anidb_password'] = encrypt(sickbeard.ANIDB_PASSWORD,
                                                      sickbeard.ENCRYPTION_VERSION)
    new_config[b'ANIDB'][b'anidb_use_mylist'] = int(sickbeard.ANIDB_USE_MYLIST)

    new_config[b'ANIME'] = {}
    new_config[b'ANIME'][b'anime_split_home'] = int(sickbeard.ANIME_SPLIT_HOME)

    # dynamically save provider settings
    for providerID, providerObj in sickbeard.providersDict[TorrentProvider.type].items():
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
                    providerObj.password, sickbeard.ENCRYPTION_VERSION)
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

    for providerID, providerObj in sickbeard.providersDict[NZBProvider.type].items():
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


def launch_browser(protocol='http', startport=8081, web_root='/'):
    browserurl = '{}://localhost:{}{}/home/'.format(protocol, startport, web_root)

    try:
        try:
            webbrowser.open(browserurl, 2, 1)
        except webbrowser.Error:
            webbrowser.open(browserurl, 1, 1)
    except webbrowser.Error:
        logging.error("Unable to launch a browser")


def get_episodes_list(epids, showid=None):
    if epids is None or len(epids) == 0:
        return []

    query = "SELECT * FROM tv_episodes WHERE indexerid in (%s)" % (",".join(['?'] * len(epids)),)
    params = epids

    if showid is not None:
        query += " AND showid = ?"
        params.append(showid)

    eplist = []
    for curEp in DBConnection().select(query, params):
        curshowobj = findCertainShow(sickbeard.showList, int(curEp[b"showid"]))
        eplist += [curshowobj.getEpisode(int(curEp[b"season"]), int(curEp[b"episode"]))]

    return eplist
