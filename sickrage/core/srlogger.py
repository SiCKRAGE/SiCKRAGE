#!/usr/bin/env python2

# Author: echel0n <echel0n@sickrage.ca>
# URL: https://git.sickrage.ca
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

import io
import locale
import logging
import os
import platform
import re
import sys
import traceback
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING
from logging.handlers import RotatingFileHandler

# logging.basicConfig()
import sickrage

from sickrage.core import makeDir

class srLogger(logging.getLoggerClass()):
    logging.captureWarnings(True)
    logging.getLogger().addHandler(logging.NullHandler())

    def __init__(self, name="sickrage"):
        super(srLogger, self).__init__(name)
        self.propagate = False

        self.consoleLogging = True
        self.fileLogging = False
        self.debugLogging = False

        self.logFile = None
        self.logSize = 1048576
        self.logNr = 5

        self.submitter_running = False

        self.CRITICAL = CRITICAL
        self.DEBUG = DEBUG
        self.ERROR = ERROR
        self.WARNING = WARNING
        self.INFO = INFO
        self.DB = 5

        self.logLevels = {
            'CRITICAL': self.CRITICAL,
            'ERROR': self.ERROR,
            'WARNING': self.WARNING,
            'INFO': self.INFO,
            'DEBUG': self.DEBUG,
            'DB': 5
        }

        self.logNameFilters = {
            '': 'No Filter',
            'DAILYSEARCHER': 'Daily Searcher',
            'BACKLOG': 'Backlog',
            'SHOWUPDATER': 'Show Updater',
            'VERSIONUPDATER': 'Check Version',
            'SHOWQUEUE': 'Show Queue',
            'SEARCHQUEUE': 'Search Queue',
            'FINDPROPERS': 'Find Propers',
            'POSTPROCESSOR': 'Postprocesser',
            'SUBTITLESEARCHER': 'Find Subtitles',
            'TRAKTSEARCHER': 'Trakt Checker',
            'EVENT': 'Event',
            'ERROR': 'Error',
            'TORNADO': 'Tornado',
            'Thread': 'Thread',
            'MAIN': 'Main',
        }

        # list of allowed loggers
        self.allowedLoggers = ['sickrage',
                               'tornado.general',
                               'tornado.application',
                               'apscheduler.jobstores',
                               'apscheduler.scheduler']

        # set custom level for database logging
        logging.addLevelName(self.logLevels['DB'], 'DB')
        logging.getLogger("sickrage").setLevel(self.logLevels['DB'])

        # start logger
        self.start()

    def start(self):
        # remove all handlers
        self.handlers = []

        # console log handler
        if self.consoleLogging:
            console = logging.StreamHandler()
            console.setFormatter(
                logging.Formatter('%(asctime)s %(levelname)s::%(threadName)s::%(message)s', '%H:%M:%S'))
            console.setLevel(self.logLevels['INFO'] if not self.debugLogging else self.logLevels['DEBUG'])
            self.addHandler(console)

        # rotating log file handlers
        if self.logFile and makeDir(os.path.dirname(self.logFile)):
            rfh = RotatingFileHandler(
                filename=self.logFile,
                maxBytes=self.logSize,
                backupCount=self.logNr
            )

            rfh_errors = RotatingFileHandler(
                filename=self.logFile.replace('.log', '.error.log'),
                maxBytes=self.logSize,
                backupCount=self.logNr
            )

            rfh.setFormatter(
                logging.Formatter('%(asctime)s %(levelname)s::%(threadName)s::%(message)s', '%Y-%m-%d %H:%M:%S'))
            rfh.setLevel(self.logLevels['INFO'] if not self.debugLogging else self.logLevels['DEBUG'])
            self.addHandler(rfh)

            rfh_errors.setFormatter(
                logging.Formatter('%(asctime)s %(levelname)s::%(threadName)s::%(message)s', '%Y-%m-%d %H:%M:%S'))
            rfh_errors.setLevel(self.logLevels['ERROR'])
            self.addHandler(rfh_errors)

    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None):
        if (False, True)[name in self.allowedLoggers]:
            record = super(srLogger, self).makeRecord(name, level, fn, lno, msg, args, exc_info, func, extra)

            try:
                record.msg = re.sub(
                    r"(.*)\b({})\b(.*)".format(
                        '|'.join([x for x in sickrage.srCore.srConfig.CENSORED_ITEMS.values() if len(x)])), r"\1\3",
                    record.msg)

                # needed because Newznab apikey isn't stored as key=value in a section.
                record.msg = re.sub(r"([&?]r|[&?]apikey|[&?]api_key)=[^&]*([&\w]?)", r"\1=**********\2", record.msg)
            except:
                pass

            # sending record to UI
            if record.levelno in [WARNING, ERROR]:
                from sickrage.core.classes import WarningViewer
                from sickrage.core.classes import ErrorViewer
                (WarningViewer(), ErrorViewer())[record.levelno == ERROR].add(record.msg, True)

            return record

    def log(self, level, msg, *args, **kwargs):
        super(srLogger, self).log(level, msg, *args, **kwargs)

    def db(self, msg, *args, **kwargs):
        super(srLogger, self).log(self.logLevels['DB'], msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        super(srLogger, self).info(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        super(srLogger, self).debug(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        super(srLogger, self).critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        super(srLogger, self).exception(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        super(srLogger, self).error(msg, exc_info=1, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        super(srLogger, self).warning(msg, *args, **kwargs)

    def log_error_and_exit(self, msg, *args, **kwargs):
        if self.consoleLogging:
            sys.exit(super(srLogger, self).error(msg, *args, **kwargs))
        sys.exit(1)

    def submit_errors(self):  # Too many local variables, too many branches, pylint: disable=R0912,R0914
        import sickrage

        submitter_result = None
        issue_id = None

        from sickrage.core.classes import ErrorViewer
        if not (
                    sickrage.srCore.srConfig.GIT_USERNAME and sickrage.srCore.srConfig.GIT_PASSWORD and sickrage.DEBUG and len(
                ErrorViewer.errors) > 0):
            submitter_result = 'Please set your GitHub username and password in the config and enable debug. Unable to submit issue ticket to GitHub!'
            return submitter_result, issue_id

        try:
            from version_updater import srVersionUpdater

            sickrage.srCore.VERSIONUPDATER.check_for_new_version()
        except Exception:
            submitter_result = 'Could not check if your SiCKRAGE is updated, unable to submit issue ticket to GitHub!'
            return submitter_result, issue_id

        if self.submitter_running:
            submitter_result = 'Issue submitter is running, please wait for it to complete'
            return submitter_result, issue_id

        self.submitter_running = True

        gh_org = sickrage.srCore.srConfig.GIT_ORG or 'SiCKRAGETV'
        gh_repo = 'sickrage-issues'

        import github
        gh = github.Github(login_or_token=sickrage.srCore.srConfig.GIT_USERNAME,
                           password=sickrage.srCore.srConfig.GIT_PASSWORD,
                           user_agent="SiCKRAGE")

        try:
            # read log file
            log_data = None

            if os.path.isfile(self.logFile):
                with io.open(self.logFile, 'r') as f:
                    log_data = f.readlines()

            for i in range(1, int(sickrage.srCore.srConfig.LOG_NR)):
                if os.path.isfile(self.logFile + ".%i" % i) and (len(log_data) <= 500):
                    with io.open(self.logFile + ".%i" % i, 'r') as f:
                        log_data += f.readlines()

            log_data = [line for line in reversed(log_data)]

            # parse and submit errors to issue tracker
            for curError in sorted(ErrorViewer.errors, key=lambda error: error.time, reverse=True)[:500]:

                try:
                    title_Error = "[APP SUBMITTED]: {}".format(curError.title)
                    if not len(title_Error) or title_Error == 'None':
                        title_Error = re.match(r"^[A-Z0-9\-\[\] :]+::\s*(.*)$", curError.message).group(1)

                    if len(title_Error) > 1000:
                        title_Error = title_Error[0:1000]
                except Exception as e:
                    super(srLogger, self).error("Unable to get error title : {}".format(e.message))

                gist = None
                regex = r"^({})\s+([A-Z]+)\s+([0-9A-Z\-]+)\s*(.*)$".format(curError.time)
                for i, x in enumerate(log_data):
                    match = re.match(regex, x)
                    if match:
                        level = match.group(2)
                        # if level == srCore.LOGGER.ERROR:
                        # paste_data = "".join(log_data[i:i + 50])
                        # if paste_data:
                        #    gist = gh.get_user().create_gist(True, {"sickrage.log": InputFileContent(paste_data)})
                        # break
                    else:
                        gist = 'No ERROR found'

                message = "### INFO\n"
                message += "Python Version: **" + sys.version[:120].replace('\n', '') + "**\n"
                message += "Operating System: **" + platform.platform() + "**\n"
                try:
                    message += "Locale: " + locale.getdefaultlocale()[1] + "\n"
                except Exception:
                    message += "Locale: unknown" + "\n"
                message += "Version: **" + sickrage.srCore.VERSIONUPDATER.updater.version + "**\n"
                if hasattr(gist, 'html_url'):
                    message += "Link to Log: " + gist.html_url + "\n"
                else:
                    message += "No Log available with ERRORS: " + "\n"
                message += "### ERROR\n"
                message += "```\n"
                message += curError.message + "\n"
                message += "```\n"
                message += "---\n"
                message += "_STAFF NOTIFIED_: @SiCKRAGETV/owners @SiCKRAGETV/moderators"

                reports = gh.get_organization(gh_org).get_repo(gh_repo).get_issues(state="all")

                def is_ascii_error(title):
                    return re.search(r".* codec can't .*code .* in position .*:", title) is not None

                def is_malformed_error(title):
                    return re.search(r".* not well-formed \(invalid token\): line .* column .*", title) is not None

                ascii_error = is_ascii_error(title_Error)
                malformed_error = is_malformed_error(title_Error)

                issue_found = False
                for report in reports:
                    if title_Error.rsplit(' :: ')[-1] in report.title or \
                            (malformed_error and is_malformed_error(report.title)) or \
                            (ascii_error and is_ascii_error(report.title)):

                        issue_id = report.number
                        if not report.raw_data['locked']:
                            if report.create_comment(message):
                                submitter_result = 'Commented on existing issue #%s successfully!' % issue_id
                            else:
                                submitter_result = 'Failed to comment on found issue #%s!' % issue_id
                        else:
                            submitter_result = 'Issue #%s is locked, check github to find info about the error.' % issue_id

                        issue_found = True
                        break

                if not issue_found:
                    issue = gh.get_organization(gh_org).get_repo(gh_repo).create_issue(title_Error, message)
                    if issue:
                        issue_id = issue.number
                        submitter_result = 'Your issue ticket #%s was submitted successfully!' % issue_id
                    else:
                        submitter_result = 'Failed to create a new issue!'

                if issue_id and curError in ErrorViewer.errors:
                    # clear error from error list
                    ErrorViewer.errors.remove(curError)

        except Exception as e:
            super(srLogger, self).error(traceback.format_exc())
            submitter_result = 'Exception generated in issue submitter, please check the log'
        finally:
            self.submitter_running = False

        return submitter_result, issue_id

    @staticmethod
    def shutdown():
        logging.shutdown()
