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

import sys, os.path

tests_dir=os.path.abspath(__file__)[:-len(os.path.basename(__file__))]

sys.path.insert(1, os.path.join(tests_dir, '../lib'))
sys.path.insert(1, os.path.join(tests_dir, '..'))

import glob
import unittest

def suite():
    alltests = unittest.TestSuite()
    for suites in unittest.defaultTestLoader.discover(tests_dir, pattern='*_tests.py'):
        for tests in suites:
            try:
                alltests.addTests(tests)
            except:
                continue
    return alltests

def testAll():
    print "######################################################################"
    print "=================="
    print "STARTING - ALL TESTS"
    print "=================="
    print "######################################################################"
    if not unittest.TextTestRunner(verbosity=2).run(suite()).wasSuccessful():
        sys.exit(1)

if __name__ == "__main__":
    testAll()