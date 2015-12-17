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

from __future__ import unicode_literals

import os.path
import sys

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest

from tests import SiCKRAGETestCase, SiCKRAGETestDBCase

import sickbeard
from sickbeard.tv import TVEpisode, TVShow


class TVShowTests(SiCKRAGETestDBCase):
    def setUp(self, **kwargs):
        super(TVShowTests, self).setUp()
        sickbeard.showList = []

    def test_init_indexerid(self):
        show = TVShow(1, 0001, "en")
        self.assertEqual(show.indexerid, 0001)

    def test_change_indexerid(self):
        show = TVShow(1, 0001, "en")
        show.name = "show name"
        show.network = "cbs"
        show.genre = "crime"
        show.runtime = 40
        show.status = "Ended"
        show.default_ep_status = "5"
        show.airs = "monday"
        show.startyear = 1987

        show.saveToDB()
        show.loadFromDB(skipNFO=True)

        show.indexerid = 0002
        show.saveToDB()
        show.loadFromDB(skipNFO=True)

        self.assertEqual(show.indexerid, 0002)

    def test_set_name(self):
        show = TVShow(1, 0001, "en")
        show.name = "newName"
        show.saveToDB()
        show.loadFromDB(skipNFO=True)
        self.assertEqual(show.name, "newName")


class TVEpisodeTests(SiCKRAGETestDBCase):
    def setUp(self, **kwargs):
        super(TVEpisodeTests, self).setUp()
        sickbeard.showList = []

    def test_init_empty_db(self):
        show = TVShow(1, 0001, "en")
        ep = TVEpisode(show, 1, 1)
        ep.name = "asdasdasdajkaj"
        ep.saveToDB()
        ep.loadFromDB(1, 1)
        self.assertEqual(ep.name, "asdasdasdajkaj")


class TVTests(SiCKRAGETestDBCase):
    def setUp(self, **kwargs):
        super(TVTests, self).setUp()
        sickbeard.showList = []

    def test_getEpisode(self):
        show = TVShow(1, 0001, "en")
        show.name = "show name"
        show.network = "cbs"
        show.genre = "crime"
        show.runtime = 40
        show.status = "Ended"
        show.default_ep_status = "5"
        show.airs = "monday"
        show.startyear = 1987
        show.saveToDB()
        sickbeard.showList = [show]
        # TODO: implement


if __name__ == '__main__':
    print "=================="
    print "STARTING - TV TESTS"
    print "=================="
    print "######################################################################"
    unittest.main()