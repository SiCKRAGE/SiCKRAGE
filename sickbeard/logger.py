#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Author: echel0n <sickrage.tv@gmail.com>
# URL: http://www.github.com/sickragetv/sickrage/
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
import os
import re
import abc
import sys
import locale
import github
import platform
import threading
import traceback

import logging
import logging.handlers
from logging import INFO, WARNING, ERROR, DEBUG, NOTSET, NullHandler

import sickbeard
from sickbeard import classes
from sickrage.helper.common import dateTimeFormat
from sickrage.helper.encoding import ek
from sickrage.helper.exceptions import ex

class SRLogger(logging.Logger):

    def __init__(self, name='root', *args, **kwargs):
        logging.Logger.__init__(self, name, *args, **kwargs)
        logging.setLoggerClass(CustomLogger)

        self.logFile = None
        self.consoleLogging = True
        self.fileLogging = False
        self.debugLogging = False
        self.logSize = 1048576
        self.logNr = 5
        self.censoredItems = {}

        self.submitter_running = False

        self.logLevels = {
            'ERROR': ERROR,
            'WARNING': WARNING,
            'INFO': INFO,
            'DEBUG': DEBUG,
            'DB': 5
        }

        self.logNameFilters = {
            '': 'No Filter',
            'DAILYSEARCHER': 'Daily Searcher',
            'BACKLOG': 'Backlog',
            'SHOWUPDATER': 'Show Updater',
            'CHECKVERSION': 'Check Version',
            'SHOWQUEUE': 'Show Queue',
            'SEARCHQUEUE': 'Search Queue',
            'FINDPROPERS': 'Find Propers',
            'POSTPROCESSER': 'Postprocesser',
            'FINDSUBTITLES': 'Find Subtitles',
            'TRAKTCHECKER': 'Trakt Checker',
            'EVENT': 'Event',
            'ERROR': 'Error',
            'TORNADO': 'Tornado',
            'Thread': 'Thread',
            'MAIN': 'Main',
        }

        # list of allowed loggers
        self.allowedLoggers = ['root', 'tornado.general', 'tornado.application']

    def initalize(self):
        # set custom level for database logging
        logging.addLevelName(self.logLevels[b'DB'], 'DB')
        logging.getLogger().setLevel(self.logLevels[b'DB'])

        # console log handler
        if self.consoleLogging:
            console = logging.StreamHandler()
            console.setFormatter(logging.Formatter('%(asctime)s %(levelname)s::%(threadName)s::%(message)s', '%H:%M:%S'))
            console.setLevel(self.logLevels[b'INFO'] if not self.debugLogging else self.logLevels[b'DEBUG'])
            logging.getLogger().addHandler(console)

        # rotating log file handler
        if self.fileLogging and self.logFile:
            rfh = logging.handlers.RotatingFileHandler(
                    filename=self.logFile,
                    maxBytes=self.logSize,
                    backupCount=self.logNr
            )
            rfh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s::%(threadName)s::%(message)s', dateTimeFormat))
            rfh.setLevel(self.logLevels[b'INFO'] if not self.debugLogging else self.logLevels[b'DEBUG'])
            logging.getLogger().addHandler(rfh)

class CustomLogger(SRLogger):
    def __init__(self, *args, **kwargs):
        super(CustomLogger, self).__init__(*args, **kwargs)
        logging.log_error_and_exit = self.log_error_and_exit
        logging.submit_errors = self.submit_errors
        logging.db = self.db

    def handle(self, record):
        if not record.name in self.allowedLoggers:
            self.disabled = 1

        if not self.disabled:
            try:
                record.msg = re.sub(r"(.*)\b({})\b(.*)"
                                    .format('|'
                                            .join([x for x in self.censoredItems.values() if len(x)])), r"\1\3",
                                    record.msg)

                # needed because Newznab apikey isn't stored as key=value in a section.
                record.msg = re.sub(r"([&?]r|[&?]apikey|[&?]api_key)=[^&]*([&\w]?)", r"\1=**********\2", record.msg)
            except:pass

            # sending record to UI
            if record.levelno in [WARNING, ERROR]:
                (classes.WarningViewer().add(record.msg, True), classes.ErrorViewer().add(record.msg, True))[int(level) == ERROR]

            super(CustomLogger, self).handle(record)
            if 'exit' in record.args:
                if self.consoleLogging:
                    sys.exit(record.msg)
                sys.exit(1)

    def error(self, msg, *args, **kwargs):
        super(CustomLogger, self).error(msg, exc_info=1, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        super(CustomLogger, self).warning(msg, exc_info=1, *args, **kwargs)

    def db(self, msg, *args, **kwargs):
        super(CustomLogger, self).log(self.logLevels[b'DB'], msg, *args, **kwargs)

    def log_error_and_exit(self, msg, *args, **kwargs):
        super(CustomLogger, self).error(msg, exit=1, *args, **kwargs)

    def submit_errors(self):  # Too many local variables, too many branches, pylint: disable=R0912,R0914
        submitter_result = None
        issue_id = None

        if not (sickbeard.GIT_USERNAME and sickbeard.GIT_PASSWORD and sickbeard.DEBUG and len(
                classes.ErrorViewer.errors) > 0):
            submitter_result = 'Please set your GitHub username and password in the config and enable debug. Unable to submit issue ticket to GitHub!'
            return submitter_result, issue_id

        try:
            from sickbeard.versionChecker import CheckVersion

            checkversion = CheckVersion()
            checkversion.check_for_new_version()
            commits_behind = checkversion.updater.get_num_commits_behind()
        except Exception:
            submitter_result = 'Could not check if your SiCKRAGE is updated, unable to submit issue ticket to GitHub!'
            return submitter_result, issue_id

        if commits_behind is None or commits_behind > 0:
            submitter_result = 'Please update SiCKRAGE, unable to submit issue ticket to GitHub with an outdated version!'
            return submitter_result, issue_id

        if self.submitter_running:
            submitter_result = 'Issue submitter is running, please wait for it to complete'
            return submitter_result, issue_id

        self.submitter_running = True

        gh_org = sickbeard.GIT_ORG or 'SiCKRAGETV'
        gh_repo = 'sickrage-issues'

        gh = Github(login_or_token=sickbeard.GIT_USERNAME, password=sickbeard.GIT_PASSWORD, user_agent="SiCKRAGE")

        try:
            # read log file
            log_data = None

            if ek(os.path.isfile, self.logFile):
                with ek(io.open, self.logFile, 'r') as f:
                    log_data = f.readlines()

            for i in range(1, int(sickbeard.LOG_NR)):
                if ek(os.path.isfile, self.logFile + ".%i" % i) and (len(log_data) <= 500):
                    with ek(io.open, self.logFile + ".%i" % i, 'r') as f:
                        log_data += f.readlines()

            log_data = [line for line in reversed(log_data)]

            # parse and submit errors to issue tracker
            for curError in sorted(classes.ErrorViewer.errors, key=lambda error: error.time, reverse=True)[:500]:

                try:
                    title_Error = "[APP SUBMITTED]: {}".format(curError.title)
                    if not len(title_Error) or title_Error == 'None':
                        title_Error = re.match(r"^[A-Z0-9\-\[\] :]+::\s*(.*)$", curError.message).group(1)

                    if len(title_Error) > 1000:
                        title_Error = title_Error[0:1000]
                except Exception as e:
                    super(CustomLogger, self).error("Unable to get error title : {}".format(ex(e)))

                gist = None
                regex = r"^({})\s+([A-Z]+)\s+([0-9A-Z\-]+)\s*(.*)$".format(curError.time)
                for i, x in enumerate(log_data):
                    match = re.match(regex, x)
                    if match:
                        level = match.group(2)
                        if level == logging.ERROR:
                            paste_data = "".join(log_data[i:i + 50])
                            if paste_data:
                                gist = gh.get_user().create_gist(True, {"sickrage.log": InputFileContent(paste_data)})
                            break
                    else:
                        gist = 'No ERROR found'

                message = "### INFO\n"
                message += "Python Version: **" + sys.version[:120].replace('\n', '') + "**\n"
                message += "Operating System: **" + platform.platform() + "**\n"
                try:
                    message += "Locale: " + locale.getdefaultlocale()[1] + "\n"
                except Exception:
                    message += "Locale: unknown" + "\n"
                message += "Branch: **" + sickbeard.BRANCH + "**\n"
                message += "Commit: SiCKRAGETV/SiCKRAGE@" + sickbeard.CUR_COMMIT_HASH + "\n"
                if gist and gist != 'No ERROR found':
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
                        if not report.raw_data[b'locked']:
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

                if issue_id and curError in classes.ErrorViewer.errors:
                    # clear error from error list
                    classes.ErrorViewer.errors.remove(curError)

        except Exception as e:
            super(CustomLogger, self).error(traceback.format_exc())
            submitter_result = 'Exception generated in issue submitter, please check the log'
        finally:
            self.submitter_running = False

        return submitter_result, issue_id

SRLogger = SRLogger()
