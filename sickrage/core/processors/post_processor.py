# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
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

import fnmatch
import glob
import os
import re
import stat
import subprocess

import sickrage
from sickrage.core.common import Quality, ARCHIVED, DOWNLOADED
from sickrage.core.exceptions import EpisodeNotFoundException, EpisodePostProcessingFailedException
from sickrage.core.helpers import findCertainShow, show_names, fixGlob, subtitleExtensions, replaceExtension, makeDir, \
    chmodAsParent, moveFile, copyFile, hardlinkFile, moveAndSymlinkFile, remove_non_release_groups, remove_extension, \
    isFileLocked, verify_freespace, delete_empty_folders, make_dirs
from sickrage.core.nameparser import InvalidNameException, InvalidShowException, \
    NameParser
from sickrage.core.searchers.subtitle_searcher import wantedLanguages
from sickrage.core.tv.show.history import FailedHistory, History
from sickrage.indexers.adba import aniDBAbstracter
from sickrage.notifiers import srNotifiers


class PostProcessor(object):
    """
    A class which will process a media file according to the post processing settings in the config.
    """

    EXISTS_LARGER = 1
    EXISTS_SAME = 2
    EXISTS_SMALLER = 3
    DOESNT_EXIST = 4

    IGNORED_FILESTRINGS = [".AppleDouble", ".DS_Store"]

    def __init__(self, file_path, nzb_name=None, process_method=None, is_priority=None):
        """
        Creates a new post processor with the given file path and optionally an NZB name.

        file_path: The path to the file to be processed
        nzb_name: The name of the NZB which resulted in this file being downloaded (optional)
        """
        # absolute path to the folder that is being processed
        self.folder_path = os.path.dirname(os.path.abspath(file_path))

        # full path to file
        self.file_path = file_path

        # file name only
        self.file_name = os.path.basename(file_path)

        # the name of the folder only
        self.folder_name = os.path.basename(self.folder_path)

        # name of the NZB that resulted in this folder
        self.nzb_name = nzb_name

        self.process_method = process_method if process_method else sickrage.srCore.srConfig.PROCESS_METHOD

        self.in_history = False

        self.release_group = None

        self.release_name = None

        self.is_proper = False

        self.is_priority = is_priority

        self.log = ''

        self.version = None

        self.anidbEpisode = None

    def _log(self, message, level=None):
        """
        A wrapper for the internal logger which also keeps track of messages and saves them to a string for later.

        :param message: The string to log (unicode)
        :param level: The log level to use (optional)
        """
        sickrage.srCore.srLogger.log(level or sickrage.srCore.srLogger.INFO, message)
        self.log += message + '\n'

    def _checkForExistingFile(self, existing_file):
        """
        Checks if a file exists already and if it does whether it's bigger or smaller than
        the file we are post processing

        ;param existing_file: The file to compare to

        :return:
            DOESNT_EXIST if the file doesn't exist
            EXISTS_LARGER if the file exists and is larger than the file we are post processing
            EXISTS_SMALLER if the file exists and is smaller than the file we are post processing
            EXISTS_SAME if the file exists and is the same size as the file we are post processing
        """

        if not existing_file:
            self._log("There is no existing file so there's no worries about replacing it",
                      sickrage.srCore.srLogger.DEBUG)
            return PostProcessor.DOESNT_EXIST

        # if the new file exists, return the appropriate code depending on the size
        if os.path.isfile(existing_file):

            # see if it's bigger than our old file
            if os.path.getsize(existing_file) > os.path.getsize(self.file_path):
                self._log("File " + existing_file + " is larger than " + self.file_path, sickrage.srCore.srLogger.DEBUG)
                return PostProcessor.EXISTS_LARGER

            elif os.path.getsize(existing_file) == os.path.getsize(self.file_path):
                self._log("File " + existing_file + " is the same size as " + self.file_path,
                          sickrage.srCore.srLogger.DEBUG)
                return PostProcessor.EXISTS_SAME

            else:
                self._log("File " + existing_file + " is smaller than " + self.file_path,
                          sickrage.srCore.srLogger.DEBUG)
                return PostProcessor.EXISTS_SMALLER

        else:
            self._log("File " + existing_file + " doesn't exist so there's no worries about replacing it",
                      sickrage.srCore.srLogger.DEBUG)
            return PostProcessor.DOESNT_EXIST

    def list_associated_files(self, file_path, base_name_only=False, subtitles_only=False, subfolders=False):
        """
        For a given file path searches for files with the same name but different extension and returns their absolute paths

        :param subfolders:
        :param subtitles_only:
        :param file_path: The file to check for associated files

        :param base_name_only: False add extra '.' (conservative search) to file_path minus extension

        :return: A list containing all files which are associated to the given file
        """

        def recursive_glob(treeroot, pattern):
            results = []
            for base, _, files in os.walk(treeroot):
                goodfiles = fnmatch.filter(files, pattern)
                results.extend(os.path.join(base, f) for f in goodfiles)
            return results

        if not file_path:
            return []

        # don't confuse glob with chars we didn't mean to use
        globbable_file_path = fixGlob(file_path)

        file_path_list = []

        if subfolders:
            base_name = os.path.basename(globbable_file_path).rpartition('.')[0]
        else:
            base_name = globbable_file_path.rpartition('.')[0]

        if not base_name_only:
            base_name += '.'

        # don't strip it all and use cwd by accident
        if not base_name:
            return []

        if subfolders:  # subfolders are only checked in show folder, so names will always be exactly alike
            filelist = recursive_glob(os.path.dirname(globbable_file_path),
                                      base_name + '*')  # just create the list of all files starting with the basename
        else:  # this is called when PP, so we need to do the filename check case-insensitive
            filelist = []

            checklist = glob.glob(os.path.join(os.path.dirname(globbable_file_path),
                                               '*'))  # get a list of all the files in the folder
            for filefound in checklist:  # loop through all the files in the folder, and check if they are the same name even when the cases don't match
                file_name = filefound.rpartition('.')[0]
                if not base_name_only:
                    file_name += '.'
                if file_name.lower() == base_name.lower().replace('[[]', '[').replace('[]]',
                                                                                      ']'):  # if there's no difference in the filename add it to the filelist
                    filelist.append(filefound)

        for associated_file_path in filelist:
            # only add associated to list
            if associated_file_path == file_path:
                continue
            # only list it if the only non-shared part is the extension or if it is a subtitle
            if subtitles_only and not associated_file_path[len(associated_file_path) - 3:] in subtitleExtensions:
                continue

            # Exclude .rar files from associated list
            if re.search(r'(^.+\.(rar|r\d+)$)', associated_file_path):
                continue

            if os.path.isfile(associated_file_path):
                file_path_list.append(associated_file_path)

        if file_path_list:
            self._log("Found the following associated files: " + str(file_path_list), sickrage.srCore.srLogger.DEBUG)
        else:
            self._log("No associated files were during this pass", sickrage.srCore.srLogger.DEBUG)

        return file_path_list

    def _delete(self, file_path, associated_files=False):
        """
        Deletes the file and optionally all associated files.

        :param file_path: The file to delete
        :param associated_files: True to delete all files which differ only by extension, False to leave them
        """

        if not file_path:
            return

        # figure out which files we want to delete
        file_list = [file_path]
        if associated_files:
            file_list = file_list + self.list_associated_files(file_path, base_name_only=True, subfolders=True)

        if not file_list:
            self._log("There were no files associated with " + file_path + ", not deleting anything",
                      sickrage.srCore.srLogger.DEBUG)
            return

        # delete the file and any other files which we want to delete
        for cur_file in file_list:
            if os.path.isfile(cur_file):
                self._log("Deleting file " + cur_file, sickrage.srCore.srLogger.DEBUG)
                # check first the read-only attribute
                file_attribute = os.stat(cur_file)[0]
                if not file_attribute & stat.S_IWRITE:
                    # File is read-only, so make it writeable
                    self._log('Read only mode on file ' + cur_file + ' Will try to make it writeable',
                              sickrage.srCore.srLogger.DEBUG)
                    try:
                        os.chmod(cur_file, stat.S_IWRITE)
                    except:
                        self._log('Cannot change permissions of ' + cur_file, sickrage.srCore.srLogger.WARNING)

                os.remove(cur_file)

                # do the library update for synoindex
                sickrage.srCore.notifiersDict.synoindex_notifier.deleteFile(cur_file)

    def _combined_file_operation(self, file_path, new_path, new_base_name, associated_files=False, action=None,
                                 subs=False):
        """
        Performs a generic operation (move or copy) on a file. Can rename the file as well as change its location,
        and optionally move associated files too.

        :param file_path: The full path of the media file to act on
        :param new_path: Destination path where we want to move/copy the file to
        :param new_base_name: The base filename (no extension) to use during the copy. Use None to keep the same name.
        :param associated_files: Boolean, whether we should copy similarly-named files too
        :param action: function that takes an old path and new path and does an operation with them (move/copy)
        :param subs: Boolean, whether we should process subtitles too
        """

        if not action:
            self._log("Must provide an action for the combined file operation", sickrage.srCore.srLogger.ERROR)
            return

        file_list = [file_path]
        if associated_files:
            file_list = file_list + self.list_associated_files(file_path)
        elif subs:
            file_list = file_list + self.list_associated_files(file_path, subtitles_only=True)

        if not file_list:
            self._log("There were no files associated with " + file_path + ", not moving anything",
                      sickrage.srCore.srLogger.DEBUG)
            return

        # create base name with file_path (media_file without .extension)
        old_base_name = file_path.rpartition('.')[0]
        old_base_name_length = len(old_base_name)

        # deal with all files
        for cur_file_path in file_list:

            cur_file_name = os.path.basename(cur_file_path)

            # get the extension without .
            cur_extension = cur_file_path[old_base_name_length + 1:]

            # check if file have subtitles language
            if os.path.splitext(cur_extension)[1][1:] in subtitleExtensions:
                cur_lang = os.path.splitext(cur_extension)[0]
                if cur_lang in wantedLanguages():
                    cur_extension = cur_lang + os.path.splitext(cur_extension)[1]

            # replace .nfo with .nfo-orig to avoid conflicts
            if cur_extension == 'nfo' and sickrage.srCore.srConfig.NFO_RENAME == True:
                cur_extension = 'nfo-orig'

            # If new base name then convert name
            if new_base_name:
                new_file_name = new_base_name + '.' + cur_extension
            # if we're not renaming we still want to change extensions sometimes
            else:
                new_file_name = replaceExtension(cur_file_name, cur_extension)

            if sickrage.srCore.srConfig.SUBTITLES_DIR and cur_extension in subtitleExtensions:
                subs_new_path = os.path.join(new_path, sickrage.srCore.srConfig.SUBTITLES_DIR)
                dir_exists = makeDir(subs_new_path)
                if not dir_exists:
                    sickrage.srCore.srLogger.error("Unable to create subtitles folder " + subs_new_path)
                else:
                    chmodAsParent(subs_new_path)
                new_file_path = os.path.join(subs_new_path, new_file_name)
            else:
                new_file_path = os.path.join(new_path, new_file_name)

            action(cur_file_path, new_file_path)

    def _move(self, file_path, new_path, new_base_name, associated_files=False, subs=False):
        """
        Move file and set proper permissions

        :param file_path: The full path of the media file to move
        :param new_path: Destination path where we want to move the file to
        :param new_base_name: The base filename (no extension) to use during the move. Use None to keep the same name.
        :param associated_files: Boolean, whether we should move similarly-named files too
        """

        def _int_move(cur_file_path, new_file_path):

            self._log("Moving file from " + cur_file_path + " to " + new_file_path, sickrage.srCore.srLogger.DEBUG)
            try:
                moveFile(cur_file_path, new_file_path)
                chmodAsParent(new_file_path)
            except (IOError, OSError) as e:
                self._log("Unable to move file " + cur_file_path + " to " + new_file_path + ": {}".format(e.message),
                          sickrage.srCore.srLogger.ERROR)
                raise

        self._combined_file_operation(file_path, new_path, new_base_name, associated_files, action=_int_move,
                                      subs=subs)

    def _copy(self, file_path, new_path, new_base_name, associated_files=False, subs=False):
        """
        Copy file and set proper permissions

        :param file_path: The full path of the media file to copy
        :param new_path: Destination path where we want to copy the file to
        :param new_base_name: The base filename (no extension) to use during the copy. Use None to keep the same name.
        :param associated_files: Boolean, whether we should copy similarly-named files too
        """

        def _int_copy(cur_file_path, new_file_path):

            self._log("Copying file from " + cur_file_path + " to " + new_file_path, sickrage.srCore.srLogger.DEBUG)
            try:
                copyFile(cur_file_path, new_file_path)
                chmodAsParent(new_file_path)
            except (IOError, OSError) as e:
                sickrage.srCore.srLogger.error(
                    "Unable to copy file " + cur_file_path + " to " + new_file_path + ": {}".format(e.message))
                raise

        self._combined_file_operation(file_path, new_path, new_base_name, associated_files, action=_int_copy,
                                      subs=subs)

    def _hardlink(self, file_path, new_path, new_base_name, associated_files=False, subs=False):
        """
        Hardlink file and set proper permissions

        :param file_path: The full path of the media file to move
        :param new_path: Destination path where we want to create a hard linked file
        :param new_base_name: The base filename (no extension) to use during the link. Use None to keep the same name.
        :param associated_files: Boolean, whether we should move similarly-named files too
        """

        def _int_hard_link(cur_file_path, new_file_path):

            self._log("Hard linking file from " + cur_file_path + " to " + new_file_path,
                      sickrage.srCore.srLogger.DEBUG)
            try:
                hardlinkFile(cur_file_path, new_file_path)
                chmodAsParent(new_file_path)
            except (IOError, OSError) as e:
                self._log("Unable to link file {} to {}: {}".format(cur_file_path, new_file_path,
                                                                    e)), sickrage.srCore.srLogger.ERROR
                raise

        self._combined_file_operation(file_path, new_path, new_base_name, associated_files, action=_int_hard_link,
                                      subs=subs)

    def _moveAndSymlink(self, file_path, new_path, new_base_name, associated_files=False, subs=False):
        """
        Move file, symlink source location back to destination, and set proper permissions

        :param file_path: The full path of the media file to move
        :param new_path: Destination path where we want to move the file to create a symbolic link to
        :param new_base_name: The base filename (no extension) to use during the link. Use None to keep the same name.
        :param associated_files: Boolean, whether we should move similarly-named files too
        """

        def _int_move_and_sym_link(cur_file_path, new_file_path):

            self._log("Moving then symbolic linking file from " + cur_file_path + " to " + new_file_path,
                      sickrage.srCore.srLogger.DEBUG)
            try:
                moveAndSymlinkFile(cur_file_path, new_file_path)
                chmodAsParent(new_file_path)
            except (IOError, OSError) as e:
                self._log("Unable to link file " + cur_file_path + " to " + new_file_path + ": {}".format(e.message),
                          sickrage.srCore.srLogger.ERROR)
                raise

        self._combined_file_operation(file_path, new_path, new_base_name, associated_files,
                                      action=_int_move_and_sym_link, subs=subs)

    def _history_lookup(self):
        """
        Look up the NZB name in the history and see if it contains a record for self.nzb_name

        :return: A (indexer_id, season, [], quality, version) tuple. The first two may be None if none were found.
        """

        to_return = (None, None, [], None, None)

        # if we don't have either of these then there's nothing to use to search the history for anyway
        if not self.nzb_name and not self.folder_name:
            self.in_history = False
            return to_return

        # make a list of possible names to use in the search
        names = []
        if self.nzb_name:
            names.append(self.nzb_name)
            if '.' in self.nzb_name: names.append(self.nzb_name.rpartition(".")[0])
        if self.folder_name: names.append(self.folder_name)

        # search the database for a possible match and return immediately if we find one

        for curName in names:
            search_name = re.sub(r"[\.\- ]", "_", curName)

            dbData = [x['doc'] for x in sickrage.srCore.mainDB.db.all('history', with_doc=True)
                      if search_name in x['doc']['resource']]

            if len(dbData) == 0:
                continue

            indexer_id = int(dbData[0]["showid"])
            season = int(dbData[0]["season"])
            quality = int(dbData[0]["quality"])
            version = int(dbData[0]["version"])

            if quality == Quality.UNKNOWN:
                quality = None

            show = findCertainShow(sickrage.srCore.SHOWLIST, indexer_id)

            self.in_history = True
            self.version = version
            to_return = (show, season, [], quality, version)

            qual_str = Quality.qualityStrings[quality] if quality is not None else quality
            self._log("Found result in history for {} - Season: {} - Quality: {} - Version: {}".format(
                show.name if show else "UNDEFINED", season, qual_str, version), sickrage.srCore.srLogger.DEBUG)

            return to_return

        self.in_history = False
        return to_return

    def _finalize(self, parse_result):
        """
        Store parse result if it is complete and final

        :param parse_result: Result of parsers
        """
        self.release_group = parse_result.release_group

        # remember whether it's a proper
        if parse_result.extra_info:
            self.is_proper = re.search(r'(^|[\. _-])(proper|repack)([\. _-]|$)', parse_result.extra_info,
                                       re.I) is not None

        # if the result is complete then remember that for later
        # if the result is complete then set release name
        if parse_result.series_name and (not (not (
                        parse_result.season_number is not None and parse_result.episode_numbers) and not parse_result.air_date)) and parse_result.release_group:

            if not self.release_name:
                self.release_name = remove_non_release_groups(
                    remove_extension(os.path.basename(parse_result.original_name)))

        else:
            sickrage.srCore.srLogger.debug(
                "Parse result not sufficient (all following have to be set). will not save release name")
            sickrage.srCore.srLogger.debug("Parse result(series_name): " + str(parse_result.series_name))
            sickrage.srCore.srLogger.debug("Parse result(season_number): " + str(parse_result.season_number))
            sickrage.srCore.srLogger.debug("Parse result(episode_numbers): " + str(parse_result.episode_numbers))
            sickrage.srCore.srLogger.debug("Parse result(air_date): " + str(parse_result.air_date))
            sickrage.srCore.srLogger.debug("Parse result(release_group): " + str(parse_result.release_group))

    def _analyze_name(self, name):
        """
        Takes a name and tries to figure out a show, season, and episode from it.

        :param name: A string which we want to analyze to determine show info from (unicode)

        :return: A (indexer_id, season, [episodes]) tuple. The first two may be None and episodes may be []
        if none were found.
        """

        to_return = (None, None, [], None, None)

        if not name:
            return to_return

        sickrage.srCore.srLogger.debug("Analyzing name " + repr(name))

        name = remove_non_release_groups(remove_extension(name))

        # parse the name to break it into show name, season, and episode
        np = NameParser(True, tryIndexers=True)
        parse_result = np.parse(name)

        # show object
        show = parse_result.show

        if parse_result.is_air_by_date:
            season = -1
            episodes = [parse_result.air_date]
        else:
            season = parse_result.season_number
            episodes = parse_result.episode_numbers

        to_return = (show, season, episodes, parse_result.quality, None)

        self._finalize(parse_result)
        return to_return

    @staticmethod
    def _build_anidb_episode(connection, filePath):
        """
        Look up anidb properties for an episode

        :param connection: anidb connection handler
        :param filePath: file to check
        :return: episode object
        """
        ep = aniDBAbstracter.Episode(connection, filePath=filePath,
                                     paramsF=["quality", "anidb_file_name", "crc32"],
                                     paramsA=["epno", "english_name", "short_name_list", "other_name", "synonym_list"])

        return ep

    def _add_to_anidb_mylist(self, filePath):
        """
        Adds an episode to anidb mylist

        :param filePath: file to add to mylist
        """
        if sickrage.srCore.ADBA_CONNECTION:
            if not self.anidbEpisode:  # seems like we could parse the name before, now lets build the anidb object
                self.anidbEpisode = self._build_anidb_episode(sickrage.srCore.ADBA_CONNECTION, filePath)

            self._log("Adding the file to the anidb mylist", sickrage.srCore.srLogger.DEBUG)
            try:
                self.anidbEpisode.add_to_mylist(status=1)  # status = 1 sets the status of the file to "internal HDD"
            except Exception as e:
                self._log("exception msg: " + str(e))

    def _find_info(self):
        """
        For a given file try to find the showid, season, and episode.

        :return: A (show, season, episodes, quality, version) tuple
        """

        show = season = quality = version = None
        episodes = []

        # try to look up the nzb in history
        attempt_list = [
            self._history_lookup,

            # try to analyze the nzb name
            lambda: self._analyze_name(self.nzb_name),

            # try to analyze the file name
            lambda: self._analyze_name(self.file_name),

            # try to analyze the dir name
            lambda: self._analyze_name(self.folder_name),

            # try to analyze the file + dir names together
            lambda: self._analyze_name(self.file_path),

            # try to analyze the dir + file name together as one name
            lambda: self._analyze_name(self.folder_name + ' ' + self.file_name)
        ]

        # attempt every possible method to get our info
        for cur_attempt in attempt_list:

            try:
                (cur_show, cur_season, cur_episodes, cur_quality, cur_version) = cur_attempt()
            except (InvalidNameException, InvalidShowException) as e:
                sickrage.srCore.srLogger.debug("Unable to parse, skipping: {}".format(e.message))
                continue

            if not cur_show:
                continue
            else:
                show = cur_show

            if cur_quality and not (self.in_history and quality):
                quality = cur_quality

            # we only get current version for animes from history to prevent issues with old database entries
            if cur_version is not None:
                version = cur_version

            if cur_season is not None:
                season = cur_season
            if cur_episodes:
                episodes = cur_episodes

            # for air-by-date shows we need to look up the season/episode from database
            if season == -1 and show and episodes:
                self._log(
                    "Looks like this is an air-by-date or sports show, attempting to convert the date to season/episode",
                    sickrage.srCore.srLogger.DEBUG)
                airdate = episodes[0].toordinal()

                # Ignore season 0 when searching for episode(Conflict between special and regular episode, same air date)
                dbData = [x['doc'] for x in sickrage.srCore.mainDB.db.get_many('tv_episodes', show.indexerid, with_doc=True)
                          if x['doc']['indexer'] == show.indexer
                          and x['doc']['airdate'] == airdate
                          and x['doc']['season'] != 0]

                if dbData:
                    season = int(dbData[0]['season'])
                    episodes = [int(dbData[0]['episode'])]
                else:
                    # Found no result, try with season 0
                    dbData = [x['doc'] for x in sickrage.srCore.mainDB.db.get_many('tv_episodes', show.indexerid, with_doc=True)
                              if x['doc']['indexer'] == show.indexer and x['doc']['airdate'] == airdate]

                    if dbData:
                        season = int(dbData[0]['season'])
                        episodes = [int(dbData[0]['episode'])]
                    else:
                        # we don't want to leave dates in the episode list if we couldn't convert them to real episode numbers
                        episodes = []
                        self._log(
                            "Unable to find episode with date " +
                            str(episodes[0]) + " for show " + str(show.indexerid) + ", skipping",
                            sickrage.srCore.srLogger.DEBUG)
                        continue

            # if there's no season then we can hopefully just use 1 automatically
            elif season is None and show:
                if len({x['doc']['season'] for x in sickrage.srCore.mainDB.db.get_many('tv_episodes', show.indexerid, with_doc=True)
                        if x['doc']['season'] != 0 and x['doc']['indexer'] == show.indexer}) == 1 and season is None:
                    season = 1
                    self._log(
                        "Don't have a season number, but this show appears to only have 1 season, setting season number to 1...",
                        sickrage.srCore.srLogger.DEBUG)

            if show and season and episodes:
                return show, season, episodes, quality, version

        return show, season, episodes, quality, version

    def _get_ep_obj(self, show, season, episodes):
        """
        Retrieve the TVEpisode object requested.

        :param show: The show object belonging to the show we want to process
        :param season: The season of the episode (int)
        :param episodes: A list of episodes to find (list of ints)

        :return: If the episode(s) can be found then a TVEpisode object with the correct related eps will
        be instantiated and returned. If the episode can't be found then None will be returned.
        """

        root_ep = None
        for cur_episode in episodes:
            self._log("Retrieving episode object for " + str(season) + "x" + str(cur_episode),
                      sickrage.srCore.srLogger.DEBUG)

            # now that we've figured out which episode this file is just load it manually
            try:
                curEp = show.getEpisode(season, cur_episode)
            except EpisodeNotFoundException as e:
                self._log("Unable to create episode: {}".format(e.message)), sickrage.srCore.srLogger.DEBUG
                raise EpisodePostProcessingFailedException()

            # associate all the episodes together under a single root episode
            if root_ep is None:
                root_ep = curEp
                root_ep.relatedEps = []
            elif curEp not in root_ep.relatedEps:
                root_ep.relatedEps.append(curEp)

        return root_ep

    def _get_quality(self, ep_obj):
        """
        Determines the quality of the file that is being post processed, first by checking if it is directly
        available in the TVEpisode's status or otherwise by parsing through the data available.

        :param ep_obj: The TVEpisode object related to the file we are post processing
        :return: A quality value found in Quality
        """

        # if there is a quality available in the status then we don't need to bother guessing from the filename
        if ep_obj.status in Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST:
            _, ep_quality = Quality.splitCompositeStatus(ep_obj.status)  # @UnusedVariable
            if ep_quality != Quality.UNKNOWN:
                self._log(
                    "The old status had a quality in it, using that: " + Quality.qualityStrings[ep_quality],
                    sickrage.srCore.srLogger.DEBUG)
                return ep_quality

        # nzb name is the most reliable if it exists, followed by folder name and lastly file name
        name_list = [self.nzb_name, self.folder_name, self.file_name]

        # search all possible names for our new quality, in case the file or dir doesn't have it
        for cur_name in name_list:

            # some stuff might be None at this point still
            if not cur_name:
                continue

            ep_quality = Quality.nameQuality(cur_name, ep_obj.show.is_anime)
            self._log(
                "Looking up quality for name " + cur_name + ", got " + Quality.qualityStrings[ep_quality],
                sickrage.srCore.srLogger.DEBUG)

            # if we find a good one then use it
            if ep_quality != Quality.UNKNOWN:
                sickrage.srCore.srLogger.debug(cur_name + " looks like it has quality " + Quality.qualityStrings[
                    ep_quality] + ", using that")
                return ep_quality

        # Try getting quality from the episode (snatched) status
        if ep_obj.status in Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST:
            _, ep_quality = Quality.splitCompositeStatus(ep_obj.status)  # @UnusedVariable
            if ep_quality != Quality.UNKNOWN:
                self._log(
                    "The old status had a quality in it, using that: " + Quality.qualityStrings[ep_quality],
                    sickrage.srCore.srLogger.DEBUG)
                return ep_quality

        # Try guessing quality from the file name
        ep_quality = Quality.assumeQuality(self.file_path)
        self._log(
            "Guessing quality for name " + self.file_name + ", got " + Quality.qualityStrings[ep_quality],
            sickrage.srCore.srLogger.DEBUG)

        if ep_quality != Quality.UNKNOWN:
            sickrage.srCore.srLogger.debug(self.file_name + " looks like it has quality " + Quality.qualityStrings[
                ep_quality] + ", using that")

        return ep_quality

    def _run_extra_scripts(self, ep_obj):
        """
        Executes any extra scripts defined in the config.

        :param ep_obj: The object to use when calling the extra script
        """
        for curScriptName in sickrage.srCore.srConfig.EXTRA_SCRIPTS:

            # generate a safe command line string to execute the script and provide all the parameters
            script_cmd = [piece for piece in re.split("( |\\\".*?\\\"|'.*?')", curScriptName) if piece.strip()]
            script_cmd[0] = os.path.abspath(script_cmd[0])
            self._log("Absolute path to script: " + script_cmd[0], sickrage.srCore.srLogger.DEBUG)

            script_cmd = script_cmd + [ep_obj.location, self.file_path, str(ep_obj.show.indexerid), str(ep_obj.season),
                                       str(ep_obj.episode), str(ep_obj.airdate)]

            # use subprocess to run the command and capture output
            self._log("Executing command " + str(script_cmd))
            try:
                p = subprocess.Popen(script_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, cwd=sickrage.PROG_DIR)
                out, _ = p.communicate()  # @UnusedVariable
                self._log("Script result: " + str(out), sickrage.srCore.srLogger.DEBUG)

            except OSError as e:
                self._log("Unable to run extra_script: {}".format(e.message))

            except Exception as e:
                self._log("Unable to run extra_script: {}".format(e.message))

    def _is_priority(self, ep_obj, new_ep_quality):
        """
        Determines if the episode is a priority download or not (if it is expected). Episodes which are expected
        (snatched) or larger than the existing episode are priority, others are not.

        :param ep_obj: The TVEpisode object in question
        :param new_ep_quality: The quality of the episode that is being processed
        :return: True if the episode is priority, False otherwise.
        """

        if self.is_priority:
            return True

        _, old_ep_quality = Quality.splitCompositeStatus(ep_obj.status)

        # if SR downloaded this on purpose we likely have a priority download
        if self.in_history or ep_obj.status in Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST:
            # if the episode is still in a snatched status, then we can assume we want this
            if not self.in_history:
                self._log("SR snatched this episode and it is not processed before", sickrage.srCore.srLogger.DEBUG)
                return True

            # if it's in history, we only want it if the new quality is higher or if it's a proper of equal or higher quality
            if new_ep_quality > old_ep_quality and new_ep_quality != Quality.UNKNOWN:
                self._log("SR snatched this episode and it is a higher quality so I'm marking it as priority",
                          sickrage.srCore.srLogger.DEBUG)
                return True

            if self.is_proper and new_ep_quality >= old_ep_quality and new_ep_quality != Quality.UNKNOWN:
                self._log(
                    "SR snatched this episode and it is a proper of equal or higher quality so I'm marking it as priority",
                    sickrage.srCore.srLogger.DEBUG)
                return True

            return False

        # if the user downloaded it manually and it's higher quality than the existing episode then it's priority
        if new_ep_quality > old_ep_quality and new_ep_quality != Quality.UNKNOWN:
            self._log(
                "This was manually downloaded but it appears to be better quality than what we have so I'm marking it as priority",
                sickrage.srCore.srLogger.DEBUG)
            return True

        # if the user downloaded it manually and it appears to be a PROPER/REPACK then it's priority
        if self.is_proper and new_ep_quality >= old_ep_quality and new_ep_quality != Quality.UNKNOWN:
            self._log("This was manually downloaded but it appears to be a proper so I'm marking it as priority",
                      sickrage.srCore.srLogger.DEBUG)
            return True

        return False

    @property
    def process(self):
        """
        Post-process a given file

        :return: True on success, False on failure
        """

        self._log("Processing {}".format(self.file_path))

        if os.path.isdir(self.file_path):
            self._log("File %s seems to be a directory" % self.file_path)
            return False

        if not os.path.exists(self.file_path):
            self._log("File %s doesn't exist, did unrar fail?" % self.file_path)
            return False

        for ignore_file in self.IGNORED_FILESTRINGS:
            if ignore_file in self.file_path:
                self._log("File %s is ignored type, skipping" % self.file_path)
                return False

        # reset per-file stuff
        self.in_history = False

        # reset the anidb episode object
        self.anidbEpisode = None

        # try to find the file info
        (show, season, episodes, quality, version) = self._find_info()
        if not show:
            self._log("This show isn't in your list, you need to add it to SR before post-processing an episode")
            raise EpisodePostProcessingFailedException()
        elif season is None or not episodes:
            self._log("Not enough information to determine what episode this is. Quitting post-processing")
            return False

        # retrieve/create the corresponding TVEpisode objects
        ep_obj = self._get_ep_obj(show, season, episodes)
        _, old_ep_quality = Quality.splitCompositeStatus(ep_obj.status)

        # get the quality of the episode we're processing
        if quality and not Quality.qualityStrings[quality] == 'Unknown':
            self._log("Snatch history had a quality in it, using that: " + Quality.qualityStrings[quality],
                      sickrage.srCore.srLogger.DEBUG)
            new_ep_quality = quality
        else:
            new_ep_quality = self._get_quality(ep_obj)

        sickrage.srCore.srLogger.debug("Quality of the episode we're processing: %s" % new_ep_quality)

        # see if this is a priority download (is it snatched, in history, PROPER, or BEST)
        priority_download = self._is_priority(ep_obj, new_ep_quality)
        self._log("Is ep a priority download: " + str(priority_download), sickrage.srCore.srLogger.DEBUG)

        # get the version of the episode we're processing
        if version:
            self._log("Snatch history had a version in it, using that: v" + str(version),
                      sickrage.srCore.srLogger.DEBUG)
            new_ep_version = version
        else:
            new_ep_version = -1

        # check for an existing file
        existing_file_status = self._checkForExistingFile(ep_obj.location)

        # if it's not priority then we don't want to replace smaller files in case it was a mistake
        if not priority_download:

            # Not a priority and the quality is lower than what we already have
            if (new_ep_quality < old_ep_quality != Quality.UNKNOWN) \
                    and not existing_file_status == PostProcessor.DOESNT_EXIST:
                self._log("File exists and new file quality is lower than existing, marking it unsafe to replace")
                return False

            # if there's an existing file that we don't want to replace stop here
            if existing_file_status == PostProcessor.EXISTS_LARGER:
                if self.is_proper:
                    self._log(
                        "File exists and new file is smaller, new file is a proper/repack, marking it safe to replace")
                    return True

                else:
                    self._log("File exists and new file is smaller, marking it unsafe to replace")
                    return False

            elif existing_file_status == PostProcessor.EXISTS_SAME:
                self._log("File exists and new file is same size, marking it unsafe to replace")
                return False

        # if the file is priority then we're going to replace it even if it exists
        else:
            self._log(
                "This download is marked a priority download so I'm going to replace an existing file if I find one")

        # try to find out if we have enough space to perform the copy or move action.
        if not isFileLocked(self.file_path, False):
            if not verify_freespace(self.file_path, ep_obj.show.location, [ep_obj] + ep_obj.relatedEps):
                self._log("Not enough space to continue PP, exiting", sickrage.srCore.srLogger.WARNING)
                return False
        else:
            self._log("Unable to determine needed filespace as the source file is locked for access")

        # delete the existing file (and company)
        for cur_ep in [ep_obj] + ep_obj.relatedEps:
            try:
                self._delete(cur_ep.location, associated_files=True)

                # clean up any left over folders
                if cur_ep.location:
                    delete_empty_folders(os.path.dirname(cur_ep.location), keep_dir=ep_obj.show.location)
            except (OSError, IOError):
                raise EpisodePostProcessingFailedException("Unable to delete the existing files")

                # set the status of the episodes
                # for curEp in [ep_obj] + ep_obj.relatedEps:
                #    curEp.status = Quality.compositeStatus(SNATCHED, new_ep_quality)

        # if the show directory doesn't exist then make it if allowed
        if not os.path.isdir(ep_obj.show.location) and sickrage.srCore.srConfig.CREATE_MISSING_SHOW_DIRS:
            self._log("Show directory doesn't exist, creating it", sickrage.srCore.srLogger.DEBUG)
            try:
                os.mkdir(ep_obj.show.location)
                chmodAsParent(ep_obj.show.location)

                # do the library update for synoindex
                sickrage.srCore.notifiersDict.synoindex_notifier.addFolder(ep_obj.show.location)
            except (OSError, IOError):
                raise EpisodePostProcessingFailedException(
                    "Unable to create the show directory: " + ep_obj.show.location)

            # get metadata for the show (but not episode because it hasn't been fully processed)
            ep_obj.show.writeMetadata(True)

        # update the ep info before we rename so the quality & release name go into the name properly
        for cur_ep in [ep_obj] + ep_obj.relatedEps:
            with cur_ep.lock:

                if self.release_name:
                    self._log("Found release name " + self.release_name, sickrage.srCore.srLogger.DEBUG)
                    cur_ep.release_name = self.release_name
                else:
                    cur_ep.release_name = ""

                if ep_obj.status in Quality.SNATCHED_BEST:
                    cur_ep.status = Quality.compositeStatus(ARCHIVED, new_ep_quality)
                else:
                    cur_ep.status = Quality.compositeStatus(DOWNLOADED, new_ep_quality)

                cur_ep.subtitles = ''

                cur_ep.subtitles_searchcount = 0

                cur_ep.subtitles_lastsearch = '0001-01-01 00:00:00'

                cur_ep.is_proper = self.is_proper

                cur_ep.version = new_ep_version

                if self.release_group:
                    cur_ep.release_group = self.release_group
                else:
                    cur_ep.release_group = ""

                cur_ep.saveToDB()

        # Just want to keep this consistent for failed handling right now
        releaseName = show_names.determineReleaseName(self.folder_path, self.nzb_name)
        if releaseName is not None:
            FailedHistory.logSuccess(releaseName)
        else:
            self._log("Couldn't find release in snatch history", sickrage.srCore.srLogger.WARNING)

        # find the destination folder
        if not os.path.isdir(ep_obj.show.location):
            raise EpisodePostProcessingFailedException(
                "Unable to post-process an episode if the show dir doesn't exist, quitting")

        proper_path = ep_obj.proper_path()
        proper_absolute_path = os.path.join(ep_obj.show.location, proper_path)
        dest_path = os.path.dirname(proper_absolute_path)

        self._log("Destination folder for this episode: " + dest_path, sickrage.srCore.srLogger.DEBUG)

        # create any folders we need
        make_dirs(dest_path)

        # figure out the base name of the resulting episode file
        if sickrage.srCore.srConfig.RENAME_EPISODES:
            orig_extension = self.file_name.rpartition('.')[-1]
            new_base_name = os.path.basename(proper_path)
            new_file_name = new_base_name + '.' + orig_extension

        else:
            # if we're not renaming then there's no new base name, we'll just use the existing name
            new_base_name = None
            new_file_name = self.file_name

        # add to anidb
        if ep_obj.show.is_anime and sickrage.srCore.srConfig.ANIDB_USE_MYLIST:
            self._add_to_anidb_mylist(self.file_path)

        try:
            # move the episode and associated files to the show dir
            if self.process_method == "copy":
                if isFileLocked(self.file_path, False):
                    raise EpisodePostProcessingFailedException("File is locked for reading")
                self._copy(self.file_path, dest_path, new_base_name, sickrage.srCore.srConfig.MOVE_ASSOCIATED_FILES,
                           sickrage.srCore.srConfig.USE_SUBTITLES and ep_obj.show.subtitles)
            elif self.process_method == "move":
                if isFileLocked(self.file_path, True):
                    raise EpisodePostProcessingFailedException("File is locked for reading/writing")
                self._move(self.file_path, dest_path, new_base_name, sickrage.srCore.srConfig.MOVE_ASSOCIATED_FILES,
                           sickrage.srCore.srConfig.USE_SUBTITLES and ep_obj.show.subtitles)
            elif self.process_method == "hardlink":
                self._hardlink(self.file_path, dest_path, new_base_name, sickrage.srCore.srConfig.MOVE_ASSOCIATED_FILES,
                               sickrage.srCore.srConfig.USE_SUBTITLES and ep_obj.show.subtitles)
            elif self.process_method == "symlink":
                if isFileLocked(self.file_path, True):
                    raise EpisodePostProcessingFailedException("File is locked for reading/writing")
                self._moveAndSymlink(self.file_path, dest_path, new_base_name,
                                     sickrage.srCore.srConfig.MOVE_ASSOCIATED_FILES,
                                     sickrage.srCore.srConfig.USE_SUBTITLES and ep_obj.show.subtitles)
            else:
                sickrage.srCore.srLogger.error("Unknown process method: " + str(self.process_method))
                raise EpisodePostProcessingFailedException("Unable to move the files to their new home")
        except (OSError, IOError):
            raise EpisodePostProcessingFailedException("Unable to move the files to their new home")

        # download subtitles
        if sickrage.srCore.srConfig.USE_SUBTITLES and ep_obj.show.subtitles:
            for cur_ep in [ep_obj] + ep_obj.relatedEps:
                with cur_ep.lock:
                    cur_ep.location = os.path.join(dest_path, new_file_name)
                    cur_ep.refreshSubtitles()
                    cur_ep.downloadSubtitles(force=True)

        # put the new location in the database
        for cur_ep in [ep_obj] + ep_obj.relatedEps:
            with cur_ep.lock:
                cur_ep.location = os.path.join(dest_path, new_file_name)
                cur_ep.saveToDB()

        # set file modify stamp to show airdate
        if sickrage.srCore.srConfig.AIRDATE_EPISODES:
            for cur_ep in [ep_obj] + ep_obj.relatedEps:
                with cur_ep.lock:
                    cur_ep.airdateModifyStamp()

        # generate nfo/tbn
        ep_obj.createMetaFiles()

        # log it to history
        History.logDownload(ep_obj, self.file_path, new_ep_quality, self.release_group, new_ep_version)

        # If any notification fails, don't stop postProcessor
        try:
            # send notifications
            srNotifiers.notify_download(ep_obj._format_pattern('%SN - %Sx%0E - %EN - %QN'))

            # do the library update for KODI
            sickrage.srCore.notifiersDict.kodi_notifier.update_library(ep_obj.show.name)

            # do the library update for Plex
            sickrage.srCore.notifiersDict.plex_notifier.update_library(ep_obj)

            # do the library update for EMBY
            sickrage.srCore.notifiersDict.emby_notifier.update_library(ep_obj.show)

            # do the library update for NMJ
            # nmj_notifier kicks off its library update when the notify_download is issued (inside notifiers)

            # do the library update for Synology Indexer
            sickrage.srCore.notifiersDict.synoindex_notifier.addFile(ep_obj.location)

            # do the library update for pyTivo
            sickrage.srCore.notifiersDict.pytivo_notifier.update_library(ep_obj)

            # do the library update for Trakt
            sickrage.srCore.notifiersDict.trakt_notifier.update_library(ep_obj)
        except:
            sickrage.srCore.srLogger.info("Some notifications could not be sent. Continuing with post-processing...")

        self._run_extra_scripts(ep_obj)

        return True
