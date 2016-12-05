
# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
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

import datetime
import glob
import os
import re
import stat
import threading
import traceback

import imdbpie
import send2trash
from CodernityDB.database import RecordNotFound

import sickrage
from sickrage.core.blackandwhitelist import BlackAndWhiteList
from sickrage.core.caches import image_cache
from sickrage.core.classes import ShowListUI
from sickrage.core.common import Quality, SKIPPED, WANTED, UNKNOWN, DOWNLOADED, IGNORED, SNATCHED, SNATCHED_PROPER, \
    UNAIRED, ARCHIVED, statusStrings, Overview, FAILED, SNATCHED_BEST
from sickrage.core.exceptions import CantRefreshShowException, CantRemoveShowException
from sickrage.core.exceptions import MultipleShowObjectsException, ShowNotFoundException, \
    EpisodeNotFoundException, EpisodeDeletedException, MultipleShowsInDatabaseException
from sickrage.core.helpers import listMediaFiles, isMediaFile, update_anime_support, findCertainShow, tryInt, \
    safe_getattr, removetree
from sickrage.core.nameparser import NameParser, InvalidNameException, InvalidShowException
from sickrage.indexers import srIndexerApi
from sickrage.indexers.config import INDEXER_TVRAGE
from sickrage.indexers.exceptions import indexer_attributenotfound


# noinspection PyUnresolvedReferences
class TVShow(object):
    def __init__(self, indexer, indexerid, lang=""):
        self.lock = threading.Lock()

        self._indexerid = int(indexerid)
        self._indexer = int(indexer)
        self._name = ""
        self._imdbid = ""
        self._network = ""
        self._genre = ""
        self._classification = 'Scripted'
        self._runtime = 0
        self._imdb_info = {}
        self._quality = tryInt(sickrage.srCore.srConfig.QUALITY_DEFAULT, UNKNOWN)
        self._flatten_folders = int(sickrage.srCore.srConfig.FLATTEN_FOLDERS_DEFAULT)
        self._status = "Unknown"
        self._airs = ""
        self._startyear = 0
        self._paused = 0
        self._air_by_date = 0
        self._subtitles = int(sickrage.srCore.srConfig.SUBTITLES_DEFAULT)
        self._dvdorder = 0
        self._archive_firstmatch = 0
        self._lang = lang
        self._last_update = datetime.datetime.now().toordinal()
        self._last_refresh = datetime.datetime.now().toordinal()
        self._sports = 0
        self._anime = 0
        self._scene = 0
        self._rls_ignore_words = ""
        self._rls_require_words = ""
        self._default_ep_status = SKIPPED
        self.dirty = True

        self._location = ""
        self.episodes = {}
        self.next_aired = ""
        self.release_groups = None

        otherShow = findCertainShow(sickrage.srCore.SHOWLIST, self.indexerid)
        if otherShow is not None:
            raise MultipleShowObjectsException("Can't create a show if it already exists")

        self.loadFromDB()

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if self._name != value:
            self.dirty = True
        self._name = value

    @property
    def indexerid(self):
        return self._indexerid

    @indexerid.setter
    def indexerid(self, value):
        if self._indexerid != value:
            self.dirty = True
        self._indexerid = value

    @property
    def indexer(self):
        return self._indexer

    @indexer.setter
    def indexer(self, value):
        if self._indexer != value:
            self.dirty = True
        self._indexer = value

    @property
    def imdbid(self):
        return self._imdbid

    @imdbid.setter
    def imdbid(self, value):
        if self._imdbid != value:
            self.dirty = True
        self._imdbid = value

    @property
    def network(self):
        return self._network

    @network.setter
    def network(self, value):
        if self._network != value:
            self.dirty = True
        self._network = value

    @property
    def genre(self):
        return self._genre

    @genre.setter
    def genre(self, value):
        if self._genre != value:
            self.dirty = True
        self._genre = value

    @property
    def classification(self):
        return self._classification

    @classification.setter
    def classification(self, value):
        if self._classification != value:
            self.dirty = True
        self._classification = value

    @property
    def runtime(self):
        return self._runtime

    @runtime.setter
    def runtime(self, value):
        if self._runtime != value:
            self.dirty = True
        self._runtime = value

    @property
    def imdb_info(self):
        return self._imdb_info

    @imdb_info.setter
    def imdb_info(self, value):
        if self._imdb_info != value:
            self.dirty = True
        self._imdb_info = value

    @property
    def quality(self):
        return self._quality

    @quality.setter
    def quality(self, value):
        if self._quality != value:
            self.dirty = True
        self._quality = value

    @property
    def flatten_folders(self):
        return self._flatten_folders

    @flatten_folders.setter
    def flatten_folders(self, value):
        if self._flatten_folders != value:
            self.dirty = True
        self._flatten_folders = value

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if self._status != value:
            self.dirty = True
        self._status = value

    @property
    def airs(self):
        return self._airs

    @airs.setter
    def airs(self, value):
        if self._airs != value:
            self.dirty = True
        self._airs = value

    @property
    def startyear(self):
        return self._startyear

    @startyear.setter
    def startyear(self, value):
        if self._startyear != value:
            self.dirty = True
        self._startyear = value

    @property
    def paused(self):
        return self._paused

    @paused.setter
    def paused(self, value):
        if self._paused != value:
            self.dirty = True
        self._paused = value

    @property
    def air_by_date(self):
        return self._air_by_date

    @air_by_date.setter
    def air_by_date(self, value):
        if self._air_by_date != value:
            self.dirty = True
        self._air_by_date = value

    @property
    def subtitles(self):
        return self._subtitles

    @subtitles.setter
    def subtitles(self, value):
        if self._subtitles != value:
            self.dirty = True
        self._subtitles = value

    @property
    def dvdorder(self):
        return self._dvdorder

    @dvdorder.setter
    def dvdorder(self, value):
        if self._dvdorder != value:
            self.dirty = True
        self._dvdorder = value

    @property
    def archive_firstmatch(self):
        return self._archive_firstmatch

    @archive_firstmatch.setter
    def archive_firstmatch(self, value):
        if self._archive_firstmatch != value:
            self.dirty = True
        self._archive_firstmatch = value

    @property
    def lang(self):
        return self._lang

    @lang.setter
    def lang(self, value):
        if self._lang != value:
            self.dirty = True
        self._lang = value

    @property
    def last_update(self):
        return self._last_update

    @last_update.setter
    def last_update(self, value):
        if self._last_update != value:
            self.dirty = True
        self._last_update = value

    @property
    def last_refresh(self):
        return self._last_refresh

    @last_refresh.setter
    def last_refresh(self, value):
        if self._last_refresh != value:
            self.dirty = True
        self._last_refresh = value

    @property
    def sports(self):
        return self._sports

    @sports.setter
    def sports(self, value):
        if self._sports != value:
            self.dirty = True
        self._sports = value

    @property
    def anime(self):
        return self._anime

    @anime.setter
    def anime(self, value):
        if self._anime != value:
            self.dirty = True
        self._anime = value

    @property
    def scene(self):
        return self._scene

    @scene.setter
    def scene(self, value):
        if self._scene != value:
            self.dirty = True
        self._scene = value

    @property
    def rls_ignore_words(self):
        return self._rls_ignore_words

    @rls_ignore_words.setter
    def rls_ignore_words(self, value):
        if self._rls_ignore_words != value:
            self.dirty = True
        self._rls_ignore_words = value

    @property
    def rls_require_words(self):
        return self._rls_require_words

    @rls_require_words.setter
    def rls_require_words(self, value):
        if self._rls_require_words != value:
            self.dirty = True
        self._rls_require_words = value

    @property
    def default_ep_status(self):
        return self._default_ep_status

    @default_ep_status.setter
    def default_ep_status(self, value):
        if self._default_ep_status != value:
            self.dirty = True
        self._default_ep_status = value

    @property
    def is_anime(self):
        return True if int(self.anime) > 0 else False

    @property
    def is_sports(self):
        return True if int(self.sports) > 0 else False

    @property
    def is_scene(self):
        return True if int(self.scene) > 0 else False

    @property
    def network_logo_name(self):
        return self.network.replace('\u00C9', 'e').replace('\u00E9', 'e').lower()

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, new_location):
        if sickrage.srCore.srConfig.ADD_SHOWS_WO_DIR or os.path.isdir(new_location):
            sickrage.srCore.srLogger.debug("Show location set to " + new_location)
            self.dirty = True
            self._location = new_location

    # delete references to anything that's not in the internal lists
    def flushEpisodes(self):
        for curSeason in self.episodes:
            for curEp in self.episodes[curSeason]:
                myEp = self.episodes[curSeason][curEp]
                self.episodes[curSeason][curEp] = None
                del myEp

    def getAllEpisodes(self, season=None, has_location=False):
        results = []
        for x in [x['doc'] for x in sickrage.srCore.mainDB.db.get_many('tv_episodes', self.indexerid, with_doc=True)]:
            if season and x['season'] != season:
                continue
            if has_location and x['location'] == '':
                continue

            results += [x]

        ep_list = []
        for cur_result in [x['doc'] for x in sickrage.srCore.mainDB.db.get_many('tv_episodes', self.indexerid, with_doc=True)]:
            cur_ep = self.getEpisode(int(cur_result["season"]), int(cur_result["episode"]))
            if not cur_ep:
                continue

            cur_ep.relatedEps = []
            if cur_ep.location:
                # if there is a location, check if it's a multi-episode (share_location > 0) and put them in relatedEps
                if len([r for r in results
                        if r['showid'] == cur_result['showid']
                        and r['season'] == cur_result['season']
                        and r['location'] != '' and r['location'] == cur_result['location']
                        and r['episode'] != cur_result['episode']]) > 0:

                    related_eps_result = sorted([x['doc'] for x in
                                                 sickrage.srCore.mainDB.db.get_many('tv_episodes', self.indexerid, with_doc=True)
                                                 if x['doc']['season'] == cur_ep.season
                                                 and x['doc']['location'] == cur_ep.location
                                                 and x['doc']['episode'] == cur_ep.episode], key=lambda d: d['episode'])

                    for cur_related_ep in related_eps_result:
                        related_ep = self.getEpisode(int(cur_related_ep["season"]), int(cur_related_ep["episode"]))
                        if related_ep and related_ep not in cur_ep.relatedEps:
                            cur_ep.relatedEps.append(related_ep)

            ep_list.append(cur_ep)

        return ep_list

    def getEpisode(self, season=None, episode=None, file=None, noCreate=False, absolute_number=None, ):

        # if we get an anime get the real season and episode
        if self.is_anime and absolute_number and not season and not episode:
            dbData = [x['doc'] for x in sickrage.srCore.mainDB.db.get_many('tv_episodes', self.indexerid, with_doc=True)
                      if x['doc']['absolute_number'] == absolute_number and x['doc']['season'] != 0]

            if len(dbData) == 1:
                episode = int(dbData[0]["episode"])
                season = int(dbData[0]["season"])
                sickrage.srCore.srLogger.debug(
                    "Found episode by absolute_number %s which is S%02dE%02d" % (
                        absolute_number, season or 0, episode or 0))
            elif len(dbData) > 1:
                sickrage.srCore.srLogger.error("Multiple entries for absolute number: " + str(
                    absolute_number) + " in show: " + self.name + " found ")
                return None
            else:
                sickrage.srCore.srLogger.debug(
                    "No entries for absolute number: " + str(absolute_number) + " in show: " + self.name + " found.")
                return None

        if season not in self.episodes:
            self.episodes[season] = {}

        if episode not in self.episodes[season] or self.episodes[season][episode] is None:
            if noCreate:
                return None

            from sickrage.core.tv.episode import TVEpisode

            if file:
                ep = TVEpisode(self, season, episode, file=file)
            else:
                ep = TVEpisode(self, season, episode)

            if ep is not None:
                self.episodes[season][episode] = ep

        return self.episodes[season][episode]

    def should_update(self, update_date=datetime.date.today()):
        # if show status 'Ended' always update (status 'Continuing')
        if self.status.lower() == 'continuing':
            return True

        # run logic against the current show latest aired and next unaired data to see if we should bypass 'Ended' status
        graceperiod = datetime.timedelta(days=30)
        last_airdate = datetime.date.fromordinal(1)

        # get latest aired episode to compare against today - graceperiod and today + graceperiod
        dbData = sorted([x['doc'] for x in sickrage.srCore.mainDB.db.get_many('tv_episodes', self.indexerid, with_doc=True)
                         if x['doc']['season'] > 0 and x['doc']['airdate'] > 1 and x['doc']['status'] == 1],
                        key=lambda d: d['airdate'], reverse=True)

        if dbData:
            last_airdate = datetime.date.fromordinal(dbData[0]['airdate'])
            if (update_date - graceperiod) <= last_airdate <= (update_date + graceperiod):
                return True

        # get next upcoming UNAIRED episode to compare against today + graceperiod
        dbData = sorted([x['doc'] for x in sickrage.srCore.mainDB.db.get_many('tv_episodes', self.indexerid, with_doc=True)
                         if x['doc']['season'] > 0 and x['doc']['airdate'] > 1 and x['doc']['status'] == 1],
                        key=lambda d: d['airdate'])

        if dbData:
            next_airdate = datetime.date.fromordinal(dbData[0]['airdate'])
            if next_airdate <= (update_date + graceperiod):
                return True

        # in the first year after ended (last airdate), update every 30 days
        if (update_date - last_airdate) < datetime.timedelta(days=450) and (
                    update_date - datetime.date.fromordinal(self.last_update)) > datetime.timedelta(days=30):
            return True

        return False

    def writeShowNFO(self):

        result = False

        if not os.path.isdir(self.location):
            sickrage.srCore.srLogger.info(str(self.indexerid) + ": Show dir doesn't exist, skipping NFO generation")
            return False

        sickrage.srCore.srLogger.debug(str(self.indexerid) + ": Writing NFOs for show")
        for cur_provider in sickrage.srCore.metadataProviderDict.values():
            if not cur_provider.enabled:
                continue

            result = cur_provider.create_show_metadata(self) or result

        return result

    def writeMetadata(self, show_only=False):

        if not os.path.isdir(self.location):
            sickrage.srCore.srLogger.info(str(self.indexerid) + ": Show dir doesn't exist, skipping NFO generation")
            return

        self.getImages()

        self.writeShowNFO()

        if not show_only:
            self.writeEpisodeNFOs()

    def writeEpisodeNFOs(self):

        if not os.path.isdir(self.location):
            sickrage.srCore.srLogger.info(str(self.indexerid) + ": Show dir doesn't exist, skipping NFO generation")
            return

        sickrage.srCore.srLogger.debug(str(self.indexerid) + ": Writing NFOs for all episodes")

        for dbData in [x['doc'] for x in sickrage.srCore.mainDB.db.get_many('tv_episodes', self.indexerid, with_doc=True)
                       if x['doc']['location'] != '']:
            sickrage.srCore.srLogger.debug(str(self.indexerid) + ": Retrieving/creating episode S%02dE%02d" % (
                dbData["season"] or 0, dbData["episode"] or 0))

            curEp = self.getEpisode(dbData["season"], dbData["episode"])
            curEp.createMetaFiles()

    def updateMetadata(self):

        if not os.path.isdir(self.location):
            sickrage.srCore.srLogger.info(str(self.indexerid) + ": Show dir doesn't exist, skipping NFO generation")
            return

        self.updateShowNFO()

    def updateShowNFO(self):

        result = False

        if not os.path.isdir(self.location):
            sickrage.srCore.srLogger.info(str(self.indexerid) + ": Show dir doesn't exist, skipping NFO generation")
            return False

        sickrage.srCore.srLogger.info(str(self.indexerid) + ": Updating NFOs for show with new indexer info")
        for cur_provider in sickrage.srCore.metadataProviderDict.values():
            if not cur_provider.enabled:
                continue

            result = cur_provider.update_show_indexer_metadata(self) or result

        return result

    # find all media files in the show folder and create episodes for as many as possible
    def loadEpisodesFromDir(self):
        if not os.path.isdir(self.location):
            sickrage.srCore.srLogger.debug(
                str(self.indexerid) + ": Show dir doesn't exist, not loading episodes from disk")
            return

        sickrage.srCore.srLogger.debug(
            str(self.indexerid) + ": Loading all episodes from the show directory " + self.location)

        # get file list
        mediaFiles = listMediaFiles(self.location)
        sickrage.srCore.srLogger.debug("%s: Found files: %s" %
                                       (self.indexerid, mediaFiles))

        # create TVEpisodes from each media file (if possible)
        for mediaFile in mediaFiles:
            curEpisode = None

            sickrage.srCore.srLogger.debug(str(self.indexerid) + ": Creating episode from " + mediaFile)
            try:
                curEpisode = self.makeEpFromFile(os.path.join(self.location, mediaFile))
            except (ShowNotFoundException, EpisodeNotFoundException) as e:
                sickrage.srCore.srLogger.error("Episode " + mediaFile + " returned an exception: {}".format(e.message))
            except EpisodeDeletedException:
                sickrage.srCore.srLogger.debug("The episode deleted itself when I tried making an object for it")

            # skip to next episode?
            if not curEpisode:
                continue

            # see if we should save the release name in the db
            ep_file_name = os.path.basename(curEpisode.location)
            ep_file_name = os.path.splitext(ep_file_name)[0]

            try:
                parse_result = None
                np = NameParser(False, showObj=self, tryIndexers=True)
                parse_result = np.parse(ep_file_name)
            except (InvalidNameException, InvalidShowException):
                pass

            if ' ' not in ep_file_name and parse_result and parse_result.release_group:
                sickrage.srCore.srLogger.debug(
                    "Name " + ep_file_name + " gave release group of " + parse_result.release_group + ", seems valid")
                curEpisode.release_name = ep_file_name

            # store the reference in the show
            if self.subtitles:
                try:
                    curEpisode.refreshSubtitles()
                except Exception:
                    sickrage.srCore.srLogger.error("%s: Could not refresh subtitles" % self.indexerid)
                    sickrage.srCore.srLogger.debug(traceback.format_exc())

            curEpisode.saveToDB()

    def loadEpisodesFromDB(self):
        scannedEps = {}

        sickrage.srCore.srLogger.debug("{}: Loading all episodes for show from DB".format(self.indexerid))

        lINDEXER_API_PARMS = srIndexerApi(self.indexer).api_params.copy()

        if self.lang:
            lINDEXER_API_PARMS['language'] = self.lang

        if self.dvdorder != 0:
            lINDEXER_API_PARMS['dvdorder'] = True

        t = srIndexerApi(self.indexer).indexer(**lINDEXER_API_PARMS)

        cachedShow = t[self.indexerid]
        cachedSeasons = {}

        for dbData in [x['doc'] for x in sickrage.srCore.mainDB.db.get_many('tv_episodes', self.indexerid, with_doc=True)]:
            deleteEp = False

            curSeason = int(dbData["season"])
            curEpisode = int(dbData["episode"])

            if curSeason not in cachedSeasons:
                try:
                    cachedSeasons[curSeason] = cachedShow[curSeason]
                except indexer_seasonnotfound, e:
                    sickrage.srCore.srLogger.warning("Error when trying to load the episode from TVDB: " + e.message)
                    deleteEp = True

            if curSeason not in scannedEps:
                scannedEps[curSeason] = {}

            try:
                sickrage.srCore.srLogger.debug(
                    "{}: Loading episode S{}E{} info".format(self.indexerid, curSeason or 0, curEpisode or 0))

                curEp = self.getEpisode(curSeason, curEpisode)
                if deleteEp: curEp.deleteEpisode()

                curEp.loadFromDB(curSeason, curEpisode)
                curEp.loadFromIndexer(tvapi=t, cachedSeason=cachedSeasons[curSeason])
                scannedEps[curSeason][curEpisode] = True
            except EpisodeDeletedException:
                continue

        return scannedEps

    def loadEpisodesFromIndexer(self, cache=True):
        scannedEps = {}

        lINDEXER_API_PARMS = srIndexerApi(self.indexer).api_params.copy()
        lINDEXER_API_PARMS['cache'] = cache

        if self.lang:
            lINDEXER_API_PARMS['language'] = self.lang

        if self.dvdorder != 0:
            lINDEXER_API_PARMS['dvdorder'] = True

        t = srIndexerApi(self.indexer).indexer(**lINDEXER_API_PARMS)
        showObj = t[self.indexerid]

        sickrage.srCore.srLogger.debug(
            str(self.indexerid) + ": Loading all episodes from " + srIndexerApi(
                self.indexer).name + "..")

        for season in showObj:
            scannedEps[season] = {}
            for episode in showObj[season]:
                # need some examples of wtf episode 0 means to decide if we want it or not
                if episode == 0:
                    continue
                try:
                    curEp = self.getEpisode(season, episode)
                except EpisodeNotFoundException:
                    sickrage.srCore.srLogger.info("%s: %s object for S%02dE%02d is incomplete, skipping this episode" % (
                        self.indexerid, srIndexerApi(self.indexer).name, season or 0, episode or 0))
                    continue
                else:
                    try:
                        curEp.loadFromIndexer(tvapi=t)
                    except EpisodeDeletedException:
                        sickrage.srCore.srLogger.info("The episode was deleted, skipping the rest of the load")
                        continue

                with curEp.lock:
                    sickrage.srCore.srLogger.debug("%s: Loading info from %s for episode S%02dE%02d" % (
                        self.indexerid, srIndexerApi(self.indexer).name, season or 0, episode or 0))

                    curEp.loadFromIndexer(season, episode, tvapi=t)
                    curEp.saveToDB()

                scannedEps[season][episode] = True

        # Done updating save last update date
        self.last_update = datetime.date.today().toordinal()
        self.saveToDB()

        return scannedEps

    def getImages(self, fanart=None, poster=None):
        fanart_result = poster_result = banner_result = False
        season_posters_result = season_banners_result = season_all_poster_result = season_all_banner_result = False

        for cur_provider in sickrage.srCore.metadataProviderDict.values():
            if not cur_provider.enabled:
                continue

            fanart_result = cur_provider.create_fanart(self) or fanart_result
            poster_result = cur_provider.create_poster(self) or poster_result
            banner_result = cur_provider.create_banner(self) or banner_result

            season_posters_result = cur_provider.create_season_posters(self) or season_posters_result
            season_banners_result = cur_provider.create_season_banners(self) or season_banners_result
            season_all_poster_result = cur_provider.create_season_all_poster(self) or season_all_poster_result
            season_all_banner_result = cur_provider.create_season_all_banner(self) or season_all_banner_result

        return fanart_result or poster_result or banner_result or season_posters_result or season_banners_result or season_all_poster_result or season_all_banner_result

    # make a TVEpisode object from a media file
    def makeEpFromFile(self, file):

        if not os.path.isfile(file):
            sickrage.srCore.srLogger.info(str(self.indexerid) + ": That isn't even a real file dude... " + file)
            return None

        sickrage.srCore.srLogger.debug(str(self.indexerid) + ": Creating episode object from " + file)

        try:
            myParser = NameParser(showObj=self, tryIndexers=True)
            parse_result = myParser.parse(file)
        except InvalidNameException:
            sickrage.srCore.srLogger.debug("Unable to parse the filename " + file + " into a valid episode")
            return None
        except InvalidShowException:
            sickrage.srCore.srLogger.debug("Unable to parse the filename " + file + " into a valid show")
            return None

        if not len(parse_result.episode_numbers):
            sickrage.srCore.srLogger.info("parse_result: " + str(parse_result))
            sickrage.srCore.srLogger.warning("No episode number found in " + file + ", ignoring it")
            return None

        # for now lets assume that any episode in the show dir belongs to that show
        season = parse_result.season_number if parse_result.season_number is not None else 1
        episodes = parse_result.episode_numbers
        rootEp = None

        for curEpNum in episodes:

            episode = int(curEpNum)

            sickrage.srCore.srLogger.debug(
                "%s: %s parsed to %s S%02dE%02d" % (self.indexerid, file, self.name, season or 0, episode or 0))

            checkQualityAgain = False
            same_file = False

            curEp = self.getEpisode(season, episode)
            if not curEp:
                try:
                    curEp = self.getEpisode(season, episode, file)
                except EpisodeNotFoundException:
                    sickrage.srCore.srLogger.error(
                        str(self.indexerid) + ": Unable to figure out what this file is, skipping")
                    continue

            else:
                # if there is a new file associated with this ep then re-check the quality
                if curEp.location and os.path.normpath(curEp.location) != os.path.normpath(file):
                    sickrage.srCore.srLogger.debug(
                        "The old episode had a different file associated with it, I will re-check the quality based on the new filename " + file)
                    checkQualityAgain = True

                with curEp.lock:
                    curEp.location = file

                    # if the sizes are the same then it's probably the same file
                    old_size = curEp.file_size
                    if old_size and curEp.file_size == old_size:
                        same_file = True
                    else:
                        same_file = False

                    curEp.checkForMetaFiles()

                    # tries to fix episodes with a UNKNOWN quality set to them
                    oldStatus, oldQuality = Quality.splitCompositeStatus(curEp.status)
                    if oldQuality == Quality.UNKNOWN:
                        newQuality = Quality.nameQuality(file, self.is_anime)
                        curEp.status = Quality.compositeStatus(oldStatus, newQuality)

            if rootEp is None:
                rootEp = curEp
            else:
                if curEp not in rootEp.relatedEps:
                    with rootEp.lock:
                        rootEp.relatedEps.append(curEp)

            # if it's a new file then
            if not same_file:
                with curEp.lock:
                    curEp.release_name = ''

            # if they replace a file on me I'll make some attempt at re-checking the quality unless I know it's the same file
            if checkQualityAgain and not same_file:
                newQuality = Quality.nameQuality(file, self.is_anime)
                sickrage.srCore.srLogger.debug("Since this file has been renamed")
                if newQuality != UNKNOWN:
                    with curEp.lock:
                        curEp.status = Quality.compositeStatus(DOWNLOADED, newQuality)


            # check for status/quality changes as long as it's a new file
            elif not same_file and isMediaFile(
                    file) and curEp.status not in Quality.DOWNLOADED + Quality.ARCHIVED + [IGNORED]:
                oldStatus, oldQuality = Quality.splitCompositeStatus(curEp.status)
                newQuality = Quality.nameQuality(file, self.is_anime)
                if newQuality == Quality.UNKNOWN:
                    newQuality = Quality.assumeQuality(file)

                newStatus = None

                # if it was snatched and now exists then set the status correctly
                if oldStatus == SNATCHED and oldQuality <= newQuality:
                    sickrage.srCore.srLogger.debug(
                        "STATUS: this ep used to be snatched with quality " + Quality.qualityStrings[
                            oldQuality] +
                        " but a file exists with quality " + Quality.qualityStrings[newQuality] +
                        " so I'm setting the status to DOWNLOADED")
                    newStatus = DOWNLOADED

                # if it was snatched proper and we found a higher quality one then allow the status change
                elif oldStatus == SNATCHED_PROPER and oldQuality < newQuality:
                    sickrage.srCore.srLogger.debug(
                        "STATUS: this ep used to be snatched proper with quality " + Quality.qualityStrings[
                            oldQuality] +
                        " but a file exists with quality " + Quality.qualityStrings[newQuality] +
                        " so I'm setting the status to DOWNLOADED")
                    newStatus = DOWNLOADED

                elif oldStatus not in (SNATCHED, SNATCHED_PROPER):
                    newStatus = DOWNLOADED

                if newStatus is not None:
                    with curEp.lock:
                        sickrage.srCore.srLogger.debug(
                            "STATUS: we have an associated file, so setting the status from " + str(
                                curEp.status) + " to DOWNLOADED/" + str(
                                Quality.statusFromName(file, anime=self.is_anime)))
                        curEp.status = Quality.compositeStatus(newStatus, newQuality)

            with curEp.lock:
                curEp.saveToDB()

        # creating metafiles on the root should be good enough
        if rootEp:
            with rootEp.lock:
                rootEp.createMetaFiles()

        return rootEp

    def loadFromDB(self, skipNFO=False):

        sickrage.srCore.srLogger.debug(str(self.indexerid) + ": Loading show info from database")

        dbData = [x['doc'] for x in sickrage.srCore.mainDB.db.get_many('tv_shows', self.indexerid, with_doc=True)]

        if len(dbData) > 1:
            raise MultipleShowsInDatabaseException()
        elif len(dbData) == 0:
            sickrage.srCore.srLogger.info(str(self.indexerid) + ": Unable to find the show in the database")
            return False

        self._indexer = tryInt(dbData[0]["indexer"], self.indexer)
        self._name = dbData[0].get("show_name", self.name)
        self._network = dbData[0].get("network", self.network)
        self._genre = dbData[0].get("genre", self.genre)
        self._classification = dbData[0].get("classification", self.classification)
        self._runtime = dbData[0].get("runtime", self.runtime)
        self._status = dbData[0].get("status", self.status)
        self._airs = dbData[0].get("airs", self.airs)
        self._startyear = tryInt(dbData[0]["startyear"], self.startyear)
        self._air_by_date = tryInt(dbData[0]["air_by_date"], self.air_by_date)
        self._anime = tryInt(dbData[0]["anime"], self.anime)
        self._sports = tryInt(dbData[0]["sports"], self.sports)
        self._scene = tryInt(dbData[0]["scene"], self.scene)
        self._subtitles = tryInt(dbData[0]["subtitles"], self.subtitles)
        self._dvdorder = tryInt(dbData[0]["dvdorder"], self.dvdorder)
        self._archive_firstmatch = tryInt(dbData[0]["archive_firstmatch"], self.archive_firstmatch)
        self._quality = tryInt(dbData[0]["quality"], self.quality)
        self._flatten_folders = tryInt(dbData[0]["flatten_folders"], self.flatten_folders)
        self._paused = tryInt(dbData[0]["paused"], self.paused)
        self._lang = dbData[0].get("lang", self.lang)
        self._last_update = dbData[0].get("last_update", self.last_update)
        self._last_refresh = dbData[0].get("last_refresh", self.last_refresh)
        self._rls_ignore_words = dbData[0].get("rls_ignore_words", self.rls_ignore_words)
        self._rls_require_words = dbData[0].get("rls_require_words", self.rls_require_words)
        self._default_ep_status = tryInt(dbData[0]["default_ep_status"], self.default_ep_status)
        self._imdbid = dbData[0].get("imdb_id", self.imdbid)
        self._location = dbData[0].get("location", self.location)

        if self.is_anime:
            self.release_groups = BlackAndWhiteList(self.indexerid)

        if not skipNFO:
            try:
                # Get IMDb_info from database
                self._imdb_info = sickrage.srCore.mainDB.db.get('imdb_info', self.indexerid, with_doc=True)['doc']
            except RecordNotFound:
                pass

    def loadFromIndexer(self, cache=True, tvapi=None, cachedSeason=None):

        if self.indexer is not INDEXER_TVRAGE:
            sickrage.srCore.srLogger.debug(
                str(self.indexerid) + ": Loading show info from " + srIndexerApi(self.indexer).name)

            t = tvapi
            if not t:
                lINDEXER_API_PARMS = srIndexerApi(self.indexer).api_params.copy()
                lINDEXER_API_PARMS['cache'] = cache

                if self.lang:
                    lINDEXER_API_PARMS['language'] = self.lang

                if self.dvdorder != 0:
                    lINDEXER_API_PARMS['dvdorder'] = True

                t = srIndexerApi(self.indexer).indexer(**lINDEXER_API_PARMS)

            myEp = t[self.indexerid]
            if not myEp:
                return

            try:
                self.name = myEp['seriesname'].strip()
            except AttributeError:
                raise indexer_attributenotfound(
                    "Found %s, but attribute 'seriesname' was empty." % self.indexerid)

            self.classification = safe_getattr(myEp, 'classification', self.classification)
            self.genre = safe_getattr(myEp, 'genre', self.genre)
            self.network = safe_getattr(myEp, 'network', self.network)
            self.runtime = safe_getattr(myEp, 'runtime', self.runtime)
            self.imdbid = safe_getattr(myEp, 'imdb_id', self.imdbid)

            try:
                self.airs = safe_getattr(myEp, 'airs_dayofweek') + " " + safe_getattr(myEp, 'airs_time')
            except:
                pass

            try:
                self.startyear = tryInt(
                    str(safe_getattr(myEp, 'firstaired') or datetime.date.fromordinal(1)).split('-')[0])
            except:
                pass

            self.status = safe_getattr(myEp, 'status', self.status)
        else:
            sickrage.srCore.srLogger.warning(
                str(self.indexerid) + ": NOT loading info from " + srIndexerApi(
                    self.indexer).name + " as it is temporarily disabled.")

    def loadIMDbInfo(self, imdbapi=None):
        imdb_info = {'imdb_id': self.imdbid,
                     'title': '',
                     'year': '',
                     'akas': [],
                     'runtimes': '',
                     'genres': [],
                     'countries': '',
                     'country_codes': [],
                     'certificates': [],
                     'rating': '',
                     'votes': '',
                     'last_update': ''}

        i = imdbpie.Imdb()
        if not self.imdbid:
            for x in i.search_for_title(self.name):
                try:
                    if int(x.get('year'), 0) == self.startyear and x.get('title') == self.name:
                        self.imdbid = x.get('imdb_id')
                        break
                except:
                    continue

        if self.imdbid:
            sickrage.srCore.srLogger.debug(str(self.indexerid) + ": Loading show info from IMDb")

            imdbTv = i.get_title_by_id(self.imdbid)
            for key in [x for x in imdb_info.keys() if hasattr(imdbTv, x.replace('_', ' '))]:
                # Store only the first value for string type
                if isinstance(imdb_info[key], basestring) and isinstance(getattr(imdbTv, key.replace('_', ' ')), list):
                    imdb_info[key] = getattr(imdbTv, key.replace('_', ' '))[0]
                else:
                    imdb_info[key] = getattr(imdbTv, key.replace('_', ' '))

            # Filter only the value
            if imdb_info['runtimes']:
                imdb_info['runtimes'] = re.search(r'\d+', imdb_info['runtimes']).group(0)
            else:
                imdb_info['runtimes'] = self.runtime

            if imdb_info['akas']:
                imdb_info['akas'] = '|'.join(imdb_info['akas'])
            else:
                imdb_info['akas'] = ''

            # Join all genres in a string
            if imdb_info['genres']:
                imdb_info['genres'] = '|'.join(imdb_info['genres'])
            else:
                imdb_info['genres'] = ''

            # Get only the production country certificate if any
            if imdb_info['certificates'] and imdb_info['countries']:
                dct = {}
                try:
                    for item in imdb_info['certificates']:
                        dct[item.split(':')[0]] = item.split(':')[1]

                    imdb_info['certificates'] = dct[imdb_info['countries']]
                except Exception:
                    imdb_info['certificates'] = ''

            else:
                imdb_info['certificates'] = ''

            if imdb_info['country_codes']:
                imdb_info['country_codes'] = '|'.join(imdb_info['country_codes'])
            else:
                imdb_info['country_codes'] = ''

            imdb_info['last_update'] = datetime.date.today().toordinal()

            # Rename dict keys without spaces for DB upsert
            self.imdb_info = dict(
                (k.replace(' ', '_'), k(v) if hasattr(v, 'keys') else v) for k, v in imdb_info.items())

            sickrage.srCore.srLogger.debug(
                str(self.indexerid) + ": Obtained IMDb info ->" + str(self.imdb_info))

    def nextEpisode(self):
        curDate = datetime.date.today().toordinal()
        if not self.next_aired or self.next_aired and curDate > self.next_aired:
            dbData = sorted([x['doc'] for x in sickrage.srCore.mainDB.db.get_many('tv_episodes', self.indexerid, with_doc=True) if
                             x['doc']['airdate'] >= datetime.date.today().toordinal() and
                             x['doc']['status'] in (UNAIRED, WANTED)], key=lambda d: d['airdate'])

            self.next_aired = dbData[0]['airdate'] if dbData else ''

    def deleteShow(self, full=False):
        [sickrage.srCore.mainDB.db.delete(x['doc']) for x in sickrage.srCore.mainDB.db.get_many('tv_episodes', self.indexerid, with_doc=True)]
        [sickrage.srCore.mainDB.db.delete(x['doc']) for x in sickrage.srCore.mainDB.db.get_many('tv_shows', self.indexerid, with_doc=True)]
        [sickrage.srCore.mainDB.db.delete(x['doc']) for x in sickrage.srCore.mainDB.db.get_many('imdb_info', self.indexerid, with_doc=True)]
        [sickrage.srCore.mainDB.db.delete(x['doc']) for x in sickrage.srCore.mainDB.db.get_many('xem_refresh', self.indexerid, with_doc=True)]
        [sickrage.srCore.mainDB.db.delete(x['doc']) for x in sickrage.srCore.mainDB.db.get_many('scene_numbering', self.indexerid, with_doc=True)]
        action = ('delete', 'trash')[sickrage.srCore.srConfig.TRASH_REMOVE_SHOW]

        # remove self from show list
        sickrage.srCore.SHOWLIST = [x for x in sickrage.srCore.SHOWLIST if int(x.indexerid) != self.indexerid]

        # clear the cache
        image_cache_dir = os.path.join(sickrage.srCore.srConfig.CACHE_DIR, 'images')
        for cache_file in glob.glob(os.path.join(image_cache_dir, str(self.indexerid) + '.*')):
            sickrage.srCore.srLogger.info('Attempt to %s cache file %s' % (action, cache_file))
            try:
                if sickrage.srCore.srConfig.TRASH_REMOVE_SHOW:
                    send2trash.send2trash(cache_file)
                else:
                    os.remove(cache_file)

            except OSError as e:
                sickrage.srCore.srLogger.warning('Unable to %s %s: %s / %s' % (action, cache_file, repr(e), str(e)))

        # remove entire show folder
        if full:
            try:
                if not os.path.isdir(self.location):
                    sickrage.srCore.srLogger.warning(
                        "Show folder does not exist, no need to %s %s" % (action, self.location))
                    return

                sickrage.srCore.srLogger.info('Attempt to %s show folder %s' % (action, self.location))

                # check first the read-only attribute
                file_attribute = os.stat(self.location)[0]
                if not file_attribute & stat.S_IWRITE:
                    # File is read-only, so make it writeable
                    sickrage.srCore.srLogger.debug(
                        'Attempting to make writeable the read only folder %s' % self.location)
                    try:
                        os.chmod(self.location, stat.S_IWRITE)
                    except Exception:
                        sickrage.srCore.srLogger.warning('Unable to change permissions of %s' % self.location)

                if sickrage.srCore.srConfig.TRASH_REMOVE_SHOW:
                    send2trash.send2trash(self.location)
                else:
                    removetree(self.location)

                sickrage.srCore.srLogger.info('%s show folder %s' %
                                              (('Deleted', 'Trashed')[sickrage.srCore.srConfig.TRASH_REMOVE_SHOW],
                                               self.location))
            except OSError as e:
                sickrage.srCore.srLogger.warning('Unable to %s %s: %s / %s' % (action, self.location, repr(e), str(e)))

        if sickrage.srCore.srConfig.USE_TRAKT and sickrage.srCore.srConfig.TRAKT_SYNC_WATCHLIST:
            sickrage.srCore.srLogger.debug(
                "Removing show: indexerid " + str(self.indexerid) + ", Title " + str(
                    self.name) + " from Watchlist")
            sickrage.srCore.notifiersDict.trakt_notifier.update_watchlist(self, update="remove")

    def populateCache(self):
        cache_inst = image_cache.ImageCache()

        sickrage.srCore.srLogger.debug("Checking & filling cache for show " + self.name)
        cache_inst.fill_cache(self)

    def refreshDir(self):

        # make sure the show dir is where we think it is unless dirs are created on the fly
        if not os.path.isdir(self.location) and not sickrage.srCore.srConfig.CREATE_MISSING_SHOW_DIRS:
            return False

        # load from dir
        try:
            self.loadEpisodesFromDir()
        except Exception as e:
            sickrage.srCore.srLogger.debug("Error searching dir for episodes: {}".format(e.message))
            sickrage.srCore.srLogger.debug(traceback.format_exc())

        # run through all locations from DB, check that they exist
        sickrage.srCore.srLogger.debug(str(self.indexerid) + ": Loading all episodes with a location from the database")

        for ep in [x['doc'] for x in sickrage.srCore.mainDB.db.get_many('tv_episodes', self.indexerid, with_doc=True)
                   if x['doc']['location'] != '']:

            curLoc = os.path.normpath(ep["location"])
            season = int(ep["season"])
            episode = int(ep["episode"])

            try:
                curEp = self.getEpisode(season, episode)
            except EpisodeDeletedException:
                sickrage.srCore.srLogger.debug(
                    "The episode was deleted while we were refreshing it, moving on to the next one")
                continue

            # if the path doesn't exist or if it's not in our show dir
            if not os.path.isfile(curLoc) or not os.path.normpath(curLoc).startswith(
                    os.path.normpath(self.location)):

                # check if downloaded files still exist, update our data if this has changed
                if not sickrage.srCore.srConfig.SKIP_REMOVED_FILES:
                    with curEp.lock:
                        # if it used to have a file associated with it and it doesn't anymore then set it to sickrage.EP_DEFAULT_DELETED_STATUS
                        if curEp.location and curEp.status in Quality.DOWNLOADED:

                            if sickrage.srCore.srConfig.EP_DEFAULT_DELETED_STATUS == ARCHIVED:
                                _, oldQuality = Quality.splitCompositeStatus(curEp.status)
                                new_status = Quality.compositeStatus(ARCHIVED, oldQuality)
                            else:
                                new_status = sickrage.srCore.srConfig.EP_DEFAULT_DELETED_STATUS

                            sickrage.srCore.srLogger.debug(
                                "%s: Location for S%02dE%02d doesn't exist, removing it and changing our status to %s" %
                                (self.indexerid, season or 0, episode or 0, statusStrings[new_status]))
                            curEp.status = new_status
                            curEp.subtitles = list()
                            curEp.subtitles_searchcount = 0
                            curEp.subtitles_lastsearch = str(datetime.datetime.min)

                        curEp.location = ''
                        curEp.hasnfo = False
                        curEp.hastbn = False
                        curEp.release_name = ''

                        # save episode to DB
                        curEp.saveToDB()
            else:
                # the file exists, set its modify file stamp
                if sickrage.srCore.srConfig.AIRDATE_EPISODES:
                    with curEp.lock:
                        curEp.airdateModifyStamp()

    def downloadSubtitles(self):
        if not os.path.isdir(self.location):
            sickrage.srCore.srLogger.debug(str(self.indexerid) + ": Show dir doesn't exist, can't download subtitles")
            return

        sickrage.srCore.srLogger.debug("%s: Downloading subtitles" % self.indexerid)

        try:
            episodes = self.getAllEpisodes(has_location=True)
            if not episodes:
                sickrage.srCore.srLogger.debug(
                    "%s: No episodes to download subtitles for %s" % (self.indexerid, self.name))
                return

            for episode in episodes:
                episode.downloadSubtitles()

        except Exception:
            sickrage.srCore.srLogger.debug(
                "%s: Error occurred when downloading subtitles for %s" % (self.indexerid, self.name))
            sickrage.srCore.srLogger.error(traceback.format_exc())

    def saveToDB(self, forceSave=False):

        if not self.dirty and not forceSave:
            return

        sickrage.srCore.srLogger.debug("%i: Saving show to database: %s" % (self.indexerid, self.name))

        tv_show = {
            '_t': 'tv_shows',
            'indexer_id': self.indexerid,
            "indexer": self.indexer,
            "show_name": self.name,
            "location": self.location,
            "network": self.network,
            "genre": self.genre,
            "classification": self.classification,
            "runtime": self.runtime,
            "quality": self.quality,
            "airs": self.airs,
            "status": self.status,
            "flatten_folders": self.flatten_folders,
            "paused": self.paused,
            "air_by_date": self.air_by_date,
            "anime": self.anime,
            "scene": self.scene,
            "sports": self.sports,
            "subtitles": self.subtitles,
            "dvdorder": self.dvdorder,
            "archive_firstmatch": self.archive_firstmatch,
            "startyear": self.startyear,
            "lang": self.lang,
            "imdb_id": self.imdbid,
            "last_update": self.last_update,
            "last_refresh": self.last_refresh,
            "rls_ignore_words": self.rls_ignore_words,
            "rls_require_words": self.rls_require_words,
            "default_ep_status": self.default_ep_status
        }

        try:
            dbData = sickrage.srCore.mainDB.db.get('tv_shows', self.indexerid, with_doc=True)['doc']
            dbData.update(tv_show)
            sickrage.srCore.mainDB.db.update(dbData)
        except RecordNotFound:
            sickrage.srCore.mainDB.db.insert(tv_show)

        update_anime_support()

        if self.imdbid and self.imdb_info:
            try:
                dbData = sickrage.srCore.mainDB.db.get('imdb_info', self.indexerid, with_doc=True)['doc']
                dbData.update(self.imdb_info)
                sickrage.srCore.mainDB.db.update(dbData)
            except RecordNotFound:
                imdb_info = {
                    '_t': 'imdb_info',
                    'indexer_id': self.indexerid
                }
                imdb_info.update(self.imdb_info)
                sickrage.srCore.mainDB.db.insert(imdb_info)

    def __str__(self):
        toReturn = ""
        toReturn += "indexerid: " + str(self.indexerid) + "\n"
        toReturn += "indexer: " + str(self.indexer) + "\n"
        toReturn += "name: " + self.name + "\n"
        toReturn += "location: " + self.location + "\n"
        if self.network:
            toReturn += "network: " + self.network + "\n"
        if self.airs:
            toReturn += "airs: " + self.airs + "\n"
        toReturn += "status: " + self.status + "\n"
        toReturn += "startyear: " + str(self.startyear) + "\n"
        if self.genre:
            toReturn += "genre: " + self.genre + "\n"
        toReturn += "classification: " + self.classification + "\n"
        toReturn += "runtime: " + str(self.runtime) + "\n"
        toReturn += "quality: " + str(self.quality) + "\n"
        toReturn += "scene: " + str(self.is_scene) + "\n"
        toReturn += "sports: " + str(self.is_sports) + "\n"
        toReturn += "anime: " + str(self.is_anime) + "\n"
        return toReturn

    def qualitiesToString(self, qualities=None):
        if qualities is None:
            qualities = []

        result = ''
        for quality in qualities:
            if Quality.qualityStrings.has_key(quality):
                result += Quality.qualityStrings[quality] + ', '
            else:
                sickrage.srCore.srLogger.info("Bad quality value: " + str(quality))

        result = re.sub(', $', '', result)

        if not len(result):
            result = 'None'

        return result

    def wantEpisode(self, season, episode, quality, manualSearch=False, downCurQuality=False):
        sickrage.srCore.srLogger.debug("Checking if found episode %s S%02dE%02d is wanted at quality %s" % (
            self.name, season or 0, episode or 0, Quality.qualityStrings[quality]))

        # if the quality isn't one we want under any circumstances then just say no
        anyQualities, bestQualities = Quality.splitQuality(self.quality)
        sickrage.srCore.srLogger.debug("Any, Best = [{}] [{}] Found = [{}]".format(
            self.qualitiesToString(anyQualities),
            self.qualitiesToString(bestQualities),
            self.qualitiesToString([quality]))
        )

        if quality not in anyQualities + bestQualities or quality is UNKNOWN:
            sickrage.srCore.srLogger.debug("Don't want this quality, ignoring found episode")
            return False

        dbData = [x['doc'] for x in sickrage.srCore.mainDB.db.get_many('tv_episodes', self.indexerid, with_doc=True)
                  if x['doc']['season'] == season and x['doc']['episode'] == episode]

        if not dbData or not len(dbData):
            sickrage.srCore.srLogger.debug("Unable to find a matching episode in database, ignoring found episode")
            return False

        epStatus = int(dbData[0]["status"])
        epStatus_text = statusStrings[epStatus]

        sickrage.srCore.srLogger.debug("Existing episode status: " + str(epStatus) + " (" + epStatus_text + ")")

        # if we know we don't want it then just say no
        if epStatus in Quality.ARCHIVED + [UNAIRED, SKIPPED, IGNORED] and not manualSearch:
            sickrage.srCore.srLogger.debug(
                "Existing episode status is unaired/skipped/ignored/archived, ignoring found episode")
            return False

        curStatus, curQuality = Quality.splitCompositeStatus(epStatus)

        # if it's one of these then we want it as long as it's in our allowed initial qualities
        if epStatus in (WANTED, SKIPPED, UNKNOWN):
            sickrage.srCore.srLogger.debug("Existing episode status is wanted/skipped/unknown, getting found episode")
            return True
        elif manualSearch:
            if (downCurQuality and quality >= curQuality) or (not downCurQuality and quality > curQuality):
                sickrage.srCore.srLogger.debug(
                    "Usually ignoring found episode, but forced search allows the quality, getting found episode")
                return True

        # if we are re-downloading then we only want it if it's in our bestQualities list and better than what we have, or we only have one bestQuality and we do not have that quality yet
        if epStatus in Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_PROPER and quality in bestQualities and (
                        quality > curQuality or curQuality not in bestQualities):
            sickrage.srCore.srLogger.debug(
                "Episode already exists but the found episode quality is wanted more, getting found episode")
            return True
        elif curQuality == UNKNOWN and manualSearch:
            sickrage.srCore.srLogger.debug("Episode already exists but quality is Unknown, getting found episode")
            return True
        else:
            sickrage.srCore.srLogger.debug(
                "Episode already exists and the found episode has same/lower quality, ignoring found episode")

        sickrage.srCore.srLogger.debug("None of the conditions were met, ignoring found episode")
        return False

    def getOverview(self, epStatus):

        if epStatus == WANTED:
            return Overview.WANTED
        elif epStatus in (UNAIRED, UNKNOWN):
            return Overview.UNAIRED
        elif epStatus in (SKIPPED, IGNORED):
            return Overview.SKIPPED
        elif epStatus in Quality.ARCHIVED:
            return Overview.GOOD
        elif epStatus in Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.FAILED + Quality.SNATCHED_BEST:

            _, bestQualities = Quality.splitQuality(self.quality)  # @UnusedVariable
            if bestQualities:
                maxBestQuality = max(bestQualities)
                minBestQuality = min(bestQualities)
            else:
                maxBestQuality = None
                minBestQuality = None

            epStatus, curQuality = Quality.splitCompositeStatus(epStatus)

            if epStatus == FAILED:
                return Overview.WANTED
            if epStatus == DOWNLOADED and curQuality == Quality.UNKNOWN:
                return Overview.QUAL
            elif epStatus in (SNATCHED, SNATCHED_PROPER, SNATCHED_BEST):
                return Overview.SNATCHED
            # if they don't want re-downloads then we call it good if they have anything
            elif maxBestQuality is None:
                return Overview.GOOD
            # if the want only first match and already have one call it good
            elif self.archive_firstmatch and curQuality in bestQualities:
                return Overview.GOOD
            # if they want only first match and current quality is higher than minimal best quality call it good
            elif self.archive_firstmatch and minBestQuality is not None and curQuality > minBestQuality:
                return Overview.GOOD
            # if they have one but it's not the best they want then mark it as qual
            elif curQuality < maxBestQuality:
                return Overview.QUAL
            # if it's >= maxBestQuality then it's good
            else:
                return Overview.GOOD

    def mapIndexers(self):
        mapped = {}

        # init mapped indexers object
        for indexer in srIndexerApi().indexers:
            mapped[indexer] = self.indexerid if int(indexer) == int(self.indexer) else 0

        # for each mapped entry
        for dbData in [x['doc'] for x in sickrage.srCore.mainDB.db.get_many('indexer_mapping', self.indexerid, with_doc=True)
                       if x['doc']['indexer'] == self.indexer]:

            # Check if its mapped with both tvdb and tvrage.
            if len([i for i in dbData if i is not None]) >= 4:
                sickrage.srCore.srLogger.debug("Found indexer mapping in cache for show: " + self.name)
                mapped[int(dbData['mindexer'])] = int(dbData['mindexer_id'])
                return mapped
        else:
            for indexer in srIndexerApi().indexers:
                if indexer == self.indexer:
                    mapped[indexer] = self.indexerid
                    continue

                lINDEXER_API_PARMS = srIndexerApi(indexer).api_params.copy()
                lINDEXER_API_PARMS['custom_ui'] = ShowListUI
                t = srIndexerApi(indexer).indexer(**lINDEXER_API_PARMS)

                try:
                    mapped_show = t[self.name]
                except Exception:
                    sickrage.srCore.srLogger.debug("Unable to map " + srIndexerApi(
                        self.indexer).name + "->" + srIndexerApi(
                        indexer).name + " for show: " + self.name + ", skipping it")
                    continue

                if mapped_show and len(mapped_show) == 1:
                    sickrage.srCore.srLogger.debug("Mapping " + srIndexerApi(
                        self.indexer).name + "->" + srIndexerApi(
                        indexer).name + " for show: " + self.name)

                    mapped[indexer] = int(mapped_show[0]['id'])

                    sickrage.srCore.srLogger.debug("Adding indexer mapping to DB for show: " + self.name)

                    dbData = [x['doc'] for x in sickrage.srCore.mainDB.db.get_many('indexer_mapping', self.indexerid, with_doc=True)
                              if x['doc']['indexer'] == self.indexer
                              and x['doc']['mindexer_id'] == int(mapped_show[0]['id'])]

                    if not len(dbData):
                        sickrage.srCore.mainDB.db.insert({
                            '_t': 'indexer_mapping',
                            'indexer_id': self.indexerid,
                            'indexer': self.indexer,
                            'mindexer_id': int(mapped_show[0]['id']),
                            'mindexer': indexer
                        })

        return mapped

    def __getstate__(self):
        d = dict(self.__dict__)
        del d['lock']
        return d

    def __setstate__(self, d):
        d['lock'] = threading.Lock()
        self.__dict__.update(d)

    @staticmethod
    def delete(indexer_id, remove_files=False):
        """
        Try to delete a show
        :param indexer_id: The unique id of the show to delete
        :param remove_files: ``True`` to remove the files associated with the show, ``False`` otherwise
        :return: A tuple containing:
         - an error message if the show could not be deleted, ``None`` otherwise
         - the show object that was deleted, if it exists, ``None`` otherwise
        """

        error, show = TVShow._validate_indexer_id(indexer_id)

        if error is not None:
            return error, show

        try:
            sickrage.srCore.SHOWQUEUE.removeShow(show, bool(remove_files))
        except CantRemoveShowException as exception:
            return exception, show

        return None, show

    @staticmethod
    def overall_stats():
        shows = sickrage.srCore.SHOWLIST
        today = str(datetime.date.today().toordinal())

        downloaded_status = Quality.DOWNLOADED + Quality.ARCHIVED
        snatched_status = Quality.SNATCHED + Quality.SNATCHED_PROPER
        total_status = [SKIPPED, WANTED]

        stats = {
            'episodes': {
                'downloaded': 0,
                'snatched': 0,
                'total': 0,
            },
            'shows': {
                'active': len([show for show in shows if show.paused == 0 and show.status.lower() == 'continuing']),
                'total': len(shows),
            },
        }

        for result in [x['doc'] for x in sickrage.srCore.mainDB.db.all('tv_episodes', with_doc=True)]:
            if not (result['season'] > 0 and result['episode'] > 0 and result['airdate'] > 1):
                continue

            if result['status'] in downloaded_status:
                stats['episodes']['downloaded'] += 1
                stats['episodes']['total'] += 1
            elif result['status'] in snatched_status:
                stats['episodes']['snatched'] += 1
                stats['episodes']['total'] += 1
            elif result['airdate'] <= today and result['status'] in total_status:
                stats['episodes']['total'] += 1

        return stats

    @staticmethod
    def pause(indexer_id, pause=None):
        """
        Change the pause state of a show
        :param indexer_id: The unique id of the show to update
        :param pause: ``True`` to pause the show, ``False`` to resume the show, ``None`` to toggle the pause state
        :return: A tuple containing:
         - an error message if the pause state could not be changed, ``None`` otherwise
         - the show object that was updated, if it exists, ``None`` otherwise
        """

        error, show = TVShow._validate_indexer_id(indexer_id)

        if error is not None:
            return error, show

        if pause is None:
            show.paused = not show.paused
        else:
            show.paused = pause

        show.saveToDB()

        return None, show

    @staticmethod
    def refresh(indexer_id):
        """
        Try to refresh a show
        :param indexer_id: The unique id of the show to refresh
        :return: A tuple containing:
         - an error message if the show could not be refreshed, ``None`` otherwise
         - the show object that was refreshed, if it exists, ``None`` otherwise
        """

        error, show = TVShow._validate_indexer_id(indexer_id)

        if error is not None:
            return error, show

        try:
            sickrage.srCore.SHOWQUEUE.refreshShow(show)
        except CantRefreshShowException as exception:
            return exception, show

        return None, show

    @staticmethod
    def _validate_indexer_id(indexer_id):
        """
        Check that the provided indexer_id is valid and corresponds with a known show
        :param indexer_id: The indexer id to check
        :return: A tuple containing:
         - an error message if the indexer id is not correct, ``None`` otherwise
         - the show object corresponding to ``indexer_id`` if it exists, ``None`` otherwise
        """

        if indexer_id is None:
            return 'Invalid show ID', None

        try:
            show = findCertainShow(sickrage.srCore.SHOWLIST, int(indexer_id))
        except MultipleShowObjectsException:
            return 'Unable to find the specified show', None

        return None, show
