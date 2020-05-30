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
import locale
import logging
import os
import pkgutil
import platform
import re
import sys
from logging import FileHandler, CRITICAL, DEBUG, ERROR, INFO, WARNING
from logging.handlers import RotatingFileHandler

import raven
from raven.handlers.logging import SentryHandler
from unidecode import unidecode

import sickrage
from sickrage.core import make_dir
from sickrage.core.classes import ErrorViewer, WarningViewer


class Logger(logging.getLoggerClass()):
    logging.captureWarnings(True)
    logging.getLogger().addHandler(logging.NullHandler())

    def __init__(self, name="sickrage", consoleLogging=True, fileLogging=False, debugLogging=False, logFile=None, logSize=1048576, logNr=5):
        super(Logger, self).__init__(name)
        self.propagate = False

        self.consoleLogging = consoleLogging
        self.fileLogging = fileLogging
        self.debugLogging = debugLogging

        self.logFile = logFile
        self.logSize = logSize
        self.logNr = logNr

        self.CRITICAL = CRITICAL
        self.DEBUG = DEBUG
        self.ERROR = ERROR
        self.WARNING = WARNING
        self.INFO = INFO
        self.DB = 5

        self.CENSORED_ITEMS = {}

        self.logLevels = {
            'CRITICAL': self.CRITICAL,
            'ERROR': self.ERROR,
            'WARNING': self.WARNING,
            'INFO': self.INFO,
            'DEBUG': self.DEBUG,
            'DB': 5
        }

        # list of allowed loggers
        self.loggers = {'sickrage': self,
                        'tornado.general': logging.getLogger('tornado.general'),
                        'tornado.application': logging.getLogger('tornado.application'),
                        'apscheduler.executors': logging.getLogger('apscheduler.executors'),
                        'apscheduler.jobstores': logging.getLogger('apscheduler.jobstores'),
                        'apscheduler.scheduler': logging.getLogger('apscheduler.scheduler')}

        # set custom level for database logging
        logging.addLevelName(self.logLevels['DB'], 'DB')
        self.setLevel(self.logLevels['DB'])

        # viewers
        self.warning_viewer = WarningViewer()
        self.error_viewer = ErrorViewer()

        # start logger
        self.start()

    def start(self):
        # remove all handlers
        self.handlers.clear()

        sentry_ignore_exceptions = [
            'KeyboardInterrupt',
            'PermissionError',
            'FileNotFoundError',
            'EpisodeNotFoundException'
        ]

        # sentry log handler
        sentry_client = raven.Client(
            'https://d4bf4ed225c946c8972c7238ad07d124@sentry.sickrage.ca/2?verify_ssl=0',
            release=sickrage.version(),
            repos={'sickrage': {'name': 'sickrage/sickrage'}},
            ignore_exceptions=sentry_ignore_exceptions
        )

        sentry_tags = {
            'platform': platform.platform(),
            'locale': locale.getdefaultlocale(),
            'python': platform.python_version()
        }

        if sickrage.app.config and sickrage.app.config.sub_id:
            sentry_tags.update({'sub_id': sickrage.app.config.sub_id})
        if sickrage.app.config and sickrage.app.config.server_id:
            sentry_tags.update({'server_id': sickrage.app.config.server_id})

        sentry_handler = SentryHandler(client=sentry_client, ignore_exceptions=sentry_ignore_exceptions, tags=sentry_tags)

        sentry_handler.setLevel(self.logLevels['ERROR'])
        sentry_handler.set_name('sentry')
        self.addHandler(sentry_handler)

        # console log handler
        if self.consoleLogging:
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s %(levelname)s::%(threadName)s::%(message)s', '%H:%M:%S')

            console_handler.setFormatter(formatter)
            console_handler.setLevel(self.logLevels['INFO'] if not self.debugLogging else self.logLevels['DEBUG'])
            self.addHandler(console_handler)

        # file log handlers
        if self.logFile:
            # make logs folder if it doesn't exist
            if not os.path.exists(os.path.dirname(self.logFile)):
                if not make_dir(os.path.dirname(self.logFile)):
                    return

            if sickrage.app.developer:
                rfh = FileHandler(
                    filename=self.logFile,
                )
            else:
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

            formatter = logging.Formatter('%(asctime)s %(levelname)s::%(threadName)s::%(message)s', '%Y-%m-%d %H:%M:%S')

            rfh.setFormatter(formatter)
            rfh.setLevel(self.logLevels['INFO'] if not self.debugLogging else self.logLevels['DEBUG'])
            self.addHandler(rfh)

            rfh_errors.setFormatter(formatter)
            rfh_errors.setLevel(self.logLevels['ERROR'])
            self.addHandler(rfh_errors)

    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):
        if (False, True)[name in self.loggers]:
            record = super(Logger, self).makeRecord(name, level, fn, lno, msg, args, exc_info, func, extra, sinfo)

            try:
                record.msg = re.sub(
                    r"(.*)\b({})\b(.*)".format(
                        '|'.join([x for x in self.CENSORED_ITEMS.values() if len(x)])), r"\1\3",
                    record.msg)

                # needed because Newznab apikey isn't stored as key=value in a section.
                record.msg = re.sub(r"([&?]r|[&?]apikey|[&?]api_key)=[^&]*([&\w]?)", r"\1=**********\2", record.msg)
                record.msg = unidecode(record.msg)
            except:
                pass

            # sending record to UI
            if record.levelno in [WARNING, ERROR]:
                (self.warning_viewer, self.error_viewer)[record.levelno == ERROR].add("{}::{}".format(record.threadName, record.msg), True)

            return record

    def set_level(self):
        self.debugLogging = sickrage.app.config.debug
        level = DEBUG if self.debugLogging else INFO
        for __, logger in self.loggers.items():
            logger.setLevel(level)
            for handler in logger.handlers:
                if not handler.name == 'sentry':
                    handler.setLevel(level)

    def list_modules(self, package):
        """Return all sub-modules for the specified package.

        :param package:
        :type package: module
        :return:
        :rtype: list of str
        """
        return [modname for importer, modname, ispkg in pkgutil.walk_packages(path=package.__path__, prefix=package.__name__ + '.', onerror=lambda x: None)]

    def get_loggers(self, package):
        """Return all loggers for package and sub-packages.

        :param package:
        :type package: module
        :return:
        :rtype: list of logging.Logger
        """
        return [logging.getLogger(modname) for modname in self.list_modules(package)]

    def log(self, level, msg, *args, **kwargs):
        super(Logger, self).log(level, msg, *args, **kwargs)

    def db(self, msg, *args, **kwargs):
        super(Logger, self).log(self.logLevels['DB'], msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        super(Logger, self).info(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        super(Logger, self).debug(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        super(Logger, self).critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        super(Logger, self).exception(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        super(Logger, self).error(msg, exc_info=1, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        super(Logger, self).warning(msg, *args, **kwargs)

    def fatal(self, msg, *args, **kwargs):
        super(Logger, self).fatal(msg, *args, **kwargs)
        sys.exit(1)

    def close(self, *args, **kwargs):
        logging.shutdown()
