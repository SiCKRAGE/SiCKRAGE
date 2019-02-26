# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
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


import datetime
import threading
import time

from queue import PriorityQueue, Queue

import sickrage


class srQueuePriorities(object):
    EXTREME = 5
    HIGH = 10
    NORMAL = 20
    LOW = 30
    PAUSED = 99


class srQueue(threading.Thread):
    def __init__(self, name="QUEUE"):
        super(srQueue, self).__init__(name=name)
        self.daemon = True
        self._queue = PriorityQueue()
        self._result_queue = Queue()
        self._current_items = []
        self.min_priority = srQueuePriorities.EXTREME
        self.amActive = False
        self.lock = threading.Lock()
        self.stop = threading.Event()

    def run(self):
        """
        Process items in this queue
        """

        while not self.stop.is_set():
            with self.lock:
                self.amActive = True

                if not self.is_paused:
                    if self.current_item:
                        if self.next_item_priority < self.current_item.priority:
                            self.current_item = self.get()
                            self.current_item.start()
                            self.current_item.join()

                    if not self.current_item or not self.current_item.isAlive():
                        if self.current_item:
                            self.current_item = None

                        self.current_item = self.get()
                        self.current_item.start()

                self.amActive = False

            time.sleep(1)

    @property
    def queue(self):
        return self._queue.queue

    @property
    def next_item_priority(self):
        try:
            priority = self._queue.queue[0].priority
        except IndexError:
            priority = (srQueuePriorities.LOW, time.time())

        return priority

    @property
    def current_item(self):
        if len(self._current_items):
            return self._current_items[0]

    @current_item.setter
    def current_item(self, value):
        if value:
            self._current_items.insert(0, value)
        else:
            del self._current_items[0]

    def get(self, *args, **kwargs):
        return self._queue.get(*args, **kwargs)

    def put(self, item, *args, **kwargs):
        """
        Adds an item to this queue

        :param item: Queue object to add
        :return: item
        """
        item.added = datetime.datetime.now()
        item.name = "{}-{}".format(self.name, item.name)
        item.result_queue = self._result_queue
        self._queue.put(item, *args, **kwargs)
        return item

    @property
    def is_busy(self):
        return bool(len([x for x in self._current_items if x.isAlive()]))

    @property
    def is_paused(self):
        return self.min_priority == srQueuePriorities.PAUSED

    def pause(self):
        """Pauses this queue"""
        sickrage.app.log.info("Pausing {}".format(self.name))
        self.min_priority = srQueuePriorities.PAUSED

    def unpause(self):
        """Unpauses this queue"""
        sickrage.app.log.info("Un-pausing {}".format(self.name))
        self.min_priority = srQueuePriorities.EXTREME

    def shutdown(self):
        self.stop.set()
        try:
            self.join(1)
        except:
            pass


class srQueueItem(threading.Thread):
    def __init__(self, name, action_id=0):
        super(srQueueItem, self).__init__(name=name.replace(" ", "-").upper())
        self.daemon = True
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.action_id = action_id
        self.added = None
        self.result = None
        self.result_queue = None
        self._priority = (srQueuePriorities.NORMAL, time.time())

    @property
    def priority(self):
        return self._priority

    @priority.setter
    def priority(self, value):
        self._priority = (value, time.time())

    def __lt__(self, other):
        return self.priority[0] < other.priority[0] and self.priority[1] < other.priority[1]
