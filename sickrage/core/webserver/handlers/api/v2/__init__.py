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
import os

import sickrage
from sickrage.core.webserver.handlers.api import APIBaseHandler


class ApiV2RetrieveSeriesMetadataHandler(APIBaseHandler):
    def get(self):
        series_directory = self.get_argument('seriesDirectory', None)
        if not series_directory:
            return self.send_error(400, error="Missing seriesDirectory parameter")

        json_data = {
            'rootDirectory': os.path.dirname(series_directory),
            'seriesDirectory': series_directory,
            'seriesId': '',
            'seriesName': '',
            'seriesProviderSlug': '',
            'seriesSlug': ''
        }

        for cur_provider in sickrage.app.metadata_providers.values():
            series_id, series_name, series_provider_id = cur_provider.retrieve_show_metadata(series_directory)

            if not json_data['seriesId'] and series_id:
                json_data['seriesId'] = series_id

            if not json_data['seriesName'] and series_name:
                json_data['seriesName'] = series_name

            if not json_data['seriesProviderSlug'] and series_provider_id:
                json_data['seriesProviderSlug'] = series_provider_id.slug

            if not json_data['seriesSlug'] and series_id and series_provider_id:
                json_data['seriesSlug'] = f'{series_id}-{series_provider_id.slug}'

        self.write_json(json_data)
