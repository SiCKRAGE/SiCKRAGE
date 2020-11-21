# Author: Frank Fenton
# URL: https://sickrage.ca
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
import os
import threading
import traceback

import sickrage
from sickrage.core.common import EpisodeStatus
from sickrage.core.enums import TraktAddMethod, SeriesProviderID
from sickrage.core.exceptions import EpisodeNotFoundException
from sickrage.core.helpers import sanitize_file_name, make_dir, chmod_as_parent, flatten
from sickrage.core.queues.search import BacklogSearchTask
from sickrage.core.traktapi import TraktAPI
from sickrage.core.tv.show.helpers import find_show, get_show_list


def set_episode_to_wanted(show, s, e):
    """
    Sets an episode to wanted, only if it is currently skipped
    """
    try:
        epObj = show.get_episode(s, e)
        if epObj.status != EpisodeStatus.SKIPPED or not epObj.airdate > datetime.date.min:
            return

        sickrage.app.log.info("Setting episode %s S%02dE%02d to wanted" % (show.name, s, e))

        epObj.status = EpisodeStatus.WANTED
        epObj.save()

        sickrage.app.search_queue.put(BacklogSearchTask(show.series_id, show.series_provider_id, epObj.season, epObj.episode))

        sickrage.app.log.info("Starting backlog search for %s S%02dE%02d because some episodes were set to wanted" % (show.name, s, e))
    except EpisodeNotFoundException as e:
        pass


class TraktSearcher(object):
    def __init__(self):
        self.name = "TRAKTSEARCHER"

        self.todoBacklog = []
        self.todoWanted = []
        self.ShowWatchlist = {}
        self.EpisodeWatchlist = {}
        self.Collectionlist = {}
        self.running = False

    def task(self, force=False):
        if self.running or not sickrage.app.config.trakt.enable and not force:
            return

        try:
            self.running = True

            # set thread name
            threading.currentThread().setName(self.name)

            self.todoWanted = []  # its about to all get re-added
            if len(sickrage.app.config.general.root_dirs.split('|')) < 2:
                sickrage.app.log.warning("No default root directory")
                return

            # add shows from tv watchlist
            if sickrage.app.config.trakt.sync_watchlist:
                try:
                    self.sync_watchlist()
                except Exception:
                    sickrage.app.log.debug(traceback.format_exc())

            # add shows from tv collection
            if sickrage.app.config.trakt.sync:
                try:
                    self.sync_collection()
                except Exception:
                    sickrage.app.log.debug(traceback.format_exc())
        finally:
            self.running = False

    def sync_watchlist(self):
        sickrage.app.log.debug("Syncing SiCKRAGE with Trakt Watchlist")

        self.remove_show_from_sickrage()

        if self._get_show_watchlist():
            self.add_show_to_trakt_watch_list()
            self.update_shows()

        if self._get_episode_watchlist():
            self.add_episodes_to_trakt_watch_list()
            if sickrage.app.config.trakt.remove_show_from_sickrage:
                self.remove_episodes_from_trakt_watch_list()
            self.update_episodes()

    def sync_collection(self):
        sickrage.app.log.debug("Syncing SiCKRAGE with Trakt Collection")
        if self._get_show_collection():
            self.add_episodes_to_trakt_collection()
            if sickrage.app.config.trakt.sync_remove:
                self.remove_episodes_from_trakt_collection()

    def find_show_match(self, series_provider_id, series_id):
        trakt_show = None

        try:
            library = TraktAPI()["sync/collection"].shows() or {}
            if not library:
                sickrage.app.log.debug("No shows found in your library, aborting library update")
                return

            trakt_show = [x for __, x in library.items() if int(series_id) == int(x.ids[sickrage.app.series_providers[series_provider_id].trakt_id])]
        except Exception as e:
            sickrage.app.log.warning(f"Could not connect to Trakt service. Aborting library check. Error: {repr(e)}")

        return trakt_show

    def remove_show_from_trakt_library(self, show_obj):
        if self.find_show_match(show_obj.series_provider_id, show_obj.series_id):
            # URL parameters
            data = {
                'shows': [
                    {
                        'title': show_obj.name,
                        'year': show_obj.startyear,
                        'ids': {show_obj.series_provider.trakt_id: show_obj.series_id}
                    }
                ]
            }

            sickrage.app.log.debug(f"Removing {show_obj.name} from tv library")

            try:
                TraktAPI()["sync/collection"].remove(data)
            except Exception as e:
                sickrage.app.log.warning(f"Could not connect to Trakt service. Aborting removing show {show_obj.name} from Trakt library. Error: {repr(e)}")

    def add_show_to_trakt_library(self, show_obj):
        """
        Sends a request to trakt indicating that the given show and all its episodes is part of our library.

        show_obj: The TVShow object to add to trakt
        """
        data = {}

        if not self.find_show_match(show_obj.series_provider_id, show_obj.series_id):
            # URL parameters
            data = {
                'shows': [
                    {
                        'title': show_obj.name,
                        'year': show_obj.startyear,
                        'ids': {show_obj.series_provider.trakt_id: show_obj.series_id}
                    }
                ]
            }

        if len(data):
            sickrage.app.log.debug(f"Adding {show_obj.name} to tv library")

            try:
                TraktAPI()["sync/collection"].add(data)
            except Exception as e:
                sickrage.app.log.warning(f"Could not connect to Trakt service. Aborting adding show {show_obj.name} to Trakt library. Error: {repr(e)}")
                return

    def add_episodes_to_trakt_collection(self):
        trakt_data = []

        sickrage.app.log.debug("COLLECTION::SYNC::START - Look for Episodes to Add to Trakt Collection")

        for s in get_show_list():
            for e in s.episodes:
                trakt_id = s.series_provider.trakt_id
                if not self._check_in_list(trakt_id, str(e.series_id), e.season, e.episode, 'Collection'):
                    sickrage.app.log.debug(f"Adding Episode {s.name} S{e.season:02d}E{e.episode:02d} to collection")
                    trakt_data.append((e.series_id, s.series_provider_id, s.name, s.startyear, e.season, e.episode))

        if len(trakt_data):
            try:
                TraktAPI()["sync/collection"].add(self.trakt_bulk_data_generate(trakt_data))
                self._get_show_collection()
            except Exception as e:
                sickrage.app.log.warning(f"Could not connect to Trakt service. Error: {e}")

        sickrage.app.log.debug("COLLECTION::ADD::FINISH - Look for Episodes to Add to Trakt Collection")

    def remove_episodes_from_trakt_collection(self):
        trakt_data = []

        sickrage.app.log.debug(
            "COLLECTION::REMOVE::START - Look for Episodes to Remove From Trakt Collection")

        for s in get_show_list():
            for e in s.episodes:
                if e.location:
                    continue

                series_provider_trakt_id = s.series_provider.trakt_id
                if self._check_in_list(series_provider_trakt_id, str(e.series_id), e.season, e.episode, 'Collection'):
                    sickrage.app.log.debug(f"Removing Episode {s.name} S{e.season:02d}E{e.episode:02d} from collection")
                    trakt_data.append((e.series_id, s.series_provider_id, s.name, s.startyear, e.season, e.episode))

        if len(trakt_data):
            try:
                TraktAPI()["sync/collection"].remove(self.trakt_bulk_data_generate(trakt_data))
                self._get_show_collection()
            except Exception as e:
                sickrage.app.log.warning(f"Could not connect to Trakt service. Error: {e}")

        sickrage.app.log.debug(
            "COLLECTION::REMOVE::FINISH - Look for Episodes to Remove From Trakt Collection")

    def remove_episodes_from_trakt_watch_list(self):
        trakt_data = []

        sickrage.app.log.debug("WATCHLIST::REMOVE::START - Look for Episodes to Remove from Trakt Watchlist")

        for s in get_show_list():
            for e in s.episodes:
                series_provider_trakt_id = s.series_provider.trakt_id
                if self._check_in_list(series_provider_trakt_id, str(e.series_id), e.season, e.episode):
                    sickrage.app.log.debug(f"Removing Episode {s.name} S{e.season:02d}E{e.episode:02d} from watchlist")
                    trakt_data.append((e.series_id, s.series_provider_id, s.name, s.startyear, e.season, e.episode))

        if len(trakt_data):
            try:
                data = self.trakt_bulk_data_generate(trakt_data)
                TraktAPI()["sync/watchlist"].remove(data)
                self._get_episode_watchlist()
            except Exception as e:
                sickrage.app.log.warning(f"Could not connect to Trakt service. Error: {e}")

        sickrage.app.log.debug(
            "WATCHLIST::REMOVE::FINISH - Look for Episodes to Remove from Trakt Watchlist")

    def add_episodes_to_trakt_watch_list(self):
        trakt_data = []

        sickrage.app.log.debug("WATCHLIST::ADD::START - Look for Episodes to Add to Trakt Watchlist")

        for show_object in get_show_list():
            for episode_object in show_object.episodes:
                if episode_object.status in flatten(
                        [EpisodeStatus.composites(EpisodeStatus.SNATCHED), EpisodeStatus.composites(EpisodeStatus.SNATCHED_PROPER), EpisodeStatus.UNKNOWN,
                         EpisodeStatus.WANTED]):
                    continue

                trakt_id = show_object.series_provider.trakt_id
                if self._check_in_list(trakt_id, str(show_object.series_id), episode_object.season, episode_object.episode):
                    sickrage.app.log.debug(f"Adding Episode {show_object.name} S{episode_object.season:02d}E{episode_object.episode:02d} to watchlist")
                    trakt_data.append(
                        (show_object.series_id, show_object.series_provider_id, show_object.name, show_object.startyear, episode_object.season,
                         episode_object.episode))

        if len(trakt_data):
            try:
                data = self.trakt_bulk_data_generate(trakt_data)
                TraktAPI()["sync/watchlist"].add(data)
                self._get_episode_watchlist()
            except Exception as e:
                sickrage.app.log.warning(f"Could not connect to Trakt service. Error {e}")

        sickrage.app.log.debug("WATCHLIST::ADD::FINISH - Look for Episodes to Add to Trakt Watchlist")

    def add_show_to_trakt_watch_list(self):
        trakt_data = []

        sickrage.app.log.debug("SHOW_WATCHLIST::ADD::START - Look for Shows to Add to Trakt Watchlist")

        for show in get_show_list():
            series_provider_trakt_id = show.series_provider.trakt_id

            if not self._check_in_list(series_provider_trakt_id, str(show.series_id), 0, 0, 'Show'):
                sickrage.app.log.debug(f"Adding Show: Series Provider {series_provider_trakt_id} {str(show.series_id)} - {show.name} to Watchlist")

                show_el = {'title': show.name,
                           'year': show.startyear,
                           'ids': {series_provider_trakt_id: show.series_id}}

                trakt_data.append(show_el)

        if len(trakt_data):
            try:
                data = {'shows': trakt_data}
                TraktAPI()["sync/watchlist"].add(data)
                self._get_show_watchlist()
            except Exception as e:
                sickrage.app.log.warning(f"Could not connect to Trakt service. Error: {e}")

        sickrage.app.log.debug("SHOW_WATCHLIST::ADD::FINISH - Look for Shows to Add to Trakt Watchlist")

    def remove_show_from_sickrage(self):
        sickrage.app.log.debug("SHOW_SICKRAGE::REMOVE::START - Look for Shows to remove from SiCKRAGE")

        for show in get_show_list():
            if show.status == "Ended":
                try:
                    progress = TraktAPI()["shows"].get(show.imdb_id)
                except Exception as e:
                    sickrage.app.log.warning(
                        "Could not connect to Trakt service. Aborting removing show %s from SiCKRAGE. Error: %s" % (
                            show.name, repr(e)))
                    return

                if progress.status in ['canceled', 'ended']:
                    sickrage.app.show_queue.remove_show(show.series_id, show.series_provider_id, full=True)
                    sickrage.app.log.debug("Show: %s has been removed from SiCKRAGE" % show.name)

        sickrage.app.log.debug("SHOW_SICKRAGE::REMOVE::FINISH - Trakt Show Watchlist")

    def update_shows(self):
        sickrage.app.log.debug("SHOW_WATCHLIST::CHECK::START - Trakt Show Watchlist")

        if not len(self.ShowWatchlist):
            sickrage.app.log.debug("No shows found in your watchlist, aborting watchlist update")
            return

        for key, show in self.ShowWatchlist.items():
            # get traktID and series_provider_id values
            trakt_id, series_id = key

            series_provider_id = None
            for item in SeriesProviderID:
                if item.trakt_id == trakt_id:
                    series_provider_id = item

            if series_provider_id:
                if sickrage.app.config.trakt.method_add != TraktAddMethod.WHOLE_SHOW:
                    self.add_default_show(series_provider_id, series_id, show.title, EpisodeStatus.SKIPPED)
                else:
                    self.add_default_show(series_provider_id, series_id, show.title, EpisodeStatus.WANTED)

                if sickrage.app.config.trakt.method_add == TraktAddMethod.DOWNLOAD_PILOT_ONLY:
                    newShow = find_show(series_id, series_provider_id)

                    if newShow is not None:
                        set_episode_to_wanted(newShow, 1, 1)
                    else:
                        self.todoWanted.append((series_id, 1, 1))

        sickrage.app.log.debug("SHOW_WATCHLIST::CHECK::FINISH - Trakt Show Watchlist")

    def update_episodes(self):
        """
        Sets episodes to wanted that are in trakt watchlist
        """
        sickrage.app.log.debug("SHOW_WATCHLIST::CHECK::START - Trakt Episode Watchlist")

        if not len(self.EpisodeWatchlist):
            sickrage.app.log.debug("No episode found in your watchlist, aborting episode update")
            return

        managed_show = []

        for key, show in self.EpisodeWatchlist.items():
            # get traktID and series_provider_id values
            trakt_id, series_id = key

            series_provider_id = None
            for item in SeriesProviderID:
                if item.trakt_id == trakt_id:
                    series_provider_id = item

            if series_provider_id:
                show_object = find_show(series_id, series_provider_id)

                try:
                    if show_object is None:
                        if series_id not in managed_show:
                            self.add_default_show(series_provider_id, series_id, show.title, EpisodeStatus.SKIPPED)
                            managed_show.append(series_id)

                            for season_number, season in show.seasons.items():
                                for episode_number, _ in season.episodes.items():
                                    self.todoWanted.append((int(series_id), int(season_number), int(episode_number)))
                    else:
                        if show_object.series_provider_id == series_provider_id:
                            for season_number, season in show.seasons.items():
                                for episode_number, _ in season.episodes.items():
                                    set_episode_to_wanted(show_object, int(season_number), int(episode_number))
                except TypeError:
                    sickrage.app.log.debug(f"Could not parse the output from trakt for {show.title} ")

        sickrage.app.log.debug("SHOW_WATCHLIST::CHECK::FINISH - Trakt Episode Watchlist")

    @staticmethod
    def add_default_show(series_provider_id, series_id, name, status):
        """
        Adds a new show with the default settings
        """
        if not find_show(int(series_id), series_provider_id):
            sickrage.app.log.info("Adding show " + str(series_id))
            root_dirs = sickrage.app.config.general.root_dirs.split('|')

            try:
                location = root_dirs[int(root_dirs[0]) + 1]
            except Exception:
                location = None

            if location:
                showPath = os.path.join(location, sanitize_file_name(name))
                dir_exists = make_dir(showPath)

                if not dir_exists:
                    sickrage.app.log.warning("Unable to create the folder %s , can't add the show" % showPath)
                    return
                else:
                    chmod_as_parent(showPath)

                sickrage.app.show_queue.add_show(series_provider_id, int(series_id), showPath,
                                                 default_status=status,
                                                 quality=int(sickrage.app.config.general.quality_default),
                                                 flatten_folders=int(sickrage.app.config.general.flatten_folders_default),
                                                 paused=sickrage.app.config.trakt.start_paused,
                                                 default_status_after=status,
                                                 scene=sickrage.app.config.general.scene_default,
                                                 skip_downloaded=sickrage.app.config.general.skip_downloaded_default)
            else:
                sickrage.app.log.warning(
                    "There was an error creating the show, no root directory setting found")
                return

    def manage_new_show(self, show):
        sickrage.app.log.debug("Checking if trakt watch list wants to search for episodes from new show " + show.name)
        for episode in [i for i in self.todoWanted if i[0] == show.series_id]:
            self.todoWanted.remove(episode)
            set_episode_to_wanted(show, int(episode[1]), int(episode[2]))

    def _check_in_list(self, trakt_id, series_id, season, episode, List=None):
        """
         Check in the Watchlist or CollectionList for Show
         Is the Show, Season and Episode in the trakt_id list (tvdb / tvrage)
        """
        if "Collection" == List:
            try:
                if self.Collectionlist[trakt_id, series_id].seasons[int(season)].episodes[int(episode)]: return True
            except Exception:
                return False
        elif "Show" == List:
            try:
                if self.ShowWatchlist[trakt_id, series_id]: return True
            except Exception:
                return False
        else:
            try:
                if self.EpisodeWatchlist[trakt_id, series_id].seasons[int(season)].episodes[int(episode)]: return True
            except Exception:
                return False

    def _get_show_watchlist(self):
        """
        Get Watchlist and parse once into addressable structure
        """
        try:
            sickrage.app.log.debug("Getting Show Watchlist")
            self.ShowWatchlist = TraktAPI()["sync/watchlist"].shows() or {}
        except Exception as e:
            sickrage.app.log.warning(
                "Could not connect to trakt service, cannot download Show Watchlist: %s" % repr(e))
            return False
        return True

    def _get_episode_watchlist(self):
        """
         Get Watchlist and parse once into addressable structure
        """
        try:
            sickrage.app.log.debug("Getting Episode Watchlist")
            self.EpisodeWatchlist = TraktAPI()["sync/watchlist"].episodes() or {}
        except Exception as e:
            sickrage.app.log.warning(
                "Could not connect to trakt service, cannot download Episode Watchlist: %s" % repr(e))
            return False

        return True

    def _get_show_collection(self):
        """
        Get Collection and parse once into addressable structure
        """
        try:
            sickrage.app.log.debug("Getting Show Collection")
            self.Collectionlist = TraktAPI()["sync/collection"].shows() or {}
        except Exception as e:
            sickrage.app.log.warning(
                "Could not connect to trakt service, cannot download Show Collection: %s" % repr(e))
            return False

        return True

    @staticmethod
    def trakt_bulk_data_generate(data):
        """
        Build the JSON structure to send back to Trakt
        """
        show_list = []

        shows = {}
        seasons = {}

        for series_id, series_provider_id, show_name, startyear, season, episode in data:
            if series_id not in shows:
                shows[series_id] = {'title': show_name,
                                    'year': startyear,
                                    'ids': {sickrage.app.series_providers[series_provider_id].trakt_id: series_id}}

            if series_id not in seasons:
                seasons[series_id] = {}
            if season not in seasons[series_id]:
                seasons[series_id] = {season: []}
            if episode not in seasons[series_id][season]:
                seasons[series_id][season] += [{'number': episode}]

        for series_id, seasonlist in seasons.items():
            if 'seasons' not in shows[series_id]: shows[series_id]['seasons'] = []
            for season, episodelist in seasonlist.items():
                shows[series_id]['seasons'] += [{'number': season, 'episodes': episodelist}]

            show_list.append(shows[series_id])

        return {'shows': show_list}
