# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.tv/
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import os
import stat

import UnRAR2
from UnRAR2.rar_exceptions import ArchiveHeaderBroken, FileOpenError, \
    IncorrectRARPassword, InvalidRARArchive, InvalidRARArchiveUsage

import sickrage
from sickrage.core.common import Quality
from sickrage.core.databases import main_db
from sickrage.core.exceptions import EpisodePostProcessingFailedException, \
    FailedPostProcessingFailedException
from sickrage.core.helpers import isMediaFile, isRarFile, isSyncFile, \
    is_hidden_folder, notTorNZBFile, real_path, removetree
from sickrage.core.nameparser import InvalidNameException, InvalidShowException, \
    NameParser
from sickrage.core.processors import failed_processor, post_processor


class ProcessResult(object):
    def __init__(self):
        self.result = True
        self.output = ''
        self.missedfiles = []
        self.aggresult = True


def delete_folder(folder, check_empty=True):
    """
    Removes a folder from the filesystem

    :param folder: Path to folder to remove
    :param check_empty: Boolean, check if the folder is empty before removing it, defaults to True
    :return: True on success, False on failure
    """

    # check if it's a folder
    if not os.path.isdir(folder):
        return False

    # check if it isn't TV_DOWNLOAD_DIR
    if sickrage.srCore.srConfig.TV_DOWNLOAD_DIR:
        if real_path(folder) == real_path(sickrage.srCore.srConfig.TV_DOWNLOAD_DIR):
            return False

    # check if it's empty folder when wanted checked
    try:
        if check_empty:
            check_files = os.listdir(folder)
            if check_files:
                sickrage.srCore.srLogger.info("Not deleting folder {} found the following files: {}".format(folder, check_files))
                return False

            sickrage.srCore.srLogger.info("Deleting folder (if it's empty): " + folder)
            os.rmdir(folder)
        else:
            sickrage.srCore.srLogger.info("Deleting folder: " + folder)
            removetree(folder)
    except (OSError, IOError) as e:
        sickrage.srCore.srLogger.warning("Warning: unable to delete folder: {}: {}".format(folder, e))
        return False

    return True


def delete_files(processPath, notwantedFiles, result, force=False):
    """
    Remove files from filesystem

    :param processPath: path to process
    :param notwantedFiles: files we do not want
    :param result: Processor results
    :param force: Boolean, force deletion, defaults to false
    """

    if not result.result and force:
        result.output += logHelper("Forcing deletion of files, even though last result was not success", sickrage.srCore.srLogger.DEBUG)
    elif not result.result:
        return

    # Delete all file not needed
    for cur_file in notwantedFiles:
        cur_file_path = os.path.join(processPath, cur_file)

        if not os.path.isfile(cur_file_path):
            continue  # Prevent error when a notwantedfiles is an associated files

        result.output += logHelper("Deleting file %s" % cur_file, sickrage.srCore.srLogger.DEBUG)

        # check first the read-only attribute
        file_attribute = os.stat(cur_file_path)[0]
        if not file_attribute & stat.S_IWRITE:
            # File is read-only, so make it writeable
            result.output += logHelper("Changing ReadOnly Flag for file %s" % cur_file, sickrage.srCore.srLogger.DEBUG)
            try:
                os.chmod(cur_file_path, stat.S_IWRITE)
            except OSError as e:
                result.output += logHelper(
                        "Cannot change permissions of %s: %s" % (
                            cur_file, str(e.strerror).decode(sickrage.SYS_ENCODING)),
                        sickrage.srCore.srLogger.DEBUG)
        try:
            os.remove(cur_file_path)
        except OSError as e:
            result.output += logHelper(
                    "Unable to delete file %s: %s" % (cur_file, str(e.strerror).decode(sickrage.SYS_ENCODING)),
                    sickrage.srCore.srLogger.DEBUG)


def logHelper(logMessage, logLevel=None):
    sickrage.srCore.srLogger.log(logLevel or sickrage.srCore.srLogger.INFO, logMessage)
    return logMessage + "\n"


def processDir(dirName, nzbName=None, process_method=None, force=False, is_priority=None, delete_on=False, failed=False,
               proc_type="auto", **kwargs):
    """
    Scans through the files in dirName and processes whatever media files it finds

    :param dirName: The folder name to look in
    :param nzbName: The NZB name which resulted in this folder being downloaded
    :param force: True to postprocess already postprocessed files
    :param failed: Boolean for whether or not the download failed
    :param proc_type: Type of postprocessing auto or manual
    """

    result = ProcessResult()

    result.output += logHelper("Processing folder %s" % dirName, sickrage.srCore.srLogger.DEBUG)

    result.output += logHelper("TV_DOWNLOAD_DIR: %s" % sickrage.srCore.srConfig.TV_DOWNLOAD_DIR, sickrage.srCore.srLogger.DEBUG)
    postpone = False

    # if they passed us a real dir then assume it's the one we want
    if os.path.isdir(dirName):
        dirName = os.path.realpath(dirName)

    # if the client and SickRage are not on the same machine translate the Dir in a network dir
    elif sickrage.srCore.srConfig.TV_DOWNLOAD_DIR and os.path.isdir(sickrage.srCore.srConfig.TV_DOWNLOAD_DIR) \
            and os.path.normpath(dirName) != os.path.normpath(sickrage.srCore.srConfig.TV_DOWNLOAD_DIR):
        dirName = os.path.join(sickrage.srCore.srConfig.TV_DOWNLOAD_DIR, os.path.abspath(dirName).split(os.path.sep)[-1])
        result.output += logHelper("Trying to use folder %s" % dirName, sickrage.srCore.srLogger.DEBUG)

    # if we didn't find a real dir then quit
    if not os.path.isdir(dirName):
        result.output += logHelper(
                "Unable to figure out what folder to process. If your downloader and SiCKRAGE aren't on the same PC make sure you fill out your TV download dir in the config.",
                sickrage.srCore.srLogger.DEBUG)
        return result.output

    path, dirs, files = get_path_dir_files(dirName, nzbName, proc_type)

    files = [x for x in files if notTorNZBFile(x)]
    SyncFiles = [x for x in files if isSyncFile(x)]

    # Don't post process if files are still being synced and option is activated
    if SyncFiles and sickrage.srCore.srConfig.POSTPONE_IF_SYNC_FILES:
        postpone = True

    nzbNameOriginal = nzbName

    if not postpone:
        result.output += logHelper("PostProcessing Path: %s" % path, sickrage.srCore.srLogger.INFO)
        result.output += logHelper("PostProcessing Dirs: [%s]" % ", ".join(dirs), sickrage.srCore.srLogger.DEBUG)

        rarFiles = [x for x in files if isRarFile(x)]
        rarContent = unRAR(path, rarFiles, force, result)
        files += rarContent
        videoFiles = [x for x in files if isMediaFile(x)]
        videoInRar = [x for x in rarContent if isMediaFile(x)]

        result.output += logHelper("PostProcessing Files: [%s]" % ", ".join(files), sickrage.srCore.srLogger.DEBUG)
        result.output += logHelper("PostProcessing VideoFiles: [%s]" % ", ".join(videoFiles), sickrage.srCore.srLogger.DEBUG)
        result.output += logHelper("PostProcessing RarContent: [%s]" % ", ".join(rarContent), sickrage.srCore.srLogger.DEBUG)
        result.output += logHelper("PostProcessing VideoInRar: [%s]" % ", ".join(videoInRar), sickrage.srCore.srLogger.DEBUG)

        # If nzbName is set and there's more than one videofile in the folder, files will be lost (overwritten).
        if len(videoFiles) >= 2:
            nzbName = None

        if not process_method:
            process_method = sickrage.srCore.srConfig.PROCESS_METHOD

        result.result = True

        # Don't Link media when the media is extracted from a rar in the same path
        if process_method in ('hardlink', 'symlink') and videoInRar:
            process_media(path, videoInRar, nzbName, 'move', force, is_priority, result)
            delete_files(path, rarContent, result)
            for video in set(videoFiles) - set(videoInRar):
                process_media(path, [video], nzbName, process_method, force, is_priority, result)
        elif sickrage.srCore.srConfig.DELRARCONTENTS and videoInRar:
            process_media(path, videoInRar, nzbName, process_method, force, is_priority, result)
            delete_files(path, rarContent, result, True)
            for video in set(videoFiles) - set(videoInRar):
                process_media(path, [video], nzbName, process_method, force, is_priority, result)
        else:
            for video in videoFiles:
                process_media(path, [video], nzbName, process_method, force, is_priority, result)

    else:
        result.output += logHelper("Found temporary sync files, skipping post processing for: %s" % path)
        result.output += logHelper("Sync Files: [%s] in path %s" % (", ".join(SyncFiles), path))
        result.missedfiles.append("%s : Syncfiles found" % path)

    # Process Video File in all TV Subdir
    for curDir in [x for x in dirs if validateDir(path, x, nzbNameOriginal, failed, result)]:

        result.result = True

        for processPath, _, fileList in os.walk(os.path.join(path, curDir), topdown=False):

            if not validateDir(path, processPath, nzbNameOriginal, failed, result):
                continue

            postpone = False

            SyncFiles = [x for x in fileList if isSyncFile(x)]

            # Don't post process if files are still being synced and option is activated
            if SyncFiles and sickrage.srCore.srConfig.POSTPONE_IF_SYNC_FILES:
                postpone = True

            if not postpone:
                rarFiles = [x for x in fileList if isRarFile(x)]
                rarContent = unRAR(processPath, rarFiles, force, result)
                fileList = set(fileList + rarContent)
                videoFiles = [x for x in fileList if isMediaFile(x)]
                videoInRar = [x for x in rarContent if isMediaFile(x)]
                notwantedFiles = [x for x in fileList if x not in videoFiles]
                if notwantedFiles:
                    result.output += logHelper("Found unwanted files: [%s]" % ", ".join(notwantedFiles), sickrage.srCore.srLogger.DEBUG)

                # Don't Link media when the media is extracted from a rar in the same path
                if process_method in ('hardlink', 'symlink') and videoInRar:
                    process_media(processPath, videoInRar, nzbName, 'move', force, is_priority, result)
                    process_media(processPath, set(videoFiles) - set(videoInRar), nzbName, process_method, force,
                                  is_priority, result)
                    delete_files(processPath, rarContent, result)
                elif sickrage.srCore.srConfig.DELRARCONTENTS and videoInRar:
                    process_media(processPath, videoInRar, nzbName, process_method, force, is_priority, result)
                    process_media(processPath, set(videoFiles) - set(videoInRar), nzbName, process_method, force,
                                  is_priority, result)
                    delete_files(processPath, rarContent, result, True)
                else:
                    process_media(processPath, videoFiles, nzbName, process_method, force, is_priority, result)

                    # Delete all file not needed
                    if process_method != "move" or not result.result \
                            or (
                                            proc_type == "manual" and not delete_on):  # Avoid to delete files if is Manual PostProcessing
                        continue

                    delete_files(processPath, notwantedFiles, result)

                    if (not sickrage.srCore.srConfig.NO_DELETE or proc_type == "manual") and process_method == "move" and \
                                    os.path.normpath(processPath) != os.path.normpath(
                                sickrage.srCore.srConfig.TV_DOWNLOAD_DIR):
                        if delete_folder(processPath, check_empty=True):
                            result.output += logHelper("Deleted folder: %s" % processPath, sickrage.srCore.srLogger.DEBUG)
            else:
                result.output += logHelper("Found temporary sync files, skipping post processing for: %s" % processPath)
                result.output += logHelper("Sync Files: [%s] in path %s" % (", ".join(SyncFiles), processPath))
                result.missedfiles.append("%s : Syncfiles found" % processPath)

    if result.aggresult:
        result.output += logHelper("Processing completed")
        if result.missedfiles:
            result.output += logHelper("I did encounter some unprocessable items: [%s]" % ", ".join(result.missedfiles))
    else:
        result.output += logHelper(
                "Problem(s) during processing, failed the following files/folders:  [%s]" % ", ".join(
                        result.missedfiles),
                sickrage.srCore.srLogger.WARNING)

    return result.output


def validateDir(path, dirName, nzbNameOriginal, failed, result):
    """
    Check if directory is valid for processing

    :param path: Path to use
    :param dirName: Directory to check
    :param nzbNameOriginal: Original NZB name
    :param failed: Previously failed objects
    :param result: Previous results
    :return: True if dir is valid for processing, False if not
    """

    IGNORED_FOLDERS = ['.AppleDouble', '.@__thumb', '@eaDir']

    folder_name = os.path.basename(dirName)
    if folder_name in IGNORED_FOLDERS:
        return False

    result.output += logHelper("Processing folder " + dirName, sickrage.srCore.srLogger.DEBUG)

    if folder_name.startswith('_FAILED_'):
        result.output += logHelper("The directory name indicates it failed to extract.", sickrage.srCore.srLogger.DEBUG)
        failed = True
    elif folder_name.startswith('_UNDERSIZED_'):
        result.output += logHelper("The directory name indicates that it was previously rejected for being undersized.",
                                   sickrage.srCore.srLogger.DEBUG)
        failed = True
    elif folder_name.upper().startswith('_UNPACK'):
        result.output += logHelper(
                "The directory name indicates that this release is in the process of being unpacked.", sickrage.srCore.srLogger.DEBUG)
        result.missedfiles.append(dirName + " : Being unpacked")
        return False

    if failed:
        process_failed(os.path.join(path, dirName), nzbNameOriginal, result)
        result.missedfiles.append(dirName + " : Failed download")
        return False

    if is_hidden_folder(os.path.join(path, dirName)):
        result.output += logHelper("Ignoring hidden folder: " + dirName, sickrage.srCore.srLogger.DEBUG)
        result.missedfiles.append(dirName + " : Hidden folder")
        return False

    # make sure the dir isn't inside a show dir
    for sqlShow in main_db.MainDB().select("SELECT * FROM tv_shows"):
        if dirName.lower().startswith(os.path.realpath(sqlShow["location"]).lower() + os.sep) or \
                        dirName.lower() == os.path.realpath(sqlShow["location"]).lower():
            result.output += logHelper(
                    "Cannot process an episode that's already been moved to its show dir, skipping " + dirName,
                    sickrage.srCore.srLogger.WARNING)
            return False

    # Get the videofile list for the next checks
    allFiles = []
    allDirs = []
    for _, processdir, fileList in os.walk(os.path.join(path, dirName), topdown=False):
        allDirs += processdir
        allFiles += fileList

    videoFiles = [x for x in allFiles if isMediaFile(x)]
    allDirs.append(dirName)

    # check if the dir have at least one tv video file
    for video in videoFiles:
        try:
            NameParser().parse(video, cache_result=False)
            return True
        except (InvalidNameException, InvalidShowException):
            pass

    for proc_dir in allDirs:
        try:
            NameParser().parse(proc_dir, cache_result=False)
            return True
        except (InvalidNameException, InvalidShowException):
            pass

    if sickrage.srCore.srConfig.UNPACK:
        # Search for packed release
        packedFiles = [x for x in allFiles if isRarFile(x)]

        for packed in packedFiles:
            try:
                NameParser().parse(packed, cache_result=False)
                return True
            except (InvalidNameException, InvalidShowException):
                pass

    result.output += logHelper(dirName + " : No processable items found in folder", sickrage.srCore.srLogger.DEBUG)
    return False


def unRAR(path, rarFiles, force, result):
    """
    Extracts RAR files

    :param path: Path to look for files in
    :param rarFiles: Names of RAR files
    :param force: process currently processing items
    :param result: Previous results
    :return: List of unpacked file names
    """

    unpacked_files = []

    if sickrage.srCore.srConfig.UNPACK and rarFiles:

        result.output += logHelper("Packed Releases detected: " + str(rarFiles), sickrage.srCore.srLogger.DEBUG)

        for archive in rarFiles:

            result.output += logHelper("Unpacking archive: " + archive, sickrage.srCore.srLogger.DEBUG)

            try:
                rar_handle = UnRAR2.RarFile(os.path.join(path, archive))

                # Skip extraction if any file in archive has previously been extracted
                skip_file = False
                for file_in_archive in [os.path.basename(x.filename) for x in rar_handle.infolist() if not x.isdir]:
                    if already_postprocessed(path, file_in_archive, force, result):
                        result.output += logHelper(
                                "Archive file already post-processed, extraction skipped: " + file_in_archive,
                                sickrage.srCore.srLogger.DEBUG)
                        skip_file = True
                        break

                if skip_file:
                    continue

                rar_handle.extract(path=path, withSubpath=False, overwrite=False)
                for x in rar_handle.infolist():
                    if not x.isdir:
                        basename = os.path.basename(x.filename)
                        if basename not in unpacked_files:
                            unpacked_files.append(basename)
                del rar_handle

            except ArchiveHeaderBroken as e:
                result.output += logHelper("Failed Unrar archive {0}: Unrar: Archive Header Broken".format(archive),
                                           sickrage.srCore.srLogger.ERROR)
                result.result = False
                result.missedfiles.append(archive + " : Unpacking failed because the Archive Header is Broken")
                continue
            except IncorrectRARPassword:
                result.output += logHelper("Failed Unrar archive {0}: Unrar: Incorrect Rar Password".format(archive),
                                           sickrage.srCore.srLogger.ERROR)
                result.result = False
                result.missedfiles.append(archive + " : Unpacking failed because of an Incorrect Rar Password")
                continue
            except FileOpenError:
                result.output += logHelper(
                        "Failed Unrar archive {0}: Unrar: File Open Error, check the parent folder and destination file permissions.".format(
                                archive), sickrage.srCore.srLogger.ERROR)
                result.result = False
                result.missedfiles.append(archive + " : Unpacking failed with a File Open Error (file permissions?)")
                continue
            except InvalidRARArchiveUsage:
                result.output += logHelper("Failed Unrar archive {0}: Unrar: Invalid Rar Archive Usage".format(archive),
                                           sickrage.srCore.srLogger.ERROR)
                result.result = False
                result.missedfiles.append(archive + " : Unpacking Failed with Invalid Rar Archive Usage")
                continue
            except InvalidRARArchive:
                result.output += logHelper("Failed Unrar archive {0}: Unrar: Invalid Rar Archive".format(archive),
                                           sickrage.srCore.srLogger.ERROR)
                result.result = False
                result.missedfiles.append(archive + " : Unpacking Failed with an Invalid Rar Archive Error")
                continue
            except Exception as e:
                result.output += logHelper("Failed Unrar archive {}: {}".format(archive, e), sickrage.srCore.srLogger.ERROR)
                result.result = False
                result.missedfiles.append(archive + " : Unpacking failed for an unknown reason")
                continue

        result.output += logHelper("UnRar content: " + str(unpacked_files), sickrage.srCore.srLogger.DEBUG)

    return unpacked_files


def already_postprocessed(dirName, videofile, force, result):
    """
    Check if we already post processed a file

    :param dirName: Directory a file resides in
    :param videofile: File name
    :param force: Force checking when already checking (currently unused)
    :param result: True if file is already postprocessed, False if not
    :return:
    """
    if force:
        return False

    # Avoid processing the same dir again if we use a process method <> move
    if main_db.MainDB().select("SELECT * FROM tv_episodes WHERE release_name = ?", [dirName]):
        # result.output += logHelper(u"You're trying to post process a dir that's already been processed, skipping", LOGGER.DEBUG)
        return True

    else:
        if main_db.MainDB().select("SELECT * FROM tv_episodes WHERE release_name = ?",
                                   [videofile.rpartition('.')[0]]):
            # result.output += logHelper(u"You're trying to post process a video that's already been processed, skipping", LOGGER.DEBUG)
            return True

        # Needed if we have downloaded the same episode @ different quality
        # But we need to make sure we check the history of the episode we're going to PP, and not others
        np = NameParser(dirName, tryIndexers=True)
        try:
            parse_result = np.parse(dirName)
        except:
            parse_result = False

        search_sql = "SELECT tv_episodes.indexerid, history.resource FROM tv_episodes INNER JOIN history ON history.showid=tv_episodes.showid"  # This part is always the same
        search_sql += " WHERE history.season=tv_episodes.season and history.episode=tv_episodes.episode"
        # If we find a showid, a season number, and one or more episode numbers then we need to use those in the query
        if parse_result and (
                        parse_result.show.indexerid and parse_result.episode_numbers and parse_result.season_number):
            search_sql += " and tv_episodes.showid = '" + str(
                    parse_result.show.indexerid) + "' and tv_episodes.season = '" + str(
                    parse_result.season_number) + "' and tv_episodes.episode = '" + str(
                    parse_result.episode_numbers[0]) + "'"

        search_sql += " and tv_episodes.status IN (" + ",".join([str(x) for x in Quality.DOWNLOADED]) + ")"
        search_sql += " and history.resource LIKE ?"
        if main_db.MainDB().select(search_sql, ['%' + videofile]):
            # result.output += logHelper(u"You're trying to post process a video that's already been processed, skipping", LOGGER.DEBUG)
            return True

    return False


def process_media(processPath, videoFiles, nzbName, process_method, force, is_priority, result):
    """
    Postprocess mediafiles

    :param processPath: Path to postprocess in
    :param videoFiles: Filenames to look for and postprocess
    :param nzbName: Name of NZB file related
    :param process_method: auto/manual
    :param force: Postprocess currently postprocessing file
    :param is_priority: Boolean, is this a priority download
    :param result: Previous results
    """

    processor = None
    for cur_video_file in videoFiles:
        cur_video_file_path = os.path.join(processPath, cur_video_file)

        if already_postprocessed(processPath, cur_video_file, force, result):
            result.output += logHelper("Already Processed " + cur_video_file_path + " : Skipping", sickrage.srCore.srLogger.DEBUG)
            continue

        try:
            processor = post_processor.PostProcessor(cur_video_file_path, nzbName, process_method, is_priority)
            result.result = processor.process
            process_fail_message = ""
        except EpisodePostProcessingFailedException as e:
            result.result = False
            process_fail_message = e.message

        if processor:
            result.output += processor.log

        if result.result:
            result.output += logHelper("Processing succeeded for " + cur_video_file_path)
        else:
            result.output += logHelper("Processing failed for " + cur_video_file_path + ": " + process_fail_message,
                                       sickrage.srCore.srLogger.WARNING)
            result.missedfiles.append(cur_video_file_path + " : Processing failed: " + process_fail_message)
            result.aggresult = False


def get_path_dir_files(dirName, nzbName, proc_type):
    """
    Get files in a path

    :param dirName: Directory to start in
    :param nzbName: NZB file, if present
    :param proc_type: auto/manual
    :return: a tuple of (path,dirs,files)
    """
    path = ""
    dirs = []
    files = []

    if dirName == sickrage.srCore.srConfig.TV_DOWNLOAD_DIR and not nzbName or proc_type == "manual":  # Scheduled Post Processing Active
        # Get at first all the subdir in the dirName
        for path, dirs, files in os.walk(dirName):
            break
    else:
        path, dirs = os.path.split(dirName)  # Script Post Processing
        if not (nzbName is None or nzbName.endswith('.nzb')):
            if os.path.isfile(os.path.join(dirName, nzbName)):
                dirs = []
                files = [os.path.join(dirName, nzbName)]
            else:
                dirs = [dirs]
                files = []
        else:
            dirs = [dirs]
            files = []

    return path, dirs, files


def process_failed(dirName, nzbName, result):
    """Process a download that did not complete correctly"""

    if sickrage.srCore.srConfig.USE_FAILED_DOWNLOADS:
        processor = None

        try:
            processor = failed_processor.FailedProcessor(dirName, nzbName)
            result.result = processor.process()
            process_fail_message = ""
        except FailedPostProcessingFailedException as e:
            result.result = False
            process_fail_message = e

        if processor:
            result.output += processor.log

        if sickrage.srCore.srConfig.DELETE_FAILED and result.result:
            if delete_folder(dirName, check_empty=False):
                result.output += logHelper("Deleted folder: " + dirName, sickrage.srCore.srLogger.DEBUG)

        if result.result:
            result.output += logHelper("Failed Download Processing succeeded: (" + str(nzbName) + ", " + dirName + ")")
        else:
            result.output += logHelper("Failed Download Processing failed: ({}, {}): {}"
                                       .format(nzbName, dirName, process_fail_message), sickrage.srCore.srLogger.WARNING)
