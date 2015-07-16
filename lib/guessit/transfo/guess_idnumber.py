#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# GuessIt - A library for guessing information from filenames
# Copyright (c) 2013 Nicolas Wack <wackou@gmail.com>
#
# GuessIt is free software; you can redistribute it and/or modify it under
# the terms of the Lesser GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# GuessIt is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# Lesser GNU General Public License for more details.
#
# You should have received a copy of the Lesser GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division, print_function, unicode_literals

import re

from guessit.plugins.transformers import Transformer
from guessit.matcher import GuessFinder


_DIGIT = 0
_LETTER = 1
_OTHER = 2


class GuessIdnumber(Transformer):
    def __init__(self):
        Transformer.__init__(self, 220)

    def supported_properties(self):
        return ['idNumber']

    _idnum = re.compile(r'(?P<idNumber>[a-zA-Z0-9-]{20,})')  # 1.0, (0, 0))

    def guess_idnumber(self, string, node=None, options=None):
        match = self._idnum.search(string)
        if match is not None:
            result = match.groupdict()
            switch_count = 0
            switch_letter_count = 0
            letter_count = 0
            last_letter = None

            last = _LETTER
            for c in result['idNumber']:
                if c in '0123456789':
                    ci = _DIGIT
                elif c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ':
                    ci = _LETTER
                    if c != last_letter:
                        switch_letter_count += 1
                    last_letter = c
                    letter_count += 1
                else:
                    ci = _OTHER

                if ci != last:
                    switch_count += 1

                last = ci

            switch_ratio = float(switch_count) / len(result['idNumber'])
            letters_ratio = (float(switch_letter_count) / letter_count) if letter_count > 0 else 1

            # only return the result as probable if we alternate often between
            # char type (more likely for hash values than for common words)
            if switch_ratio > 0.4 and letters_ratio > 0.4:
                return result, match.span()

        return None, None

    def process(self, mtree, options=None):
        GuessFinder(self.guess_idnumber, 0.4, self.log, options).process_nodes(mtree.unidentified_leaves())
