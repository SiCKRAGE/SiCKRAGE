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

import certifi
import requests
import sickbeard.providers as providers
from sickrage.helper.exceptions import ex

class SNI_Tests(SiCKRAGETestCase): pass

def test_sni(self, provider):
    try:
        requests.head(provider.url, verify=certifi.where(), timeout=5)
    except requests.exceptions.Timeout:
        pass
    except requests.exceptions.SSLError as error:
        if 'SSL3_GET_SERVER_CERTIFICATE' not in ex(error):
            print(error)
    except Exception:
        pass

for provider in providers.sortedProviderList():
    setattr(SNI_Tests, 'test_%s' % provider.name, lambda self, x=provider: test_sni(self, x))

if __name__ == "__main__":
    print("==================")
    print("STARTING - SSL TESTS")
    print("==================")
    print("######################################################################")
    unittest.main()