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

from sickbeard import show_name_helpers, scene_exceptions, common, name_cache
from sickbeard import db
from sickbeard.tv import TVShow as Show


class SceneTests(SiCKRAGETestDBCase):
    def _test_sceneToNormalShowNames(self, name, expected):
        result = show_name_helpers.sceneToNormalShowNames(name)
        self.assertTrue(len(set(expected).intersection(set(result))) == len(expected))

        dot_result = show_name_helpers.sceneToNormalShowNames(name.replace(' ', '.'))
        dot_expected = [x.replace(' ', '.') for x in expected]
        self.assertTrue(len(set(dot_expected).intersection(set(dot_result))) == len(dot_expected))

    def _test_allPossibleShowNames(self, name, indexerid=0, expected=[]):
        s = Show(1, indexerid)
        s.name = name

        result = show_name_helpers.allPossibleShowNames(s)
        self.assertTrue(len(set(expected).intersection(set(result))) == len(expected))

    def _test_filterBadReleases(self, name, expected):
        result = show_name_helpers.filterBadReleases(name)
        self.assertEqual(result, expected)

    def _test_isGoodName(self, name, show):
        self.assertTrue(show_name_helpers.isGoodResult(name, show))

    def test_isGoodName(self):
        listOfcases = [('Show.Name.S01E02.Test-Test', 'Show/Name'),
                       ('Show.Name.S01E02.Test-Test', 'Show. Name'),
                       ('Show.Name.S01E02.Test-Test', 'Show- Name'),
                       ('Show.Name.Part.IV.Test-Test', 'Show Name'),
                       ('Show.Name.S01.Test-Test', 'Show Name'),
                       ('Show.Name.E02.Test-Test', 'Show: Name'),
                       ('Show Name Season 2 Test', 'Show: Name'),
                       ]

        for testCase in listOfcases:
            scene_name, show_name = testCase
            s = Show(1, 0)
            s.name = show_name
            self._test_isGoodName(scene_name, s)
            del s

    def test_sceneToNormalShowNames(self):
        self._test_sceneToNormalShowNames('Show Name 2010', ['Show Name 2010', 'Show Name (2010)'])
        self._test_sceneToNormalShowNames('Show Name US', ['Show Name US', 'Show Name (US)'])
        self._test_sceneToNormalShowNames('Show Name AU', ['Show Name AU', 'Show Name (AU)'])
        self._test_sceneToNormalShowNames('Show Name CA', ['Show Name CA', 'Show Name (CA)'])
        self._test_sceneToNormalShowNames('Show and Name', ['Show and Name', 'Show & Name'])
        self._test_sceneToNormalShowNames('Show and Name 2010',
                                          ['Show and Name 2010', 'Show & Name 2010', 'Show and Name (2010)',
                                           'Show & Name (2010)'])
        self._test_sceneToNormalShowNames('show name us', ['show name us', 'show name (us)'])
        self._test_sceneToNormalShowNames('Show And Name', ['Show And Name', 'Show & Name'])

        # failure cases
        self._test_sceneToNormalShowNames('Show Name 90210', ['Show Name 90210'])
        self._test_sceneToNormalShowNames('Show Name YA', ['Show Name YA'])

    def test_allPossibleShowNames(self):
        scene_exceptions.exceptionsCache[-1] = ['Exception Test']
        myDB = db.DBConnection("cache.db")
        myDB.action("INSERT INTO scene_exceptions (indexer_id, show_name, season) VALUES (?,?,?)",
                    [-1, 'Exception Test', -1])
        common.countryList['Full Country Name'] = 'FCN'

        self._test_allPossibleShowNames('Show Name', expected=['Show Name'])
        self._test_allPossibleShowNames('Show Name', -1, expected=['Show Name', 'Exception Test'])
        self._test_allPossibleShowNames('Show Name FCN', expected=['Show Name FCN', 'Show Name (Full Country Name)'])
        self._test_allPossibleShowNames('Show Name (FCN)',
                                        expected=['Show Name (FCN)', 'Show Name (Full Country Name)'])
        self._test_allPossibleShowNames('Show Name Full Country Name',
                                        expected=['Show Name Full Country Name', 'Show Name (FCN)'])
        self._test_allPossibleShowNames('Show Name (Full Country Name)',
                                        expected=['Show Name (Full Country Name)', 'Show Name (FCN)'])

    def test_filterBadReleases(self):
        self._test_filterBadReleases('Show.S02.German.Stuff-Grp', False)
        self._test_filterBadReleases('Show.S02.Some.Stuff-Core2HD', False)
        self._test_filterBadReleases('Show.S02.Some.German.Stuff-Grp', False)
        self._test_filterBadReleases('Show.S02.This.Is.German', False)


class SceneExceptionTestCase(SiCKRAGETestDBCase):
    def setUp(self, **kwargs):
        super(SceneExceptionTestCase, self).setUp()
        scene_exceptions.retrieve_exceptions()

    def tearDown(self, **kwargs):
        super(SceneExceptionTestCase, self).tearDown()

    def test_sceneExceptionsEmpty(self):
        self.assertEqual(scene_exceptions.get_scene_exceptions(0), [])

    def test_sceneExceptionsBabylon5(self):
        self.assertEqual(sorted(scene_exceptions.get_scene_exceptions(70726)), ['Babylon 5', 'Babylon5'])

    def test_sceneExceptionByName(self):
        self.assertEqual(scene_exceptions.get_scene_exception_by_name('Babylon5'), (70726, -1))
        self.assertEqual(scene_exceptions.get_scene_exception_by_name('babylon 5'), (70726, -1))
        self.assertEqual(scene_exceptions.get_scene_exception_by_name('Carlos 2010'), (164451, -1))

    def test_sceneExceptionByNameEmpty(self):
        self.assertEqual(scene_exceptions.get_scene_exception_by_name('nothing useful'), (None, None))

    def test_sceneExceptionsResetNameCache(self):
        # clear the exceptions
        myDB = db.DBConnection("cache.db")
        myDB.action("DELETE FROM scene_exceptions")

        # put something in the cache
        name_cache.addNameToCache('Cached Name', 0)

        # updating should not clear the cache this time since our exceptions didn't change
        scene_exceptions.retrieve_exceptions()
        self.assertEqual(name_cache.retrieveNameFromCache('Cached Name'), 0)


if __name__ == '__main__':
    print("==================")
    print("STARTING - SCENE HELPER TESTS")
    print("==================")
    print("######################################################################")
    unittest.main()
