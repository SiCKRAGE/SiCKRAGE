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

import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import threading
from time import sleep

import sickrage
from sickrage.core.helpers import backupSR
from sickrage.core.websession import WebSession
from sickrage.core.websocket import WebSocketMessage
from sickrage.notifiers import Notifiers


class VersionUpdater(object):
    def __init__(self):
        self.name = "VERSIONUPDATER"
        self.amActive = False

    @property
    def updater(self):
        return self.find_install_type()

    def run(self, force=False):
        if self.amActive:
            return

        self.amActive = True

        # set thread name
        threading.currentThread().setName(self.name)

        try:
            if self.check_for_new_version(force):
                if sickrage.app.config.auto_update:
                    if sickrage.app.show_updater.amActive:
                        sickrage.app.log.debug("We can't proceed with auto-updating. Shows are being updated")
                        return

                    sickrage.app.log.info("New update found for SiCKRAGE, starting auto-updater ...")
                    sickrage.app.alerts.message(_('Updater'),
                                                _('New update found for SiCKRAGE, starting auto-updater'))
                    if self.update():
                        sickrage.app.log.info("Update was successful!")
                        sickrage.app.alerts.message(_('Updater'),
                                                    _('Update was successful'))
                        sickrage.app.shutdown(restart=True)
                    else:
                        sickrage.app.log.info("Update failed!")
                        sickrage.app.alerts.error(_('Updater'),
                                                  _('Update failed!'))
        finally:
            self.amActive = False

    def backup(self):
        # Do a system backup before update
        sickrage.app.log.info("Config backup in progress...")
        sickrage.app.alerts.message(_('Updater'),
                                    _('Config backup in progress...'))
        try:
            backupDir = os.path.join(sickrage.app.data_dir, 'backup')
            if not os.path.isdir(backupDir):
                os.mkdir(backupDir)

            if backupSR(backupDir, keep_latest=True):
                sickrage.app.log.info("Config backup successful, updating...")
                sickrage.app.alerts.message(_('Updater'),
                                            _('Config backup successful, updating...'))
                return True
            else:
                sickrage.app.log.warning("Config backup failed, aborting update")
                sickrage.app.alerts.error(_('Updater'),
                                          _('Config backup failed, aborting update'))
                return False
        except Exception as e:
            sickrage.app.log.warning('Update: Config backup failed. Error: {}'.format(e))
            sickrage.app.alerts.error(_('Updater'),
                                      _('Config backup failed, aborting update'))
            return False

    @staticmethod
    def safe_to_update():
        if sickrage.app.auto_postprocessor.amActive:
            sickrage.app.log.debug("We can't proceed with updating, post-processor is running")
            sickrage.app.alerts.message(_('Updater'),
                                        _("We can't proceed with updating, post-processor is running"))
            return False

        sickrage.app.show_queue.pause()
        sickrage.app.log.debug("Waiting for jobs in show queue to finish before updating")
        sickrage.app.alerts.message(_('Updater'),
                                    _("Waiting for jobs in show queue to finish before updating"))
        while sickrage.app.show_queue.is_busy:
            sleep(1)

        return True

    @staticmethod
    def find_install_type():
        """
        Determines how this copy of sr was installed.

        returns: type of installation. Possible values are:

            'git': running from source using git
            'pip': running from source using pip
            'source': running from source without git
        """

        # default to source install type
        install_type = SourceUpdateManager()

        if os.path.isdir(os.path.join(sickrage.MAIN_DIR, '.git')):
            # GIT install type
            install_type = GitUpdateManager()
        elif PipUpdateManager().version:
            # PIP install type
            install_type = PipUpdateManager()

        return install_type

    def check_for_new_version(self, force=False):
        """
        Checks the internet for a newer version.

        returns: bool, True for new version or False for no new version.
        :param force: if true the version_notify setting will be ignored and a check will be forced
        """

        if not self.updater or (not sickrage.app.config.version_notify or sickrage.app.developer) and not force:
            return False

        if self.updater.need_update():
            if not sickrage.app.config.auto_update or force:
                self.updater.set_newest_text()
            return True

    def update(self, webui=False):
        if self.updater:
            # check if its safe to update
            if not self.safe_to_update():
                return False

            # backup
            if not self.backup():
                return False

            # check for updates
            if not self.updater.need_update():
                return False

            # attempt update
            if self.updater.update():
                # Clean up after update
                to_clean = os.path.join(sickrage.app.cache_dir, 'mako')

                for root, dirs, files in os.walk(to_clean, topdown=False):
                    [os.remove(os.path.join(root, name)) for name in files]
                    [shutil.rmtree(os.path.join(root, name)) for name in dirs]

                sickrage.app.config.view_changelog = True

                if webui:
                    WebSocketMessage('task', {'cmd': 'restart'}).push()

                return True

            if webui:
                sickrage.app.alerts.error(_("Updater"),
                                          _("Update wasn't successful, not restarting. Check your log for more "
                                            "information."))

    @property
    def version(self):
        if self.updater:
            return self.updater.version

    @property
    def branch(self):
        if self.updater:
            return self.updater.current_branch
        return "master"


class UpdateManager(object):
    @property
    def _git_path(self):
        test_cmd = '--version'

        main_git = sickrage.app.config.git_path or 'git'

        # sickrage.app.log.debug("Checking if we can use git commands: " + main_git + ' ' + test_cmd)
        __, __, exit_status = self._git_cmd(main_git, test_cmd, silent=True)
        if exit_status == 0:
            # sickrage.app.log.debug("Using: " + main_git)
            return main_git

        # trying alternatives
        alternative_git = []

        # osx people who start sr from launchd have a broken path, so try a hail-mary attempt for them
        if platform.system().lower() == 'darwin':
            alternative_git.append('/usr/local/git/bin/git')

        if platform.system().lower() == 'windows':
            if main_git != main_git.lower():
                alternative_git.append(main_git.lower())

        if alternative_git:
            sickrage.app.log.debug("Trying known alternative git locations")

            for cur_git in alternative_git:
                # sickrage.app.log.debug("Checking if we can use git commands: " + cur_git + ' ' + test_cmd)
                __, __, exit_status = self._git_cmd(cur_git, test_cmd)
                if exit_status == 0:
                    # sickrage.app.log.debug("Using: " + cur_git)
                    return cur_git

        # Still haven't found a working git
        error_message = _('Unable to find your git executable - Set your git path from Settings->General->Advanced OR '
                          'delete your {git_folder} folder and run from source to enable updates.'.format(**{
            'git_folder': os.path.join(sickrage.MAIN_DIR, '.git')
        }))

        sickrage.app.alerts.error(_('Updater'), error_message)

    @property
    def _pip_path(self):
        test_cmd = '-V'

        main_pip = sickrage.app.config.pip_path or 'pip2'

        # sickrage.app.log.debug("Checking if we can use pip commands: " + main_pip + ' ' + test_cmd)
        __, __, exit_status = self._pip_cmd(main_pip, test_cmd, silent=True)
        if exit_status == 0:
            # sickrage.app.log.debug("Using: " + main_pip)
            return main_pip

        # trying alternatives
        alternative_pip = []

        # osx people who start sr from launchd have a broken path, so try a hail-mary attempt for them
        if platform.system().lower() == 'darwin':
            alternative_pip.append('/usr/local/python2.7/bin/pip2')

        if platform.system().lower() == 'windows':
            if main_pip != main_pip.lower():
                alternative_pip.append(main_pip.lower())

        if alternative_pip:
            sickrage.app.log.debug("Trying known alternative pip locations")

            for cur_pip in alternative_pip:
                # sickrage.app.log.debug("Checking if we can use pip commands: " + cur_pip + ' ' + test_cmd)
                __, __, exit_status = self._pip_cmd(cur_pip, test_cmd)
                if exit_status == 0:
                    # sickrage.app.log.debug("Using: " + cur_pip)
                    return cur_pip

        # Still haven't found a working git
        error_message = _('Unable to find your pip executable - Set your pip path from Settings->General->Advanced')

        sickrage.app.alerts.error(_('Updater'), error_message)

    @staticmethod
    def _git_cmd(git_path, args, silent=False):
        output = err = None

        if not git_path:
            sickrage.app.log.warning("No path to git specified, can't use git commands")
            exit_status = 1
            return output, err, exit_status

        cmd = [git_path] + args.split()

        try:
            if not silent:
                sickrage.app.log.debug("Executing " + ' '.join(cmd) + " with your shell in " + sickrage.MAIN_DIR)

            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 shell=(sys.platform == 'win32'), cwd=sickrage.MAIN_DIR)
            output, err = p.communicate()
            exit_status = p.returncode

            if output:
                output = output.strip()

        except OSError:
            sickrage.app.log.info("Command " + ' '.join(cmd) + " didn't work")
            exit_status = 1

        if exit_status == 0:
            if not silent:
                sickrage.app.log.debug(' '.join(cmd) + " : returned successful")
            exit_status = 0
        elif exit_status == 1:
            if output:
                if 'stash' in output:
                    sickrage.app.log.warning(
                        "Please enable 'git reset' in settings or stash your changes in local files")
                else:
                    sickrage.app.log.debug(' '.join(cmd) + " returned : " + str(output))
            else:
                sickrage.app.log.warning('{} returned no data'.format(cmd))
            exit_status = 1
        elif exit_status == 128 or 'fatal:' in output or err:
            sickrage.app.log.debug(' '.join(cmd) + " returned : " + str(output))
            exit_status = 128
        else:
            sickrage.app.log.debug(' '.join(cmd) + " returned : " + str(output) + ", treat as error for now")
            exit_status = 1

        return output, err, exit_status

    @staticmethod
    def _pip_cmd(pip_path, args, silent=False):
        output = err = None

        if not pip_path:
            sickrage.app.log.warning("No path to pip specified, can't use pip commands")
            exit_status = 1
            return output, err, exit_status

        cmd = [pip_path] + args.split()

        try:
            if not silent:
                sickrage.app.log.debug("Executing " + ' '.join(cmd) + " with your shell in " + sickrage.MAIN_DIR)

            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 shell=(sys.platform == 'win32'), cwd=sickrage.MAIN_DIR)
            output, err = p.communicate()
            exit_status = p.returncode

            if output:
                output = output.strip()
        except OSError:
            sickrage.app.log.info("Command " + ' '.join(cmd) + " didn't work")
            exit_status = 1

        if exit_status == 0:
            if not silent:
                sickrage.app.log.debug(' '.join(cmd) + " : returned successful")
            exit_status = 0
        else:
            sickrage.app.log.debug(' '.join(cmd) + " returned : " + str(output) + ", treat as error for now")
            exit_status = 1

        return output, err, exit_status

    @staticmethod
    def get_update_url():
        return "{}/home/update/?pid={}".format(sickrage.app.config.web_root, sickrage.app.pid)

    def install_requirements(self):
        for req_file in ['requirements.txt', sickrage.REQS_FILE]:
            __, __, exit_status = self._pip_cmd(self._pip_path,
                                                'install --no-cache-dir -r {}'.format(req_file))

            if exit_status != 0:
                __, __, exit_status = self._pip_cmd(self._pip_path,
                                                    'install --no-cache-dir --user -r {}'.format(req_file))

            if exit_status == 0:
                return True

        sickrage.app.log.warning('Unable to update requirements using {req_file}'.format(**{
            'req_file': sickrage.REQS_FILE
        }))

        return False


class GitUpdateManager(UpdateManager):
    def __init__(self):
        self.type = "git"

    @property
    def version(self):
        return self._find_installed_version()

    @property
    def get_newest_version(self):
        return self._check_for_new_version() or self.version

    @property
    def current_branch(self):
        branch, __, exit_status = self._git_cmd(self._git_path, 'rev-parse --abbrev-ref HEAD')
        return ("", branch)[exit_status == 0 and branch is not None]

    @property
    def remote_branches(self):
        branches, __, exit_status = self._git_cmd(self._git_path,
                                                  'ls-remote --heads {}'.format(sickrage.app.config.git_remote))
        if exit_status == 0 and branches:
            return re.findall(r'refs/heads/(.*)', branches)

        return []

    def _find_installed_version(self):
        """
        Attempts to find the currently installed version of SiCKRAGE.

        Uses git show to get commit version.

        Returns: True for success or False for failure
        """

        output, __, exit_status = self._git_cmd(self._git_path, 'rev-parse HEAD')
        if exit_status == 0 and output:
            cur_commit_hash = output.strip()
            if not re.match('^[a-z0-9]+$', cur_commit_hash):
                sickrage.app.log.error("Output doesn't look like a hash, not using it")
                return False
            return cur_commit_hash

    def _check_for_new_version(self):
        """
        Uses git commands to check if there is a newer version that the provided
        commit hash. If there is a newer version it sets _num_commits_behind.
        """

        # get all new info from server
        output, __, exit_status = self._git_cmd(self._git_path, 'remote update')
        if not exit_status == 0:
            sickrage.app.log.warning("Unable to contact server, can't check for update, Output: {}".format(output))
            return

        # get latest commit_hash from remote
        output, __, exit_status = self._git_cmd(self._git_path,
                                                'rev-parse --verify --quiet origin/{}'.format(self.current_branch))
        if exit_status == 0 and output:
            return output.strip()

    def set_newest_text(self):
        if self.version != self.get_newest_version:
            newest_text = _(
                'There is a newer version available, version {} &mdash; <a href=\"{}\">Update Now</a>').format(
                self.get_newest_version, self.get_update_url())
            sickrage.app.newest_version_string = newest_text

    def need_update(self):
        try:
            return (False, True)[self.version != self.get_newest_version]
        except Exception as e:
            sickrage.app.log.warning("Unable to contact server, can't check for update: " + repr(e))
            return False

    def update(self):
        """
        Calls git pull origin <branch> in order to update SiCKRAGE. Returns a bool depending
        on the call's success.
        """

        # remove untracked files and performs a hard reset on git branch to avoid update issues
        if sickrage.app.config.git_reset:
            # self.clean() # This is removing user data and backups
            self.reset()

        __, __, exit_status = self._git_cmd(self._git_path, 'pull -f {} {}'.format(sickrage.app.config.git_remote,
                                                                                   self.current_branch))
        if exit_status == 0:
            sickrage.app.log.info("Updating SiCKRAGE from GIT servers")
            sickrage.app.alerts.message(_('Updater'),
                                        _('Updating SiCKRAGE from GIT servers'))
            Notifiers.mass_notify_version_update(self.get_newest_version)
            return self.install_requirements()

        return False

    def clean(self):
        """
        Calls git clean to remove all untracked files. Returns a bool depending
        on the call's success.
        """
        __, __, exit_status = self._git_cmd(self._git_path, 'clean -df ""')
        return (False, True)[exit_status == 0]

    def reset(self):
        """
        Calls git reset --hard to perform a hard reset. Returns a bool depending
        on the call's success.
        """
        __, __, exit_status = self._git_cmd(self._git_path, 'reset --hard')
        return (False, True)[exit_status == 0]

    def fetch(self):
        """
        Calls git fetch to fetch all remote branches
        on the call's success.
        """
        __, __, exit_status = self._git_cmd(self._git_path,
                                            'config remote.origin.fetch %s' % '+refs/heads/*:refs/remotes/origin/*')
        if exit_status == 0:
            __, __, exit_status = self._git_cmd(self._git_path, 'fetch --all')
        return (False, True)[exit_status == 0]

    def checkout_branch(self, branch):
        if branch in self.remote_branches:
            sickrage.app.log.debug("Branch checkout: " + self._find_installed_version() + "->" + branch)

            # remove untracked files and performs a hard reset on git branch to avoid update issues
            if sickrage.app.config.git_reset:
                self.reset()

            # fetch all branches
            self.fetch()

            __, __, exit_status = self._git_cmd(self._git_path, 'checkout -f ' + branch)
            if exit_status == 0:
                return self.install_requirements()

        return False

    def get_remote_url(self):
        url, __, exit_status = self._git_cmd(self._git_path,
                                             'remote get-url {}'.format(sickrage.app.config.git_remote))
        return ("", url)[exit_status == 0 and url is not None]

    def set_remote_url(self):
        if not sickrage.app.developer:
            self._git_cmd(self._git_path, 'remote set-url {} {}'.format(sickrage.app.config.git_remote,
                                                                        sickrage.app.config.git_remote_url))


class SourceUpdateManager(UpdateManager):
    def __init__(self):
        self.type = "source"

    @property
    def version(self):
        return self._find_installed_version()

    @property
    def get_newest_version(self):
        return self._check_for_new_version() or self.version

    @property
    def current_branch(self):
        return 'master'

    @staticmethod
    def _find_installed_version():
        return sickrage.version() or ""

    def need_update(self):
        try:
            return (False, True)[self.version != self.get_newest_version]
        except Exception as e:
            sickrage.app.log.warning("Unable to contact server, can't check for update: " + repr(e))
            return False

    def _check_for_new_version(self):
        git_version_url = "https://git.sickrage.ca/SiCKRAGE/sickrage/raw/master/sickrage/version.txt"

        try:
            return WebSession().get(git_version_url).text
        except Exception:
            return self._find_installed_version()

    def set_newest_text(self):
        if not self.version:
            sickrage.app.log.debug("Unknown current version number, don't know if we should update or not")
            return

        newest_text = _("There is a newer version available, version {} &mdash; "
                        "<a href=\"{}\">Update Now</a>").format(self.get_newest_version, self.get_update_url())
        sickrage.app.newest_version_string = newest_text

    def update(self):
        """
        Downloads the latest source tarball from server and installs it over the existing version.
        """

        tar_download_url = 'https://git.sickrage.ca/SiCKRAGE/sickrage/repository/archive.tar?ref=master'

        try:
            # prepare the update dir
            sr_update_dir = os.path.join(sickrage.app.data_dir, 'sr-update')

            if os.path.isdir(sr_update_dir):
                sickrage.app.log.info("Clearing out update folder " + sr_update_dir + " before extracting")
                shutil.rmtree(sr_update_dir)

            sickrage.app.log.info("Creating update folder " + sr_update_dir + " before extracting")
            try:
                os.makedirs(sr_update_dir)
            except OSError as e:
                sickrage.app.log.warning("Unable to create update folder " + sr_update_dir + ': ' + str(e))
                return False

            # retrieve file
            sickrage.app.log.info("Downloading update from " + repr(tar_download_url))
            tar_download_path = os.path.join(sr_update_dir, 'sr-update.tar')
            WebSession().download(tar_download_url, tar_download_path)

            if not os.path.isfile(tar_download_path):
                sickrage.app.log.warning(
                    "Unable to retrieve new version from " + tar_download_url + ", can't update")
                return False

            if not tarfile.is_tarfile(tar_download_path):
                sickrage.app.log.warning(
                    "Retrieved version from " + tar_download_url + " is corrupt, can't update")
                return False

            # extract to sr-update dir
            sickrage.app.log.info("Extracting file " + tar_download_path)
            tar = tarfile.open(tar_download_path)
            tar.extractall(sr_update_dir)
            tar.close()

            # delete .tar.gz
            sickrage.app.log.info("Deleting file " + tar_download_path)
            os.remove(tar_download_path)

            # find update dir name
            update_dir_contents = [x for x in os.listdir(sr_update_dir) if
                                   os.path.isdir(os.path.join(sr_update_dir, x))]
            if len(update_dir_contents) != 1:
                sickrage.app.log.warning("Invalid update data, update failed: " + str(update_dir_contents))
                return False

            # walk temp folder and move files to main folder
            content_dir = os.path.join(sr_update_dir, update_dir_contents[0])
            sickrage.app.log.info("Moving files from " + content_dir + " to " + sickrage.MAIN_DIR)
            for dirname, __, filenames in os.walk(content_dir):
                dirname = dirname[len(content_dir) + 1:]
                for curfile in filenames:
                    old_path = os.path.join(content_dir, dirname, curfile)
                    new_path = os.path.join(sickrage.MAIN_DIR, dirname, curfile)

                    if os.path.isfile(new_path):
                        os.remove(new_path)
                    os.renames(old_path, new_path)

            # install requirements
            if not self.install_requirements():
                return False
        except Exception as e:
            sickrage.app.log.error("Error while trying to update: {}".format(e))
            return False

        # Notify update successful
        Notifiers.mass_notify_version_update(self.get_newest_version)

        return True


class PipUpdateManager(UpdateManager):
    def __init__(self):
        self.type = "pip"

    @property
    def version(self):
        return self._find_installed_version()

    @property
    def get_newest_version(self):
        return self._check_for_new_version() or self.version

    @property
    def current_branch(self):
        return 'master'

    def _find_installed_version(self):
        out, __, exit_status = self._pip_cmd(self._pip_path, 'show sickrage')
        if exit_status == 0:
            return out.split('\n')[1].split()[1]
        return ""

    def need_update(self):
        # need this to run first to set self._newest_commit_hash
        try:
            pypi_version = self.get_newest_version
            if self.version != pypi_version:
                sickrage.app.log.debug(
                    "Version upgrade: " + self._find_installed_version() + " -> " + pypi_version)
                return True
        except Exception as e:
            sickrage.app.log.warning("Unable to contact PyPi, can't check for update: " + repr(e))
            return False

    def _check_for_new_version(self):
        from distutils.version import LooseVersion
        url = "https://pypi.org/pypi/{}/json".format('sickrage')
        resp = WebSession().get(url)
        versions = resp.json()["releases"].keys()
        versions = [x for x in versions if 'dev' not in x]
        versions.sort(key=LooseVersion, reverse=True)

        try:
            return versions[0]
        except Exception:
            return self._find_installed_version()

    def set_newest_text(self):
        if not self.version:
            sickrage.app.log.debug("Unknown current version number, don't know if we should update or not")
            return

        newest_text = _("New SiCKRAGE update found on PyPi servers, version {} &mdash; "
                        "<a href=\"{}\">Update Now</a>").format(self.get_newest_version, self.get_update_url())
        sickrage.app.newest_version_string = newest_text

    def update(self):
        """
        Performs pip upgrade
        """
        __, __, exit_status = self._pip_cmd(self._pip_path, 'install -U --no-cache-dir sickrage')
        if exit_status == 0:
            sickrage.app.log.info("Updating SiCKRAGE from PyPi servers")
            sickrage.app.alerts.message(_('Updater'), _('Updating SiCKRAGE from PyPi servers'))
            Notifiers.mass_notify_version_update(self.get_newest_version)
            return True

        return False
