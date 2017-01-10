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
import re
import shutil
import socket
import threading
import traceback
from multiprocessing import cpu_count

from apscheduler.schedulers.tornado import TornadoScheduler
from tornado.ioloop import IOLoop

import sickrage
from sickrage.core.caches.name_cache import srNameCache
from sickrage.core.classes import AttrDict, srIntervalTrigger
from sickrage.core.common import SD, SKIPPED, WANTED
from sickrage.core.databases.cache import CacheDB
from sickrage.core.databases.failed import FailedDB
from sickrage.core.databases.main import MainDB
from sickrage.core.google import googleAuth
from sickrage.core.helpers import findCertainShow, \
    generateCookieSecret, makeDir, removetree, get_lan_ip, restoreSR, getDiskSpaceUsage, getFreeSpace
from sickrage.core.nameparser.validator import check_force_season_folders
from sickrage.core.processors import auto_postprocessor
from sickrage.core.processors.auto_postprocessor import srPostProcessor
from sickrage.core.queues.search import srSearchQueue
from sickrage.core.queues.show import srShowQueue
from sickrage.core.scene_exceptions import retrieve_exceptions
from sickrage.core.searchers.backlog_searcher import srBacklogSearcher, \
    get_backlog_cycle_time
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
        self.started = False
        self.io_loop = IOLoop.current()

        # process id
        self.PID = os.getpid()

        # cpu count
        self.CPU_COUNT = cpu_count()

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

        # init notification queue
        self.srNotifications = Notifications()

        # init logger
        self.srLogger = srLogger()

        # init config
        self.srConfig = srConfig()

        # init databases
        self.mainDB = MainDB()
        self.cacheDB = CacheDB()
        self.failedDB = FailedDB()

        # init scheduler service
        self.srScheduler = TornadoScheduler()

        # init web server
        self.srWebServer = srWebServer()

        # init web client session
        self.srWebSession = srSession()

        # google api
        self.googleAuth = googleAuth()

        # name cache
        self.NAMECACHE = srNameCache()

        # queues
        self.SHOWQUEUE = srShowQueue()
        self.SEARCHQUEUE = srSearchQueue()

        # updaters
        self.VERSIONUPDATER = srVersionUpdater()
        self.SHOWUPDATER = srShowUpdater()

        # searchers
        self.DAILYSEARCHER = srDailySearcher()
        self.BACKLOGSEARCHER = srBacklogSearcher()
        self.PROPERSEARCHER = srProperSearcher()
        self.TRAKTSEARCHER = srTraktSearcher()
        self.SUBTITLESEARCHER = srSubtitleSearcher()

        # auto postprocessor
        self.AUTOPOSTPROCESSOR = srPostProcessor()

        # sickrage version
        self.NEWEST_VERSION = None
        self.NEWEST_VERSION_STRING = None

        # anidb connection
        self.ADBA_CONNECTION = None

        # show list
        self.SHOWLIST = []

    def start(self):
        self.started = True

        # thread name
        threading.currentThread().setName('CORE')

        # Check if we need to perform a restore first
        if os.path.exists(os.path.abspath(os.path.join(sickrage.DATA_DIR, 'restore'))):
            success = restoreSR(os.path.abspath(os.path.join(sickrage.DATA_DIR, 'restore')), sickrage.DATA_DIR)
            print("Restoring SiCKRAGE backup: %s!\n" % ("FAILED", "SUCCESSFUL")[success])
            if success:
                shutil.rmtree(os.path.abspath(os.path.join(sickrage.DATA_DIR, 'restore')), ignore_errors=True)

        # migrate old database file names to new ones
        if os.path.isfile(os.path.abspath(os.path.join(sickrage.DATA_DIR, 'sickbeard.db'))):
            if os.path.isfile(os.path.join(sickrage.DATA_DIR, 'sickrage.db')):
                helpers.moveFile(os.path.join(sickrage.DATA_DIR, 'sickrage.db'),
                                 os.path.join(sickrage.DATA_DIR, '{}.bak-{}'
                                              .format('sickrage.db',
                                                      datetime.datetime.now().strftime(
                                                          '%Y%m%d_%H%M%S'))))

            helpers.moveFile(os.path.abspath(os.path.join(sickrage.DATA_DIR, 'sickbeard.db')),
                             os.path.abspath(os.path.join(sickrage.DATA_DIR, 'sickrage.db')))

        # perform database startup actions
        for db in [self.mainDB, self.cacheDB, self.failedDB]:
            # initialize database
            db.initialize()

            # check integrity of database
            db.check_integrity()

            # migrate database
            db.migrate()

            # compact database
            db.compact()

        # load config
        self.srConfig.load()

        # set socket timeout
        socket.setdefaulttimeout(self.srConfig.SOCKET_TIMEOUT)

        # setup logger settings
        self.srLogger.logSize = self.srConfig.LOG_SIZE
        self.srLogger.logNr = self.srConfig.LOG_NR
        self.srLogger.logFile = self.srConfig.LOG_FILE
        self.srLogger.debugLogging = sickrage.DEBUG
        self.srLogger.consoleLogging = not sickrage.QUITE

        # start logger
        self.srLogger.start()

        # Check available space
        try:
            total_space, available_space = getFreeSpace(sickrage.DATA_DIR)
            if available_space < 100:
                self.srLogger.error(
                    'Shutting down as SiCKRAGE needs some space to work. You\'ll get corrupted data otherwise. Only %sMB left',
                    available_space)
                sickrage.restart = False
                return
        except:
            self.srLogger.error('Failed getting diskspace: %s', traceback.format_exc())

        # load data for shows from database
        self.load_shows()

        # build name cache
        self.NAMECACHE.build()

        if self.srConfig.DEFAULT_PAGE not in ('home', 'schedule', 'history', 'news', 'IRC'):
            self.srConfig.DEFAULT_PAGE = 'home'

        # cleanup cache folder
        for folder in ['mako', 'sessions', 'indexers']:
            try:
                shutil.rmtree(os.path.join(self.srConfig.CACHE_DIR, folder), ignore_errors=True)
            except Exception:
                continue

        # init anidb connection
        if not self.srConfig.USE_ANIDB:
            try:
                self.ADBA_CONNECTION = adba.Connection(keepAlive=True, log=lambda msg: self.srLogger.debug(
                    "AniDB: %s " % msg)).auth(self.srConfig.ANIDB_USERNAME, self.srConfig.ANIDB_PASSWORD)
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

        if self.srConfig.PROPER_SEARCHER_INTERVAL not in ('15m', '45m', '90m', '4h', 'daily'):
            self.srConfig.PROPER_SEARCHER_INTERVAL = 'daily'

        if self.srConfig.AUTOPOSTPROCESSOR_FREQ < self.srConfig.MIN_AUTOPOSTPROCESSOR_FREQ:
            self.srConfig.AUTOPOSTPROCESSOR_FREQ = self.srConfig.MIN_AUTOPOSTPROCESSOR_FREQ

        if self.srConfig.NAMECACHE_FREQ < self.srConfig.MIN_NAMECACHE_FREQ:
            self.srConfig.NAMECACHE_FREQ = self.srConfig.MIN_NAMECACHE_FREQ

        if self.srConfig.DAILY_SEARCHER_FREQ < self.srConfig.MIN_DAILY_SEARCHER_FREQ:
            self.srConfig.DAILY_SEARCHER_FREQ = self.srConfig.MIN_DAILY_SEARCHER_FREQ

        self.srConfig.MIN_BACKLOG_SEARCHER_FREQ = get_backlog_cycle_time()
        if self.srConfig.BACKLOG_SEARCHER_FREQ < self.srConfig.MIN_BACKLOG_SEARCHER_FREQ:
            self.srConfig.BACKLOG_SEARCHER_FREQ = self.srConfig.MIN_BACKLOG_SEARCHER_FREQ

        if self.srConfig.VERSION_UPDATER_FREQ < self.srConfig.MIN_VERSION_UPDATER_FREQ:
            self.srConfig.VERSION_UPDATER_FREQ = self.srConfig.MIN_VERSION_UPDATER_FREQ

        if self.srConfig.SHOWUPDATE_HOUR > 23:
            self.srConfig.SHOWUPDATE_HOUR = 0
        elif self.srConfig.SHOWUPDATE_HOUR < 0:
            self.srConfig.SHOWUPDATE_HOUR = 0

        if self.srConfig.SUBTITLE_SEARCHER_FREQ < self.srConfig.MIN_SUBTITLE_SEARCHER_FREQ:
            self.srConfig.SUBTITLE_SEARCHER_FREQ = self.srConfig.MIN_SUBTITLE_SEARCHER_FREQ

        self.srConfig.NEWS_LATEST = self.srConfig.NEWS_LAST_READ

        if self.srConfig.SUBTITLES_LANGUAGES[0] == '':
            self.srConfig.SUBTITLES_LANGUAGES = []

        # initialize metadata_providers
        for cur_metadata_tuple in [(self.srConfig.METADATA_KODI, kodi),
                                   (self.srConfig.METADATA_KODI_12PLUS, kodi_12plus),
                                   (self.srConfig.METADATA_MEDIABROWSER, mediabrowser),
                                   (self.srConfig.METADATA_PS3, ps3),
                                   (self.srConfig.METADATA_WDTV, wdtv),
                                   (self.srConfig.METADATA_TIVO, tivo),
                                   (self.srConfig.METADATA_MEDE8ER, mede8er)]:
            (cur_metadata_config, cur_metadata_class) = cur_metadata_tuple
            tmp_provider = cur_metadata_class.metadata_class()
            tmp_provider.set_config(cur_metadata_config)

            self.metadataProviderDict[tmp_provider.name] = tmp_provider

        # add version checker job
        self.srScheduler.add_job(
            self.VERSIONUPDATER.run,
            srIntervalTrigger(
                **{'hours': self.srConfig.VERSION_UPDATER_FREQ, 'min': self.srConfig.MIN_VERSION_UPDATER_FREQ}),
            name="VERSIONUPDATER",
            id="VERSIONUPDATER"
        )

        # add network timezones updater job
        self.srScheduler.add_job(
            update_network_dict,
            srIntervalTrigger(**{'days': 1}),
            name="TZUPDATER",
            id="TZUPDATER"
        )

        # add namecache updater job
        self.srScheduler.add_job(
            self.NAMECACHE.run,
            srIntervalTrigger(
                **{'minutes': self.srConfig.NAMECACHE_FREQ, 'min': self.srConfig.MIN_NAMECACHE_FREQ}),
            name="NAMECACHE",
            id="NAMECACHE"
        )

        # add show updater job
        self.srScheduler.add_job(
            self.SHOWUPDATER.run,
            srIntervalTrigger(
                **{'hours': 1,
                   'start_date': datetime.datetime.now().replace(hour=self.srConfig.SHOWUPDATE_HOUR)}),
            name="SHOWUPDATER",
            id="SHOWUPDATER"
        )

        # add daily search job
        self.srScheduler.add_job(
            self.DAILYSEARCHER.run,
            srIntervalTrigger(
                **{'minutes': self.srConfig.DAILY_SEARCHER_FREQ,
                   'min': self.srConfig.MIN_DAILY_SEARCHER_FREQ,
                   'start_date': datetime.datetime.now() + datetime.timedelta(minutes=4)}),
            name="DAILYSEARCHER",
            id="DAILYSEARCHER"
        )

        # add backlog search job
        self.srScheduler.add_job(
            self.BACKLOGSEARCHER.run,
            srIntervalTrigger(
                **{'minutes': self.srConfig.BACKLOG_SEARCHER_FREQ,
                   'min': self.srConfig.MIN_BACKLOG_SEARCHER_FREQ,
                   'start_date': datetime.datetime.now() + datetime.timedelta(minutes=30)}),
            name="BACKLOG",
            id="BACKLOG"
        )

        # add auto-postprocessing job
        self.srScheduler.add_job(
            self.AUTOPOSTPROCESSOR.run,
            srIntervalTrigger(**{'minutes': self.srConfig.AUTOPOSTPROCESSOR_FREQ,
                                 'min': self.srConfig.MIN_AUTOPOSTPROCESSOR_FREQ}),
            name="POSTPROCESSOR",
            id="POSTPROCESSOR"
        )

        # add find proper job
        self.srScheduler.add_job(
            self.PROPERSEARCHER.run,
            srIntervalTrigger(**{
                'minutes': {'15m': 15, '45m': 45, '90m': 90, '4h': 4 * 60, 'daily': 24 * 60}[
                    self.srConfig.PROPER_SEARCHER_INTERVAL]}),
            name="PROPERSEARCHER",
            id="PROPERSEARCHER"
        )

        # add trakt.tv checker job
        self.srScheduler.add_job(
            self.TRAKTSEARCHER.run,
            srIntervalTrigger(**{'hours': 1}),
            name="TRAKTSEARCHER",
            id="TRAKTSEARCHER"
        )

        # add subtitles finder job
        self.srScheduler.add_job(
            self.SUBTITLESEARCHER.run,
            srIntervalTrigger(**{'hours': self.srConfig.SUBTITLE_SEARCHER_FREQ}),
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

        # start webserver
        self.srWebServer.start()

        # start ioloop event handler
        self.io_loop.start()

    def shutdown(self):
        if self.started:
            self.started = False

            self.srLogger.info('SiCKRAGE IS SHUTTING DOWN!!!')

            # shutdown/restart webserver
            self.srWebServer.shutdown()

            # shutdown scheduler
            self.srLogger.debug("Shutting down scheduler")
            self.srScheduler.shutdown()

            # shutdown show queue
            if self.SHOWQUEUE:
                self.srLogger.debug("Shutting down show queue")
                self.SHOWQUEUE.shutdown()

            # shutdown search queue
            if self.SEARCHQUEUE:
                self.srLogger.debug("Shutting down search queue")
                self.SEARCHQUEUE.shutdown()

            # log out of ADBA
            if sickrage.srCore.ADBA_CONNECTION:
                self.srLogger.debug("Logging out ANIDB connection")
                sickrage.srCore.ADBA_CONNECTION.logout()

            # save all show and config settings
            self.save_all()

            # shutdown logging
            self.srLogger.close()

        # stop daemon process
        if not sickrage.restart and sickrage.daemon: sickrage.daemon.stop()

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
                self.srLogger.debug("Loading data for show: [%s]", dbData['show_name'])
                show = TVShow(int(dbData['indexer']), int(dbData['indexer_id']))
                show.nextEpisode()
                self.SHOWLIST += [show]
            except Exception as e:
                self.srLogger.error("Show error in [%s]: %s" % (dbData['location'], e.message))
