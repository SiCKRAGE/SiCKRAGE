#!/usr/bin/env python2
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

from __future__ import unicode_literals

import os
import re

import sickrage
from sickrage.core.common import NAMING_EXTEND, NAMING_LIMITED_EXTEND, NAMING_LIMITED_EXTEND_E_PREFIXED, \
    NAMING_DUPLICATE, NAMING_SEPARATED_REPEAT, Quality
from sickrage.core.helpers import sanitizeFileName, sanitizeSceneName, remove_non_release_groups, remove_extension
from sickrage.core.nameparser import NameParser, InvalidNameException, InvalidShowException


def dirty_setter(attr_name):
    def wrapper(self, val):
        if getattr(self, attr_name) != val:
            setattr(self, attr_name, val)
            self.dirty = True
    return wrapper

def _ep_name(episode):
    """
    Returns the name of the episode to use during renaming. Combines the names of related episodes.
    Eg. "Ep Name (1)" and "Ep Name (2)" becomes "Ep Name"
        "Ep Name" and "Other Ep Name" becomes "Ep Name & Other Ep Name"
    """

    multiNameRegex = r"(.*) \(\d{1,2}\)"

    episode.relatedEps = sorted(episode.relatedEps, key=lambda x: x.episode)

    singleName = True
    curGoodName = None

    for curName in [episode.name] + [x.name for x in episode.relatedEps]:
        match = re.match(multiNameRegex, curName)
        if not match:
            singleName = False
            break

        if curGoodName is None:
            curGoodName = match.group(1)
        elif curGoodName != match.group(1):
            singleName = False
            break

    if singleName:
        goodName = curGoodName
    else:
        goodName = episode.name
        for relEp in episode.relatedEps:
            goodName += " & " + relEp.name

    return goodName

def _replace_map(episode):
    """
    Generates a replacement map for this episode which maps all possible custom naming patterns to the correct
    value for this episode.

    Returns: A dict with patterns as the keys and their replacement values as the values.
    """

    ep_name = _ep_name(episode)

    def dot(name):
        return sanitizeSceneName(name)

    def us(name):
        return re.sub('[ -]', '_', name)

    def release_name(name):
        if name:
            name = remove_non_release_groups(remove_extension(name))
        return name

    def release_group(show, name):
        if name:
            name = remove_non_release_groups(remove_extension(name))
        else:
            return ""

        try:
            np = NameParser(name, showObj=show, naming_pattern=True)
            parse_result = np.parse(name)
        except (InvalidNameException, InvalidShowException) as e:
            sickrage.LOGGER.debug("Unable to get parse release_group: {}".format(e))
            return ''

        if not parse_result.release_group:
            return ''
        return parse_result.release_group

    _, epQual = Quality.splitCompositeStatus(episode.status)  # @UnusedVariable

    if sickrage.NAMING_STRIP_YEAR:
        show_name = re.sub(r"\(\d+\)$", "", episode.show.name).rstrip()
    else:
        show_name = episode.show.name

    # try to get the release group
    rel_grp = {}
    rel_grp[b"SiCKRAGE"] = 'SiCKRAGE'
    if hasattr(episode, 'location'):  # from the location name
        rel_grp[b'location'] = release_group(episode.show, episode.location)
        if not rel_grp[b'location']:
            del rel_grp[b'location']
    if hasattr(episode, '_release_group'):  # from the release group field in db
        rel_grp[b'database'] = episode._release_group
        if not rel_grp[b'database']:
            del rel_grp[b'database']
    if hasattr(episode, 'release_name'):  # from the release name field in db
        rel_grp[b'release_name'] = release_group(episode.show, episode.release_name)
        if not rel_grp[b'release_name']:
            del rel_grp[b'release_name']

    # use release_group, release_name, location in that order
    if 'database' in rel_grp:
        relgrp = 'database'
    elif 'release_name' in rel_grp:
        relgrp = 'release_name'
    elif 'location' in rel_grp:
        relgrp = 'location'
    else:
        relgrp = 'SiCKRAGE'

    # try to get the release encoder to comply with scene naming standards
    encoder = Quality.sceneQualityFromName(episode.release_name.replace(rel_grp[relgrp], ""), epQual)
    if encoder:
        sickrage.LOGGER.debug("Found codec for '" + show_name + ": " + ep_name + "'.")

    return {
        '%SN': show_name,
        '%S.N': dot(show_name),
        '%S_N': us(show_name),
        '%EN': ep_name,
        '%E.N': dot(ep_name),
        '%E_N': us(ep_name),
        '%QN': Quality.qualityStrings[epQual],
        '%Q.N': dot(Quality.qualityStrings[epQual]),
        '%Q_N': us(Quality.qualityStrings[epQual]),
        '%SQN': Quality.sceneQualityStrings[epQual] + encoder,
        '%SQ.N': dot(Quality.sceneQualityStrings[epQual] + encoder),
        '%SQ_N': us(Quality.sceneQualityStrings[epQual] + encoder),
        '%S': str(episode.season),
        '%0S': '%02d' % episode.season,
        '%E': str(episode.episode),
        '%0E': '%02d' % episode.episode,
        '%XS': str(episode.scene_season),
        '%0XS': '%02d' % episode.scene_season,
        '%XE': str(episode.scene_episode),
        '%0XE': '%02d' % episode.scene_episode,
        '%AB': '%(#)03d' % {'#': episode.absolute_number},
        '%XAB': '%(#)03d' % {'#': episode.scene_absolute_number},
        '%RN': release_name(episode.release_name),
        '%RG': rel_grp[relgrp],
        '%CRG': rel_grp[relgrp].upper(),
        '%AD': str(episode.airdate).replace('-', ' '),
        '%A.D': str(episode.airdate).replace('-', '.'),
        '%A_D': us(str(episode.airdate)),
        '%A-D': str(episode.airdate),
        '%Y': str(episode.airdate.year),
        '%M': str(episode.airdate.month),
        '%D': str(episode.airdate.day),
        '%0M': '%02d' % episode.airdate.month,
        '%0D': '%02d' % episode.airdate.day,
        '%RT': "PROPER" if episode.is_proper else "",
    }


def _format_string(pattern, replace_map):
    """
    Replaces all template strings with the correct value
    """

    result_name = pattern

    # do the replacements
    for cur_replacement in sorted(replace_map.keys(), reverse=True):
        result_name = result_name.replace(cur_replacement,
                                          sanitizeFileName(replace_map[cur_replacement]))
        result_name = result_name.replace(cur_replacement.lower(),
                                          sanitizeFileName(replace_map[cur_replacement].lower()))

    return result_name

def _format_pattern(show, episode, pattern=None, multi=None, anime_type=None):
    """
    Manipulates an episode naming pattern and then fills the template in
    """

    if pattern is None:
        pattern = sickrage.NAMING_PATTERN

    if multi is None:
        multi = sickrage.NAMING_MULTI_EP

    if sickrage.NAMING_CUSTOM_ANIME:
        if anime_type is None:
            anime_type = sickrage.NAMING_ANIME
    else:
        anime_type = 3

    replace_map = _replace_map(episode)

    result_name = pattern

    # if there's no release group in the db, let the user know we replaced it
    if replace_map['%RG'] and replace_map['%RG'] != 'SiCKRAGE':
        if not hasattr(episode, '_release_group'):
            sickrage.LOGGER.debug("Episode has no release group, replacing it with '" + replace_map['%RG'] + "'")
            episode._release_group = replace_map['%RG']  # if release_group is not in the db, put it there
        elif not episode._release_group:
            sickrage.LOGGER.debug("Episode has no release group, replacing it with '" + replace_map['%RG'] + "'")
            episode._release_group = replace_map['%RG']  # if release_group is not in the db, put it there

    # if there's no release name then replace it with a reasonable facsimile
    if not replace_map['%RN']:

        if show.air_by_date or show.sports:
            result_name = result_name.replace('%RN', '%S.N.%A.D.%E.N-' + replace_map['%RG'])
            result_name = result_name.replace('%rn', '%s.n.%A.D.%e.n-' + replace_map['%RG'].lower())

        elif anime_type != 3:
            result_name = result_name.replace('%RN', '%S.N.%AB.%E.N-' + replace_map['%RG'])
            result_name = result_name.replace('%rn', '%s.n.%ab.%e.n-' + replace_map['%RG'].lower())

        else:
            result_name = result_name.replace('%RN', '%S.N.S%0SE%0E.%E.N-' + replace_map['%RG'])
            result_name = result_name.replace('%rn', '%s.n.s%0se%0e.%e.n-' + replace_map['%RG'].lower())

            # sickrage.LOGGER.debug(u"Episode has no release name, replacing it with a generic one: " + result_name)

    if not replace_map['%RT']:
        result_name = re.sub('([ _.-]*)%RT([ _.-]*)', r'\2', result_name)

    # split off ep name part only
    name_groups = re.split(r'[\\/]', result_name)

    # figure out the double-ep numbering style for each group, if applicable
    for cur_name_group in name_groups:

        season_format = sep = ep_sep = ep_format = None

        season_ep_regex = r'''
                            (?P<pre_sep>[ _.-]*)
                            ((?:s(?:eason|eries)?\s*)?%0?S(?![._]?N))
                            (.*?)
                            (%0?E(?![._]?N))
                            (?P<post_sep>[ _.-]*)
                          '''
        ep_only_regex = r'(E?%0?E(?![._]?N))'

        # try the normal way
        season_ep_match = re.search(season_ep_regex, cur_name_group, re.I | re.X)
        ep_only_match = re.search(ep_only_regex, cur_name_group, re.I | re.X)

        # if we have a season and episode then collect the necessary data
        if season_ep_match:
            season_format = season_ep_match.group(2)
            ep_sep = season_ep_match.group(3)
            ep_format = season_ep_match.group(4)
            sep = season_ep_match.group('pre_sep')
            if not sep:
                sep = season_ep_match.group('post_sep')
            if not sep:
                sep = ' '

            # force 2-3-4 format if they chose to extend
            if multi in (NAMING_EXTEND, NAMING_LIMITED_EXTEND,
                         NAMING_LIMITED_EXTEND_E_PREFIXED):
                ep_sep = '-'

            regex_used = season_ep_regex

        # if there's no season then there's not much choice so we'll just force them to use 03-04-05 style
        elif ep_only_match:
            season_format = ''
            ep_sep = '-'
            ep_format = ep_only_match.group(1)
            sep = ''
            regex_used = ep_only_regex

        else:
            continue

        # we need at least this much info to continue
        if not ep_sep or not ep_format:
            continue

        # start with the ep string, eg. E03
        ep_string = _format_string(ep_format.upper(), replace_map)
        for other_ep in episode.relatedEps:

            # for limited extend we only append the last ep
            if multi in (NAMING_LIMITED_EXTEND, NAMING_LIMITED_EXTEND_E_PREFIXED) and other_ep != \
                    episode.relatedEps[
                        -1]:
                continue

            elif multi == NAMING_DUPLICATE:
                # add " - S01"
                ep_string += sep + season_format

            elif multi == NAMING_SEPARATED_REPEAT:
                ep_string += sep

            # add "E04"
            ep_string += ep_sep

            if multi == NAMING_LIMITED_EXTEND_E_PREFIXED:
                ep_string += 'E'

            ep_string += other_ep._format_string(ep_format.upper(), other_ep._replace_map())

        if anime_type != 3:
            if episode.absolute_number == 0:
                curAbsolute_number = episode
            else:
                curAbsolute_number = episode.absolute_number

            if episode.season != 0:  # dont set absolute numbers if we are on specials !
                if anime_type == 1:  # this crazy person wants both ! (note: +=)
                    ep_string += sep + "%(#)03d" % {
                        "#": curAbsolute_number}
                elif anime_type == 2:  # total anime freak only need the absolute number ! (note: =)
                    ep_string = "%(#)03d" % {"#": curAbsolute_number}

                for relEp in episode.relatedEps:
                    if relEp.absolute_number != 0:
                        ep_string += '-' + "%(#)03d" % {"#": relEp.absolute_number}
                    else:
                        ep_string += '-' + "%(#)03d" % {"#": relEp.episode}

        regex_replacement = None
        if anime_type == 2:
            regex_replacement = r'\g<pre_sep>' + ep_string + r'\g<post_sep>'
        elif season_ep_match:
            regex_replacement = r'\g<pre_sep>\g<2>\g<3>' + ep_string + r'\g<post_sep>'
        elif ep_only_match:
            regex_replacement = ep_string

        if regex_replacement:
            # fill out the template for this piece and then insert this piece into the actual pattern
            cur_name_group_result = re.sub('(?i)(?x)' + regex_used, regex_replacement, cur_name_group)
            # cur_name_group_result = cur_name_group.replace(ep_format, ep_string)
            # sickrage.LOGGER.debug(u"found "+ep_format+" as the ep pattern using "+regex_used+" and replaced it with "+regex_replacement+" to result in "+cur_name_group_result+" from "+cur_name_group)
            result_name = result_name.replace(cur_name_group, cur_name_group_result)

    result_name = _format_string(result_name, replace_map)

    sickrage.LOGGER.debug("Formatting pattern: " + pattern + " -> " + result_name)

    return result_name

def formatted_filename(show, episode, pattern=None, multi=None, anime_type=None):
    """
    Just the filename of the episode, formatted based on the naming settings
    """

    if pattern is None:
        # we only use ABD if it's enabled, this is an ABD show, AND this is not a multi-ep
        if show.air_by_date and sickrage.NAMING_CUSTOM_ABD and not episode.relatedEps:
            pattern = sickrage.NAMING_ABD_PATTERN
        elif show.sports and sickrage.NAMING_CUSTOM_SPORTS and not episode.relatedEps:
            pattern = sickrage.NAMING_SPORTS_PATTERN
        elif show.anime and sickrage.NAMING_CUSTOM_ANIME:
            pattern = sickrage.NAMING_ANIME_PATTERN
        else:
            pattern = sickrage.NAMING_PATTERN

    # split off the dirs only, if they exist
    name_groups = re.split(r'[\\/]', pattern)

    return sanitizeFileName(_format_pattern(show, episode, name_groups[-1], multi, anime_type))

def formatted_dir(show, episode, pattern=None, multi=None):
    """
    Just the folder name of the episode
    """

    if pattern is None:
        # we only use ABD if it's enabled, this is an ABD show, AND this is not a multi-ep
        if show.air_by_date and sickrage.NAMING_CUSTOM_ABD and not episode.relatedEps:
            pattern = sickrage.NAMING_ABD_PATTERN
        elif show.sports and sickrage.NAMING_CUSTOM_SPORTS and not episode.relatedEps:
            pattern = sickrage.NAMING_SPORTS_PATTERN
        elif show.anime and sickrage.NAMING_CUSTOM_ANIME:
            pattern = sickrage.NAMING_ANIME_PATTERN
        else:
            pattern = sickrage.NAMING_PATTERN

    # split off the dirs only, if they exist
    name_groups = re.split(r'[\\/]', pattern)

    if len(name_groups) == 1:
        return ''
    else:
        return _format_pattern(show, episode, os.sep.join(name_groups[:-1]), multi)