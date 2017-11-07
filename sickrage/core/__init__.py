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

from __future__ import unicode_literals

import datetime
import os
import platform
import re
import shutil
import socket
import sys
import threading
import time
import traceback
import urllib
import urlparse
import uuid

import adba
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fake_useragent import UserAgent
from pytz import utc
from tornado.ioloop import IOLoop
from tzlocal import get_localzone

import sickrage
from sickrage.core.caches.name_cache import srNameCache
from sickrage.core.common import SD, SKIPPED, WANTED
from sickrage.core.databases.cache import CacheDB
from sickrage.core.databases.failed import FailedDB
from sickrage.core.databases.main import MainDB
from sickrage.core.google import googleAuth
from sickrage.core.helpers import findCertainShow, \
    generateCookieSecret, makeDir, get_lan_ip, restoreSR, getDiskSpaceUsage, getFreeSpace, launch_browser
from sickrage.core.helpers.encoding import get_sys_encoding, ek, patch_modules
from sickrage.core.nameparser.validator import check_force_season_folders
from sickrage.core.processors import auto_postprocessor
from sickrage.core.processors.auto_postprocessor import srPostProcessor
from sickrage.core.queues.postprocessor import srPostProcessorQueue
from sickrage.core.queues.search import srSearchQueue
from sickrage.core.queues.show import srShowQueue
from sickrage.core.searchers.backlog_searcher import srBacklogSearcher
from sickrage.core.searchers.daily_searcher import srDailySearcher
from sickrage.core.searchers.proper_searcher import srProperSearcher
from sickrage.core.searchers.subtitle_searcher import srSubtitleSearcher
from sickrage.core.searchers.trakt_searcher import srTraktSearcher
from sickrage.core.srconfig import srConfig
from sickrage.core.srlogger import srLogger
from sickrage.core.tv.show import TVShow
from sickrage.core.ui import Notifications
from sickrage.core.updaters.show_updater import srShowUpdater
from sickrage.core.updaters.tz_updater import update_network_dict
from sickrage.core.version_updater import srVersionUpdater
from sickrage.core.webclient.session import srSession
from sickrage.core.webserver import srWebServer
from sickrage.metadata import metadataProvidersDict
from sickrage.notifiers import notifiersDict
from sickrage.providers import providersDict


class Core(object):
    def __init__(self):
        self.started = False
        self.daemon = None
        self.io_loop = IOLoop().instance()

        self.CONFIG_FILE = None
        self.DATA_DIR = None
        self.CACHE_DIR = None
        self.QUITE = None
        self.NOLAUNCH = None
        self.WEB_PORT = None
        self.DEVELOPER = None
        self.DEBUG = None
        self.NEWEST_VERSION = None
        self.NEWEST_VERSION_STRING = None
        self.ADBA_CONNECTION = None
        self.SHOWLIST = []

        self.PID = os.getpid()
        self.USER_AGENT = 'SiCKRAGE.CE.1/({};{};{})'.format(platform.system(), platform.release(), str(uuid.uuid1()))
        self.SYS_ENCODING = get_sys_encoding()
        self.LANGUAGES = [language for language in os.listdir(sickrage.LOCALE_DIR) if '_' in language]

        self.notifiersDict = None
        self.metadataProvidersDict = None
        self.providersDict = None
        self.srNotifications = None
        self.log = None
        self.config = None
        self.mainDB = None
        self.cacheDB = None
        self.failedDB = None
        self.srScheduler = None
        self.srWebServer = None
        self.srWebSession = None
        self.googleAuth = None
        self.NAMECACHE = None
        self.SHOWQUEUE = None
        self.SEARCHQUEUE = None
        self.POSTPROCESSORQUEUE = None
        self.VERSIONUPDATER = None
        self.SHOWUPDATER = None
        self.DAILYSEARCHER = None
        self.BACKLOGSEARCHER = None
        self.PROPERSEARCHER = None
        self.TRAKTSEARCHER = None
        self.SUBTITLESEARCHER = None
        self.AUTOPOSTPROCESSOR = None

        # patch modules with encoding kludge
        patch_modules()

    def start(self):
        self.started = True

        # thread name
        threading.currentThread().setName('CORE')

        # init core classes
        self.notifiersDict = notifiersDict()
        self.metadataProvidersDict = metadataProvidersDict()
        self.providersDict = providersDict()
        self.srNotifications = Notifications()
        self.log = srLogger()
        self.config = srConfig()
        self.mainDB = MainDB()
        self.cacheDB = CacheDB()
        self.failedDB = FailedDB()
        self.srScheduler = BackgroundScheduler()
        self.srWebServer = srWebServer()
        self.srWebSession = srSession()
        self.googleAuth = googleAuth()
        self.NAMECACHE = srNameCache()
        self.SHOWQUEUE = srShowQueue()
        self.SEARCHQUEUE = srSearchQueue()
        self.POSTPROCESSORQUEUE = srPostProcessorQueue()
        self.VERSIONUPDATER = srVersionUpdater()
        self.SHOWUPDATER = srShowUpdater()
        self.DAILYSEARCHER = srDailySearcher()
        self.BACKLOGSEARCHER = srBacklogSearcher()
        self.PROPERSEARCHER = srProperSearcher()
        self.TRAKTSEARCHER = srTraktSearcher()
        self.SUBTITLESEARCHER = srSubtitleSearcher()
        self.AUTOPOSTPROCESSOR = srPostProcessor()

        # Check if we need to perform a restore first
        if os.path.exists(os.path.abspath(os.path.join(self.DATA_DIR, 'restore'))):
            success = restoreSR(os.path.abspath(os.path.join(self.DATA_DIR, 'restore')), self.DATA_DIR)
            print("Restoring SiCKRAGE backup: %s!\n" % ("FAILED", "SUCCESSFUL")[success])
            if success:
                shutil.rmtree(os.path.abspath(os.path.join(self.DATA_DIR, 'restore')), ignore_errors=True)

        # migrate old database file names to new ones
        if os.path.isfile(os.path.abspath(os.path.join(self.DATA_DIR, 'sickbeard.db'))):
            if os.path.isfile(os.path.join(self.DATA_DIR, 'sickrage.db')):
                helpers.moveFile(os.path.join(self.DATA_DIR, 'sickrage.db'),
                                 os.path.join(self.DATA_DIR, '{}.bak-{}'
                                              .format('sickrage.db',
                                                      datetime.datetime.now().strftime(
                                                          '%Y%m%d_%H%M%S'))))

            helpers.moveFile(os.path.abspath(os.path.join(self.DATA_DIR, 'sickbeard.db')),
                             os.path.abspath(os.path.join(self.DATA_DIR, 'sickrage.db')))

        # load config
        self.srConfig.load()

        # set language
        self.srConfig.change_gui_lang(self.srConfig.GUI_LANG)

        # set socket timeout
        socket.setdefaulttimeout(self.srConfig.SOCKET_TIMEOUT)

        # setup logger settings
        self.srLogger.logSize = self.srConfig.LOG_SIZE
        self.srLogger.logNr = self.srConfig.LOG_NR
        self.srLogger.logFile = os.path.join(self.DATA_DIR, 'logs', 'sickrage.log')
        self.srLogger.debugLogging = self.srConfig.DEBUG
        self.srLogger.consoleLogging = not self.QUITE

        # start logger
        self.srLogger.start()

        # user agent
        if self.srConfig.RANDOM_USER_AGENT:
            self.USER_AGENT = UserAgent().random

        urlparse.uses_netloc.append('scgi')
        urllib.FancyURLopener.version = self.USER_AGENT

        # Check available space
        try:
            total_space, available_space = getFreeSpace(self.DATA_DIR)
            if available_space < 100:
                self.srLogger.error(
                    'Shutting down as SiCKRAGE needs some space to work. You\'ll get corrupted data otherwise. Only %sMB left',
                    available_space)
                return
        except:
            self.srLogger.error('Failed getting diskspace: %s', traceback.format_exc())

        # perform database startup actions
        for db in [self.mainDB, self.cacheDB, self.failedDB]:
            # initialize database
            db.initialize()

            # check integrity of database
            db.check_integrity()

            # migrate database
            db.migrate()

            # misc database cleanups
            db.cleanup()

        # compact main database
        if not self.srConfig.DEVELOPER and self.srConfig.LAST_DB_COMPACT < time.time() - 604800:  # 7 days
            self.mainDB.compact()
            self.srConfig.LAST_DB_COMPACT = int(time.time())

        # load name cache
        self.NAMECACHE.load()

        # load data for shows from database
        self.load_shows()

        if self.srConfig.DEFAULT_PAGE not in ('home', 'schedule', 'history', 'news', 'IRC'):
            self.srConfig.DEFAULT_PAGE = 'home'

        # cleanup cache folder
        for folder in ['mako', 'sessions', 'indexers']:
            try:
                shutil.rmtree(os.path.join(sickrage.app.CACHE_DIR, folder), ignore_errors=True)
            except Exception:
                continue

        # init anidb connection
        if self.srConfig.USE_ANIDB:
            def anidb_logger(msg):
                return self.srLogger.debug("AniDB: {} ".format(msg))

            try:
                self.ADBA_CONNECTION = adba.Connection(keepAlive=True, log=anidb_logger)
                self.ADBA_CONNECTION.auth(self.srConfig.ANIDB_USERNAME, self.srConfig.ANIDB_PASSWORD)
            except Exception as e:
                self.srLogger.warning("AniDB exception msg: %r " % repr(e))

        if self.srConfig.WEB_PORT < 21 or self.srConfig.WEB_PORT > 65535:
            self.srConfig.WEB_PORT = 8081

        if not self.srConfig.WEB_COOKIE_SECRET:
            self.srConfig.WEB_COOKIE_SECRET = generateCookieSecret()

        # attempt to help prevent users from breaking links by using a bad url
        if not self.srConfig.ANON_REDIRECT.endswith('?'):
            self.srConfig.ANON_REDIRECT = ''

        if not re.match(r'\d+\|[^|]+(?:\|[^|]+)*', self.srConfig.ROOT_DIRS):
            self.srConfig.ROOT_DIRS = ''

        self.srConfig.NAMING_FORCE_FOLDERS = check_force_season_folders()
        if self.srConfig.NZB_METHOD not in ('blackhole', 'sabnzbd', 'nzbget'):
            self.srConfig.NZB_METHOD = 'blackhole'

        if self.srConfig.TORRENT_METHOD not in ('blackhole',
                                                'utorrent',
                                                'transmission',
                                                'deluge',
                                                'deluged',
                                                'download_station',
                                                'rtorrent',
                                                'qbittorrent',
                                                'mlnet',
                                                'putio'): self.srConfig.TORRENT_METHOD = 'blackhole'

        if self.srConfig.AUTOPOSTPROCESSOR_FREQ < self.srConfig.MIN_AUTOPOSTPROCESSOR_FREQ:
            self.srConfig.AUTOPOSTPROCESSOR_FREQ = self.srConfig.MIN_AUTOPOSTPROCESSOR_FREQ
        if self.srConfig.DAILY_SEARCHER_FREQ < self.srConfig.MIN_DAILY_SEARCHER_FREQ:
            self.srConfig.DAILY_SEARCHER_FREQ = self.srConfig.MIN_DAILY_SEARCHER_FREQ
        self.srConfig.MIN_BACKLOG_SEARCHER_FREQ = self.BACKLOGSEARCHER.get_backlog_cycle_time()
        if self.srConfig.BACKLOG_SEARCHER_FREQ < self.srConfig.MIN_BACKLOG_SEARCHER_FREQ:
            self.srConfig.BACKLOG_SEARCHER_FREQ = self.srConfig.MIN_BACKLOG_SEARCHER_FREQ
        if self.srConfig.VERSION_UPDATER_FREQ < self.srConfig.MIN_VERSION_UPDATER_FREQ:
            self.srConfig.VERSION_UPDATER_FREQ = self.srConfig.MIN_VERSION_UPDATER_FREQ
        if self.srConfig.SUBTITLE_SEARCHER_FREQ < self.srConfig.MIN_SUBTITLE_SEARCHER_FREQ:
            self.srConfig.SUBTITLE_SEARCHER_FREQ = self.srConfig.MIN_SUBTITLE_SEARCHER_FREQ
        if self.srConfig.PROPER_SEARCHER_INTERVAL not in ('15m', '45m', '90m', '4h', 'daily'):
            self.srConfig.PROPER_SEARCHER_INTERVAL = 'daily'
        if self.srConfig.SHOWUPDATE_HOUR < 0 or self.srConfig.SHOWUPDATE_HOUR > 23:
            self.srConfig.SHOWUPDATE_HOUR = 0
        if self.srConfig.SUBTITLES_LANGUAGES[0] == '':
            self.srConfig.SUBTITLES_LANGUAGES = []

        # add version checker job
        self.srScheduler.add_job(
            self.VERSIONUPDATER.run,
            IntervalTrigger(
                hours=self.srConfig.VERSION_UPDATER_FREQ
            ),
            name="VERSIONUPDATER",
            id="VERSIONUPDATER"
        )

        # add network timezones updater job
        self.srScheduler.add_job(
            update_network_dict,
            IntervalTrigger(
                days=1
            ),
            name="TZUPDATER",
            id="TZUPDATER"
        )

        # add show updater job
        self.srScheduler.add_job(
            self.SHOWUPDATER.run,
            IntervalTrigger(
                days=1,
                start_date=utc.localize(datetime.datetime.now().replace(hour=self.srConfig.SHOWUPDATE_HOUR)).astimezone(
                    get_localzone())
            ),
            name="SHOWUPDATER",
            id="SHOWUPDATER"
        )

        # add daily search job
        self.srScheduler.add_job(
            self.DAILYSEARCHER.run,
            IntervalTrigger(
                minutes=self.srConfig.DAILY_SEARCHER_FREQ,
                start_date=utc.localize(datetime.datetime.now() + datetime.timedelta(minutes=4)).astimezone(
                    get_localzone())
            ),
            name="DAILYSEARCHER",
            id="DAILYSEARCHER"
        )

        # add backlog search job
        self.srScheduler.add_job(
            self.BACKLOGSEARCHER.run,
            IntervalTrigger(
                minutes=self.srConfig.BACKLOG_SEARCHER_FREQ,
                start_date=utc.localize(datetime.datetime.now() + datetime.timedelta(minutes=30)).astimezone(
                    get_localzone())
            ),
            name="BACKLOG",
            id="BACKLOG"
        )

        # add auto-postprocessing job
        self.srScheduler.add_job(
            self.AUTOPOSTPROCESSOR.run,
            IntervalTrigger(
                minutes=self.srConfig.AUTOPOSTPROCESSOR_FREQ
            ),
            name="POSTPROCESSOR",
            id="POSTPROCESSOR"
        )

        # add find proper job
        self.srScheduler.add_job(
            self.PROPERSEARCHER.run,
            IntervalTrigger(
                minutes={'15m': 15, '45m': 45, '90m': 90, '4h': 4 * 60, 'daily': 24 * 60}[
                    self.srConfig.PROPER_SEARCHER_INTERVAL]
            ),
            name="PROPERSEARCHER",
            id="PROPERSEARCHER"
        )

        # add trakt.tv checker job
        self.srScheduler.add_job(
            self.TRAKTSEARCHER.run,
            IntervalTrigger(
                hours=1
            ),
            name="TRAKTSEARCHER",
            id="TRAKTSEARCHER"
        )

        # add subtitles finder job
        self.srScheduler.add_job(
            self.SUBTITLESEARCHER.run,
            IntervalTrigger(
                hours=self.srConfig.SUBTITLE_SEARCHER_FREQ
            ),
            name="SUBTITLESEARCHER",
            id="SUBTITLESEARCHER"
        )

        # start scheduler service
        self.srScheduler.start()

        # Pause/Resume PROPERSEARCHER job
        (self.srScheduler.get_job('PROPERSEARCHER').pause,
         self.srScheduler.get_job('PROPERSEARCHER').resume
         )[self.srConfig.DOWNLOAD_PROPERS]()

        # Pause/Resume TRAKTSEARCHER job
        (self.srScheduler.get_job('TRAKTSEARCHER').pause,
         self.srScheduler.get_job('TRAKTSEARCHER').resume
         )[self.srConfig.USE_TRAKT]()

        # Pause/Resume SUBTITLESEARCHER job
        (self.srScheduler.get_job('SUBTITLESEARCHER').pause,
         self.srScheduler.get_job('SUBTITLESEARCHER').resume
         )[self.srConfig.USE_SUBTITLES]()

        # Pause/Resume POSTPROCESS job
        (self.srScheduler.get_job('POSTPROCESSOR').pause,
         self.srScheduler.get_job('POSTPROCESSOR').resume
         )[self.srConfig.PROCESS_AUTOMATICALLY]()

        # start queue's
        self.SEARCHQUEUE.start()
        self.SHOWQUEUE.start()
        self.POSTPROCESSORQUEUE.start()

        # start webserver
        self.srWebServer.start()

    def shutdown(self, restart=False):
        if self.started:
            self.srLogger.info('SiCKRAGE IS SHUTTING DOWN!!!')

            # shutdown webserver
            self.srWebServer.shutdown()

            # shutdown show queue
            if self.SHOWQUEUE:
                self.srLogger.debug("Shutting down show queue")
                self.SHOWQUEUE.shutdown()
                del self.SHOWQUEUE

            # shutdown search queue
            if self.SEARCHQUEUE:
                self.srLogger.debug("Shutting down search queue")
                self.SEARCHQUEUE.shutdown()
                del self.SEARCHQUEUE

            # shutdown post-processor queue
            if self.POSTPROCESSORQUEUE:
                self.srLogger.debug("Shutting down post-processor queue")
                self.POSTPROCESSORQUEUE.shutdown()
                del self.POSTPROCESSORQUEUE

            # log out of ADBA
            if self.ADBA_CONNECTION:
                self.srLogger.debug("Shutting down ANIDB connection")
                self.ADBA_CONNECTION.stop()

            # save all show and config settings
            self.save_all()

            # close databases
            for db in [self.mainDB, self.cacheDB, self.failedDB]:
                if db.opened:
                    self.srLogger.debug("Shutting down {} database connection".format(db.name))
                    db.close()

            # shutdown logging
            self.srLogger.close()

        if restart:
            os.execl(sys.executable, sys.executable, *sys.argv)
        elif sickrage.app.daemon:
            sickrage.app.daemon.stop()

        self.started = False

    def save_all(self):
        # write all shows
        self.srLogger.info("Saving all shows to the database")
        for SHOW in self.SHOWLIST:
            try:
                SHOW.saveToDB()
            except:
                continue

        # save config
        self.srConfig.save()

    def load_shows(self):
        """
        Populates the showlist with shows from the database
        """

        for dbData in [x['doc'] for x in self.mainDB.db.all('tv_shows', with_doc=True)]:
            try:
                self.srLogger.debug("Loading data for show: [{}]".format(dbData['show_name']))
                show = TVShow(int(dbData['indexer']), int(dbData['indexer_id']))
                show.nextEpisode()
                self.NAMECACHE.build(show)
                self.SHOWLIST += [show]
            except Exception as e:
                self.srLogger.error("Show error in [%s]: %s" % (dbData['location'], e.message))
