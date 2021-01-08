# ##############################################################################
#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#  -
#  This file is part of SiCKRAGE.
#  -
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  -
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
# ##############################################################################


import os
import re
import time
from collections import OrderedDict
from threading import Lock

from dateutil import parser
from sqlalchemy import orm

import sickrage
from sickrage.core.common import Quality, Qualities
from sickrage.core.databases.main import MainDB
from sickrage.core.enums import SeriesProviderID
from sickrage.core.helpers import remove_extension, strip_accents
from sickrage.core.nameparser import regexes
from sickrage.core.scene_numbering import get_absolute_number_from_season_and_episode, get_series_provider_absolute_numbering, get_series_provider_numbering
from sickrage.core.tv.show.helpers import find_show_by_name, find_show, find_show_by_scene_exception
from sickrage.series_providers.helpers import search_series_provider_for_series_id


class NameParser(object):
    ALL_REGEX = 0
    NORMAL_REGEX = 1
    ANIME_REGEX = 2

    def __init__(self, file_name=True, series_id=None, series_provider_id=None, naming_pattern=False, validate_show=True):
        self.file_name = file_name
        self.show_obj = find_show(series_id, series_provider_id) if series_id and series_provider_id else None
        self.naming_pattern = naming_pattern
        self.validate_show = validate_show

        if self.show_obj and not self.show_obj.is_anime:
            self._compile_regexes(self.NORMAL_REGEX)
        elif self.show_obj and self.show_obj.is_anime:
            self._compile_regexes(self.ANIME_REGEX)
        else:
            self._compile_regexes(self.ALL_REGEX)

    def get_show(self, name):
        if not name:
            return None

        def series_provider_lookup(term):
            for _series_provider_id in SeriesProviderID:
                result = search_series_provider_for_series_id(term, _series_provider_id)
                if result:
                    return result, _series_provider_id
                return None, None

        def scene_exception_lookup(term):
            tv_show = find_show_by_scene_exception(term)
            if tv_show:
                return tv_show.series_id, tv_show.series_provider_id
            return None, None

        def show_cache_lookup(term):
            tv_show = find_show_by_name(term)
            if tv_show:
                return tv_show.series_id, tv_show.series_provider_id
            return None, None

        for lookup in [show_cache_lookup, scene_exception_lookup, series_provider_lookup]:
            for show_name in list({name, strip_accents(name), strip_accents(name).replace("'", " ")}):
                try:
                    series_id, series_provider_id = lookup(show_name)
                    if not series_id or not series_provider_id:
                        continue

                    if self.validate_show and not find_show(series_id, series_provider_id):
                        continue

                    if series_id and series_provider_id:
                        return series_id, series_provider_id
                except Exception as e:
                    sickrage.app.log.debug('SiCKRAGE encountered a error when attempting to lookup a series id by show name, Error: {!r}'.format(e))

    @staticmethod
    def clean_series_name(series_name):
        """Cleans up series name by removing any . and _
        characters, along with any trailing hyphens.

        Is basically equivalent to replacing all _ and . with a
        space, but handles decimal numbers in string, for example:
        """

        series_name = re.sub(r"(\D)\.(?!\s)(\D)", "\\1 \\2", series_name)
        series_name = re.sub(r"(\d)\.(\d{4})", "\\1 \\2", series_name)  # if it ends in a year then don't keep the dot
        series_name = re.sub(r"(\D)\.(?!\s)", "\\1 ", series_name)
        series_name = re.sub(r"\.(?!\s)(\D)", " \\1", series_name)
        series_name = series_name.replace("_", " ")
        series_name = re.sub(r"-$", "", series_name)
        series_name = re.sub(r"^\[.*\]", "", series_name)
        return series_name.strip()

    def _compile_regexes(self, regexMode):
        if regexMode == self.ANIME_REGEX:
            dbg_str = "ANIME"
            uncompiled_regex = [regexes.anime_regexes]
        elif regexMode == self.NORMAL_REGEX:
            dbg_str = "NORMAL"
            uncompiled_regex = [regexes.normal_regexes]
        else:
            dbg_str = "ALL"
            uncompiled_regex = [regexes.normal_regexes, regexes.anime_regexes]

        self.compiled_regexes = []
        for regexItem in uncompiled_regex:
            for cur_pattern_num, (cur_pattern_name, cur_pattern) in enumerate(regexItem):
                try:
                    cur_regex = re.compile(cur_pattern, re.VERBOSE | re.IGNORECASE)
                except re.error as errormsg:
                    sickrage.app.log.info(
                        "WARNING: Invalid episode_pattern using %s regexs, %s. %s" % (
                            dbg_str, errormsg, cur_pattern))
                else:
                    self.compiled_regexes.append((cur_pattern_num, cur_pattern_name, cur_regex))

    def _parse_string(self, name, skip_scene_detection=False):
        if not name:
            return

        session = sickrage.app.main_db.session()

        matches = []
        best_result = None

        for (cur_regex_num, cur_regex_name, cur_regex) in self.compiled_regexes:
            match = cur_regex.match(name)

            if not match:
                continue

            result = ParseResult(name)
            result.which_regex = {cur_regex_name}
            result.score = 0 - cur_regex_num

            named_groups = match.groupdict().keys()

            if 'series_name' in named_groups:
                result.series_name = match.group('series_name')
                if result.series_name:
                    result.series_name = self.clean_series_name(result.series_name)

            if 'season_num' in named_groups:
                tmp_season = int(match.group('season_num'))
                if cur_regex_name == 'bare' and tmp_season in (19, 20):
                    continue
                if cur_regex_name == 'fov' and tmp_season > 500:
                    continue

                result.season_number = tmp_season

            if 'ep_num' in named_groups:
                ep_num = self._convert_number(match.group('ep_num'))
                if 'extra_ep_num' in named_groups and match.group('extra_ep_num'):
                    tmp_episodes = list(range(ep_num, self._convert_number(match.group('extra_ep_num')) + 1))
                    # if len(tmp_episodes) > 6:
                    #     continue
                else:
                    tmp_episodes = [ep_num]

                result.episode_numbers = tmp_episodes

            if 'ep_ab_num' in named_groups:
                ep_ab_num = self._convert_number(match.group('ep_ab_num'))

                if 'extra_ab_ep_num' in named_groups and match.group('extra_ab_ep_num'):
                    result.ab_episode_numbers = list(range(ep_ab_num, self._convert_number(match.group('extra_ab_ep_num')) + 1))
                else:
                    result.ab_episode_numbers = [ep_ab_num]

            if 'air_date' in named_groups:
                air_date = match.group('air_date')
                try:
                    result.air_date = parser.parse(air_date, fuzzy=True).date()
                    result.score += cur_regex_num
                except Exception:
                    continue

            if 'extra_info' in named_groups:
                tmp_extra_info = match.group('extra_info')

                # Show.S04.Special or Show.S05.Part.2.Extras is almost certainly not every episode in the season
                if tmp_extra_info and cur_regex_name == 'season_only' and re.search(
                        r'([. _-]|^)(special|extra)s?\w*([. _-]|$)', tmp_extra_info, re.I):
                    continue
                result.extra_info = tmp_extra_info

            if 'release_group' in named_groups:
                result.release_group = match.group('release_group')

            if 'version' in named_groups:
                # assigns version to anime file if detected using anime regex. Non-anime regex receives -1
                version = match.group('version')
                if version:
                    result.version = version
                else:
                    result.version = 1
            else:
                result.version = -1

            result.score += len([x for x in result.__dict__ if getattr(result, x, None) is not None])
            matches.append(result)

        if len(matches):
            # pick best match with highest score based on placement
            best_result = max(sorted(matches, reverse=True, key=lambda x: x.which_regex), key=lambda x: x.score)

            show_obj = None
            best_result.series_id = self.show_obj.series_id if self.show_obj else 0
            best_result.series_provider_id = self.show_obj.series_provider_id if self.show_obj else SeriesProviderID.THETVDB

            if not self.naming_pattern:
                # try and create a show object for this result
                result = self.get_show(best_result.series_name)
                if result and len(result) == 2:
                    best_result.series_id, best_result.series_provider_id = result

                if best_result.series_id and best_result.series_provider_id:
                    show_obj = find_show(best_result.series_id, best_result.series_provider_id)

            # if this is a naming pattern test or result doesn't have a show object then return best result
            if not show_obj or self.naming_pattern:
                return best_result

            # get quality
            best_result.quality = Quality.name_quality(name, show_obj.is_anime)

            new_episode_numbers = []
            new_season_numbers = []
            new_absolute_numbers = []

            # if we have an air-by-date show then get the real season/episode numbers
            if best_result.is_air_by_date:
                try:
                    dbData = session.query(MainDB.TVEpisode).filter_by(series_id=show_obj.series_id, series_provider_id=show_obj.series_provider_id,
                                                                       airdate=best_result.air_date).one()
                    season_number = int(dbData.season)
                    episode_numbers = [int(dbData.episode)]
                except (orm.exc.NoResultFound, orm.exc.MultipleResultsFound):
                    season_number = None
                    episode_numbers = []

                if not season_number or not episode_numbers:
                    series_provider_language = show_obj.lang or sickrage.app.config.general.series_provider_default_language
                    series = show_obj.series_provider.search(show_obj.series_id, language=series_provider_language)
                    if series:
                        ep_obj = series.aired_on(best_result.air_date)
                        if not ep_obj:
                            if best_result.in_showlist:
                                sickrage.app.log.warning(f"Unable to find episode with date {best_result.air_date} for show {show_obj.name}, skipping")
                            episode_numbers = []
                        else:
                            season_number = int(ep_obj[0]["airedseason"])
                            episode_numbers = [int(ep_obj[0]["airedepisodenumber"])]

                for epNo in episode_numbers:
                    s = season_number
                    e = epNo

                    if show_obj.scene and not skip_scene_detection:
                        (s, e) = get_series_provider_numbering(show_obj.series_id,
                                                               show_obj.series_provider_id,
                                                               season_number,
                                                               epNo)
                    if s != -1:
                        new_season_numbers.append(s)

                    if e != -1:
                        new_episode_numbers.append(e)

            elif show_obj.is_anime and best_result.ab_episode_numbers:
                for epAbsNo in best_result.ab_episode_numbers:
                    a = epAbsNo

                    if show_obj.scene:
                        scene_result = show_obj.get_scene_exception_by_name(best_result.series_name)
                        if scene_result:
                            a = get_series_provider_absolute_numbering(show_obj.series_id,
                                                                       show_obj.series_provider_id, epAbsNo,
                                                                       True, scene_result[1])

                    (s, e) = show_obj.get_all_episodes_from_absolute_number([a])

                    if a != -1:
                        new_absolute_numbers.append(a)

                    new_season_numbers.append(s)
                    new_episode_numbers.extend(e)

            elif best_result.season_number and best_result.episode_numbers:
                for epNo in best_result.episode_numbers:
                    s = best_result.season_number
                    e = epNo

                    if show_obj.scene and not skip_scene_detection:
                        (s, e) = get_series_provider_numbering(show_obj.series_id,
                                                               show_obj.series_provider_id,
                                                               best_result.season_number,
                                                               epNo)
                    if show_obj.is_anime:
                        a = get_absolute_number_from_season_and_episode(show_obj.series_id, show_obj.series_provider_id, s, e)
                        if a not in [-1, None]:
                            new_absolute_numbers.append(a)

                    if s != -1:
                        new_season_numbers.append(s)

                    if e != -1:
                        new_episode_numbers.append(e)

            # need to do a quick sanity check here.  It's possible that we now have episodes
            # from more than one season (by tvdb numbering), and this is just too much
            # for sickrage, so we'd need to flag it.
            new_season_numbers = list(set(new_season_numbers))  # remove duplicates
            if len(new_season_numbers) > 1:
                raise InvalidNameException(
                    f"Scene numbering results episodes from seasons {new_season_numbers}, (i.e. more than one) and sickrage does not support this.  Sorry.")

            # I guess it's possible that we'd have duplicate episodes too, so lets
            # eliminate them
            new_episode_numbers = list(set(new_episode_numbers))
            new_episode_numbers.sort()

            # maybe even duplicate absolute numbers so why not do them as well
            new_absolute_numbers = list(set(new_absolute_numbers))
            new_absolute_numbers.sort()

            if len(new_absolute_numbers):
                best_result.ab_episode_numbers = new_absolute_numbers

            if len(new_season_numbers) and len(new_episode_numbers):
                best_result.episode_numbers = new_episode_numbers
                best_result.season_number = new_season_numbers[0]

            if show_obj.scene and not skip_scene_detection:
                sickrage.app.log.debug(f"Scene converted parsed result {best_result.original_name} into {best_result}")

        # CPU sleep
        time.sleep(0.02)

        return best_result

    def _combine_results(self, first, second, attr):
        # if the first doesn't exist then return the second or nothing
        if not first:
            if not second:
                return None
            else:
                return getattr(second, attr)

        # if the second doesn't exist then return the first
        if not second:
            return getattr(first, attr)

        a = getattr(first, attr)
        b = getattr(second, attr)

        # if a is good use it
        if a is not None or (isinstance(a, list) and a):
            return a
        # if not use b (if b isn't set it'll just be default)
        else:
            return b

    @staticmethod
    def _convert_number(org_number):
        """
         Convert org_number into an integer
         org_number: integer or representation of a number: string or unicode
         Try force converting to int first, on error try converting from Roman numerals
         returns integer or 0
         """

        try:
            # try forcing to int
            if org_number:
                number = int(org_number)
            else:
                number = 0

        except Exception:
            # on error try converting from Roman numerals
            roman_to_int_map = (
                ('M', 1000), ('CM', 900), ('D', 500), ('CD', 400), ('C', 100),
                ('XC', 90), ('L', 50), ('XL', 40), ('X', 10),
                ('IX', 9), ('V', 5), ('IV', 4), ('I', 1)
            )

            roman_numeral = org_number.upper()
            number = 0
            index = 0

            for numeral, integer in roman_to_int_map:
                while roman_numeral[index:index + len(numeral)] == numeral:
                    number += integer
                    index += len(numeral)

        return number

    def parse(self, name, cache_result=True, skip_scene_detection=False):
        if self.naming_pattern:
            cache_result = False

        cached = name_parser_cache.get(name)
        if cached:
            return cached

        # break it into parts if there are any (dirname, file name, extension)
        dir_name, file_name = os.path.split(name)

        base_file_name = file_name
        if self.file_name:
            base_file_name = remove_extension(file_name)

        # set up a result to use
        final_result = ParseResult(name)

        # try parsing the file name
        file_name_result = self._parse_string(base_file_name, skip_scene_detection)

        # use only the direct parent dir
        dir_name = os.path.basename(dir_name)

        # parse the dirname for extra info if needed
        dir_name_result = self._parse_string(dir_name, skip_scene_detection)

        # build the ParseResult object
        final_result.air_date = self._combine_results(file_name_result, dir_name_result, 'air_date')

        # anime absolute numbers
        final_result.ab_episode_numbers = self._combine_results(file_name_result, dir_name_result, 'ab_episode_numbers')

        # season and episode numbers
        final_result.season_number = self._combine_results(file_name_result, dir_name_result, 'season_number')
        final_result.episode_numbers = self._combine_results(file_name_result, dir_name_result, 'episode_numbers')

        # if the dirname has a release group/show name I believe it over the filename
        final_result.series_name = self._combine_results(dir_name_result, file_name_result, 'series_name')

        final_result.extra_info = self._combine_results(dir_name_result, file_name_result, 'extra_info')
        final_result.release_group = self._combine_results(dir_name_result, file_name_result, 'release_group')
        final_result.version = self._combine_results(dir_name_result, file_name_result, 'version')

        if final_result == file_name_result:
            final_result.which_regex = file_name_result.which_regex
        elif final_result == dir_name_result:
            final_result.which_regex = dir_name_result.which_regex
        else:
            if file_name_result:
                final_result.which_regex |= file_name_result.which_regex
            if dir_name_result:
                final_result.which_regex |= dir_name_result.which_regex

        final_result.series_id = self._combine_results(file_name_result, dir_name_result, 'series_id')
        final_result.series_provider_id = self._combine_results(file_name_result, dir_name_result, 'series_provider_id')
        final_result.quality = self._combine_results(file_name_result, dir_name_result, 'quality')

        if self.validate_show:
            if not self.naming_pattern and (not final_result.series_id or not final_result.series_provider_id):
                raise InvalidShowException("Unable to match {} to a show in your database. Parser result: {}".format(name, final_result))

        # if there's no useful info in it then raise an exception
        if final_result.season_number is None and not final_result.episode_numbers and final_result.air_date is None and not final_result.ab_episode_numbers and not final_result.series_name:
            raise InvalidNameException("Unable to parse {} to a valid episode. Parser result: {}".format(name, final_result))

        if cache_result and final_result.series_id and final_result.series_provider_id:
            name_parser_cache.add(name, final_result)

        sickrage.app.log.debug("Parsed {} into {}".format(name, final_result))
        return final_result


class ParseResult(object):
    def __init__(self,
                 original_name,
                 series_name=None,
                 season_number=None,
                 episode_numbers=None,
                 extra_info=None,
                 release_group=None,
                 air_date=None,
                 ab_episode_numbers=None,
                 series_id=None,
                 series_provider_id=None,
                 score=None,
                 quality=None,
                 version=None
                 ):

        self.original_name = original_name
        self.series_name = series_name
        self.season_number = season_number
        self.episode_numbers = episode_numbers or []
        self.ab_episode_numbers = ab_episode_numbers or []
        self.quality = quality or Qualities.UNKNOWN
        self.extra_info = extra_info
        self.release_group = release_group
        self.air_date = air_date
        self.series_id = series_id or 0
        self.series_provider_id = series_provider_id or SeriesProviderID.THETVDB
        self.score = score
        self.version = version
        self.which_regex = set()

    def __eq__(self, other):
        return other and all([
            self.__class__ == other.__class__,
            self.series_name == other.series_name,
            self.season_number == other.season_number,
            self.episode_numbers == other.episode_numbers,
            self.extra_info == other.extra_info,
            self.release_group == other.release_group,
            self.air_date == other.air_date,
            self.ab_episode_numbers == other.ab_episode_numbers,
            self.score == other.score,
            self.quality == other.quality,
            self.version == other.version
        ])

    def __str__(self):
        to_return = ""
        if self.series_name is not None:
            to_return += 'SHOW:[{}]'.format(self.series_name)
        if self.season_number is not None:
            to_return += ' SEASON:[{}]'.format(str(self.season_number).zfill(2))
        if self.episode_numbers and len(self.episode_numbers):
            to_return += ' EPISODE:[{}]'.format(','.join(str(x).zfill(2) for x in self.episode_numbers))
        if self.is_air_by_date:
            to_return += ' AIRDATE:[{}]'.format(self.air_date)
        if self.ab_episode_numbers:
            to_return += ' ABS:[{}]'.format(','.join(str(x).zfill(3) for x in self.ab_episode_numbers))
        if self.version and self.is_anime is True:
            to_return += ' ANIME VER:[{}]'.format(self.version)
        if self.release_group:
            to_return += ' GROUP:[{}]'.format(self.release_group)

        to_return += ' ABD:[{}]'.format(self.is_air_by_date)
        to_return += ' ANIME:[{}]'.format(self.is_anime)
        to_return += ' REGEX:[{}]'.format(' '.join(self.which_regex))

        return to_return

    @property
    def is_air_by_date(self):
        if self.air_date:
            return True
        return False

    @property
    def is_anime(self):
        if self.ab_episode_numbers:
            return True
        return False

    @property
    def in_showlist(self):
        if find_show(self.series_id, self.series_provider_id):
            return True
        return False


class NameParserCache(object):
    def __init__(self):
        self.lock = Lock()
        self.data = OrderedDict()
        self.max_size = 200

    def get(self, key):
        with self.lock:
            value = self.data.get(key)
            if value:
                sickrage.app.log.debug("Using cached parse result for: {}".format(key))
            return value

    def add(self, key, value):
        with self.lock:
            self.data.update({key: value})
            while len(self.data) > self.max_size:
                self.data.pop(list(self.data.keys())[0], None)


name_parser_cache = NameParserCache()


class InvalidNameException(Exception):
    """The given release name is not valid"""


class InvalidShowException(Exception):
    """The given show name is not valid"""
