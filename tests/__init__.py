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

from __future__ import print_function, unicode_literals

import os
import os.path
import socket
import threading
import unittest

from tornado.ioloop import IOLoop

import sickrage
from core import encodingInit, srLogger
from core import webserver
from core.caches import tv_cache
from core.caches.name_cache import srNameCache
from core.classes import AttrDict
from core.databases import Connection
from core.databases import cache_db
from core.databases import failed_db
from core.databases import main_db
from core.helpers import removetree
from core.srscheduler import srScheduler
from core.tv import episode
from indexers import srIndexerApi
from metadata import get_metadata_generator_dict
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
from providers import GenericProvider
from providers import NZBProvider
from providers import NewznabProvider
from providers import TorrentProvider
from providers import TorrentRssProvider

threading.currentThread().setName('TESTS')
socket.setdefaulttimeout(30)

# =================
# test globals
# =================
TESTALL = False
TESTSKIPPED = ['test_issue_submitter', 'test_ssl_sni']
TESTDIR = os.path.abspath(os.path.dirname(__file__))
TESTDBNAME = "sickrage.db"
TESTCACHEDBNAME = "cache.db"
TESTFAILEDDBNAME = "failed.db"
TESTDB_INITALIZED = False

SHOWNAME = "show name"
SEASON = 4
EPISODE = 2
FILENAME = "show name - s0" + str(SEASON) + "e0" + str(EPISODE) + ".mkv"
FILEDIR = os.path.join(TESTDIR, SHOWNAME)
FILEPATH = os.path.join(FILEDIR, FILENAME)
SHOWDIR = os.path.join(TESTDIR, SHOWNAME + " final")


# =================
# prepare env functions
# =================
def createTestLogFolder():
    if not os.path.isdir(sickrage.srCore.CONFIG.LOG_DIR):
        os.mkdir(sickrage.srCore.CONFIG.LOG_DIR)


def createTestCacheFolder():
    if not os.path.isdir(sickrage.srCore.CONFIG.CACHE_DIR):
        os.mkdir(sickrage.srCore.CONFIG.CACHE_DIR)


# =================
# sickrage globals
# =================
import core

threading.Thread(None, IOLoop.instance().start).start()

sickrage.srCore.DATA_DIR = TESTDIR
CONFIG_FILE = os.path.join(sickrage.srCore.DATA_DIR, "config.ini")
sickrage.srCore.PROG_DIR = os.path.abspath(os.path.join(TESTDIR, os.pardir, 'sickrage'))
sickrage.srCore = core.Core(CONFIG_FILE, sickrage.srCore.DATA_DIR)
sickrage.srCore.CONFIG.SYS_ENCODING = encodingInit()
sickrage.srCore.CONFIG.SSL_VERIFY = False
sickrage.srCore.CONFIG.PROXY_SETTING = ''
sickrage.srCore.SHOWLIST = []

sickrage.srCore.CONFIG.CACHE_DIR = os.path.join(TESTDIR, 'cache')
createTestCacheFolder()

sickrage.srCore.CONFIG.LOG_DIR = os.path.join(TESTDIR, 'Logs')
createTestLogFolder()

sickrage.srCore.CONFIG.IGNORE_WORDS = 'german, french, core2hd, dutch, swedish, reenc, MrLss'
sickrage.srCore.CONFIG.QUALITY_DEFAULT = 4  # hdtv
sickrage.srCore.CONFIG.FLATTEN_FOLDERS_DEFAULT = 0

sickrage.srCore.CONFIG.NAMING_PATTERN = ''
sickrage.srCore.CONFIG.NAMING_ABD_PATTERN = ''
sickrage.srCore.CONFIG.NAMING_SPORTS_PATTERN = ''
sickrage.srCore.CONFIG.NAMING_MULTI_EP = 1

sickrage.srCore.CONFIG.PROVIDER_ORDER = ["sick_beard_index"]
sickrage.srCore.newznabProviderList = NewznabProvider.getProviderList(NewznabProvider.getDefaultProviders())
sickrage.srCore.torrentRssProviderList = TorrentRssProvider.getProviderList(
    TorrentRssProvider.getDefaultProviders())
sickrage.srCore.metadataProviderDict = get_metadata_generator_dict()
sickrage.srCore.CONFIG.GUI_NAME = "slick"
sickrage.srCore.CONFIG.THEME_NAME = "dark"
sickrage.srCore.CONFIG.GUI_DIR = os.path.join(sickrage.srCore.PROG_DIR, 'core', 'webserver', 'gui',
                                              sickrage.srCore.CONFIG.GUI_NAME)
sickrage.srCore.CONFIG.TV_DOWNLOAD_DIR = FILEDIR
sickrage.srCore.CONFIG.HTTPS_CERT = "server.crt"
sickrage.srCore.CONFIG.HTTPS_KEY = "server.key"
sickrage.srCore.CONFIG.WEB_USERNAME = "sickrage"
sickrage.srCore.CONFIG.WEB_PASSWORD = "sickrage"
sickrage.srCore.CONFIG.WEB_COOKIE_SECRET = "sickrage"
sickrage.srCore.CONFIG.WEB_ROOT = ""
sickrage.srCore.WEBSERVER = None
sickrage.srCore.CONFIG.CPU_PRESET = "NORMAL"
sickrage.srCore.CONFIG.EXTRA_SCRIPTS = []

sickrage.srCore.CONFIG.LOG_FILE = os.path.join(sickrage.srCore.CONFIG.LOG_DIR, 'sickrage.log')
sickrage.srCore.CONFIG.LOG_NR = 5
sickrage.srCore.CONFIG.LOG_SIZE = 1048576

LOGGER = srLogger(logFile=sickrage.srCore.CONFIG.LOG_FILE, logSize=sickrage.srCore.CONFIG.LOG_SIZE,
                  logNr=sickrage.srCore.CONFIG.LOG_NR,
                  fileLogging=sickrage.srCore.CONFIG.LOG_DIR, debugLogging=True)

sickrage.srCore.CONFIG.GIT_USERNAME = sickrage.srCore.CONFIG.check_setting_str('General', 'git_username', '')
sickrage.srCore.CONFIG.GIT_PASSWORD = sickrage.srCore.CONFIG.check_setting_str('General', 'git_password', '',
                                                                               censor_log=True)

sickrage.srCore.providersDict = {
    GenericProvider.NZB: {p.id: p for p in NZBProvider.getProviderList()},
    GenericProvider.TORRENT: {p.id: p for p in TorrentProvider.getProviderList()},
}

sickrage.srCore.INDEXER_API = srIndexerApi
sickrage.srCore.SCHEDULER = srScheduler()
sickrage.srCore.NAMECACHE = srNameCache()

sickrage.srCore.NOTIFIERS = AttrDict(
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


# =================
# dummy functions
# =================
def _dummy_saveConfig(cfgfile=sickrage.srCore.CONFIG_FILE):
    return True


# this overrides the sickrage save_config which gets called during a db upgrade
sickrage.srCore.save_all = _dummy_saveConfig
sickrage.srCore.CONFIG.save_config = _dummy_saveConfig


# the real one tries to contact tvdb just stop it from getting more info on the ep
def _fake_specifyEP(self, season, episode):
    pass


episode.TVEpisode.specifyEpisode = _fake_specifyEP


# =================
# test classes
# =================
class SiCKRAGETestCase(unittest.TestCase):
    def setUp(self, **kwargs):
        if TESTALL and self.__module__ in TESTSKIPPED:
            raise unittest.SkipTest()


class SiCKRAGETestDBCase(SiCKRAGETestCase):
    def setUp(self, web=False, force_db=False):
        sickrage.srCore.SHOWLIST = []
        setUp_test_db(force_db)
        setUp_test_episode_file()
        setUp_test_show_dir()
        if web:
            setUp_test_web_server()

    def tearDown(self, web=False):
        sickrage.srCore.SHOWLIST = []
        tearDown_test_episode_file()
        tearDown_test_show_dir()
        if web:
            tearDown_test_web_server()


class TestCacheDBConnection(Connection, object):
    def __init__(self, providerName):
        super(TestCacheDBConnection, self).__init__(providerName)

        # Create the table if it's not already there
        try:
            if not self.hasTable(providerName):
                self.action(
                    "CREATE TABLE [" + providerName + "] (name TEXT, season NUMERIC, episodes TEXT, indexerid NUMERIC, url TEXT, time NUMERIC, quality TEXT, release_group TEXT)")
            else:
                sqlResults = self.select(
                    "SELECT url, COUNT(url) AS count FROM [" + providerName + "] GROUP BY url HAVING count > 1")

                for cur_dupe in sqlResults:
                    self.action("DELETE FROM [" + providerName + "] WHERE url = ?", [cur_dupe[b"url"]])

            # add unique index to prevent further dupes from happening if one does not exist
            self.action("CREATE UNIQUE INDEX IF NOT EXISTS idx_url ON [" + providerName + "] (url)")

            # add release_group column to table if missing
            if not self.hasColumn(providerName, 'release_group'):
                self.addColumn(providerName, 'release_group', "TEXT", "")

            # add version column to table if missing
            if not self.hasColumn(providerName, 'version'):
                self.addColumn(providerName, 'version', "NUMERIC", "-1")

        except Exception as e:
            if str(e) != "table [" + providerName + "] already exists":
                raise

        # Create the table if it's not already there
        try:
            if not self.hasTable('lastUpdate'):
                self.action("CREATE TABLE lastUpdate (provider TEXT, time NUMERIC)")
        except Exception as e:
            if str(e) != "table lastUpdate already exists":
                raise


# this will override the normal cache db connection
tv_cache.CacheDBConnection = TestCacheDBConnection


# =================
# test functions
# =================
def setUp_test_db(force=False):
    """upgrades the db to the latest version
    """

    global TESTDB_INITALIZED

    if not TESTDB_INITALIZED or force:
        # remove old db files
        tearDown_test_db()

        # upgrade main
        main_db.MainDB().InitialSchema().upgrade()

        # sanity check main
        main_db.MainDB().SanityCheck()

        # upgrade cache
        cache_db.CacheDB().InitialSchema().upgrade()

        # upgrade failed
        failed_db.FailedDB().InitialSchema().upgrade()

        # populate scene exceiptions table
        #retrieve_exceptions(False, False)

        TESTDB_INITALIZED = True


def tearDown_test_db():
    for current_db in [TESTDBNAME, TESTCACHEDBNAME, TESTFAILEDDBNAME]:
        file_name = os.path.join(TESTDIR, current_db)
        if os.path.exists(file_name):
            try:
                os.remove(file_name)
            except Exception as e:
                print(e.message)
                continue


def setUp_test_episode_file():
    if not os.path.exists(FILEDIR):
        os.makedirs(FILEDIR)

    try:
        with open(FILEPATH, 'wb') as f:
            f.write(b"foo bar")
            f.flush()
    except Exception:
        print("Unable to set up test episode")
        raise


def tearDown_test_episode_file():
    if os.path.exists(FILEDIR):
        removetree(FILEDIR)


def setUp_test_show_dir():
    if not os.path.exists(SHOWDIR):
        os.makedirs(SHOWDIR)


def tearDown_test_show_dir():
    if os.path.exists(SHOWDIR):
        removetree(SHOWDIR)


def setUp_test_web_server():
    sickrage.srCore.WEBSERVER = webserver.srWebServer()
    threading.Thread(None, sickrage.srCore.WEBSERVER.start).start()


def tearDown_test_web_server():
    if sickrage.srCore.WEBSERVER:
        sickrage.srCore.WEBSERVER.server_shutdown()


def load_tests(loader, tests, pattern):
    global TESTALL
    TESTALL = True
    return tests
