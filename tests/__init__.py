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

from __future__ import print_function
from __future__ import unicode_literals

import os.path
import sys

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest

from configobj import ConfigObj

import sickbeard

from sickbeard import db, providers, tvcache
from sickbeard.databases import mainDB
from sickbeard.databases import cache_db, failed_db
from sickbeard.tv import TVEpisode
from sickrage.helper.encoding import ek, encodingInit
from sickbeard.webserveInit import SRWebServer
from sickbeard.logger import SRLogger

# =================
# test globals
# =================
TESTALL = False
TESTSKIPPED = ['test_issue_submitter', 'test_ssl_sni']
TESTDIR = ek(os.path.abspath, ek(os.path.dirname, __file__))
TESTDBNAME = "sickbeard.db"
TESTCACHEDBNAME = "cache.db"
TESTFAILEDDBNAME = "failed.db"

SHOWNAME = "show name"
SEASON = 4
EPISODE = 2
FILENAME = "show name - s0" + str(SEASON) + "e0" + str(EPISODE) + ".mkv"
FILEDIR = ek(os.path.join, TESTDIR, SHOWNAME)
FILEPATH = ek(os.path.join, FILEDIR, FILENAME)
SHOWDIR = ek(os.path.join, TESTDIR, SHOWNAME + " final")

# =================
# prepare env functions
# =================
def createTestLogFolder():
    if not ek(os.path.isdir, sickbeard.LOG_DIR):
        ek(os.mkdir, sickbeard.LOG_DIR)


def createTestCacheFolder():
    if not ek(os.path.isdir, sickbeard.CACHE_DIR):
        ek(os.mkdir, sickbeard.CACHE_DIR)


# call env functions at appropriate time during sickbeard var setup
encodingInit()

# =================
# sickbeard globals
# =================
sickbeard.SYS_ENCODING = 'UTF-8'

sickbeard.showList = []
sickbeard.QUALITY_DEFAULT = 4  # hdtv
sickbeard.FLATTEN_FOLDERS_DEFAULT = 0

sickbeard.NAMING_PATTERN = ''
sickbeard.NAMING_ABD_PATTERN = ''
sickbeard.NAMING_SPORTS_PATTERN = ''
sickbeard.NAMING_MULTI_EP = 1

sickbeard.PROVIDER_ORDER = ["sick_beard_index"]
sickbeard.newznabProviderList = providers.getNewznabProviderList(
    "'Sick Beard Index|http://lolo.sickbeard.com/|0|5030,5040|0|eponly|0|0|0!!!NZBs.org|https://nzbs.org/||5030,5040,5060,5070,5090|0|eponly|0|0|0!!!Usenet-Crawler|https://www.usenet-crawler.com/||5030,5040,5060|0|eponly|0|0|0'")
sickbeard.providerList = providers.makeProviderList()

sickbeard.PROG_DIR = ek(os.path.abspath, ek(os.path.join, TESTDIR, '..'))
sickbeard.DATA_DIR = TESTDIR
sickbeard.CONFIG_FILE = ek(os.path.join, sickbeard.DATA_DIR, "config.ini")
sickbeard.CFG = ConfigObj(sickbeard.CONFIG_FILE)
sickbeard.TV_DOWNLOAD_DIR = FILEDIR
sickbeard.GUI_NAME = "slick"
sickbeard.HTTPS_CERT = "server.crt"
sickbeard.HTTPS_KEY = "server.key"
sickbeard.WEB_USERNAME = "sickrage"
sickbeard.WEB_PASSWORD = "sickrage"
sickbeard.WEB_COOKIE_SECRET = "sickrage"
sickbeard.WEB_ROOT = ""
sickbeard.WEB_SERVER = None
sickbeard.CPU_PRESET = "NORMAL"

sickbeard.BRANCH = sickbeard.config.check_setting_str(sickbeard.CFG, 'General', 'branch', '')
sickbeard.CUR_COMMIT_HASH = sickbeard.config.check_setting_str(sickbeard.CFG, 'General', 'cur_commit_hash', '')
sickbeard.GIT_USERNAME = sickbeard.config.check_setting_str(sickbeard.CFG, 'General', 'git_username', '')
sickbeard.GIT_PASSWORD = sickbeard.config.check_setting_str(sickbeard.CFG, 'General', 'git_password', '',
                                                            censor_log=True)

sickbeard.CACHE_DIR = ek(os.path.join, TESTDIR, 'cache')
createTestCacheFolder()

sickbeard.LOG_DIR = ek(os.path.join, TESTDIR, 'Logs')
sickbeard.LOG_FILE = ek(os.path.join, sickbeard.LOG_DIR, 'test_sickrage.log')
sickbeard.LOG_NR = 5
sickbeard.LOG_SIZE = 1048576

createTestLogFolder()

SRLogger.consoleLogging=False
SRLogger.fileLogging=True
SRLogger.debugLogging=True
SRLogger.logFile=sickbeard.LOG_FILE
SRLogger.logSize=sickbeard.LOG_SIZE
SRLogger.logNr=sickbeard.LOG_NR
SRLogger.initalize()


# =================
# dummy functions
# =================
def _dummy_saveConfig():
    return True


# this overrides the sickbeard save_config which gets called during a db upgrade
mainDB.sickbeard.save_config = _dummy_saveConfig


# the real one tries to contact tvdb just stop it from getting more info on the ep
def _fake_specifyEP(self, season, episode):
    pass


TVEpisode.specifyEpisode = _fake_specifyEP


# =================
# test classes
# =================
class SiCKRAGETestCase(unittest.TestCase):
    def setUp(self, **kwargs):
        if TESTALL and self.__module__ in TESTSKIPPED:
            raise unittest.SkipTest()


class SiCKRAGETestDBCase(SiCKRAGETestCase):
    def setUp(self, web=False):
        sickbeard.showList = []
        setUp_test_db()
        setUp_test_episode_file()
        setUp_test_show_dir()
        if web:
            setUp_test_web_server()

    def tearDown(self, web=False):
        sickbeard.showList = []
        tearDown_test_db()
        tearDown_test_episode_file()
        tearDown_test_show_dir()
        if web:
            tearDown_test_web_server()


class TestDBConnection(db.DBConnection, object):
    def __init__(self, filename=TESTDBNAME):
        super(TestDBConnection, self).__init__(ek(os.path.join, TESTDIR, filename))


class TestCacheDBConnection(TestDBConnection, object):
    def __init__(self, providerName):
        db.DBConnection.__init__(self, ek(os.path.join, TESTDIR, TESTCACHEDBNAME))

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


# this will override the normal db connection
sickbeard.db.DBConnection = TestDBConnection
sickbeard.tvcache.CacheDBConnection = TestCacheDBConnection


# =================
# test functions
# =================
def setUp_test_db():
    """upgrades the db to the latest version
    """
    # upgrading the db
    db.upgradeDatabase(db.DBConnection(), mainDB.InitialSchema)

    # fix up any db problems
    db.sanityCheckDatabase(db.DBConnection(), mainDB.MainSanityCheck)

    # and for cachedb too
    db.upgradeDatabase(db.DBConnection("cache.db"), cache_db.InitialSchema)

    # and for faileddb too
    db.upgradeDatabase(db.DBConnection("failed.db"), failed_db.InitialSchema)


def tearDown_test_db():
    for current_db in [TESTDBNAME, TESTCACHEDBNAME, TESTFAILEDDBNAME]:
        file_name = ek(os.path.join, TESTDIR, current_db)
        if ek(os.path.exists, file_name):
            try:
                ek(os.remove, file_name)
            except Exception as e:
                print(sickbeard.ex(e))
                continue


def setUp_test_episode_file():
    if not ek(os.path.exists, FILEDIR):
        ek(os.makedirs, FILEDIR)

    try:
        with open(FILEPATH, 'wb') as f:
            f.write(b"foo bar")
            f.flush()
    except Exception:
        print("Unable to set up test episode")
        raise


def tearDown_test_episode_file():
    if ek(os.path.exists, FILEDIR):
        ek(sickbeard.helpers.removetree, FILEDIR)


def setUp_test_show_dir():
    if not ek(os.path.exists, SHOWDIR):
        ek(os.makedirs, SHOWDIR)


def tearDown_test_show_dir():
    if ek(os.path.exists, SHOWDIR):
        ek(sickbeard.helpers.removetree, SHOWDIR)


def setUp_test_web_server():
    sickbeard.WEB_SERVER = SRWebServer({
        'port': 8081,
        'host': '0.0.0.0',
        'data_root': ek(os.path.join, sickbeard.PROG_DIR, 'gui', sickbeard.GUI_NAME),
        'web_root': "",
        'log_dir': sickbeard.LOG_DIR,
        'username': sickbeard.WEB_USERNAME,
        'password': sickbeard.WEB_PASSWORD,
        'enable_https': 0,
        'handle_reverse_proxy': 0,
        'https_cert': ek(os.path.join, sickbeard.PROG_DIR, sickbeard.HTTPS_CERT),
        'https_key': ek(os.path.join, sickbeard.PROG_DIR, sickbeard.HTTPS_KEY),
    }).start()


def tearDown_test_web_server():
    if sickbeard.WEB_SERVER:
        sickbeard.WEB_SERVER.shutDown()

        try:
            sickbeard.WEB_SERVER.join(10)
        except:
            pass

        sickbeard.WEB_SERVER = None

def load_tests(loader, tests, pattern):
    global TESTALL
    TESTALL = True
    return tests