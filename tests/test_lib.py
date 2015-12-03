# coding=UTF-8
# Author: Dennis Lutter <lad1337@gmail.com>
# URL: http://code.google.com/p/sickbeard/
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


import sys, os.path

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest

from configobj import ConfigObj

import shutil

import sickbeard

from sickbeard import db, providers, tvcache, logger
from sickbeard.databases import mainDB
from sickbeard.databases import cache_db, failed_db
from sickbeard.tv import TVEpisode
from sickrage.helper.encoding import ek

#=================
# test globals
#=================
TESTSKIPPED = ['issue_submitter_tests']
TESTDIR = ek(os.path.abspath, ek(os.path.dirname, __file__))
TESTDBNAME = "sickbeard.db"
TESTCACHEDBNAME = "cache.db"
TESTFAILEDDBNAME = "failed.db"

SHOWNAME = u"show name"
SEASON = 4
EPISODE = 2
FILENAME = u"show name - s0" + str(SEASON) + "e0" + str(EPISODE) + ".mkv"
FILEDIR = ek(os.path.join, TESTDIR, SHOWNAME)
FILEPATH = ek(os.path.join, FILEDIR, FILENAME)
SHOWDIR = ek(os.path.join, TESTDIR, SHOWNAME + " final")

#=================
# prepare env functions
#=================
def createTestLogFolder():
    if not ek(os.path.isdir,sickbeard.LOG_DIR):
        ek(os.mkdir, sickbeard.LOG_DIR)

def createTestCacheFolder():
    if not ek(os.path.isdir,sickbeard.CACHE_DIR):
        ek(os.mkdir, sickbeard.CACHE_DIR)

# call env functions at appropriate time during sickbeard var setup

#=================
# sickbeard globals
#=================
sickbeard.SYS_ENCODING = 'UTF-8'

sickbeard.showList = []
sickbeard.QUALITY_DEFAULT = 4  # hdtv
sickbeard.FLATTEN_FOLDERS_DEFAULT = 0

sickbeard.NAMING_PATTERN = ''
sickbeard.NAMING_ABD_PATTERN = ''
sickbeard.NAMING_SPORTS_PATTERN = ''
sickbeard.NAMING_MULTI_EP = 1


sickbeard.PROVIDER_ORDER = ["sick_beard_index"]
sickbeard.newznabProviderList = providers.getNewznabProviderList("'Sick Beard Index|http://lolo.sickbeard.com/|0|5030,5040|0|eponly|0|0|0!!!NZBs.org|https://nzbs.org/||5030,5040,5060,5070,5090|0|eponly|0|0|0!!!Usenet-Crawler|https://www.usenet-crawler.com/||5030,5040,5060|0|eponly|0|0|0'")
sickbeard.providerList = providers.makeProviderList()

sickbeard.PROG_DIR = ek(os.path.abspath, ek(os.path.join, TESTDIR, '..'))
sickbeard.DATA_DIR = TESTDIR
sickbeard.CONFIG_FILE = ek(os.path.join, sickbeard.DATA_DIR, "config.ini")
sickbeard.CFG = ConfigObj(sickbeard.CONFIG_FILE)
sickbeard.TV_DOWNLOAD_DIR = FILEDIR

sickbeard.BRANCH = sickbeard.config.check_setting_str(sickbeard.CFG, 'General', 'branch', '')
sickbeard.CUR_COMMIT_HASH = sickbeard.config.check_setting_str(sickbeard.CFG, 'General', 'cur_commit_hash', '')
sickbeard.GIT_USERNAME = sickbeard.config.check_setting_str(sickbeard.CFG, 'General', 'git_username', '')
sickbeard.GIT_PASSWORD = sickbeard.config.check_setting_str(sickbeard.CFG, 'General', 'git_password', '', censor_log=True)

sickbeard.CACHE_DIR = ek(os.path.join, TESTDIR, 'cache')
createTestCacheFolder()

sickbeard.LOG_DIR = ek(os.path.join, TESTDIR, 'Logs')
sickbeard.logger.logFile = ek(os.path.join, sickbeard.LOG_DIR, 'test_sickbeard.log')
createTestLogFolder()

sickbeard.logger.initLogging(False, True)

#=================
# dummy functions
#=================
def _dummy_saveConfig():
    return True

# this overrides the sickbeard save_config which gets called during a db upgrade
mainDB.sickbeard.save_config = _dummy_saveConfig

# the real one tries to contact tvdb just stop it from getting more info on the ep
def _fake_specifyEP(self, season, episode):
    pass

TVEpisode.specifyEpisode = _fake_specifyEP

#=================
# test classes
#=================
class SiCKRAGETestCase(unittest.TestCase):
    def setUp(self):
        if self.__module__ in TESTSKIPPED:
            raise unittest.SkipTest()

class SiCKRAGETestDBCase(SiCKRAGETestCase):
    def setUp(self):
        sickbeard.showList = []
        setUp_test_db()
        setUp_test_episode_file()
        setUp_test_show_dir()

    def tearDown(self):
        sickbeard.showList = []
        tearDown_test_db()
        tearDown_test_episode_file()
        tearDown_test_show_dir()

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
                sqlResults = self.select("SELECT url, COUNT(url) AS count FROM [" + providerName + "] GROUP BY url HAVING count > 1")

                for cur_dupe in sqlResults:
                    self.action("DELETE FROM [" + providerName + "] WHERE url = ?", [cur_dupe["url"]])

            # add unique index to prevent further dupes from happening if one does not exist
            self.action("CREATE UNIQUE INDEX IF NOT EXISTS idx_url ON [" + providerName + "] (url)")

            # add release_group column to table if missing
            if not self.hasColumn(providerName, 'release_group'):
                self.addColumn(providerName, 'release_group', "TEXT", "")

            # add version column to table if missing
            if not self.hasColumn(providerName, 'version'):
                self.addColumn(providerName, 'version', "NUMERIC", "-1")

        except Exception, e:
            if str(e) != "table [" + providerName + "] already exists":
                raise

        # Create the table if it's not already there
        try:
            if not self.hasTable('lastUpdate'):
                self.action("CREATE TABLE lastUpdate (provider TEXT, time NUMERIC)")
        except Exception, e:
            if str(e) != "table lastUpdate already exists":
                raise

# this will override the normal db connection
sickbeard.db.DBConnection = TestDBConnection
sickbeard.tvcache.CacheDBConnection = TestCacheDBConnection

#=================
# test functions
#=================
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
    for current_db in [ TESTDBNAME, TESTCACHEDBNAME, TESTFAILEDDBNAME ]:
        file_name = ek(os.path.join, TESTDIR, current_db)
        if ek(os.path.exists,file_name):
            try:
                ek(os.remove, file_name)
            except Exception as e:
                print sickbeard.ex(e)
                continue

def setUp_test_episode_file():
    if not ek(os.path.exists,FILEDIR):
        ek(os.makedirs, FILEDIR)

    try:
        with open(FILEPATH, 'wb') as f:
            f.write("foo bar")
            f.flush()
    except Exception:
        print "Unable to set up test episode"
        raise


def tearDown_test_episode_file():
    if ek(os.path.exists,FILEDIR):
        ek(sickbeard.helpers.removetree,FILEDIR)


def setUp_test_show_dir():
    if not ek(os.path.exists,SHOWDIR):
        ek(os.makedirs, SHOWDIR)


def tearDown_test_show_dir():
    if ek(os.path.exists,SHOWDIR):
        ek(sickbeard.helpers.removetree,SHOWDIR)


if __name__ == '__main__':
    print "=================="
    print "Dont call this directly"
    print "=================="
    print "you might want to call"

    dirList = ek(os.listdir, TESTDIR)
    for fname in dirList:
        if (fname.find("_test") > 0) and (fname.find("pyc") < 0):
            print "- " + fname

    print "=================="
    print "or just call all_tests.py"