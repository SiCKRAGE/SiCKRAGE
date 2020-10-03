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
from abc import ABC

from tornado.escape import json_decode

import sickrage
from sickrage.core.queues.search import ManualSearchTask
from sickrage.core.tv.episode.helpers import find_epsiode
from sickrage.core.tv.show.helpers import find_show
from sickrage.core.webserver.handlers.api.v2 import APIv2BaseHandler
from sickrage.core.websocket import WebSocketMessage


class EpisodesManualSearchHandler(APIv2BaseHandler, ABC):
    def get(self, episode_id):
        use_existing_quality = self.get_argument('use_existing_quality')

        episode = find_epsiode(int(episode_id))
        if episode is None:
            return self.send_error(404, reason="Unable to find the specified episode: {}".format(episode_id))

        # make a queue item for it and put it on the queue
        ep_queue_item = ManualSearchTask(int(episode.show.indexer_id), int(episode.season), int(episode.episode), bool(use_existing_quality))

        sickrage.app.search_queue.put(ep_queue_item)
        if not all([ep_queue_item.started, ep_queue_item.success]):
            return self.write_json({'result': 'success'})

        return self.send_error(404, reason=_("Unable to find season {} episode {} for show {}".format(episode.season, episode.episode, episode.show.name)))


class EpisodesRenameHandler(APIv2BaseHandler, ABC):
    def get(self):
        series_id = self.get_argument('series_id', None)
        if not series_id:
            return self.send_error(400, reason="Missing series id")

        rename_data = []

        series = find_show(int(series_id))
        if series is None:
            return self.send_error(404, reason="Unable to find the specified series: {}".format(series_id))

        if not os.path.isdir(series.location):
            return self.send_error(400, reason="Can't rename episodes when the show location does not exist")

        for episode in series.episodes:
            if not episode.location:
                continue

            current_location = episode.location[len(episode.show.location) + 1:]
            new_location = "{}.{}".format(episode.proper_path(), current_location.split('.')[-1])

            if current_location != new_location:
                rename_data.append({
                    'episode_id': episode.indexer_id,
                    'season': episode.season,
                    'episode': episode.episode,
                    'current_location': current_location,
                    'new_location': new_location,
                })

        return self.write_json(rename_data)

    def post(self):
        data = json_decode(self.request.body)

        renamed_episodes = []

        series_id = data.get('series_id', None)
        if not series_id:
            return self.send_error(400, reason="Missing series id")

        series = find_show(int(series_id))
        if series is None:
            return self.send_error(404, reason="Unable to find the specified series: {}".format(series_id))

        if not os.path.isdir(series.location):
            return self.send_error(400, reason="Can't rename episodes when the show location does not exist")

        for episode_id in data.get('episode_id_list', []):
            episode = find_epsiode(episode_id)
            if episode:
                episode.rename()
                renamed_episodes.append(episode_id)

        if len(renamed_episodes) > 0:
            WebSocketMessage('SHOW_RENAMED', {'series_id': int(series_id)}).push()

        return self.write_json(renamed_episodes)
