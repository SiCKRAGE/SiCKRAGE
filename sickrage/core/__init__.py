# -*- coding: utf-8 -*
# Author: echel0n <sickrage.tv@gmail.com>
# URL: https://sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
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
import urllib
import urlparse
import webbrowser

import sickrage
from sickrage.core.caches.name_cache import nameCache
from sickrage.core.classes import SiCKRAGEURLopener, AttrDict
from sickrage.core.common import SD
from sickrage.core.common import SKIPPED
from sickrage.core.common import WANTED
from sickrage.core.databases import main_db, cache_db, failed_db
from sickrage.core.helpers import encrypt, findCertainShow, \
    generateCookieSecret, makeDir, removetree, restoreDB, get_lan_ip
from sickrage.core.helpers.encoding import encodingInit
from sickrage.core.nameparser.validator import check_force_season_folders
from sickrage.core.processors import auto_postprocessor
from sickrage.core.queues.search import SearchQueue
from sickrage.core.queues.show import ShowQueue
from sickrage.core.scheduler import SRIntervalTrigger, Scheduler
from sickrage.core.searchers.backlog_searcher import BacklogSearcher, \
    get_backlog_cycle_time
from sickrage.core.searchers.daily_searcher import DailySearcher
from sickrage.core.searchers.proper_searcher import ProperSearcher
from sickrage.core.searchers.subtitle_searcher import SubtitleSearcher
from sickrage.core.searchers.trakt_searcher import TraktSearcher
from sickrage.core.srconfig import srConfig
from sickrage.core.tv import episode, show
from sickrage.core.tv.show import TVShow
from sickrage.core.updaters.show_updater import ShowUpdater
from sickrage.core.updaters.tz_updater import update_network_dict
from sickrage.core.version_updater import VersionUpdater
from sickrage.core.webserver import SRWebServer
from sickrage.indexers.indexer_api import indexerApi
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
from sickrage.providers import GenericProvider

urllib._urlopener = SiCKRAGEURLopener()
urlparse.uses_netloc.append('scgi')

from time import strptime
strptime("2012", "%Y")

def initialize():
    if not sickrage.INITIALIZED:
        with threading.Lock():
            # init encoding
            encodingInit()

            # Check if we need to perform a restore first
            os.chdir(sickrage.DATA_DIR)
            restore_dir = os.path.join(sickrage.DATA_DIR, 'restore')
            if os.path.exists(restore_dir):
                success = restoreDB(restore_dir, sickrage.DATA_DIR)
                sickrage.LOGGER.info("Restore: restoring DB and config.ini %s!\n" % ("FAILED", "SUCCESSFUL")[success])

            # init indexerApi
            sickrage.INDEXER_API = indexerApi

            # initialize notifiers
            sickrage.NOTIFIERS = AttrDict(
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

            sickrage.NAMING_EP_TYPE = ("%(seasonnumber)dx%(episodenumber)02d",
                                       "s%(seasonnumber)02de%(episodenumber)02d",
                                       "S%(seasonnumber)02dE%(episodenumber)02d",
                                       "%(seasonnumber)02dx%(episodenumber)02d")

            sickrage.SPORTS_EP_TYPE = ("%(seasonnumber)dx%(episodenumber)02d",
                                       "s%(seasonnumber)02de%(episodenumber)02d",
                                       "S%(seasonnumber)02dE%(episodenumber)02d",
                                       "%(seasonnumber)02dx%(episodenumber)02d")

            sickrage.NAMING_EP_TYPE_TEXT = ("1x02", "s01e02", "S01E02", "01x02")
            sickrage.NAMING_MULTI_EP_TYPE = {0: ["-%(episodenumber)02d"] * len(sickrage.NAMING_EP_TYPE),
                                             1: [" - " + x for x in sickrage.NAMING_EP_TYPE],
                                             2: [x + "%(episodenumber)02d" for x in ("x", "e", "E", "x")]}

            sickrage.NAMING_MULTI_EP_TYPE_TEXT = ("extend", "duplicate", "repeat")
            sickrage.NAMING_SEP_TYPE = (" - ", " ")
            sickrage.NAMING_SEP_TYPE_TEXT = (" - ", "space")

            # migrate old database filenames to new ones
            if not os.path.exists(main_db.MainDB().filename) and os.path.exists("sickbeard.db"):
                helpers.moveFile("sickbeard.db", main_db.MainDB().filename)

            # init config file
            srConfig.load_config(sickrage.CONFIG_FILE, True)

            # set socket timeout
            socket.setdefaulttimeout(sickrage.SOCKET_TIMEOUT)

            # init logger
            sickrage.LOGGER = sickrage.LOGGER.__class__(logFile=sickrage.LOG_FILE,
                                                        logSize=sickrage.LOG_SIZE,
                                                        logNr=sickrage.LOG_NR,
                                                        fileLogging=makeDir(sickrage.LOG_DIR),
                                                        debugLogging=sickrage.DEBUG)

            # init updater and get current version
            sickrage.VERSIONUPDATER = VersionUpdater()
            sickrage.VERSION = sickrage.VERSIONUPDATER.updater.get_cur_version

            # initialize the main SB database
            main_db.MainDB().InitialSchema().upgrade()

            # initialize the cache database
            cache_db.CacheDB().InitialSchema().upgrade()

            # initialize the failed downloads database
            failed_db.FailedDB().InitialSchema().upgrade()

            # fix up any db problems
            main_db.MainDB().SanityCheck()

            if sickrage.DEFAULT_PAGE not in ('home', 'schedule', 'history', 'news', 'IRC'):
                sickrage.DEFAULT_PAGE = 'home'

            if not makeDir(sickrage.CACHE_DIR):
                sickrage.LOGGER.error("!!! Creating local cache dir failed")
                sickrage.CACHE_DIR = None

            # Check if we need to perform a restore of the cache folder
            try:
                restore_dir = os.path.join(sickrage.DATA_DIR, 'restore')
                if os.path.exists(restore_dir) and os.path.exists(os.path.join(restore_dir, 'cache')):
                    def restore_cache(srcdir, dstdir):
                        def path_leaf(path):
                            head, tail = os.path.split(path)
                            return tail or os.path.basename(head)

                        try:
                            if os.path.isdir(dstdir):
                                bakfilename = '{}-{1}'.format(path_leaf(dstdir),
                                                               datetime.datetime.strftime(datetime.date.now(),
                                                                                          '%Y%m%d_%H%M%S'))
                                shutil.move(dstdir, os.path.join(os.path.dirname(dstdir), bakfilename))

                            shutil.move(srcdir, dstdir)
                            sickrage.LOGGER.info("Restore: restoring cache successful")
                        except Exception as E:
                            sickrage.LOGGER.error("Restore: restoring cache failed: {}".format(E))

                    restore_cache(os.path.join(restore_dir, 'cache'), sickrage.CACHE_DIR)
            except Exception as e:
                sickrage.LOGGER.error("Restore: restoring cache failed: {}".format(e))
            finally:
                if os.path.exists(os.path.join(sickrage.DATA_DIR, 'restore')):
                    try:
                        removetree(os.path.join(sickrage.DATA_DIR, 'restore'))
                    except Exception as e:
                        sickrage.LOGGER.error("Restore: Unable to remove the restore directory: {}".format(e))

                    for cleanupDir in ['mako', 'sessions', 'indexers']:
                        try:
                            removetree(os.path.join(sickrage.CACHE_DIR, cleanupDir))
                        except Exception as e:
                            sickrage.LOGGER.warning(
                                    "Restore: Unable to remove the cache/{} directory: {1}".format(cleanupDir, e))

            if sickrage.WEB_PORT < 21 or sickrage.WEB_PORT > 65535:
                sickrage.WEB_PORT = 8081

            if not sickrage.WEB_COOKIE_SECRET:
                sickrage.WEB_COOKIE_SECRET = generateCookieSecret()

            # attempt to help prevent users from breaking links by using a bad url
            if not sickrage.ANON_REDIRECT.endswith('?'):
                sickrage.ANON_REDIRECT = ''

            if not re.match(r'\d+\|[^|]+(?:\|[^|]+)*', sickrage.ROOT_DIRS):
                sickrage.ROOT_DIRS = ''

            sickrage.NAMING_FORCE_FOLDERS = check_force_season_folders()
            if sickrage.NZB_METHOD not in ('blackhole', 'sabnzbd', 'nzbget'):
                sickrage.NZB_METHOD = 'blackhole'

            if not sickrage.PROVIDER_ORDER:
                sickrage.PROVIDER_ORDER = sickrage.providersDict[GenericProvider.NZB].keys() + \
                                          sickrage.providersDict[GenericProvider.TORRENT].keys()

            if sickrage.TORRENT_METHOD not in (
                    'blackhole', 'utorrent', 'transmission', 'deluge', 'deluged', 'download_station', 'rtorrent',
                    'qbittorrent', 'mlnet'):
                sickrage.TORRENT_METHOD = 'blackhole'

            if sickrage.PROPER_SEARCHER_INTERVAL not in ('15m', '45m', '90m', '4h', 'daily'):
                sickrage.PROPER_SEARCHER_INTERVAL = 'daily'

            if sickrage.AUTOPOSTPROCESSOR_FREQ < sickrage.MIN_AUTOPOSTPROCESSOR_FREQ:
                sickrage.AUTOPOSTPROCESSOR_FREQ = sickrage.MIN_AUTOPOSTPROCESSOR_FREQ

            if sickrage.NAMECACHE_FREQ < sickrage.MIN_NAMECACHE_FREQ:
                sickrage.NAMECACHE_FREQ = sickrage.MIN_NAMECACHE_FREQ

            if sickrage.DAILY_SEARCHER_FREQ < sickrage.MIN_DAILY_SEARCHER_FREQ:
                sickrage.DAILY_SEARCHER_FREQ = sickrage.MIN_DAILY_SEARCHER_FREQ

            sickrage.MIN_BACKLOG_SEARCHER_FREQ = get_backlog_cycle_time()
            if sickrage.BACKLOG_SEARCHER_FREQ < sickrage.MIN_BACKLOG_SEARCHER_FREQ:
                sickrage.BACKLOG_SEARCHER_FREQ = sickrage.MIN_BACKLOG_SEARCHER_FREQ

            if sickrage.VERSION_UPDATER_FREQ < sickrage.MIN_VERSION_UPDATER_FREQ:
                sickrage.VERSION_UPDATER_FREQ = sickrage.MIN_VERSION_UPDATER_FREQ

            if sickrage.SHOWUPDATE_HOUR > 23:
                sickrage.SHOWUPDATE_HOUR = 0
            elif sickrage.SHOWUPDATE_HOUR < 0:
                sickrage.SHOWUPDATE_HOUR = 0

            if sickrage.SUBTITLE_SEARCHER_FREQ < sickrage.MIN_SUBTITLE_SEARCHER_FREQ:
                sickrage.SUBTITLE_SEARCHER_FREQ = sickrage.MIN_SUBTITLE_SEARCHER_FREQ

            sickrage.NEWS_LATEST = sickrage.NEWS_LAST_READ

            if sickrage.SUBTITLES_LANGUAGES[0] == '':
                sickrage.SUBTITLES_LANGUAGES = []

            sickrage.TIME_PRESET = sickrage.TIME_PRESET_W_SECONDS.replace(":%S", "")

            # initialize metadata_providers
            sickrage.metadataProvideDict = get_metadata_generator_dict()
            for cur_metadata_tuple in [(sickrage.METADATA_KODI, kodi),
                                       (sickrage.METADATA_KODI_12PLUS, kodi_12plus),
                                       (sickrage.METADATA_MEDIABROWSER, mediabrowser),
                                       (sickrage.METADATA_PS3, ps3),
                                       (sickrage.METADATA_WDTV, wdtv),
                                       (sickrage.METADATA_TIVO, tivo),
                                       (sickrage.METADATA_MEDE8ER, mede8er)]:
                (cur_metadata_config, cur_metadata_class) = cur_metadata_tuple
                tmp_provider = cur_metadata_class.metadata_class()
                tmp_provider.set_config(cur_metadata_config)

                sickrage.metadataProvideDict[tmp_provider.name] = tmp_provider

            # init caches
            sickrage.NAMECACHE = nameCache()

            # init queues
            sickrage.SHOWUPDATER = ShowUpdater()
            sickrage.SHOWQUEUE = ShowQueue()
            sickrage.SEARCHQUEUE = SearchQueue()

            # load data for shows from database
            sickrage.showList = load_shows()

            # init searchers
            sickrage.DAILYSEARCHER = DailySearcher()
            sickrage.BACKLOGSEARCHER = BacklogSearcher()
            sickrage.PROPERSEARCHER = ProperSearcher()
            sickrage.TRAKTSEARCHER = TraktSearcher()
            sickrage.SUBTITLESEARCHER = SubtitleSearcher()

            # init scheduler
            sickrage.Scheduler = Scheduler()

            # add version checker job to scheduler
            sickrage.Scheduler.add_job(
                    sickrage.VERSIONUPDATER.run,
                    SRIntervalTrigger(
                        **{'hours': sickrage.VERSION_UPDATER_FREQ, 'min': sickrage.MIN_VERSION_UPDATER_FREQ}),
                    name="VERSIONUPDATER",
                    id="VERSIONUPDATER",
                    replace_existing=True
            )

            # add network timezones updater job to scheduler
            sickrage.Scheduler.add_job(
                    update_network_dict,
                    SRIntervalTrigger(**{'days': 1}),
                    name="TZUPDATER",
                    id="TZUPDATER",
                    replace_existing=True
            )

            # add namecache updater job to scheduler
            sickrage.Scheduler.add_job(
                    sickrage.NAMECACHE.run,
                    SRIntervalTrigger(**{'minutes': sickrage.NAMECACHE_FREQ, 'min': sickrage.MIN_NAMECACHE_FREQ}),
                    name="NAMECACHE",
                    id="NAMECACHE",
                    replace_existing=True
            )

            # add show queue job to scheduler
            sickrage.Scheduler.add_job(
                    sickrage.SHOWQUEUE.run,
                    SRIntervalTrigger(**{'seconds': 3}),
                    name="SHOWQUEUE",
                    id="SHOWQUEUE",
                    replace_existing=True
            )

            # add search queue job to scheduler
            sickrage.Scheduler.add_job(
                    sickrage.SEARCHQUEUE.run,
                    SRIntervalTrigger(**{'seconds': 1}),
                    name="SEARCHQUEUE",
                    id="SEARCHQUEUE",
                    replace_existing=True
            )

            # add show updater job to scheduler
            sickrage.Scheduler.add_job(
                    sickrage.SHOWUPDATER.run,
                    SRIntervalTrigger(
                            **{'hours': 1,
                               'start_date': datetime.datetime.now().replace(hour=sickrage.SHOWUPDATE_HOUR)}),
                    name="SHOWUPDATER",
                    id="SHOWUPDATER",
                    replace_existing=True
            )

            # add daily search job to scheduler
            sickrage.Scheduler.add_job(
                    sickrage.DAILYSEARCHER.run,
                    SRIntervalTrigger(
                            **{'minutes': sickrage.DAILY_SEARCHER_FREQ, 'min': sickrage.MIN_DAILY_SEARCHER_FREQ}),
                    name="DAILYSEARCHER",
                    id="DAILYSEARCHER",
                    replace_existing=True
            )

            # add backlog search job to scheduler
            sickrage.Scheduler.add_job(
                    sickrage.BACKLOGSEARCHER.run,
                    SRIntervalTrigger(
                            **{'minutes': sickrage.BACKLOG_SEARCHER_FREQ,
                               'min': sickrage.MIN_BACKLOG_SEARCHER_FREQ}),
                    name="BACKLOG",
                    id="BACKLOG",
                    replace_existing=True
            )

            # add auto-postprocessing job to scheduler
            job = sickrage.Scheduler.add_job(
                    auto_postprocessor.PostProcessor().run,
                    SRIntervalTrigger(**{'minutes': sickrage.AUTOPOSTPROCESSOR_FREQ,
                                         'min': sickrage.MIN_AUTOPOSTPROCESSOR_FREQ}),
                    name="POSTPROCESSOR",
                    id="POSTPROCESSOR",
                    replace_existing=True
            )
            (job.pause, job.resume)[sickrage.PROCESS_AUTOMATICALLY]()

            # add find propers job to scheduler
            job = sickrage.Scheduler.add_job(
                    sickrage.PROPERSEARCHER.run,
                    SRIntervalTrigger(**{
                        'minutes': {'15m': 15, '45m': 45, '90m': 90, '4h': 4 * 60, 'daily': 24 * 60}[
                            sickrage.PROPER_SEARCHER_INTERVAL]}),
                    name="PROPERSEARCHER",
                    id="PROPERSEARCHER",
                    replace_existing=True
            )
            (job.pause, job.resume)[sickrage.DOWNLOAD_PROPERS]()

            # add trakt.tv checker job to scheduler
            job = sickrage.Scheduler.add_job(
                    sickrage.TRAKTSEARCHER.run,
                    SRIntervalTrigger(**{'hours': 1}),
                    name="TRAKTSEARCHER",
                    id="TRAKTSEARCHER",
                    replace_existing=True,
            )
            (job.pause, job.resume)[sickrage.USE_TRAKT]()

            # add subtitles finder job to scheduler
            job = sickrage.Scheduler.add_job(
                    sickrage.SUBTITLESEARCHER.run,
                    SRIntervalTrigger(**{'hours': sickrage.SUBTITLE_SEARCHER_FREQ}),
                    name="SUBTITLESEARCHER",
                    id="SUBTITLESEARCHER",
                    replace_existing=True
            )
            (job.pause, job.resume)[sickrage.USE_SUBTITLES]()

            # initialize web server
            sickrage.WEB_SERVER = SRWebServer(**{
                'port': int(sickrage.WEB_PORT),
                'host': sickrage.WEB_HOST,
                'data_root': sickrage.DATA_DIR,
                'gui_root': sickrage.GUI_DIR,
                'web_root': sickrage.WEB_ROOT,
                'log_dir': sickrage.WEB_LOG or sickrage.LOG_DIR,
                'username': sickrage.WEB_USERNAME,
                'password': sickrage.WEB_PASSWORD,
                'enable_https': sickrage.ENABLE_HTTPS,
                'handle_reverse_proxy': sickrage.HANDLE_REVERSE_PROXY,
                'https_cert': os.path.join(sickrage.ROOT_DIR, sickrage.HTTPS_CERT),
                'https_key': os.path.join(sickrage.ROOT_DIR, sickrage.HTTPS_KEY),
                'daemonize': sickrage.DAEMONIZE,
                'pidfile': sickrage.PIDFILE,
                'stop_timeout': 3,
                'nolaunch': sickrage.WEB_NOLAUNCH
            })

            sickrage.LOGGER.info("SiCKRAGE VERSION:[{}] CONFIG:[{}]".format(sickrage.VERSION, sickrage.CONFIG_FILE))
            sickrage.INITIALIZED = True
            return True

def halt():
    if sickrage.INITIALIZED and sickrage.STARTED:
        with threading.Lock():
            sickrage.LOGGER.info("Aborting all threads")

            # shutdown scheduler
            sickrage.LOGGER.info("Shutting down scheduler jobs")
            sickrage.Scheduler.shutdown()

            if sickrage.ADBA_CONNECTION:
                sickrage.LOGGER.info("Loggging out ANIDB connection")
                sickrage.ADBA_CONNECTION.logout()

            sickrage.STARTED = False
            return True

def shutdown():
    if sickrage.STARTED:
        halt()
        saveall()

def load_shows():
    """
    Populates the showlist with shows from the database
    """

    showlist = []
    for sqlShow in main_db.MainDB().select("SELECT * FROM tv_shows"):
        try:
            curshow = TVShow(int(sqlShow[b"indexer"]), int(sqlShow[b"indexer_id"]))
            sickrage.LOGGER.debug("Loading data for show: [{}]".format(curshow.name))
            sickrage.NAMECACHE.buildNameCache(curshow)
            curshow.nextEpisode()
            showlist += [curshow]
        except Exception as e:
            sickrage.LOGGER.error("There was an error creating the show in {}: {}".format(sqlShow[b"location"], e))
            sickrage.LOGGER.debug(traceback.format_exc())
            continue

    return showlist


def saveall():
    # write all shows
    sickrage.LOGGER.info("Saving all shows to the database")
    for show in sickrage.showList:
        show.saveToDB()

    # save config
    sickrage.LOGGER.info("Saving settings to disk")
    srConfig.save_config(sickrage.CONFIG_FILE)


def launch_browser(protocol='http', startport=8081, web_root='/'):
    browserurl = '{}://localhost:{}{}/home/'.format(protocol, startport, web_root)

    try:
        try:
            webbrowser.open(browserurl, 2, 1)
        except webbrowser.Error:
            webbrowser.open(browserurl, 1, 1)
    except webbrowser.Error:
        sickrage.LOGGER.error("Unable to launch a browser")


def get_episodes_list(epids, showid=None):
    if epids is None or len(epids) == 0:
        return []

    query = "SELECT * FROM tv_episodes WHERE indexerid in (%s)" % (",".join(['?'] * len(epids)),)
    params = epids

    if showid is not None:
        query += " AND showid = ?"
        params.append(showid)

    eplist = []
    for curEp in main_db.MainDB().select(query, params):
        curshowobj = findCertainShow(sickrage.showList, int(curEp[b"showid"]))
        eplist += [curshowobj.getEpisode(int(curEp[b"season"]), int(curEp[b"episode"]))]

    return eplist
