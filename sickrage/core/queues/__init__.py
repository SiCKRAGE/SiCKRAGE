# Author: echel0n <echel0n@sickrage.ca>
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

import threading
from Queue import PriorityQueue
from datetime import datetime

try:
    from futures import ThreadPoolExecutor, thread
except ImportError:
    from concurrent.futures import ThreadPoolExecutor, thread

import sickrage


class QueuePriorities(object):
    LOW = 10
    NORMAL = 20
    HIGH = 30


class srQueue(PriorityQueue):
    def __init__(self, maxsize=0):
        PriorityQueue.__init__(self, maxsize)
        self.queue_name = "QUEUE"
        self.lock = threading.Lock()
        self.currentItem = None
        self.min_priority = 0
        self.amActive = False
        self.stop = threading.Event()
        self.threads  = []

    @property
    def name(self):
        return self.queue_name

    def get(self, *args, **kwargs):
        _, item = PriorityQueue.get(self, *args, **kwargs)
        return item

    def put(self, item, *args, **kwargs):
        """
        Adds an item to this queue

        :param item: Queue object to add
        :return: item
        """
        item.name = "{}-{}".format(self.name, item.name)
        item.added = datetime.now()
        PriorityQueue.put(self, (item.priority, item), *args, **kwargs)
        return item

    def pause(self):
        """Pauses this queue"""
        sickrage.srCore.srLogger.info("Pausing queue")
        self.min_priority = 999999999999

    def unpause(self):
        """Unpauses this queue"""
        sickrage.srCore.srLogger.info("Unpausing queue")
        self.min_priority = 0

    def run(self, force=False):
        """
        Process items in this queue

        :param force: Force queue processing (currently not implemented)
        """

        if self.amActive:
            return

        with self.lock:
            self.amActive = True

            while not self.empty() and not self.stop.isSet():
                if self.queue[0][0] >= self.min_priority:
                    t = threading.Thread(name=self.name, target=self.callback)
                    self.threads += [t]
                    t.start()

            self.amActive = False

    def callback(self):
        item = self.get()
        item.run()
        item.finish()

    def shutdown(self):
        self.stop.set()
        for t in self.threads:
            try:
                t.join(10)
            except Exception:
                continue


class QueueItem(object):
    def __init__(self, name, action_id=0):
        self.lock = threading.Lock()
        self.name = name.replace(" ", "-").upper()
        self.inProgress = False
        self.priority = QueuePriorities.NORMAL
        self.action_id = action_id
        self.stop = threading.Event()
        self.added = None

    def run(self):
        threading.currentThread().setName(self.name)
        self.inProgress = True

    def finish(self):
        self.inProgress = False
