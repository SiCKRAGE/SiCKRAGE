#!/usr/bin/env python2.7
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

from __future__ import print_function

import sys, os.path

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest

import test_lib as test

import sickbeard
from sickrage.helper.exceptions import ex

class RSSTest(test.SiCKRAGETestCase): pass

def test_get_rss(self, provider):
        result = provider.cache.getRSSFeed(provider.url)
        self.assertIsNot(result, None, "Failed to get RSS feed for %s" % provider.name)
        self.assertTrue(isinstance(result['feed'], dict))
        self.assertTrue(isinstance(result['entries'], list))
        for item in result['entries']:
            title, url = provider._get_title_and_url(item)
            self.assertTrue(title and url, "Failed to get title and url from RSS feed for %s" % provider.name)

def test_update_cache(self, provider):
    provider.cache.updateCache()

for provider in sickbeard.providers.sortedProviderList():
    setattr(RSSTest, 'test_get_rss_%s' % provider.name, lambda self,x=provider: test_get_rss(self, x))
    setattr(RSSTest, 'test_update_cache_%s' % provider.name, lambda self,x=provider: test_update_cache(self, x))

if __name__ == "__main__":
    print("==================")
    print("STARTING - RSS TESTS")
    print("==================")
    print("######################################################################")

    suite = unittest.TestLoader().loadTestsFromTestCase(RSSTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
