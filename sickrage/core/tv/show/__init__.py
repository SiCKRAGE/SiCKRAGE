#!/usr/bin/env python2
# Author: echel0n <sickrage.tv@gmail.com>
# URL: http://www.github.com/sickragetv/sickrage/
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

import glob
import json
import os
import re
import stat
import threading
import traceback
from datetime import date, datetime, timedelta

import imdbpie
import requests
import send2trash
import tmdbsimple

import sickrage
from core.blackandwhitelist import BlackAndWhiteList
from core.caches import image_cache
from core.classes import ShowListUI
from core.common import Quality, SKIPPED, WANTED, UNKNOWN, DOWNLOADED, IGNORED, SNATCHED, SNATCHED_PROPER, UNAIRED, \
    ARCHIVED, \
    statusStrings, Overview, FAILED, SNATCHED_BEST
from core.databases import main_db
from core.exceptions import CantRefreshShowException, \
    CantRemoveShowException
from core.exceptions import MultipleShowObjectsException, ShowDirectoryNotFoundException, ShowNotFoundException, \
    EpisodeNotFoundException, EpisodeDeletedException, MultipleShowsInDatabaseException
from core.helpers import listMediaFiles, isMediaFile, update_anime_support, findCertainShow, tryInt, safe_getattr
from core.nameparser import NameParser, InvalidNameException, InvalidShowException
from core.tv import dirty_setter
from indexers.indexer_config import INDEXER_TVRAGE
from indexers.indexer_exceptions import indexer_attributenotfound


# noinspection PyUnresolvedReferences
class TVShow(object):
    def __init__(self, indexer, indexerid, lang=""):
        self.lock = threading.Lock()
        self.dirty = True

        self._indexerid = int(indexerid)
        self._indexer = int(indexer)
        self._name = ""
        self._imdbid = ""
        self._tmdbid = ""
        self._network = ""
        self._genre = ""
        self._classification = 'Scripted'
        self._runtime = 0
        self._imdb_info = {}
        self._tmdb_info = {}
        self._quality = tryInt(sickrage.srConfig.QUALITY_DEFAULT, UNKNOWN)
        self._flatten_folders = int(sickrage.srConfig.FLATTEN_FOLDERS_DEFAULT)
        self._status = "Unknown"
        self._airs = ""
        self._startyear = 0
        self._paused = 0
        self._air_by_date = 0
        self._subtitles = int(sickrage.srConfig.SUBTITLES_DEFAULT)
        self._dvdorder = 0
        self._archive_firstmatch = 0
        self._lang = lang
        self._last_update_indexer = 1
        self._sports = 0
        self._anime = 0
        self._scene = 0
        self._rls_ignore_words = ""
        self._rls_require_words = ""
        self._default_ep_status = SKIPPED
        self._location = ""
        self.episodes = {}
        self.nextaired = ""
        self.release_groups = None

        otherShow = findCertainShow(sickrage.srCore.SHOWLIST, self.indexerid)
        if otherShow is not None:
            raise MultipleShowObjectsException("Can't create a show if it already exists")

        self.loadFromDB()

    name = property(lambda self: self._name, dirty_setter("_name"))
    indexerid = property(lambda self: self._indexerid, dirty_setter("_indexerid"))
    indexer = property(lambda self: self._indexer, dirty_setter("_indexer"))
    imdbid = property(lambda self: self._imdbid, dirty_setter("_imdbid"))
    tmdbid = property(lambda self: self._tmdbid, dirty_setter("_tmdbid"))
    network = property(lambda self: self._network, dirty_setter("_network"))
    genre = property(lambda self: self._genre, dirty_setter("_genre"))
    classification = property(lambda self: self._classification, dirty_setter("_classification"))
    runtime = property(lambda self: self._runtime, dirty_setter("_runtime"))
    imdb_info = property(lambda self: self._imdb_info, dirty_setter("_imdb_info"))
    tmdb_info = property(lambda self: self._tmdb_info, dirty_setter("_tmdb_info"))
    quality = property(lambda self: self._quality, dirty_setter("_quality"))
    flatten_folders = property(lambda self: self._flatten_folders, dirty_setter("_flatten_folders"))
    status = property(lambda self: self._status, dirty_setter("_status"))
    airs = property(lambda self: self._airs, dirty_setter("_airs"))
    startyear = property(lambda self: self._startyear, dirty_setter("_startyear"))
    paused = property(lambda self: self._paused, dirty_setter("_paused"))
    air_by_date = property(lambda self: self._air_by_date, dirty_setter("_air_by_date"))
    subtitles = property(lambda self: self._subtitles, dirty_setter("_subtitles"))
    dvdorder = property(lambda self: self._dvdorder, dirty_setter("_dvdorder"))
    archive_firstmatch = property(lambda self: self._archive_firstmatch, dirty_setter("_archive_firstmatch"))
    lang = property(lambda self: self._lang, dirty_setter("_lang"))
    last_update_indexer = property(lambda self: self._last_update_indexer, dirty_setter("_last_update_indexer"))
    sports = property(lambda self: self._sports, dirty_setter("_sports"))
    anime = property(lambda self: self._anime, dirty_setter("_anime"))
    scene = property(lambda self: self._scene, dirty_setter("_scene"))
    rls_ignore_words = property(lambda self: self._rls_ignore_words, dirty_setter("_rls_ignore_words"))
    rls_require_words = property(lambda self: self._rls_require_words, dirty_setter("_rls_require_words"))
    default_ep_status = property(lambda self: self._default_ep_status, dirty_setter("_default_ep_status"))

    @property
    def is_anime(self):
        if int(self.anime) > 0:
            return True
        else:
            return False

    @property
    def is_sports(self):
        if int(self.sports) > 0:
            return True
        else:
            return False

    @property
    def is_scene(self):
        if int(self.scene) > 0:
            return True
        else:
            return False

    @property
    def network_logo_name(self):
        return self.network.replace('\u00C9', 'e').replace('\u00E9', 'e').lower()

    def _get_location(self):
        # no dir check needed if missing show dirs are created during post-processing
        if sickrage.srConfig.CREATE_MISSING_SHOW_DIRS or os.path.isdir(self._location):
            return self._location
        else:
            raise ShowDirectoryNotFoundException("Invalid folder for the show!")

    def _set_location(self, new_location):
        sickrage.srLogger.debug("Setter sets location to " + new_location)
        # Don't validate dir if user wants to add shows without creating a dir
        if sickrage.srConfig.ADD_SHOWS_WO_DIR or os.path.isdir(new_location):
            dirty_setter("_location")(self, new_location)
        else:
            raise ShowDirectoryNotFoundException("Invalid folder for the show!")

    location = property(_get_location, _set_location)

    # delete references to anything that's not in the internal lists
    def flushEpisodes(self):
        for curSeason in self.episodes:
            for curEp in self.episodes[curSeason]:
                myEp = self.episodes[curSeason][curEp]
                self.episodes[curSeason][curEp] = None
                del myEp

    def getAllEpisodes(self, season=None, has_location=False):

        sql_selection = "SELECT season, episode,"

        # subselection to detect multi-episodes early, share_location > 0
        sql_selection += " (SELECT COUNT (*) FROM tv_episodes WHERE showid = tve.showid AND season = tve.season AND location != '' AND location = tve.location AND episode != tve.episode) AS share_location"
        sql_selection += " FROM tv_episodes tve WHERE showid = " + str(self.indexerid)

        if season is not None:
            sql_selection += " AND season = " + str(season)

        if has_location:
            sql_selection += " AND location != '' "

        # need ORDER episode ASC to rename multi-episodes in order S01E01-02
        sql_selection += " ORDER BY season ASC, episode ASC"

        results = main_db.MainDB().select(sql_selection)

        ep_list = []
        for cur_result in results:
            cur_ep = self.getEpisode(int(cur_result[b"season"]), int(cur_result[b"episode"]))
            if not cur_ep:
                continue

            cur_ep.relatedEps = []
            if cur_ep.location:
                # if there is a location, check if it's a multi-episode (share_location > 0) and put them in relatedEps
                if cur_result[b"share_location"] > 0:
                    related_eps_result = main_db.MainDB().select(
                        "SELECT * FROM tv_episodes WHERE showid = ? AND season = ? AND location = ? AND episode != ? ORDER BY episode ASC",
                        [self.indexerid, cur_ep.season, cur_ep.location, cur_ep.episode])
                    for cur_related_ep in related_eps_result:
                        related_ep = self.getEpisode(int(cur_related_ep[b"season"]),
                                                     int(cur_related_ep[b"episode"]))
                        if related_ep and related_ep not in cur_ep.relatedEps:
                            cur_ep.relatedEps.append(related_ep)
            ep_list.append(cur_ep)

        return ep_list

    def getEpisode(self, season=None, episode=None, file=None, noCreate=False, absolute_number=None, forceUpdate=False):

        # if we get an anime get the real season and episode
        if self.is_anime and absolute_number and not season and not episode:

            sql = "SELECT * FROM tv_episodes WHERE showid = ? AND absolute_number = ? AND season != 0"
            sqlResults = main_db.MainDB().select(sql, [self.indexerid, absolute_number])

            if len(sqlResults) == 1:
                episode = int(sqlResults[0][b"episode"])
                season = int(sqlResults[0][b"season"])
                sickrage.srLogger.debug(
                    "Found episode by absolute_number %s which is S%02dE%02d" % (
                        absolute_number, season or 0, episode or 0))
            elif len(sqlResults) > 1:
                sickrage.srLogger.error("Multiple entries for absolute number: " + str(
                    absolute_number) + " in show: " + self.name + " found ")
                return None
            else:
                sickrage.srLogger.debug(
                    "No entries for absolute number: " + str(
                        absolute_number) + " in show: " + self.name + " found.")
                return None

        if not season in self.episodes:
            self.episodes[season] = {}

        if not episode in self.episodes[season] or self.episodes[season][episode] is None:
            if noCreate:
                return None

            from core.tv.episode import TVEpisode

            if file:
                ep = TVEpisode(self, season, episode, file)
            else:
                ep = TVEpisode(self, season, episode)

            if ep is not None:
                self.episodes[season][episode] = ep

        return self.episodes[season][episode]

    def should_update(self, update_date=date.today()):

        # if show is not 'Ended' always update (status 'Continuing')
        if self.status == 'Continuing':
            return True

        # run logic against the current show latest aired and next unaired data to see if we should bypass 'Ended' status

        graceperiod = timedelta(days=30)

        last_airdate = date.fromordinal(1)

        # get latest aired episode to compare against today - graceperiod and today + graceperiod

        sql_result = main_db.MainDB().select(
            "SELECT * FROM tv_episodes WHERE showid = ? AND season > '0' AND airdate > '1' AND status > '1' ORDER BY airdate DESC LIMIT 1",
            [self.indexerid])

        if sql_result:
            last_airdate = date.fromordinal(sql_result[0][b'airdate'])
            if last_airdate >= (update_date - graceperiod) and last_airdate <= (update_date + graceperiod):
                return True

        # get next upcoming UNAIRED episode to compare against today + graceperiod
        sql_result = main_db.MainDB().select(
            "SELECT * FROM tv_episodes WHERE showid = ? AND season > '0' AND airdate > '1' AND status = '1' ORDER BY airdate ASC LIMIT 1",
            [self.indexerid])

        if sql_result:
            next_airdate = date.fromordinal(sql_result[0][b'airdate'])
            if next_airdate <= (update_date + graceperiod):
                return True

        self.last_update_indexer = date.fromordinal(self.last_update_indexer)

        # in the first year after ended (last airdate), update every 30 days
        if (update_date - last_airdate) < timedelta(days=450) and (
                    update_date - self.last_update_indexer) > timedelta(days=30):
            return True

        return False

    def writeShowNFO(self):

        result = False

        if not os.path.isdir(self.location):
            sickrage.srLogger.info(str(self.indexerid) + ": Show dir doesn't exist, skipping NFO generation")
            return False

        sickrage.srLogger.debug(str(self.indexerid) + ": Writing NFOs for show")
        for cur_provider in sickrage.srCore.metadataProviderDict.values():
            result = cur_provider.create_show_metadata(self) or result

        return result

    def writeMetadata(self, show_only=False):

        if not os.path.isdir(self.location):
            sickrage.srLogger.info(str(self.indexerid) + ": Show dir doesn't exist, skipping NFO generation")
            return

        self.getImages()

        self.writeShowNFO()

        if not show_only:
            self.writeEpisodeNFOs()

    def writeEpisodeNFOs(self):

        if not os.path.isdir(self.location):
            sickrage.srLogger.info(str(self.indexerid) + ": Show dir doesn't exist, skipping NFO generation")
            return

        sickrage.srLogger.debug(str(self.indexerid) + ": Writing NFOs for all episodes")

        sqlResults = main_db.MainDB().select("SELECT * FROM tv_episodes WHERE showid = ? AND location != ''",
                                             [self.indexerid])

        for epResult in sqlResults:
            sickrage.srLogger.debug(str(self.indexerid) + ": Retrieving/creating episode S%02dE%02d" % (
                epResult[b"season"] or 0, epResult[b"episode"] or 0))
            curEp = self.getEpisode(epResult[b"season"], epResult[b"episode"])
            if not curEp:
                continue

            curEp.createMetaFiles()

    def updateMetadata(self):

        if not os.path.isdir(self.location):
            sickrage.srLogger.info(str(self.indexerid) + ": Show dir doesn't exist, skipping NFO generation")
            return

        self.updateShowNFO()

    def updateShowNFO(self):

        result = False

        if not os.path.isdir(self.location):
            sickrage.srLogger.info(str(self.indexerid) + ": Show dir doesn't exist, skipping NFO generation")
            return False

        sickrage.srLogger.info(str(self.indexerid) + ": Updating NFOs for show with new indexer info")
        for cur_provider in sickrage.srCore.metadataProviderDict.values():
            result = cur_provider.update_show_indexer_metadata(self) or result

        return result

    # find all media files in the show folder and create episodes for as many as possible
    def loadEpisodesFromDir(self):
        if not os.path.isdir(self.location):
            sickrage.srLogger.debug(
                str(self.indexerid) + ": Show dir doesn't exist, not loading episodes from disk")
            return

        sickrage.srLogger.debug(
            str(self.indexerid) + ": Loading all episodes from the show directory " + self.location)

        # get file list
        mediaFiles = listMediaFiles(self.location)
        sickrage.srLogger.debug("%s: Found files: %s" %
                                (self.indexerid, mediaFiles))

        # create TVEpisodes from each media file (if possible)
        sql_l = []
        for mediaFile in mediaFiles:
            curEpisode = None

            sickrage.srLogger.debug(str(self.indexerid) + ": Creating episode from " + mediaFile)
            try:
                curEpisode = self.makeEpFromFile(os.path.join(self.location, mediaFile))
            except (ShowNotFoundException, EpisodeNotFoundException) as e:
                sickrage.srLogger.error("Episode " + mediaFile + " returned an exception: {}".format(e.message))
            except EpisodeDeletedException:
                sickrage.srLogger.debug("The episode deleted itself when I tried making an object for it")

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
                sickrage.srLogger.debug(
                    "Name " + ep_file_name + " gave release group of " + parse_result.release_group + ", seems valid")
                curEpisode.release_name = ep_file_name

            # store the reference in the show
            if self.subtitles:
                try:
                    curEpisode.refreshSubtitles()
                except Exception:
                    sickrage.srLogger.error("%s: Could not refresh subtitles" % self.indexerid)
                    sickrage.srLogger.debug(traceback.format_exc())

            sql_q = curEpisode.saveToDB(False)
            if sql_q:
                sql_l.append(sql_q)
                del sql_q  # cleanup

        if len(sql_l) > 0:
            main_db.MainDB().mass_upsert(sql_l)
            del sql_l  # cleanup

    def loadEpisodesFromDB(self):
        scannedEps = {}

        sickrage.srLogger.debug("{}: Loading all episodes for show".format(self.indexerid))

        sql = "SELECT * FROM tv_episodes WHERE showid = ?"
        sqlResults = main_db.MainDB().select(sql, [self.indexerid])

        for curResult in sqlResults:
            curEp = None

            curSeason = int(curResult[b"season"])
            curEpisode = int(curResult[b"episode"])

            if curSeason not in scannedEps:
                sickrage.srLogger.debug("Not curSeason in scannedEps")
                scannedEps[curSeason] = {}

            try:
                sickrage.srLogger.debug(
                    "{}: Loading episode S{}E{} info".format(self.indexerid, curSeason or 0, curEpisode or 0))

                curEp = self.getEpisode(curSeason, curEpisode)
                if not curEp:
                    raise EpisodeNotFoundException

                scannedEps[curSeason][curEpisode] = True
            except EpisodeDeletedException:
                if curEp:
                    curEp.deleteEpisode()

        sickrage.srLogger.debug("{}: Finished loading all episodes for show".format(self.indexerid))
        return scannedEps

    def loadEpisodesFromIndexer(self, cache=True):
        scannedEps = {}

        lINDEXER_API_PARMS = sickrage.srCore.INDEXER_API(self.indexer).api_params.copy()

        if not cache:
            lINDEXER_API_PARMS[b'cache'] = False

        if self.lang:
            lINDEXER_API_PARMS[b'language'] = self.lang

        if self.dvdorder != 0:
            lINDEXER_API_PARMS[b'dvdorder'] = True

        t = sickrage.srCore.INDEXER_API(self.indexer).indexer(**lINDEXER_API_PARMS)
        showObj = t[self.indexerid]

        sickrage.srLogger.debug(
            str(self.indexerid) + ": Loading all episodes from " + sickrage.srCore.INDEXER_API(
                self.indexer).name + "..")

        sql_l = []
        for season in showObj:
            if season not in scannedEps:
                scannedEps[season] = {}

            for episode in showObj[season]:
                curEp = None

                # need some examples of wtf episode 0 means to decide if we want it or not
                if episode == 0:
                    continue

                try:
                    curEp = self.getEpisode(season, episode)
                    if not curEp:
                        raise EpisodeNotFoundException

                    with curEp.lock:
                        sickrage.srLogger.debug("%s: Loading info from %s for episode S%02dE%02d" % (
                            self.indexerid, sickrage.srCore.INDEXER_API(self.indexer).name, season or 0, episode or 0))

                        sql_q = curEp.saveToDB(False)
                        if sql_q:
                            sql_l.append(sql_q)
                            del sql_q  # cleanup

                    scannedEps[season][episode] = True
                except EpisodeNotFoundException:
                    sickrage.LOGGER.info("%s: %s object for S%02dE%02d is incomplete, skipping this episode" % (
                        self.indexerid, sickrage.srCore.INDEXER_API(self.indexer).name, season or 0, episode or 0))

        if len(sql_l) > 0:
            main_db.MainDB().mass_upsert(sql_l)
            del sql_l  # cleanup

        # Done updating save last update date
        self.last_update_indexer = date.today().toordinal()

        self.saveToDB()

        return scannedEps

    def getImages(self, fanart=None, poster=None):
        fanart_result = poster_result = banner_result = False
        season_posters_result = season_banners_result = season_all_poster_result = season_all_banner_result = False

        for cur_provider in sickrage.srCore.metadataProviderDict.values():
            # LOGGER.debug(u"Running metadata routines for " + cur_provider.name)

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
            sickrage.srLogger.info(str(self.indexerid) + ": That isn't even a real file dude... " + file)
            return None

        sickrage.srLogger.debug(str(self.indexerid) + ": Creating episode object from " + file)

        try:
            myParser = NameParser(showObj=self, tryIndexers=True)
            parse_result = myParser.parse(file)
        except InvalidNameException:
            sickrage.srLogger.debug("Unable to parse the filename " + file + " into a valid episode")
            return None
        except InvalidShowException:
            sickrage.srLogger.debug("Unable to parse the filename " + file + " into a valid show")
            return None

        if not len(parse_result.episode_numbers):
            sickrage.srLogger.info("parse_result: " + str(parse_result))
            sickrage.srLogger.warning("No episode number found in " + file + ", ignoring it")
            return None

        # for now lets assume that any episode in the show dir belongs to that show
        season = parse_result.season_number if parse_result.season_number is not None else 1
        episodes = parse_result.episode_numbers
        rootEp = None

        sql_l = []
        for curEpNum in episodes:

            episode = int(curEpNum)

            sickrage.srLogger.debug(
                "%s: %s parsed to %s S%02dE%02d" % (self.indexerid, file, self.name, season or 0, episode or 0))

            checkQualityAgain = False
            same_file = False

            curEp = self.getEpisode(season, episode)
            if not curEp:
                try:
                    curEp = self.getEpisode(season, episode, file)
                    if not curEp:
                        raise EpisodeNotFoundException
                except EpisodeNotFoundException:
                    sickrage.srLogger.error(
                        str(self.indexerid) + ": Unable to figure out what this file is, skipping")
                    continue

            else:
                # if there is a new file associated with this ep then re-check the quality
                if curEp.location and os.path.normpath(curEp.location) != os.path.normpath(file):
                    sickrage.srLogger.debug(
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
                sickrage.srLogger.debug("Since this file has been renamed")
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
                    sickrage.srLogger.debug(
                        "STATUS: this ep used to be snatched with quality " + Quality.qualityStrings[
                            oldQuality] +
                        " but a file exists with quality " + Quality.qualityStrings[newQuality] +
                        " so I'm setting the status to DOWNLOADED")
                    newStatus = DOWNLOADED

                # if it was snatched proper and we found a higher quality one then allow the status change
                elif oldStatus == SNATCHED_PROPER and oldQuality < newQuality:
                    sickrage.srLogger.debug(
                        "STATUS: this ep used to be snatched proper with quality " + Quality.qualityStrings[
                            oldQuality] +
                        " but a file exists with quality " + Quality.qualityStrings[newQuality] +
                        " so I'm setting the status to DOWNLOADED")
                    newStatus = DOWNLOADED

                elif oldStatus not in (SNATCHED, SNATCHED_PROPER):
                    newStatus = DOWNLOADED

                if newStatus is not None:
                    with curEp.lock:
                        sickrage.srLogger.debug(
                            "STATUS: we have an associated file, so setting the status from " + str(
                                curEp.status) + " to DOWNLOADED/" + str(
                                Quality.statusFromName(file, anime=self.is_anime)))
                        curEp.status = Quality.compositeStatus(newStatus, newQuality)

            with curEp.lock:
                sql_q = curEp.saveToDB(False)
                if sql_q:
                    sql_l.append(sql_q)
                    del sql_q  # cleanup

        if len(sql_l) > 0:
            main_db.MainDB().mass_upsert(sql_l)
            del sql_l  # cleanup

        # creating metafiles on the root should be good enough
        if rootEp:
            with rootEp.lock:
                rootEp.createMetaFiles()

        return rootEp

    def loadFromDB(self, skipNFO=False):

        sickrage.srLogger.debug(str(self.indexerid) + ": Loading show info from database")

        sqlResults = main_db.MainDB().select("SELECT * FROM tv_shows WHERE indexer_id = ?",
                                             [self.indexerid])

        if len(sqlResults) > 1:
            raise MultipleShowsInDatabaseException()
        elif len(sqlResults) == 0:
            sickrage.srLogger.info(str(self.indexerid) + ": Unable to find the show in the database")
            return False

        self._indexer = tryInt(sqlResults[0][b"indexer"], self.indexer)
        self._name = sqlResults[0][b"show_name"] or self.name
        self._network = sqlResults[0][b"network"] or self.network
        self._genre = sqlResults[0][b"genre"] or self.genre
        self._classification = sqlResults[0][b"classification"] or self.classification
        self._runtime = sqlResults[0][b"runtime"] or self.runtime
        self._status = sqlResults[0][b"status"] or self.status
        self._airs = sqlResults[0][b"airs"] or self.airs
        self._startyear = tryInt(sqlResults[0][b"startyear"], self.startyear)
        self._air_by_date = tryInt(sqlResults[0][b"air_by_date"], self.air_by_date)
        self._anime = tryInt(sqlResults[0][b"anime"], self.anime)
        self._sports = tryInt(sqlResults[0][b"sports"], self.sports)
        self._scene = tryInt(sqlResults[0][b"scene"], self.scene)
        self._subtitles = tryInt(sqlResults[0][b"subtitles"], self.subtitles)
        self._dvdorder = tryInt(sqlResults[0][b"dvdorder"], self.dvdorder)
        self._archive_firstmatch = tryInt(sqlResults[0][b"archive_firstmatch"], self.archive_firstmatch)
        self._quality = tryInt(sqlResults[0][b"quality"], self.quality)
        self._flatten_folders = tryInt(sqlResults[0][b"flatten_folders"], self.flatten_folders)
        self._paused = tryInt(sqlResults[0][b"paused"], self.paused)
        self._lang = sqlResults[0][b"lang"] or self.lang
        self._last_update_indexer = sqlResults[0][b"last_update_indexer"] or self.last_update_indexer
        self._rls_ignore_words = sqlResults[0][b"rls_ignore_words"] or self.rls_ignore_words
        self._rls_require_words = sqlResults[0][b"rls_require_words"] or self.rls_require_words
        self._default_ep_status = tryInt(sqlResults[0][b"default_ep_status"], self.default_ep_status)
        self._imdbid = sqlResults[0][b"imdb_id"] or self.imdbid
        self._tmdbid = sqlResults[0][b"tmdb_id"] or self.tmdbid
        self._location = sqlResults[0][b"location"] or self.location

        if self.is_anime:
            self._release_groups = BlackAndWhiteList(self.indexerid)

        if not skipNFO:
            foundNFO = False

            # Get TMDb_info from database
            sqlResults = main_db.MainDB().select("SELECT * FROM tmdb_info WHERE indexer_id = ?", [self.indexerid])
            if len(sqlResults) == 0:
                sickrage.srLogger.debug(str(self.indexerid) + ": Unable to find TMDb show info in the database")
            else:
                self._tmdb_info = dict(zip(sqlResults[0].keys(), sqlResults[0])) or self.tmdb_info
                foundNFO = True

            # Get IMDb_info from database
            sqlResults = main_db.MainDB().select("SELECT * FROM imdb_info WHERE indexer_id = ?", [self.indexerid])
            if len(sqlResults) == 0:
                sickrage.srLogger.debug(str(self.indexerid) + ": Unable to find IMDb show info in the database")
            else:
                self._imdb_info = dict(zip(sqlResults[0].keys(), sqlResults[0])) or self.imdb_info
                foundNFO = True

            if not foundNFO:
                return False

        return True

    def loadFromIndexer(self, cache=True, tvapi=None, cachedSeason=None):

        if self.indexer is not INDEXER_TVRAGE:
            sickrage.srLogger.debug(
                str(self.indexerid) + ": Loading show info from " + sickrage.srCore.INDEXER_API(self.indexer).name)

            # There's gotta be a better way of doing this but we don't wanna
            # change the cache value elsewhere
            t = tvapi
            if tvapi is None:
                lINDEXER_API_PARMS = sickrage.srCore.INDEXER_API(self.indexer).api_params.copy()

                if not cache:
                    lINDEXER_API_PARMS[b'cache'] = False

                if self.lang:
                    lINDEXER_API_PARMS[b'language'] = self.lang

                if self.dvdorder != 0:
                    lINDEXER_API_PARMS[b'dvdorder'] = True

                t = sickrage.srCore.INDEXER_API(self.indexer).indexer(**lINDEXER_API_PARMS)

            myEp = t[self.indexerid]
            if not myEp:
                return

            try:
                self.name = myEp[b'seriesname'].strip()
            except AttributeError:
                raise indexer_attributenotfound(
                    "Found %s, but attribute 'seriesname' was empty." % (self.indexerid))

            self.classification = safe_getattr(myEp, 'classification', self.classification)
            self.genre = safe_getattr(myEp, 'genre', self.genre)
            self.network = safe_getattr(myEp, 'network', self.network)
            self.runtime = safe_getattr(myEp, 'runtime', self.runtime)
            self.imdbid = safe_getattr(myEp, 'imdb_id', self.imdbid)
            self.tmdbid = safe_getattr(myEp, 'tmdb_id', self.tmdbid)

            try:
                self.airs = safe_getattr(myEp, 'airs_dayofweek') + " " + safe_getattr(myEp, 'airs_time')
            except:
                pass

            try:
                self.startyear = tryInt(str(safe_getattr(myEp, 'firstaired') or date.fromordinal(1)).split('-')[0])
            except:
                pass

            self.status = safe_getattr(myEp, 'status', self.status)
        else:
            sickrage.srLogger.warning(
                str(self.indexerid) + ": NOT loading info from " + sickrage.srCore.INDEXER_API(
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
            self.imdbid = i.search_for_title(self.name).imdb_id or self.imdbid

        if self.imdbid:
            sickrage.srLogger.debug(str(self.indexerid) + ": Loading show info from IMDb")

            imdbTv = i.get_title_by_id(self.imdbid)

            for key in [x for x in imdb_info.keys() if x.replace('_', ' ') in imdbTv.keys()]:
                # Store only the first value for string type
                if isinstance(imdb_info[key], basestring) and isinstance(imdbTv.get(key.replace('_', ' ')), list):
                    imdb_info[key] = imdbTv.get(key.replace('_', ' '))[0]
                else:
                    imdb_info[key] = imdbTv.get(key.replace('_', ' '))

            # Filter only the value
            if imdb_info[b'runtimes']:
                imdb_info[b'runtimes'] = re.search(r'\d+', imdb_info[b'runtimes']).group(0)
            else:
                imdb_info[b'runtimes'] = self.runtime

            if imdb_info[b'akas']:
                imdb_info[b'akas'] = '|'.join(imdb_info[b'akas'])
            else:
                imdb_info[b'akas'] = ''

            # Join all genres in a string
            if imdb_info[b'genres']:
                imdb_info[b'genres'] = '|'.join(imdb_info[b'genres'])
            else:
                imdb_info[b'genres'] = ''

            # Get only the production country certificate if any
            if imdb_info[b'certificates'] and imdb_info[b'countries']:
                dct = {}
                try:
                    for item in imdb_info[b'certificates']:
                        dct[item.split(':')[0]] = item.split(':')[1]

                    imdb_info[b'certificates'] = dct[imdb_info[b'countries']]
                except Exception:
                    imdb_info[b'certificates'] = ''

            else:
                imdb_info[b'certificates'] = ''

            if imdb_info[b'country_codes']:
                imdb_info[b'country_codes'] = '|'.join(imdb_info[b'country_codes'])
            else:
                imdb_info[b'country_codes'] = ''

            imdb_info[b'last_update'] = date.today().toordinal()

            # Rename dict keys without spaces for DB upsert
            self.imdb_info = dict(
                (k.replace(' ', '_'), k(v) if hasattr(v, 'keys') else v) for k, v in imdb_info.iteritems())
            sickrage.srLogger.debug(
                str(self.indexerid) + ": Obtained IMDb info from TMDb ->" + str(self.imdb_info))

    def loadTMDbInfo(self, tmdbapi=None):
        tmdb_info = {'tmdb_id': self.tmdbid,
                     'name': '',
                     'first_air_date': '',
                     'akas': [],
                     'episode_run_time': [],
                     'genres': [],
                     'origin_country': [],
                     'languages': [],
                     'production_companies': [],
                     'popularity': '',
                     'vote_count': '',
                     'last_air_date': ''}

        tmdbsimple.API_KEY = sickrage.srConfig.TMDB_API_KEY
        def _request(self, method, path, params=None, payload=None):
            url = self._get_complete_url(path)
            params = self._get_params(params)

            requests.packages.urllib3.disable_warnings()
            response = requests.request(method, url, params=params, data=json.dumps(payload)
            if payload else payload, headers=self.headers, verify=False)

            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.json()

        tmdbsimple.base.TMDB._request = _request
        if not self.tmdbid:
            tmdb_result = tmdbsimple.Search().tv(query=self.name)['results']
            if len(tmdb_result) > 0:
                self.tmdbid = tmdb_result[0]['id']

        if self.tmdbid:
            tmdb_info[b'tmdb_id'] = self.tmdbid
            tmdbInfo = tmdbsimple.TV(id=self.tmdbid).info()
            sickrage.srLogger.debug(str(self.indexerid) + ": Loading show info from TMDb")
            for key in tmdb_info.keys():
                # Store only the first value for string type
                if isinstance(tmdb_info[key], basestring) and isinstance(tmdbInfo.get(key), list):
                    tmdb_info[key] = tmdbInfo.get(key)[0] or []
                else:
                    tmdb_info[key] = tmdbInfo.get(key) or ''

            # Filter only the value
            tmdb_info[b'episode_run_time'] = re.search(
                r'\d+', str(tmdb_info[b'episode_run_time'])
            ).group(0) or self.runtime

            tmdb_info[b'akas'] = tmdbInfo.get('alternaive_titles', [])
            tmdb_info[b'akas'] = '|'.join([x[b'name'] for x in tmdb_info[b'akas']]) or ''

            tmdb_info[b'origin_country'] = '|'.join(tmdb_info[b'origin_country']) or ''
            tmdb_info[b'genres'] = '|'.join([x[b'name'] for x in tmdb_info[b'genres']]) or ''
            tmdb_info[b'languages'] = '|'.join(tmdb_info[b'languages']) or ''
            tmdb_info[b'last_air_date'] = date.today().toordinal()

            # Get only the production country certificate if any
            if tmdb_info[b'production_companies'] and tmdb_info[b'production_companies']:
                try:
                    dct = {}
                    for item in tmdb_info[b'production_companies']:
                        dct[item.split(':')[0]] = item.split(':')[1]

                    tmdb_info[b'production_companies'] = dct[tmdb_info[b'production_companies']]
                except Exception:
                    tmdb_info[b'production_companies'] = ''
            else:
                tmdb_info[b'production_companies'] = ''

            # Rename dict keys without spaces for DB upsert
            self.tmdb_info = dict(
                (k.replace(' ', '_'), k(v) if hasattr(v, 'keys') else v) for k, v in tmdb_info.items())
            sickrage.srLogger.debug(str(self.indexerid) + ": Obtained info from TMDb ->" + str(self.tmdb_info))

    def nextEpisode(self):
        sickrage.srLogger.debug(str(self.indexerid) + ": Finding the episode which airs next")

        curDate = date.today().toordinal()
        if not self.nextaired or self.nextaired and curDate > self.nextaired:

            sqlResults = main_db.MainDB().select(
                "SELECT airdate, season, episode FROM tv_episodes WHERE showid = ? AND airdate >= ? AND status IN (?,?) ORDER BY airdate ASC LIMIT 1",
                [self.indexerid, date.today().toordinal(), UNAIRED, WANTED])

            if sqlResults is None or len(sqlResults) == 0:
                sickrage.srLogger.debug(
                    str(self.indexerid) + ": No episode found... need to implement a show status")
                self.nextaired = ""
            else:
                sickrage.srLogger.debug("%s: Found episode S%02dE%02d" % (
                    self.indexerid, sqlResults[0][b"season"] or 0, sqlResults[0][b"episode"] or 0))
                self.nextaired = sqlResults[0][b'airdate']

        return self.nextaired

    def deleteShow(self, full=False):

        main_db.MainDB().mass_action([["DELETE FROM tv_episodes WHERE showid = ?", [self.indexerid]],
                                      ["DELETE FROM tv_shows WHERE indexer_id = ?", [self.indexerid]],
                                      ["DELETE FROM imdb_info WHERE indexer_id = ?", [self.indexerid]],
                                      ["DELETE FROM xem_refresh WHERE indexer_id = ?", [self.indexerid]],
                                      ["DELETE FROM scene_numbering WHERE indexer_id = ?", [self.indexerid]]])

        action = ('delete', 'trash')[sickrage.srConfig.TRASH_REMOVE_SHOW]

        # remove self from show list
        sickrage.srCore.SHOWLIST = [x for x in sickrage.srCore.SHOWLIST if int(x.indexerid) != self.indexerid]

        # clear the cache
        image_cache_dir = os.path.join(sickrage.srConfig.CACHE_DIR, 'images')
        for cache_file in glob.glob(os.path.join(image_cache_dir, str(self.indexerid) + '.*')):
            sickrage.srLogger.info('Attempt to %s cache file %s' % (action, cache_file))
            try:
                if sickrage.srConfig.TRASH_REMOVE_SHOW:
                    send2trash.send2trash(cache_file)
                else:
                    os.remove(cache_file)

            except OSError as e:
                sickrage.srLogger.warning('Unable to %s %s: %s / %s' % (action, cache_file, repr(e), str(e)))

        # remove entire show folder
        if full:
            try:
                sickrage.srLogger.info('Attempt to %s show folder %s' % (action, self.location))
                # check first the read-only attribute
                file_attribute = os.stat(self.location)[0]
                if not file_attribute & stat.S_IWRITE:
                    # File is read-only, so make it writeable
                    sickrage.srLogger.debug(
                        'Attempting to make writeable the read only folder %s' % self.location)
                    try:
                        os.chmod(self.location, stat.S_IWRITE)
                    except Exception:
                        sickrage.srLogger.warning('Unable to change permissions of %s' % self.location)

                if sickrage.srConfig.TRASH_REMOVE_SHOW:
                    send2trash.send2trash(self.location)
                else:
                    removetree(self.location)

                sickrage.srLogger.info('%s show folder %s' %
                                       (('Deleted', 'Trashed')[sickrage.srConfig.TRASH_REMOVE_SHOW],
                                        self.location))

            except ShowDirectoryNotFoundException:
                sickrage.srLogger.warning(
                    "Show folder does not exist, no need to %s %s" % (action, self.location))
            except OSError as e:
                sickrage.srLogger.warning('Unable to %s %s: %s / %s' % (action, self.location, repr(e), str(e)))

        if sickrage.srConfig.USE_TRAKT and sickrage.srConfig.TRAKT_SYNC_WATCHLIST:
            sickrage.srLogger.debug(
                "Removing show: indexerid " + str(self.indexerid) + ", Title " + str(
                    self.name) + " from Watchlist")
            sickrage.srCore.NOTIFIERS.trakt_notifier.update_watchlist(self, update="remove")

    def populateCache(self):
        cache_inst = image_cache.ImageCache()

        sickrage.srLogger.debug("Checking & filling cache for show " + self.name)
        cache_inst.fill_cache(self)

    def refreshDir(self):

        # make sure the show dir is where we think it is unless dirs are created on the fly
        if not os.path.isdir(self.location) and not sickrage.srConfig.CREATE_MISSING_SHOW_DIRS:
            return False

        # load from dir
        self.loadEpisodesFromDir()

        # run through all locations from DB, check that they exist
        sickrage.srLogger.debug(str(self.indexerid) + ": Loading all episodes with a location from the database")

        sqlResults = main_db.MainDB().select("SELECT * FROM tv_episodes WHERE showid = ? AND location != ''",
                                             [self.indexerid])

        sql_l = []
        for ep in sqlResults:
            curLoc = os.path.normpath(ep[b"location"])
            season = int(ep[b"season"])
            episode = int(ep[b"episode"])

            try:
                curEp = self.getEpisode(season, episode)
                if not curEp:
                    raise EpisodeDeletedException
            except EpisodeDeletedException:
                sickrage.srLogger.debug(
                    "The episode was deleted while we were refreshing it, moving on to the next one")
                continue

            # if the path doesn't exist or if it's not in our show dir
            if not os.path.isfile(curLoc) or not os.path.normpath(curLoc).startswith(
                    os.path.normpath(self.location)):

                # check if downloaded files still exist, update our data if this has changed
                if not sickrage.srConfig.SKIP_REMOVED_FILES:
                    with curEp.lock:
                        # if it used to have a file associated with it and it doesn't anymore then set it to sickrage.EP_DEFAULT_DELETED_STATUS
                        if curEp.location and curEp.status in Quality.DOWNLOADED:

                            if sickrage.srConfig.EP_DEFAULT_DELETED_STATUS == ARCHIVED:
                                _, oldQuality = Quality.splitCompositeStatus(curEp.status)
                                new_status = Quality.compositeStatus(ARCHIVED, oldQuality)
                            else:
                                new_status = sickrage.srConfig.EP_DEFAULT_DELETED_STATUS

                            sickrage.srLogger.debug(
                                "%s: Location for S%02dE%02d doesn't exist, removing it and changing our status to %s" %
                                (self.indexerid, season or 0, episode or 0, statusStrings[new_status]))
                            curEp.status = new_status
                            curEp.subtitles = list()
                            curEp.subtitles_searchcount = 0
                            curEp.subtitles_lastsearch = str(datetime.min)
                        curEp.location = ''
                        curEp.hasnfo = False
                        curEp.hastbn = False
                        curEp.release_name = ''

                        sql_q = curEp.saveToDB(False)
                        if sql_q:
                            sql_l.append(sql_q)
                            del sql_q  # cleanup
            else:
                # the file exists, set its modify file stamp
                if sickrage.srConfig.AIRDATE_EPISODES:
                    with curEp.lock:
                        curEp.airdateModifyStamp()

        if len(sql_l) > 0:
            main_db.MainDB().mass_upsert(sql_l)
            del sql_l  # cleanup

    def downloadSubtitles(self, force=False):
        # TODO: Add support for force option
        if not os.path.isdir(self.location):
            sickrage.srLogger.debug(str(self.indexerid) + ": Show dir doesn't exist, can't download subtitles")
            return

        sickrage.srLogger.debug("%s: Downloading subtitles" % self.indexerid)

        try:
            episodes = self.getAllEpisodes(has_location=True)
            if not episodes:
                sickrage.srLogger.debug(
                    "%s: No episodes to download subtitles for %s" % (self.indexerid, self.name))
                return

            for episode in episodes:
                episode.downloadSubtitles(force=force)

        except Exception:
            sickrage.srLogger.debug(
                "%s: Error occurred when downloading subtitles for %s" % (self.indexerid, self.name))
            sickrage.srLogger.error(traceback.format_exc())

    def saveToDB(self, forceSave=False):

        if not self.dirty and not forceSave:
            return

        sickrage.srLogger.debug("%i: Saving to database: %s" % (self.indexerid, self.name))

        controlValueDict = {"indexer_id": self.indexerid}
        newValueDict = {"indexer": self.indexer,
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
                        "tmdb_id": self.tmdbid,
                        "last_update_indexer": self.last_update_indexer,
                        "rls_ignore_words": self.rls_ignore_words,
                        "rls_require_words": self.rls_require_words,
                        "default_ep_status": self.default_ep_status}

        main_db.MainDB().upsert("tv_shows", newValueDict, controlValueDict)

        update_anime_support()

        if self.imdbid and self.imdb_info:
            controlValueDict = {"indexer_id": self.indexerid}
            newValueDict = self.imdb_info
            main_db.MainDB().upsert("imdb_info", newValueDict, controlValueDict)

        if self.tmdbid and self.tmdb_info:
            controlValueDict = {"indexer_id": self.indexerid}
            newValueDict = self.tmdb_info
            main_db.MainDB().upsert("tmdb_info", newValueDict, controlValueDict)

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
                sickrage.srLogger.info("Bad quality value: " + str(quality))

        result = re.sub(', $', '', result)

        if not len(result):
            result = 'None'

        return result

    def wantEpisode(self, season, episode, quality, manualSearch=False, downCurQuality=False):

        sickrage.srLogger.debug("Checking if found episode %s S%02dE%02d is wanted at quality %s" % (
            self.name, season or 0, episode or 0, Quality.qualityStrings[quality]))

        # if the quality isn't one we want under any circumstances then just say no
        anyQualities, bestQualities = Quality.splitQuality(self.quality)
        sickrage.srLogger.debug("Any,Best = [ %s ] [ %s ] Found = [ %s ]" %
                                (self.qualitiesToString(anyQualities),
                                 self.qualitiesToString(bestQualities),
                                 self.qualitiesToString([quality])))

        if quality not in anyQualities + bestQualities or quality is UNKNOWN:
            sickrage.srLogger.debug("Don't want this quality, ignoring found episode")
            return False

        sqlResults = main_db.MainDB().select(
            "SELECT status FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?",
            [self.indexerid, season, episode])

        if not sqlResults or not len(sqlResults):
            sickrage.srLogger.debug("Unable to find a matching episode in database, ignoring found episode")
            return False

        epStatus = int(sqlResults[0][b"status"])
        epStatus_text = statusStrings[epStatus]

        sickrage.srLogger.debug("Existing episode status: " + str(epStatus) + " (" + epStatus_text + ")")

        # if we know we don't want it then just say no
        if epStatus in Quality.ARCHIVED + [UNAIRED, SKIPPED, IGNORED] and not manualSearch:
            sickrage.srLogger.debug(
                "Existing episode status is unaired/skipped/ignored/archived, ignoring found episode")
            return False

        curStatus, curQuality = Quality.splitCompositeStatus(epStatus)

        # if it's one of these then we want it as long as it's in our allowed initial qualities
        if epStatus in (WANTED, SKIPPED, UNKNOWN):
            sickrage.srLogger.debug("Existing episode status is wanted/skipped/unknown, getting found episode")
            return True
        elif manualSearch:
            if (downCurQuality and quality >= curQuality) or (not downCurQuality and quality > curQuality):
                sickrage.srLogger.debug(
                    "Usually ignoring found episode, but forced search allows the quality, getting found episode")
                return True

        # if we are re-downloading then we only want it if it's in our bestQualities list and better than what we have, or we only have one bestQuality and we do not have that quality yet
        if epStatus in Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_PROPER and quality in bestQualities and (
                        quality > curQuality or curQuality not in bestQualities):
            sickrage.srLogger.debug(
                "Episode already exists but the found episode quality is wanted more, getting found episode")
            return True
        elif curQuality == UNKNOWN and manualSearch:
            sickrage.srLogger.debug("Episode already exists but quality is Unknown, getting found episode")
            return True
        else:
            sickrage.srLogger.debug(
                "Episode already exists and the found episode has same/lower quality, ignoring found episode")

        sickrage.srLogger.debug("None of the conditions were met, ignoring found episode")
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
        for indexer in sickrage.srCore.INDEXER_API().indexers:
            mapped[indexer] = self.indexerid if int(indexer) == int(self.indexer) else 0

        sqlResults = main_db.MainDB().select(
            "SELECT * FROM indexer_mapping WHERE indexer_id = ? AND indexer = ?",
            [self.indexerid, self.indexer])

        # for each mapped entry
        for curResult in sqlResults:
            nlist = [i for i in curResult if i is not None]
            # Check if its mapped with both tvdb and tvrage.
            if len(nlist) >= 4:
                sickrage.srLogger.debug("Found indexer mapping in cache for show: " + self.name)
                mapped[int(curResult[b'mindexer'])] = int(curResult[b'mindexer_id'])
                return mapped
        else:
            sql_l = []
            for indexer in sickrage.srCore.INDEXER_API().indexers:
                if indexer == self.indexer:
                    mapped[indexer] = self.indexerid
                    continue

                lINDEXER_API_PARMS = sickrage.srCore.INDEXER_API(indexer).api_params.copy()
                lINDEXER_API_PARMS[b'custom_ui'] = ShowListUI
                t = sickrage.srCore.INDEXER_API(indexer).indexer(**lINDEXER_API_PARMS)

                try:
                    mapped_show = t[self.name]
                except Exception:
                    sickrage.srLogger.debug("Unable to map " + sickrage.srCore.INDEXER_API(
                        self.indexer).name + "->" + sickrage.srCore.INDEXER_API(
                        indexer).name + " for show: " + self.name + ", skipping it")
                    continue

                if mapped_show and len(mapped_show) == 1:
                    sickrage.srLogger.debug("Mapping " + sickrage.srCore.INDEXER_API(
                        self.indexer).name + "->" + sickrage.srCore.INDEXER_API(
                        indexer).name + " for show: " + self.name)

                    mapped[indexer] = int(mapped_show[0][b'id'])

                    sickrage.srLogger.debug("Adding indexer mapping to DB for show: " + self.name)

                    sql_l.append([
                        "INSERT OR IGNORE INTO indexer_mapping (indexer_id, indexer, mindexer_id, mindexer) VALUES (?,?,?,?)",
                        [self.indexerid, self.indexer, int(mapped_show[0][b'id']), indexer]])

            if len(sql_l) > 0:
                main_db.MainDB().mass_action(sql_l)
                del sql_l  # cleanup

        return mapped

    def __getstate__(self):
        d = dict(self.__dict__)
        del d[b'lock']
        return d

    def __setstate__(self, d):
        d[b'lock'] = threading.Lock()
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
        today = str(date.today().toordinal())

        downloaded_status = Quality.DOWNLOADED + Quality.ARCHIVED
        snatched_status = Quality.SNATCHED + Quality.SNATCHED_PROPER
        total_status = [SKIPPED, WANTED]

        results = main_db.MainDB().select(
            'SELECT airdate, status '
            'FROM tv_episodes '
            'WHERE season > 0 '
            'AND episode > 0 '
            'AND airdate > 1'
        )

        stats = {
            'episodes': {
                'downloaded': 0,
                'snatched': 0,
                'total': 0,
            },
            'shows': {
                'active': len([show for show in shows if show.paused == 0 and show.status == 'Continuing']),
                'total': len(shows),
            },
        }

        for result in results:
            if result[b'status'] in downloaded_status:
                stats[b'episodes'][b'downloaded'] += 1
                stats[b'episodes'][b'total'] += 1
            elif result[b'status'] in snatched_status:
                stats[b'episodes'][b'snatched'] += 1
                stats[b'episodes'][b'total'] += 1
            elif result[b'airdate'] <= today and result[b'status'] in total_status:
                stats[b'episodes'][b'total'] += 1

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
