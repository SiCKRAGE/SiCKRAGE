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

import sickrage
from sickrage.core.tv.show.coming_episodes import ComingEpisodes
from sickrage.core.webserver.handlers.api import APIBaseHandler


class ApiV2ScheduleHandler(APIBaseHandler):
    def get(self):
        """Get TV show schedule information"
        ---
        tags: [Schedule]
        summary: Get TV show schedule information
        description: Get TV show schedule information
        responses:
          200:
            description: Success payload
            content:
              application/json:
                schema:
                  ScheduleSuccessSchema
          400:
            description: Bad request; Check `errors` for any validation errors
            content:
              application/json:
                schema:
                  BadRequestSchema
          401:
            description: Returned if your JWT token is missing or expired
            content:
              application/json:
                schema:
                  NotAuthorizedSchema
          404:
            description: Returned if the given series slug does not exist or no series results.
            content:
              application/json:
                schema:
                  NotFoundSchema
        """

        next_week = datetime.datetime.combine(datetime.date.today() + datetime.timedelta(days=7),
                                              datetime.datetime.now().time().replace(tzinfo=sickrage.app.tz))

        today = datetime.datetime.now().replace(tzinfo=sickrage.app.tz)

        results = ComingEpisodes.get_coming_episodes(ComingEpisodes.categories, sickrage.app.config.gui.coming_eps_sort, group=False)

        for i, result in enumerate(results.copy()):
            results[i]['airdate'] = datetime.datetime.fromordinal(result['airdate'].toordinal()).timestamp()
            results[i]['series_provider_id'] = result['series_provider_id'].name
            results[i]['quality'] = result['quality'].name
            results[i]['localtime'] = result['localtime'].timestamp()

        return self.write_json({'episodes': results, 'today': today.timestamp(), 'nextWeek': next_week.timestamp()})
