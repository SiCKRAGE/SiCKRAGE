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
import functools
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading
from time import sleep

import dirsync as dirsync

import sickrage
from sickrage.core.helpers import backup_app_data
from sickrage.core.websession import WebSession
from sickrage.core.websocket import WebSocketMessage
from sickrage.notification_providers import NotificationProvider


class VersionUpdater(object):
    def __init__(self):
        self.name = "VERSIONUPDATER"
        self.running = False

    @property
    def updater(self):
        return self.find_install_type()

    def task(self, force=False):
        if self.running or sickrage.app.disable_updates or sickrage.app.developer:
            return

        try:
            self.running = True

            # set thread name
            threading.currentThread().setName(self.name)

            if self.check_for_new_version(force):
                if sickrage.app.config.general.auto_update:
                    if sickrage.app.show_updater.running:
                        sickrage.app.log.debug("We can't proceed with auto-updating. Shows are being updated")
                        return

                    sickrage.app.log.info("New update found for SiCKRAGE, starting auto-updater ...")
                    sickrage.app.alerts.message(_('Updater'), _('New update found for SiCKRAGE, starting auto-updater'))
                    if self.update():
                        sickrage.app.log.info("Update was successful!")
                        sickrage.app.alerts.message(_('Updater'), _('Update was successful'))
                        sickrage.app.shutdown(restart=True)
                    else:
                        sickrage.app.log.info("Update failed!")
                        sickrage.app.alerts.error(_('Updater'), _('Update failed!'))
        finally:
            self.running = False

    def backup(self):
        # Do a system backup before update
        sickrage.app.log.info("Config backup in progress...")
        sickrage.app.alerts.message(_('Updater'), _('Config backup in progress...'))

        try:
            backupDir = os.path.join(sickrage.app.data_dir, 'backup')
            if not os.path.isdir(backupDir):
                os.mkdir(backupDir)

            if backup_app_data(backupDir, keep_latest=True):
                sickrage.app.log.info("Config backup successful, updating...")
                sickrage.app.alerts.message(_('Updater'), _('Config backup successful, updating...'))
                return True
            else:
                sickrage.app.log.warning("Config backup failed, aborting update")
                sickrage.app.alerts.error(_('Updater'), _('Config backup failed, aborting update'))
                return False
        except Exception as e:
            sickrage.app.log.warning('Update: Config backup failed. Error: {}'.format(e))
            sickrage.app.alerts.error(_('Updater'), _('Config backup failed, aborting update'))
            return False

    @staticmethod
    def safe_to_update():
        sickrage.app.postprocessor_queue.shutdown()
        sickrage.app.log.debug("Waiting for jobs in post-processor queue to finish before updating")
        sickrage.app.alerts.message(_('Updater'), _("Waiting for jobs in post-processor queue to finish before updating"))

        while sickrage.app.postprocessor_queue.is_busy:
            sleep(1)

        sickrage.app.show_queue.shutdown()
        sickrage.app.log.debug("Waiting for jobs in show queue to finish before updating")
        sickrage.app.alerts.message(_('Updater'), _("Waiting for jobs in show queue to finish before updating"))

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

        if sickrage.app.disable_updates:
            return False

        if not self.updater or not sickrage.app.config.general.version_notify and not force:
            return False

        if self.updater.need_update():
            if not sickrage.app.config.general.auto_update or force:
                self.updater.set_newest_text()
            return True

    def update(self, webui=False):
        if self.updater:
            # check if its safe to update
            if not self.safe_to_update():
                return False

            # backup
            if sickrage.app.config.general.backup_on_update and not self.backup():
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

                sickrage.app.config.general.view_changelog = True

                if webui:
                    WebSocketMessage('redirect', {'url': '{}/home/restart/?pid={}'.format(sickrage.app.config.general.web_root, sickrage.app.pid)}).push()

                return True

            if webui:
                sickrage.app.alerts.error(_("Updater"), _("Update wasn't successful, not restarting. Check your log for more information."))

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
    def version_regex(self):
        return re.compile('^(?P<major>[0-9]+).(?P<minor>[0-9]+).(?P<patch>[0-9]+)(?:.dev(?P<pre_release>[0-9]+))?$', re.IGNORECASE)

    @property
    def _git_path(self):
        test_cmd = '--version'

        alternative_git = {
            'windows': 'git',
            'darwin': '/usr/local/git/bin/git'
        }

        main_git = sickrage.app.config.general.git_path or 'git'

        # sickrage.app.log.debug("Checking if we can use git commands: " + main_git + ' ' + test_cmd)
        __, __, exit_status = self._git_cmd(main_git, test_cmd, silent=True)
        if exit_status == 0:
            # sickrage.app.log.debug("Using: " + main_git)
            return main_git

        if platform.system().lower() in alternative_git:
            sickrage.app.log.debug("Trying known alternative GIT application locations")

            # sickrage.app.log.debug("Checking if we can use git commands: " + cur_git + ' ' + test_cmd)
            __, __, exit_status = self._git_cmd(alternative_git[platform.system().lower()], test_cmd)
            if exit_status == 0:
                # sickrage.app.log.debug("Using: " + cur_git)
                return alternative_git[platform.system().lower()]

        # Still haven't found a working git
        error_message = _('Unable to find your git executable - Set your git path from Settings->General->Advanced OR '
                          'delete your {git_folder} folder and run from source to enable '
                          'updates.'.format(**{'git_folder': os.path.join(sickrage.MAIN_DIR, '.git')}))

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

            if output is not None:
                output = output.decode("utf-8", "ignore").strip() if isinstance(output, bytes) else output.strip()
        except (RuntimeError, OSError):
            sickrage.app.log.info("Command " + ' '.join(cmd) + " didn't work")
            exit_status = 1

        if exit_status == 0:
            if not silent:
                sickrage.app.log.debug(' '.join(cmd) + " : returned successful")
            exit_status = 0
        elif exit_status == 1:
            if output:
                if 'stash' in output:
                    sickrage.app.log.warning("Please enable 'git reset' in settings or stash your changes in local files")
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
    def _pip_cmd(args, silent=False):
        output = err = None

        cmd = [sys.executable, "-m", "pip"] + args.split()

        try:
            if not silent:
                sickrage.app.log.debug("Executing " + ' '.join(cmd) + " with your shell in " + sickrage.MAIN_DIR)

            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=(sys.platform == 'win32'),
                                 cwd=sickrage.MAIN_DIR)

            output, err = p.communicate()
            exit_status = p.returncode
        except (RuntimeError, OSError):
            sickrage.app.log.info("Command " + ' '.join(cmd) + " didn't work")
            exit_status = 1

        if exit_status == 0:
            exit_status = 0
        else:
            exit_status = 1

        if output:
            output = output.decode("utf-8", "ignore").strip() if isinstance(output, bytes) else output.strip()

        return output, err, exit_status

    @staticmethod
    def get_update_url():
        return "{}/home/update/?pid={}".format(sickrage.app.config.general.web_root, sickrage.app.pid)

    def upgrade_pip(self):
        output, __, exit_status = self._pip_cmd('install --no-cache-dir -U pip')

        if exit_status != 0:
            __, __, exit_status = self._pip_cmd('install --no-cache-dir --user -U PIP')

        if exit_status == 0:
            return True

        sickrage.app.alerts.error(_('Updater'), _('Failed to update PIP'))

        sickrage.app.log.warning('Unable to update PIP')

        if output:
            output = output.decode("utf-8", "ignore").strip() if isinstance(output, bytes) else output.strip()
            sickrage.app.log.debug("PIP CMD OUTPUT: {}".format(output))

    def install_requirements(self, branch):
        requirements_url = "https://git.sickrage.ca/SiCKRAGE/sickrage/raw/{}/requirements.txt".format(branch)
        requirements_file = tempfile.NamedTemporaryFile(delete=False)

        try:
            requirements_file.write(WebSession().get(requirements_url).content)
            requirements_file.close()
        except Exception:
            requirements_file.close()
            os.unlink(requirements_file.name)
            return False

        output, __, exit_status = self._pip_cmd('install --no-deps --no-cache-dir -r {}'.format(requirements_file.name))
        if exit_status != 0:
            __, __, exit_status = self._pip_cmd('install --no-deps --no-cache-dir --user -r {}'.format(requirements_file.name))

        if exit_status == 0:
            requirements_file.close()
            os.unlink(requirements_file.name)
            return True

        sickrage.app.alerts.error(_('Updater'), _('Failed to update requirements'))

        sickrage.app.log.warning('Unable to update requirements')

        if output:
            output = output.decode("utf-8", "ignore").strip() if isinstance(output, bytes) else output.strip()
            sickrage.app.log.debug("PIP CMD OUTPUT: {}".format(output))

        requirements_file.close()
        os.unlink(requirements_file.name)

        return False


class GitUpdateManager(UpdateManager):
    def __init__(self):
        self.type = "git"
        self._num_commits_behind = 0
        self._num_commits_ahead = 0

    @property
    def version(self):
        return self._find_installed_version()

    @property
    def get_newest_version(self):
        return self._check_for_new_version() or self.version

    @property
    def current_branch(self):
        branch_ref, __, exit_status = self._git_cmd(self._git_path, 'symbolic-ref -q HEAD')
        if exit_status == 0 and branch_ref is not None:
            return branch_ref.strip().replace('refs/heads/', '', 1)
        return ""

    @property
    def remote_branches(self):
        branches, __, exit_status = self._git_cmd(self._git_path, 'ls-remote --heads {}'.format(sickrage.app.git_remote_url))
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

        # check if branch exists on remote
        if self.current_branch not in self.remote_branches:
            return

        # get all new info from server
        output, __, exit_status = self._git_cmd(self._git_path, 'remote update')
        if not exit_status == 0:
            sickrage.app.log.warning("Unable to contact server, can't check for update")
            if output:
                sickrage.app.log.debug("GIT CMD OUTPUT: {}".format(output.strip()))
            return

        # get number of commits behind and ahead (option --count not supported git < 1.7.2)
        output, __, exit_status = self._git_cmd(self._git_path, 'rev-list --left-right origin/{}...HEAD'.format(self.current_branch))
        if exit_status == 0 and output:
            try:
                self._num_commits_behind = int(output.count("<"))
                self._num_commits_ahead = int(output.count(">"))
            except Exception:
                sickrage.app.log.debug("Unable to determine number of commits ahead or behind for git install, failed new version check.")
                return

        # get latest commit_hash from remote
        output, __, exit_status = self._git_cmd(self._git_path, 'rev-parse --verify --quiet origin/{}'.format(self.current_branch))
        if exit_status == 0 and output:
            return output.strip()

    def set_newest_text(self):
        if self.version != self.get_newest_version:
            newest_text = _('There is a newer version available, version {} &mdash; <a href=\"{}\">Update Now</a>').format(
                self.get_newest_version, self.get_update_url())
            sickrage.app.newest_version_string = newest_text

    def need_update(self):
        try:
            return (False, True)[self.version != self.get_newest_version and self._num_commits_behind > 0]
        except Exception as e:
            sickrage.app.log.error("Unable to contact server, can't check for update: " + repr(e))
            return False

    def update(self):
        """
        Calls git pull origin <branch> in order to update SiCKRAGE. Returns a bool depending
        on the call's success.
        """

        if sickrage.app.config.general.git_reset:
            self.reset()

        if not self.upgrade_pip():
            return False

        if not self.install_requirements(self.current_branch):
            return False

        __, __, exit_status = self._git_cmd(self._git_path, 'pull -f {} {}'.format(sickrage.app.git_remote_url,
                                                                                   self.current_branch))
        if exit_status == 0:
            sickrage.app.log.info("Updating SiCKRAGE from GIT servers")
            sickrage.app.alerts.message(_('Updater'), _('Updating SiCKRAGE from GIT servers'))
            NotificationProvider.mass_notify_version_update(self.get_newest_version)
            return True

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

            if not self.upgrade_pip():
                return False

            if not self.install_requirements(self.current_branch):
                return False

            # remove untracked files and performs a hard reset on git branch to avoid update issues
            if sickrage.app.config.general.git_reset:
                self.reset()

            # fetch all branches
            self.fetch()

            __, __, exit_status = self._git_cmd(self._git_path, 'checkout -f ' + branch)
            if exit_status == 0:
                return True

        return False

    def get_remote_url(self):
        url, __, exit_status = self._git_cmd(self._git_path,
                                             'remote get-url {}'.format(sickrage.app.git_remote_url))
        return ("", url)[exit_status == 0 and url is not None]

    def set_remote_url(self):
        if not sickrage.app.developer:
            self._git_cmd(self._git_path, 'remote set-url {} {}'.format(sickrage.app.git_remote_url,
                                                                        sickrage.app.app.git_remote_url))


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
        current_version_match = self.version_regex.match(self.version)
        new_version_match = self.version_regex.match(self.get_newest_version)

        if current_version_match and new_version_match:
            for version_label in ['major', 'minor', 'patch', 'pre_release']:
                try:
                    if version_label not in current_version_match.groupdict().keys() or version_label not in new_version_match.groupdict().keys():
                        continue

                    current_version_part = current_version_match.group(version_label)
                    new_version_part = new_version_match.group(version_label)

                    if current_version_part is None or new_version_part is None:
                        continue

                    if int(new_version_part) > int(current_version_part):
                        return True
                except (IndexError, TypeError):
                    continue

    def _check_for_new_version(self):
        git_version_url = "https://git.sickrage.ca/SiCKRAGE/sickrage/raw/{}/sickrage/version.txt"

        try:
            return WebSession().get(git_version_url.format(('master', 'develop')['dev' in self.version])).text
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

        tar_download_url = 'https://git.sickrage.ca/SiCKRAGE/sickrage/repository/archive.tar.gz?ref={}'.format(('master', 'develop')['dev' in self.version])

        try:
            if not self.upgrade_pip():
                return False

            if not self.install_requirements(self.current_branch):
                return False

            with tempfile.TemporaryFile() as update_tarfile:
                sickrage.app.log.info("Downloading update from " + repr(tar_download_url))
                resp = WebSession().get(tar_download_url)
                if not resp or not resp.content:
                    sickrage.app.log.warning('Failed to download SiCKRAGE update')
                    return False

                update_tarfile.write(resp.content)
                update_tarfile.seek(0)

                with tempfile.TemporaryDirectory(prefix='sr_update_', dir=sickrage.app.data_dir) as unpack_dir:
                    sickrage.app.log.info("Extracting SiCKRAGE update file")
                    try:
                        tar = tarfile.open(fileobj=update_tarfile, mode='r:gz')
                        tar.extractall(unpack_dir)
                        tar.close()
                    except tarfile.TarError:
                        sickrage.app.log.warning("Invalid update data, update failed: not a gzip file")
                        return False

                    if len(os.listdir(unpack_dir)) != 1:
                        sickrage.app.log.warning("Invalid update data, update failed")
                        return False

                    update_dir = os.path.join(*[unpack_dir, os.listdir(unpack_dir)[0], 'sickrage'])
                    sickrage.app.log.info("Sync folder {} to {}".format(update_dir, sickrage.PROG_DIR))
                    dirsync.sync(update_dir, sickrage.PROG_DIR, 'sync', purge=True)
        except Exception as e:
            sickrage.app.log.error("Error while trying to update: {}".format(e))
            return False

        # Notify update successful
        NotificationProvider.mass_notify_version_update(self.get_newest_version)

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
        out, __, exit_status = self._pip_cmd('show sickrage')
        if exit_status == 0:
            return out.split('\n')[1].split()[1]
        return ""

    def need_update(self):
        # need this to run first to set self._newest_commit_hash
        try:
            pypi_version = self.get_newest_version
            if self.version != pypi_version:
                sickrage.app.log.debug("Version upgrade: " + self._find_installed_version() + " -> " + pypi_version)
                return True
        except Exception as e:
            sickrage.app.log.warning("Unable to contact PyPi, can't check for update: " + repr(e))
            return False

    def _check_for_new_version(self):
        from distutils.version import LooseVersion
        url = "https://pypi.org/pypi/{}/json".format('sickrage')

        try:
            resp = WebSession().get(url)
            versions = resp.json()["releases"].keys()
            versions = [x for x in versions if 'dev' not in x]
            versions.sort(key=LooseVersion, reverse=True)
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
        __, __, exit_status = self._pip_cmd('install -U --no-cache-dir sickrage')
        if exit_status == 0:
            sickrage.app.log.info("Updating SiCKRAGE from PyPi servers")
            sickrage.app.alerts.message(_('Updater'), _('Updating SiCKRAGE from PyPi servers'))
            NotificationProvider.mass_notify_version_update(self.get_newest_version)
            return True

        return False
