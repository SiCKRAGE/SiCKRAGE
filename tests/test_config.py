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

from tests import SiCKRAGETestCase

from sickbeard import config


class QualityTests(SiCKRAGETestCase):
    def test_clean_url(self):
        self.assertEqual(config.clean_url("https://subdomain.domain.tld/endpoint"),
                         "https://subdomain.domain.tld/endpoint")
        self.assertEqual(config.clean_url("google.com/xml.rpc"), "http://google.com/xml.rpc")
        self.assertEqual(config.clean_url("google.com"), "http://google.com/")
        self.assertEqual(config.clean_url("http://www.example.com/folder/"), "http://www.example.com/folder/")
        self.assertEqual(config.clean_url("scgi:///home/user/.config/path/socket"),
                         "scgi:///home/user/.config/path/socket")


if __name__ == '__main__':
    print("==================")
    print("STARTING - CONFIG TESTS")
    print("==================")
    print("######################################################################")
    unittest.main()