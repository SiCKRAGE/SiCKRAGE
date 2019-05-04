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

from tornado import gen

import sickrage
from sickrage.core.common import cpu_presets
from sickrage.core.queues import srQueue, srQueueItem, srQueuePriorities
from sickrage.core.search import search_providers, snatch_episode
from sickrage.core.tv.episode.helpers import find_episode
from sickrage.core.tv.show import find_show
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

    def is_in_queue(self, show_id, episode_ids):
        for cur_item in self.queue_items:
            if isinstance(cur_item,
                          BacklogQueueItem) and cur_item.show_id == show_id and cur_item.episode_ids == episode_ids:
                return True
        return False

    def is_ep_in_queue(self, episode_id):
        for cur_item in self.queue_items:
            if isinstance(cur_item, (ManualSearchQueueItem, FailedQueueItem)) and cur_item.episode_id == episode_id:
                return True
        return False

    def is_show_in_queue(self, show_id):
        for cur_item in self.queue_items:
            if isinstance(cur_item, (ManualSearchQueueItem, FailedQueueItem)) and cur_item.show_id == show_id:
                return True
        return False

    def get_all_episode_ids_from_queue(self, show_id):
        episode_ids = []
        for cur_item in self.queue_items:
            if isinstance(cur_item, (ManualSearchQueueItem, FailedQueueItem)) and str(cur_item.show_id) == show_id:
                episode_ids.append(cur_item.episode_id)
        return episode_ids

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

    def is_manual_search_in_progress(self):
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
        elif isinstance(item, BacklogQueueItem) and not self.is_in_queue(item.show_id, item.episode_ids):
            # backlog searches
            sickrage.app.io_loop.add_callback(super(SearchQueue, self).put, item)
        elif isinstance(item, (ManualSearchQueueItem, FailedQueueItem)) and not self.is_ep_in_queue(item.episode_id):
            # manual and failed searches
            sickrage.app.io_loop.add_callback(super(SearchQueue, self).put, item)
        else:
            sickrage.app.log.debug("Not adding item, it's already in the queue")


class DailySearchQueueItem(srQueueItem):
    def __init__(self, show_id, episode_ids):
        super(DailySearchQueueItem, self).__init__('Daily Search', DAILY_SEARCH)
        self.name = 'DAILY-{}'.format(show_id)
        self.show_id = show_id
        self.episode_ids = episode_ids
        self.success = False
        self.started = False

    def run(self):
        self.started = True

        show_obj = find_show(self.show_id)

        try:
            sickrage.app.log.info("Starting daily search for: [" + show_obj.name + "]")

            search_result = search_providers(self.show_id, self.episode_ids, cacheOnly=sickrage.app.config.enable_rss_cache)
            if search_result:
                for result in search_result:
                    # just use the first result for now
                    sickrage.app.log.info("Downloading " + result.name + " from " + result.provider.name)
                    snatch_episode(result)

                    # give the CPU a break
                    time.sleep(cpu_presets[sickrage.app.config.cpu_preset])
            else:
                sickrage.app.log.info("Unable to find search results for: [" + show_obj.name + "]")
        except Exception:
            sickrage.app.log.debug(traceback.format_exc())
        finally:
            sickrage.app.log.info("Finished daily search for: [" + show_obj.name + "]")


class ManualSearchQueueItem(srQueueItem):
    def __init__(self, show_id, episode_id, downCurQuality=False):
        super(ManualSearchQueueItem, self).__init__('Manual Search', MANUAL_SEARCH)
        self.name = 'MANUAL-{}'.format(show_id)
        self.show_id = show_id
        self.episode_id = episode_id
        self.success = False
        self.started = False
        self.priority = srQueuePriorities.EXTREME
        self.downCurQuality = downCurQuality

    def run(self):
        self.started = True

        episode_obj = find_episode(self.show_id, self.episode_id)

        try:
            sickrage.app.log.info("Starting manual search for: [" + episode_obj.pretty_name() + "]")

            search_result = search_providers(self.show_id, [self.episode_id], manualSearch=True,
                                             downCurQuality=self.downCurQuality)
            if search_result:
                # just use the first result for now
                sickrage.app.log.info(
                    "Downloading " + search_result[0].name + " from " + search_result[0].provider.name)
                self.success = snatch_episode(search_result[0])

                # give the CPU a break
                time.sleep(cpu_presets[sickrage.app.config.cpu_preset])

            else:
                sickrage.app.alerts.message(
                    _('No downloads were found'),
                    _("Couldn't find a download for <i>%s</i>") % episode_obj.pretty_name()
                )

                sickrage.app.log.info("Unable to find a download for: [" + episode_obj.pretty_name() + "]")
        except Exception:
            sickrage.app.log.debug(traceback.format_exc())
        finally:
            sickrage.app.log.info("Finished manual search for: [" + episode_obj.pretty_name() + "]")

        # Keep a list with the 100 last executed searches
        fifo(MANUAL_SEARCH_HISTORY, self, MANUAL_SEARCH_HISTORY_SIZE)


class BacklogQueueItem(srQueueItem):
    def __init__(self, show_id, episode_ids):
        super(BacklogQueueItem, self).__init__('Backlog Search', BACKLOG_SEARCH)
        self.name = 'BACKLOG-{}'.format(show_id)
        self.show_id = show_id
        self.episode_ids = episode_ids
        self.priority = srQueuePriorities.LOW
        self.success = False
        self.started = False

    async def run(self):
        self.started = True

        show_obj = find_show(self.show_id)

        try:
            sickrage.app.log.info("Starting backlog search for: [" + show_obj.name + "]")

            search_result = search_providers(self.show_id, self.episode_ids, manualSearch=False)
            if search_result:
                for result in search_result:
                    # just use the first result for now
                    sickrage.app.log.info("Downloading " + result.name + " from " + result.provider.name)
                    snatch_episode(result)

                    # give the CPU a break
                    await gen.sleep(cpu_presets[sickrage.app.config.cpu_preset])
            else:
                sickrage.app.log.info("Unable to find search results for: [" + show_obj.name + "]")
        except Exception:
            sickrage.app.log.debug(traceback.format_exc())
        finally:
            sickrage.app.log.info("Finished backlog search for: [" + show_obj.name + "]")


class FailedQueueItem(srQueueItem):
    def __init__(self, show_id, episode_id, downCurQuality=False):
        super(FailedQueueItem, self).__init__('Retry', FAILED_SEARCH)
        self.name = 'RETRY-{}'.format(show_id)
        self.show_id = show_id
        self.episode_id = episode_id
        self.priority = srQueuePriorities.HIGH
        self.downCurQuality = downCurQuality
        self.success = False
        self.started = False

    def run(self):
        self.started = True

        show_obj = find_show(self.show_id)

        try:
            sickrage.app.log.info("Starting failed download search for: [" + show_obj.name + "]")

            episode_obj = find_episode(self.show_id, self.episode_id)

            sickrage.app.log.info("Marking episode as bad: [" + episode_obj.pretty_name() + "]")

            FailedHistory.mark_failed(episode_obj)

            (release, provider) = FailedHistory.find_failed_release(episode_obj)
            if release:
                FailedHistory.log_failed(release)
                History.log_failed(self.show_id, self.episode_id, release, provider)

            FailedHistory.revert_failed_episode(self.show_id, self.episode_id)

            search_result = search_providers(show_obj, [self.episode_id], manualSearch=True, downCurQuality=False)
            if search_result:
                for result in search_result:
                    # just use the first result for now
                    sickrage.app.log.info("Downloading " + result.name + " from " + result.provider.name)
                    snatch_episode(result)

                    # give the CPU a break
                    time.sleep(cpu_presets[sickrage.app.config.cpu_preset])
        except Exception:
            sickrage.app.log.debug(traceback.format_exc())
        finally:
            sickrage.app.log.info("Finished failed download search for: [" + show_obj.name + "]")

        # Keep a list with the 100 last executed searches
        fifo(MANUAL_SEARCH_HISTORY, self, MANUAL_SEARCH_HISTORY_SIZE)
