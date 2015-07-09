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

from guessit.plugins.transformers import Transformer, get_transformer
from guessit.textutils import reorder_title

from guessit.matcher import found_property


class GuessEpisodeInfoFromPosition(Transformer):
    def __init__(self):
        Transformer.__init__(self, -200)

    def supported_properties(self):
        return ['title', 'series']

    def match_from_epnum_position(self, mtree, node, options):
        epnum_idx = node.node_idx

        # a few helper functions to be able to filter using high-level semantics
        def before_epnum_in_same_pathgroup():
            return [leaf for leaf in mtree.unidentified_leaves(lambda x: len(x.clean_value) > 1)
                    if (leaf.node_idx[0] == epnum_idx[0] and
                    leaf.node_idx[1:] < epnum_idx[1:])]

        def after_epnum_in_same_pathgroup():
            return [leaf for leaf in mtree.unidentified_leaves(lambda x: len(x.clean_value) > 1)
                    if (leaf.node_idx[0] == epnum_idx[0] and
                    leaf.node_idx[1:] > epnum_idx[1:])]

        def after_epnum_in_same_explicitgroup():
            return [leaf for leaf in mtree.unidentified_leaves(lambda x: len(x.clean_value) > 1)
                    if (leaf.node_idx[:2] == epnum_idx[:2] and
                    leaf.node_idx[2:] > epnum_idx[2:])]

        # epnumber is the first group and there are only 2 after it in same
        # path group
        # -> series title - episode title
        title_candidates = self._filter_candidates(after_epnum_in_same_pathgroup(), options)

        if ('title' not in mtree.info and  # no title
                'series' in mtree.info and # series present
                before_epnum_in_same_pathgroup() == [] and  # no groups before
                len(title_candidates) == 1):  # only 1 group after

            found_property(title_candidates[0], 'title', confidence=0.4)
            return

        if ('title' not in mtree.info and  # no title
                before_epnum_in_same_pathgroup() == [] and  # no groups before
                len(title_candidates) == 2):  # only 2 groups after

            found_property(title_candidates[0], 'series', confidence=0.4)
            found_property(title_candidates[1], 'title', confidence=0.4)
            return

        # if we have at least 1 valid group before the episodeNumber, then it's
        # probably the series name
        series_candidates = before_epnum_in_same_pathgroup()
        if len(series_candidates) >= 1:
            found_property(series_candidates[0], 'series', confidence=0.7)

        # only 1 group after (in the same path group) and it's probably the
        # episode title.
        title_candidates = self._filter_candidates(after_epnum_in_same_pathgroup(), options)
        if len(title_candidates) == 1:
            found_property(title_candidates[0], 'title', confidence=0.5)
            return
        else:
            # try in the same explicit group, with lower confidence
            title_candidates = self._filter_candidates(after_epnum_in_same_explicitgroup(), options)
            if len(title_candidates) == 1:
                found_property(title_candidates[0], 'title', confidence=0.4)
                return
            elif len(title_candidates) > 1:
                found_property(title_candidates[0], 'title', confidence=0.3)
                return

        # get the one with the longest value
        title_candidates = self._filter_candidates(after_epnum_in_same_pathgroup(), options)
        if title_candidates:
            maxidx = -1
            maxv = -1
            for i, c in enumerate(title_candidates):
                if len(c.clean_value) > maxv:
                    maxidx = i
                    maxv = len(c.clean_value)
            found_property(title_candidates[maxidx], 'title', confidence=0.3)

    def should_process(self, mtree, options=None):
        options = options or {}
        return not options.get('skip_title') and mtree.guess.get('type', '').startswith('episode')

    @staticmethod
    def _filter_candidates(candidates, options):
        episode_details_transformer = get_transformer('guess_episode_details')
        if episode_details_transformer:
            return [n for n in candidates if not episode_details_transformer.container.find_properties(n.value, n, options, re_match=True)]
        else:
            return candidates

    def process(self, mtree, options=None):
        """
        try to identify the remaining unknown groups by looking at their
        position relative to other known elements
        """
        eps = [node for node in mtree.leaves() if 'episodeNumber' in node.guess]

        if not eps:
            eps = [node for node in mtree.leaves() if 'date' in node.guess]

        if eps:
            self.match_from_epnum_position(mtree, eps[0], options)

        else:
            # if we don't have the episode number, but at least 2 groups in the
            # basename, then it's probably series - eptitle
            basename = mtree.node_at((-2,))

            title_candidates = self._filter_candidates(basename.unidentified_leaves(), options)

            if len(title_candidates) >= 2 and 'series' not in mtree.info:
                found_property(title_candidates[0], 'series', confidence=0.4)
                found_property(title_candidates[1], 'title', confidence=0.4)
            elif len(title_candidates) == 1:
                # but if there's only one candidate, it's probably the series name
                found_property(title_candidates[0], 'series' if 'series' not in mtree.info else 'title', confidence=0.4)

        # if we only have 1 remaining valid group in the folder containing the
        # file, then it's likely that it is the series name
        try:
            series_candidates = list(mtree.node_at((-3,)).unidentified_leaves())
        except ValueError:
            series_candidates = []

        if len(series_candidates) == 1:
            found_property(series_candidates[0], 'series', confidence=0.3)

        # if there's a path group that only contains the season info, then the
        # previous one is most likely the series title (ie: ../series/season X/..)
        eps = [node for node in mtree.nodes()
               if 'season' in node.guess and 'episodeNumber' not in node.guess]

        if eps:
            previous = [node for node in mtree.unidentified_leaves()
                        if node.node_idx[0] == eps[0].node_idx[0] - 1]
            if len(previous) == 1:
                found_property(previous[0], 'series', confidence=0.5)

        # If we have found title without any serie name, replace it by the serie name.
        if 'series' not in mtree.info and 'title' in mtree.info:
            title_leaf = mtree.first_leaf_containing('title')
            metadata = title_leaf.guess.metadata('title')
            value = title_leaf.guess['title']
            del title_leaf.guess['title']
            title_leaf.guess.set('series', value, metadata=metadata)

    def post_process(self, mtree, options=None):
        for node in mtree.nodes():
            if 'series' not in node.guess:
                continue

            node.guess['series'] = reorder_title(node.guess['series'])
