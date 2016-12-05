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
from sickrage.core.common import countryList
from sickrage.core.helpers import show_names
from sickrage.core.scene_exceptions import exceptionsCache, get_scene_exceptions, \
    get_scene_exception_by_name
from sickrage.core.tv.show import TVShow
from tests import SiCKRAGETestDBCase


class SceneTests(SiCKRAGETestDBCase):
    def _test_sceneToNormalShowNames(self, name, expected):
        result = show_names.sceneToNormalShowNames(name)
        self.assertTrue(len(set(expected).intersection(set(result))) == len(expected))

        dot_result = show_names.sceneToNormalShowNames(name.replace(' ', '.'))
        dot_expected = [x.replace(' ', '.') for x in expected]
        self.assertTrue(len(set(dot_expected).intersection(set(dot_result))) == len(dot_expected))

    def _test_allPossibleShowNames(self, name, indexerid=0, expected=[]):
        s = TVShow(1, indexerid)
        s.name = name
        s.saveToDB()
        s.loadFromDB(skipNFO=True)


        result = show_names.allPossibleShowNames(s)
        self.assertTrue(len(set(expected).intersection(set(result))) == len(expected))

    def _test_filterBadReleases(self, name, expected):
        result = show_names.filterBadReleases(name)
        self.assertEqual(result, expected)

    def _test_isGoodName(self, name, show):
        self.assertTrue(show_names.isGoodResult(name, show))

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
            s = TVShow(1, 0)
            s.name = show_name
            s.saveToDB()
            s.loadFromDB(skipNFO=True)
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
        sickrage.srCore.cacheDB.db.insert({
            '_t': 'scene_exceptions',
            'indexer_id': -1,
            'show_name': 'Exception Test',
            'season': -1
        })

        exceptionsCache[-1] = ['Exception Test']
        countryList['Full Country Name'] = 'FCN'

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

    def tearDown(self, **kwargs):
        super(SceneExceptionTestCase, self).tearDown()

    def test_sceneExceptionsEmpty(self):
        self.assertEqual(get_scene_exceptions(0), [])

    def test_sceneExceptionsBabylon5(self):
        self.assertEqual(sorted(get_scene_exceptions(70726)), ['Babylon 5', 'Babylon5'])

    def test_sceneExceptionByName(self):
        self.assertEqual(get_scene_exception_by_name('Babylon5'), (70726, -1))
        self.assertEqual(get_scene_exception_by_name('babylon 5'), (70726, -1))
        self.assertEqual(get_scene_exception_by_name('Carlos 2010'), (164451, -1))

    def test_sceneExceptionByNameEmpty(self):
        self.assertEqual(get_scene_exception_by_name('nothing useful'), (None, None))

    def test_sceneExceptionsResetNameCache(self):
        # clear the exceptions
        [sickrage.srCore.cacheDB.db.delete(x['doc']) for x in sickrage.srCore.cacheDB.db.all('scene_exceptions', with_doc=True)]

        # put something in the cache
        sickrage.srCore.NAMECACHE.put('Cached Name', 0)

        # updating should not clear the cache this time since our exceptions didn't change
        self.assertEqual(sickrage.srCore.NAMECACHE.get('Cached Name'), 0)


if __name__ == '__main__':
    print("==================")
    print("STARTING - SCENE HELPER TESTS")
    print("==================")
    print("######################################################################")
    unittest.main()
