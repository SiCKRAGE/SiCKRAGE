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
import os

import sickrage
from sickrage.core import Quality
from sickrage.core.common import dateTimeFormat
from sickrage.core.helpers import convert_dict_keys_to_camelcase
from sickrage.core.tv.show.history import History
from sickrage.core.webserver.handlers.api.v2 import ApiV2BaseHandler


class ApiV2HistoryHandler(ApiV2BaseHandler):
    def get(self):
        """Get snatch and download history"
        ---
        tags: [History]
        summary: Get snatch and download history
        description: Get snatch and download history
        responses:
          200:
            description: Success payload
            content:
              application/json:
                schema:
                  HistorySuccessSchema
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

        limit = int(self.get_argument('limit', sickrage.app.config.gui.history_limit or 100))

        results = []

        for row in History().get(limit):
            status, quality = Quality.split_composite_status(int(row["action"]))

            # if self.type and not status.lower() == self.type:
            #     continue

            row["status"] = status.display_name
            row["quality"] = quality.name
            row["date"] = datetime.datetime.fromordinal(row["date"].toordinal()).timestamp()

            del row["action"]

            row["series_id"] = row.pop("series_id")
            row['series_provider_id'] = row['series_provider_id'].name
            row["resource_path"] = os.path.dirname(row["resource"])
            row["resource"] = os.path.basename(row["resource"])

            row = convert_dict_keys_to_camelcase(row)

            results.append(row)

        return self.json_response(results)
