#!/usr/bin/env python2

# Author: echel0n <echel0n@sickrage.ca>
# URL: https://git.sickrage.ca
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

import io
import os
import os.path
import shutil
import sys
import threading
import unittest

import sickrage
from sickrage.core import Core
from sickrage.core.caches import tv_cache
from sickrage.core.databases import Connection, main_db, cache_db, failed_db
from sickrage.core.tv import episode

# =================
# prepare env functions
# =================
def createFolder(dirname):
    if not os.path.isdir(dirname):
        os.mkdir(dirname)

# =================
# dummy functions
# =================
# the real one tries to contact tvdb just stop it from getting more info on the ep
def _fake_specifyEP(self, season, episode):
    pass

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
                    self.action("DELETE FROM [" + providerName + "] WHERE url = ?", [cur_dupe["url"]])

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
        # retrieve_exceptions(False, False)

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
        with io.open(FILEPATH, 'wb') as f:
            f.write(b"foo bar")
            f.flush()
    except Exception:
        print("Unable to set up test episode")
        raise


def tearDown_test_episode_file():
    if os.path.exists(FILEDIR):
        shutil.rmtree(FILEDIR)


def setUp_test_show_dir():
    if not os.path.exists(SHOWDIR):
        os.makedirs(SHOWDIR)


def tearDown_test_show_dir():
    if os.path.exists(SHOWDIR):
        shutil.rmtree(SHOWDIR)


def setUp_test_web_server():
    threading.Thread(None, sickrage.srCore.srWebServer.start).start()


def tearDown_test_web_server():
    if sickrage.srCore:
        sickrage.srCore.srWebServer.shutdown()


def load_tests(loader, tests):
    global TESTALL
    TESTALL = True
    return tests

# =================
# test globals
# =================
threading.currentThread().setName('TESTS')

PROG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'sickrage'))
if PROG_DIR not in sys.path:
    sys.path.insert(0, PROG_DIR)

sickrage.DATA_DIR = TESTDIR = os.path.abspath(os.path.dirname(__file__))
sickrage.CONFIG_FILE = TESTCONFIGNAME = os.path.abspath(os.path.join(TESTDIR, "config.ini"))
sickrage.NOLAUNCH = True
sickrage.srCore = Core()

TESTALL = False
TESTSKIPPED = ['test_issue_submitter', 'test_ssl_sni']
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

episode.TVEpisode.populateEpisode = _fake_specifyEP
tv_cache.CacheDBConnection = TestCacheDBConnection

threading.Thread(target=sickrage.srCore.start).start()