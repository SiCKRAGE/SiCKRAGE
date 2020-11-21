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
from sickrage.core.tv.episode.helpers import find_episode_by_slug, find_episode
from sickrage.core.tv.show.helpers import find_show_by_slug
from sickrage.core.webserver.handlers.api.v2 import APIv2BaseHandler
from sickrage.core.websocket import WebSocketMessage


class EpisodesManualSearchHandler(APIv2BaseHandler, ABC):
    def get(self, episode_slug):
        use_existing_quality = self.get_argument('useExistingQuality')

        episode = find_episode_by_slug(episode_slug)
        if episode is None:
            return self.send_error(404, error=f"Unable to find the specified episode using slug: {episode_slug}")

        # make a queue item for it and put it on the queue
        ep_queue_item = ManualSearchTask(int(episode.show.series_id),
                                         episode.show.series_provider_id,
                                         int(episode.season),
                                         int(episode.episode),
                                         bool(use_existing_quality))

        sickrage.app.search_queue.put(ep_queue_item)
        if not all([ep_queue_item.started, ep_queue_item.success]):
            return self.write_json({'result': 'success'})

        return self.send_error(404, error=_("Unable to find season {} episode {} for show {}".format(episode.season, episode.episode, episode.show.name)))


class EpisodesRenameHandler(APIv2BaseHandler, ABC):
    def get(self):
        series_slug = self.get_argument('seriesSlug', None)
        if not series_slug:
            return self.send_error(400, error="Missing series slug")

        rename_data = []

        series = find_show_by_slug(series_slug)
        if series is None:
            return self.send_error(404, error=f"Unable to find the specified series using slug: {series_slug}")

        if not os.path.isdir(series.location):
            return self.send_error(400, error="Can't rename episodes when the show location does not exist")

        for episode in series.episodes:
            if not episode.location:
                continue

            current_location = episode.location[len(episode.show.location) + 1:]
            new_location = "{}.{}".format(episode.proper_path(), current_location.split('.')[-1])

            if current_location != new_location:
                rename_data.append({
                    'episodeId': episode.episode_id,
                    'season': episode.season,
                    'episode': episode.episode,
                    'currentLocation': current_location,
                    'newLocation': new_location,
                })

        return self.write_json(rename_data)

    def post(self):
        data = json_decode(self.request.body)

        renamed_episodes = []

        series_slug = data.get('seriesSlug', None)
        if not series_slug:
            return self.send_error(400, error="Missing series id")

        series = find_show_by_slug(series_slug)
        if series is None:
            return self.send_error(404, error=f"Unable to find the specified series using slug: {series_slug}")

        if not os.path.isdir(series.location):
            return self.send_error(400, error="Can't rename episodes when the show location does not exist")

        for episode_id in data.get('episodeIdList', []):
            episode = find_episode(episode_id, series.series_provider_id)
            if episode:
                episode.rename()
                renamed_episodes.append(episode.episode_id)

        if len(renamed_episodes) > 0:
            WebSocketMessage('SHOW_RENAMED', {'seriesSlug': series.slug}).push()

        return self.write_json(renamed_episodes)
