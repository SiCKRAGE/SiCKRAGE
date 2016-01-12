# Author: echel0n <sickrage.tv@gmail.com>
# URL: https://sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
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

from apscheduler.job import Job
from apscheduler.jobstores.base import ConflictingIdError, JobLookupError
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.tornado import TornadoScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.util import datetime_to_utc_timestamp
from dill import dill
from sqlalchemy.exc import IntegrityError

from sickrage.core.databases import dbFilename


class SRIntervalTrigger(IntervalTrigger):
    def __init__(self, weeks=0, days=0, hours=0, minutes=0, seconds=0, start_date=None, end_date=None, timezone=None,
                 **kwargs):
        min = kwargs.pop('min', 0)
        if min <= weeks + days + hours + minutes + seconds:
            super(SRIntervalTrigger, self).__init__(weeks, days, hours, minutes, seconds, start_date, end_date,
                                                    timezone)


class SRJobStore(SQLAlchemyJobStore):
    def __init__(self, *args, **kwargs):
        super(SRJobStore, self).__init__(*args, **kwargs)

    def add_job(self, job):
        insert = self.jobs_t.insert().values(**{
            'id': job.id,
            'next_run_time': datetime_to_utc_timestamp(job.next_run_time),
            'job_state': dill.dumps(job.__getstate__(), self.pickle_protocol)
        })
        try:
            self.engine.execute()
        except IntegrityError:
            raise ConflictingIdError(job.id)

    def update_job(self, job):
        update = self.jobs_t.update().values(**{
            'next_run_time': datetime_to_utc_timestamp(job.next_run_time),
            'job_state': dill.dumps(job.__getstate__(), self.pickle_protocol)
        }).where(self.jobs_t.c.id == job.id)
        result = self.engine.execute()
        if result.rowcount == 0:
            raise JobLookupError(id)

    def _reconstitute_job(self, job_state):
        job_state = dill.loads(job_state)
        job_state['jobstore'] = self
        job = Job.__new__(Job)
        job.__setstate__(job_state)
        job._scheduler = self._scheduler
        job._jobstore_alias = self._alias
        return job


class Scheduler(TornadoScheduler):
    def __init__(self, gconfig={}, **options):
        gconfig['jobstores'] = {'default': SRJobStore(url='sqlite:///{}'.format(dbFilename('scheduler.db')))}
        super(Scheduler, self).__init__(gconfig, **options)
