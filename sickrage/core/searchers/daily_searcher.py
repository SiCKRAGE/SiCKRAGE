# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import datetime
import threading

import sickrage
from sickrage.core.common import Quality, Qualities, EpisodeStatus
from sickrage.core.queues.search import DailySearchTask
from sickrage.core.tv.show.helpers import get_show_list


class DailySearcher(object):
    def __init__(self):
        self.name = "DAILYSEARCHER"
        self.lock = threading.Lock()
        self.running = False

    def task(self, force=False):
        """
        Runs the daily searcher, queuing selected episodes for search
        :param force: Force search
        """
        if self.running and not force:
            return

        try:
            self.running = True

            # set thread name
            threading.currentThread().setName(self.name)

            # find new released episodes and update their statuses
            for curShow in get_show_list():
                if curShow.paused:
                    sickrage.app.log.debug("Skipping search for {} because the show is paused".format(curShow.name))
                    continue

                for tv_episode in curShow.new_episodes:
                    tv_episode.status = tv_episode.show.default_ep_status if tv_episode.season > 0 else EpisodeStatus.SKIPPED
                    tv_episode.save()
                    sickrage.app.log.info('Setting status ({status}) for show airing today: {name} {special}'.format(
                        name=tv_episode.pretty_name(),
                        status=tv_episode.status.display_name,
                        special='(specials are not supported)' if not tv_episode.season > 0 else '',
                    ))

                wanted = self._get_wanted(curShow, datetime.date.today())
                if not wanted:
                    sickrage.app.log.debug("Nothing needs to be downloaded for {}, skipping".format(curShow.name))
                    continue

                for season, episode in wanted:
                    if (curShow.series_id, season, episode) in sickrage.app.search_queue.SNATCH_HISTORY:
                        sickrage.app.search_queue.SNATCH_HISTORY.remove((curShow.series_id, season, episode))

                    sickrage.app.search_queue.put(DailySearchTask(curShow.series_id, curShow.series_provider_id, season, episode))
        finally:
            self.running = False

    @staticmethod
    def _get_wanted(show, from_date):
        """
        Get a list of episodes that we want to download
        :param show: Show these episodes are from
        :param fromDate: Search from a certain date
        :return: list of wanted episodes
        """

        wanted = []

        any_qualities, best_qualities = Quality.split_quality(show.quality)
        all_qualities = list(set(any_qualities + best_qualities))

        sickrage.app.log.debug("Seeing if we need anything for today from {}".format(show.name))

        # check through the list of statuses to see if we want any
        for episode_object in show.episodes:
            if not episode_object.season > 0 or not episode_object.airdate >= from_date:
                continue

            cur_status, cur_quality = Quality.split_composite_status(episode_object.status)

            # if we need a better one then say yes
            if cur_status not in (EpisodeStatus.WANTED, EpisodeStatus.DOWNLOADED, EpisodeStatus.SNATCHED, EpisodeStatus.SNATCHED_PROPER):
                continue

            if cur_status != EpisodeStatus.WANTED:
                if best_qualities:
                    if cur_quality in best_qualities:
                        continue
                    elif cur_quality != Qualities.UNKNOWN and cur_quality > max(best_qualities):
                        continue
                elif any_qualities:
                    if cur_quality in any_qualities:
                        continue
                    elif cur_quality != Qualities.UNKNOWN and cur_quality > max(any_qualities):
                        continue

            # skip upgrading quality of downloaded episodes if enabled
            if cur_status == EpisodeStatus.DOWNLOADED and show.skip_downloaded:
                continue

            wanted += [(episode_object.season, episode_object.episode)]

        return wanted
