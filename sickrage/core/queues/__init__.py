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
import random
import string
import threading
from collections import deque
from enum import Enum
from functools import cmp_to_key

import sickrage


class TaskPriority(object):
    LOW = 10
    NORMAL = 20
    HIGH = 30
    EXTREME = 40


class TaskStatus(Enum):
    """
    Defines all the possible status for a task in the queue
    """
    QUEUED = 'queued'
    FINISHED = 'finished'
    FAILED = 'failed'
    STARTED = 'started'
    DEFERRED = 'deferred'
    NOT_QUEUED = 'not queued'


class WorkerStatus(Enum):
    """
    Defines all the possible status for a worker in the queue
    """
    WORKING = 'working'
    IDLE = 'idle'
    STOPPED = 'stopped'


class Queue(object):
    def __init__(self, name="QUEUE"):
        super(Queue, self).__init__()
        self.name = name
        self.lock = threading.RLock()
        self.queue = deque([])
        self.tasks = {}
        self.task_results = {}
        self.workers = []
        self.timer = None
        self.auto_remove_tasks_timer = None
        self.pause = False

    def start_worker(self, n_workers=1):
        """
        This function starts a given number of workers providing them a
        random identifier.
        :param n_workers: the total new workers to be created
        :return: the list of new workers
        """
        ids = []
        for i in range(0, n_workers):
            worker_id = "w" + self.get_random_id()
            self.workers.append(Worker(worker_id, self))
            ids.append(worker_id)

        self.auto_remove_tasks_timer = threading.Timer(10.0, self.auto_remove_tasks)
        self.auto_remove_tasks_timer.setName(self.name)
        self.auto_remove_tasks_timer.start()

        return ids

    def stop_worker(self, worker_id=None):
        """
        This function stops and kills a worker.
        If no id is provided, all workers are killed.
        :param worker_id: the identifier for the worker to kill
        :return: None
        """
        try:
            self.lock.acquire()
            if worker_id is None:
                sickrage.app.log.info("Shutting down all {} workers".format(self.name))
                for worker in self.workers:
                    worker.must_die = True
            else:
                for worker in self.workers:
                    if worker.id == worker_id:
                        worker.must_die = True
                        break

            if self.auto_remove_tasks_timer is not None:
                self.auto_remove_tasks_timer.cancel()
                self.auto_remove_tasks_timer = None
        finally:
            self.lock.release()
            self.notify_workers()

    def remove_worker(self, worker_id):
        """
        This function removes a worker from the list of workers
        (only if the worker was notified "to die" previously)
        :param worker_id: the ID for the worker to remove
        :return:
        """
        try:
            self.lock.acquire()

            i = 0

            for worker in self.workers:
                if worker.id == worker_id and worker.must_die is True:
                    self.workers.pop(i)
                    break
                i += 1
        finally:
            self.lock.release()
            self.notify_workers()

    def auto_remove_tasks(self):
        for task in self.tasks.copy().values():
            if task.status in [TaskStatus.FINISHED, TaskStatus.FAILED]:
                self.remove_task(task.id)

        self.auto_remove_tasks_timer = threading.Timer(10.0, self.auto_remove_tasks)
        self.auto_remove_tasks_timer.setName(self.name)
        self.auto_remove_tasks_timer.start()

    def get(self, *args, **kwargs):
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

        try:
            self.lock.acquire()

            if len(self.queue) > 0:
                self.queue = deque(sorted(self.queue, key=cmp_to_key(lambda x, y: queue_sorter(x, y))))

                if self.is_paused:
                    if self.timer is None:
                        self.timer = threading.Timer(10.0, self.notify_workers)
                        self.timer.setName(self.name)
                        self.timer.start()
                    return None

                switch_pos = 1
                next_task = self.queue[len(self.queue) - 1]
                runnable = next_task.can_run(self.tasks)

                while not runnable:
                    switch_pos = switch_pos + 1
                    if switch_pos > len(self.queue):
                        self.queue.rotate(1)
                        switch_pos = 0
                        if self.timer is None:
                            self.timer = threading.Timer(10.0, self.notify_workers)
                            self.timer.setName(self.name)
                            self.timer.start()
                        return None
                    elif len(self.queue) > 1:
                        task_aux = self.queue[len(self.queue) - switch_pos]
                        self.queue[len(self.queue) - switch_pos] = self.queue[len(self.queue) - 1]
                        self.queue[len(self.queue) - 1] = task_aux
                    next_task = self.queue[len(self.queue) - 1]
                    runnable = next_task.can_run(self.tasks)

                return self.queue.pop()
            return None
        finally:
            self.lock.release()

    def put(self, task, task_id=None, depend=None, *args, **kwargs):
        """
        Adds an task to this queue

        :param task: Task object to add
        :param task_id: Task ID to add to task object
        :param depend: Task depends on other task to be in queue
        :return: task_id
        """
        try:
            self.lock.acquire()

            if not task_id:
                task_id = self.get_random_id()
                while task_id in self.tasks:
                    task_id = self.get_random_id()
            elif task_id in self.tasks:
                raise RuntimeError("Task already in {} (Task id : {})".format(self.name, task_id))

            task.id = task_id
            task.added = datetime.datetime.now()
            task.name = "{}-{}-{}".format(self.name, task_id, task.name)
            task.depend = depend

            self.tasks[task_id] = task
            self.queue.appendleft(task)

            sickrage.app.log.debug("New {} task {} added".format(self.name, task_id))
        finally:
            self.lock.release()
            self.notify_workers()
            return task_id

    def notify_workers(self):
        # sickrage.app.log.debug("Notifying {} workers".format(self.name))
        if self.timer is not None:
            # sickrage.app.log.debug("Clearing {} timer".format(self.name))
            self.timer.cancel()
            self.timer = None
        for worker in self.workers:
            worker.notify()

    def check_status(self, task_id):
        task = self.tasks.get(task_id, None)
        if task:
            return task.status
        return TaskStatus.NOT_QUEUED

    def fetch_task(self, task_id):
        return self.tasks.get(task_id, None)

    def remove_task(self, task_id):
        try:
            self.lock.acquire()

            if task_id in self.tasks:
                sickrage.app.log.debug("Removing {} task {}".format(self.name, task_id))
                task = self.tasks.get(task_id)
                if task in self.queue:
                    self.queue.remove(self.tasks.get(task_id))
                del self.tasks[task_id]
        finally:
            self.lock.release()

    def get_result(self, task_id):
        return self.task_results.pop(task_id) if task_id in self.task_results else None

    @property
    def is_busy(self):
        return any(worker.status == WorkerStatus.WORKING for worker in self.workers)

    @property
    def is_paused(self):
        return self.pause

    def pause(self):
        """Pauses this queue"""
        sickrage.app.log.info("Pausing {}".format(self.name))
        self.pause = True

    def unpause(self):
        """Unpauses this queue"""
        sickrage.app.log.info("Un-pausing {}".format(self.name))
        self.pause = False

    def get_random_id(self):
        """
        This function returns a new random task id
        @returns taskID
        """
        return ''.join(random.sample(string.ascii_letters + string.octdigits * 5, 10)).upper()

    def shutdown(self):
        sickrage.app.log.info("Shutting down {}".format(self.name))
        self.stop_worker()
        self.queue.clear()
        self.tasks.clear()


class Worker(object):
    def __init__(self, _id, _queue):
        self.id = _id
        self.queue = _queue
        self.status = WorkerStatus.IDLE
        self.must_die = False
        self.task = None

    def notify(self):
        if self.status != WorkerStatus.WORKING:
            if self.must_die:
                self.queue.remove_worker(self.id)
            else:
                task = self.queue.get()
                if task is not None:
                    self.task = task
                    WorkerThread(self).start()

    def run(self):
        try:
            sickrage.app.log.debug("Worker " + str(self.id) + " task started...")
            self.status = WorkerStatus.WORKING
            # fn = self.task.fn
            # args = self.task.args
            self.task.status = TaskStatus.STARTED
            self.task.result = self.task.run()
            self.task.status = TaskStatus.FINISHED
            if self.task.result is not None:
                self.queue.task_results[self.task.id] = self.task.result
            self.task.finish()
        except Exception as e:
            if self.task is not None:
                self.task.status = TaskStatus.FAILED
                self.task.error_message = str(e)
                sickrage.app.log.error("{} task failed: {}".format(self.task.name, self.task.error_message))
            else:
                sickrage.app.log.debug("Worker " + str(self.id) + " without task.")
        finally:
            sickrage.app.log.debug("Worker " + str(self.id) + " task completed...")
            self.status = WorkerStatus.IDLE
            self.notify()


class WorkerThread(threading.Thread):
    def __init__(self, worker):
        super(WorkerThread, self).__init__()
        self.name = worker.task.name
        self.worker = worker

    def run(self):
        self.worker.run()


class Task(object):
    def __init__(self, name, action=0, depend=None):
        super(Task, self).__init__()
        self.name = name.replace(" ", "-").upper()
        self.id = None
        self.action = action
        self.priority = TaskPriority.NORMAL
        self.status = TaskStatus.QUEUED
        self.added = None
        self.result = None
        self.error_message = None
        self.depend = depend

    def run(self):
        pass

    def finish(self):
        pass

    def is_finished(self):
        return self.status == TaskStatus.FINISHED

    def is_started(self):
        return self.status == TaskStatus.STARTED

    def is_queued(self):
        return self.status == TaskStatus.QUEUED

    def is_failed(self):
        return self.status == TaskStatus.FAILED

    def get_status(self):
        return self.status

    def can_run(self, tasks):
        if self.depend is not None:
            for dependency in self.depend:
                task = tasks.get(dependency, None)
                if task is None:
                    # sickrage.app.log.debug("Cannot run task " + str(self.id) + ". Unable to find task " + str(dependency) + " in queue.")
                    return False
                if not task.is_finished():
                    # sickrage.app.log.debug("Cannot run task " + str(self.id) + ". Task " + str(dependency) + " is not finished")
                    return False

        return True
