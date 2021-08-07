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
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from distutils.version import LooseVersion
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
        # default to source install type
        install_type = SourceUpdateManager()

        if sickrage.install_type() == 'git':
            install_type = GitUpdateManager()
        elif sickrage.install_type() == 'windows':
            install_type = WindowsUpdateManager()
        elif sickrage.install_type() == 'synology':
            install_type = SynologyUpdateManager()
        elif sickrage.install_type() == 'docker':
            install_type = DockerUpdateManager()
        elif sickrage.install_type() == 'qnap':
            install_type = QnapUpdateManager()
        elif sickrage.install_type() == 'readynas':
            install_type = ReadynasUpdateManager()
        elif sickrage.install_type() == 'pip':
            install_type = PipUpdateManager()

        return install_type

    @property
    def version(self):
        return self.updater.version

    @property
    def branch(self):
        return self.updater.current_branch

    def task(self, force=False):
        if self.running:
            return

        try:
            self.running = True

            if not self.check_for_update():
                return

            if not sickrage.app.config.general.auto_update and not force:
                return

            if self.updater.manual_update:
                sickrage.app.log.debug("We can't proceed with auto-updating, install type only allows manual updating")
                return

            if sickrage.app.show_updater.running:
                sickrage.app.log.debug("We can't proceed with auto-updating, shows are being updated")
                return

            sickrage.app.log.info("New update found for SiCKRAGE, starting auto-updater ...")
            sickrage.app.alerts.message(_('Updater'), _('New update found for SiCKRAGE, starting auto-updater'))

            if self.update():
                sickrage.app.log.info("Update was successful!")
                sickrage.app.alerts.message(_('Updater'), _('Update was successful'))
                sickrage.app.restart()
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
            sickrage.app.log.warning(f'Update: Config backup failed. Error: {e!r}')
            sickrage.app.alerts.error(_('Updater'), _('Config backup failed, aborting update'))
            return False

    def safe_to_update(self):
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

    def check_for_update(self):
        """
        Checks the internet for a newer version.

        returns: bool, True for new version or False for no new version.
        :param force: forces return value of True
        """

        if sickrage.app.disable_updates:
            return False

        if not self.updater.need_update():
            return False

        self.updater.set_latest_version()

        return True

    def update(self, webui=False):
        # check if updater only allows manual updates
        if self.updater.manual_update:
            return False

        # check for updates
        if not self.updater.need_update():
            return False

        # check if its safe to update
        if not self.safe_to_update():
            return False

        # backup
        if sickrage.app.config.general.backup_on_update and not self.backup():
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
                WebSocketMessage('redirect', {'url': f'{sickrage.app.config.general.web_root}/home/restart/?pid={sickrage.app.pid}'}).push()

            return True

        if webui:
            sickrage.app.alerts.error(_("Updater"), _("Update wasn't successful, not restarting. Check your log for more information."))


class UpdateManager(object):
    def __init__(self):
        self.manual_update = False

    @property
    def version(self):
        return sickrage.version()

    @property
    def latest_version(self):
        releases = []
        latest_version = None

        try:
            version_url = "https://git.sickrage.ca/SiCKRAGE/sickrage/-/releases.json"
            resp = WebSession().get(version_url).json()

            if self.current_branch == 'develop':
                releases = [x['tag'] for x in resp if 'dev' in x['tag']]
            elif self.current_branch == 'master':
                releases = [x['tag'] for x in resp if 'dev' not in x['tag']]

            if releases:
                latest_version = sorted(releases, key=LooseVersion, reverse=True)[0]
        finally:
            return latest_version or self.version

    @property
    def current_branch(self):
        return ("master", "develop")["dev" in sickrage.version()]

    def need_update(self):
        try:
            latest_version = self.latest_version
            if LooseVersion(self.version) < LooseVersion(latest_version):
                sickrage.app.log.debug(f"SiCKRAGE version upgrade: {self.version} -> {latest_version}")
                return True
        except Exception as e:
            sickrage.app.log.warning(f"Unable to check for updates: {e!r}")
            return False

    def update(self):
        pass

    def set_latest_version(self):
        latest_version = self.latest_version

        if not self.manual_update:
            update_url = f"{sickrage.app.config.general.web_root}/home/update/?pid={sickrage.app.pid}"
            message = _(f'New SiCKRAGE {self.current_branch} {sickrage.install_type()} update available, version {latest_version} &mdash; <a href=\"{update_url}\">Update Now</a>')
        else:
            message = _(f"New SiCKRAGE {self.current_branch} {sickrage.install_type()} update available, version {latest_version}, please manually update!")

        sickrage.app.latest_version_string = message

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
            sickrage.app.log.info(f"Command {' '.join(cmd)} didn't work")
            exit_status = 1

        if exit_status == 0:
            exit_status = 0
        else:
            exit_status = 1

        if output:
            output = output.decode("utf-8", "ignore").strip() if isinstance(output, bytes) else output.strip()

        return output, err, exit_status

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
            sickrage.app.log.debug(f"PIP CMD OUTPUT: {output}")

    def install_requirements(self, branch):
        requirements_url = f"https://git.sickrage.ca/SiCKRAGE/sickrage/raw/{branch}/requirements.txt"
        requirements_file = tempfile.NamedTemporaryFile(delete=False)

        try:
            requirements_file.write(WebSession().get(requirements_url).content)
            requirements_file.close()
        except Exception:
            requirements_file.close()
            os.unlink(requirements_file.name)
            return False

        output, __, exit_status = self._pip_cmd(f'install --no-deps --no-cache-dir -r {requirements_file.name}')
        if exit_status != 0:
            __, __, exit_status = self._pip_cmd(f'install --no-deps --no-cache-dir --user -r {requirements_file.name}')

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
        super(GitUpdateManager, self).__init__()
        self.type = "git"
        self._num_commits_behind = 0
        self._num_commits_ahead = 0

    @property
    def version(self):
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

    @property
    def latest_version(self):
        """
        Uses git commands to check if there is a newer version that the provided
        commit hash. If there is a newer version it sets _num_commits_behind.
        """

        # check if branch exists on remote
        if self.current_branch not in self.remote_branches:
            return self.version

        # get all new info from server
        output, __, exit_status = self._git_cmd(self._git_path, 'remote update')
        if not exit_status == 0:
            sickrage.app.log.warning("Unable to contact server, can't check for update")

            if output:
                sickrage.app.log.debug(f'GIT CMD OUTPUT: {output.strip()}')

            return self.version

        # get number of commits behind and ahead (option --count not supported git < 1.7.2)
        output, __, exit_status = self._git_cmd(self._git_path, f'rev-list --left-right origin/{self.current_branch}...HEAD')
        if exit_status == 0 and output:
            try:
                self._num_commits_behind = int(output.count("<"))
                self._num_commits_ahead = int(output.count(">"))
            except Exception:
                sickrage.app.log.debug("Unable to determine number of commits ahead or behind for git install, failed new version check.")
                return self.version

        # get latest commit_hash from remote
        output, __, exit_status = self._git_cmd(self._git_path, f'rev-parse --verify --quiet origin/{self.current_branch}')
        if exit_status == 0 and output:
            return output.strip() or self.version

    @property
    def current_branch(self):
        branch_ref, __, exit_status = self._git_cmd(self._git_path, 'symbolic-ref -q HEAD')
        if exit_status == 0 and branch_ref is not None:
            return branch_ref.strip().replace('refs/heads/', '', 1)
        return ""

    @property
    def remote_branches(self):
        branches, __, exit_status = self._git_cmd(self._git_path, f'ls-remote --heads {sickrage.app.git_remote_url}')
        if exit_status == 0 and branches:
            return re.findall(r'refs/heads/(.*)', branches)

        return []

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
            sickrage.app.log.info(f"Command {' '.join(cmd)} didn\'t work")
            exit_status = 1

        if exit_status == 0:
            if not silent:
                sickrage.app.log.debug(f"{' '.join(cmd)} : returned successful")
            exit_status = 0
        elif exit_status == 1:
            if output:
                if 'stash' in output:
                    sickrage.app.log.warning("Please enable 'git reset' in settings or stash your changes in local files")
                else:
                    sickrage.app.log.debug(f"{' '.join(cmd)} returned : {str(output)}")
            else:
                sickrage.app.log.warning(f'{cmd} returned no data')
            exit_status = 1
        elif exit_status == 128 or 'fatal:' in output or err:
            sickrage.app.log.debug(f"{' '.join(cmd)} returned : {str(output)}")
            exit_status = 128
        else:
            sickrage.app.log.debug(f"{' '.join(cmd)} returned : {str(output)}, treat as error for now")
            exit_status = 1

        return output, err, exit_status

    def need_update(self):
        try:
            return self.version != self.latest_version and self._num_commits_behind > 0
        except Exception as e:
            sickrage.app.log.error(f"Unable to contact server, can't check for update: {e!r}")
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

        __, __, exit_status = self._git_cmd(self._git_path, f'pull -f {sickrage.app.git_remote_url} {self.current_branch}')
        if exit_status == 0:
            sickrage.app.log.info("Updating SiCKRAGE from GIT servers")
            sickrage.app.alerts.message(_('Updater'), _('Updating SiCKRAGE from GIT servers'))
            NotificationProvider.mass_notify_version_update(self.latest_version)
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
        __, __, exit_status = self._git_cmd(self._git_path, f'config remote.origin.fetch {"+refs/heads/*:refs/remotes/origin/*"}')
        if exit_status == 0:
            __, __, exit_status = self._git_cmd(self._git_path, 'fetch --all')
        return (False, True)[exit_status == 0]

    def checkout_branch(self, branch):
        if branch in self.remote_branches:
            sickrage.app.log.debug(f"Branch checkout: {self.version} -> {branch}")

            if not self.upgrade_pip():
                return False

            if not self.install_requirements(self.current_branch):
                return False

            # remove untracked files and performs a hard reset on git branch to avoid update issues
            if sickrage.app.config.general.git_reset:
                self.reset()

            # fetch all branches
            self.fetch()

            __, __, exit_status = self._git_cmd(self._git_path, f'checkout -f {branch}')
            if exit_status == 0:
                return True

        return False

    def get_remote_url(self):
        url, __, exit_status = self._git_cmd(self._git_path, f'remote get-url {sickrage.app.git_remote_url}')
        return ("", url)[exit_status == 0 and url is not None]

    def set_remote_url(self):
        if not sickrage.app.developer:
            self._git_cmd(self._git_path, f'remote set-url {sickrage.app.git_remote_url} {sickrage.app.app.git_remote_url}')


class WindowsUpdateManager(UpdateManager):
    def __init__(self):
        super(WindowsUpdateManager, self).__init__()
        self.type = "windows"
        self.manual_update = True


class SynologyUpdateManager(UpdateManager):
    def __init__(self):
        super(SynologyUpdateManager, self).__init__()
        self.type = "synology"
        self.manual_update = True


class DockerUpdateManager(UpdateManager):
    def __init__(self):
        super(DockerUpdateManager, self).__init__()
        self.type = "docker"
        self.manual_update = True


class ReadynasUpdateManager(UpdateManager):
    def __init__(self):
        super(ReadynasUpdateManager, self).__init__()
        self.type = "readynas"
        self.manual_update = True


class QnapUpdateManager(UpdateManager):
    def __init__(self):
        super(QnapUpdateManager, self).__init__()
        self.type = "qnap"
        self.manual_update = True


class PipUpdateManager(UpdateManager):
    def __init__(self):
        super(PipUpdateManager, self).__init__()
        self.type = "pip"
        self.manual_update = True


class SourceUpdateManager(UpdateManager):
    def __init__(self):
        super(SourceUpdateManager, self).__init__()
        self.type = "source"

    def update(self):
        """
        Downloads the latest source tarball from server and installs it over the existing version.
        """

        latest_version = self.latest_version

        tar_download_url = f'https://git.sickrage.ca/SiCKRAGE/sickrage/-/archive/{latest_version}/sickrage-{latest_version}.tar.gz'

        try:
            if not self.upgrade_pip():
                return False

            if not self.install_requirements(self.current_branch):
                return False

            retry_count = 0
            while retry_count < 3:
                with tempfile.TemporaryFile() as update_tarfile:
                    sickrage.app.log.info(f"Downloading update from {tar_download_url!r}")
                    resp = WebSession().get(tar_download_url)
                    if not resp or not resp.content:
                        sickrage.app.log.warning('Failed to download SiCKRAGE update')
                        retry_count += 1
                        continue

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
                            retry_count += 1
                            continue

                        if len(os.listdir(unpack_dir)) != 1:
                            sickrage.app.log.warning("Invalid update data, update failed")
                            retry_count += 1
                            continue

                        update_dir = os.path.join(*[unpack_dir, os.listdir(unpack_dir)[0], 'sickrage'])
                        sickrage.app.log.info(f"Sync folder {update_dir} to {sickrage.PROG_DIR}")
                        dirsync.sync(update_dir, sickrage.PROG_DIR, 'sync', purge=True)

                        # Notify update successful
                        NotificationProvider.mass_notify_version_update(latest_version)

                        return True
        except Exception as e:
            sickrage.app.log.error(f"Error while trying to update: {e!r}")
            return False
