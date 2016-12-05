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

from __future__ import print_function
from __future__ import print_function
from __future__ import print_function
from __future__ import print_function
from __future__ import print_function
from __future__ import print_function
from __future__ import print_function
from __future__ import print_function
from __future__ import print_function
from __future__ import print_function
from __future__ import print_function
from __future__ import print_function
from __future__ import print_function
from __future__ import print_function
from __future__ import print_function
from __future__ import unicode_literals

import os.path
import unittest
from datetime import date

import sickrage
from sickrage.core.nameparser import ParseResult, NameParser, InvalidNameException, InvalidShowException
from sickrage.core.tv.show import TVShow
from tests import SiCKRAGETestDBCase

sickrage.SYS_ENCODING = 'UTF-8'

DEBUG = VERBOSE = False

simple_test_cases = {
    'standard': {
        'Mr.Show.Name.S01E02.Source.Quality.Etc-Group': ParseResult(None, 'Mr Show Name', 1, [2],
                                                                    'Source.Quality.Etc', 'Group'),
        'Show.Name.S01E02': ParseResult(None, 'Show Name', 1, [2]),
        'Show Name - S01E02 - My Ep Name': ParseResult(None, 'Show Name', 1, [2], 'My Ep Name'),
        'Show.1.0.Name.S01.E03.My.Ep.Name-Group': ParseResult(None, 'Show 1.0 Name', 1, [3],
                                                              'My.Ep.Name',
                                                              'Group'),
        'Show.Name.S01E02E03.Source.Quality.Etc-Group': ParseResult(None, 'Show Name', 1, [2, 3],
                                                                    'Source.Quality.Etc', 'Group'),
        'Mr. Show Name - S01E02-03 - My Ep Name': ParseResult(None, 'Mr. Show Name', 1, [2, 3],
                                                              'My Ep Name'),
        'Show.Name.S01.E02.E03': ParseResult(None, 'Show Name', 1, [2, 3]),
        'Show.Name-0.2010.S01E02.Source.Quality.Etc-Group': ParseResult(None, 'Show Name-0 2010', 1,
                                                                        [2],
                                                                        'Source.Quality.Etc', 'Group'),
        'S01E02 Ep Name': ParseResult(None, None, 1, [2], 'Ep Name'),
        'Show Name - S06E01 - 2009-12-20 - Ep Name': ParseResult(None, 'Show Name', 6, [1],
                                                                 '2009-12-20 - Ep Name'),
        'Show Name - S06E01 - -30-': ParseResult(None, 'Show Name', 6, [1], '30-'),
        'Show-Name-S06E01-720p': ParseResult(None, 'Show-Name', 6, [1], '720p'),
        'Show-Name-S06E01-1080i': ParseResult(None, 'Show-Name', 6, [1], '1080i'),
        'Show.Name.S06E01.Other.WEB-DL': ParseResult(None, 'Show Name', 6, [1], 'Other.WEB-DL'),
        'Show.Name.S06E01 Some-Stuff Here': ParseResult(None, 'Show Name', 6, [1], 'Some-Stuff Here')
    },

    'fov': {
        'Show_Name.1x02.Source_Quality_Etc-Group': ParseResult(None, 'Show Name', 1, [2],
                                                               'Source_Quality_Etc',
                                                               'Group'),
        'Show Name 1x02': ParseResult(None, 'Show Name', 1, [2]),
        'Show Name 1x02 x264 Test': ParseResult(None, 'Show Name', 1, [2], 'x264 Test'),
        'Show Name - 1x02 - My Ep Name': ParseResult(None, 'Show Name', 1, [2], 'My Ep Name'),
        'Show_Name.1x02x03x04.Source_Quality_Etc-Group': ParseResult(None, 'Show Name', 1, [2, 3, 4],
                                                                     'Source_Quality_Etc', 'Group'),
        'Show Name - 1x02-03-04 - My Ep Name': ParseResult(None, 'Show Name', 1, [2, 3, 4],
                                                           'My Ep Name'),
        '1x02 Ep Name': ParseResult(None, None, 1, [2], 'Ep Name'),
        'Show-Name-1x02-720p': ParseResult(None, 'Show-Name', 1, [2], '720p'),
        'Show-Name-1x02-1080i': ParseResult(None, 'Show-Name', 1, [2], '1080i'),
        'Show Name [05x12] Ep Name': ParseResult(None, 'Show Name', 5, [12], 'Ep Name'),
        'Show.Name.1x02.WEB-DL': ParseResult(None, 'Show Name', 1, [2], 'WEB-DL')
    },

    'standard_repeat': {
        'Show.Name.S01E02.S01E03.Source.Quality.Etc-Group': ParseResult(None, 'Show Name', 1, [2, 3],
                                                                        'Source.Quality.Etc', 'Group'),
        'Show.Name.S01E02.S01E03': ParseResult(None, 'Show Name', 1, [2, 3]),
        'Show Name - S01E02 - S01E03 - S01E04 - Ep Name': ParseResult(None, 'Show Name', 1, [2, 3, 4],
                                                                      'Ep Name'),
        'Show.Name.S01E02.S01E03.WEB-DL': ParseResult(None, 'Show Name', 1, [2, 3], 'WEB-DL')
    },

    'fov_repeat': {
        'Show.Name.1x02.1x03.Source.Quality.Etc-Group': ParseResult(None, 'Show Name', 1, [2, 3],
                                                                    'Source.Quality.Etc', 'Group'),
        'Show.Name.1x02.1x03': ParseResult(None, 'Show Name', 1, [2, 3]),
        'Show Name - 1x02 - 1x03 - 1x04 - Ep Name': ParseResult(None, 'Show Name', 1, [2, 3, 4],
                                                                'Ep Name'),
        'Show.Name.1x02.1x03.WEB-DL': ParseResult(None, 'Show Name', 1, [2, 3], 'WEB-DL')
    },

    'bare': {
        'Show.Name.102.Source.Quality.Etc-Group': ParseResult(None, 'Show Name', 1, [2],
                                                              'Source.Quality.Etc',
                                                              'Group'),
        'show.name.2010.123.source.quality.etc-group': ParseResult(None, 'show name 2010', 1, [23],
                                                                   'source.quality.etc', 'group'),
        'show.name.2010.222.123.source.quality.etc-group': ParseResult(None, 'show name 2010.222', 1,
                                                                       [23],
                                                                       'source.quality.etc', 'group'),
        'Show.Name.102': ParseResult(None, 'Show Name', 1, [2]),
        'the.event.401.hdtv-group': ParseResult(None, 'the event', 4, [1], 'hdtv', 'group'),
        'show.name.2010.special.hdtv-blah': None,
        'show.ex-name.102.hdtv-group': ParseResult(None, 'show ex-name', 1, [2], 'hdtv', 'group'),
    },

    'stupid': {
        'tpz-abc102': ParseResult(None, None, 1, [2], None, 'tpz'),
        'tpz-abc.102': ParseResult(None, None, 1, [2], None, 'tpz')
    },

    'no_season': {
        'Show Name - 01 - Ep Name': ParseResult(None, 'Show Name', None, [1], 'Ep Name'),
        '01 - Ep Name': ParseResult(None, None, None, [1], 'Ep Name'),
        'Show Name - 01 - Ep Name - WEB-DL': ParseResult(None, 'Show Name', None, [1],
                                                         'Ep Name - WEB-DL')
    },

    'no_season_general': {
        'Show.Name.E23.Source.Quality.Etc-Group': ParseResult(None, 'Show Name', None, [23],
                                                              'Source.Quality.Etc', 'Group'),
        'Show Name - Episode 01 - Ep Name': ParseResult(None, 'Show Name', None, [1], 'Ep Name'),
        'Show.Name.Part.3.Source.Quality.Etc-Group': ParseResult(None, 'Show Name', None, [3],
                                                                 'Source.Quality.Etc', 'Group'),
        'Show.Name.Part.1.and.Part.2.Blah-Group': ParseResult(None, 'Show Name', None, [1, 2], 'Blah',
                                                              'Group'),
        'Show.Name.Part.IV.Source.Quality.Etc-Group': ParseResult(None, 'Show Name', None, [4],
                                                                  'Source.Quality.Etc', 'Group'),
        'Deconstructed.E07.1080i.HDTV.DD5.1.MPEG2-TrollHD': ParseResult(None, 'Deconstructed', None,
                                                                        [7],
                                                                        '1080i.HDTV.DD5.1.MPEG2', 'TrollHD'),
        'Show.Name.E23.WEB-DL': ParseResult(None, 'Show Name', None, [23], 'WEB-DL'),
    },

    'no_season_multi_ep': {
        'Show.Name.E23-24.Source.Quality.Etc-Group': ParseResult(None, 'Show Name', None, [23, 24],
                                                                 'Source.Quality.Etc', 'Group'),
        'Show Name - Episode 01-02 - Ep Name': ParseResult(None, 'Show Name', None, [1, 2], 'Ep Name'),
        'Show.Name.E23-24.WEB-DL': ParseResult(None, 'Show Name', None, [23, 24], 'WEB-DL')
    },

    'season_only': {
        'Show.Name.S02.Source.Quality.Etc-Group': ParseResult(None, 'Show Name', 2, [],
                                                              'Source.Quality.Etc',
                                                              'Group'),
        'Show Name Season 2': ParseResult(None, 'Show Name', 2),
        'Season 02': ParseResult(None, None, 2)
    },

    'scene_date_format': {
        'Show.Name.2010.11.23.Source.Quality.Etc-Group': ParseResult(None, 'Show Name', None, [],
                                                                     'Source.Quality.Etc', 'Group',
                                                                     date(2010, 11, 23)),
        'Show Name - 2010.11.23': ParseResult(None, 'Show Name', air_date=date(2010, 11, 23)),
        'Show.Name.2010.23.11.Source.Quality.Etc-Group': ParseResult(None, 'Show Name', None, [],
                                                                     'Source.Quality.Etc', 'Group',
                                                                     date(2010, 11, 23)),
        'Show Name - 2010-11-23 - Ep Name': ParseResult(None, 'Show Name', extra_info='Ep Name',
                                                        air_date=date(2010, 11, 23)),
        '2010-11-23 - Ep Name': ParseResult(None, extra_info='Ep Name',
                                            air_date=date(2010, 11, 23)),
        'Show.Name.2010.11.23.WEB-DL': ParseResult(None, 'Show Name', None, [], 'WEB-DL', None,
                                                   date(2010, 11, 23))
    },
}

combination_test_cases = [
    ('/test/path/to/Season 02/03 - Ep Name.avi',
     ParseResult(None, None, 2, [3], 'Ep Name'),
     ['no_season', 'season_only']),

    ('Show.Name.S02.Source.Quality.Etc-Group/tpz-sn203.avi',
     ParseResult(None, 'Show Name', 2, [3], 'Source.Quality.Etc', 'Group'),
     ['stupid', 'season_only']),

    ('MythBusters.S08E16.720p.HDTV.x264-aAF/aaf-mb.s08e16.720p.mkv',
     ParseResult(None, 'MythBusters', 8, [16], '720p.HDTV.x264', 'aAF'),
     ['standard']),

    (
        '/home/drop/storage/TV/Terminator The Sarah Connor Chronicles/Season 2/S02E06 The Tower is Tall, But the Fall is Short.mkv',
        ParseResult(None, None, 2, [6], 'The Tower is Tall, But the Fall is Short'),
        ['standard']),

    (r'/Test/TV/Jimmy Fallon/Season 2/Jimmy Fallon - 2010-12-15 - blah.avi',
     ParseResult(None, 'Jimmy Fallon', extra_info='blah', air_date=date(2010, 12, 15)),
     ['scene_date_format']),

    (r'/X/30 Rock/Season 4/30 Rock - 4x22 -.avi',
     ParseResult(None, '30 Rock', 4, [22]),
     ['fov']),

    ('Season 2\\Show Name - 03-04 - Ep Name.ext',
     ParseResult(None, 'Show Name', 2, [3, 4], extra_info='Ep Name'),
     ['no_season', 'season_only']),

    ('Season 02\\03-04-05 - Ep Name.ext',
     ParseResult(None, None, 2, [3, 4, 5], extra_info='Ep Name'),
     ['no_season', 'season_only']),
]

unicode_test_cases = [
    ('The.Big.Bang.Theory.2x07.The.Panty.Pi\xf1ata.Polarization.720p.HDTV.x264.AC3-SHELDON.mkv',
     ParseResult(None, 'The.Big.Bang.Theory', 2, [7],
                 'The.Panty.Pi\xf1ata.Polarization.720p.HDTV.x264.AC3',
                 'SHELDON')),
    ('The.Big.Bang.Theory.2x07.The.Panty.Pi\xc3\xb1ata.Polarization.720p.HDTV.x264.AC3-SHELDON.mkv',
     ParseResult(None, 'The.Big.Bang.Theory', 2, [7],
                 'The.Panty.Pi\xc3\xb1ata.Polarization.720p.HDTV.x264.AC3',
                 'SHELDON'))
]

failure_cases = ['7sins-jfcs01e09-720p-bluray-x264']


class UnicodeTests(SiCKRAGETestDBCase):
    def __init__(self, something):
        super(UnicodeTests, self).__init__(something)
        self.setUp()
        self.show = TVShow(1, 1, 'en')
        self.show.name = "The Big Bang Theory"
        self.show.saveToDB()
        self.show.loadFromDB(skipNFO=True)

    def _test_unicode(self, name, result):
        np = NameParser(True, showObj=self.show)
        parse_result = np.parse(name)

        # this shouldn't raise an exception
        repr(str(parse_result))
        self.assertEqual(parse_result.extra_info, result.extra_info)

    def test_unicode(self):
        for (name, result) in unicode_test_cases:
            self._test_unicode(name, result)


class FailureCaseTests(SiCKRAGETestDBCase):
    @staticmethod
    def _test_name(name):
        np = NameParser(True)
        try:
            parse_result = np.parse(name)
        except (InvalidNameException, InvalidShowException):
            return True

        if VERBOSE:
            print('Actual: ', parse_result.which_regex, parse_result)
        return False

    def test_failures(self):
        for name in failure_cases:
            self.assertTrue(self._test_name(name))


class ComboTests(SiCKRAGETestDBCase):
    def _test_combo(self, name, result, which_regexes):

        if VERBOSE:
            print()
            print('Testing', name)

        np = NameParser(True)

        try:
            test_result = np.parse(name)
        except InvalidShowException:
            return False

        if DEBUG:
            print(test_result, test_result.which_regex)
            print(result, which_regexes)

        self.assertEqual(test_result, result)
        for cur_regex in which_regexes:
            self.assertTrue(cur_regex in test_result.which_regex)
        self.assertEqual(len(which_regexes), len(test_result.which_regex))

    def test_combos(self):

        for (name, result, which_regexes) in combination_test_cases:
            # Normalise the paths. Converts UNIX-style paths into Windows-style
            # paths when test is run on Windows.
            self._test_combo(os.path.normpath(name), result, which_regexes)


class BasicTests(SiCKRAGETestDBCase):
    def __init__(self, something):
        super(BasicTests, self).__init__(something)
        super(BasicTests, self).setUp()
        self.show = TVShow(1, 1, 'en')
        self.show.saveToDB()

    def _test_names(self, np, section, transform=None, verbose=False):
        if VERBOSE or verbose:
            print('Running', section, 'tests')
        for cur_test_base in simple_test_cases[section]:
            if transform:
                cur_test = transform(cur_test_base)
                np.file_name = cur_test
            else:
                cur_test = cur_test_base
            if VERBOSE or verbose:
                print('Testing', cur_test)

            result = simple_test_cases[section][cur_test_base]

            self.show.name = result.series_name if result else None
            np.showObj = self.show
            if not result:
                self.assertRaises(InvalidNameException, np.parse, cur_test)
                return
            else:
                result.which_regex = [section]
                test_result = np.parse(cur_test)

            if DEBUG or verbose:
                print('air_by_date:', test_result.is_air_by_date, 'air_date:', test_result.air_date)
                print('anime:', test_result.is_anime, 'ab_episode_numbers:', test_result.ab_episode_numbers)
                print(test_result)
                print(result)
            self.assertEqual(test_result.which_regex, [section])
            self.assertEqual(str(test_result), str(result))

    def test_standard_names(self):
        np = NameParser(True)
        self._test_names(np, 'standard')

    def test_standard_repeat_names(self):
        np = NameParser(False)
        self._test_names(np, 'standard_repeat')

    def test_fov_names(self):
        np = NameParser(False)
        self._test_names(np, 'fov')

    def test_fov_repeat_names(self):
        np = NameParser(False)
        self._test_names(np, 'fov_repeat')

    # def test_bare_names(self):
    #    np = parser.NameParser(False)
    #    self._test_names(np, 'bare')

    def test_stupid_names(self):
        np = NameParser(False)
        self._test_names(np, 'stupid')

    # def test_no_season_names(self):
    #    np = parser.NameParser(False)
    #    self._test_names(np, 'no_season')

    def test_no_season_general_names(self):
        np = NameParser(False)
        self._test_names(np, 'no_season_general')

    def test_no_season_multi_ep_names(self):
        np = NameParser(False)
        self._test_names(np, 'no_season_multi_ep')

    def test_season_only_names(self):
        np = NameParser(False)
        self._test_names(np, 'season_only')

    # def test_scene_date_format_names(self):
    #    np = parser.NameParser(False)
    #    self._test_names(np, 'scene_date_format')

    def test_standard_file_names(self):
        np = NameParser()
        self._test_names(np, 'standard', lambda x: x + '.avi')

    def test_standard_repeat_file_names(self):
        np = NameParser()
        self._test_names(np, 'standard_repeat', lambda x: x + '.avi')

    def test_fov_file_names(self):
        np = NameParser()
        self._test_names(np, 'fov', lambda x: x + '.avi')

    def test_fov_repeat_file_names(self):
        np = NameParser()
        self._test_names(np, 'fov_repeat', lambda x: x + '.avi')

    # def test_bare_file_names(self):
    #    np = parser.NameParser()
    #    self._test_names(np, 'bare', lambda x: x + '.avi')

    def test_stupid_file_names(self):
        np = NameParser()
        self._test_names(np, 'stupid', lambda x: x + '.avi')

    # def test_no_season_file_names(self):
    #    np = parser.NameParser()
    #    self._test_names(np, 'no_season', lambda x: x + '.avi')

    def test_no_season_general_file_names(self):
        np = NameParser()
        self._test_names(np, 'no_season_general', lambda x: x + '.avi')

    def test_no_season_multi_ep_file_names(self):
        np = NameParser()
        self._test_names(np, 'no_season_multi_ep', lambda x: x + '.avi')

    def test_season_only_file_names(self):
        np = NameParser()
        self._test_names(np, 'season_only', lambda x: x + '.avi')

    # def test_scene_date_format_file_names(self):
    #    np = parser.NameParser()
    #    self._test_names(np, 'scene_date_format', lambda x: x + '.avi')

    def test_combination_names(self):
        pass


if __name__ == '__main__':
    print("==================")
    print("STARTING - NAME PARSER TESTS")
    print("==================")
    print("######################################################################")
    unittest.main()
