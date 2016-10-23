# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import os
from datetime import date

import sickrage
from sickrage.core.common import DOWNLOADED, Quality
from sickrage.core.nameparser import NameParser
from sickrage.core.nameparser.episode import Episode

name_presets = (
    '%SN - %Sx%0E - %EN',
    '%S.N.S%0SE%0E.%E.N',
    '%Sx%0E - %EN',
    'S%0SE%0E - %EN',
    'Season %0S/%S.N.S%0SE%0E.%Q.N-%RG'
)

name_anime_presets = name_presets

name_abd_presets = (
    '%SN - %A-D - %EN',
    '%S.N.%A.D.%E.N.%Q.N',
    '%Y/%0M/%S.N.%A.D.%E.N-%RG'
)

name_sports_presets = (
    '%SN - %A-D - %EN',
    '%S.N.%A.D.%E.N.%Q.N',
    '%Y/%0M/%S.N.%A.D.%E.N-%RG'
)


def check_force_season_folders(pattern=None, multi=None, anime_type=None):
    """
    Checks if the name can still be parsed if you strip off the folders to determine if we need to force season folders
    to be enabled or not.

    :param pattern: formatting pattern
    :param multi: multi-episode
    :param anime_type: anime type
    :return: true if season folders need to be forced on or false otherwise.
    """
    if pattern is None:
        pattern = sickrage.srCore.srConfig.NAMING_PATTERN

    if anime_type is None:
        anime_type = sickrage.srCore.srConfig.NAMING_ANIME

    return not validate_name(pattern, multi, anime_type, file_only=True)


def check_valid_naming(pattern=None, multi=None, anime_type=None):
    """
    Checks if the name is can be parsed back to its original form for both single and multi episodes.

    :param pattern: formatting pattern
    :param multi: multi-episode
    :param anime_type: anime type
    :return: true if the naming is valid, false if not.
    """
    if pattern is None:
        pattern = sickrage.srCore.srConfig.NAMING_PATTERN

    if anime_type is None:
        anime_type = sickrage.srCore.srConfig.NAMING_ANIME

    sickrage.srCore.srLogger.debug("Checking whether the pattern " + pattern + " is valid")
    return validate_name(pattern, multi, anime_type)


def check_valid_abd_naming(pattern=None):
    """
    Checks if the name is can be parsed back to its original form for an air-by-date format.

    :param pattern: formatting pattern
    :return: true if the naming is valid, false if not.
    """
    if pattern is None:
        pattern = sickrage.srCore.srConfig.NAMING_PATTERN

    sickrage.srCore.srLogger.debug("Checking whether the pattern " + pattern + " is valid for an air-by-date episode")
    valid = validate_name(pattern, abd=True)

    return valid


def check_valid_sports_naming(pattern=None):
    """
    Checks if the name is can be parsed back to its original form for an sports format.

    :param pattern: formatting pattern
    :return: true if the naming is valid, false if not.
    """
    if pattern is None:
        pattern = sickrage.srCore.srConfig.NAMING_PATTERN

    sickrage.srCore.srLogger.debug("Checking whether the pattern " + pattern + " is valid for an sports episode")
    valid = validate_name(pattern, sports=True)

    return valid


def validate_name(pattern, multi=None, anime_type=None, file_only=False, abd=False, sports=False):
    """
    See if we understand a name

    :param pattern: Name to analyse
    :param multi: Is this a multi-episode name
    :param anime_type: Is this anime
    :param file_only: Is this just a file or a dir
    :param abd: Is air-by-date enabled
    :param sports: Is this sports
    :return: True if valid name, False if not
    """
    ep = generate_sample_ep(multi, abd, sports, anime_type)

    new_name = ep.formatted_filename(pattern, multi, anime_type) + '.ext'
    new_path = ep.formatted_dir(pattern, multi)
    if not file_only:
        new_name = os.path.join(new_path, new_name)

    if not new_name:
        sickrage.srCore.srLogger.debug("Unable to create a name out of " + pattern)
        return False

    sickrage.srCore.srLogger.debug("Trying to parse " + new_name)

    parser = NameParser(True, showObj=ep.show, naming_pattern=True)

    try:
        result = parser.parse(new_name)
    except Exception:
        sickrage.srCore.srLogger.debug("Unable to parse " + new_name + ", not valid")
        return False

    sickrage.srCore.srLogger.debug("Parsed " + new_name + " into " + str(result))

    if abd or sports:
        if result.air_date != ep.airdate:
            sickrage.srCore.srLogger.debug("Air date incorrect in parsed episode, pattern isn't valid")
            return False
    elif anime_type != 3:
        if len(result.ab_episode_numbers) and result.ab_episode_numbers != [x.absolute_number for x in
                                                                            [ep] + ep.relatedEps]:
            sickrage.srCore.srLogger.debug("Absolute numbering incorrect in parsed episode, pattern isn't valid")
            return False
    else:
        if result.season_number != ep.season:
            sickrage.srCore.srLogger.debug("Season number incorrect in parsed episode, pattern isn't valid")
            return False
        if result.episode_numbers != [x.episode for x in [ep] + ep.relatedEps]:
            sickrage.srCore.srLogger.debug("Episode numbering incorrect in parsed episode, pattern isn't valid")
            return False

    return True


def generate_sample_ep(multi=None, abd=False, sports=False, anime_type=None):
    # make a fake episode object
    ep = Episode(2, 3, 3, "Ep Name")

    ep._status = Quality.compositeStatus(DOWNLOADED, Quality.HDTV)
    ep._airdate = date(2011, 3, 9)

    if abd:
        ep._release_name = 'Show.Name.2011.03.09.HDTV.XviD-RLSGROUP'
        ep.show.air_by_date = 1
    elif sports:
        ep._release_name = 'Show.Name.2011.03.09.HDTV.XviD-RLSGROUP'
        ep.show.sports = 1
    else:
        if anime_type != 3:
            ep.show.anime = 1
            ep._release_name = 'Show.Name.003.HDTV.XviD-RLSGROUP'
        else:
            ep._release_name = 'Show.Name.S02E03.HDTV.XviD-RLSGROUP'

    if multi is not None:
        ep._name = "Ep Name (1)"

        if anime_type != 3:
            ep.show.anime = 1

            ep._release_name = 'Show.Name.003-004.HDTV.XviD-RLSGROUP'

            second_ep = Episode(2, 4, 4, "Ep Name (2)")
            second_ep._status = Quality.compositeStatus(DOWNLOADED, Quality.HDTV)
            second_ep._release_name = ep.release_name

            ep.relatedEps.append(second_ep)
        else:
            ep._release_name = 'Show.Name.S02E03E04E05.HDTV.XviD-RLSGROUP'

            second_ep = Episode(2, 4, 4, "Ep Name (2)")
            second_ep._status = Quality.compositeStatus(DOWNLOADED, Quality.HDTV)
            second_ep._release_name = ep.release_name

            third_ep = Episode(2, 5, 5, "Ep Name (3)")
            third_ep._status = Quality.compositeStatus(DOWNLOADED, Quality.HDTV)
            third_ep._release_name = ep.release_name

            ep.relatedEps.append(second_ep)
            ep.relatedEps.append(third_ep)

    return ep


def test_name(pattern, multi=None, abd=False, sports=False, anime_type=None):
    ep = generate_sample_ep(multi, abd, sports, anime_type)
    return {'name': ep.formatted_filename(pattern, multi, anime_type), 'dir': ep.formatted_dir(pattern, multi)}
