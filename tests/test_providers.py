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
from sickrage.core.websession import WebSession
from tests import SiCKRAGETestCase

providers_disabled = ['bitcannon']


class ProviderTest(SiCKRAGETestCase):
    pass


def generator(provider):
    """
    Generate test
    """

    def do_test(self):
        resp = WebSession(cache=False).get(provider.urls['base_url'], timeout=30)
        self.assertTrue(provider.urls['base_url'] in resp.url,
                        '{} redirected to {}'.format(provider.urls['base_url'], resp.url))
        self.assertTrue(resp.status_code in [200, 403],
                        '{} returned a status code of {}'.format(resp.url, resp.status_code))

    return do_test


for providerID, providerObj in sickrage.app.search_providers.torrent().items():
    if not providerID in providers_disabled:
        test = generator(providerObj)
        setattr(ProviderTest, 'test_{}'.format(providerID), test)

if __name__ == '__main__':
    print("=========================")
    print("STARTING - PROVIDER TESTS")
    print("=========================")
    print("######################################################################")
    unittest.main()
