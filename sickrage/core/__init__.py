# -*- coding: utf-8 -*
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

import datetime
import os
import re
import shutil
import socket
import sys
import traceback

import sickrage
from sickrage.core.caches.name_cache import srNameCache
from sickrage.core.classes import AttrDict
from sickrage.core.common import SD, SKIPPED, WANTED
from sickrage.core.databases import main_db, cache_db, failed_db
from sickrage.core.helpers import findCertainShow, \
    generateCookieSecret, makeDir, removetree, restoreDB, get_lan_ip, get_temp_dir
from sickrage.core.nameparser.validator import check_force_season_folders
from sickrage.core.processors import auto_postprocessor
from sickrage.core.processors.auto_postprocessor import srPostProcessor
from sickrage.core.queues.search import srSearchQueue
from sickrage.core.queues.show import srShowQueue
from sickrage.core.searchers.backlog_searcher import srBacklogSearcher, \
    get_backlog_cycle_time
from sickrage.core.searchers.daily_searcher import srDailySearcher
from sickrage.core.searchers.proper_searcher import srProperSearcher
from sickrage.core.searchers.subtitle_searcher import srSubtitleSearcher
from sickrage.core.searchers.trakt_searcher import srTraktSearcher
from sickrage.core.srconfig import srConfig
from sickrage.core.srlogger import srLogger
from sickrage.core.srscheduler import srIntervalTrigger, srScheduler
from sickrage.core.tv.show import TVShow
from sickrage.core.updaters.show_updater import srShowUpdater
from sickrage.core.updaters.tz_updater import update_network_dict
from sickrage.core.version_updater import srVersionUpdater
from sickrage.core.webclient.session import srFuturesSession
from sickrage.core.webserver import srWebServer
from sickrage.indexers import adba
from sickrage.metadata import get_metadata_generator_dict, kodi, kodi_12plus, \
    mede8er, mediabrowser, ps3, tivo, wdtv
from sickrage.notifiers.boxcar import BoxcarNotifier
from sickrage.notifiers.boxcar2 import Boxcar2Notifier
from sickrage.notifiers.emailnotify import EmailNotifier
from sickrage.notifiers.emby import EMBYNotifier
from sickrage.notifiers.freemobile import FreeMobileNotifier
from sickrage.notifiers.growl import GrowlNotifier
from sickrage.notifiers.kodi import KODINotifier
from sickrage.notifiers.libnotify import LibnotifyNotifier
from sickrage.notifiers.nma import NMA_Notifier
from sickrage.notifiers.nmj import NMJNotifier
from sickrage.notifiers.nmjv2 import NMJv2Notifier
from sickrage.notifiers.plex import PLEXNotifier
from sickrage.notifiers.prowl import ProwlNotifier
from sickrage.notifiers.pushalot import PushalotNotifier
from sickrage.notifiers.pushbullet import PushbulletNotifier
from sickrage.notifiers.pushover import PushoverNotifier
from sickrage.notifiers.pytivo import pyTivoNotifier
from sickrage.notifiers.synoindex import synoIndexNotifier
from sickrage.notifiers.synologynotifier import synologyNotifier
from sickrage.notifiers.trakt import TraktNotifier
from sickrage.notifiers.tweet import TwitterNotifier
from sickrage.providers import providersDict


class Core(object):
    def __init__(self):
        self.STARTED = False
        self.RESTARTED = False

        # process id
        self.PID = os.getpid()

        # Check if we need to perform a restore first
        os.chdir(sickrage.DATA_DIR)
        restore_dir = os.path.join(sickrage.DATA_DIR, 'restore')
        if os.path.exists(restore_dir):
            success = restoreDB(restore_dir, sickrage.DATA_DIR)
            print("Restore: restoring DB and config.ini %s!\n" % ("FAILED", "SUCCESSFUL")[success])
            if success:
                os.execl(sys.executable, sys.executable, *sys.argv)

        # generate notifiers dict
        self.notifiersDict = AttrDict(
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
            email_notifier=EmailNotifier()
        )

        # generate metadata providers dict
        self.metadataProviderDict = get_metadata_generator_dict()

        # generate providers dict
        self.providersDict = providersDict()

        # init logger
        sickrage.srLogger = srLogger()

        # init config
        sickrage.srConfig = srConfig()

        # init scheduler
        sickrage.srScheduler = srScheduler()

        # init web server
        sickrage.srWebServer = srWebServer()

        # init web client session
        sickrage.srWebSession = srFuturesSession()

        # sickrage version
        self.VERSION = None
        self.NEWEST_VERSION = None
        self.NEWEST_VERSION_STRING = None

        # show list
        self.SHOWLIST = []

        # updater
        self.VERSIONUPDATER = None

        # name cache
        self.NAMECACHE = None

        # queues
        self.SHOWUPDATER = None
        self.SHOWQUEUE = None
        self.SEARCHQUEUE = None

        # searchers
        self.DAILYSEARCHER = None
        self.BACKLOGSEARCHER = None
        self.PROPERSEARCHER = None
        self.TRAKTSEARCHER = None
        self.SUBTITLESEARCHER = None

        # auto postprocessor
        self.AUTOPOSTPROCESSOR = None

        # anidb connection
        self.ADBA_CONNECTION = None

    def start(self):
        sickrage.srConfig.load()
        self.STARTED = True

        # setup logger settings
        sickrage.srLogger.logSize = sickrage.srConfig.LOG_SIZE
        sickrage.srLogger.logNr = sickrage.srConfig.LOG_NR
        sickrage.srLogger.debugLogging = sickrage.DEBUG
        sickrage.srLogger.consoleLogging = not sickrage.QUITE
        sickrage.srLogger.logFile = os.path.abspath(os.path.join(
            sickrage.DATA_DIR,
            sickrage.srConfig.LOG_DIR,
            sickrage.srConfig.LOG_FILE
        ))

        # start logger
        sickrage.srLogger.start()

        # set socket timeout
        socket.setdefaulttimeout(sickrage.srConfig.SOCKET_TIMEOUT)

        # init version updater
        self.VERSIONUPDATER = srVersionUpdater()

        # init updater and get current version
        self.VERSION = self.VERSIONUPDATER.updater.version

        # init caches
        self.NAMECACHE = srNameCache()

        # init queues
        self.SHOWUPDATER = srShowUpdater()
        self.SHOWQUEUE = srShowQueue()
        self.SEARCHQUEUE = srSearchQueue()

        # init searchers
        self.DAILYSEARCHER = srDailySearcher()
        self.BACKLOGSEARCHER = srBacklogSearcher()
        self.PROPERSEARCHER = srProperSearcher()
        self.TRAKTSEARCHER = srTraktSearcher()
        self.SUBTITLESEARCHER = srSubtitleSearcher()

        # init postprocessor
        self.AUTOPOSTPROCESSOR = srPostProcessor()

        # migrate old database file names to new ones
        if not os.path.exists(main_db.MainDB().filename) and os.path.exists("sickbeard.db"):
            helpers.moveFile("sickbeard.db", main_db.MainDB().filename)

        # initialize the main SB database
        main_db.MainDB().InitialSchema().upgrade()

        # initialize the cache database
        cache_db.CacheDB().InitialSchema().upgrade()

        # initialize the failed downloads database
        failed_db.FailedDB().InitialSchema().upgrade()

        # fix up any db problems
        main_db.MainDB().SanityCheck()

        # load data for shows from database
        self.load_shows()

        if sickrage.srConfig.DEFAULT_PAGE not in ('home', 'schedule', 'history', 'news', 'IRC'):
            sickrage.srConfig.DEFAULT_PAGE = 'home'

        if not makeDir(sickrage.srConfig.CACHE_DIR):
            sickrage.srLogger.error("!!! Creating local cache dir failed")
            sickrage.srConfig.CACHE_DIR = get_temp_dir()

        # Check if we need to perform a restore of the cache folder
        try:
            restore_dir = os.path.join(sickrage.DATA_DIR, 'restore')
            if os.path.exists(restore_dir) and os.path.exists(os.path.join(restore_dir, 'cache')):
                def restore_cache(src_dir, dst_dir):
                    def path_leaf(path):
                        head, tail = os.path.split(path)
                        return tail or os.path.basename(head)

                    try:
                        if os.path.isdir(dst_dir):
                            bak_filename = '{}-{}'.format(path_leaf(dst_dir),
                                                          datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
                            shutil.move(dst_dir, os.path.join(os.path.dirname(dst_dir), bak_filename))

                        shutil.move(src_dir, dst_dir)
                        sickrage.srLogger.info("Restore: restoring cache successful")
                    except Exception as E:
                        sickrage.srLogger.error("Restore: restoring cache failed: {}".format(E.message))

                restore_cache(os.path.join(restore_dir, 'cache'), sickrage.srConfig.CACHE_DIR)
        except Exception as e:
            sickrage.srLogger.error("Restore: restoring cache failed: {}".format(e.message))
        finally:
            if os.path.exists(os.path.join(sickrage.DATA_DIR, 'restore')):
                try:
                    removetree(os.path.join(sickrage.DATA_DIR, 'restore'))
                except Exception as e:
                    sickrage.srLogger.error("Restore: Unable to remove the restore directory: {}".format(e.message))

                for cleanupDir in ['mako', 'sessions', 'indexers']:
                    try:
                        removetree(os.path.join(sickrage.srConfig.CACHE_DIR, cleanupDir))
                    except Exception as e:
                        sickrage.srLogger.warning(
                            "Restore: Unable to remove the cache/{} directory: {1}".format(cleanupDir, e))


        # init anidb connection
        if not sickrage.srConfig.USE_ANIDB:
            try:
                self.ADBA_CONNECTION = adba.Connection(keepAlive=True, log=lambda msg: sickrage.srLogger.debug(
                    "AniDB: %s " % msg)).auth(sickrage.srConfig.ANIDB_USERNAME, sickrage.srConfig.ANIDB_PASSWORD)
            except Exception as e:
                sickrage.srLogger.warning("AniDB exception msg: %r " % repr(e))

        if sickrage.srConfig.WEB_PORT < 21 or sickrage.srConfig.WEB_PORT > 65535:
            sickrage.srConfig.WEB_PORT = 8081

        if not sickrage.srConfig.WEB_COOKIE_SECRET:
            sickrage.srConfig.WEB_COOKIE_SECRET = generateCookieSecret()

        # attempt to help prevent users from breaking links by using a bad url
        if not sickrage.srConfig.ANON_REDIRECT.endswith('?'):
            sickrage.srConfig.ANON_REDIRECT = ''

        if not re.match(r'\d+\|[^|]+(?:\|[^|]+)*', sickrage.srConfig.ROOT_DIRS):
            sickrage.srConfig.ROOT_DIRS = ''

        sickrage.srConfig.NAMING_FORCE_FOLDERS = check_force_season_folders()
        if sickrage.srConfig.NZB_METHOD not in ('blackhole', 'sabnzbd', 'nzbget'):
            sickrage.srConfig.NZB_METHOD = 'blackhole'

        if sickrage.srConfig.TORRENT_METHOD not in (
                'blackhole', 'utorrent', 'transmission', 'deluge', 'deluged', 'download_station', 'rtorrent',
                'qbittorrent', 'mlnet'):
            sickrage.srConfig.TORRENT_METHOD = 'blackhole'

        if sickrage.srConfig.PROPER_SEARCHER_INTERVAL not in ('15m', '45m', '90m', '4h', 'daily'):
            sickrage.srConfig.PROPER_SEARCHER_INTERVAL = 'daily'

        if sickrage.srConfig.AUTOPOSTPROCESSOR_FREQ < sickrage.srConfig.MIN_AUTOPOSTPROCESSOR_FREQ:
            sickrage.srConfig.AUTOPOSTPROCESSOR_FREQ = sickrage.srConfig.MIN_AUTOPOSTPROCESSOR_FREQ

        if sickrage.srConfig.NAMECACHE_FREQ < sickrage.srConfig.MIN_NAMECACHE_FREQ:
            sickrage.srConfig.NAMECACHE_FREQ = sickrage.srConfig.MIN_NAMECACHE_FREQ

        if sickrage.srConfig.DAILY_SEARCHER_FREQ < sickrage.srConfig.MIN_DAILY_SEARCHER_FREQ:
            sickrage.srConfig.DAILY_SEARCHER_FREQ = sickrage.srConfig.MIN_DAILY_SEARCHER_FREQ

        sickrage.srConfig.MIN_BACKLOG_SEARCHER_FREQ = get_backlog_cycle_time()
        if sickrage.srConfig.BACKLOG_SEARCHER_FREQ < sickrage.srConfig.MIN_BACKLOG_SEARCHER_FREQ:
            sickrage.srConfig.BACKLOG_SEARCHER_FREQ = sickrage.srConfig.MIN_BACKLOG_SEARCHER_FREQ

        if sickrage.srConfig.VERSION_UPDATER_FREQ < sickrage.srConfig.MIN_VERSION_UPDATER_FREQ:
            sickrage.srConfig.VERSION_UPDATER_FREQ = sickrage.srConfig.MIN_VERSION_UPDATER_FREQ

        if sickrage.srConfig.SHOWUPDATE_HOUR > 23:
            sickrage.srConfig.SHOWUPDATE_HOUR = 0
        elif sickrage.srConfig.SHOWUPDATE_HOUR < 0:
            sickrage.srConfig.SHOWUPDATE_HOUR = 0

        if sickrage.srConfig.SUBTITLE_SEARCHER_FREQ < sickrage.srConfig.MIN_SUBTITLE_SEARCHER_FREQ:
            sickrage.srConfig.SUBTITLE_SEARCHER_FREQ = sickrage.srConfig.MIN_SUBTITLE_SEARCHER_FREQ

        sickrage.srConfig.NEWS_LATEST = sickrage.srConfig.NEWS_LAST_READ

        if sickrage.srConfig.SUBTITLES_LANGUAGES[0] == '':
            sickrage.srConfig.SUBTITLES_LANGUAGES = []

        # initialize metadata_providers
        for cur_metadata_tuple in [(sickrage.srConfig.METADATA_KODI, kodi),
                                   (sickrage.srConfig.METADATA_KODI_12PLUS, kodi_12plus),
                                   (sickrage.srConfig.METADATA_MEDIABROWSER, mediabrowser),
                                   (sickrage.srConfig.METADATA_PS3, ps3),
                                   (sickrage.srConfig.METADATA_WDTV, wdtv),
                                   (sickrage.srConfig.METADATA_TIVO, tivo),
                                   (sickrage.srConfig.METADATA_MEDE8ER, mede8er)]:
            (cur_metadata_config, cur_metadata_class) = cur_metadata_tuple
            tmp_provider = cur_metadata_class.metadata_class()
            tmp_provider.set_config(cur_metadata_config)

            self.metadataProviderDict[tmp_provider.name] = tmp_provider

        # add version checker job to scheduler
        sickrage.srScheduler.add_job(
            self.VERSIONUPDATER.run,
            srIntervalTrigger(
                **{'hours': sickrage.srConfig.VERSION_UPDATER_FREQ, 'min': sickrage.srConfig.MIN_VERSION_UPDATER_FREQ}),
            name="VERSIONUPDATER",
            id="VERSIONUPDATER",
            replace_existing=True
        )

        # add network timezones updater job to scheduler
        sickrage.srScheduler.add_job(
            update_network_dict,
            srIntervalTrigger(**{'days': 1}),
            name="TZUPDATER",
            id="TZUPDATER",
            replace_existing=True
        )

        # add namecache updater job to scheduler
        sickrage.srScheduler.add_job(
            self.NAMECACHE.run,
            srIntervalTrigger(
                **{'minutes': sickrage.srConfig.NAMECACHE_FREQ, 'min': sickrage.srConfig.MIN_NAMECACHE_FREQ}),
            name="NAMECACHE",
            id="NAMECACHE",
            replace_existing=True
        )

        # add show queue job to scheduler
        sickrage.srScheduler.add_job(
            self.SHOWQUEUE.run,
            srIntervalTrigger(**{'seconds': 3}),
            name="SHOWQUEUE",
            id="SHOWQUEUE",
            replace_existing=True
        )

        # add search queue job to scheduler
        sickrage.srScheduler.add_job(
            self.SEARCHQUEUE.run,
            srIntervalTrigger(**{'seconds': 1}),
            name="SEARCHQUEUE",
            id="SEARCHQUEUE",
            replace_existing=True
        )

        # add show updater job to scheduler
        sickrage.srScheduler.add_job(
            self.SHOWUPDATER.run,
            srIntervalTrigger(
                **{'hours': 1,
                   'start_date': datetime.datetime.now().replace(hour=sickrage.srConfig.SHOWUPDATE_HOUR)}),
            name="SHOWUPDATER",
            id="SHOWUPDATER",
            replace_existing=True
        )

        # add daily search job to scheduler
        sickrage.srScheduler.add_job(
            self.DAILYSEARCHER.run,
            srIntervalTrigger(
                **{'minutes': sickrage.srConfig.DAILY_SEARCHER_FREQ, 'min': sickrage.srConfig.MIN_DAILY_SEARCHER_FREQ}),
            name="DAILYSEARCHER",
            id="DAILYSEARCHER",
            replace_existing=True
        )

        # add backlog search job to scheduler
        sickrage.srScheduler.add_job(
            self.BACKLOGSEARCHER.run,
            srIntervalTrigger(
                **{'minutes': sickrage.srConfig.BACKLOG_SEARCHER_FREQ,
                   'min': sickrage.srConfig.MIN_BACKLOG_SEARCHER_FREQ}),
            name="BACKLOG",
            id="BACKLOG",
            replace_existing=True
        )

        # add auto-postprocessing job to scheduler
        job = sickrage.srScheduler.add_job(
            self.AUTOPOSTPROCESSOR.run,
            srIntervalTrigger(**{'minutes': sickrage.srConfig.AUTOPOSTPROCESSOR_FREQ,
                                 'min': sickrage.srConfig.MIN_AUTOPOSTPROCESSOR_FREQ}),
            name="POSTPROCESSOR",
            id="POSTPROCESSOR",
            replace_existing=True
        )
        (job.pause, job.resume)[sickrage.srConfig.PROCESS_AUTOMATICALLY]()

        # add find proper job to scheduler
        job = sickrage.srScheduler.add_job(
            self.PROPERSEARCHER.run,
            srIntervalTrigger(**{
                'minutes': {'15m': 15, '45m': 45, '90m': 90, '4h': 4 * 60, 'daily': 24 * 60}[
                    sickrage.srConfig.PROPER_SEARCHER_INTERVAL]}),
            name="PROPERSEARCHER",
            id="PROPERSEARCHER",
            replace_existing=True
        )
        (job.pause, job.resume)[sickrage.srConfig.DOWNLOAD_PROPERS]()

        # add trakt.tv checker job to scheduler
        job = sickrage.srScheduler.add_job(
            self.TRAKTSEARCHER.run,
            srIntervalTrigger(**{'hours': 1}),
            name="TRAKTSEARCHER",
            id="TRAKTSEARCHER",
            replace_existing=True,
        )
        (job.pause, job.resume)[sickrage.srConfig.USE_TRAKT]()

        # add subtitles finder job to scheduler
        job = sickrage.srScheduler.add_job(
            self.SUBTITLESEARCHER.run,
            srIntervalTrigger(**{'hours': sickrage.srConfig.SUBTITLE_SEARCHER_FREQ}),
            name="SUBTITLESEARCHER",
            id="SUBTITLESEARCHER",
            replace_existing=True
        )
        (job.pause, job.resume)[sickrage.srConfig.USE_SUBTITLES]()

        # start scheduler
        sickrage.srScheduler.start()

        # start webserver
        sickrage.srWebServer.start()

    def shutdown(self, status=None, restart=False):
        self.RESTARTED = restart

        if self.STARTED:
            if restart:
                sickrage.srLogger.info('SiCKRAGE IS PERFORMING A RESTART!')
            else:
                sickrage.srLogger.info('SiCKRAGE IS PERFORMING A SHUTDOWN!')

            # stop all background services
            sickrage.srLogger.info("Aborting all threads")

            # shutdown scheduler
            sickrage.srLogger.info("Shutting down scheduler jobs")
            sickrage.srScheduler.shutdown()

            if sickrage.srCore.ADBA_CONNECTION:
                sickrage.srLogger.info("Logging out ANIDB connection")
                sickrage.srCore.ADBA_CONNECTION.logout()

            # save all settings
            self.save_all()

            # shutdown/restart webserver
            sickrage.srWebServer.shutdown()

            if restart:
                sickrage.srLogger.info('SiCKRAGE IS RESTARTING!')
            else:
                sickrage.srLogger.info('SiCKRAGE IS SHUTDOWN!')

            # shutdown logging
            sickrage.srLogger.shutdown()

        # delete pid file
        if sickrage.DAEMONIZE:
            sickrage.delpid(sickrage.PIDFILE)

        # system exit with status
        if not restart:
            sys.exit(status)

    def save_all(self):
        # write all shows
        sickrage.srLogger.info("Saving all shows to the database")
        for SHOW in self.SHOWLIST:
            try:
                SHOW.saveToDB()
            except:
                continue

        # save config
        sickrage.srConfig.save()

    def load_shows(self):
        """
        Populates the showlist with shows from the database
        """

        for sqlShow in main_db.MainDB().select("SELECT * FROM tv_shows"):
            try:
                curshow = TVShow(int(sqlShow["indexer"]), int(sqlShow["indexer_id"]))
                sickrage.srLogger.debug("Loading data for show: [{}]".format(curshow.name))
                self.NAMECACHE.buildNameCache(curshow)
                curshow.nextEpisode()
                self.SHOWLIST += [curshow]
            except Exception as e:
                sickrage.srLogger.error(
                    "There was an error creating the show in {}: {}".format(sqlShow["location"], e.message))
                sickrage.srLogger.debug(traceback.format_exc())
                continue
