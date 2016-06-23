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

import unittest

import sickrage
from sickrage.core.processors.post_processor import PostProcessor
from sickrage.core.tv.episode import TVEpisode
from sickrage.core.tv.show import TVShow
from tests import EPISODE, FILENAME, FILEPATH, SEASON, SHOWDIR, \
    SHOWNAME, SiCKRAGETestCase, SiCKRAGETestDBCase


class PPInitTests(SiCKRAGETestCase):
    def setUp(self, **kwargs):
        super(PPInitTests, self).setUp()
        self.pp = PostProcessor(FILEPATH)

    def tearDown(self, **kwargs):
        super(PPInitTests, self).tearDown()

    def test_init_file_name(self):
        self.assertEqual(self.pp.file_name, FILENAME)

    def test_init_folder_name(self):
        self.assertEqual(self.pp.folder_name, SHOWNAME)


class PPBasicTests(SiCKRAGETestDBCase):
    def setUp(self, **kwargs):
        super(PPBasicTests, self).setUp()

    def tearDown(self, **kwargs):
        super(PPBasicTests, self).tearDown()

    def test_process(self):
        show = TVShow(1, 3)
        show.name = SHOWNAME
        show.location = SHOWDIR
        show.saveToDB()
        show.loadFromDB(skipNFO=True)
        sickrage.srCore.SHOWLIST = [show]
        ep = TVEpisode(show, SEASON, EPISODE)
        ep.name = "some ep name"
        ep.saveToDB()

        sickrage.srCore.NAMECACHE.addNameToCache('show name', 3)
        self.pp = PostProcessor(FILEPATH, process_method='move')
        self.assertTrue(self.pp.process)


# class PPWebServerTests(SiCKRAGETestDBCase):
#     def setUp(self, **kwargs):
#         super(PPWebServerTests, self).setUp(True)
#
#     def tearDown(self, **kwargs):
#         super(PPWebServerTests, self).tearDown(True)
#
#     def test_process(self):
#         s = requests.Session()
#
#         params = {
#             "proc_dir": FILEDIR,
#             "nzbName": FILEPATH,
#             "failed": 0,
#             "process_method": "move",
#             "force": 0,
#             "quiet": 1
#         }
#
#         login_params = {
#             'username': sickrage.WEB_USERNAME,
#             'password': sickrage.WEB_PASSWORD
#         }
#
#         s.post(
#                 "http://localhost:8081/login",
#                 data=login_params,
#                 stream=True,
#                 verify=False,
#                 timeout=(30, 60)
#         )
#
#         r = s.get(
#                 "http://localhost:8081/home/postprocess/processEpisode",
#                 auth=(sickrage.WEB_USERNAME, sickrage.WEB_PASSWORD),
#                 params=params,
#                 stream=True,
#                 verify=False,
#                 timeout=(30, 1800)
#         )
#
#         self.assertTrue(
#                 line for line in r.iter_lines() if line.lower() in ["processing succeeded", "successfully processed"])


if __name__ == '__main__':
    print("==================")
    print("STARTING - POSTPROCESSOR TESTS")
    print("==================")
    print("######################################################################")
    unittest.main()
