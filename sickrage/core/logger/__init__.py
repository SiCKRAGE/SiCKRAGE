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
import logging
import os
import pkgutil
import re
import sys
from logging import FileHandler, CRITICAL, DEBUG, ERROR, INFO, WARNING
from logging.handlers import RotatingFileHandler

from unidecode import unidecode

import sickrage
from sickrage.core.classes import ErrorViewer, WarningViewer
from sickrage.core.helpers import make_dir
from sickrage.search_providers import SearchProviderType


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

    @property
    def censored_items(self):
        try:
            items = [
                sickrage.app.config.user.password,
                sickrage.app.config.sabnzbd.password,
                sickrage.app.config.sabnzbd.apikey,
                sickrage.app.config.nzbget.password,
                sickrage.app.config.synology.password,
                sickrage.app.config.torrent.password,
                sickrage.app.config.kodi.password,
                sickrage.app.config.plex.password,
                sickrage.app.config.plex.server_token,
                sickrage.app.config.emby.apikey,
                sickrage.app.config.growl.password,
                sickrage.app.config.freemobile.apikey,
                sickrage.app.config.telegram.apikey,
                sickrage.app.config.join_app.apikey,
                sickrage.app.config.prowl.apikey,
                sickrage.app.config.twitter.password,
                sickrage.app.config.twilio.auth_token,
                sickrage.app.config.boxcar2.access_token,
                sickrage.app.config.pushover.apikey,
                sickrage.app.config.nma.api_keys,
                sickrage.app.config.pushalot.auth_token,
                sickrage.app.config.pushbullet.api_key,
                sickrage.app.config.email.password,
                sickrage.app.config.subtitles.addic7ed_pass,
                sickrage.app.config.subtitles.legendastv_pass,
                sickrage.app.config.subtitles.itasa_pass,
                sickrage.app.config.subtitles.opensubtitles_pass,
                sickrage.app.config.anidb.password
            ]

            for __, search_provider in sickrage.app.search_providers.all().items():
                if search_provider.provider_type in [SearchProviderType.NZB, SearchProviderType.NEWZNAB]:
                    items.append(search_provider.api_key)
                elif search_provider.provider_type == SearchProviderType.TORRENT_RSS and not search_provider.default:
                    items.append(search_provider.urls['base_url'])

                items.append(search_provider.cookies)

                [items.append(search_provider.custom_settings[item]) for item in [
                    'digest',
                    'hash',
                    'api_key',
                    'password',
                    'passkey',
                    'pin',
                ] if item in search_provider.custom_settings]

            return list(filter(None, items))
        except AttributeError:
            return []

    def start(self):
        # remove all handlers
        self.handlers.clear()

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
        if name in self.loggers:
            record = super(Logger, self).makeRecord(name, level, fn, lno, msg, args, exc_info, func, extra, sinfo)

            try:
                def repl(m):
                    return '*' * len(m.group())

                record.msg = re.sub(fr"\b({'|'.join(self.censored_items)})\b", repl, record.msg)
                record.msg = unidecode(record.msg)
            except:
                pass

            # sending record to UI
            if record.levelno in [WARNING, ERROR]:
                (self.warning_viewer, self.error_viewer)[record.levelno == ERROR].add("{}::{}".format(record.threadName, record.msg), True)

            return record

    def set_level(self):
        self.debugLogging = sickrage.app.debug
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
        kwargs['exc_info'] = True
        super(Logger, self).error(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        super(Logger, self).warning(msg, *args, **kwargs)

    def fatal(self, msg, *args, **kwargs):
        super(Logger, self).fatal(msg, *args, **kwargs)
        sys.exit(1)

    def close(self, *args, **kwargs):
        logging.shutdown()
