# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
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
import time
import traceback

import sickrage
from sickrage.core.common import cpu_presets
from sickrage.core.queues import srQueue, srQueueItem, srQueuePriorities
from sickrage.core.search import searchForNeededEpisodes, searchProviders, \
    snatchEpisode
from sickrage.core.tv.show.history import FailedHistory, History

search_queue_lock = threading.Lock()

BACKLOG_SEARCH = 10
DAILY_SEARCH = 20
FAILED_SEARCH = 30
MANUAL_SEARCH = 40

MANUAL_SEARCH_HISTORY = []
MANUAL_SEARCH_HISTORY_SIZE = 100


def fifo(myList, item, maxSize=100):
    if len(myList) >= maxSize:
        myList.pop(0)
    myList.append(item)


class srSearchQueue(srQueue):
    def __init__(self):
        srQueue.__init__(self, "SEARCHQUEUE")

    def is_in_queue(self, show, segment):
        for cur_priority, cur_item in self.queue:
            if isinstance(cur_item, BacklogQueueItem) and cur_item.show == show and cur_item.segment == segment:
                return True
        return False

    def is_ep_in_queue(self, segment):
        for cur_priority, cur_item in self.queue:
            if isinstance(cur_item, (ManualSearchQueueItem, FailedQueueItem)) and cur_item.segment == segment:
                return True
        return False

    def is_show_in_queue(self, show):
        for cur_priority, cur_item in self.queue:
            if isinstance(cur_item, (ManualSearchQueueItem, FailedQueueItem)) and cur_item.show.indexerid == show:
                return True
        return False

    def get_all_ep_from_queue(self, show):
        ep_obj_list = []
        for cur_priority, cur_item in self.queue:
            if isinstance(cur_item, (ManualSearchQueueItem, FailedQueueItem)) and str(cur_item.show.indexerid) == show:
                ep_obj_list.append(cur_item)
        return ep_obj_list

    def pause_backlog(self):
        self.min_priority = srQueuePriorities.HIGH
        sickrage.srCore.srScheduler.pause_job('BACKLOG')

    def unpause_backlog(self):
        self.min_priority = 0
        sickrage.srCore.srScheduler.resume_job('BACKLOG')

    def is_backlog_paused(self):
        # backlog priorities are NORMAL, this should be done properly somewhere
        return self.min_priority >= srQueuePriorities.NORMAL

    def is_manualsearch_in_progress(self):
        # Only referenced in webviews.py, only current running manualsearch or failedsearch is needed!!
        if isinstance(self.currentItem, (ManualSearchQueueItem, FailedQueueItem)):
            return True

        return False

    def is_backlog_in_progress(self):
        for cur_priority, cur_item in self.queue + [(0, self.currentItem)]:
            if isinstance(cur_item, BacklogQueueItem):
                return True

        return False

    def is_dailysearch_in_progress(self):
        for cur_priority, cur_item in self.queue + [(0, self.currentItem)]:
            if isinstance(cur_item, DailySearchQueueItem):
                return True

        return False

    def queue_length(self):
        length = {'backlog': 0, 'daily': 0, 'manual': 0, 'failed': 0}
        for cur_priority, cur_item in self.queue:
            if isinstance(cur_item, DailySearchQueueItem):
                length['daily'] += 1
            elif isinstance(cur_item, BacklogQueueItem):
                length['backlog'] += 1
            elif isinstance(cur_item, ManualSearchQueueItem):
                length['manual'] += 1
            elif isinstance(cur_item, FailedQueueItem):
                length['failed'] += 1

        return length

    def put(self, item, *args, **kwargs):
        if not len(sickrage.srCore.providersDict.enabled()):
            sickrage.srCore.srLogger.warning("Search Failed, No NZB/Torrent providers enabled")
            return

        if isinstance(item, DailySearchQueueItem):
            # daily searches
            super(srSearchQueue, self).put(item)
        elif isinstance(item, BacklogQueueItem) and not self.is_in_queue(item.show, item.segment):
            # backlog searches
            super(srSearchQueue, self).put(item)
        elif isinstance(item, (ManualSearchQueueItem, FailedQueueItem)) and not self.is_ep_in_queue(item.segment):
            # manual and failed searches
            super(srSearchQueue, self).put(item)
        else:
            sickrage.srCore.srLogger.debug("Not adding item, it's already in the queue")


class DailySearchQueueItem(srQueueItem):
    def __init__(self):
        super(DailySearchQueueItem, self).__init__('Daily Search', DAILY_SEARCH)
        self.success = False
        self.started = False

    def run(self):
        self.started = True

        try:
            sickrage.srCore.srLogger.info("Starting daily search for new episodes")

            foundResults = searchForNeededEpisodes()
            if foundResults:
                for result in foundResults:
                    # just use the first result for now
                    sickrage.srCore.srLogger.info("Downloading " + result.name + " from " + result.provider.name)
                    self.success = snatchEpisode(result)

                    # give the CPU a break
                    time.sleep(cpu_presets[sickrage.srCore.srConfig.CPU_PRESET])
        except Exception:
            sickrage.srCore.srLogger.debug(traceback.format_exc())
        finally:
            sickrage.srCore.srLogger.info("Finished daily search for new episodes")


class ManualSearchQueueItem(srQueueItem):
    def __init__(self, show, segment, downCurQuality=False):
        super(ManualSearchQueueItem, self).__init__('Manual Search', MANUAL_SEARCH)
        self.name = 'MANUAL-' + str(show.indexerid)
        self.show = show
        self.segment = segment
        self.success = False
        self.started = False
        self.priority = srQueuePriorities.HIGH
        self.downCurQuality = downCurQuality

    def run(self):
        self.started = True

        try:
            sickrage.srCore.srLogger.info("Starting manual search for: [" + self.segment.prettyName() + "]")

            searchResult = searchProviders(self.show, [self.segment], True, self.downCurQuality)
            if searchResult:
                # just use the first result for now
                sickrage.srCore.srLogger.info(
                    "Downloading " + searchResult[0].name + " from " + searchResult[0].provider.name)
                self.success = snatchEpisode(searchResult[0])

                # give the CPU a break
                time.sleep(cpu_presets[sickrage.srCore.srConfig.CPU_PRESET])

            else:
                sickrage.srCore.srNotifications.message(
                    'No downloads were found',
                    "Couldn't find a download for <i>%s</i>" % self.segment.prettyName()
                )

                sickrage.srCore.srLogger.info("Unable to find a download for: [" + self.segment.prettyName() + "]")

        except Exception:
            sickrage.srCore.srLogger.debug(traceback.format_exc())
        finally:
            sickrage.srCore.srLogger.info("Finished manual search for: [" + self.segment.prettyName() + "]")

        # Keep a list with the 100 last executed searches
        fifo(MANUAL_SEARCH_HISTORY, self, MANUAL_SEARCH_HISTORY_SIZE)


class BacklogQueueItem(srQueueItem):
    def __init__(self, show, segment):
        super(BacklogQueueItem, self).__init__('Backlog', BACKLOG_SEARCH)
        self.show = show
        self.name = 'BACKLOG-' + str(show.indexerid)
        self.success = False
        self.started = False
        self.segment = segment
        self.priority = srQueuePriorities.LOW

    def run(self):
        self.started = True

        if not self.show.paused:
            try:
                sickrage.srCore.srLogger.info("Starting backlog search for: [" + self.show.name + "]")

                searchResult = searchProviders(self.show, self.segment, False)
                if searchResult:
                    for result in searchResult:
                        # just use the first result for now
                        sickrage.srCore.srLogger.info("Downloading " + result.name + " from " + result.provider.name)
                        snatchEpisode(result)

                        # give the CPU a break
                        time.sleep(cpu_presets[sickrage.srCore.srConfig.CPU_PRESET])
            except Exception:
                sickrage.srCore.srLogger.debug(traceback.format_exc())
            finally:
                sickrage.srCore.srLogger.info("Finished backlog search for: [" + self.show.name + "]")


class FailedQueueItem(srQueueItem):
    def __init__(self, show, segment, downCurQuality=False):
        super(FailedQueueItem, self).__init__('Retry', FAILED_SEARCH)
        self.show = show
        self.name = 'RETRY-' + str(show.indexerid)
        self.success = False
        self.started = False
        self.segment = segment
        self.priority = srQueuePriorities.HIGH
        self.downCurQuality = downCurQuality

    def run(self):
        self.started = True

        try:
            sickrage.srCore.srLogger.info("Starting failed download search for: [" + self.show.name + "]")

            for epObj in self.segment:
                sickrage.srCore.srLogger.info("Marking episode as bad: [" + epObj.prettyName() + "]")

                FailedHistory.markFailed(epObj)
                (release, provider) = FailedHistory.findFailedRelease(epObj)
                if release:
                    FailedHistory.logFailed(release)
                    History.logFailed(epObj, release, provider)

                FailedHistory.revertFailedEpisode(epObj)

            searchResult = searchProviders(self.show, self.segment, True, False)
            if searchResult:
                for result in searchResult:
                    # just use the first result for now
                    sickrage.srCore.srLogger.info("Downloading " + result.name + " from " + result.provider.name)
                    snatchEpisode(result)

                    # give the CPU a break
                    time.sleep(cpu_presets[sickrage.srCore.srConfig.CPU_PRESET])
        except Exception:
            sickrage.srCore.srLogger.debug(traceback.format_exc())
        finally:
            sickrage.srCore.srLogger.info("Finished failed download search for: [" + self.show.name + "]")

        # Keep a list with the 100 last executed searches
        fifo(MANUAL_SEARCH_HISTORY, self, MANUAL_SEARCH_HISTORY_SIZE)
