#!/usr/bin/env python3
# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import datetime
import unittest

import sickrage
import tests
from sickrage.core.tv.show.helpers import find_show
from sickrage.core.common import UNAIRED
from sickrage.core.databases.main import MainDB
from sickrage.core.tv.episode import TVEpisode
from sickrage.core.tv.show import TVShow


class DBBasicTests(tests.SiCKRAGETestDBCase):
    def setUp(self):
        super(DBBasicTests, self).setUp()
        show = TVShow(1, 0o0001, "en")
        show.save_to_db()
        sickrage.app.showlist += [show]

        ep = TVEpisode(show, 1, 1)
        ep.indexerid = 1
        ep.name = "test episode 1"
        ep.airdate = datetime.date.fromordinal(733832)
        ep.status = UNAIRED
        ep.save_to_db()
        ep = TVEpisode(show, 1, 2)
        ep.indexerid = 2
        ep.name = "test episode 2"
        ep.airdate = datetime.date.fromordinal(733832)
        ep.status = UNAIRED
        ep.save_to_db()
        ep = TVEpisode(show, 1, 3)
        ep.indexerid = 3
        ep.name = "test episode 3"
        ep.airdate = datetime.date.fromordinal(733832)
        ep.status = UNAIRED
        ep.save_to_db()

    def test_unaired(self):
        count = 0

        for episode in MainDB.TVEpisode.query:
            if all([episode.status == UNAIRED, episode.season > 0, episode.airdate > 1]):
                count += 1

                show = find_show(int(episode.showid))

                ep = TVEpisode(show, 1, episode.episode)
                ep.indexerid = episode.episode
                ep.name = "test episode {}".format(episode.episode)
                ep.airdate = datetime.date.fromordinal(733832)
                ep.status = UNAIRED

                ep.save_to_db()

        self.assertEqual(count, 3)


if __name__ == '__main__':
    print("==================")
    print("STARTING - DB TESTS")
    print("==================")
    print("######################################################################")
    unittest.main()
