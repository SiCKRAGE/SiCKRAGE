# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import os
import shutil
import stat

import rarfile
from sqlalchemy import or_, literal

import sickrage
from sickrage.core.common import Quality
from sickrage.core.databases.main import MainDB
from sickrage.core.exceptions import EpisodePostProcessingFailedException, \
    FailedPostProcessingFailedException, NoFreeSpaceException
from sickrage.core.helpers import is_media_file, is_rar_file, is_hidden_folder, real_path, is_torrent_or_nzb_file, \
    is_sync_file
from sickrage.core.nameparser import InvalidNameException, InvalidShowException, \
    NameParser
from sickrage.core.processors import failed_processor, post_processor


class ProcessResult(object):
    def __init__(self):
        self.result = True
        self.output = ''
        self.missed_files = []
        self.agg_result = True

    def __str__(self):
        return self.output


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
    if sickrage.app.config.tv_download_dir:
        if real_path(folder) == real_path(sickrage.app.config.tv_download_dir):
            return False

    # check if it's empty folder when wanted checked
    try:
        if check_empty:
            check_files = os.listdir(folder)
            if check_files:
                sickrage.app.log.info(
                    "Not deleting folder {} found the following files: {}".format(folder, check_files))
                return False

            sickrage.app.log.info("Deleting folder (if it's empty): " + folder)
            shutil.rmtree(folder)
        else:
            sickrage.app.log.info("Deleting folder: " + folder)
            shutil.rmtree(folder)
    except (OSError, IOError) as e:
        sickrage.app.log.warning("Warning: unable to delete folder: {}: {}".format(folder, e))
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
        result.output += logHelper("Forcing deletion of files, even though last result was not success",
                                   sickrage.app.log.DEBUG)
    elif not result.result:
        return

    # Delete all file not needed
    for cur_file in notwantedFiles:
        cur_file_path = os.path.join(processPath, cur_file)

        if not os.path.isfile(cur_file_path):
            continue  # Prevent error when a notwantedfiles is an associated files

        result.output += logHelper("Deleting file %s" % cur_file, sickrage.app.log.DEBUG)

        # check first the read-only attribute
        file_attribute = os.stat(cur_file_path)[0]
        if not file_attribute & stat.S_IWRITE:
            # File is read-only, so make it writeable
            result.output += logHelper("Changing ReadOnly Flag for file {}".format(cur_file), sickrage.app.log.DEBUG)
            try:
                os.chmod(cur_file_path, stat.S_IWRITE)
            except OSError as e:
                result.output += logHelper("Cannot change permissions of {}: {}".format(cur_file, e.strerror),
                                           sickrage.app.log.DEBUG)
        try:
            os.remove(cur_file_path)
        except OSError as e:
            result.output += logHelper("Unable to delete file {}: {}".format(cur_file, e.strerror),
                                       sickrage.app.log.DEBUG)


def logHelper(logMessage, logLevel=None):
    sickrage.app.log.log(logLevel or sickrage.app.log.INFO, logMessage)
    return logMessage + "\n"


def processDir(dirName, nzbName=None, process_method=None, force=False, is_priority=None, delete_on=False, failed=False,
               proc_type="auto", **kwargs):
    """
    Scans through the files in dirName and processes whatever media files it finds

    :param dirName: The folder name to look in
    :param nzbName: The NZB name which resulted in this folder being downloaded
    :param force: True to postprocess already postprocessed files
    :param is_priority: whether to replace the file even if it exists at higher quality
    :param delete_on: delete files and folders after they are processed (always happens with move and auto combination)
    :param failed: Boolean for whether or not the download failed
    :param proc_type: Type of postprocessing auto or manual
    """

    result = ProcessResult()

    # if they passed us a real dir then assume it's the one we want
    if os.path.isdir(dirName):
        dirName = os.path.realpath(dirName)
        result.output += logHelper("Processing in folder {0}".format(dirName), sickrage.app.log.DEBUG)

    # if the client and SickRage are not on the same machine translate the directory into a network directory
    elif all([sickrage.app.config.tv_download_dir,
              os.path.isdir(sickrage.app.config.tv_download_dir),
              os.path.normpath(dirName) == os.path.normpath(sickrage.app.config.tv_download_dir)]):
        dirName = os.path.join(sickrage.app.config.tv_download_dir, os.path.abspath(dirName).split(os.path.sep)[-1])
        result.output += logHelper("Trying to use folder: {0} ".format(dirName), sickrage.app.log.DEBUG)

    # if we didn't find a real dir then quit
    if not os.path.isdir(dirName):
        result.output += logHelper("Unable to figure out what folder to process. "
                                   "If your downloader and SiCKRAGE aren't on the same PC "
                                   "make sure you fill out your TV download dir in the config.",
                                   sickrage.app.log.DEBUG)
        return result

    process_method = process_method or sickrage.app.config.process_method

    directories_from_rars = set()

    # If we have a release name (probably from nzbToMedia), and it is a rar/video, only process that file
    if nzbName and (is_media_file(nzbName) or is_rar_file(nzbName)):
        result.output += logHelper("Processing {}".format(nzbName), sickrage.app.log.INFO)
        generator_to_use = [(dirName, [], [nzbName])]
    else:
        result.output += logHelper("Processing {}".format(dirName), sickrage.app.log.INFO)
        generator_to_use = os.walk(dirName, followlinks=sickrage.app.config.processor_follow_symlinks)

    rar_files = []
    for current_directory, directory_names, file_names in generator_to_use:
        result.result = True

        file_names = [f for f in file_names if not is_torrent_or_nzb_file(f)]
        rar_files = [x for x in file_names if is_rar_file(os.path.join(current_directory, x))]
        if rar_files:
            extracted_directories = unrar(current_directory, rar_files, force, result)
            if extracted_directories:
                for extracted_directory in extracted_directories:
                    if extracted_directory.split(current_directory)[-1] not in directory_names:
                        result.output += logHelper(
                            "Adding extracted directory to the list of directories to process: {0}".format(
                                extracted_directory), sickrage.app.log.DEBUG
                        )
                        directories_from_rars.add(extracted_directory)

        if not validateDir(current_directory, nzbName, failed, result):
            continue

        video_files = list(filter(is_media_file, file_names))
        if video_files:
            try:
                process_media(current_directory, video_files, nzbName, process_method, force, is_priority, result)
            except NoFreeSpaceException:
                continue
        else:
            result.result = False

        # Delete all file not needed and avoid deleting files if Manual PostProcessing
        if not (process_method == "move" and result.result) or (proc_type == "manual" and not delete_on):
            continue

        # Check for unwanted files
        unwanted_files = list(filter(lambda x: x in video_files + rar_files, file_names))
        if unwanted_files:
            result.output += logHelper("Found unwanted files: {0}".format(unwanted_files), sickrage.app.log.DEBUG)

        delete_folder(os.path.join(current_directory, '@eaDir'), False)
        delete_files(current_directory, unwanted_files, result)
        if delete_folder(current_directory, check_empty=not delete_on):
            result.output += logHelper("Deleted folder: {0}".format(current_directory), sickrage.app.log.DEBUG)

    # For processing extracted rars, only allow methods 'move' and 'copy'.
    # On different methods fall back to 'move'.
    method_fallback = ('move', process_method)[process_method in ('move', 'copy')]

    # auto post-processing deletes rar content by default if method is 'move',
    # sickbeard.DELRARCONTENTS allows to override even if method is NOT 'move'
    # manual post-processing will only delete when prompted by delete_on
    delete_rar_contents = any([sickrage.app.config.delrarcontents and proc_type != 'manual',
                               not sickrage.app.config.delrarcontents and proc_type == 'auto' and method_fallback == 'move',
                               proc_type == 'manual' and delete_on])

    for directory_from_rar in directories_from_rars:
        processDir(
            dirName=directory_from_rar,
            nzbName=os.path.basename(directory_from_rar),
            process_method=method_fallback,
            force=force,
            is_priority=is_priority,
            delete_on=delete_rar_contents,
            failed=failed,
            proc_type=proc_type
        )

        # Delete rar file only if the extracted dir was successfully processed
        if proc_type == 'auto' and method_fallback == 'move' or proc_type == 'manual' and delete_on:
            this_rar = [rar_file for rar_file in rar_files if
                        os.path.basename(directory_from_rar) == rar_file.rpartition('.')[0]]
            delete_files(dirName, this_rar, result)  # Deletes only if result.result == True

    result.output += logHelper(("Processing Failed", "Successfully processed")[result.agg_result],
                               (sickrage.app.log.WARNING, sickrage.app.log.INFO)[result.agg_result])
    if result.missed_files:
        result.output += logHelper("Some items were not processed.")
        for missed_file in result.missed_files:
            result.output += logHelper(missed_file)

    return result


def validateDir(process_path, release_name, failed, result):
    """
    Check if directory is valid for processing

    :param process_path: Directory to check
    :param release_name: Original NZB/Torrent name
    :param failed: Previously failed objects
    :param result: Previous results
    :return: True if dir is valid for processing, False if not
    """

    result.output += logHelper("Processing folder " + process_path, sickrage.app.log.DEBUG)

    upper_name = os.path.basename(process_path).upper()
    if upper_name.startswith('_FAILED_') or upper_name.endswith('_FAILED_'):
        result.output += logHelper("The directory name indicates it failed to extract.", sickrage.app.log.DEBUG)
        failed = True
    elif upper_name.startswith('_UNDERSIZED_') or upper_name.endswith('_UNDERSIZED_'):
        result.output += logHelper("The directory name indicates that it was previously rejected for being undersized.",
                                   sickrage.app.log.DEBUG)
        failed = True
    elif upper_name.startswith('_UNPACK') or upper_name.endswith('_UNPACK'):
        result.output += logHelper(
            "The directory name indicates that this release is in the process of being unpacked.",
            sickrage.app.log.DEBUG)
        result.missed_files.append("{0} : Being unpacked".format(process_path))
        return False

    if failed:
        process_failed(process_path, release_name, result)
        result.missed_files.append("{0} : Failed download".format(process_path))
        return False

    if sickrage.app.config.tv_download_dir and real_path(process_path) != real_path(
            sickrage.app.config.tv_download_dir) and is_hidden_folder(process_path):
        result.output += logHelper("Ignoring hidden folder: {0}".format(process_path), sickrage.app.log.DEBUG)
        result.missed_files.append("{0} : Hidden folder".format(process_path))
        return False

    # make sure the dir isn't inside a show dir
    for show in sickrage.app.showlist:
        if process_path.lower().startswith(os.path.realpath(show.location).lower() + os.sep) or \
                process_path.lower() == os.path.realpath(show.location).lower():
            result.output += logHelper(
                "Cannot process an episode that's already been moved to its show dir, skipping " + process_path,
                sickrage.app.log.WARNING)
            return False

    for current_directory, directory_names, file_names in os.walk(process_path, topdown=False,
                                                                  followlinks=sickrage.app.config.processor_follow_symlinks):
        sync_files = list(filter(is_sync_file, file_names))
        if sync_files and sickrage.app.config.postpone_if_sync_files:
            result.output += logHelper("Found temporary sync files: {0} in path: {1}".format(sync_files,
                                                                                             os.path.join(process_path,
                                                                                                          sync_files[
                                                                                                              0])))
            result.output += logHelper("Skipping post processing for folder: {0}".format(process_path))
            result.missed_files.append("{0} : Sync files found".format(os.path.join(process_path, sync_files[0])))
            continue

        found_files = list(filter(is_media_file, file_names))
        if sickrage.app.config.unpack == 1:
            found_files += list(filter(is_rar_file, file_names))

        if current_directory != sickrage.app.config.tv_download_dir and found_files:
            found_files.append(os.path.basename(current_directory))

        for found_file in found_files:
            try:
                NameParser().parse(found_file, cache_result=False)
            except (InvalidNameException, InvalidShowException) as e:
                pass
            else:
                return True

    result.output += logHelper("{0} : No processable items found in folder".format(process_path),
                               sickrage.app.log.DEBUG)
    return False


def unrar(path, rar_files, force, result):
    """
    Extracts RAR files

    :param path: Path to look for files in
    :param rar_files: Names of RAR files
    :param force: process currently processing items
    :param result: Previous results
    :return: List of unpacked file names
    """

    unpacked_dirs = []

    if sickrage.app.config.unpack == 1 and rar_files:
        result.output += logHelper("Packed Releases detected: {0}".format(rar_files), sickrage.app.log.DEBUG)
        for archive in rar_files:
            failure = None
            rar_handle = None
            try:
                archive_path = os.path.join(path, archive)
                if already_postprocessed(path, archive, force, result):
                    result.output += logHelper("Archive file already post-processed, extraction skipped: {}".format
                                               (archive_path), sickrage.app.log.DEBUG)
                    continue

                if not is_rar_file(archive_path):
                    continue

                result.output += logHelper("Checking if archive is valid and contains a video: {}".format(archive_path),
                                           sickrage.app.log.DEBUG)
                rar_handle = rarfile.RarFile(archive_path)
                if rar_handle.needs_password():
                    # TODO: Add support in settings for a list of passwords to try here with rar_handle.set_password(x)
                    result.output += logHelper('Archive needs a password, skipping: {0}'.format(archive_path))
                    continue

                # If there are no video files in the rar, don't extract it
                rar_media_files = list(filter(is_media_file, rar_handle.namelist()))
                if not rar_media_files:
                    continue

                rar_release_name = archive.rpartition('.')[0]

                # Choose the directory we'll unpack to:
                if sickrage.app.config.unpack_dir and os.path.isdir(sickrage.app.config.unpack_dir):
                    unpack_base_dir = sickrage.app.config.unpack_dir
                else:
                    unpack_base_dir = path
                    if sickrage.app.config.unpack_dir:  # Let user know if we can't unpack there
                        result.output += logHelper('Unpack directory cannot be verified. Using {}'.format(path),
                                                   sickrage.app.log.DEBUG)

                # Fix up the list for checking if already processed
                rar_media_files = [os.path.join(unpack_base_dir, rar_release_name, rar_media_file) for rar_media_file in
                                   rar_media_files]

                skip_rar = False
                for rar_media_file in rar_media_files:
                    check_path, check_file = os.path.split(rar_media_file)
                    if already_postprocessed(check_path, check_file, force, result):
                        result.output += logHelper(
                            "Archive file already post-processed, extraction skipped: {0}".format
                            (rar_media_file), sickrage.app.log.DEBUG)
                        skip_rar = True
                        break

                if skip_rar:
                    continue

                rar_extract_path = os.path.join(unpack_base_dir, rar_release_name)
                result.output += logHelper("Unpacking archive: {0}".format(archive), sickrage.app.log.DEBUG)
                rar_handle.extractall(path=rar_extract_path)
                unpacked_dirs.append(rar_extract_path)

            except rarfile.RarCRCError:
                failure = ('Archive Broken', 'Unpacking failed because of a CRC error')
            except rarfile.RarWrongPassword:
                failure = ('Incorrect RAR Password', 'Unpacking failed because of an Incorrect Rar Password')
            except rarfile.PasswordRequired:
                failure = ('Rar is password protected', 'Unpacking failed because it needs a password')
            except rarfile.RarOpenError:
                failure = ('Rar Open Error, check the parent folder and destination file permissions.',
                           'Unpacking failed with a File Open Error (file permissions?)')
            except rarfile.RarExecError:
                failure = ('Invalid Rar Archive Usage',
                           'Unpacking Failed with Invalid Rar Archive Usage. Is unrar installed and on the system PATH?')
            except rarfile.BadRarFile:
                failure = ('Invalid Rar Archive', 'Unpacking Failed with an Invalid Rar Archive Error')
            except rarfile.NeedFirstVolume:
                continue
            except (Exception, rarfile.Error) as e:
                failure = (e, 'Unpacking failed')
            finally:
                if rar_handle:
                    del rar_handle

            if failure:
                result.output += logHelper('Failed to extract the archive {}: {}'.format(archive, failure[0]),
                                           sickrage.app.log.WARNING)
                result.missed_files.append('{} : Unpacking failed: {}'.format(archive, failure[1]))
                result.result = False
                continue

    return unpacked_dirs


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
    if MainDB.TVEpisode.query().filter(or_(literal(dirName).contains(MainDB.TVEpisode.release_name),
                                           literal(videofile).contains(MainDB.TVEpisode.release_name))):
        return True

    # Needed if we have downloaded the same episode @ different quality
    # But we need to make sure we check the history of the episode we're going to PP, and not others
    np = NameParser(dirName)
    try:
        parse_result = np.parse(dirName)
    except:
        parse_result = False

    for h in MainDB.History.query().filter(MainDB.History.resource.endswith(videofile)):
        for e in MainDB.TVEpisode.query().filter_by(showid=h.showid, season=h.season, episode=h.episode).filter(
                MainDB.TVEpisode.status.in_(Quality.DOWNLOADED)):
            # If we find a showid, a season number, and one or more episode numbers then we need to use those in the
            # query
            if parse_result and (parse_result.indexerid and parse_result.episode_numbers and
                                 parse_result.season_number):
                if e.showid == int(parse_result.indexerid) and \
                        e.season == int(parse_result.season_number and
                                        e.episode) == int(parse_result.episode_numbers[0]):
                    return True
            else:
                return True

    # Checks for processed file marker
    if os.path.isfile(os.path.join(dirName, videofile + '.sr_processed')):
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
            result.output += logHelper("Skipping already processed file: {0}".format(cur_video_file),
                                       sickrage.app.log.DEBUG)
            continue

        try:
            processor = post_processor.PostProcessor(cur_video_file_path, nzbName, process_method, is_priority)
            result.result = processor.process
            process_fail_message = ""
        except EpisodePostProcessingFailedException as e:
            result.result = False
            process_fail_message = "{}".format(e)

        if processor:
            result.output += processor.log

        if result.result:
            result.output += logHelper("Processing succeeded for " + cur_video_file_path)
        else:
            result.output += logHelper(
                "Processing failed for {0}: {1}".format(cur_video_file_path, process_fail_message),
                sickrage.app.log.WARNING)
            result.missed_files.append("{0} : Processing failed: {1}".format(cur_video_file_path, process_fail_message))
            result.agg_result = False


def process_failed(dirName, nzbName, result):
    """Process a download that did not complete correctly"""

    try:
        processor = failed_processor.FailedProcessor(dirName, nzbName)
        result.result = processor.process()
        process_fail_message = ""
    except FailedPostProcessingFailedException as e:
        processor = None
        result.result = False
        process_fail_message = e

    if processor:
        result.output += processor.log

    if sickrage.app.config.delete_failed and result.result:
        if delete_folder(dirName, check_empty=False):
            result.output += logHelper("Deleted folder: " + dirName, sickrage.app.log.DEBUG)

    if result.result:
        result.output += logHelper("Failed Download Processing succeeded: (" + str(nzbName) + ", " + dirName + ")")
    else:
        result.output += logHelper("Failed Download Processing failed: ({}, {}): {}"
                                   .format(nzbName, dirName, process_fail_message),
                                   sickrage.app.log.WARNING)
