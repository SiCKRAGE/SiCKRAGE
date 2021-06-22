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
import datetime

from tornado.ioloop import IOLoop
from tornado.web import authenticated

import sickrage
from sickrage.core.webserver.handlers.base import BaseHandler


class ManageQueuesHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        return self.render('manage/queues.mako',
                           backlogSearchPaused=sickrage.app.search_queue.is_backlog_searcher_paused(),
                           dailySearchPaused=sickrage.app.search_queue.is_daily_searcher_paused(),
                           backlogSearchStatus=sickrage.app.search_queue.is_backlog_in_progress(),
                           dailySearchStatus=sickrage.app.search_queue.is_dailysearch_in_progress(),
                           findPropersStatus=sickrage.app.proper_searcher.running,
                           searchQueueLength=sickrage.app.search_queue.queue_length(),
                           postProcessorPaused=sickrage.app.postprocessor_queue.is_paused,
                           postProcessorRunning=sickrage.app.postprocessor_queue.is_busy,
                           postProcessorQueueLength=sickrage.app.postprocessor_queue.queue_length,
                           title=_('Manage Queues'),
                           header=_('Manage Queues'),
                           topmenu='manage',
                           controller='manage',
                           action='queues')


class ForceBacklogSearchHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        # force it to run the next time it looks
        sickrage.app.log.info("Backlog search forced")
        sickrage.app.alerts.message(_('Backlog search started'))

        job = sickrage.app.scheduler.get_job(sickrage.app.backlog_searcher.name)
        if job:
            job.modify(next_run_time=datetime.datetime.utcnow(), kwargs={'force': True})

        return self.redirect("/manage/manageQueues/")


class ForceDailySearchHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        # force it to run the next time it looks
        sickrage.app.log.info("Daily search forced")
        sickrage.app.alerts.message(_('Daily search started'))

        job = sickrage.app.scheduler.get_job(sickrage.app.daily_searcher.name)
        if job:
            job.modify(next_run_time=datetime.datetime.utcnow(), kwargs={'force': True})

        return self.redirect("/manage/manageQueues/")


class ForceFindPropersHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        # force it to run the next time it looks
        sickrage.app.log.info("Find propers search forced")
        sickrage.app.alerts.message(_('Find propers search started'))

        job = sickrage.app.scheduler.get_job(sickrage.app.proper_searcher.name)
        if job:
            job.modify(next_run_time=datetime.datetime.utcnow(), kwargs={'force': True})

        return self.redirect("/manage/manageQueues/")


class PauseDailySearcherHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        paused = self.get_argument('paused')

        if paused == "1":
            sickrage.app.search_queue.pause_daily_searcher()
        else:
            sickrage.app.search_queue.unpause_daily_searcher()

        return self.redirect("/manage/manageQueues/")


class PauseBacklogSearcherHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        paused = self.get_argument('paused')

        if paused == "1":
            sickrage.app.search_queue.pause_backlog_searcher()
        else:
            sickrage.app.search_queue.unpause_backlog_searcher()

        return self.redirect("/manage/manageQueues/")


class PausePostProcessorHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        paused = self.get_argument('paused')

        if paused == "1":
            sickrage.app.postprocessor_queue.pause()
        else:
            sickrage.app.postprocessor_queue.unpause()

        return self.redirect("/manage/manageQueues/")
