# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
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

from __future__ import with_statement

import time
import os
import sys
import threading

import logging

import sickbeard

from sickbeard import classes


# number of log files to keep
NUM_LOGS = 3

# log size in bytes
LOG_SIZE = 10000000  # 10 megs

ERROR = logging.ERROR
WARNING = logging.WARNING
MESSAGE = logging.INFO
DEBUG = logging.DEBUG
DB = 5

reverseNames = {u'ERROR': ERROR,
                u'WARNING': WARNING,
                u'INFO': MESSAGE,
                u'DEBUG': DEBUG,
                u'DB': DB}

# send logging to null
class NullHandler(logging.Handler):
    def emit(self, record):
        pass

class SBRotatingLogHandler(object):
    def __init__(self, log_file, num_files, num_bytes):
        self.num_files = num_files
        self.num_bytes = num_bytes

        self.log_file = log_file
        self.log_file_path = log_file
        self.cur_handler = None

        self.writes_since_check = 0

        self.console_logging = False
        self.log_lock = threading.Lock()

    def close_log(self, handler=None):
        if not handler:
            handler = self.cur_handler

        if handler:
            sb_logger = logging.getLogger('sickbeard')
            sub_logger = logging.getLogger('subliminal')
            imdb_logger = logging.getLogger('imdbpy')
            tornado_logger = logging.getLogger('tornado')
            feedcache_logger = logging.getLogger('feedcache')

            sb_logger.removeHandler(handler)
            sub_logger.removeHandler(handler)
            imdb_logger.removeHandler(handler)
            tornado_logger.removeHandler(handler)
            feedcache_logger.removeHandler(handler)

            handler.flush()
            handler.close()

    def initLogging(self, consoleLogging=False):

        if consoleLogging:
            self.console_logging = consoleLogging

        old_handler = None

        # get old handler in case we want to close it
        if self.cur_handler:
            old_handler = self.cur_handler
        else:

            #Add a new logging level DB
            logging.addLevelName(5, 'DB')

            # only start consoleLogging on first initialize
            if self.console_logging:
                # define a Handler which writes INFO messages or higher to the sys.stderr
                console = logging.StreamHandler()

                console.setLevel(logging.INFO)
                if sickbeard.DEBUG:
                    console.setLevel(logging.DEBUG)

                # set a format which is simpler for console use
                console.setFormatter(DispatchingFormatter(
                    {'sickbeard': logging.Formatter('%(asctime)s %(levelname)s::%(message)s', '%H:%M:%S'),
                     'subliminal': logging.Formatter('%(asctime)s %(levelname)s::SUBLIMINAL :: %(message)s',
                                                     '%H:%M:%S'),
                     'imdbpy': logging.Formatter('%(asctime)s %(levelname)s::IMDBPY :: %(message)s', '%H:%M:%S'),
                     'tornado.general': logging.Formatter('%(asctime)s %(levelname)s::TORNADO :: %(message)s', '%H:%M:%S'),
                     'tornado.application': logging.Formatter('%(asctime)s %(levelname)s::TORNADO :: %(message)s', '%H:%M:%S'),
                     'feedcache.cache': logging.Formatter('%(asctime)s %(levelname)s::FEEDCACHE :: %(message)s',
                                                          '%H:%M:%S')
                    },
                    logging.Formatter('%(message)s'), ))

                # add the handler to the root logger
                logging.getLogger('sickbeard').addHandler(console)
                logging.getLogger('tornado.general').addHandler(console)
                logging.getLogger('tornado.application').addHandler(console)
                logging.getLogger('subliminal').addHandler(console)
                logging.getLogger('imdbpy').addHandler(console)
                logging.getLogger('feedcache').addHandler(console)

        self.log_file_path = os.path.join(sickbeard.LOG_DIR, self.log_file)

        self.cur_handler = self._config_handler()
        logging.getLogger('sickbeard').addHandler(self.cur_handler)
        logging.getLogger('tornado.access').addHandler(NullHandler())
        logging.getLogger('tornado.general').addHandler(self.cur_handler)
        logging.getLogger('tornado.application').addHandler(self.cur_handler)
        logging.getLogger('subliminal').addHandler(self.cur_handler)
        logging.getLogger('imdbpy').addHandler(self.cur_handler)
        logging.getLogger('feedcache').addHandler(self.cur_handler)

        logging.getLogger('sickbeard').setLevel(DB)

        log_level = logging.WARNING
        if sickbeard.DEBUG:
            log_level = logging.DEBUG

        logging.getLogger('tornado.general').setLevel(log_level)
        logging.getLogger('tornado.application').setLevel(log_level)
        logging.getLogger('subliminal').setLevel(log_level)
        logging.getLogger('imdbpy').setLevel(log_level)
        logging.getLogger('feedcache').setLevel(log_level)


        # already logging in new log folder, close the old handler
        if old_handler:
            self.close_log(old_handler)
            #            old_handler.flush()
            #            old_handler.close()
            #            sb_logger = logging.getLogger('sickbeard')
            #            sub_logger = logging.getLogger('subliminal')
            #            imdb_logger = logging.getLogger('imdbpy')
            #            sb_logger.removeHandler(old_handler)
            #            subli_logger.removeHandler(old_handler)
            #            imdb_logger.removeHandler(old_handler)

    def _config_handler(self):
        """
        Configure a file handler to log at file_name and return it.
        """

        file_handler = logging.FileHandler(self.log_file_path, encoding='utf-8')
        file_handler.setLevel(DB)
        file_handler.setFormatter(DispatchingFormatter(
            {'sickbeard': logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', '%Y-%m-%d %H:%M:%S'),
             'subliminal': logging.Formatter('%(asctime)s %(levelname)-8s SUBLIMINAL :: %(message)s',
                                             '%Y-%m-%d %H:%M:%S'),
             'imdbpy': logging.Formatter('%(asctime)s %(levelname)-8s IMDBPY :: %(message)s', '%Y-%m-%d %H:%M:%S'),
             'tornado.general': logging.Formatter('%(asctime)s %(levelname)-8s TORNADO :: %(message)s', '%Y-%m-%d %H:%M:%S'),
             'tornado.application': logging.Formatter('%(asctime)s %(levelname)-8s TORNADO :: %(message)s', '%Y-%m-%d %H:%M:%S'),
             'feedcache.cache': logging.Formatter('%(asctime)s %(levelname)-8s FEEDCACHE :: %(message)s',
                                                      '%Y-%m-%d %H:%M:%S')
            },
            logging.Formatter('%(message)s'), ))

        return file_handler

    def _log_file_name(self, i):
        """
        Returns a numbered log file name depending on i. If i==0 it just uses logName, if not it appends
        it to the extension (blah.log.3 for i == 3)
        
        i: Log number to ues
        """

        return self.log_file_path + ('.' + str(i) if i else '')

    def _num_logs(self):
        """
        Scans the log folder and figures out how many log files there are already on disk

        Returns: The number of the last used file (eg. mylog.log.3 would return 3). If there are no logs it returns -1
        """

        cur_log = 0
        while os.path.isfile(self._log_file_name(cur_log)):
            cur_log += 1
        return cur_log - 1

    def _rotate_logs(self):

        sb_logger = logging.getLogger('sickbeard')
        sub_logger = logging.getLogger('subliminal')
        imdb_logger = logging.getLogger('imdbpy')
        tornado_logger = logging.getLogger('tornado')
        feedcache_logger = logging.getLogger('feedcache')

        # delete the old handler
        if self.cur_handler:
            self.close_log()

        # rename or delete all the old log files
        for i in range(self._num_logs(), -1, -1):
            cur_file_name = self._log_file_name(i)
            try:
                if i >= NUM_LOGS:
                    os.remove(cur_file_name)
                else:
                    os.rename(cur_file_name, self._log_file_name(i + 1))
            except OSError:
                pass

        # the new log handler will always be on the un-numbered .log file
        new_file_handler = self._config_handler()

        self.cur_handler = new_file_handler

        sb_logger.addHandler(new_file_handler)
        sub_logger.addHandler(new_file_handler)
        imdb_logger.addHandler(new_file_handler)
        tornado_logger.addHandler(new_file_handler)
        feedcache_logger.addHandler(new_file_handler)

    def log(self, toLog, logLevel=MESSAGE):

        with self.log_lock:

            # check the size and see if we need to rotate
            if self.writes_since_check >= 10:
                if os.path.isfile(self.log_file_path) and os.path.getsize(self.log_file_path) >= LOG_SIZE:
                    self._rotate_logs()
                self.writes_since_check = 0
            else:
                self.writes_since_check += 1

            meThread = threading.currentThread().getName()
            message = meThread + u" :: " + toLog

            out_line = message

            sb_logger = logging.getLogger('sickbeard')
            setattr(sb_logger, 'db', lambda *args: sb_logger.log(DB, *args))

            sub_logger = logging.getLogger('subliminal')
            imdb_logger = logging.getLogger('imdbpy')
            tornado_logger = logging.getLogger('tornado')
            feedcache_logger = logging.getLogger('feedcache')

            try:
                if logLevel == DEBUG:
                    sb_logger.debug(out_line)
                elif logLevel == MESSAGE:
                    sb_logger.info(out_line)
                elif logLevel == WARNING:
                    sb_logger.warning(out_line)
                elif logLevel == ERROR:
                    sb_logger.error(out_line)
                    # add errors to the UI logger
                    classes.ErrorViewer.add(classes.UIError(message))
                elif logLevel == DB:
                    sb_logger.db(out_line)
                else:
                    sb_logger.log(logLevel, out_line)
            except ValueError:
                pass

    def log_error_and_exit(self, error_msg):
        log(error_msg, ERROR)

        if not self.console_logging:
            sys.exit(error_msg.encode(sickbeard.SYS_ENCODING, 'xmlcharrefreplace'))
        else:
            sys.exit(1)


class DispatchingFormatter:
    def __init__(self, formatters, default_formatter):
        self._formatters = formatters
        self._default_formatter = default_formatter

    def format(self, record):
        formatter = self._formatters.get(record.name, self._default_formatter)
        return formatter.format(record)


sb_log_instance = SBRotatingLogHandler('sickbeard.log', NUM_LOGS, LOG_SIZE)


def log(toLog, logLevel=MESSAGE):
    sb_log_instance.log(toLog, logLevel)


def log_error_and_exit(error_msg):
    sb_log_instance.log_error_and_exit(error_msg)


def close():
    sb_log_instance.close_log()    