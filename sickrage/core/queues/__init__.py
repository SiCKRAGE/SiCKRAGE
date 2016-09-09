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
        self.threads = []

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

        self.amActive = True

        with self.lock:
            while not self.empty() and not self.stop.isSet():
                # only start a new task if one isn't already going
                if self.currentItem is None or not self.currentItem.isAlive():
                    # if the thread is dead then the current item should be finished
                    if self.currentItem:
                        self.currentItem.finish()
                        self.currentItem = None

                    if self.queue[0][0] >= self.min_priority:
                        self.currentItem = self.get()
                        sickrage.srCore.srScheduler.add_job(self.callback, name=self.currentItem.name)

        self.amActive = False

    def callback(self):
        self.currentItem.run()
        self.currentItem.finish()

    def shutdown(self):
        self.stop.set()


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
