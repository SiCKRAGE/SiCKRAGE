# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
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

import logging
import threading

from tornado.ioloop import PeriodicCallback

class Scheduler(PeriodicCallback):
    def __init__(self, callback, callback_time, name='ScheduledThread', silent=True, start_time=None, run_delay=None):
        self.action = callback()
        super(Scheduler, self).__init__(self.action.run, callback_time)
        self.name = "SCHEDULER"
        threading.Thread.name = name
        self.silent = silent
        self.enabled = True

    def forceRun(self):
        if not self.callback.amActive:
            self.force = True
            return True
        return False

    def start(self):
        if self.enabled:
            if not self.silent:
                logging.debug("Starting new scheduler thread: {}".format(self.name))
            super(Scheduler, self).start()
