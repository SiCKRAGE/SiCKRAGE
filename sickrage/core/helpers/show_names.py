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


import datetime
import fnmatch
import os
import re
from functools import partial

import sickrage
from sickrage.core.common import EpisodeStatus, countryList
from sickrage.core.enums import SearchFormat
from sickrage.core.helpers import sanitize_scene_name, strip_accents
from sickrage.core.tv.show.helpers import find_show

resultFilters = [
    "sub(bed|ed|pack|s)",
    "(dir|sub|nfo)fix",
    "(?<!shomin.)sample",
    "(dvd)?extras",
    "dub(bed)?"
]

if hasattr('General', 'ignored_subs_list') and sickrage.app.config.general.ignored_subs_list:
    resultFilters.append("(" + sickrage.app.config.general.ignored_subs_list.replace(",", "|") + ")sub(bed|ed|s)?")


def contains_at_least_one_word(name, words):
    """
    Filters out results based on filter_words

    name: name to check
    words : string of words separated by a ',' or list of words

    Returns: False if the name doesn't contain any word of words list, or the found word from the list.
    :return:
    :param name:
    :param words:
    :return:
    :rtype: unicode
    """
    if isinstance(words, str):
        words = words.split(',')
    items = [(re.compile('(^|[\W_])%s($|[\W_])' % re.escape(word.strip()), re.I), word.strip()) for word in words]
    for regexp, word in items:
        if regexp.search(name):
            return word
    return False


def filter_bad_releases(name, parse=True):
    """
    Filters out non-english and just all-around stupid releases by comparing them
    to the resultFilters contents.

    name: the release name to check

    Returns: True if the release name is OK, False if it's bad.
    :return:
    :param name:
    :param parse:
    :return:
    """

    from sickrage.core.nameparser import InvalidNameException, InvalidShowException, NameParser

    try:
        if parse:
            NameParser().parse(name)
    except InvalidNameException as e:
        sickrage.app.log.debug("{}".format(e))
        return False
    except InvalidShowException:
        pass

    # if any of the bad strings are in the name then say no
    ignore_words = list(resultFilters)
    if sickrage.app.config.general.ignore_words:
        ignore_words.extend(sickrage.app.config.general.ignore_words.split(','))

    word = contains_at_least_one_word(name, ignore_words)
    if word:
        sickrage.app.log.debug("Release: " + name + " contains " + word + ", ignoring it")
        return False

    # if any of the good strings aren't in the name then say no
    if sickrage.app.config.general.require_words:
        require_words = sickrage.app.config.general.require_words
        if not contains_at_least_one_word(name, require_words):
            sickrage.app.log.debug("Release: " + name + " doesn't contain any of " +
                                   ', '.join(set(require_words)) + ", ignoring it")
            return False

    return True


def scene_to_normal_show_names(name):
    """
        Takes a show name from a scene dirname and converts it to a more "human-readable" format.

    name: The show name to convert

    Returns: a list of all the possible "normal" names
    :return:
    :param name:
    """

    if not name:
        return []

    name_list = [name]

    # use both and and &
    new_name = re.sub(r'(?i)([\. ])and([\. ])', '\\1&\\2', name, re.I)
    if new_name not in name_list:
        name_list.append(new_name)

    results = []

    for cur_name in name_list:
        # add brackets around the year
        results.append(re.sub(r'(\D)(\d{4})$', '\\1(\\2)', cur_name))

        # add brackets around the country
        country_match_str = '|'.join(countryList.values())
        results.append(re.sub(r'(?i)([. _-])(' + country_match_str + ')$', '\\1(\\2)', cur_name))

    results += name_list

    return list(set(results))


def all_possible_show_names(series_id, series_provider_id, season=-1):
    """
    Figures out every possible variation of the name for a particular show. Includes TVDB name, TVRage name,
    country codes on the end, eg. "Show Name (AU)", and any scene exception names.

    show: a TVShow object that we should get the names of

    Returns: a list of all the possible show names
    :rtype: list[unicode]
    """

    show = find_show(series_id, series_provider_id)

    show_names = show.get_scene_exceptions_by_season(season=season)[:]
    if not show_names:  # if we dont have any season specific exceptions fallback to generic exceptions
        season = -1
        show_names = show.get_scene_exceptions_by_season(season=season)[:]

    if season in [-1, 1]:
        show_names.append(show.name)

    show_names.append(strip_accents(show.name))
    show_names.append(strip_accents(show.name).replace("'", " "))

    if not show.is_anime:
        new_show_names = []
        country_list = countryList
        country_list.update(dict(zip(countryList.values(), countryList.keys())))
        for curName in set(show_names):
            if not curName:
                continue

            # if we have "Show Name Australia" or "Show Name (Australia)" this will add "Show Name (AU)" for
            # any countries defined in common.countryList
            # (and vice versa)
            for curCountry in country_list:
                if curName.endswith(' ' + curCountry):
                    new_show_names.append(curName.replace(' ' + curCountry, ' (' + country_list[curCountry] + ')'))
                elif curName.endswith(' (' + curCountry + ')'):
                    new_show_names.append(curName.replace(' (' + curCountry + ')', ' (' + country_list[curCountry] + ')'))

            # if we have "Show Name (2013)" this will strip the (2013) show year from the show name
            new_show_names.append(re.sub(r'\({}\)'.format(show.startyear), '', curName))

        show_names += new_show_names

    return list(set(show_names))


def determine_release_name(dir_name=None, nzb_name=None):
    """Determine a release name from an nzb and/or folder name
    :param dir_name:
    :param nzb_name:
    :return:
    """

    if nzb_name is not None:
        sickrage.app.log.info("Using nzb_name for release name.")
        return nzb_name.rpartition('.')[0]

    if dir_name is None:
        return None

    # try to get the release name from nzb/nfo
    file_types = ["*.nzb", "*.nfo"]

    for search in file_types:
        reg_expr = re.compile(fnmatch.translate(search), re.IGNORECASE)
        files = [file_name for file_name in os.listdir(dir_name) if
                 os.path.isfile(os.path.join(dir_name, file_name))]

        results = list(filter(reg_expr.search, files))
        if len(results) == 1:
            found_file = os.path.basename(results[0])
            found_file = found_file.rpartition('.')[0]
            if filter_bad_releases(found_file):
                sickrage.app.log.info("Release name ({}) found from file ({})".format(found_file, results[0]))
                return found_file.rpartition('.')[0]

    # If that fails, we try the folder
    folder = os.path.basename(dir_name)
    if filter_bad_releases(folder):
        # NOTE: Multiple failed downloads will change the folder name.
        # (e.g., appending #s)
        # Should we handle that?
        sickrage.app.log.debug("Folder name (" + folder + ") appears to be a valid release name. Using it.")
        return folder

    return None
