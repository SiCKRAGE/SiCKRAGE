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

import test_lib as test

import sickbeard
from sickbeard.tv import TVEpisode, TVShow
from sickbeard.name_cache import addNameToCache
from sickbeard.postProcessor import PostProcessor

class PPInitTests(test.SiCKRAGETestCase):
    def setUp(self):
        super(PPInitTests, self).setUp()
        self.pp = PostProcessor(test.FILEPATH)

    def tearDown(self):
        super(PPInitTests, self).tearDown()

    def test_init_file_name(self):
        self.assertEqual(self.pp.file_name, test.FILENAME)

    def test_init_folder_name(self):
        self.assertEqual(self.pp.folder_name, test.SHOWNAME)

class PPBasicTests(test.SiCKRAGETestDBCase):
    def setUp(self):
        super(PPBasicTests, self).setUp()

    def tearDown(self):
        super(PPBasicTests, self).tearDown()

    def test_process(self):
        show = TVShow(1,3)
        show.name = test.SHOWNAME
        show.location = test.SHOWDIR
        show.saveToDB()

        sickbeard.showList = [show]
        ep = TVEpisode(show, test.SEASON, test.EPISODE)
        ep.name = "some ep name"
        ep.saveToDB()

        addNameToCache('show name', 3)
        self.pp = PostProcessor(test.FILEPATH, process_method='move')
        self.assertTrue(self.pp.process())

if __name__ == '__main__':
    print "=================="
    print "STARTING - POSTPROCESSOR TESTS"
    print "=================="
    print "######################################################################"
    suite = unittest.TestLoader().loadTestsFromTestCase(PPInitTests)
    unittest.TextTestRunner(verbosity=2).run(suite)
    print "######################################################################"
    suite = unittest.TestLoader().loadTestsFromTestCase(PPBasicTests)
    unittest.TextTestRunner(verbosity=2).run(suite)
