# Author: echel0n <sickrage.tv@gmail.com>
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
import os
import platform
import re
import subprocess
import time
import traceback

import github

import sickrage
from sickrage.core.databases import main_db
from sickrage.core.helpers import backupAll, getURL
from sickrage.core.ui import notifications
from sickrage.notifiers import notify_version_update


class VersionUpdater(object):
    """
    Version check class meant to run as a thread object with the sr scheduler.
    """

    def __init__(self, **kwargs):
        self.name = "VERSIONUPDATER"
        self.amActive = False
        self.updater = (SourceUpdateManager(), GitUpdateManager())[self.find_install_type() == 'git']
        self.session = None

    def run(self, force=False):
        if self.amActive:
            return

        self.amActive = True

        try:
            if self.updater:
                if self.check_for_new_version(force):
                    if self.run_backup_if_safe() is True:
                        from sickrage.core.ui import notifications
                        if self.update():
                            sickrage.LOGGER.info("Update was successful!")
                            notifications.message('Update was successful')
                            sickrage.WEB_SERVER.server_restart()
                        else:
                            sickrage.LOGGER.info("Update failed!")
                            notifications.message('Update failed!')

                self.check_for_new_news(force)
        finally:self.amActive = False

    def run_backup_if_safe(self):
        return self.safe_to_update() is True and self._runbackup() is True

    def _runbackup(self):
        # Do a system backup before update
        sickrage.LOGGER.info("Config backup in progress...")
        notifications.message('Backup', 'Config backup in progress...')
        try:
            backupDir = os.path.join(sickrage.DATA_DIR, 'backup')
            if not os.path.isdir(backupDir):
                os.mkdir(backupDir)

            if self._keeplatestbackup(backupDir) and backupAll(backupDir):
                sickrage.LOGGER.info("Config backup successful, updating...")
                notifications.message('Backup', 'Config backup successful, updating...')
                return True
            else:
                sickrage.LOGGER.error("Config backup failed, aborting update")
                notifications.message('Backup', 'Config backup failed, aborting update')
                return False
        except Exception as e:
            sickrage.LOGGER.error('Update: Config backup failed. Error: %s' % e)
            notifications.message('Backup', 'Config backup failed, aborting update')
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

    def getDBcompare(self):
        try:
            self.updater.need_update()
            cur_hash = str(self.updater.get_newest_commit_hash)
            assert len(cur_hash) is 40, "Commit hash wrong length: %s hash: %s" % (len(cur_hash), cur_hash)

            check_url = "http://cdn.rawgit.com/%s/%s/%s/sickrage/databases/main_db.py" % (
                sickrage.GIT_ORG, sickrage.GIT_REPO, cur_hash)
            response = getURL(check_url, session=self.session)
            assert response, "Empty response from %s" % check_url

            match = re.search(r"MAX_DB_VERSION\s=\s(?P<version>\d{2,3})", response)
            branchDestDBversion = int(match.group('version'))
            branchCurrDBversion = main_db.MainDB().checkDBVersion()
            if branchDestDBversion > branchCurrDBversion:
                return 'upgrade'
            elif branchDestDBversion == branchCurrDBversion:
                return 'equal'
            else:
                return 'downgrade'
        except:
            raise

    def safe_to_update(self):
        def db_safe():
            try:
                result = self.getDBcompare()

                if result == 'equal':
                    sickrage.LOGGER.debug("We can proceed with the update. New update has same DB version")
                    return True
                elif result == 'upgrade':
                    sickrage.LOGGER.warning(
                            "We can't proceed with the update. New update has a new DB version. Please manually update")
                    return False
                elif result == 'downgrade':
                    sickrage.LOGGER.error(
                            "We can't proceed with the update. New update has a old DB version. It's not possible to downgrade")
                    return False
            except Exception as e:
                sickrage.LOGGER.error(
                        "We can't proceed with the update. Unable to compare DB version. Error: %s" % repr(e))

        def postprocessor_safe():
            if not sickrage.STARTED:
                return True

            if not sickrage.Scheduler.get_job('POSTPROCESSOR').func.im_self.amActive:
                sickrage.LOGGER.debug("We can proceed with the update. Post-Processor is not running")
                return True
            else:
                sickrage.LOGGER.debug("We can't proceed with the update. Post-Processor is running")
                return False

        def showupdate_safe():
            if not sickrage.STARTED:
                return True

            if not sickrage.Scheduler.get_job('SHOWUPDATER').func.im_self.amActive:
                sickrage.LOGGER.debug("We can proceed with the update. Shows are not being updated")
                return True
            else:
                sickrage.LOGGER.debug("We can't proceed with the update. Shows are being updated")
                return False

        if postprocessor_safe() and showupdate_safe():
            sickrage.LOGGER.debug("Safely proceeding with auto update")
            return True

        sickrage.LOGGER.debug("Unsafe to auto update currently, aborted")

    @staticmethod
    def find_install_type():
        """
        Determines how this copy of sr was installed.

        returns: type of installation. Possible values are:

            'git': running from source using git
            'source': running from source without git
        """

        if os.path.isdir(os.path.join(sickrage.ROOT_DIR, '.git')):
            install_type = 'git'
        else:
            install_type = 'source'

        return install_type

    def check_for_new_version(self, force=False):
        """
        Checks the internet for a newer version.

        returns: bool, True for new version or False for no new version.
        :param force: if true the VERSION_NOTIFY setting will be ignored and a check will be forced
        """

        if not self.updater or (not sickrage.VERSION_NOTIFY and not sickrage.AUTO_UPDATE and not force):
            sickrage.LOGGER.info("Version checking is disabled, not checking for the newest version")
            return False

        # checking for updates
        if force or not sickrage.AUTO_UPDATE:
            sickrage.LOGGER.info("Checking for updates using " + self.updater.type.upper())

        if self.updater.need_update():
            self.updater.set_newest_text()

            if sickrage.AUTO_UPDATE:
                sickrage.LOGGER.info("New update found for SiCKRAGE, starting auto-updater ...")
                notifications.message('New update found for SiCKRAGE, starting auto-updater')

            return True

        # no updates needed if we made it here
        if force:
            notifications.message('No update needed')
            sickrage.LOGGER.info("No update needed")

    def check_for_new_news(self, force=False):
        """
        Checks GitHub for the latest news.

        returns: unicode, a copy of the news

        force: ignored
        """

        news = ''

        # Grab a copy of the news
        sickrage.LOGGER.debug('check_for_new_news: Checking GitHub for latest news.')
        try:
            news = getURL(sickrage.NEWS_URL, session=self.session)
        except:
            sickrage.LOGGER.warning('check_for_new_news: Could not load news from repo.')

        if news:
            dates = re.finditer(r'^####(\d{4}-\d{2}-\d{2})####$', news, re.M)
            if not list(dates):
                return news or ''

            try:
                last_read = datetime.datetime.strptime(sickrage.NEWS_LAST_READ, '%Y-%m-%d')
            except:
                last_read = 0

            sickrage.NEWS_UNREAD = 0
            gotLatest = False
            for match in dates:
                if not gotLatest:
                    gotLatest = True
                    sickrage.NEWS_LATEST = match.group(1)

                try:
                    if datetime.datetime.strptime(match.group(1), '%Y-%m-%d') > last_read:
                        sickrage.NEWS_UNREAD += 1
                except Exception:
                    pass

        return news

    def update(self):
        if self.updater:
            # update branch with current config branch value
            self.updater.branch = sickrage.VERSION

            # check for updates
            if self.updater.need_update():
                update_status = self.updater.update()
                if update_status:
                    # Clean up after update
                    toclean = os.path.join(sickrage.CACHE_DIR, 'mako')
                    for root, dirs, files in os.walk(toclean, topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
                    return True

    @property
    def list_remote_branches(self):
        if self.updater:
            return self.updater.list_remote_branches

    @property
    def get_branch(self):
        if self.updater:
            return self.updater.branch


class UpdateManager(object):
    @staticmethod
    def get_github_org():
        return sickrage.GIT_ORG

    @staticmethod
    def get_github_repo():
        return sickrage.GIT_REPO

    @staticmethod
    def get_update_url():
        return "home/update/?pid={}".format(sickrage.PID)


class GitUpdateManager(UpdateManager):
    def __init__(self):
        self.type = "git"

        # init github api
        self._git_path = self._find_working_git
        self.github_org = self.get_github_org()
        self.github_repo = self.get_github_repo()
        self.init_github()

        self._cur_commit_hash = ""
        self._newest_commit_hash = ""
        self._num_commits_behind = 0
        self._num_commits_ahead = 0

        self.branch = sickrage.VERSION = self._find_installed_version()

    def init_github(self):
        try:
            sickrage.GITHUB = github.Github(
                    login_or_token=sickrage.GIT_USERNAME,
                    password=sickrage.GIT_PASSWORD,
                    user_agent="SiCKRAGE")
        except:
            sickrage.GITHUB = github.Github(user_agent="SiCKRAGE")

    @property
    def get_cur_commit_hash(self):
        return self._cur_commit_hash

    @property
    def get_newest_commit_hash(self):
        return self._newest_commit_hash

    @property
    def get_cur_version(self):
        return self._find_installed_version()

    @property
    def get_newest_version(self):
        return self._run_git(self._git_path, "describe --abbrev=0 " + self._newest_commit_hash)[0]

    @property
    def get_num_commits_behind(self):
        return self._num_commits_behind

    @staticmethod
    def _git_error():
        error_message = 'Unable to find your git executable - Shutdown SiCKRAGE and EITHER set git_path in your config.ini OR delete your .git folder and run from source to enable updates.'
        sickrage.NEWEST_VERSION_STRING = error_message

    @property
    def _find_working_git(self):
        test_cmd = 'version'

        if sickrage.GIT_PATH:
            main_git = '"' + sickrage.GIT_PATH + '"'
        else:
            main_git = 'git'

        sickrage.LOGGER.debug("Checking if we can use git commands: " + main_git + ' ' + test_cmd)
        _, _, exit_status = self._run_git(main_git, test_cmd)

        if exit_status == 0:
            sickrage.LOGGER.debug("Using: " + main_git)
            return main_git
        else:
            sickrage.LOGGER.debug("Not using: " + main_git)

        # trying alternatives


        alternative_git = []

        # osx people who start sr from launchd have a broken path, so try a hail-mary attempt for them
        if platform.system().lower() == 'darwin':
            alternative_git.append('/usr/local/git/bin/git')

        if platform.system().lower() == 'windows':
            if main_git != main_git.lower():
                alternative_git.append(main_git.lower())

        if alternative_git:
            sickrage.LOGGER.debug("Trying known alternative git locations")

            for cur_git in alternative_git:
                sickrage.LOGGER.debug("Checking if we can use git commands: " + cur_git + ' ' + test_cmd)
                _, _, exit_status = self._run_git(cur_git, test_cmd)

                if exit_status == 0:
                    sickrage.LOGGER.debug("Using: " + cur_git)
                    return cur_git
                else:
                    sickrage.LOGGER.debug("Not using: " + cur_git)

        # Still haven't found a working git
        error_message = 'Unable to find your git executable - Shutdown SiCKRAGE and EITHER set git_path in your config.ini OR delete your .git folder and run from source to enable updates.'
        sickrage.NEWEST_VERSION_STRING = error_message

        return None

    @staticmethod
    def _run_git(git_path, args):

        output = err = None

        if not git_path:
            sickrage.LOGGER.warning("No git specified, can't use git commands")
            exit_status = 1
            return output, err, exit_status

        cmd = git_path + ' ' + args

        try:
            sickrage.LOGGER.debug("Executing " + cmd + " with your shell in " + sickrage.ROOT_DIR)
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 shell=True, cwd=sickrage.ROOT_DIR)
            output, err = p.communicate()
            exit_status = p.returncode

            if output:
                output = output.strip()


        except OSError:
            sickrage.LOGGER.info("Command " + cmd + " didn't work")
            exit_status = 1

        if exit_status == 0:
            sickrage.LOGGER.debug(cmd + " : returned successful")
            exit_status = 0

        elif exit_status == 1:
            if 'stash' in output:
                sickrage.LOGGER.warning("Please enable 'git reset' in settings or stash your changes in local files")
            else:
                sickrage.LOGGER.error(cmd + " returned : " + str(output))
            exit_status = 1

        elif exit_status == 128 or 'fatal:' in output or err:
            sickrage.LOGGER.debug(cmd + " returned : " + str(output))
            exit_status = 128

        else:
            sickrage.LOGGER.error(cmd + " returned : " + str(output) + ", treat as error for now")
            exit_status = 1

        return output, err, exit_status

    def _find_installed_commit(self):
        """
        Attempts to find the currently installed version of SiCKRAGE.

        Uses git show to get commit version.

        Returns: True for success or False for failure
        """

        output, _, exit_status = self._run_git(self._git_path, 'rev-parse HEAD')  # @UnusedVariable

        if exit_status == 0 and output:
            cur_commit_hash = output.strip()
            if not re.match('^[a-z0-9]+$', cur_commit_hash):
                sickrage.LOGGER.error("Output doesn't look like a hash, not using it")
                return False
            self._cur_commit_hash = cur_commit_hash
            sickrage.CUR_COMMIT_HASH = str(cur_commit_hash)
            return True
        else:
            return False

    def _find_installed_version(self):
        branch_info, _, exit_status = self._run_git(self._git_path, 'symbolic-ref -q HEAD')  # @UnusedVariable
        if exit_status == 0 and branch_info:
            return branch_info.strip().replace('refs/heads/', '', 1).strip()

        return ""

    def _check_for_new_version(self):
        """
        Uses git commands to check if there is a newer version that the provided
        commit hash. If there is a newer version it sets _num_commits_behind.
        """

        self._num_commits_behind = 0
        self._num_commits_ahead = 0

        # update remote origin url
        self.update_remote_origin()

        # get all new info from github
        output, _, exit_status = self._run_git(self._git_path, 'fetch %s' % sickrage.GIT_REMOTE)
        if not exit_status == 0:
            sickrage.LOGGER.warning("Unable to contact github, can't check for update")
            return

        # get latest commit_hash from remote
        output, _, exit_status = self._run_git(self._git_path, 'rev-parse --verify --quiet "@{upstream}"')

        if exit_status == 0 and output:
            cur_commit_hash = output.strip()

            if not re.match('^[a-z0-9]+$', cur_commit_hash):
                sickrage.LOGGER.debug("Output doesn't look like a hash, not using it")
                return

            else:
                self._newest_commit_hash = cur_commit_hash
        else:
            sickrage.LOGGER.debug("git didn't return newest commit hash")
            return

        # get number of commits behind and ahead (option --count not supported git < 1.7.2)
        output, _, exit_status = self._run_git(self._git_path, 'rev-list --left-right "@{upstream}"...HEAD')
        if exit_status == 0 and output:

            try:
                self._num_commits_behind = int(output.count("<"))
                self._num_commits_ahead = int(output.count(">"))

            except Exception:
                sickrage.LOGGER.debug("git didn't return numbers for behind and ahead, not using it")
                return

        sickrage.LOGGER.debug("cur_commit = %s, newest_commit = %s, num_commits_behind = %s, num_commits_ahead = %s" %
                              (
                                  self._cur_commit_hash, self._newest_commit_hash, self._num_commits_behind,
                                  self._num_commits_ahead))

    def set_newest_text(self):

        # if we're up to date then don't set this
        sickrage.NEWEST_VERSION_STRING = None

        if self._num_commits_ahead:
            sickrage.LOGGER.warning("Local branch is ahead of " + self.branch + ". Automatic update not possible.")
            newest_text = "Local branch is ahead of " + self.branch + ". Automatic update not possible."

        elif self._num_commits_behind > 0:

            base_url = 'http://github.com/' + self.github_org + '/' + self.github_repo
            if self._newest_commit_hash:
                url = base_url + '/compare/' + self._cur_commit_hash + '...' + self._newest_commit_hash
            else:
                url = base_url + '/commits/'

            newest_text = 'There is a <a href="{}" onclick="window.open(this.href); return false;">newer version available</a> '.format(url)
            newest_text += " (you're {} commit(s)".format(self._num_commits_behind)
            newest_text += ' behind)' + "&mdash; <a href=\"{}\">Update Now</a>".format(self.get_update_url())
        else:
            return

        sickrage.NEWEST_VERSION_STRING = newest_text

    def need_update(self):

        if self.branch != self._find_installed_version():
            sickrage.LOGGER.debug("Branch checkout: " + self._find_installed_version() + "->" + self.branch)
            return True

        self._find_installed_version()
        if not self._cur_commit_hash:
            return True
        else:
            try:
                self._check_for_new_version()
            except Exception as e:
                sickrage.LOGGER.warning("Unable to contact github, can't check for update: " + repr(e))
                return False

            if self._num_commits_behind > 0:
                return True

        return False

    def update(self):
        """
        Calls git pull origin <branch> in order to update SiCKRAGE. Returns a bool depending
        on the call's success.
        """

        # update remote origin url
        self.update_remote_origin()

        # remove untracked files and performs a hard reset on git branch to avoid update issues
        if sickrage.GIT_RESET:
            # self.clean() # This is removing user data and backups
            self.reset()

        if self.branch == self._find_installed_version():
            _, _, exit_status = self._run_git(self._git_path,
                                              'pull -f %s %s' % (sickrage.GIT_REMOTE, self.branch))  # @UnusedVariable
        else:
            _, _, exit_status = self._run_git(self._git_path, 'checkout -f ' + self.branch)  # @UnusedVariable

        if exit_status == 0:
            _, _, exit_status = self._run_git(self._git_path, 'submodule update --init --recursive')

            if exit_status == 0:
                self._find_installed_version()

                # Notify update successful
                if sickrage.NOTIFY_ON_UPDATE:
                    notify_version_update(sickrage.CUR_COMMIT_HASH or "")

                return True

            else:
                return False

        else:
            return False

    def clean(self):
        """
        Calls git clean to remove all untracked files. Returns a bool depending
        on the call's success.
        """
        _, _, exit_status = self._run_git(self._git_path, 'clean -df ""')  # @UnusedVariable
        if exit_status == 0:
            return True

    def reset(self):
        """
        Calls git reset --hard to perform a hard reset. Returns a bool depending
        on the call's success.
        """
        _, _, exit_status = self._run_git(self._git_path, 'reset --hard')  # @UnusedVariable
        if exit_status == 0:
            return True

    @property
    def list_remote_branches(self):
        # update remote origin url
        self.update_remote_origin()

        branches, _, exit_status = self._run_git(self._git_path,
                                                 'ls-remote --heads %s' % sickrage.GIT_REMOTE)  # @UnusedVariable
        if exit_status == 0 and branches:
            if branches:
                return re.findall(r'refs/heads/(.*)', branches)
        return []

    def update_remote_origin(self):
        self._run_git(self._git_path, 'config remote.%s.url %s' % (sickrage.GIT_REMOTE, sickrage.GIT_REMOTE_URL))
        if sickrage.GIT_USERNAME:
            self._run_git(self._git_path, 'config remote.%s.pushurl %s' % (
                sickrage.GIT_REMOTE, sickrage.GIT_REMOTE_URL.replace(sickrage.GIT_ORG, sickrage.GIT_USERNAME)))


class SourceUpdateManager(UpdateManager):
    def __init__(self):
        self.type = "source"

        self.github_org = self.get_github_org()
        self.github_repo = self.get_github_repo()

        self._cur_commit_hash = ""
        self._newest_commit_hash = ""
        self._num_commits_behind = 0

        self.branch = sickrage.VERSION = self._find_installed_version()

    @property
    def get_cur_commit_hash(self):
        return self._cur_commit_hash

    @property
    def get_newest_commit_hash(self):
        return self._newest_commit_hash

    @property
    def get_cur_version(self):
        return self._find_installed_version()

    @property
    def get_newest_version(self):
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

    def _find_installed_version(self):
        with open(os.path.join(sickrage.PROG_DIR, 'version.txt')) as f:
            return f.read().strip() or ""

    @property
    def get_num_commits_behind(self):
        return self._num_commits_behind

    def need_update(self):
        # need this to run first to set self._newest_commit_hash
        try:
            pypi_version = self.get_newest_version
            if self._find_installed_version() != pypi_version:
                self.branch = sickrage.VERSION = pypi_version
                sickrage.LOGGER.debug("Version upgrade: " + self._find_installed_version() + "->" + pypi_version)
                return True
        except Exception as e:
            sickrage.LOGGER.warning("Unable to contact PyPi, can't check for update: " + repr(e))
            return False

    def _check_for_new_version(self):
        return self.get_newest_version

    def set_newest_text(self):

        # if we're up to date then don't set this
        sickrage.NEWEST_VERSION_STRING = None

        if not sickrage.VERSION:
            sickrage.LOGGER.debug("Unknown current version number, don't know if we should update or not")

            newest_text = "Unknown current version number: If yo've never used the SiCKRAGE upgrade system before then current version is not set."
            newest_text += "&mdash; <a href=\"{}\">Update Now</a>".format(self.get_update_url())
            return
        else:
            newest_text = "New SiCKRAGE update found on PyPy servers, version {}".format(sickrage.VERSION)
            newest_text += "&mdash; <a href=\"{}\">Update Now</a>".format(self.get_update_url())

        sickrage.NEWEST_VERSION_STRING = newest_text

    def update(self):
        """
        Downloads the latest source tarball from github and installs it over the existing version.
        """
        try:
            import pip
            sickrage.LOGGER.info("Updating SiCKRAGE from PyPi servers")
            pip.main(['install', '-q', '-U', '--no-cache-dir', 'sickrage'])
        except Exception as e:
            sickrage.LOGGER.error("Error while trying to update: {}".format(e))
            sickrage.LOGGER.debug("Traceback: " + traceback.format_exc())
            return False

        # Notify update successful
        notify_version_update(sickrage.NEWEST_VERSION_STRING)

        return True

    @property
    def list_remote_branches(self):
        return []
