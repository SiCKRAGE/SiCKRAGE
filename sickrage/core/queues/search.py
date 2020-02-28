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


import traceback

from apscheduler.triggers.interval import IntervalTrigger

import sickrage
from sickrage.core.databases.main import MainDB
from sickrage.core.queues import SRQueue, SRQueueItem, SRQueuePriorities
from sickrage.core.search import search_providers, snatch_episode
from sickrage.core.tv.show.helpers import find_show
from sickrage.core.tv.show.history import FailedHistory, History

BACKLOG_SEARCH = 10
DAILY_SEARCH = 20
FAILED_SEARCH = 30
MANUAL_SEARCH = 40


class SearchQueue(SRQueue):
    def __init__(self):
        SRQueue.__init__(self, "SEARCHQUEUE")
        self.SNATCH_HISTORY = []
        self.SNATCH_HISTORY_SIZE = 100
        self.MANUAL_SEARCH_HISTORY = []
        self.MANUAL_SEARCH_HISTORY_SIZE = 100

        self.scheduler.add_job(
            self.run,
            IntervalTrigger(
                seconds=1,
                timezone='utc'
            ),
            name=self.name,
            id=self.name
        )

    def fifo(self, my_list, item, max_size=100):
        if len(my_list) >= max_size:
            my_list.pop(0)
        my_list.append(item)

    def is_in_queue(self, show_id, season, episode):
        for cur_item in self.queue_items:
            if isinstance(cur_item, BacklogQueueItem) and all([cur_item.show_id == show_id, cur_item.season == season, cur_item.episode == episode]):
                return True
        return False

    def is_ep_in_queue(self, season, episode):
        for cur_item in self.queue_items:
            if isinstance(cur_item, (ManualSearchQueueItem, FailedQueueItem)) and all([cur_item.season == season, cur_item.episode == episode]):
                return True
        return False

    def is_show_in_queue(self, show_id):
        for cur_item in self.queue_items:
            if isinstance(cur_item, (ManualSearchQueueItem, FailedQueueItem)) and cur_item.show_id == show_id:
                return True
        return False

    def get_all_items_from_queue(self, show_id):
        items = []
        for cur_item in self.queue_items:
            if isinstance(cur_item, (ManualSearchQueueItem, FailedQueueItem)) and cur_item.show_id == show_id:
                items.append(cur_item)
        return items

    def remove_from_queue(self, show_id, season, episode):
        for cur_item in self.queue_items:
            if all([cur_item.show_id == show_id, cur_item.season == season, cur_item.episode == episode]):
                self.stop_item(cur_item)

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
        elif isinstance(item, BacklogQueueItem) and not self.is_in_queue(item.show_id, item.season, item.episode):
            # backlog searches
            sickrage.app.io_loop.add_callback(super(SearchQueue, self).put, item)
        elif isinstance(item, (ManualSearchQueueItem, FailedQueueItem)) and not self.is_ep_in_queue(item.season, item.episode):
            # manual and failed searches
            sickrage.app.io_loop.add_callback(super(SearchQueue, self).put, item)
        else:
            sickrage.app.log.debug("Not adding item, it's already in the queue")


class DailySearchQueueItem(SRQueueItem):
    def __init__(self, show_id, season, episode):
        super(DailySearchQueueItem, self).__init__('Daily Search', DAILY_SEARCH)
        self.name = 'DAILY-{}'.format(show_id)
        self.show_id = show_id
        self.season = season
        self.episode = episode
        self.success = False
        self.started = False

    def run(self):
        self.started = True

        show_obj = find_show(self.show_id)

        try:
            sickrage.app.log.info("Starting daily search for: [" + show_obj.name + "]")

            search_result = search_providers(self.show_id, self.season, self.episode, cacheOnly=sickrage.app.config.enable_rss_cache)
            if search_result:
                for episode in search_result.episodes:
                    if (search_result.show_id, search_result.season, episode) in sickrage.app.search_queue.SNATCH_HISTORY:
                        raise StopIteration

                    sickrage.app.search_queue.fifo(sickrage.app.search_queue.SNATCH_HISTORY, (search_result.show_id, search_result.season, episode),
                                                   sickrage.app.search_queue.SNATCH_HISTORY_SIZE)

                sickrage.app.log.info("Downloading " + search_result.name + " from " + search_result.provider.name)
                snatch_episode(search_result)
            else:
                sickrage.app.log.info("Unable to find search results for: [" + show_obj.name + "]")
        except StopIteration:
            pass
        except Exception:
            sickrage.app.log.debug(traceback.format_exc())
        finally:
            sickrage.app.log.info("Finished daily search for: [" + show_obj.name + "]")


class ManualSearchQueueItem(SRQueueItem):
    def __init__(self, show_id, season, episode, downCurQuality=False):
        super(ManualSearchQueueItem, self).__init__('Manual Search', MANUAL_SEARCH)
        self.name = 'MANUAL-{}'.format(show_id)
        self.show_id = show_id
        self.season = season
        self.episode = episode
        self.success = False
        self.started = False
        self.priority = SRQueuePriorities.EXTREME
        self.downCurQuality = downCurQuality

    def run(self):
        self.started = True

        show_object = find_show(self.show_id)
        episode_object = show_object.get_episode(self.season, self.episode)

        try:
            sickrage.app.log.info("Starting manual search for: [" + episode_object.pretty_name() + "]")

            search_result = search_providers(self.show_id, self.season, self.episode, manualSearch=True, downCurQuality=self.downCurQuality)
            if search_result:
                sickrage.app.log.info("Downloading " + search_result.name + " from " + search_result.provider.name)
                for episode in search_result.episodes:
                    sickrage.app.search_queue.fifo(sickrage.app.search_queue.SNATCH_HISTORY, (search_result.show_id, search_result.season, episode),
                                                   sickrage.app.search_queue.SNATCH_HISTORY_SIZE)

                self.success = snatch_episode(search_result)
            else:
                sickrage.app.alerts.message(
                    _('No downloads were found'),
                    _("Couldn't find a download for <i>%s</i>") % episode_object.pretty_name()
                )

                sickrage.app.log.info("Unable to find a download for: [" + episode_object.pretty_name() + "]")
        except Exception:
            sickrage.app.log.debug(traceback.format_exc())
        finally:
            sickrage.app.log.info("Finished manual search for: [" + episode_object.pretty_name() + "]")
            sickrage.app.search_queue.fifo(sickrage.app.search_queue.MANUAL_SEARCH_HISTORY, self, sickrage.app.search_queue.MANUAL_SEARCH_HISTORY_SIZE)


class BacklogQueueItem(SRQueueItem):
    def __init__(self, show_id, season, episode):
        super(BacklogQueueItem, self).__init__('Backlog Search', BACKLOG_SEARCH)
        self.name = 'BACKLOG-{}'.format(show_id)
        self.show_id = show_id
        self.season = season
        self.episode = episode
        self.priority = SRQueuePriorities.LOW
        self.success = False
        self.started = False

    def run(self):
        self.started = True

        show_object = find_show(self.show_id)

        try:
            sickrage.app.log.info("Starting backlog search for: [" + show_object.name + "]")

            search_result = search_providers(self.show_id, self.season, self.episode, manualSearch=False)
            if search_result:
                for episode in search_result.episodes:
                    if (search_result.show_id, search_result.season, episode) in sickrage.app.search_queue.SNATCH_HISTORY:
                        raise StopIteration

                    sickrage.app.search_queue.fifo(sickrage.app.search_queue.SNATCH_HISTORY, (search_result.show_id, search_result.season, episode),
                                                   sickrage.app.search_queue.SNATCH_HISTORY_SIZE)

                sickrage.app.log.info("Downloading " + search_result.name + " from " + search_result.provider.name)
                snatch_episode(search_result)
            else:
                sickrage.app.log.info("Unable to find search results for: [" + show_object.name + "]")
        except StopIteration:
            pass
        except Exception:
            sickrage.app.log.debug(traceback.format_exc())
        finally:
            sickrage.app.log.info("Finished backlog search for: [" + show_object.name + "]")


class FailedQueueItem(SRQueueItem):
    def __init__(self, show_id, season, episode, downCurQuality=False):
        super(FailedQueueItem, self).__init__('Retry', FAILED_SEARCH)
        self.name = 'RETRY-{}'.format(show_id)
        self.show_id = show_id
        self.season = season
        self.episode = episode
        self.priority = SRQueuePriorities.HIGH
        self.downCurQuality = downCurQuality
        self.success = False
        self.started = False

    def run(self):
        self.started = True

        show_object = find_show(self.show_id)
        episode_object = show_object.get_episode(self.season, self.episode)

        try:
            sickrage.app.log.info("Starting failed download search for: [" + episode_object.name + "]")

            sickrage.app.log.info("Marking episode as bad: [" + episode_object.pretty_name() + "]")

            FailedHistory.mark_failed(self.show_id, self.season, self.episode)

            (release, provider) = FailedHistory.find_failed_release(self.show_id, self.season, self.episode)
            if release:
                FailedHistory.log_failed(release)
                History.log_failed(self.show_id, self.season, self.episode, release, provider)

            FailedHistory.revert_failed_episode(self.show_id, self.season, self.episode)

            search_result = search_providers(self.show_id, self.season, self.episode, manualSearch=True, downCurQuality=False)
            if search_result:
                for episode in search_result.episodes:
                    if (search_result.show_id, search_result.season, episode) in sickrage.app.search_queue.SNATCH_HISTORY:
                        raise StopIteration

                    sickrage.app.search_queue.fifo(sickrage.app.search_queue.SNATCH_HISTORY, (search_result.show_id, search_result.season, episode),
                                                   sickrage.app.search_queue.SNATCH_HISTORY_SIZE)

                sickrage.app.log.info("Downloading " + search_result.name + " from " + search_result.provider.name)
                snatch_episode(search_result)
        except StopIteration:
            pass
        except Exception:
            sickrage.app.log.debug(traceback.format_exc())
        finally:
            sickrage.app.log.info("Finished failed download search for: [" + show_object.name + "]")
            sickrage.app.search_queue.fifo(sickrage.app.search_queue.MANUAL_SEARCH_HISTORY, self, sickrage.app.search_queue.MANUAL_SEARCH_HISTORY_SIZE)
