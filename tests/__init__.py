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

from configobj import ConfigObj

import sickrage
from sickrage.core.caches import tv_cache
from sickrage.core.caches.name_cache import nameCache
from sickrage.core.databases import Connection, cache_db, failed_db, main_db
from sickrage.core.helpers import removetree, get_lan_ip
from sickrage.core.helpers.encoding import encodingInit
from sickrage.core.scheduler import Scheduler
from sickrage.core.srconfig import srConfig
from sickrage.core.srlogger import srLogger
from sickrage.core.tv import episode, show
from sickrage.core.webserver import SRWebServer
from sickrage.indexers.indexer_api import indexerApi
from sickrage.metadata import get_metadata_generator_dict
from sickrage.providers import NewznabProvider, GenericProvider, NZBProvider, TorrentProvider, TorrentRssProvider

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
    if not os.path.isdir(sickrage.LOG_DIR):
        os.mkdir(sickrage.LOG_DIR)


def createTestCacheFolder():
    if not os.path.isdir(sickrage.CACHE_DIR):
        os.mkdir(sickrage.CACHE_DIR)


# call env functions at appropriate time during sickrage var setup
encodingInit()

# =================
# sickrage globals
# =================
sickrage.SYS_ENCODING = 'UTF-8'

sickrage.INDEXER_API = indexerApi

sickrage.NAMECACHE = nameCache()

sickrage.showList = []
sickrage.QUALITY_DEFAULT = 4  # hdtv
sickrage.FLATTEN_FOLDERS_DEFAULT = 0

sickrage.NAMING_PATTERN = ''
sickrage.NAMING_ABD_PATTERN = ''
sickrage.NAMING_SPORTS_PATTERN = ''
sickrage.NAMING_MULTI_EP = 1

sickrage.PROVIDER_ORDER = ["sick_beard_index"]
sickrage.newznabProviderList = NewznabProvider.getProviderList(NewznabProvider.getDefaultProviders())
sickrage.torrentRssProviderList = TorrentRssProvider.getProviderList(TorrentRssProvider.getDefaultProviders())
sickrage.metadataProvideDict = get_metadata_generator_dict()
sickrage.GUI_NAME = "slick"
sickrage.THEME_NAME = "dark"
sickrage.ROOT_DIR = sickrage.DATA_DIR = TESTDIR
sickrage.PROG_DIR = os.path.abspath(os.path.join(TESTDIR, os.pardir, 'sickrage'))
sickrage.GUI_DIR = os.path.join(sickrage.PROG_DIR, 'core', 'webserver', 'gui', sickrage.GUI_NAME)
sickrage.CONFIG_FILE = os.path.join(sickrage.DATA_DIR, "config.ini")
sickrage.CFG = ConfigObj(sickrage.CONFIG_FILE)
sickrage.TV_DOWNLOAD_DIR = FILEDIR
sickrage.HTTPS_CERT = "server.crt"
sickrage.HTTPS_KEY = "server.key"
sickrage.WEB_USERNAME = "sickrage"
sickrage.WEB_PASSWORD = "sickrage"
sickrage.WEB_COOKIE_SECRET = "sickrage"
sickrage.WEB_ROOT = ""
sickrage.WEB_SERVER = None
sickrage.CPU_PRESET = "NORMAL"
sickrage.EXTRA_SCRIPTS = []

sickrage.CACHE_DIR = os.path.join(TESTDIR, 'cache')
createTestCacheFolder()

sickrage.LOG_DIR = os.path.join(TESTDIR, 'Logs')
createTestLogFolder()

sickrage.LOG_FILE = os.path.join(sickrage.LOG_DIR, 'sickrage.log')
sickrage.LOG_NR = 5
sickrage.LOG_SIZE = 1048576

sickrage.LOGGER = srLogger(logFile=sickrage.LOG_FILE, logSize=sickrage.LOG_SIZE, logNr=sickrage.LOG_NR,
                           fileLogging=sickrage.LOG_DIR, debugLogging=True)

sickrage.CUR_COMMIT_HASH = srConfig.check_setting_str(sickrage.CFG, 'General', 'cur_commit_hash', '')
sickrage.GIT_USERNAME = srConfig.check_setting_str(sickrage.CFG, 'General', 'git_username', '')
sickrage.GIT_PASSWORD = srConfig.check_setting_str(sickrage.CFG, 'General', 'git_password', '',
                                                   censor_log=True)

sickrage.providersDict = {
    GenericProvider.NZB: {p.id: p for p in NZBProvider.getProviderList()},
    GenericProvider.TORRENT: {p.id: p for p in TorrentProvider.getProviderList()},
}

sickrage.Scheduler = Scheduler()


# =================
# dummy functions
# =================
def _dummy_loadFromDB(self, skipNFO=False):
    return True

show.TVShow.loadFromDB = _dummy_loadFromDB


def _dummy_saveConfig(cfgfile=sickrage.CONFIG_FILE):
    return True


# this overrides the sickrage save_config which gets called during a db upgrade
sickrage.core.saveall = _dummy_saveConfig
srConfig.save_config = _dummy_saveConfig


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
    def setUp(self, web=False):
        setUp_test_db()
        sickrage.showList = []
        setUp_test_episode_file()
        setUp_test_show_dir()
        if web:
            setUp_test_web_server()

    def tearDown(self, web=False):
        sickrage.showList = []
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
def setUp_test_db():
    """upgrades the db to the latest version
    """

    global TESTDB_INITALIZED

    if not TESTDB_INITALIZED:
        # remove old db files
        tearDown_test_db()

        # upgrading the db
        main_db.MainDB().InitialSchema().upgrade()

        # fix up any db problems
        main_db.MainDB().SanityCheck()

        # and for cachedb too
        cache_db.CacheDB().InitialSchema().upgrade()

        # and for faileddb too
        failed_db.FailedDB().InitialSchema().upgrade()

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
    sickrage.WEB_SERVER = SRWebServer(**{
        'port': 8081,
        'host': get_lan_ip(),
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

    threading.Thread(None, sickrage.WEB_SERVER.start).start()


def tearDown_test_web_server():
    if sickrage.WEB_SERVER:
        sickrage.WEB_SERVER.server_shutdown()


def load_tests(loader, tests, pattern):
    global TESTALL
    TESTALL = True
    return tests
