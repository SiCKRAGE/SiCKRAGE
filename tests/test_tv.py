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

from __future__ import unicode_literals

import unittest

import sickrage
from sickrage.core.tv.episode import TVEpisode
from sickrage.core.tv.show import TVShow
from tests import SiCKRAGETestDBCase


class TVShowTests(SiCKRAGETestDBCase):
    def setUp(self, **kwargs):
        super(TVShowTests, self).setUp()
        sickrage.srCore.SHOWLIST = []

    def test_init_indexerid(self):
        show = TVShow(1, 0001, "en")
        show.saveToDB()
        show.loadFromDB(skipNFO=True)

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
        super(TVEpisodeTests, self).setUp(force_db=True)
        sickrage.srCore.SHOWLIST = []

    def test_init_empty_db(self):
        show = TVShow(1, 0001, "en")
        show.saveToDB()
        show.loadFromDB(skipNFO=True)

        ep = TVEpisode(show, 1, 1)
        ep.name = "asdasdasdajkaj"
        ep.saveToDB()
        ep.loadFromDB(1, 1)
        self.assertEqual(ep.name, "asdasdasdajkaj")


class TVTests(SiCKRAGETestDBCase):
    def setUp(self, **kwargs):
        super(TVTests, self).setUp()
        sickrage.srCore.SHOWLIST = []

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
        show.loadFromDB(skipNFO=True)
        sickrage.srCore.SHOWLIST = [show]

if __name__ == '__main__':
    print "=================="
    print "STARTING - TV TESTS"
    print "=================="
    print "######################################################################"
    unittest.main()
