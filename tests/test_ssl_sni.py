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

import certifi
import requests

import sickrage
from tests import SiCKRAGETestCase


class SNI_Tests(SiCKRAGETestCase): pass

def test_sni(self, provider):
    try:
        requests.head(provider.url, verify=certifi.where(), timeout=5)
    except requests.exceptions.Timeout:
        pass
    except requests.exceptions.SSLError as error:
        if 'SSL3_GET_SERVER_CERTIFICATE' not in error:
            print(error)
    except Exception:
        pass


for providerID, providerObj in sickrage.srCore.providersDict.all().items():
    setattr(SNI_Tests, 'test_%s' % providerObj.name, lambda self, x=providerObj: test_sni(self, x))

if __name__ == "__main__":
    print("==================")
    print("STARTING - SSL TESTS")
    print("==================")
    print("######################################################################")
    unittest.main()
