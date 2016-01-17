# Author: echel0n <sickrage.tv@gmail.com>
# URL: https://sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
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

import datetime
import os

import sickrage
from sickrage.core.common import DOWNLOADED, Quality
from sickrage.core.nameparser import NameParser
from sickrage.core.tv import formatted_filename, formatted_dir

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


class Validator(object):
    class FakeTVShow(object):
        def __init__(self):
            self.name = "Show Name"
            self.genre = "Comedy"
            self.indexerid = 00001
            self.air_by_date = 0
            self.sports = 0
            self.anime = 0
            self.scene = 0

        def _is_anime(self):
            """
            Find out if show is anime
            :return: True if show is anime, False if not
            """
            if self.anime > 0:
                return True
            else:
                return False

        is_anime = property(_is_anime)

        def _is_sports(self):
            """
            Find out if show is sports
            :return: True if show is sports, False if not
            """
            if self.sports > 0:
                return True
            else:
                return False

        is_sports = property(_is_sports)

        def _is_scene(self):
            """
            Find out if show is scene numbering
            :return: True if show is scene numbering, False if not
            """
            if self.scene > 0:
                return True
            else:
                return False

        is_scene = property(_is_scene)

    class FakeTVEpisode(object):
        def __init__(self, season, episode, absolute_number, name):
            self.relatedEps = []
            self.name = name
            self.season = season
            self.episode = episode
            self.absolute_number = absolute_number
            self.scene_season = season
            self.scene_episode = episode
            self.scene_absolute_number = absolute_number
            self.airdate = datetime.date(2010, 3, 9)
            self.show = Validator.FakeTVShow()
            self.status = Quality.compositeStatus(DOWNLOADED, Quality.SDTV)
            self.release_name = 'Show.Name.S02E03.HDTV.XviD-RLSGROUP'
            self.is_proper = True


def check_force_season_folders(pattern=None, multi=None, anime_type=None):
    """
    Checks if the name can still be parsed if you strip off the folders to determine if we need to force season folders
    to be enabled or not.

    :return: true if season folders need to be forced on or false otherwise.
    """
    if pattern is None:
        pattern = sickrage.NAMING_PATTERN

    if anime_type is None:
        anime_type = sickrage.NAMING_ANIME

    valid = not validate_name(pattern=pattern, anime_type=anime_type, file_only=True)

    if multi is not None:
        valid = valid or not validate_name(pattern, multi, anime_type, file_only=True)

    return valid


def check_valid_naming(pattern=None, multi=None, anime_type=None):
    """
    Checks if the name is can be parsed back to its original form for both single and multi episodes.

    :return: true if the naming is valid, false if not.
    """
    if pattern is None:
        pattern = sickrage.NAMING_PATTERN

    if anime_type is None:
        anime_type = sickrage.NAMING_ANIME

    sickrage.LOGGER.debug("Checking whether the pattern " + pattern + " is valid for a single episode")
    valid = validate_name(pattern=pattern, anime_type=anime_type)

    if multi is not None:
        sickrage.LOGGER.debug("Checking whether the pattern " + pattern + " is valid for a multi episode")
        valid = valid and validate_name(pattern, multi, anime_type)

    return valid


def check_valid_abd_naming(pattern=None):
    """
    Checks if the name is can be parsed back to its original form for an air-by-date format.

    :return: true if the naming is valid, false if not.
    """
    if pattern is None:
        pattern = sickrage.NAMING_PATTERN

    sickrage.LOGGER.debug("Checking whether the pattern " + pattern + " is valid for an air-by-date episode")
    valid = validate_name(pattern, abd=True)

    return valid


def check_valid_sports_naming(pattern=None):
    """
    Checks if the name is can be parsed back to its original form for an sports format.

    :return: true if the naming is valid, false if not.
    """
    if pattern is None:
        pattern = sickrage.NAMING_PATTERN

    sickrage.LOGGER.debug("Checking whether the pattern " + pattern + " is valid for an sports episode")
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

    new_name = formatted_filename(ep.show, ep, pattern, multi, anime_type) + '.ext'
    new_path = formatted_dir(ep.show, ep, pattern, multi)
    if not file_only:
        new_name = os.path.join(new_path, new_name)

    if not new_name:
        sickrage.LOGGER.debug("Unable to create a name out of " + pattern)
        return False

    sickrage.LOGGER.debug("Trying to parse " + new_name)

    parser = NameParser(True, showObj=ep.show, naming_pattern=True)

    try:
        result = parser.parse(new_name)
    except Exception:
        sickrage.LOGGER.debug("Unable to parse " + new_name + ", not valid")
        return False

    sickrage.LOGGER.debug("Parsed " + new_name + " into " + str(result))

    if abd or sports:
        if result.air_date != ep.airdate:
            sickrage.LOGGER.debug("Air date incorrect in parsed episode, pattern isn't valid")
            return False
    elif anime_type != 3:
        if len(result.ab_episode_numbers) and result.ab_episode_numbers != [x.absolute_number for x in
                                                                            [ep] + ep.relatedEps]:
            sickrage.LOGGER.debug("Absolute numbering incorrect in parsed episode, pattern isn't valid")
            return False
    else:
        if result.season_number != ep.season:
            sickrage.LOGGER.debug("Season number incorrect in parsed episode, pattern isn't valid")
            return False
        if result.episode_numbers != [x.episode for x in [ep] + ep.relatedEps]:
            sickrage.LOGGER.debug("Episode numbering incorrect in parsed episode, pattern isn't valid")
            return False

    return True


def generate_sample_ep(multi=None, abd=False, sports=False, anime_type=None):
    # make a fake episode object
    ep = Validator.FakeTVEpisode(2, 3, 3, "Ep Name")

    ep.status = Quality.compositeStatus(DOWNLOADED, Quality.HDTV)
    ep.airdate = datetime.date(2011, 3, 9)

    if abd:
        ep.release_name = 'Show.Name.2011.03.09.HDTV.XviD-RLSGROUP'
        ep.show.air_by_date = 1
    elif sports:
        ep.release_name = 'Show.Name.2011.03.09.HDTV.XviD-RLSGROUP'
        ep.show.sports = 1
    else:
        if anime_type != 3:
            ep.show.anime = 1
            ep.release_name = 'Show.Name.003.HDTV.XviD-RLSGROUP'
        else:
            ep.release_name = 'Show.Name.S02E03.HDTV.XviD-RLSGROUP'

    if multi is not None:
        ep.name = "Ep Name (1)"

        if anime_type != 3:
            ep.show.anime = 1

            ep.release_name = 'Show.Name.003-004.HDTV.XviD-RLSGROUP'

            secondEp = Validator.FakeTVEpisode(2, 4, 4, "Ep Name (2)")
            secondEp.status = Quality.compositeStatus(DOWNLOADED, Quality.HDTV)
            secondEp.release_name = ep.release_name

            ep.relatedEps.append(secondEp)
        else:
            ep.release_name = 'Show.Name.S02E03E04E05.HDTV.XviD-RLSGROUP'

            secondEp = Validator.FakeTVEpisode(2, 4, 4, "Ep Name (2)")
            secondEp.status = Quality.compositeStatus(DOWNLOADED, Quality.HDTV)
            secondEp.release_name = ep.release_name

            thirdEp = Validator.FakeTVEpisode(2, 5, 5, "Ep Name (3)")
            thirdEp.status = Quality.compositeStatus(DOWNLOADED, Quality.HDTV)
            thirdEp.release_name = ep.release_name

            ep.relatedEps.append(secondEp)
            ep.relatedEps.append(thirdEp)

    return ep


def test_name(pattern, multi=None, abd=False, sports=False, anime_type=None):
    ep = generate_sample_ep(multi, abd, sports, anime_type)

    return {'name': formatted_filename(ep.show, ep, pattern, multi, anime_type), 'dir': formatted_dir(ep.show, ep, pattern, multi)}
