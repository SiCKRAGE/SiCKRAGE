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
import os
import time
import traceback
from enum import Enum

import sickrage
from sickrage.core.process_tv import ProcessResult
from sickrage.core.queues import Queue, Task, TaskPriority, TaskStatus


class PostProcessorTaskActions(Enum):
    AUTO = 'Auto'
    MANUAL = 'Manual'


class PostProcessorQueue(Queue):
    def __init__(self):
        Queue.__init__(self, "POSTPROCESSORQUEUE")
        self._output = []

    @property
    def output(self):
        return '\n'.join(self._output)

    def log(self, message, level=None):
        sickrage.app.log.log(level or sickrage.app.log.INFO, message)
        self._output.append(message)

    def clear_log(self):
        self._output = []

    def find_in_queue(self, dirName, proc_type):
        """
        Finds any item in the queue with the given dirName and proc_type pair
        :param dirName: directory to be processed by the task
        :param proc_type: processing type, auto/manual
        :return: instance of PostProcessorTask or None
        """
        for task in self.tasks.copy().values():
            if isinstance(task, PostProcessorTask) and task.dirName == dirName and task.proc_type == proc_type:
                return True

        return False

    @property
    def queue_length(self):
        """
        Returns a dict showing how many auto and manual tasks are in the queue
        :return: dict
        """
        length = {'auto': 0, 'manual': 0}

        for task in self.tasks.copy().values():
            if isinstance(task, PostProcessorTask):
                if task.proc_type == 'auto':
                    length['auto'] += 1
                else:
                    length['manual'] += 1

        return length

    def put(self, dirName, nzbName=None, process_method=None, force=False, is_priority=None, delete_on=False,
            failed=False, proc_type="auto", force_next=False, **kwargs):
        """
        Adds an item to post-processing queue
        :param dirName: directory to process
        :param nzbName: release/nzb name if available
        :param process_method: processing method, copy/move/symlink/link
        :param force: force overwriting of existing files regardless of quality
        :param is_priority: whether to replace the file even if it exists at higher quality
        :param delete_on: delete files and folders after they are processed (always happens with move and auto combination)
        :param failed: mark downloads as failed if they fail to process
        :param proc_type: processing type: auto/manual
        :param force_next: wait until the current item in the queue is finished then process this item next
        :return: string indicating success or failure
        """

        self.clear_log()

        if not dirName:
            self.log("{} post-processing attempted but directory is not set".format(proc_type.title()), sickrage.app.log.WARNING)
            return self.output

        if not os.path.isabs(dirName):
            self.log("{} post-processing attempted but directory is relative (and probably not "
                     "what you really want to process): {}".format(proc_type.title(), dirName),
                     sickrage.app.log.WARNING)
            return self.output

        if not delete_on:
            delete_on = (False, (not sickrage.app.config.general.no_delete, True)[process_method == "move"])[proc_type == "auto"]

        if self.find_in_queue(dirName, proc_type):
            self.log("An item with directory {} is already being processed in the queue".format(dirName))
            return self.output
        else:
            task_id = super(PostProcessorQueue, self).put(
                PostProcessorTask(dirName, nzbName, process_method, force, is_priority, delete_on, failed, proc_type))

            if force_next:
                while self.check_status(task_id) not in [TaskStatus.FINISHED, TaskStatus.FAILED]:
                    time.sleep(1)

                return self.get_result(task_id)

            self.log("{} post-processing job for {} has been added to the queue".format(proc_type.title(), dirName))
            return self.output + "<p><span class='hidden'>Processing succeeded</span></p>"


class PostProcessorTask(Task):
    def __init__(self, dirName, nzbName=None, process_method=None, force=False, is_priority=None, delete_on=False, failed=False, proc_type="auto"):
        action = (PostProcessorTaskActions.MANUAL, PostProcessorTaskActions.AUTO)[proc_type == "auto"]
        super(PostProcessorTask, self).__init__(action.value, action)

        self.dirName = dirName
        self.nzbName = nzbName
        self.process_method = process_method
        self.force = force
        self.is_priority = is_priority
        self.delete_on = delete_on
        self.failed = failed
        self.proc_type = proc_type

        self.priority = (TaskPriority.HIGH, TaskPriority.NORMAL)[proc_type == 'auto']

    def run(self):
        """
        Runs the task
        :return: None
        """

        try:
            sickrage.app.log.info("Started {} post-processing job for: {}".format(self.proc_type, self.dirName))

            result = ProcessResult(self.dirName, self.process_method, self.proc_type).process(
                nzbName=self.nzbName,
                force=self.force,
                is_priority=self.is_priority,
                delete_on=self.delete_on,
                failed=self.failed
            )

            sickrage.app.log.info("Finished {} post-processing job for: {}".format(self.proc_type, self.dirName))
        except Exception:
            sickrage.app.log.debug(traceback.format_exc())
            result = '{}'.format(traceback.format_exc())
            result += 'Processing Failed'

        return result
