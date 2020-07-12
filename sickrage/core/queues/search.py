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
from collections import deque
from enum import Enum

import sickrage
from sickrage.core.queues import Queue, Task, TaskPriority
from sickrage.core.search import search_providers, snatch_episode
from sickrage.core.tv.show.helpers import find_show
from sickrage.core.tv.show.history import FailedHistory, History


class SearchTaskActions(Enum):
    BACKLOG_SEARCH = 'Backlog Search'
    DAILY_SEARCH = 'Daily Search'
    FAILED_SEARCH = 'Failed Search'
    MANUAL_SEARCH = 'Manual Search'


class SearchQueue(Queue):
    def __init__(self):
        Queue.__init__(self, "SEARCHQUEUE")
        self.SNATCH_HISTORY = deque(maxlen=100)
        self.MANUAL_SEARCH_HISTORY = deque(maxlen=100)

    def is_in_queue(self, show_id, season, episode):
        for task in self.tasks.copy().values():
            if all([isinstance(task, BacklogSearchTask), task.show_id == show_id, task.season == season, task.episode == episode]):
                return True

        return False

    def is_ep_in_queue(self, season, episode):
        for task in self.tasks.copy().values():
            if all([isinstance(task, (ManualSearchTask, FailedSearchTask)), task.season == season, task.episode == episode]):
                return True

        return False

    def is_show_in_queue(self, show_id):
        return any(isinstance(task, (ManualSearchTask, FailedSearchTask)) and task.show_id == show_id for task in self.tasks.copy().values())

    def get_all_tasks_from_queue(self, show_id):
        return [task for task in self.tasks.copy().values() if isinstance(task, (ManualSearchTask, FailedSearchTask)) and task.show_id == show_id]

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
        return any(isinstance(task, (ManualSearchTask, FailedSearchTask)) for task in self.tasks.copy().values())

    def is_backlog_in_progress(self):
        return any(isinstance(task, BacklogSearchTask) for task in self.tasks.copy().values())

    def is_dailysearch_in_progress(self):
        return any(isinstance(task, DailySearchTask) for task in self.tasks.copy().values())

    def queue_length(self):
        length = {'backlog': 0, 'daily': 0, 'manual': 0, 'failed': 0}
        for task in self.tasks.copy().values():
            if isinstance(task, DailySearchTask):
                length['daily'] += 1
            elif isinstance(task, BacklogSearchTask):
                length['backlog'] += 1
            elif isinstance(task, ManualSearchTask):
                length['manual'] += 1
            elif isinstance(task, FailedSearchTask):
                length['failed'] += 1

        return length

    def put(self, item, *args, **kwargs):
        if all([not sickrage.app.config.use_nzbs, not sickrage.app.config.use_torrents]):
            return

        if not len(sickrage.app.search_providers.enabled()):
            sickrage.app.log.warning("Search Failed, No NZB/Torrent providers enabled")
            return

        if isinstance(item, DailySearchTask):
            # daily searches
            super(SearchQueue, self).put(item)
        elif isinstance(item, BacklogSearchTask) and not self.is_in_queue(item.show_id, item.season, item.episode):
            # backlog searches
            super(SearchQueue, self).put(item)
        elif isinstance(item, (ManualSearchTask, FailedSearchTask)) and not self.is_ep_in_queue(item.season, item.episode):
            # manual and failed searches
            super(SearchQueue, self).put(item)
        else:
            sickrage.app.log.debug("Not adding item, it's already in the queue")


class DailySearchTask(Task):
    def __init__(self, show_id, season, episode):
        super(DailySearchTask, self).__init__(SearchTaskActions.DAILY_SEARCH.value, SearchTaskActions.DAILY_SEARCH)
        self.name = 'DAILY-{}'.format(show_id)
        self.show_id = show_id
        self.season = season
        self.episode = episode
        self.success = False
        self.started = False

    def run(self):
        self.started = True

        show_obj = find_show(self.show_id)
        if not show_obj:
            return

        try:
            sickrage.app.log.info("Starting daily search for: [" + show_obj.name + "]")

            search_result = search_providers(self.show_id, self.season, self.episode, cacheOnly=sickrage.app.config.enable_rss_cache)
            if search_result:
                snatch = all([(search_result.show_id, search_result.season, episode)
                              not in sickrage.app.search_queue.SNATCH_HISTORY for episode in search_result.episodes])

                if snatch:
                    [sickrage.app.search_queue.SNATCH_HISTORY.append((search_result.show_id, search_result.season, episode)) for episode in
                     search_result.episodes]

                    sickrage.app.log.info("Downloading " + search_result.name + " from " + search_result.provider.name)
                    snatch_episode(search_result)
            else:
                sickrage.app.log.info("Unable to find search results for: [" + show_obj.name + "]")
        except Exception:
            sickrage.app.log.debug(traceback.format_exc())
        finally:
            sickrage.app.log.info("Finished daily search for: [" + show_obj.name + "]")


class ManualSearchTask(Task):
    def __init__(self, show_id, season, episode, downCurQuality=False):
        super(ManualSearchTask, self).__init__(SearchTaskActions.MANUAL_SEARCH.value, SearchTaskActions.MANUAL_SEARCH)
        self.name = 'MANUAL-{}'.format(show_id)
        self.show_id = show_id
        self.season = season
        self.episode = episode
        self.success = False
        self.started = False
        self.priority = TaskPriority.EXTREME
        self.downCurQuality = downCurQuality
        self.auto_remove = False

    def run(self):
        self.started = True

        show_object = find_show(self.show_id)
        if not show_object:
            return

        episode_object = show_object.get_episode(self.season, self.episode)

        try:
            sickrage.app.log.info("Starting manual search for: [" + episode_object.pretty_name() + "]")

            search_result = search_providers(self.show_id, self.season, self.episode, manualSearch=True, downCurQuality=self.downCurQuality)
            if search_result:
                [sickrage.app.search_queue.SNATCH_HISTORY.append((search_result.show_id, search_result.season, episode)) for episode in
                 search_result.episodes]

                sickrage.app.log.info("Downloading " + search_result.name + " from " + search_result.provider.name)
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
            sickrage.app.search_queue.MANUAL_SEARCH_HISTORY.append(self)


class BacklogSearchTask(Task):
    def __init__(self, show_id, season, episode):
        super(BacklogSearchTask, self).__init__(SearchTaskActions.BACKLOG_SEARCH.value, SearchTaskActions.BACKLOG_SEARCH)
        self.name = 'BACKLOG-{}'.format(show_id)
        self.show_id = show_id
        self.season = season
        self.episode = episode
        self.priority = TaskPriority.LOW
        self.success = False
        self.started = False

    def run(self):
        self.started = True

        show_object = find_show(self.show_id)
        if not show_object:
            return

        try:
            sickrage.app.log.info("Starting backlog search for: [{}] S{:02d}E{:02d}".format(show_object.name, self.season, self.episode))

            search_result = search_providers(self.show_id, self.season, self.episode, manualSearch=False)
            if search_result:
                snatch = all([(search_result.show_id, search_result.season, episode)
                              not in sickrage.app.search_queue.SNATCH_HISTORY for episode in search_result.episodes])

                if snatch:
                    [sickrage.app.search_queue.SNATCH_HISTORY.append((search_result.show_id, search_result.season, episode)) for episode in
                     search_result.episodes]

                    sickrage.app.log.info("Downloading {} from {}".format(search_result.name, search_result.provider.name))
                    snatch_episode(search_result)
            else:
                sickrage.app.log.info("Unable to find search results for: [{}] S{:02d}E{:02d}".format(show_object.name, self.season, self.episode))
        except Exception:
            sickrage.app.log.debug(traceback.format_exc())
        finally:
            sickrage.app.log.info("Finished backlog search for: [{}] S{:02d}E{:02d}".format(show_object.name, self.season, self.episode))


class FailedSearchTask(Task):
    def __init__(self, show_id, season, episode, downCurQuality=False):
        super(FailedSearchTask, self).__init__(SearchTaskActions.FAILED_SEARCH.value, SearchTaskActions.FAILED_SEARCH)
        self.name = 'RETRY-{}'.format(show_id)
        self.show_id = show_id
        self.season = season
        self.episode = episode
        self.priority = TaskPriority.HIGH
        self.downCurQuality = downCurQuality
        self.success = False
        self.started = False
        self.auto_remove = False

    def run(self):
        self.started = True

        show_object = find_show(self.show_id)
        if not show_object:
            return

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
                snatch = all([(search_result.show_id, search_result.season, episode)
                              not in sickrage.app.search_queue.SNATCH_HISTORY for episode in search_result.episodes])

                if snatch:
                    [sickrage.app.search_queue.SNATCH_HISTORY.append((search_result.show_id, search_result.season, episode)) for episode in
                     search_result.episodes]

                    sickrage.app.log.info("Downloading " + search_result.name + " from " + search_result.provider.name)
                    snatch_episode(search_result)
        except Exception:
            sickrage.app.log.debug(traceback.format_exc())
        finally:
            sickrage.app.log.info("Finished failed download search for: [" + show_object.name + "]")
            sickrage.app.search_queue.MANUAL_SEARCH_HISTORY.append(self)
