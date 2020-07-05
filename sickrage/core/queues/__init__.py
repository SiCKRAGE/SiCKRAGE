# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import datetime
import threading
import time
from functools import cmp_to_key
from queue import Queue

import sickrage


class SRQueuePriorities(object):
    PAUSED = 0
    LOW = 10
    NORMAL = 20
    HIGH = 30
    EXTREME = 40


class SRQueue(threading.Thread):
    def __init__(self, name="QUEUE"):
        super(SRQueue, self).__init__()
        self.name = name
        self.lock = threading.Lock()
        self.min_priority = SRQueuePriorities.EXTREME
        self.queue = []
        self.result_queue = []
        self.current_item = None
        self.amActive = False
        self.stop = False

    def run(self):
        """
        Process items in this queue
        """

        self.amActive = True

        while not self.stop:
            with self.lock:
                if self.current_item is None or not self.current_item.is_alive():
                    if self.current_item:
                        if self.current_item.result:
                            self.result_queue.append(self.current_item.result)
                        self.current_item = None

                    if self.queue and not self.is_paused:
                        self.current_item = self.get()
                        self.current_item.start()

            time.sleep(0.1)

        self.amActive = False

    def get(self):
        def queue_sorter(x, y):
            """
            Sorts by priority descending then time ascending
            """
            if x.priority == y.priority:
                if y.added == x.added:
                    return 0
                elif y.added < x.added:
                    return 1
                elif y.added > x.added:
                    return -1
            else:
                return y.priority - x.priority

        self.queue.sort(key=cmp_to_key(lambda x, y: queue_sorter(x, y)))
        return self.queue.pop(0)

    def put(self, item, *args, **kwargs):
        """
        Adds an item to this queue

        :param item: Queue object to add
        :return: item
        """
        if self.stop:
            return

        item.added = datetime.datetime.now()
        item.name = "{}-{}".format(self.name, item.name)
        self.queue.append(item)
        return item

    @property
    def queue_items(self):
        items = self.queue.copy()
        if self.current_item:
            items.append(self.current_item)

        return items

    @property
    def is_busy(self):
        return bool(len(self.queue_items) > 0)

    @property
    def is_paused(self):
        return self.min_priority == SRQueuePriorities.PAUSED

    def pause(self):
        """Pauses this queue"""
        sickrage.app.log.info("Pausing {}".format(self.name))
        self.min_priority = SRQueuePriorities.PAUSED

    def unpause(self):
        """Unpauses this queue"""
        sickrage.app.log.info("Un-pausing {}".format(self.name))
        self.min_priority = SRQueuePriorities.EXTREME

    def shutdown(self):
        self.stop = True
        if self.current_item:
            self.current_item.join(10)
        self.queue.clear()
        self.join(10)


class SRQueueItem(threading.Thread):
    def __init__(self, name, action_id=0):
        super(SRQueueItem, self).__init__()
        self.name = name.replace(" ", "-").upper()
        self.action_id = action_id
        self.priority = SRQueuePriorities.NORMAL
        self.added = None
        self.result = None
