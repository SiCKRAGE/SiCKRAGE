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

from tests import SiCKRAGETestCase, SiCKRAGETestDBCase

import sickbeard


class RSSTest(SiCKRAGETestCase): pass


def test_get_rss(self, provider):
    result = provider.cache.getRSSFeed(provider.url)
    if result:
        self.assertTrue(isinstance(result[b'feed'], dict))
        self.assertTrue(isinstance(result[b'entries'], list))
        for item in result[b'entries']:
            title, url = provider._get_title_and_url(item)
            self.assertTrue(title and url, "Failed to get title and url from RSS feed for %s" % provider.name)



for provider in sickbeard.providers.sortedProviderList():
    setattr(RSSTest, 'test_rss_%s' % provider.name, lambda self, x=provider: test_get_rss(self, x))

if __name__ == "__main__":
    print("==================")
    print("STARTING - RSS TESTS")
    print("==================")
    print("######################################################################")
    unittest.main()
