
# Author: Frank Fenton
# URL: http://github.com/SiCKRAGETV/SickRage/
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

import os
import traceback

from datetime import date

import sickrage
from core.common import Quality
from core.common import SKIPPED, WANTED, ARCHIVED, UNKNOWN
from core.databases import main_db
from core.helpers import findCertainShow, sanitizeFileName, makeDir, chmodAsParent
from core.queues.search import BacklogQueueItem
from core.trakt import TraktAPI, traktException



def setEpisodeToWanted(show, s, e):
    """
    Sets an episode to wanted, only if it is currently skipped
    """
    epObj = show.getEpisode(int(s), int(e))
    if epObj:
        with epObj.lock:
            if epObj.status != SKIPPED or epObj.airdate == date.fromordinal(1):
                return

            sickrage.srLogger.info("Setting episode %s S%02dE%02d to wanted" % (show.name, s, e))
            # figure out what segment the episode is in and remember it so we can backlog it

            epObj.status = WANTED
            epObj.saveToDB()

        sickrage.srCore.SEARCHQUEUE.add_item(BacklogQueueItem(show, [epObj]))

        # cleanup
        del epObj

        sickrage.srLogger.info(
                "Starting backlog search for %s S%02dE%02d because some episodes were set to wanted" % (
                    show.name, s, e))


class srTraktSearcher(object):
    def __init__(self, *args, **kwargs):
        self.name = "TRAKTSEARCHER"
        self.trakt_api = TraktAPI(sickrage.srConfig.SSL_VERIFY, sickrage.srConfig.TRAKT_TIMEOUT)
        self.todoBacklog = []
        self.todoWanted = []
        self.ShowWatchlist = {}
        self.EpisodeWatchlist = {}
        self.Collectionlist = {}
        self.amActive = False

    def run(self, force=False):
        if self.amActive:
            return

        self.amActive = True

        # add shows from tv watchlist
        if sickrage.srConfig.TRAKT_SYNC_WATCHLIST:
            self.todoWanted = []  # its about to all get re-added
            if len(sickrage.srConfig.ROOT_DIRS.split('|')) < 2:
                sickrage.srLogger.warning("No default root directory")
                return

            try:
                self.syncWatchlist()
            except Exception:
                sickrage.srLogger.debug(traceback.format_exc())

            try:
                # sync tv library with sickrage library
                self.syncLibrary()
            except Exception:
                sickrage.srLogger.debug(traceback.format_exc())

        self.amActive = False

    def findShow(self, indexer, indexerid):
        traktShow = None

        try:
            library = self.trakt_api.traktRequest("sync/collection/shows") or []

            if not library:
                sickrage.srLogger.warning("Could not connect to trakt service, aborting library check")
                return

            if not len(library):
                sickrage.srLogger.debug("No shows found in your library, aborting library update")
                return

            traktShow = [x for x in library if
                         int(indexerid) in [int(x[b'show'][b'ids'][b'tvdb'] or 0),
                                            int(x[b'show'][b'ids'][b'tvrage'] or 0)]]
        except traktException as e:
            sickrage.srLogger.warning("Could not connect to Trakt service. Aborting library check. Error: %s" % repr(e))

        return traktShow

    def removeShowFromTraktLibrary(self, show_obj):
        if self.findShow(show_obj.indexer, show_obj.indexerid):
            trakt_id = sickrage.srCore.INDEXER_API(show_obj.indexer).config[b'trakt_id']

            # URL parameters
            data = {
                'shows': [
                    {
                        'title': show_obj.name,
                        'year': show_obj.startyear,
                        'ids': {}
                    }
                ]
            }

            if trakt_id == 'tvdb_id':
                data[b'shows'][0][b'ids'][b'tvdb'] = show_obj.indexerid
            else:
                data[b'shows'][0][b'ids'][b'tvrage'] = show_obj.indexerid

            sickrage.srLogger.debug("Removing %s from tv library" % show_obj.name)

            try:
                self.trakt_api.traktRequest("sync/collection/remove", data, method='POST')
            except traktException as e:
                sickrage.srLogger.warning(
                        "Could not connect to Trakt service. Aborting removing show %s from Trakt library. Error: %s" % (
                            show_obj.name, repr(e)))

    def addShowToTraktLibrary(self, show_obj):
        """
        Sends a request to trakt indicating that the given show and all its episodes is part of our library.

        show_obj: The TVShow object to add to trakt
        """
        data = {}

        if not self.findShow(show_obj.indexer, show_obj.indexerid):
            trakt_id = sickrage.srCore.INDEXER_API(show_obj.indexer).config[b'trakt_id']
            # URL parameters
            data = {
                'shows': [
                    {
                        'title': show_obj.name,
                        'year': show_obj.startyear,
                        'ids': {}
                    }
                ]
            }

            if trakt_id == 'tvdb_id':
                data[b'shows'][0][b'ids'][b'tvdb'] = show_obj.indexerid
            else:
                data[b'shows'][0][b'ids'][b'tvrage'] = show_obj.indexerid

        if len(data):
            sickrage.srLogger.debug("Adding %s to tv library" % show_obj.name)

            try:
                self.trakt_api.traktRequest("sync/collection", data, method='POST')
            except traktException as e:
                sickrage.srLogger.warning(
                        "Could not connect to Trakt service. Aborting adding show %s to Trakt library. Error: %s" % (
                            show_obj.name, repr(e)))
                return

    def syncLibrary(self):
        if sickrage.srConfig.TRAKT_SYNC and sickrage.srConfig.USE_TRAKT:
            sickrage.srLogger.debug("Sync SiCKRAGE with Trakt Collection")

            if self._getShowCollection():
                self.addEpisodeToTraktCollection()
                if sickrage.srConfig.TRAKT_SYNC_REMOVE:
                    self.removeEpisodeFromTraktCollection()

    def removeEpisodeFromTraktCollection(self):
        if sickrage.srConfig.TRAKT_SYNC_REMOVE and sickrage.srConfig.TRAKT_SYNC and sickrage.srConfig.USE_TRAKT:
            sickrage.srLogger.debug("COLLECTION::REMOVE::START - Look for Episodes to Remove From Trakt Collection")

            sql_selection = 'SELECT tv_shows.indexer, tv_shows.startyear, showid, show_name, season, episode, tv_episodes.status, tv_episodes.location FROM tv_episodes,tv_shows WHERE tv_shows.indexer_id = tv_episodes.showid'
            episodes = main_db.MainDB().select(sql_selection)

            if episodes is not None:
                trakt_data = []

                for cur_episode in episodes:
                    trakt_id = sickrage.srCore.INDEXER_API(cur_episode[b"indexer"]).config[b'trakt_id']

                    if self._checkInList(trakt_id, str(cur_episode[b"showid"]), str(cur_episode[b"season"]),
                                         str(cur_episode[b"episode"]), List='Collection'):
                        if cur_episode[b"location"] == '':
                            sickrage.srLogger.debug("Removing Episode %s S%02dE%02d from collection" %
                                                     (cur_episode[b"show_name"], cur_episode[b"season"], cur_episode[b"episode"]))
                            trakt_data.append(
                                    (cur_episode[b"showid"], cur_episode[b"indexer"], cur_episode[b"show_name"],
                                     cur_episode[b"startyear"], cur_episode[b"season"], cur_episode[b"episode"]))

                if len(trakt_data):
                    try:
                        data = self.trakt_bulk_data_generate(trakt_data)
                        self.trakt_api.traktRequest("sync/collection/remove", data, method='POST')
                        self._getShowCollection()
                    except traktException as e:
                        sickrage.srLogger.warning("Could not connect to Trakt service. Error: %s" % e)

            sickrage.srLogger.debug("COLLECTION::REMOVE::FINISH - Look for Episodes to Remove From Trakt Collection")

    def addEpisodeToTraktCollection(self):
        if sickrage.srConfig.TRAKT_SYNC and sickrage.srConfig.USE_TRAKT:
            sickrage.srLogger.debug("COLLECTION::ADD::START - Look for Episodes to Add to Trakt Collection")

            sql_selection = 'SELECT tv_shows.indexer, tv_shows.startyear, showid, show_name, season, episode FROM tv_episodes,tv_shows WHERE tv_shows.indexer_id = tv_episodes.showid AND tv_episodes.status IN (' + ','.join(
                    [str(x) for x in Quality.DOWNLOADED + [ARCHIVED]]) + ')'
            episodes = main_db.MainDB().select(sql_selection)

            if episodes is not None:
                trakt_data = []

                for cur_episode in episodes:
                    trakt_id = sickrage.srCore.INDEXER_API(cur_episode[b"indexer"]).config[b'trakt_id']

                    if not self._checkInList(trakt_id, str(cur_episode[b"showid"]), str(cur_episode[b"season"]),
                                             str(cur_episode[b"episode"]), List='Collection'):
                        sickrage.srLogger.debug("Adding Episode %s S%02dE%02d to collection" %
                                                 (cur_episode[b"show_name"], cur_episode[b"season"], cur_episode[b"episode"]))
                        trakt_data.append((cur_episode[b"showid"], cur_episode[b"indexer"], cur_episode[b"show_name"],
                                           cur_episode[b"startyear"], cur_episode[b"season"], cur_episode[b"episode"]))

                if len(trakt_data):
                    try:
                        data = self.trakt_bulk_data_generate(trakt_data)
                        self.trakt_api.traktRequest("sync/collection", data, method='POST')
                        self._getShowCollection()
                    except traktException as e:
                        sickrage.srLogger.warning("Could not connect to Trakt service. Error: %s" % e)

            sickrage.srLogger.debug("COLLECTION::ADD::FINISH - Look for Episodes to Add to Trakt Collection")

    def syncWatchlist(self):
        if sickrage.srConfig.TRAKT_SYNC_WATCHLIST and sickrage.srConfig.USE_TRAKT:
            sickrage.srLogger.debug("Sync SiCKRAGE with Trakt Watchlist")

            self.removeShowFromSickRage()

            if self._getShowWatchlist():
                self.addShowToTraktWatchList()
                self.updateShows()

            if self._getEpisodeWatchlist():
                self.removeEpisodeFromTraktWatchList()
                self.addEpisodeToTraktWatchList()
                self.updateEpisodes()

    def removeEpisodeFromTraktWatchList(self):
        if sickrage.srConfig.TRAKT_SYNC_WATCHLIST and sickrage.srConfig.USE_TRAKT:
            sickrage.srLogger.debug("WATCHLIST::REMOVE::START - Look for Episodes to Remove from Trakt Watchlist")

            sql_selection = 'SELECT tv_shows.indexer, tv_shows.startyear, showid, show_name, season, episode, tv_episodes.status FROM tv_episodes,tv_shows WHERE tv_shows.indexer_id = tv_episodes.showid'
            episodes = main_db.MainDB().select(sql_selection)

            if episodes is not None:
                trakt_data = []

                for cur_episode in episodes:
                    trakt_id = sickrage.srCore.INDEXER_API(cur_episode[b"indexer"]).config[b'trakt_id']

                    if self._checkInList(trakt_id, str(cur_episode[b"showid"]), str(cur_episode[b"season"]),
                                         str(cur_episode[b"episode"])) and cur_episode[
                        b"status"] not in Quality.SNATCHED + Quality.SNATCHED_PROPER + [UNKNOWN] + [WANTED]:
                        sickrage.srLogger.debug("Removing Episode %s S%02dE%02d from watchlist" %
                                                 (cur_episode[b"show_name"], cur_episode[b"season"], cur_episode[b"episode"]))
                        trakt_data.append((cur_episode[b"showid"], cur_episode[b"indexer"], cur_episode[b"show_name"],
                                           cur_episode[b"startyear"], cur_episode[b"season"], cur_episode[b"episode"]))

                if len(trakt_data):
                    try:
                        data = self.trakt_bulk_data_generate(trakt_data)
                        self.trakt_api.traktRequest("sync/watchlist/remove", data, method='POST')
                        self._getEpisodeWatchlist()
                    except traktException as e:
                        sickrage.srLogger.warning("Could not connect to Trakt service. Error: %s" % e)

                sickrage.srLogger.debug("WATCHLIST::REMOVE::FINISH - Look for Episodes to Remove from Trakt Watchlist")

    def addEpisodeToTraktWatchList(self):
        if sickrage.srConfig.TRAKT_SYNC_WATCHLIST and sickrage.srConfig.USE_TRAKT:
            sickrage.srLogger.debug("WATCHLIST::ADD::START - Look for Episodes to Add to Trakt Watchlist")

            sql_selection = 'SELECT tv_shows.indexer, tv_shows.startyear, showid, show_name, season, episode FROM tv_episodes,tv_shows WHERE tv_shows.indexer_id = tv_episodes.showid AND tv_episodes.status IN (' + ','.join(
                    [str(x) for x in Quality.SNATCHED + Quality.SNATCHED_PROPER + [WANTED]]) + ')'
            episodes = main_db.MainDB().select(sql_selection)

            if episodes is not None:
                trakt_data = []

                for cur_episode in episodes:
                    trakt_id = sickrage.srCore.INDEXER_API(cur_episode[b"indexer"]).config[b'trakt_id']

                    if not self._checkInList(trakt_id, str(cur_episode[b"showid"]), str(cur_episode[b"season"]),
                                             str(cur_episode[b"episode"])):
                        sickrage.srLogger.debug("Adding Episode %s S%02dE%02d to watchlist" %
                                                 (cur_episode[b"show_name"], cur_episode[b"season"], cur_episode[b"episode"]))
                        trakt_data.append((cur_episode[b"showid"], cur_episode[b"indexer"], cur_episode[b"show_name"],
                                           cur_episode[b"startyear"], cur_episode[b"season"],
                                           cur_episode[b"episode"]))

                if len(trakt_data):
                    try:
                        data = self.trakt_bulk_data_generate(trakt_data)
                        self.trakt_api.traktRequest("sync/watchlist", data, method='POST')
                        self._getEpisodeWatchlist()
                    except traktException as e:
                        sickrage.srLogger.warning("Could not connect to Trakt service. Error %s" % e)

            sickrage.srLogger.debug("WATCHLIST::ADD::FINISH - Look for Episodes to Add to Trakt Watchlist")

    def addShowToTraktWatchList(self):
        if sickrage.srConfig.TRAKT_SYNC_WATCHLIST and sickrage.srConfig.USE_TRAKT:
            sickrage.srLogger.debug("SHOW_WATCHLIST::ADD::START - Look for Shows to Add to Trakt Watchlist")

            if sickrage.srCore.SHOWLIST is not None:
                trakt_data = []

                for show in sickrage.srCore.SHOWLIST:
                    trakt_id = sickrage.srCore.INDEXER_API(show.indexer).config[b'trakt_id']

                    if not self._checkInList(trakt_id, str(show.indexerid), '0', '0', List='Show'):
                        sickrage.srLogger.debug(
                                "Adding Show: Indexer %s %s - %s to Watchlist" % (
                                    trakt_id, str(show.indexerid), show.name))
                        show_el = {'title': show.name, 'year': show.startyear, 'ids': {}}
                        if trakt_id == 'tvdb_id':
                            show_el[b'ids'][b'tvdb'] = show.indexerid
                        else:
                            show_el[b'ids'][b'tvrage'] = show.indexerid
                        trakt_data.append(show_el)

                if len(trakt_data):
                    try:
                        data = {'shows': trakt_data}
                        self.trakt_api.traktRequest("sync/watchlist", data, method='POST')
                        self._getShowWatchlist()
                    except traktException as e:
                        sickrage.srLogger.warning("Could not connect to Trakt service. Error: %s" % e)

            sickrage.srLogger.debug("SHOW_WATCHLIST::ADD::FINISH - Look for Shows to Add to Trakt Watchlist")

    def removeShowFromSickRage(self):
        if sickrage.srConfig.TRAKT_SYNC_WATCHLIST and sickrage.srConfig.USE_TRAKT and sickrage.srConfig.TRAKT_REMOVE_SHOW_FROM_SICKRAGE:
            sickrage.srLogger.debug("SHOW_SICKRAGE::REMOVE::START - Look for Shows to remove from SiCKRAGE")

            if sickrage.srCore.SHOWLIST:
                for show in sickrage.srCore.SHOWLIST:
                    if show.status == "Ended":
                        try:
                            progress = self.trakt_api.traktRequest("shows/" + show.imdbid + "/progress/watched") or {}
                        except traktException as e:
                            sickrage.srLogger.warning(
                                    "Could not connect to Trakt service. Aborting removing show %s from SiCKRAGE. Error: %s" % (
                                        show.name, repr(e)))
                            return

                        if 'aired' in progress and 'completed' in progress and progress[b'aired'] == progress[
                            b'completed']:
                            sickrage.srCore.SHOWQUEUE.removeShow(show, full=True)
                            sickrage.srLogger.debug("Show: %s has been removed from SiCKRAGE" % show.name)

            sickrage.srLogger.debug("SHOW_SICKRAGE::REMOVE::FINISH - Trakt Show Watchlist")

    def updateShows(self):
        sickrage.srLogger.debug("SHOW_WATCHLIST::CHECK::START - Trakt Show Watchlist")

        if not len(self.ShowWatchlist):
            sickrage.srLogger.debug("No shows found in your watchlist, aborting watchlist update")
            return

        indexer = int(sickrage.srConfig.TRAKT_DEFAULT_INDEXER)
        trakt_id = sickrage.srCore.INDEXER_API(indexer).config[b'trakt_id']

        for show_el in self.ShowWatchlist[trakt_id]:
            indexer_id = int(str(show_el))
            show = self.ShowWatchlist[trakt_id][show_el]

            # LOGGER.debug(u"Checking Show: %s %s %s" % (trakt_id, indexer_id, show[b'title']))
            if int(sickrage.srConfig.TRAKT_METHOD_ADD) != 2:
                self.addDefaultShow(indexer, indexer_id, show[b'title'], SKIPPED)
            else:
                self.addDefaultShow(indexer, indexer_id, show[b'title'], WANTED)

            if int(sickrage.srConfig.TRAKT_METHOD_ADD) == 1:
                newShow = findCertainShow(sickrage.srCore.SHOWLIST, indexer_id)

                if newShow is not None:
                    setEpisodeToWanted(newShow, 1, 1)
                else:
                    self.todoWanted.append((indexer_id, 1, 1))
        sickrage.srLogger.debug("SHOW_WATCHLIST::CHECK::FINISH - Trakt Show Watchlist")

    def updateEpisodes(self):
        """
        Sets episodes to wanted that are in trakt watchlist
        """
        sickrage.srLogger.debug("SHOW_WATCHLIST::CHECK::START - Trakt Episode Watchlist")

        if not len(self.EpisodeWatchlist):
            sickrage.srLogger.debug("No episode found in your watchlist, aborting episode update")
            return

        managed_show = []

        indexer = int(sickrage.srConfig.TRAKT_DEFAULT_INDEXER)
        trakt_id = sickrage.srCore.INDEXER_API(indexer).config[b'trakt_id']

        for show_el in self.EpisodeWatchlist[trakt_id]:
            indexer_id = int(show_el)
            show = self.EpisodeWatchlist[trakt_id][show_el]

            newShow = findCertainShow(sickrage.srCore.SHOWLIST, indexer_id)

            try:
                if newShow is None:
                    if indexer_id not in managed_show:
                        self.addDefaultShow(indexer, indexer_id, show[b'title'], SKIPPED)
                        managed_show.append(indexer_id)

                        for season_el in show[b'seasons']:
                            season = int(season_el)

                            for episode_el in show[b'seasons'][season_el][b'episodes']:
                                self.todoWanted.append((indexer_id, season, int(episode_el)))
                else:
                    if newShow.indexer == indexer:
                        for season_el in show[b'seasons']:
                            season = int(season_el)

                            for episode_el in show[b'seasons'][season_el][b'episodes']:
                                setEpisodeToWanted(newShow, season, int(episode_el))
            except TypeError:
                sickrage.srLogger.debug("Could not parse the output from trakt for %s " % show[b"title"])
        sickrage.srLogger.debug("SHOW_WATCHLIST::CHECK::FINISH - Trakt Episode Watchlist")

    @staticmethod
    def addDefaultShow(indexer, indexer_id, name, status):
        """
        Adds a new show with the default settings
        """
        if not findCertainShow(sickrage.srCore.SHOWLIST, int(indexer_id)):
            sickrage.srLogger.info("Adding show " + str(indexer_id))
            root_dirs = sickrage.srConfig.ROOT_DIRS.split('|')

            try:
                location = root_dirs[int(root_dirs[0]) + 1]
            except Exception:
                location = None

            if location:
                showPath = os.path.join(location, sanitizeFileName(name))
                dir_exists = makeDir(showPath)

                if not dir_exists:
                    sickrage.srLogger.warning("Unable to create the folder %s , can't add the show" % showPath)
                    return
                else:
                    chmodAsParent(showPath)

                sickrage.srCore.SHOWQUEUE.addShow(int(indexer), int(indexer_id), showPath,
                                              default_status=status,
                                              quality=int(sickrage.srConfig.QUALITY_DEFAULT),
                                              flatten_folders=int(sickrage.srConfig.FLATTEN_FOLDERS_DEFAULT),
                                              paused=sickrage.srConfig.TRAKT_START_PAUSED,
                                              default_status_after=status,
                                              archive=sickrage.srConfig.ARCHIVE_DEFAULT)
            else:
                sickrage.srLogger.warning("There was an error creating the show, no root directory setting found")
                return

    def manageNewShow(self, show):
        sickrage.srLogger.debug("Checking if trakt watch list wants to search for episodes from new show " + show.name)
        episodes = [i for i in self.todoWanted if i[0] == show.indexerid]

        for episode in episodes:
            self.todoWanted.remove(episode)
            setEpisodeToWanted(show, episode[1], episode[2])

    def _checkInList(self, trakt_id, showid, season, episode, List=None):
        """
         Check in the Watchlist or CollectionList for Show
         Is the Show, Season and Episode in the trakt_id list (tvdb / tvrage)
        """
        # LOGGER.debug(u"Checking Show: %s %s %s " % (trakt_id, showid, List))

        if "Collection" == List:
            try:
                if self.Collectionlist[trakt_id][showid][b'seasons'][season][b'episodes'][episode] == episode:
                    return True
            except Exception:
                return False
        elif "Show" == List:
            try:
                if self.ShowWatchlist[trakt_id][showid][b'id'] == showid:
                    return True
            except Exception:
                return False
        else:
            try:
                if self.EpisodeWatchlist[trakt_id][showid][b'seasons'][season][b'episodes'][episode] == episode:
                    return True
            except Exception:
                return False

    def _getShowWatchlist(self):
        """
        Get Watchlist and parse once into addressable structure
        """
        try:
            self.ShowWatchlist = {'tvdb_id': {}, 'tvrage_id': {}}
            TraktShowWatchlist = self.trakt_api.traktRequest("sync/watchlist/shows")
            tvdb_id = 'tvdb'
            tvrage_id = 'tvrage'

            for watchlist_el in TraktShowWatchlist:
                tvdb = False
                tvrage = False

                if not watchlist_el[b'show'][b'ids'][b"tvdb"] is None:
                    tvdb = True

                if not watchlist_el[b'show'][b'ids'][b"tvrage"] is None:
                    tvrage = True

                title = watchlist_el[b'show'][b'title']
                year = str(watchlist_el[b'show'][b'year'])

                if tvdb:
                    showid = str(watchlist_el[b'show'][b'ids'][tvdb_id])
                    self.ShowWatchlist[tvdb_id + '_id'][showid] = {'id': showid, 'title': title, 'year': year}

                if tvrage:
                    showid = str(watchlist_el[b'show'][b'ids'][tvrage_id])
                    self.ShowWatchlist[tvrage_id + '_id'][showid] = {'id': showid, 'title': title, 'year': year}
        except traktException as e:
            sickrage.srLogger.warning("Could not connect to trakt service, cannot download Show Watchlist: %s" % repr(e))
            return False
        return True

    def _getEpisodeWatchlist(self):
        """
         Get Watchlist and parse once into addressable structure
        """
        try:
            self.EpisodeWatchlist = {'tvdb_id': {}, 'tvrage_id': {}}
            TraktEpisodeWatchlist = self.trakt_api.traktRequest("sync/watchlist/episodes")
            tvdb_id = 'tvdb'
            tvrage_id = 'tvrage'

            for watchlist_el in TraktEpisodeWatchlist:
                tvdb = False
                tvrage = False

                if not watchlist_el[b'show'][b'ids'][b"tvdb"] is None:
                    tvdb = True

                if not watchlist_el[b'show'][b'ids'][b"tvrage"] is None:
                    tvrage = True

                title = watchlist_el[b'show'][b'title']
                year = str(watchlist_el[b'show'][b'year'])
                season = str(watchlist_el[b'episode'][b'season'])
                episode = str(watchlist_el[b'episode'][b'number'])

                if tvdb:
                    showid = str(watchlist_el[b'show'][b'ids'][tvdb_id])

                    if showid not in self.EpisodeWatchlist[tvdb_id + '_id'].keys():
                        self.EpisodeWatchlist[tvdb_id + '_id'][showid] = {'id': showid, 'title': title, 'year': year,
                                                                          'seasons': {}}

                    if season not in self.EpisodeWatchlist[tvdb_id + '_id'][showid][b'seasons'].keys():
                        self.EpisodeWatchlist[tvdb_id + '_id'][showid][b'seasons'][season] = {'s': season,
                                                                                              'episodes': {}}

                    if episode not in self.EpisodeWatchlist[tvdb_id + '_id'][showid][b'seasons'][season][
                        'episodes'].keys():
                        self.EpisodeWatchlist[tvdb_id + '_id'][showid][b'seasons'][season][b'episodes'][
                            episode] = episode

                if tvrage:
                    showid = str(watchlist_el[b'show'][b'ids'][tvrage_id])

                    if showid not in self.EpisodeWatchlist[tvrage_id + '_id'].keys():
                        self.EpisodeWatchlist[tvrage_id + '_id'][showid] = {'id': showid, 'title': title, 'year': year,
                                                                            'seasons': {}}

                    if season not in self.EpisodeWatchlist[tvrage_id + '_id'][showid][b'seasons'].keys():
                        self.EpisodeWatchlist[tvrage_id + '_id'][showid][b'seasons'][season] = {'s': season,
                                                                                                'episodes': {}}

                    if episode not in self.EpisodeWatchlist[tvrage_id + '_id'][showid][b'seasons'][season][
                        'episodes'].keys():
                        self.EpisodeWatchlist[tvrage_id + '_id'][showid][b'seasons'][season][b'episodes'][
                            episode] = episode
        except traktException as e:
            sickrage.srLogger.warning("Could not connect to trakt service, cannot download Episode Watchlist: %s" % repr(e))
            return False
        return True

    def _getShowCollection(self):
        """
        Get Collection and parse once into addressable structure
        """
        try:
            self.Collectionlist = {'tvdb_id': {}, 'tvrage_id': {}}
            sickrage.srLogger.debug("Getting Show Collection")
            TraktCollectionList = self.trakt_api.traktRequest("sync/collection/shows")
            tvdb_id = 'tvdb'
            tvrage_id = 'tvrage'

            for watchlist_el in TraktCollectionList:
                tvdb = False
                tvrage = False

                if not watchlist_el[b'show'][b'ids'][b"tvdb"] is None:
                    tvdb = True

                if not watchlist_el[b'show'][b'ids'][b"tvrage"] is None:
                    tvrage = True

                title = watchlist_el[b'show'][b'title']
                year = str(watchlist_el[b'show'][b'year'])

                if 'seasons' in watchlist_el:
                    for season_el in watchlist_el[b'seasons']:
                        for episode_el in season_el[b'episodes']:
                            season = str(season_el[b'number'])
                            episode = str(episode_el[b'number'])

                            if tvdb:
                                showid = str(watchlist_el[b'show'][b'ids'][tvdb_id])

                                if showid not in self.Collectionlist[tvdb_id + '_id'].keys():
                                    self.Collectionlist[tvdb_id + '_id'][showid] = {'id': showid, 'title': title,
                                                                                    'year': year, 'seasons': {}}

                                if season not in self.Collectionlist[tvdb_id + '_id'][showid][b'seasons'].keys():
                                    self.Collectionlist[tvdb_id + '_id'][showid][b'seasons'][season] = {'s': season,
                                                                                                        'episodes': {}}

                                if episode not in self.Collectionlist[tvdb_id + '_id'][showid][b'seasons'][season][
                                    'episodes'].keys():
                                    self.Collectionlist[tvdb_id + '_id'][showid][b'seasons'][season][b'episodes'][
                                        episode] = episode

                            if tvrage:
                                showid = str(watchlist_el[b'show'][b'ids'][tvrage_id])

                                if showid not in self.Collectionlist[tvrage_id + '_id'].keys():
                                    self.Collectionlist[tvrage_id + '_id'][showid] = {'id': showid, 'title': title,
                                                                                      'year': year, 'seasons': {}}

                                if season not in self.Collectionlist[tvrage_id + '_id'][showid][b'seasons'].keys():
                                    self.Collectionlist[tvrage_id + '_id'][showid][b'seasons'][season] = {'s': season,
                                                                                                          'episodes': {}}

                                if episode not in self.Collectionlist[tvrage_id + '_id'][showid][b'seasons'][season][
                                    'episodes'].keys():
                                    self.Collectionlist[tvrage_id + '_id'][showid][b'seasons'][season][b'episodes'][
                                        episode] = episode
        except traktException as e:
            sickrage.srLogger.warning("Could not connect to trakt service, cannot download Show Collection: %s" % repr(e))
            return False
        return True

    @staticmethod
    def trakt_bulk_data_generate(data):
        """
        Build the JSON structure to send back to Trakt
        """
        uniqueShows = {}
        uniqueSeasons = {}

        for showid, indexerid, show_name, startyear, season, episode in data:
            if showid not in uniqueShows:
                uniqueShows[showid] = {'title': show_name, 'year': startyear, 'ids': {}, 'seasons': []}
                trakt_id = sickrage.srCore.INDEXER_API(indexerid).config[b'trakt_id']

                if trakt_id == 'tvdb_id':
                    uniqueShows[showid][b'ids'][b"tvdb"] = showid
                else:
                    uniqueShows[showid][b'ids'][b"tvrage"] = showid
                uniqueSeasons[showid] = []

        # Get the unique seasons per Show
        for showid, indexerid, show_name, startyear, season, episode in data:
            if season not in uniqueSeasons[showid]:
                uniqueSeasons[showid].append(season)

        # build the query
        traktShowList = []
        seasonsList = {}

        for searchedShow in uniqueShows:
            seasonsList[searchedShow] = []

            for searchedSeason in uniqueSeasons[searchedShow]:
                episodesList = []

                for showid, indexerid, show_name, startyear, season, episode in data:
                    if season == searchedSeason and showid == searchedShow:
                        episodesList.append({'number': episode})
                show = uniqueShows[searchedShow]
                show[b'seasons'].append({'number': searchedSeason, 'episodes': episodesList})
                traktShowList.append(show)
        post_data = {'shows': traktShowList}
        return post_data
