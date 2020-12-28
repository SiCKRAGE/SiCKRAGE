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
import shutil
import stat

import rarfile
from sqlalchemy import or_

import sickrage
from sickrage.core.common import EpisodeStatus
from sickrage.core.databases.main import MainDB
from sickrage.core.enums import ProcessMethod
from sickrage.core.exceptions import EpisodePostProcessingFailedException, FailedPostProcessingFailedException, NoFreeSpaceException
from sickrage.core.helpers import is_media_file, is_rar_file, is_hidden_folder, real_path, is_torrent_or_nzb_file, is_sync_file, get_extension
from sickrage.core.nameparser import InvalidNameException, InvalidShowException, NameParser
from sickrage.core.processors import failed_processor, post_processor
from sickrage.core.tv.show.helpers import get_show_list


class ProcessResult(object):
    def __init__(self, path, process_method=None, process_type='auto'):
        self._output = []
        self._path = path
        self.process_method = process_method or sickrage.app.config.general.process_method
        self.process_type = process_type
        self.video_files = []
        self.missed_files = []
        self.result = True
        self.succeeded = True

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        dir_name = None
        if os.path.isdir(value):
            dir_name = os.path.realpath(value)
            self.log("Processing in folder {0}".format(dir_name), sickrage.app.log.DEBUG)
        elif all([sickrage.app.config.general.tv_download_dir,
                  os.path.isdir(sickrage.app.config.general.tv_download_dir),
                  os.path.normpath(value) == os.path.normpath(sickrage.app.config.general.tv_download_dir)]):
            dir_name = os.path.join(sickrage.app.config.general.tv_download_dir,
                                    os.path.abspath(value).split(os.path.sep)[-1])
            self.log("Trying to use folder: {0} ".format(dir_name), sickrage.app.log.DEBUG)
        else:
            self.log("Unable to figure out what folder to process. "
                     "If your downloader and SiCKRAGE aren't on the same PC "
                     "make sure you fill out your TV download dir in the config.",
                     sickrage.app.log.DEBUG)

        self._path = dir_name

    @property
    def output(self):
        return '\n'.join(self._output)

    def log(self, message, level=None):
        sickrage.app.log.log(level or sickrage.app.log.INFO, message)
        self._output.append(message)

    def clear_log(self):
        self._output = []

    def delete_folder(self, folder, check_empty=True):
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
        if sickrage.app.config.general.tv_download_dir:
            if real_path(folder) == real_path(sickrage.app.config.general.tv_download_dir):
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

    def delete_files(self, processPath, notwantedFiles, force=False):
        """
        Remove files from filesystem

        :param processPath: path to process
        :param notwantedFiles: files we do not want
        :param force: Boolean, force deletion, defaults to false
        """

        if not self.result and force:
            self.log("Forcing deletion of files, even though last result was not success",
                     sickrage.app.log.DEBUG)
        elif not self.result:
            return

        # Delete all file not needed
        for cur_file in notwantedFiles:
            cur_file_path = os.path.join(processPath, cur_file)

            if not os.path.isfile(cur_file_path):
                continue  # Prevent error when a notwantedfiles is an associated files

            self.log("Deleting file %s" % cur_file, sickrage.app.log.DEBUG)

            # check first the read-only attribute
            file_attribute = os.stat(cur_file_path)[0]
            if not file_attribute & stat.S_IWRITE:
                # File is read-only, so make it writeable
                self.log("Changing ReadOnly Flag for file {}".format(cur_file),
                         sickrage.app.log.DEBUG)
                try:
                    os.chmod(cur_file_path, stat.S_IWRITE)
                except OSError as e:
                    self.log("Cannot change permissions of {}: {}".format(cur_file, e.strerror),
                             sickrage.app.log.DEBUG)
            try:
                os.remove(cur_file_path)
            except OSError as e:
                self.log("Unable to delete file {}: {}".format(cur_file, e.strerror),
                         sickrage.app.log.DEBUG)

    def process(self, nzbName=None, force=False, is_priority=None, delete_on=False, failed=False):
        """
        Scans through the files in dir_name and processes whatever media files it finds

        :param nzbName: The NZB name which resulted in this folder being downloaded
        :param force: True to postprocess already postprocessed files
        :param is_priority: whether to replace the file even if it exists at higher quality
        :param delete_on: delete files and folders after they are processed (always happens with move and auto combination)
        :param failed: Boolean for whether or not the download failed
        """

        self.clear_log()

        directories_from_rars = set()

        # If we have a release name (probably from nzbToMedia), and it is a rar/video, only process that file
        if nzbName and (is_media_file(nzbName) or is_rar_file(nzbName)):
            self.log("Processing {}".format(nzbName), sickrage.app.log.INFO)
            generator_to_use = [(self.path, [], [nzbName])]
        else:
            self.log("Processing {}".format(self.path), sickrage.app.log.INFO)
            generator_to_use = os.walk(self.path, followlinks=sickrage.app.config.general.processor_follow_symlinks)

        rar_files = []
        for current_directory, directory_names, file_names in generator_to_use:
            self.result = True

            file_names = [f for f in file_names if not is_torrent_or_nzb_file(f)]
            rar_files = [x for x in file_names if is_rar_file(os.path.join(current_directory, x))]
            if rar_files:
                extracted_directories = self.unrar(current_directory, rar_files, force)
                if extracted_directories:
                    for extracted_directory in extracted_directories:
                        if extracted_directory.split(current_directory)[-1] not in directory_names:
                            self.log(
                                "Adding extracted directory to the list of directories to process: {0}".format(
                                    extracted_directory), sickrage.app.log.DEBUG
                            )
                            directories_from_rars.add(extracted_directory)

            if not self.validateDir(current_directory, nzbName, failed):
                continue

            video_files = list(filter(is_media_file, file_names))
            if video_files:
                try:
                    self.process_media(current_directory, video_files, nzbName, self.process_method, force, is_priority)
                except NoFreeSpaceException:
                    continue
            else:
                self.result = False

            # Delete all file not needed and avoid deleting files if Manual PostProcessing
            if not (self.process_method == ProcessMethod.MOVE and self.result) or (self.process_type == "manual" and not delete_on):
                continue

            # Check for unwanted files
            unwanted_files = list(
                filter(
                    lambda x: x not in video_files and get_extension(x) not in sickrage.app.config.general.allowed_extensions,
                    file_names)
            )

            if unwanted_files:
                self.log("Found unwanted files: {0}".format(unwanted_files), sickrage.app.log.DEBUG)

            self.delete_folder(os.path.join(current_directory, '@eaDir'), False)
            self.delete_files(current_directory, unwanted_files)
            if self.delete_folder(current_directory, check_empty=not delete_on):
                self.log("Deleted folder: {0}".format(current_directory), sickrage.app.log.DEBUG)

        method_fallback = (ProcessMethod.MOVE, self.process_method)[self.process_method in (ProcessMethod.MOVE, ProcessMethod.COPY)]

        delete_rar_contents = any([sickrage.app.config.general.del_rar_contents and self.process_type != 'manual',
                                   not sickrage.app.config.general.del_rar_contents and self.process_type == 'auto' and method_fallback == ProcessMethod.MOVE,
                                   self.process_type == 'manual' and delete_on])

        for directory_from_rar in directories_from_rars:
            ProcessResult(directories_from_rars, self.process_method, self.process_type).process(
                nzbName=os.path.basename(directory_from_rar),
                force=force,
                is_priority=is_priority,
                delete_on=delete_rar_contents,
                failed=failed
            )

            # Delete rar file only if the extracted dir was successfully processed
            if self.process_type == 'auto' and method_fallback == ProcessMethod.MOVE or self.process_type == 'manual' and delete_on:
                this_rar = [rar_file for rar_file in rar_files if
                            os.path.basename(directory_from_rar) == rar_file.rpartition('.')[0]]
                self.delete_files(self.path, this_rar)

        self.log(("Processing Failed", "Successfully processed")[self.succeeded],
                 (sickrage.app.log.WARNING, sickrage.app.log.INFO)[self.succeeded])

        if self.missed_files:
            self.log("Some items were not processed.")
            for missed_file in self.missed_files:
                self.log(missed_file)

        return self.output

    def validateDir(self, process_path, release_name, failed):
        """
        Check if directory is valid for processing

        :param process_path: Directory to check
        :param release_name: Original NZB/Torrent name
        :param failed: Previously failed objects
        :return: True if dir is valid for processing, False if not
        """

        self.log("Processing folder " + process_path, sickrage.app.log.DEBUG)

        upper_name = os.path.basename(process_path).upper()
        if upper_name.startswith('_FAILED_') or upper_name.endswith('_FAILED_'):
            self.log("The directory name indicates it failed to extract.", sickrage.app.log.DEBUG)
            failed = True
        elif upper_name.startswith('_UNDERSIZED_') or upper_name.endswith('_UNDERSIZED_'):
            self.log(
                "The directory name indicates that it was previously rejected for being undersized.",
                sickrage.app.log.DEBUG)
            failed = True
        elif upper_name.startswith('_UNPACK') or upper_name.endswith('_UNPACK'):
            self.log(
                "The directory name indicates that this release is in the process of being unpacked.",
                sickrage.app.log.DEBUG)
            self.missed_files.append("{0} : Being unpacked".format(process_path))
            return False

        if failed:
            self.process_failed(process_path, release_name)
            self.missed_files.append("{0} : Failed download".format(process_path))
            return False

        if sickrage.app.config.general.tv_download_dir and real_path(process_path) != real_path(
                sickrage.app.config.general.tv_download_dir) and is_hidden_folder(process_path):
            self.log("Ignoring hidden folder: {0}".format(process_path), sickrage.app.log.DEBUG)
            self.missed_files.append("{0} : Hidden folder".format(process_path))
            return False

        # make sure the dir isn't inside a show dir
        for show in get_show_list():
            if process_path.lower().startswith(os.path.realpath(show.location).lower() + os.sep) or \
                    process_path.lower() == os.path.realpath(show.location).lower():
                self.log("Cannot process an episode that's already been moved to its show dir, skipping " + process_path, sickrage.app.log.WARNING)
                return False

        for current_directory, directory_names, file_names in os.walk(process_path, topdown=False,
                                                                      followlinks=sickrage.app.config.general.processor_follow_symlinks):
            sync_files = list(filter(is_sync_file, file_names))
            if sync_files and sickrage.app.config.general.postpone_if_sync_files:
                self.log("Found temporary sync files: {0} in path: {1}".format(sync_files,
                                                                               os.path.join(
                                                                                   process_path,
                                                                                   sync_files[
                                                                                       0])))
                self.log("Skipping post processing for folder: {0}".format(process_path))
                self.missed_files.append("{0} : Sync files found".format(os.path.join(process_path, sync_files[0])))
                continue

            found_files = list(filter(is_media_file, file_names))
            if sickrage.app.config.general.unpack == 1:
                found_files += list(filter(is_rar_file, file_names))

            if current_directory != sickrage.app.config.general.tv_download_dir and found_files:
                found_files.append(os.path.basename(current_directory))

            for found_file in found_files:
                try:
                    NameParser().parse(found_file, cache_result=False)
                except (InvalidNameException, InvalidShowException) as e:
                    pass
                else:
                    return True

        self.log("Folder {} : No processable items found in folder".format(process_path),
                 sickrage.app.log.DEBUG)
        return False

    def unrar(self, path, rar_files, force):
        """
        Extracts RAR files

        :param path: Path to look for files in
        :param rar_files: Names of RAR files
        :param force: process currently processing items
        :return: List of unpacked file names
        """

        unpacked_dirs = []

        if sickrage.app.config.general.unpack == 1 and rar_files:
            self.log("Packed Releases detected: {0}".format(rar_files), sickrage.app.log.DEBUG)
            for archive in rar_files:
                failure = None
                rar_handle = None
                try:
                    archive_path = os.path.join(path, archive)
                    if self.already_postprocessed(path, archive, force):
                        self.log("Archive file already post-processed, extraction skipped: {}".format
                                 (archive_path), sickrage.app.log.DEBUG)
                        continue

                    if not is_rar_file(archive_path):
                        continue

                    self.log(
                        "Checking if archive is valid and contains a video: {}".format(archive_path),
                        sickrage.app.log.DEBUG)
                    rar_handle = rarfile.RarFile(archive_path)
                    if rar_handle.needs_password():
                        # TODO: Add support in settings for a list of passwords to try here with rar_handle.set_password(x)
                        self.log('Archive needs a password, skipping: {0}'.format(archive_path))
                        continue

                    # If there are no video files in the rar, don't extract it
                    rar_media_files = list(filter(is_media_file, rar_handle.namelist()))
                    if not rar_media_files:
                        continue

                    rar_release_name = archive.rpartition('.')[0]

                    # Choose the directory we'll unpack to:
                    if sickrage.app.config.general.unpack_dir and os.path.isdir(sickrage.app.config.general.unpack_dir):
                        unpack_base_dir = sickrage.app.config.general.unpack_dir
                    else:
                        unpack_base_dir = path
                        if sickrage.app.config.general.unpack_dir:  # Let user know if we can't unpack there
                            self.log('Unpack directory cannot be verified. Using {}'.format(path),
                                     sickrage.app.log.DEBUG)

                    # Fix up the list for checking if already processed
                    rar_media_files = [os.path.join(unpack_base_dir, rar_release_name, rar_media_file) for
                                       rar_media_file in
                                       rar_media_files]

                    skip_rar = False
                    for rar_media_file in rar_media_files:
                        check_path, check_file = os.path.split(rar_media_file)
                        if self.already_postprocessed(check_path, check_file, force):
                            self.log(
                                "Archive file already post-processed, extraction skipped: {0}".format
                                (rar_media_file), sickrage.app.log.DEBUG)
                            skip_rar = True
                            break

                    if skip_rar:
                        continue

                    rar_extract_path = os.path.join(unpack_base_dir, rar_release_name)
                    self.log("Unpacking archive: {0}".format(archive), sickrage.app.log.DEBUG)
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
                               'Unpacking Failed with Invalid Rar Archive Usage. Is unrar installed and on the system '
                               'PATH?')
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
                    self.log('Failed to extract the archive {}: {}'.format(archive, failure[0]),
                             sickrage.app.log.WARNING)
                    self.missed_files.append('{} : Unpacking failed: {}'.format(archive, failure[1]))
                    self.result = False
                    continue

        return unpacked_dirs

    def already_postprocessed(self, dirName, videofile, force):
        """
        Check if we already post processed a file

        :param dirName: Directory a file resides in
        :param videofile: File name
        :param force: Force checking when already checking (currently unused)
        :return:
        """
        if force:
            return False

        session = sickrage.app.main_db.session()

        # Avoid processing the same dir again if we use a process method <> move
        if session.query(MainDB.TVEpisode).filter(
                or_(MainDB.TVEpisode.release_name.contains(dirName), MainDB.TVEpisode.release_name.contains(videofile))).count() > 0:
            return True

        # Needed if we have downloaded the same episode @ different quality
        # But we need to make sure we check the history of the episode we're going to PP, and not others
        np = NameParser(dirName)
        try:
            parse_result = np.parse(dirName)
        except:
            parse_result = False

        for h in session.query(MainDB.History).filter(MainDB.History.resource.endswith(videofile)):
            for e in session.query(MainDB.TVEpisode).filter_by(series_id=h.series_id, season=h.season, episode=h.episode).filter(
                    MainDB.TVEpisode.status.in_(EpisodeStatus.composites(EpisodeStatus.DOWNLOADED))):
                if parse_result and (parse_result.series_id and parse_result.episode_numbers and parse_result.season_number):
                    if e.series_id == int(parse_result.series_id) and e.season == int(parse_result.season_number and e.episode) == int(
                            parse_result.episode_numbers[0]):
                        return True
                else:
                    return True

        # Checks for processed file marker
        if os.path.isfile(os.path.join(dirName, videofile + '.sr_processed')):
            return True

        return False

    def process_media(self, processPath, videoFiles, nzbName, process_method, force, is_priority):
        """
        Postprocess mediafiles

        :param processPath: Path to postprocess in
        :param videoFiles: Filenames to look for and postprocess
        :param nzbName: Name of NZB file related
        :param process_method: auto/manual
        :param force: Postprocess currently postprocessing file
        :param is_priority: Boolean, is this a priority download
        """

        processor = None
        for cur_video_file in videoFiles:
            cur_video_file_path = os.path.join(processPath, cur_video_file)

            if self.already_postprocessed(processPath, cur_video_file, force):
                self.log("Skipping already processed file: {0}".format(cur_video_file), sickrage.app.log.DEBUG)
                continue

            try:
                processor = post_processor.PostProcessor(cur_video_file_path, nzbName, process_method, is_priority)
                self.result = processor.process()
                process_fail_message = ""
            except EpisodePostProcessingFailedException as e:
                self.result = False
                process_fail_message = "{}".format(e)

            if processor:
                self._output.append(processor.log)

            if self.result:
                self.log("Processing succeeded for " + cur_video_file_path)
            else:
                self.log("Processing failed for {0}: {1}".format(cur_video_file_path, process_fail_message), sickrage.app.log.WARNING)
                self.missed_files.append("{0} : Processing failed: {1}".format(cur_video_file_path, process_fail_message))
                self.succeeded = False

    def process_failed(self, dirName, nzbName):
        """Process a download that did not complete correctly"""

        try:
            processor = failed_processor.FailedProcessor(dirName, nzbName)
            self.result = processor.process()
            process_fail_message = ""
        except FailedPostProcessingFailedException as e:
            processor = None
            self.result = False
            process_fail_message = e

        if processor:
            self._output.append(processor.log)

        if sickrage.app.config.failed_downloads.enable and self.result:
            if self.delete_folder(dirName, check_empty=False):
                self.log("Deleted folder: " + dirName, sickrage.app.log.DEBUG)

        if self.result:
            self.log(
                "Failed Download Processing succeeded: (" + str(nzbName) + ", " + dirName + ")")
        else:
            self.log("Failed Download Processing failed: ({}, {}): {}"
                     .format(nzbName, dirName, process_fail_message),
                     sickrage.app.log.WARNING)
