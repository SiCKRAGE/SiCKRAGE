#!/usr/bin/env python3
# coding=utf-8
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


import os.path
import unittest

import tests
from sickrage.core.helpers import sanitize_file_name


class EncodingTests(tests.SiCKRAGETestCase):
    def test_encoding(self):
        rootDir = 'C:\\Temp\\TV'
        strings = ['Les Enfants De La T\xe9l\xe9', 'RT� One']

        for s in strings:
            show_dir = os.path.join(rootDir, sanitize_file_name(s))
            self.assertIsInstance(show_dir, str)


if __name__ == "__main__":
    print("==================")
    print("STARTING - ENCODING TESTS")
    print("==================")
    print("######################################################################")
    unittest.main()
