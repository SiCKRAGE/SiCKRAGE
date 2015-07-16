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

import itertools

from guessit.plugins.transformers import Transformer
from guessit.matcher import found_guess
from guessit.containers import PropertiesContainer


class GuessEpisodeDetails(Transformer):
    def __init__(self):
        Transformer.__init__(self, -205)
        self.container = PropertiesContainer()
        self.container.register_property('episodeDetails', 'Special', 'Bonus', 'Omake', 'Ova', 'Oav', 'Pilot', 'Unaired')
        self.container.register_property('episodeDetails', 'Extras?', canonical_form='Extras')

    def guess_details(self, string, node=None, options=None):
        properties = self.container.find_properties(string, node, options, 'episodeDetails', multiple=True)
        guesses = self.container.as_guess(properties, multiple=True)
        return guesses

    def second_pass_options(self, mtree, options=None):
        if not mtree.guess.get('type', '').startswith('episode'):
            for unidentified_leaf in mtree.unidentified_leaves():
                properties = self.container.find_properties(unidentified_leaf.value, unidentified_leaf, options, 'episodeDetails')
                guess = self.container.as_guess(properties)
                if guess:
                    return {'type': 'episode'}
        return None

    def supported_properties(self):
        return self.container.get_supported_properties()

    def process(self, mtree, options=None):
        if (mtree.guess.get('type', '').startswith('episode') and
            (not mtree.info.get('episodeNumber') or
             mtree.info.get('season') == 0)):

            for leaf in itertools.chain(mtree.leaves_containing('title'),
                                        mtree.unidentified_leaves()):
                guesses = self.guess_details(leaf.value, leaf, options)
                for guess in guesses:
                    found_guess(leaf, guess, update_guess=False)

        return None
