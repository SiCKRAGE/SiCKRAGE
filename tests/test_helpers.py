#!/usr/bin/env python3
# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.



import unittest

import tests

test_result = 'Show.Name.S01E01.HDTV.x264-RLSGROUP'
test_cases = {
    'removewords': [
        test_result,
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[cttv]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP.RiPSaLoT',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[GloDLS]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[EtHD]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP-20-40',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[NO-RAR] - [ www.torrentday.com ]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[rarbg]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[Seedbox]',
        '{ www.SceneTime.com } - Show.Name.S01E01.HDTV.x264-RLSGROUP',
        '].[www.tensiontorrent.com] - Show.Name.S01E01.HDTV.x264-RLSGROUP',
        '[ www.TorrentDay.com ] - Show.Name.S01E01.HDTV.x264-RLSGROUP',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[silv4]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[AndroidTwoU]',
        '[www.newpct1.com]Show.Name.S01E01.HDTV.x264-RLSGROUP',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP-NZBGEEK',
        '.www.Cpasbien.pwShow.Name.S01E01.HDTV.x264-RLSGROUP',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP [1044]',
        '[ www.Cpasbien.pw ] Show.Name.S01E01.HDTV.x264-RLSGROUP',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP.[BT]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[vtv]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP.[www.usabit.com]',
        '[www.Cpasbien.com] Show.Name.S01E01.HDTV.x264-RLSGROUP',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[ettv]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[rartv]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP-Siklopentan',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP-RP',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[PublicHD]',
        '[www.Cpasbien.pe] Show.Name.S01E01.HDTV.x264-RLSGROUP',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP[eztv]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP-[SpastikusTV]',
        '].[ www.tensiontorrent.com ] - Show.Name.S01E01.HDTV.x264-RLSGROUP',
        '[ www.Cpasbien.com ] Show.Name.S01E01.HDTV.x264-RLSGROUP',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP- { www.SceneTime.com }',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP- [ www.torrentday.com ]',
        'Show.Name.S01E01.HDTV.x264-RLSGROUP.Renc'
    ]
}


class HelpersTests(tests.SiCKRAGETestCase):
    pass


def test_generator(test_strings):
    def _test(self):
        for test_string in test_strings:
            from sickrage.core.helpers import remove_non_release_groups
            self.assertEqual(remove_non_release_groups(test_string), test_result)

    return _test


for name, test_data in test_cases.items():
    setattr(HelpersTests, 'test_%s' % name, test_generator(test_data))

if __name__ == '__main__':
    print("==================")
    print("STARTING - Helpers TESTS")
    print("==================")
    print("######################################################################")

    unittest.main()
