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


import os
import unittest

import sickrage
import tests
from sickrage.core.helpers import make_dirs
from sickrage.core.processors.post_processor import PostProcessor
from sickrage.core.tv.episode import TVEpisode
from sickrage.core.tv.show import TVShow


def _log(message, level=None):
    sickrage.app.log.info(message)


class PPInitTests(tests.SiCKRAGETestCase):
    def setUp(self, **kwargs):
        super(PPInitTests, self).setUp()
        self.pp = PostProcessor(self.FILEPATH)

    def test_init_file_name(self):
        self.assertEqual(self.pp.file_name, self.FILENAME)

    def test_init_folder_name(self):
        self.assertEqual(self.pp.folder_name, self.SHOWNAME)


class PPBasicTests(tests.SiCKRAGETestDBCase):
    def test_process(self):
        show = TVShow(1, 3)
        show.name = self.SHOWNAME
        show.location = self.SHOWDIR
        show.save_to_db()
        sickrage.app.showlist = [show]
        ep = TVEpisode(show, self.SEASON, self.EPISODE)
        ep.name = "some ep name"
        ep.save_to_db()

        sickrage.app.name_cache.put('show name', 3)
        self.post_processor = PostProcessor(self.FILEPATH, process_method='move')
        self.post_processor._log = _log
        self.assertTrue(self.post_processor.process)


class PPMultiEPTests(tests.SiCKRAGETestDBCase):
    def setUp(self):
        self.FILEPATH = os.path.join(self.FILEDIR, 'show name.S01E01E02E03E04E05E06E07E08.Flight.462.Part.1-8.mkv')
        super(PPMultiEPTests, self).setUp()

    def test_process(self):
        show = TVShow(1, 3)
        show.name = self.SHOWNAME
        show.location = self.SHOWDIR
        show.save_to_db()
        sickrage.app.showlist = [show]

        sickrage.app.name_cache.put('show name', 3)
        self.post_processor = PostProcessor(self.FILEPATH, process_method='move')
        self.post_processor._log = _log
        self.assertTrue(self.post_processor.process)


class ListAssociatedFiles(tests.SiCKRAGETestCase):
    def setUp(self):
        super(ListAssociatedFiles, self).setUp()
        self.test_tree = os.path.join(self.FILEDIR, 'associated_files', 'random', 'recursive', 'subdir')

        file_names = [
            'Show Name [SickRage].avi',
            'Show Name [SickRage].srt',
            'Show Name [SickRage].nfo',
            'Show Name [SickRage].en.srt',
            'Non-Associated Show [SickRage].srt',
            'Non-Associated Show [SickRage].en.srt',
            'Show [SickRage] Non-Associated.en.srt',
            'Show [SickRage] Non-Associated.srt',
        ]
        self.file_list = [os.path.join(self.FILEDIR, f) for f in file_names] + [os.path.join(self.test_tree, f) for f in
                                                                                file_names]
        self.post_processor = PostProcessor('Show Name')
        self.post_processor._log = _log
        self.maxDiff = None
        sickrage.app.config.move_associated_files = True
        sickrage.app.config.allowed_extensions = ''

        make_dirs(self.test_tree)
        for test_file in self.file_list:
            open(test_file, 'a').close()

    def test_subfolders(self):
        # Test edge cases first:
        self.assertEqual([], self.post_processor.list_associated_files('', subfolders=True))
        self.assertEqual([], self.post_processor.list_associated_files('\\Show Name\\.nomedia', subfolders=True))

        associated_files = self.post_processor.list_associated_files(self.file_list[0], subfolders=True)

        associated_files = sorted(file_name.lstrip('./') for file_name in associated_files)
        out_list = sorted(file_name for file_name in self.file_list[1:] if 'Non-Associated' not in file_name)

        self.assertEqual(out_list, associated_files)

        # Test no associated files:
        associated_files = self.post_processor.list_associated_files('Fools Quest.avi', subfolders=True)

    def test_no_subfolders(self):
        associated_files = self.post_processor.list_associated_files(self.file_list[0], subfolders=False)

        associated_files = sorted(file_name.lstrip('./') for file_name in associated_files)
        out_list = sorted(file_name for file_name in self.file_list[1:] if
                          'associated_files' not in file_name and 'Non-Associated' not in file_name)

        self.assertEqual(out_list, associated_files)

    def test_subtitles_only(self):
        associated_files = self.post_processor.list_associated_files(self.file_list[0], subtitles_only=True,
                                                                     subfolders=True)

        associated_files = sorted(file_name.lstrip('./') for file_name in associated_files)
        out_list = sorted(file_name for file_name in self.file_list if
                          file_name.endswith('.srt') and 'Non-Associated' not in file_name)

        self.assertEqual(out_list, associated_files)

    def test_subtitles_only_no_subfolders(self):
        associated_files = self.post_processor.list_associated_files(self.file_list[0], subtitles_only=True,
                                                                     subfolders=False)
        associated_files = sorted(file_name.lstrip('./') for file_name in associated_files)
        out_list = sorted(file_name for file_name in self.file_list if file_name.endswith(
            '.srt') and 'associated_files' not in file_name and 'Non-Associated' not in file_name)

        self.assertEqual(out_list, associated_files)


if __name__ == '__main__':
    print("==================")
    print("STARTING - POSTPROCESSOR TESTS")
    print("==================")
    print("######################################################################")
    unittest.main()
