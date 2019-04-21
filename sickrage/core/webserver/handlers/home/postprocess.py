#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#
#  This file is part of SiCKRAGE.
#
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
from abc import ABC

from tornado.web import authenticated

import sickrage
from sickrage.core.helpers import argToBool
from sickrage.core.webserver.handlers.base import BaseHandler


class HomePostProcessHandler(BaseHandler, ABC):
    @authenticated
    def get(self):
        return self.render(
            "/home/postprocess.mako",
            title=_('Post Processing'),
            header=_('Post Processing'),
            topmenu='home',
            controller='home',
            action='postprocess'
        )


class HomeProcessEpisodeHandler(BaseHandler, ABC):
    @authenticated
    async def post(self, *args, **kwargs):
        pp_options = {
            'proc_dir': self.get_body_argument('proc_dir'),
            'nzbname': self.get_body_argument('nzbname', ''),
            'process_method': self.get_body_argument('process_method'),
            'proc_type': self.get_body_argument('proc_type'),
            'force': argToBool(self.get_body_argument('force', 'false')),
            'is_priority': argToBool(self.get_body_argument('is_priority', 'false')),
            'delete_on': argToBool(self.get_body_argument('delete_on', 'false')),
            'force_next': argToBool(self.get_body_argument('force_next', 'false')),
            'failed': argToBool(self.get_body_argument('failed', 'false')),
            'quiet': argToBool(self.get_body_argument('quiet', 'false')),
        }

        proc_dir = pp_options.pop("proc_dir")
        quiet = pp_options.pop("quiet")

        if not proc_dir:
            return self.redirect("/home/postprocess/")

        result = await self.run_task(lambda: sickrage.app.postprocessor_queue.put(proc_dir, **pp_options))

        if quiet:
            return self.write(result)

        return self._genericMessage(_("Postprocessing results"), result.replace("\n", "<br>\n"))
