# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
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



import threading
import time
import traceback

from tornado.ioloop import IOLoop

import sickrage
from sickrage.core.common import cpu_presets
from sickrage.core.queues import srQueue, srQueueItem, srQueuePriorities
from sickrage.core.search import searchProviders, snatchEpisode
from sickrage.core.tv.show.history import FailedHistory, History

search_queue_lock = threading.Lock()

BACKLOG_SEARCH = 10
DAILY_SEARCH = 20
FAILED_SEARCH = 30
MANUAL_SEARCH = 40

MANUAL_SEARCH_HISTORY = []
MANUAL_SEARCH_HISTORY_SIZE = 100


def fifo(my_list, item, max_size=100):
    if len(my_list) >= max_size:
        my_list.pop(0)
    my_list.append(item)


class SearchQueue(srQueue):
    def __init__(self):
        srQueue.__init__(self, "SEARCHQUEUE")

    def is_in_queue(self, show, segment):
        for cur_item in self.queue_items:
            if isinstance(cur_item, BacklogQueueItem) and cur_item.show == show and cur_item.segment == segment:
                return True
        return False

    def is_ep_in_queue(self, segment):
        for cur_item in self.queue_items:
            if isinstance(cur_item, (ManualSearchQueueItem, FailedQueueItem)) and cur_item.segment == segment:
                return True
        return False

    def is_show_in_queue(self, show):
        for cur_item in self.queue_items:
            if isinstance(cur_item, (ManualSearchQueueItem, FailedQueueItem)) and cur_item.show.indexer_id == show:
                return True
        return False

    def get_all_ep_from_queue(self, show):
        ep_obj_list = []
        for cur_item in self.queue_items:
            if isinstance(cur_item, (ManualSearchQueueItem, FailedQueueItem)) and str(cur_item.show.indexer_id) == show:
                ep_obj_list.append(cur_item)
        return ep_obj_list

    def pause_daily_searcher(self):
        sickrage.app.scheduler.pause_job(sickrage.app.daily_searcher.name)

    def unpause_daily_searcher(self):
        sickrage.app.scheduler.resume_job(sickrage.app.daily_searcher.name)

    def is_daily_searcher_paused(self):
        return not sickrage.app.scheduler.get_job(sickrage.app.daily_searcher.name).next_run_time

    def pause_backlog_searcher(self):
        sickrage.app.scheduler.pause_job(sickrage.app.backlog_searcher.name)

    def unpause_backlog_searcher(self):
        sickrage.app.scheduler.resume_job(sickrage.app.backlog_searcher.name)

    def is_backlog_searcher_paused(self):
        return not sickrage.app.scheduler.get_job(sickrage.app.backlog_searcher.name).next_run_time

    def is_manualsearch_in_progress(self):
        for cur_item in self.queue_items:
            if isinstance(cur_item, (ManualSearchQueueItem, FailedQueueItem)):
                return True
        return False

    def is_backlog_in_progress(self):
        for cur_item in self.queue_items:
            if isinstance(cur_item, BacklogQueueItem):
                return True
        return False

    def is_dailysearch_in_progress(self):
        for cur_item in self.queue_items:
            if isinstance(cur_item, DailySearchQueueItem):
                return True

        return False

    def queue_length(self):
        length = {'backlog': 0, 'daily': 0, 'manual': 0, 'failed': 0}
        for cur_item in self.queue_items:
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
        if all([not sickrage.app.config.use_nzbs, not sickrage.app.config.use_torrents]):
            return

        if not len(sickrage.app.search_providers.enabled()):
            sickrage.app.log.warning("Search Failed, No NZB/Torrent providers enabled")
            return

        if isinstance(item, DailySearchQueueItem):
            # daily searches
            sickrage.app.io_loop.add_callback(super(SearchQueue, self).put, item)
        elif isinstance(item, BacklogQueueItem) and not self.is_in_queue(item.show, item.segment):
            # backlog searches
            sickrage.app.io_loop.add_callback(super(SearchQueue, self).put, item)
        elif isinstance(item, (ManualSearchQueueItem, FailedQueueItem)) and not self.is_ep_in_queue(item.segment):
            # manual and failed searches
            sickrage.app.io_loop.add_callback(super(SearchQueue, self).put, item)
        else:
            sickrage.app.log.debug("Not adding item, it's already in the queue")


class DailySearchQueueItem(srQueueItem):
    def __init__(self, show, segment):
        super(DailySearchQueueItem, self).__init__('Daily Search', DAILY_SEARCH)
        self.name = 'DAILY-' + str(show.indexer_id)
        self.show = show
        self.segment = segment
        self.success = False
        self.started = False

    def run(self):
        self.started = True

        try:
            sickrage.app.log.info("Starting daily search for: [" + self.show.name + "]")

            search_result = searchProviders(self.show, self.segment, cacheOnly=sickrage.app.config.enable_rss_cache)
            if search_result:
                for result in search_result:
                    # just use the first result for now
                    sickrage.app.log.info("Downloading " + result.name + " from " + result.provider.name)
                    snatchEpisode(result)

                    # give the CPU a break
                    time.sleep(cpu_presets[sickrage.app.config.cpu_preset])
            else:
                sickrage.app.log.info("Unable to find search results for: [" + self.show.name + "]")
        except Exception:
            sickrage.app.log.debug(traceback.format_exc())
        finally:
            sickrage.app.log.info("Finished daily search for: [" + self.show.name + "]")


class ManualSearchQueueItem(srQueueItem):
    def __init__(self, show, segment, downCurQuality=False):
        super(ManualSearchQueueItem, self).__init__('Manual Search', MANUAL_SEARCH)
        self.name = 'MANUAL-' + str(show.indexer_id)
        self.show = show
        self.segment = segment
        self.success = False
        self.started = False
        self.priority = srQueuePriorities.EXTREME
        self.downCurQuality = downCurQuality

    def run(self):
        self.started = True

        try:
            sickrage.app.log.info("Starting manual search for: [" + self.segment.pretty_name() + "]")

            search_result = searchProviders(self.show, [self.segment], manualSearch=True,
                                            downCurQuality=self.downCurQuality)
            if search_result:
                # just use the first result for now
                sickrage.app.log.info(
                    "Downloading " + search_result[0].name + " from " + search_result[0].provider.name)
                self.success = snatchEpisode(search_result[0])

                # give the CPU a break
                time.sleep(cpu_presets[sickrage.app.config.cpu_preset])

            else:
                sickrage.app.alerts.message(
                    _('No downloads were found'),
                    _("Couldn't find a download for <i>%s</i>") % self.segment.pretty_name()
                )

                sickrage.app.log.info("Unable to find a download for: [" + self.segment.pretty_name() + "]")
        except Exception:
            sickrage.app.log.debug(traceback.format_exc())
        finally:
            sickrage.app.log.info("Finished manual search for: [" + self.segment.pretty_name() + "]")

        # Keep a list with the 100 last executed searches
        fifo(MANUAL_SEARCH_HISTORY, self, MANUAL_SEARCH_HISTORY_SIZE)


class BacklogQueueItem(srQueueItem):
    def __init__(self, show, segment):
        super(BacklogQueueItem, self).__init__('Backlog Search', BACKLOG_SEARCH)
        self.name = 'BACKLOG-' + str(show.indexer_id)
        self.show = show
        self.segment = segment
        self.priority = srQueuePriorities.LOW
        self.success = False
        self.started = False

    def run(self):
        self.started = True

        try:
            sickrage.app.log.info("Starting backlog search for: [" + self.show.name + "]")

            search_result = searchProviders(self.show, self.segment, manualSearch=False)
            if search_result:
                for result in search_result:
                    # just use the first result for now
                    sickrage.app.log.info("Downloading " + result.name + " from " + result.provider.name)
                    snatchEpisode(result)

                    # give the CPU a break
                    time.sleep(cpu_presets[sickrage.app.config.cpu_preset])
            else:
                sickrage.app.log.info("Unable to find search results for: [" + self.show.name + "]")
        except Exception:
            sickrage.app.log.debug(traceback.format_exc())
        finally:
            sickrage.app.log.info("Finished backlog search for: [" + self.show.name + "]")


class FailedQueueItem(srQueueItem):
    def __init__(self, show, segment, downCurQuality=False):
        super(FailedQueueItem, self).__init__('Retry', FAILED_SEARCH)
        self.name = 'RETRY-' + str(show.indexer_id)
        self.show = show
        self.segment = segment
        self.priority = srQueuePriorities.HIGH
        self.downCurQuality = downCurQuality
        self.success = False
        self.started = False

    def run(self):
        self.started = True

        try:
            sickrage.app.log.info("Starting failed download search for: [" + self.show.name + "]")

            for epObj in self.segment:
                sickrage.app.log.info("Marking episode as bad: [" + epObj.pretty_name() + "]")

                FailedHistory.markFailed(epObj)

                (release, provider) = FailedHistory.findFailedRelease(epObj)
                if release:
                    FailedHistory.logFailed(release)
                    History.logFailed(epObj, release, provider)

                FailedHistory.revertFailedEpisode(epObj)

            search_result = searchProviders(self.show, self.segment, manualSearch=True, downCurQuality=False)
            if search_result:
                for result in search_result:
                    # just use the first result for now
                    sickrage.app.log.info("Downloading " + result.name + " from " + result.provider.name)
                    snatchEpisode(result)

                    # give the CPU a break
                    time.sleep(cpu_presets[sickrage.app.config.cpu_preset])
        except Exception:
            sickrage.app.log.debug(traceback.format_exc())
        finally:
            sickrage.app.log.info("Finished failed download search for: [" + self.show.name + "]")

        # Keep a list with the 100 last executed searches
        fifo(MANUAL_SEARCH_HISTORY, self, MANUAL_SEARCH_HISTORY_SIZE)
