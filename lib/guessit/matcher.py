#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# GuessIt - A library for guessing information from filenames
# Copyright (c) 2013 Nicolas Wack <wackou@gmail.com>
# Copyright (c) 2013 Rémi Alvergnat <toilal.dev@gmail.com>
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

from __future__ import absolute_import, division, print_function, \
    unicode_literals

import logging
import inspect

from guessit import PY3, u
from guessit.transfo import TransformerException
from guessit.matchtree import MatchTree
from guessit.textutils import normalize_unicode, clean_default
from guessit.guess import Guess

log = logging.getLogger(__name__)


class IterativeMatcher(object):
    """An iterative matcher tries to match different patterns that appear
    in the filename.

    The ``filetype`` argument indicates which type of file you want to match.
    If it is undefined, the matcher will try to see whether it can guess
    that the file corresponds to an episode, or otherwise will assume it is
    a movie.

    The recognized ``filetype`` values are:
    ``['subtitle', 'info', 'movie', 'moviesubtitle', 'movieinfo', 'episode',
    'episodesubtitle', 'episodeinfo']``

    ``options`` is a dict of options values to be passed to the transformations used
    by the matcher.

    The IterativeMatcher works mainly in 2 steps:

    First, it splits the filename into a match_tree, which is a tree of groups
    which have a semantic meaning, such as episode number, movie title,
    etc...

    The match_tree created looks like the following::

      0000000000000000000000000000000000000000000000000000000000000000000000000000000000 111
      0000011111111111112222222222222233333333444444444444444455555555666777777778888888 000
      0000000000000000000000000000000001111112011112222333333401123334000011233340000000 000
      __________________(The.Prestige).______.[____.HP.______.{__-___}.St{__-___}.Chaps].___
      xxxxxttttttttttttt               ffffff  vvvv    xxxxxx  ll lll     xx xxx         ccc
      [XCT].Le.Prestige.(The.Prestige).DVDRip.[x264.HP.He-Aac.{Fr-Eng}.St{Fr-Eng}.Chaps].mkv

    The first 3 lines indicates the group index in which a char in the
    filename is located. So for instance, ``x264`` (in the middle) is the group (0, 4, 1), and
    it corresponds to a video codec, denoted by the letter ``v`` in the 4th line.
    (for more info, see guess.matchtree.to_string)

    Second, it tries to merge all this information into a single object
    containing all the found properties, and does some (basic) conflict
    resolution when they arise.
    """
    def __init__(self, filename, options=None, **kwargs):
        options = dict(options or {})
        for k, v in kwargs.items():
            if k not in options or not options[k]:
                options[k] = v  # options dict has priority over keyword arguments
        self._validate_options(options)
        if not PY3 and not isinstance(filename, unicode):
            log.warning('Given filename to matcher is not unicode...')
            filename = filename.decode('utf-8')

        filename = normalize_unicode(filename)
        if options and options.get('clean_function'):
            clean_function = options.get('clean_function')
            if not hasattr(clean_function, '__call__'):
                module, function = clean_function.rsplit('.')
                if not module:
                    module = 'guessit.textutils'
                clean_function = getattr(__import__(module), function)
                if not clean_function:
                    log.error('Can\'t find clean function %s. Default will be used.' % options.get('clean_function'))
                    clean_function = clean_default
        else:
            clean_function = clean_default

        self.match_tree = MatchTree(filename, clean_function=clean_function)
        self.options = options
        self._transfo_calls = []

        # sanity check: make sure we don't process a (mostly) empty string
        if clean_function(filename).strip() == '':
            return

        from guessit.plugins import transformers

        try:
            mtree = self.match_tree
            if 'type' in self.options:
                mtree.guess.set('type', self.options['type'], confidence=0.0)

            # Process
            for transformer in transformers.all_transformers():
                disabled = options.get('disabled_transformers')
                if not disabled or transformer.name not in disabled:
                    self._process(transformer, False)

            # Post-process
            for transformer in transformers.all_transformers():
                disabled = options.get('disabled_transformers')
                if not disabled or transformer.name not in disabled:
                    self._process(transformer, True)

            log.debug('Found match tree:\n%s' % u(mtree))
        except TransformerException as e:
            log.debug('An error has occurred in Transformer %s: %s' % (e.transformer, e))

    def _process(self, transformer, post=False):

        if not hasattr(transformer, 'should_process') or transformer.should_process(self.match_tree, self.options):
            if post:
                transformer.post_process(self.match_tree, self.options)
            else:
                transformer.process(self.match_tree, self.options)
                self._transfo_calls.append(transformer)

    @property
    def second_pass_options(self):
        second_pass_options = {}
        for transformer in self._transfo_calls:
            if hasattr(transformer, 'second_pass_options'):
                transformer_second_pass_options = transformer.second_pass_options(self.match_tree, self.options)
                if transformer_second_pass_options:
                    second_pass_options.update(transformer_second_pass_options)

        return second_pass_options

    @staticmethod
    def _validate_options(options):
        valid_filetypes = ('subtitle', 'info', 'video',
                           'movie', 'moviesubtitle', 'movieinfo',
                           'episode', 'episodesubtitle', 'episodeinfo')

        type_ = options.get('type')
        if type_ and type_ not in valid_filetypes:
            raise ValueError("filetype needs to be one of %s" % (valid_filetypes,))

    def matched(self):
        return self.match_tree.matched()


def build_guess(node, name, value=None, confidence=1.0):
    guess = Guess({name: node.clean_value if value is None else value}, confidence=confidence)
    guess.metadata().input = node.value if value is None else value
    if value is None:
        left_offset = 0
        right_offset = 0

        clean_value = node.clean_value

        if clean_value:
            for i in range(0, len(node.value)):
                if clean_value[0] == node.value[i]:
                    break
                left_offset += 1

            for i in reversed(range(0, len(node.value))):
                if clean_value[-1] == node.value[i]:
                    break
                right_offset += 1

        guess.metadata().span = (node.span[0] - node.offset + left_offset, node.span[1] - node.offset - right_offset)
    return guess


def found_property(node, name, value=None, confidence=1.0, update_guess=True, logger=None):
    # automatically retrieve the log object from the caller frame
    if not logger:
        caller_frame = inspect.stack()[1][0]
        logger = caller_frame.f_locals['self'].log
    guess = build_guess(node, name, value, confidence)
    return found_guess(node, guess, update_guess=update_guess, logger=logger)


def found_guess(node, guess, update_guess=True, logger=None):
    if node.guess:
        if update_guess:
            node.guess.update_highest_confidence(guess)
        else:
            child = node.add_child(guess.metadata().span)
            child.guess = guess
    else:
        node.guess = guess
    log_found_guess(guess, logger)
    return node.guess


def log_found_guess(guess, logger=None):
    for k, v in guess.items():
        (logger or log).debug('Property found: %s=%s (%s) (confidence=%.2f)' %
                              (k, v, guess.raw(k), guess.confidence(k)))


class GuessFinder(object):
    def __init__(self, guess_func, confidence=None, logger=None, options=None):
        self.guess_func = guess_func
        self.confidence = confidence
        self.logger = logger or log
        self.options = options or {}

    def process_nodes(self, nodes):
        for node in nodes:
            self.process_node(node)

    def process_node(self, node, iterative=True, partial_span=None):
        if partial_span:
            value = node.value[partial_span[0]:partial_span[1]]
        else:
            value = node.value
        string = ' %s ' % value  # add sentinels

        matcher_result = self.guess_func(string, node, self.options)
        if not matcher_result:
            return

        if not isinstance(matcher_result, Guess):
            result, span = matcher_result
        else:
            result, span = matcher_result, matcher_result.metadata().span
            #log.error('span2 %s' % (span,))

        if not result:
            return

        if span[1] == len(string):
            # somehow, the sentinel got included in the span. Remove it
            span = (span[0], span[1] - 1)

        # readjust span to compensate for sentinels
        span = (span[0] - 1, span[1] - 1)

        # readjust span to compensate for partial_span
        if partial_span:
            span = (span[0] + partial_span[0], span[1] + partial_span[0])

        skip_nodes = self.options.get('skip_nodes')
        if skip_nodes:
            # if we guessed a node that we need to skip, recurse down the tree and ignore that node
            for skip_node in skip_nodes:
                skip_node_relative_span = (skip_node.span[0] - node.offset, skip_node.span[1] - node.offset)
                if skip_node_relative_span == span:
                    partition_spans = [s for s in node.get_partition_spans(span) if s != skip_node.span]
                    for partition_span in partition_spans:
                        relative_span = (partition_span[0] - node.offset, partition_span[1] - node.offset)
                        self.process_node(node, partial_span=relative_span)
                    return


        # restore sentinels compensation
        if isinstance(result, Guess):
            guess = result
        else:
            guess = Guess(result, confidence=self.confidence, input=string, span=span)

        if not iterative:
            found_guess(node, guess, logger=self.logger)
        else:
            absolute_span = (span[0] + node.offset, span[1] + node.offset)
            node.partition(span)

            if node.is_leaf():
                # FIXME: this seems like it is dead code...
                found_guess(node, guess, logger=self.logger)

            else:
                found_child = None

                for child in node.children:
                    if child.span == absolute_span:
                        # if we have a match on one of our children, mark it as such...
                        found_guess(child, guess, logger=self.logger)
                        found_child = child
                        break

                # ...and only then recurse on the other children
                for child in node.children:
                    if child is not found_child:
                        self.process_node(child)

