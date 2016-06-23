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

from sickrage.core.databases import main_db
from tests import SiCKRAGETestDBCase


class DBBasicTests(SiCKRAGETestDBCase):
    def setUp(self, **kwargs):
        super(DBBasicTests, self).setUp()
        self.db = main_db.MainDB()

    def test_select(self):
        self.db.select("SELECT * FROM tv_episodes WHERE showid = ? AND location != ''", [0000])


if __name__ == '__main__':
    print("==================")
    print("STARTING - DB TESTS")
    print("==================")
    print("######################################################################")
    unittest.main()
