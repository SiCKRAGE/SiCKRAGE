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


import sickrage
from sickrage.core.common import Overview
from sickrage.core.common import Qualities, EpisodeStatus
from sickrage.core.enums import SearchFormat
from sickrage.core.webserver.handlers.api.v2 import ApiV2BaseHandler


class ApiV2ConfigHandler(ApiV2BaseHandler):
    def get(self, *args, **kwargs):
        config_data = sickrage.app.config.to_json()

        config_data['constants'] = {
            'episodeStatuses': [{
                'name': x.name,
                'displayName': x.display_name,
                'value': x.value
            } for x in EpisodeStatus],
            'overviewStrings': [{
                'name': x.name,
                'cssName': x.css_name
            } for x in Overview],
            'showSearchFormats': [{
                'name': x.name,
                'displayName': x.display_name,
                'value': x.value
            } for x in SearchFormat],
            'qualities': [{
                'name': x.name,
                'displayName': x.display_name,
                'cssName': x.css_name,
                'isPreset': x.is_preset,
                'value': x.value
            } for x in Qualities],
            'compositeStatuses': {
                'snatched': [x.name for x in EpisodeStatus.composites(EpisodeStatus.SNATCHED)],
                'downloaded': [x.name for x in EpisodeStatus.composites(EpisodeStatus.DOWNLOADED)]
            }
        }

        return self.json_response(config_data)
