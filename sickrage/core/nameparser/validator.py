# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import os
from datetime import date

import sickrage
from sickrage.core.enums import SearchFormat, SeriesProviderID
from sickrage.core.nameparser import NameParser
from sickrage.core.common import Quality, Qualities, EpisodeStatus
from sickrage.core.tv.episode import TVEpisode

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


class FakeEpisode(object):
    def __init__(self, season, episode, absolute_number, name):
        self.name = name
        self.season = season
        self.episode = episode
        self.absolute_number = absolute_number
        self.airdate = datetime.date(2010, 3, 9)
        self.status = Quality.composite_status(EpisodeStatus.DOWNLOADED, Qualities.SDTV)
        self.release_name = 'Show.Name.S02E03.HDTV.XviD-RLSGROUP'
        self.release_group = 'RLSGROUP'
        self.is_proper = True

        self.show = FakeShow()
        self.scene_season = season
        self.scene_episode = episode
        self.scene_absolute_number = absolute_number
        self.related_episodes = []

        self.session = sickrage.app.main_db.session()

    def formatted_filename(self, *args, **kwargs):
        return TVEpisode.formatted_filename(self, *args, **kwargs)

    def _format_pattern(self, *args, **kwargs):
        return TVEpisode._format_pattern(self, *args, **kwargs)

    def _replace_map(self):
        return TVEpisode._replace_map(self)

    def _ep_name(self):
        return TVEpisode._ep_name(self)

    def _format_string(self, *args, **kwargs):
        return TVEpisode._format_string(self, *args, **kwargs)

    def formatted_dir(self, *args, **kwargs):
        return TVEpisode.formatted_dir(self, *args, **kwargs)


class FakeShow(object):
    def __init__(self):
        self.name = "Show Name"
        self.genre = "Comedy"
        self.series_id = 0o00001
        self.series_provider_id = SeriesProviderID.THETVDB
        self.search_format = SearchFormat.STANDARD
        self.startyear = 2011
        self.anime = 0


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
        pattern = sickrage.app.config.general.naming_pattern

    if anime_type is None:
        anime_type = sickrage.app.config.general.naming_anime

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
        pattern = sickrage.app.config.general.naming_pattern

    if anime_type is None:
        anime_type = sickrage.app.config.general.naming_anime

    sickrage.app.log.debug("Checking whether the pattern " + pattern + " is valid")
    return validate_name(pattern, multi, anime_type)


def check_valid_abd_naming(pattern=None):
    """
    Checks if the name is can be parsed back to its original form for an air-by-date format.

    :param pattern: formatting pattern
    :return: true if the naming is valid, false if not.
    """
    if pattern is None:
        pattern = sickrage.app.config.general.naming_pattern

    sickrage.app.log.debug("Checking whether the pattern " + pattern + " is valid for an air-by-date episode")
    valid = validate_name(pattern, abd=True)

    return valid


def check_valid_sports_naming(pattern=None):
    """
    Checks if the name is can be parsed back to its original form for an sports format.

    :param pattern: formatting pattern
    :return: true if the naming is valid, false if not.
    """
    if pattern is None:
        pattern = sickrage.app.config.general.naming_pattern

    sickrage.app.log.debug("Checking whether the pattern " + pattern + " is valid for an sports episode")
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
        sickrage.app.log.debug("Unable to create a name out of " + pattern)
        return False

    sickrage.app.log.debug("Trying to parse " + new_name)

    parser = NameParser(True, series_id=ep.show.series_id, series_provider_id=ep.show.series_provider_id, naming_pattern=True)

    try:
        result = parser.parse(new_name)
    except Exception:
        sickrage.app.log.debug("Unable to parse " + new_name + ", not valid")
        return False

    sickrage.app.log.debug("Parsed " + new_name + " into " + str(result))

    if abd or sports:
        if result.air_date != ep.airdate:
            sickrage.app.log.debug("Air date incorrect in parsed episode, pattern isn't valid")
            return False
    elif anime_type != 3:
        if len(result.ab_episode_numbers) and result.ab_episode_numbers != [x.absolute_number for x in
                                                                            [ep] + ep.related_episodes]:
            sickrage.app.log.debug("Absolute numbering incorrect in parsed episode, pattern isn't valid")
            return False
    else:
        if result.season_number != ep.season:
            sickrage.app.log.debug("Season number incorrect in parsed episode, pattern isn't valid")
            return False
        if result.episode_numbers != [x.episode for x in [ep] + ep.related_episodes]:
            sickrage.app.log.debug("Episode numbering incorrect in parsed episode, pattern isn't valid")
            return False

    return True


def generate_sample_ep(multi=None, abd=False, sports=False, anime_type=None):
    # make a fake episode object
    ep = FakeEpisode(2, 3, 3, "Ep Name")

    ep.status = Quality.composite_status(EpisodeStatus.DOWNLOADED, Qualities.HDTV)
    ep.airdate = date(2011, 3, 9)

    if abd:
        ep.release_name = 'Show.Name.2011.03.09.HDTV.XviD-RLSGROUP'
        ep.show.search_format = SearchFormat.AIR_BY_DATE
    elif sports:
        ep.release_name = 'Show.Name.2011.03.09.HDTV.XviD-RLSGROUP'
        ep.show.search_format = SearchFormat.SPORTS
    else:
        if anime_type != 3:
            ep.show.search_format = SearchFormat.ANIME
            ep.release_name = 'Show.Name.003.HDTV.XviD-RLSGROUP'
        else:
            ep.release_name = 'Show.Name.S02E03.HDTV.XviD-RLSGROUP'

    if multi is not None:
        ep.name = "Ep Name (1)"

        if anime_type != 3:
            ep.show.search_format = SearchFormat.ANIME

            ep.release_name = 'Show.Name.003-004.HDTV.XviD-RLSGROUP'

            second_ep = FakeEpisode(2, 4, 4, "Ep Name (2)")
            second_ep.status = Quality.composite_status(EpisodeStatus.DOWNLOADED, Qualities.HDTV)
            second_ep.release_name = ep.release_name

            ep.related_episodes.append(second_ep)
        else:
            ep.release_name = 'Show.Name.S02E03E04E05.HDTV.XviD-RLSGROUP'

            second_ep = FakeEpisode(2, 4, 4, "Ep Name (2)")
            second_ep.status = Quality.composite_status(EpisodeStatus.DOWNLOADED, Qualities.HDTV)
            second_ep.release_name = ep.release_name

            third_ep = FakeEpisode(2, 5, 5, "Ep Name (3)")
            third_ep.status = Quality.composite_status(EpisodeStatus.DOWNLOADED, Qualities.HDTV)
            third_ep.release_name = ep.release_name

            ep.related_episodes.append(second_ep)
            ep.related_episodes.append(third_ep)

    return ep


def test_name(pattern, multi=None, abd=False, sports=False, anime_type=None):
    ep = generate_sample_ep(multi, abd, sports, anime_type)
    return {'name': ep.formatted_filename(pattern, multi, anime_type), 'dir': ep.formatted_dir(pattern, multi)}
