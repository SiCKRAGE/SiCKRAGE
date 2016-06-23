# Author: echel0n <echel0n@sickrage.ca>
# URL: http://github.com/SiCKRAGETV/SickRage/
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

import datetime
import io
import os
import platform
import re
import stat
import subprocess
import tarfile
import threading
import time
import traceback

import github

import sickrage
from sickrage.core.helpers import backupSR, removetree
from sickrage.notifiers import srNotifiers


class srVersionUpdater(object):
    """
    Version check class meant to run as a thread object with the sr scheduler.
    """

    def __init__(self, **kwargs):
        self.name = "VERSIONUPDATER"
        self.amActive = False
        self.updater = self.find_install_type()

    def run(self, force=False):
        if self.amActive:
            return

        self.amActive = True

        # set thread name
        threading.currentThread().setName(self.name)

        try:
            if self.updater:
                if self.check_for_new_version(force):
                    if sickrage.srCore.srConfig.AUTO_UPDATE:
                        sickrage.srCore.srLogger.info("New update found for SiCKRAGE, starting auto-updater ...")
                        sickrage.srCore.srNotifications.message('New update found for SiCKRAGE, starting auto-updater')
                        if self.run_backup_if_safe() is True:
                            if self.update():
                                sickrage.srCore.srLogger.info("Update was successful!")
                                sickrage.srCore.srNotifications.message('Update was successful')
                                sickrage.srCore.shutdown(restart=True)
                            else:
                                sickrage.srCore.srLogger.info("Update failed!")
                                sickrage.srCore.srNotifications.message('Update failed!')

                self.check_for_new_news(force)
        finally:
            self.amActive = False

    def run_backup_if_safe(self):
        return self.safe_to_update() is True and self._runbackup() is True

    def _runbackup(self):
        # Do a system backup before update
        sickrage.srCore.srLogger.info("Config backup in progress...")
        sickrage.srCore.srNotifications.message('Backup', 'Config backup in progress...')
        try:
            backupDir = os.path.join(sickrage.DATA_DIR, 'backup')
            if not os.path.isdir(backupDir):
                os.mkdir(backupDir)

            if self._keeplatestbackup(backupDir) and backupSR(backupDir):
                sickrage.srCore.srLogger.info("Config backup successful, updating...")
                sickrage.srCore.srNotifications.message('Backup', 'Config backup successful, updating...')
                return True
            else:
                sickrage.srCore.srLogger.error("Config backup failed, aborting update")
                sickrage.srCore.srNotifications.message('Backup', 'Config backup failed, aborting update')
                return False
        except Exception as e:
            sickrage.srCore.srLogger.error('Update: Config backup failed. Error: %s' % e)
            sickrage.srCore.srNotifications.message('Backup', 'Config backup failed, aborting update')
            return False

    @staticmethod
    def _keeplatestbackup(backupDir=None):
        if not backupDir:
            return False

        import glob
        files = glob.glob(os.path.join(backupDir, '*.zip'))
        if not files:
            return True

        now = time.time()
        newest = files[0], now - os.path.getctime(files[0])
        for f in files[1:]:
            age = now - os.path.getctime(f)
            if age < newest[1]:
                newest = f, age
        files.remove(newest[0])

        for f in files:
            os.remove(f)

        return True

    def safe_to_update(self):
        def postprocessor_safe():
            if not sickrage.srCore.STARTED:
                return True

            if not sickrage.srCore.srScheduler.get_job('POSTPROCESSOR').func.im_self.amActive:
                sickrage.srCore.srLogger.debug("We can proceed with the update. Post-Processor is not running")
                return True
            else:
                sickrage.srCore.srLogger.debug("We can't proceed with the update. Post-Processor is running")
                return False

        def showupdate_safe():
            if not sickrage.srCore.STARTED:
                return True

            if not sickrage.srCore.srScheduler.get_job('SHOWUPDATER').func.im_self.amActive:
                sickrage.srCore.srLogger.debug("We can proceed with the update. Shows are not being updated")
                return True
            else:
                sickrage.srCore.srLogger.debug("We can't proceed with the update. Shows are being updated")
                return False

        if postprocessor_safe() and showupdate_safe():
            sickrage.srCore.srLogger.debug("Safely proceeding with auto update")
            return True

        sickrage.srCore.srLogger.debug("Unsafe to auto update currently, aborted")

    @staticmethod
    def find_install_type():
        """
        Determines how this copy of sr was installed.

        returns: type of installation. Possible values are:

            'git': running from source using git
            'source': running from source without git
        """

        import pip

        if os.path.isdir(os.path.join(os.path.dirname(sickrage.PROG_DIR), '.git')):
            # git install
            return GitUpdateManager()
        else:
            for dist in pip.get_installed_distributions():
                if dist.project_name.lower() == 'sickrage':
                    # pip install
                    return PipUpdateManager()
            # git source install
            return SourceUpdateManager()

    def check_for_new_version(self, force=False):
        """
        Checks the internet for a newer version.

        returns: bool, True for new version or False for no new version.
        :param force: if true the VERSION_NOTIFY setting will be ignored and a check will be forced
        """

        if not self.updater or not any([sickrage.srCore.srConfig.VERSION_NOTIFY, force]):
            return False

        if self.updater.need_update():
            self.updater.set_newest_text()
            return True

    def check_for_new_news(self):
        """
        Checks server for the latest news.

        returns: unicode, a copy of the news

        force: ignored
        """

        # Grab a copy of the news
        try:
            news = sickrage.srCore.srWebSession.get(sickrage.srCore.srConfig.NEWS_URL).text
        except Exception:
            news = ""

        if news:
            dates = re.finditer(r'^####(\d{4}-\d{2}-\d{2})####$', news, re.M)
            if not list(dates):
                return news or ''

            try:
                last_read = datetime.datetime.strptime(sickrage.srCore.srConfig.NEWS_LAST_READ, '%Y-%m-%d')
            except:
                last_read = 0

            sickrage.srCore.srConfig.NEWS_UNREAD = 0
            got_latest = False
            for match in dates:
                if not got_latest:
                    got_latest = True
                    sickrage.srCore.srConfig.NEWS_LATEST = match.group(1)

                try:
                    if datetime.datetime.strptime(match.group(1), '%Y-%m-%d') > last_read:
                        sickrage.srCore.srConfig.NEWS_UNREAD += 1
                except Exception:
                    pass

        return news

    def update(self):
        if self.updater:
            # check for updates
            if self.updater.need_update():
                if self.updater.update():
                    # Clean up after update
                    toclean = os.path.join(sickrage.srCore.srConfig.CACHE_DIR, 'mako')

                    for root, dirs, files in os.walk(toclean, topdown=False):
                        [os.remove(os.path.join(root, name)) for name in files]
                        [os.rmdir(os.path.join(root, name)) for name in dirs]

                    return True

    @property
    def get_version(self):
        if self.updater:
            return self.updater.version


class UpdateManager(object):
    @staticmethod
    def get_update_url():
        return "home/update/?pid={}".format(sickrage.srCore.PID)

    @staticmethod
    def github():
        try:
            return github.Github(
                login_or_token=sickrage.srCore.srConfig.GIT_USERNAME,
                password=sickrage.srCore.srConfig.GIT_PASSWORD,
                user_agent="SiCKRAGE")
        except:
            return github.Github(user_agent="SiCKRAGE")


class GitUpdateManager(UpdateManager):
    def __init__(self):
        self.type = "git"

    @property
    def version(self):
        return self._find_installed_version()

    @property
    def get_newest_version(self):
        return self._check_for_new_version()

    @staticmethod
    def _git_error():
        error_message = 'Unable to find your git executable - Shutdown SiCKRAGE and EITHER set git_path in your config.ini OR delete your .git folder and run from source to enable updates.'
        sickrage.srCore.NEWEST_VERSION_STRING = error_message

    @property
    def _find_working_git(self):
        test_cmd = 'version'

        main_git = sickrage.srCore.srConfig.GIT_PATH or 'git'

        sickrage.srCore.srLogger.debug("Checking if we can use git commands: " + main_git + ' ' + test_cmd)
        _, _, exit_status = self._run_git(main_git, test_cmd)

        if exit_status == 0:
            sickrage.srCore.srLogger.debug("Using: " + main_git)
            return main_git
        else:
            sickrage.srCore.srLogger.debug("Not using: " + main_git)

        # trying alternatives
        alternative_git = []

        # osx people who start sr from launchd have a broken path, so try a hail-mary attempt for them
        if platform.system().lower() == 'darwin':
            alternative_git.append('/usr/local/git/bin/git')

        if platform.system().lower() == 'windows':
            if main_git != main_git.lower():
                alternative_git.append(main_git.lower())

        if alternative_git:
            sickrage.srCore.srLogger.debug("Trying known alternative git locations")

            for cur_git in alternative_git:
                sickrage.srCore.srLogger.debug("Checking if we can use git commands: " + cur_git + ' ' + test_cmd)
                _, _, exit_status = self._run_git(cur_git, test_cmd)

                if exit_status == 0:
                    sickrage.srCore.srLogger.debug("Using: " + cur_git)
                    return cur_git
                else:
                    sickrage.srCore.srLogger.debug("Not using: " + cur_git)

        # Still haven't found a working git
        error_message = 'Unable to find your git executable - Shutdown SiCKRAGE and EITHER set git_path in your config.ini OR delete your .git folder and run from source to enable updates.'
        sickrage.srCore.NEWEST_VERSION_STRING = error_message

        return None

    @staticmethod
    def _run_git(git_path, args):

        output = err = None

        if not git_path:
            sickrage.srCore.srLogger.warning("No git specified, can't use git commands")
            exit_status = 1
            return output, err, exit_status

        cmd = git_path + ' ' + args

        try:
            sickrage.srCore.srLogger.debug("Executing " + cmd + " with your shell in " + sickrage.PROG_DIR)
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 shell=True, cwd=sickrage.PROG_DIR)
            output, err = p.communicate()
            exit_status = p.returncode

            if output:
                output = output.strip()


        except OSError:
            sickrage.srCore.srLogger.info("Command " + cmd + " didn't work")
            exit_status = 1

        if exit_status == 0:
            sickrage.srCore.srLogger.debug(cmd + " : returned successful")
            exit_status = 0

        elif exit_status == 1:
            if 'stash' in output:
                sickrage.srCore.srLogger.warning(
                    "Please enable 'git reset' in settings or stash your changes in local files")
            else:
                sickrage.srCore.srLogger.error(cmd + " returned : " + str(output))
            exit_status = 1

        elif exit_status == 128 or 'fatal:' in output or err:
            sickrage.srCore.srLogger.debug(cmd + " returned : " + str(output))
            exit_status = 128

        else:
            sickrage.srCore.srLogger.error(cmd + " returned : " + str(output) + ", treat as error for now")
            exit_status = 1

        return output, err, exit_status

    def _find_installed_version(self):
        """
        Attempts to find the currently installed version of SiCKRAGE.

        Uses git show to get commit version.

        Returns: True for success or False for failure
        """

        output, _, exit_status = self._run_git(self._find_working_git, 'rev-parse HEAD')  # @UnusedVariable
        if exit_status == 0 and output:
            cur_commit_hash = output.strip()
            if not re.match('^[a-z0-9]+$', cur_commit_hash):
                sickrage.srCore.srLogger.error("Output doesn't look like a hash, not using it")
                return False
            return cur_commit_hash

    def _check_for_new_version(self):
        """
        Uses git commands to check if there is a newer version that the provided
        commit hash. If there is a newer version it sets _num_commits_behind.
        """

        # get all new info from server
        output, _, exit_status = self._run_git(self._find_working_git, 'remote update')
        if not exit_status == 0:
            sickrage.srCore.srLogger.warning("Unable to contact server, can't check for update")
            return

        # get latest commit_hash from remote
        output, _, exit_status = self._run_git(self._find_working_git, 'rev-parse --verify --quiet "@{upstream}"')
        if exit_status == 0 and output:
            return output.strip()

    def set_newest_text(self):

        # if we're up to date then don't set this
        sickrage.srCore.NEWEST_VERSION_STRING = None

        if self.version != self.get_newest_version:
            newest_text = 'There is a newer version available, version {}'.format(self.get_newest_version)
            newest_text += "&mdash; <a href=\"{}\">Update Now</a>".format(self.get_update_url())
        else:
            return

        sickrage.srCore.NEWEST_VERSION_STRING = newest_text

    def need_update(self):
        try:
            return (False, True)[self.version != self.get_newest_version]
        except Exception as e:
            sickrage.srCore.srLogger.warning("Unable to contact server, can't check for update: " + repr(e))
            return False

    def update(self):
        """
        Calls git pull origin <branch> in order to update SiCKRAGE. Returns a bool depending
        on the call's success.
        """

        # remove untracked files and performs a hard reset on git branch to avoid update issues
        if sickrage.srCore.srConfig.GIT_RESET:
            # self.clean() # This is removing user data and backups
            self.reset()

        _, _, exit_status = self._run_git(self._find_working_git, 'pull -f origin ' + self.current_branch)
        if exit_status == 0:
            if sickrage.srCore.srConfig.NOTIFY_ON_UPDATE:
                srNotifiers.notify_version_update(sickrage.srCore.NEWEST_VERSION_STRING)
            return True

        return False

    def clean(self):
        """
        Calls git clean to remove all untracked files. Returns a bool depending
        on the call's success.
        """
        _, _, exit_status = self._run_git(self._find_working_git, 'clean -df ""')
        return (False, True)[exit_status == 0]

    def reset(self):
        """
        Calls git reset --hard to perform a hard reset. Returns a bool depending
        on the call's success.
        """
        _, _, exit_status = self._run_git(self._find_working_git, 'reset --hard')
        return (False, True)[exit_status == 0]

    def checkout_branch(self, branch):
        if branch in self.remote_branches:
            sickrage.srCore.srLogger.debug("Branch checkout: " + self._find_installed_version() + "->" + branch)

            # remove untracked files and performs a hard reset on git branch to avoid update issues
            if sickrage.srCore.srConfig.GIT_RESET:
                self.reset()

            _, _, exit_status = self._run_git(self._find_working_git, 'checkout -f ' + branch)
            if exit_status == 0:
                return True

        return False

    @property
    def current_branch(self):
        branch, _, exit_status = self._run_git(self._find_working_git, 'rev-parse --abbrev-ref HEAD')
        return ("", branch)[exit_status == 0 and branch is not None]

    @property
    def remote_branches(self):
        branches, _, exit_status = self._run_git(self._find_working_git, 'ls-remote --heads origin')
        if exit_status == 0 and branches:
            return re.findall(r'refs/heads/(.*)', branches)

        return []

    @property
    def remote_url(self):
        url, _, exit_status = self._run_git(self._find_working_git, 'config --get remote.origin.url')
        return ("", url)[exit_status == 0 and url is not None]

class SourceUpdateManager(UpdateManager):
    def __init__(self):
        self.type = "source"

    @property
    def version(self):
        return self._find_installed_version()

    @property
    def get_newest_version(self):
        return self._check_for_new_version()

    def _find_installed_version(self):
        with io.open(os.path.join(sickrage.PROG_DIR, 'version.txt')) as f:
            return f.read().strip() or ""

    def need_update(self):
        try:
            return (False, True)[self.version != self.get_newest_version]
        except Exception as e:
            sickrage.srCore.srLogger.warning("Unable to contact server, can't check for update: " + repr(e))
            return False

    def _check_for_new_version(self):
        git_version_url = "http://www.sickrage.ca/version.txt"

        try:
            return sickrage.srCore.srWebSession.get(git_version_url).text
        except Exception:
            return self._find_installed_version()

    def set_newest_text(self):
        # if we're up to date then don't set this
        sickrage.srCore.NEWEST_VERSION_STRING = None

        if not self.version:
            sickrage.srCore.srLogger.debug("Unknown current version number, don't know if we should update or not")

            newest_text = "Unknown current version number: If yo've never used the SiCKRAGE upgrade system before then current version is not set."
            newest_text += "&mdash; <a href=\"" + self.get_update_url() + "\">Update Now</a>"

        else:
            newest_text = 'There is a newer version available, version {}'.format(self.get_newest_version)
            newest_text += "&mdash; <a href=\"" + self.get_update_url() + "\">Update Now</a>"

        sickrage.srCore.NEWEST_VERSION_STRING = newest_text

    def update(self):
        """
        Downloads the latest source tarball from server and installs it over the existing version.
        """

        tar_download_url = 'http://www.sickrage.ca/sr-update.tar'

        try:
            # prepare the update dir
            sr_update_dir = os.path.join(sickrage.PROG_DIR, 'sr-update')

            if os.path.isdir(sr_update_dir):
                sickrage.srCore.srLogger.info("Clearing out update folder " + sr_update_dir + " before extracting")
                removetree(sr_update_dir)

            sickrage.srCore.srLogger.info("Creating update folder " + sr_update_dir + " before extracting")
            os.makedirs(sr_update_dir)

            # retrieve file
            sickrage.srCore.srLogger.info("Downloading update from " + repr(tar_download_url))
            tar_download_path = os.path.join(sr_update_dir, 'sr-update.tar')
            sickrage.srCore.srWebSession.download(tar_download_url, tar_download_path)

            if not os.path.isfile(tar_download_path):
                sickrage.srCore.srLogger.warning(
                    "Unable to retrieve new version from " + tar_download_url + ", can't update")
                return False

            if not tarfile.is_tarfile(tar_download_path):
                sickrage.srCore.srLogger.error(
                    "Retrieved version from " + tar_download_url + " is corrupt, can't update")
                return False

            # extract to sr-update dir
            sickrage.srCore.srLogger.info("Extracting file " + tar_download_path)
            tar = tarfile.open(tar_download_path)
            tar.extractall(sr_update_dir)
            tar.close()

            # delete .tar.gz
            sickrage.srCore.srLogger.info("Deleting file " + tar_download_path)
            os.remove(tar_download_path)

            # find update dir name
            update_dir_contents = [x for x in os.listdir(sr_update_dir) if
                                   os.path.isdir(os.path.join(sr_update_dir, x))]
            if len(update_dir_contents) != 1:
                sickrage.srCore.srLogger.error("Invalid update data, update failed: " + str(update_dir_contents))
                return False
            content_dir = os.path.join(sr_update_dir, update_dir_contents[0])

            # walk temp folder and move files to main folder
            sickrage.srCore.srLogger.info("Moving files from " + content_dir + " to " + sickrage.PROG_DIR)
            for dirname, _, filenames in os.walk(content_dir):  # @UnusedVariable
                dirname = dirname[len(content_dir) + 1:]
                for curfile in filenames:
                    old_path = os.path.join(content_dir, dirname, curfile)
                    new_path = os.path.join(sickrage.PROG_DIR, dirname, curfile)

                    # Avoid DLL access problem on WIN32/64
                    # These files needing to be updated manually
                    # or find a way to kill the access from memory
                    if curfile in ('unrar.dll', 'unrar64.dll'):
                        try:
                            os.chmod(new_path, stat.S_IWRITE)
                            os.remove(new_path)
                            os.renames(old_path, new_path)
                        except Exception as e:
                            sickrage.srCore.srLogger.debug("Unable to update " + new_path + ': ' + e.message)
                            os.remove(old_path)  # Trash the updated file without moving in new path
                        continue

                    if os.path.isfile(new_path):
                        os.remove(new_path)
                    os.renames(old_path, new_path)

        except Exception as e:
            sickrage.srCore.srLogger.error("Error while trying to update: {}".format(e.message))
            sickrage.srCore.srLogger.debug("Traceback: " + traceback.format_exc())
            return False

        # Notify update successful
        sickrage.srCore.notifiersDict.notify_git_update(sickrage.srCore.NEWEST_VERSION_STRING)

        return True


class PipUpdateManager(UpdateManager):
    def __init__(self):
        self.type = "pip"

    @property
    def version(self):
        return self._find_installed_version()

    @property
    def get_newest_version(self):
        return self._check_for_new_version()

    def _find_installed_version(self):
        with io.open(os.path.join(sickrage.PROG_DIR, 'version.txt')) as f:
            return f.read().strip() or ""

    def need_update(self):
        # need this to run first to set self._newest_commit_hash
        try:
            pypi_version = self.get_newest_version
            if self._find_installed_version() != pypi_version:
                sickrage.srCore.srLogger.debug(
                    "Version upgrade: " + self._find_installed_version() + "->" + pypi_version)
                return True
        except Exception as e:
            sickrage.srCore.srLogger.warning("Unable to contact PyPi, can't check for update: " + repr(e))
            return False

    def _check_for_new_version(self):
        import xmlrpclib
        pypi = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')

        import pip
        for dist in pip.get_installed_distributions():
            if not dist.project_name.lower() == 'sickrage':
                continue

            available = pypi.package_releases(dist.project_name)
            if not available:
                # Try to capitalize pkg name
                available = pypi.package_releases(dist.project_name.capitalize())

            if available:
                return available[0]

        return self._find_installed_version()

    def set_newest_text(self):

        # if we're up to date then don't set this
        sickrage.srCore.NEWEST_VERSION_STRING = None

        if self.version:
            sickrage.srCore.srLogger.debug("Unknown current version number, don't know if we should update or not")

            newest_text = "Unknown current version number: If yo've never used the SiCKRAGE upgrade system before then current version is not set."
            newest_text += "&mdash; <a href=\"{}\">Update Now</a>".format(self.get_update_url())
            return
        else:
            newest_text = "New SiCKRAGE update found on PyPy servers, version {}".format(self.get_newest_version)
            newest_text += "&mdash; <a href=\"{}\">Update Now</a>".format(self.get_update_url())

        sickrage.srCore.NEWEST_VERSION_STRING = newest_text

    def update(self):
        """
        Performs pip upgrade
        """
        # Notify update successful
        sickrage.srCore.srLogger.info("Updating SiCKRAGE from PyPi servers")
        srNotifiers.notify_version_update(sickrage.srCore.NEWEST_VERSION_STRING)

        from pip.commands.install import InstallCommand
        options = InstallCommand().parse_args([])[0]
        options.use_user_site = all([not sickrage.isElevatedUser(), not sickrage.isVirtualEnv()])
        options.cache_dir = None
        options.upgrade = True
        options.quiet = 1

        options.ignore_dependencies = True
        InstallCommand().run(options, ['sickrage'])
        options.ignore_dependencies = False
        InstallCommand().run(options, ['sickrage'])

        return True
