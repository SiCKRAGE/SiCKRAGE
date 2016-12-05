#!/usr/bin/env python2.7
# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
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
from tests import SiCKRAGETestCase


class RSSTest(SiCKRAGETestCase): pass

def test_get_rss(self, provider):
    result = provider.cache.getRSSFeed(provider.urls['base_url'])
    if result:
        self.assertTrue(isinstance(result['feed'], dict))
        self.assertTrue(isinstance(result['entries'], list))
        for item in result['entries']:
            title, url = provider._get_title_and_url(item)
            self.assertTrue(title and url, "Failed to get title and url from RSS feed for %s" % provider.name)


for providerID, providerObj in sickrage.srCore.providersDict.all().items():
    setattr(RSSTest, 'test_rss_%s' % providerObj.name, lambda self, x=providerObj: test_get_rss(self, x))

if __name__ == "__main__":
    print("==================")
    print("STARTING - RSS TESTS")
    print("==================")
    print("######################################################################")
    unittest.main()
