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
import shutil
import stat
import threading
import traceback

import send2trash
from CodernityDB.database import RecordNotFound, RevConflict
from unidecode import unidecode

import sickrage
from sickrage.core.api.imdb import IMDbAPI
from sickrage.core.blackandwhitelist import BlackAndWhiteList
from sickrage.core.caches import image_cache
from sickrage.core.classes import ShowListUI
from sickrage.core.common import Quality, SKIPPED, WANTED, UNKNOWN, DOWNLOADED, IGNORED, SNATCHED, SNATCHED_PROPER, \
    UNAIRED, ARCHIVED, statusStrings, Overview
from sickrage.core.exceptions import ShowNotFoundException, \
    EpisodeNotFoundException, EpisodeDeletedException, MultipleShowsInDatabaseException, MultipleShowObjectsException
from sickrage.core.helpers import list_media_files, is_media_file, try_int, safe_getattr, findCertainShow
from sickrage.core.nameparser import NameParser, InvalidNameException, InvalidShowException
from sickrage.indexers import IndexerApi
from sickrage.indexers.config import INDEXER_TVRAGE
from sickrage.indexers.exceptions import indexer_attributenotfound


class TVShow(object):
    def __init__(self, indexer, indexerid, lang=""):
        self.lock = threading.Lock()

        self._indexerid = int(indexerid)
        self._indexer = int(indexer)
        self._name = ""
        self._imdbid = ""
        self._network = ""
        self._genre = ""
        self._overview = ""
        self._classification = 'Scripted'
        self._runtime = 0
        self._imdb_info = {}
        self._quality = try_int(sickrage.app.config.quality_default, UNKNOWN)
        self._flatten_folders = int(sickrage.app.config.flatten_folders_default)
        self._status = "Unknown"
        self._airs = ""
        self._startyear = 0
        self._paused = 0
        self._air_by_date = 0
        self._subtitles = int(sickrage.app.config.subtitles_default)
        self._subtitles_sr_metadata = 0
        self._dvdorder = 0
        self._skip_downloaded = 0
        self._lang = lang
        self._last_update = datetime.datetime.now().toordinal()
        self._last_refresh = datetime.datetime.now().toordinal()
        self._sports = 0
        self._anime = 0
        self._scene = 0
        self._rls_ignore_words = ""
        self._rls_require_words = ""
        self._default_ep_status = SKIPPED
        self._notify_list = ""
        self._search_delay = 0
        self.dirty = True

        self._location = ""
        self._next_aired = ""
        self.episodes = {}
        self.release_groups = None

        if findCertainShow(self.indexerid) is not None:
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
    def overview(self):
        return self._overview

    @overview.setter
    def overview(self, value):
        if self._overview != value:
            self.dirty = True
        self._overview = value

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
    def skip_downloaded(self):
        return self._skip_downloaded

    @skip_downloaded.setter
    def skip_downloaded(self, value):
        if self._skip_downloaded != value:
            self.dirty = True
        self._skip_downloaded = value

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
    def notify_list(self):
        return self._notify_list

    @notify_list.setter
    def notify_list(self, value):
        if self._notify_list != value:
            self.dirty = True
        self._notify_list = value

    @property
    def search_delay(self):
        return self._search_delay

    @search_delay.setter
    def search_delay(self, value):
        if self._search_delay != value:
            self.dirty = True
        self._search_delay = value

    @property
    def subtitles_sr_metadata(self):
        return self._subtitles_sr_metadata

    @subtitles_sr_metadata.setter
    def subtitles_sr_metadata(self, value):
        if self._subtitles_sr_metadata != value:
            self.dirty = True
        self._subtitles_sr_metadata = value

    @property
    def is_anime(self):
        return int(self.anime) > 0

    @property
    def is_sports(self):
        return int(self.sports) > 0

    @property
    def is_scene(self):
        return int(self.scene) > 0

    @property
    def network_logo_name(self):
        return unidecode(self.network).lower()

    @property
    def next_aired(self):
        if not self.paused:
            curDate = datetime.date.today()

            if not self._next_aired or self._next_aired and curDate.toordinal() > self._next_aired:
                dbData = sorted([x for x in sickrage.app.main_db.get_many('tv_episodes', self.indexerid)
                                 if x['airdate'] >= curDate.toordinal()
                                 and x['status'] in (UNAIRED, WANTED)], key=lambda d: d['airdate'])

                self._next_aired = dbData[0]['airdate'] if dbData else ''
        return self._next_aired

    @property
    def show_size(self):
        total_size = 0
        for x in sickrage.app.main_db.get_many('tv_episodes', self.indexerid):
            total_size += x['file_size']
        return total_size

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, new_location):
        if sickrage.app.config.add_shows_wo_dir or os.path.isdir(new_location):
            sickrage.app.log.debug("Show location set to " + new_location)
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
        for x in sickrage.app.main_db.get_many('tv_episodes', self.indexerid):
            if (season and x['season'] != season) or (has_location and x['location'] == ''):
                continue

            results += [x]

        ep_list = []
        for cur_result in sickrage.app.main_db.get_many('tv_episodes', self.indexerid):
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

                    related_eps_result = sorted([x for x in sickrage.app.main_db.get_many('tv_episodes', self.indexerid)
                                                 if x['season'] == cur_ep.season
                                                 and x['location'] == cur_ep.location
                                                 and x['episode'] != cur_ep.episode], key=lambda d: d['episode'])

                    for cur_related_ep in related_eps_result:
                        related_ep = self.getEpisode(int(cur_related_ep["season"]), int(cur_related_ep["episode"]))
                        if related_ep and related_ep not in cur_ep.relatedEps:
                            cur_ep.relatedEps.append(related_ep)

            ep_list.append(cur_ep)

        return ep_list

    def getEpisode(self, season=None, episode=None, file=None, noCreate=False, absolute_number=None, ):

        # if we get an anime get the real season and episode
        if self.is_anime and absolute_number is not None and not season and not episode:
            dbData = [x for x in sickrage.app.main_db.get_many('tv_episodes', self.indexerid)
                      if x['absolute_number'] == absolute_number and x['season'] != 0]

            if len(dbData) == 1:
                episode = int(dbData[0]["episode"])
                season = int(dbData[0]["season"])
                sickrage.app.log.debug(
                    "Found episode by absolute_number %s which is S%02dE%02d" % (
                        absolute_number, season or 0, episode or 0))
            elif len(dbData) > 1:
                sickrage.app.log.error("Multiple entries for absolute number: " + str(
                    absolute_number) + " in show: " + self.name + " found ")
                return None
            else:
                sickrage.app.log.debug(
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
        dbData = sorted((x for x in sickrage.app.main_db.get_many('tv_episodes', self.indexerid)
                         if x['season'] > 0 and x['airdate'] > 1 and x['status'] == 1),
                        key=lambda d: d['airdate'], reverse=True)

        if dbData:
            last_airdate = datetime.date.fromordinal(dbData[0]['airdate'])
            if (update_date - graceperiod) <= last_airdate <= (update_date + graceperiod):
                return True

        # get next upcoming UNAIRED episode to compare against today + graceperiod
        dbData = sorted((x for x in sickrage.app.main_db.get_many('tv_episodes', self.indexerid)
                         if x['season'] > 0 and x['airdate'] > 1 and x['status'] == 1), key=lambda d: d['airdate'])

        if dbData:
            next_airdate = datetime.date.fromordinal(dbData[0]['airdate'])
            if next_airdate <= (update_date + graceperiod):
                return True

        # in the first year after ended (last airdate), update every 30 days
        if (update_date - last_airdate) < datetime.timedelta(days=450) and (
                update_date - datetime.date.fromordinal(self.last_update)) > datetime.timedelta(days=30):
            return True

        return False

    def writeShowNFO(self, force=False):

        result = False

        if not os.path.isdir(self.location):
            sickrage.app.log.info(str(self.indexerid) + ": Show dir doesn't exist, skipping NFO generation")
            return False

        sickrage.app.log.debug(str(self.indexerid) + ": Writing NFOs for show")
        for cur_provider in sickrage.app.metadata_providers.values():
            result = cur_provider.create_show_metadata(self, force) or result

        return result

    def writeMetadata(self, show_only=False, force=False):

        if not os.path.isdir(self.location):
            sickrage.app.log.info(str(self.indexerid) + ": Show dir doesn't exist, skipping NFO generation")
            return

        self.getImages()

        self.writeShowNFO(force)

        if not show_only:
            self.writeEpisodeNFOs(force)

    def writeEpisodeNFOs(self, force=False):

        if not os.path.isdir(self.location):
            sickrage.app.log.info(str(self.indexerid) + ": Show dir doesn't exist, skipping NFO generation")
            return

        sickrage.app.log.debug(str(self.indexerid) + ": Writing NFOs for all episodes")

        for dbData in sickrage.app.main_db.get_many('tv_episodes', self.indexerid):
            if dbData['location'] == '':
                continue

            sickrage.app.log.debug(str(self.indexerid) + ": Retrieving/creating episode S%02dE%02d" % (
                dbData["season"] or 0, dbData["episode"] or 0))

            self.getEpisode(dbData["season"], dbData["episode"]).createMetaFiles(force)

    # find all media files in the show folder and create episodes for as many as possible
    def loadEpisodesFromDir(self):
        if not os.path.isdir(self.location):
            sickrage.app.log.debug(
                str(self.indexerid) + ": Show dir doesn't exist, not loading episodes from disk")
            return

        sickrage.app.log.debug(
            str(self.indexerid) + ": Loading all episodes from the show directory " + self.location)

        # get file list
        mediaFiles = list_media_files(self.location)

        # create TVEpisodes from each media file (if possible)
        for mediaFile in mediaFiles:
            curEpisode = None

            sickrage.app.log.debug(str(self.indexerid) + ": Creating episode from " + mediaFile)
            try:
                curEpisode = self.make_ep_from_file(os.path.join(self.location, mediaFile))
            except (ShowNotFoundException, EpisodeNotFoundException) as e:
                sickrage.app.log.warning("Episode " + mediaFile + " returned an exception: {}".format(e))
            except EpisodeDeletedException:
                sickrage.app.log.debug("The episode deleted itself when I tried making an object for it")

            # skip to next episode?
            if not curEpisode:
                continue

            # see if we should save the release name in the db
            ep_file_name = os.path.basename(curEpisode.location)
            ep_file_name = os.path.splitext(ep_file_name)[0]

            try:
                parse_result = NameParser(False, showObj=self).parse(ep_file_name)
            except (InvalidNameException, InvalidShowException):
                parse_result = None

            if ' ' not in ep_file_name and parse_result and parse_result.release_group:
                sickrage.app.log.debug(
                    "Name " + ep_file_name + " gave release group of " + parse_result.release_group + ", seems valid")
                curEpisode.release_name = ep_file_name

            # store the reference in the show
            if self.subtitles and sickrage.app.config.use_subtitles:
                try:
                    curEpisode.refreshSubtitles()
                except Exception:
                    sickrage.app.log.error("%s: Could not refresh subtitles" % self.indexerid)
                    sickrage.app.log.debug(traceback.format_exc())

            curEpisode.saveToDB()

    def loadEpisodesFromDB(self):
        scannedEps = {}

        sickrage.app.log.debug("{}: Loading all episodes for show from DB".format(self.indexerid))

        for dbData in sickrage.app.main_db.get_many('tv_episodes', self.indexerid):
            deleteEp = False

            curSeason = int(dbData["season"])
            curEpisode = int(dbData["episode"])

            if curSeason not in scannedEps:
                scannedEps[curSeason] = {}

            try:
                sickrage.app.log.debug(
                    "{}: Loading episode S{:02d}E{:02d} info".format(self.indexerid, curSeason or 0, curEpisode or 0))

                if deleteEp:
                    self.getEpisode(curSeason, curEpisode).deleteEpisode()

                scannedEps[curSeason][curEpisode] = True
            except EpisodeDeletedException:
                continue

        return scannedEps

    def loadEpisodesFromIndexer(self, cache=True):
        scannedEps = {}

        lINDEXER_API_PARMS = IndexerApi(self.indexer).api_params.copy()
        lINDEXER_API_PARMS['cache'] = cache

        lINDEXER_API_PARMS['language'] = self.lang or sickrage.app.config.indexer_default_language

        if self.dvdorder != 0:
            lINDEXER_API_PARMS['dvdorder'] = True

        t = IndexerApi(self.indexer).indexer(**lINDEXER_API_PARMS)
        showObj = t[self.indexerid]

        sickrage.app.log.debug(
            str(self.indexerid) + ": Loading all episodes from " + IndexerApi(
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
                    sickrage.app.log.info(
                        "%s: %s object for S%02dE%02d is incomplete, skipping this episode" % (
                            self.indexerid, IndexerApi(self.indexer).name, season or 0, episode or 0))
                    continue
                else:
                    try:
                        curEp.loadFromIndexer(tvapi=t)
                    except EpisodeDeletedException:
                        sickrage.app.log.info("The episode was deleted, skipping the rest of the load")
                        continue

                with curEp.lock:
                    sickrage.app.log.debug("%s: Loading info from %s for episode S%02dE%02d" % (
                        self.indexerid, IndexerApi(self.indexer).name, season or 0, episode or 0))

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

        for cur_provider in sickrage.app.metadata_providers.values():
            fanart_result = cur_provider.create_fanart(self) or fanart_result
            poster_result = cur_provider.create_poster(self) or poster_result
            banner_result = cur_provider.create_banner(self, ) or banner_result

            season_posters_result = cur_provider.create_season_posters(self) or season_posters_result
            season_banners_result = cur_provider.create_season_banners(self) or season_banners_result
            season_all_poster_result = cur_provider.create_season_all_poster(self) or season_all_poster_result
            season_all_banner_result = cur_provider.create_season_all_banner(self) or season_all_banner_result

        return fanart_result or poster_result or banner_result or season_posters_result or season_banners_result or season_all_poster_result or season_all_banner_result

    # make a TVEpisode object from a media file
    def make_ep_from_file(self, filename):
        if not os.path.isfile(filename):
            sickrage.app.log.info(str(self.indexerid) + ": That isn't even a real file dude... " + filename)
            return None

        sickrage.app.log.debug(str(self.indexerid) + ": Creating episode object from " + filename)

        try:
            parse_result = NameParser(showObj=self).parse(filename, skip_scene_detection=True)
        except InvalidNameException:
            sickrage.app.log.debug("Unable to parse the filename " + filename + " into a valid episode")
            return None
        except InvalidShowException:
            sickrage.app.log.debug("Unable to parse the filename " + filename + " into a valid show")
            return None

        if not len(parse_result.episode_numbers):
            sickrage.app.log.info("parse_result: " + str(parse_result))
            sickrage.app.log.warning("No episode number found in " + filename + ", ignoring it")
            return None

        # for now lets assume that any episode in the show dir belongs to that show
        season = parse_result.season_number if parse_result.season_number is not None else 1
        rootEp = None

        for curEpNum in parse_result.episode_numbers:
            episode = int(curEpNum)

            sickrage.app.log.debug(
                "%s: %s parsed to %s S%02dE%02d" % (self.indexerid, filename, self.name, season or 0, episode or 0))

            checkQualityAgain = False
            same_file = False

            curEp = self.getEpisode(season, episode)
            if not curEp:
                try:
                    curEp = self.getEpisode(season, episode, filename)
                except EpisodeNotFoundException:
                    sickrage.app.log.error(
                        str(self.indexerid) + ": Unable to figure out what this file is, skipping")
                    continue

            else:
                # if there is a new file associated with this ep then re-check the quality
                if curEp.location and os.path.normpath(curEp.location) != os.path.normpath(filename):
                    sickrage.app.log.debug("The old episode had a different file associated with it, I will re-check "
                                           "the quality based on the new filename " + filename)
                    checkQualityAgain = True

                with curEp.lock:
                    # if the sizes are the same then it's probably the same file
                    old_size = curEp.file_size
                    curEp.location = filename
                    same_file = old_size and curEp.file_size == old_size
                    curEp.checkForMetaFiles()

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
                newQuality = Quality.nameQuality(filename, self.is_anime)
                sickrage.app.log.debug("Since this file has been renamed")

                with curEp.lock:
                    curEp.status = Quality.compositeStatus(DOWNLOADED, newQuality)

            # check for status/quality changes as long as it's a new file
            elif not same_file and is_media_file(
                    filename) and curEp.status not in Quality.DOWNLOADED + Quality.ARCHIVED + [IGNORED]:
                oldStatus, oldQuality = Quality.splitCompositeStatus(curEp.status)
                newQuality = Quality.nameQuality(filename, self.is_anime)

                newStatus = None

                # if it was snatched and now exists then set the status correctly
                if oldStatus == SNATCHED and oldQuality <= newQuality:
                    sickrage.app.log.debug(
                        "STATUS: this ep used to be snatched with quality " + Quality.qualityStrings[
                            oldQuality] +
                        " but a file exists with quality " + Quality.qualityStrings[newQuality] +
                        " so I'm setting the status to DOWNLOADED")
                    newStatus = DOWNLOADED

                # if it was snatched proper and we found a higher quality one then allow the status change
                elif oldStatus == SNATCHED_PROPER and oldQuality < newQuality:
                    sickrage.app.log.debug(
                        "STATUS: this ep used to be snatched proper with quality " + Quality.qualityStrings[
                            oldQuality] +
                        " but a file exists with quality " + Quality.qualityStrings[newQuality] +
                        " so I'm setting the status to DOWNLOADED")
                    newStatus = DOWNLOADED

                elif oldStatus not in (SNATCHED, SNATCHED_PROPER):
                    newStatus = DOWNLOADED

                if newStatus is not None:
                    with curEp.lock:
                        sickrage.app.log.debug(
                            "STATUS: we have an associated file, so setting the status from " + str(
                                curEp.status) + " to DOWNLOADED/" + str(
                                Quality.statusFromName(filename, anime=self.is_anime)))
                        curEp.status = Quality.compositeStatus(newStatus, newQuality)

            with curEp.lock:
                curEp.saveToDB()

        # creating metafiles on the root should be good enough
        if rootEp:
            with rootEp.lock:
                rootEp.createMetaFiles()

        return rootEp

    def loadFromDB(self, skipNFO=False):
        sickrage.app.log.debug(str(self.indexerid) + ": Loading show info from database")

        dbData = [x for x in sickrage.app.main_db.get_many('tv_shows', self.indexerid)]

        if len(dbData) > 1:
            raise MultipleShowsInDatabaseException()
        elif len(dbData) == 0:
            return ShowNotFoundException()

        self._indexer = try_int(dbData[0]["indexer"], self.indexer)
        self._name = dbData[0].get("show_name", self.name)
        self._network = dbData[0].get("network", self.network)
        self._genre = dbData[0].get("genre", self.genre)
        self._overview = dbData[0].get("overview", self.overview)
        self._classification = dbData[0].get("classification", self.classification)
        self._runtime = dbData[0].get("runtime", self.runtime)
        self._status = dbData[0].get("status", self.status)
        self._airs = dbData[0].get("airs", self.airs)
        self._startyear = try_int(dbData[0]["startyear"], self.startyear)
        self._air_by_date = try_int(dbData[0]["air_by_date"], self.air_by_date)
        self._anime = try_int(dbData[0]["anime"], self.anime)
        self._sports = try_int(dbData[0]["sports"], self.sports)
        self._scene = try_int(dbData[0]["scene"], self.scene)
        self._subtitles = try_int(dbData[0]["subtitles"], self.subtitles)
        self._subtitles_sr_metadata = dbData[0].get("subtitles_sr_metadata", self.subtitles_sr_metadata)
        self._dvdorder = try_int(dbData[0]["dvdorder"], self.dvdorder)
        self._skip_downloaded = try_int(dbData[0]["skip_downloaded"], self.skip_downloaded)
        self._quality = try_int(dbData[0]["quality"], self.quality)
        self._flatten_folders = try_int(dbData[0]["flatten_folders"], self.flatten_folders)
        self._paused = try_int(dbData[0]["paused"], self.paused)
        self._lang = dbData[0].get("lang", self.lang)
        self._last_update = dbData[0].get("last_update", self.last_update)
        self._last_refresh = dbData[0].get("last_refresh", self.last_refresh)
        self._rls_ignore_words = dbData[0].get("rls_ignore_words", self.rls_ignore_words)
        self._rls_require_words = dbData[0].get("rls_require_words", self.rls_require_words)
        self._default_ep_status = try_int(dbData[0]["default_ep_status"], self.default_ep_status)
        self._notify_list = dbData[0].get("notify_list", self.notify_list)
        self._search_delay = dbData[0].get("search_delay", self.search_delay)
        self._imdbid = dbData[0].get("imdb_id", self.imdbid)
        self._location = dbData[0].get("location", self.location)

        if self.is_anime:
            self.release_groups = BlackAndWhiteList(self.indexerid)

        if not skipNFO:
            try:
                # Get IMDb_info from database
                self._imdb_info = sickrage.app.main_db.get('imdb_info', self.indexerid)
            except RecordNotFound:
                pass

    def loadFromIndexer(self, cache=True, tvapi=None, cachedSeason=None):

        if self.indexer is not INDEXER_TVRAGE:
            sickrage.app.log.debug(
                str(self.indexerid) + ": Loading show info from " + IndexerApi(self.indexer).name)

            t = tvapi
            if not t:
                lINDEXER_API_PARMS = IndexerApi(self.indexer).api_params.copy()
                lINDEXER_API_PARMS['cache'] = cache

                lINDEXER_API_PARMS['language'] = self.lang or sickrage.app.config.indexer_default_language

                if self.dvdorder != 0:
                    lINDEXER_API_PARMS['dvdorder'] = True

                t = IndexerApi(self.indexer).indexer(**lINDEXER_API_PARMS)

            myEp = t[self.indexerid]
            if not myEp:
                return

            try:
                self.name = myEp['seriesname'].strip()
            except AttributeError:
                raise indexer_attributenotfound(
                    "Found %s, but attribute 'seriesname' was empty." % self.indexerid)

            self.overview = safe_getattr(myEp, 'overview', self.overview)
            self.classification = safe_getattr(myEp, 'classification', self.classification)
            self.genre = safe_getattr(myEp, 'genre', self.genre)
            self.network = safe_getattr(myEp, 'network', self.network)
            self.runtime = safe_getattr(myEp, 'runtime', self.runtime)
            self.imdbid = safe_getattr(myEp, 'imdbid', self.imdbid)

            try:
                self.airs = (safe_getattr(myEp, 'airsdayofweek') + " " + safe_getattr(myEp, 'airstime')).strip()
            except:
                pass

            try:
                self.startyear = try_int(
                    str(safe_getattr(myEp, 'firstaired') or datetime.date.fromordinal(1)).split('-')[0])
            except:
                pass

            self.status = safe_getattr(myEp, 'status', self.status)
        else:
            sickrage.app.log.warning(
                str(self.indexerid) + ": NOT loading info from " + IndexerApi(
                    self.indexer).name + " as it is temporarily disabled.")

        # save to database
        self.saveToDB()

    def load_imdb_info(self):
        if not self.imdbid:
            for x in IMDbAPI().search_by_imdb_title(self.name) or []:
                try:
                    if int(x.get('Year'), 0) == self.startyear and x.get('Title') in self.name:
                        self.imdbid = x.get('imdbID')
                        break
                except:
                    continue

        if self.imdbid:
            sickrage.app.log.debug(str(self.indexerid) + ": Loading show info from IMDb")

            self.imdb_info = IMDbAPI().search_by_imdb_id(self.imdbid)
            if not self.imdb_info:
                sickrage.app.log.debug(str(self.indexerid) + ': Unable to obtain IMDb info')
                return

            sickrage.app.log.debug(
                str(self.indexerid) + ": Obtained IMDb info ->" + str(self.imdb_info))

            # save imdb info to database
            imdb_info = {
                '_t': 'imdb_info',
                'indexer_id': self.indexerid,
                'last_update': datetime.date.today().toordinal()
            }

            try:
                dbData = sickrage.app.main_db.get('imdb_info', self.indexerid)
                dbData.update(self.imdb_info)
                sickrage.app.main_db.update(dbData)
            except RevConflict:
                dbData = sickrage.app.main_db.get('imdb_info', self.indexerid)
                sickrage.app.main_db.delete(dbData)
                imdb_info.update(self.imdb_info)
                sickrage.app.main_db.insert(imdb_info)
            except RecordNotFound:
                imdb_info.update(self.imdb_info)
                sickrage.app.main_db.insert(imdb_info)

    def deleteShow(self, full=False):
        # choose delete or trash action
        action = ('delete', 'trash')[sickrage.app.config.trash_remove_show]

        # remove from tv episodes table
        for x in sickrage.app.main_db.get_many('tv_episodes', self.indexerid):
            sickrage.app.main_db.delete(x)

        # remove from tv shows table
        for x in sickrage.app.main_db.get_many('tv_shows', self.indexerid):
            sickrage.app.main_db.delete(x)

        # remove from imdb info table
        for x in sickrage.app.main_db.get_many('imdb_info', self.indexerid):
            sickrage.app.main_db.delete(x)

        # remove from xem scene table
        for x in sickrage.app.main_db.get_many('xem_refresh', self.indexerid):
            sickrage.app.main_db.delete(x)

        # remove from scene numbering table
        for x in sickrage.app.main_db.get_many('scene_numbering', self.indexerid):
            sickrage.app.main_db.delete(x)

        # remove self from show list
        sickrage.app.showlist = [x for x in sickrage.app.showlist if int(x.indexerid) != self.indexerid]

        # clear the cache
        image_cache_dir = os.path.join(sickrage.app.cache_dir, 'images')
        for cache_file in glob.glob(os.path.join(image_cache_dir, str(self.indexerid) + '.*')):
            sickrage.app.log.info('Attempt to %s cache file %s' % (action, cache_file))
            try:
                if sickrage.app.config.trash_remove_show:
                    send2trash.send2trash(cache_file)
                else:
                    os.remove(cache_file)
            except OSError as e:
                sickrage.app.log.warning('Unable to %s %s: %s / %s' % (action, cache_file, repr(e), str(e)))

        # remove entire show folder
        if full:
            try:
                if os.path.isdir(self.location):
                    sickrage.app.log.info('Attempt to %s show folder %s' % (action, self.location))

                    # check first the read-only attribute
                    file_attribute = os.stat(self.location)[0]
                    if not file_attribute & stat.S_IWRITE:
                        # File is read-only, so make it writeable
                        sickrage.app.log.debug(
                            'Attempting to make writeable the read only folder %s' % self.location)
                        try:
                            os.chmod(self.location, stat.S_IWRITE)
                        except Exception:
                            sickrage.app.log.warning('Unable to change permissions of %s' % self.location)

                    if sickrage.app.config.trash_remove_show:
                        send2trash.send2trash(self.location)
                    else:
                        shutil.rmtree(self.location)

                    sickrage.app.log.info('%s show folder %s' %
                                          (('Deleted', 'Trashed')[sickrage.app.config.trash_remove_show],
                                           self.location))
            except OSError as e:
                sickrage.app.log.warning('Unable to %s %s: %s / %s' % (action, self.location, repr(e), str(e)))

        if sickrage.app.config.use_trakt and sickrage.app.config.trakt_sync_watchlist:
            sickrage.app.log.debug(
                "Removing show: {}, {} from watchlist".format(self.indexerid, self.name))
            sickrage.app.notifier_providers['trakt'].update_watchlist(self, update="remove")

    def populateCache(self, force=False):
        sickrage.app.log.debug("Checking & filling cache for show " + self.name)
        image_cache.ImageCache().fill_cache(self, force)

    def refreshDir(self):
        # make sure the show dir is where we think it is unless dirs are created on the fly
        if not os.path.isdir(self.location) and not sickrage.app.config.create_missing_show_dirs:
            return False

        # load from dir
        try:
            self.loadEpisodesFromDir()
        except Exception as e:
            sickrage.app.log.debug("Error searching dir for episodes: {}".format(e))
            sickrage.app.log.debug(traceback.format_exc())

        # run through all locations from DB, check that they exist
        sickrage.app.log.debug(str(self.indexerid) + ": Loading all episodes with a location from the database")

        for ep in sickrage.app.main_db.get_many('tv_episodes', self.indexerid):
            if ep['location'] == '':
                continue

            curLoc = os.path.normpath(ep["location"])
            season = int(ep["season"])
            episode = int(ep["episode"])

            try:
                curEp = self.getEpisode(season, episode)
            except EpisodeDeletedException:
                sickrage.app.log.debug(
                    "The episode was deleted while we were refreshing it, moving on to the next one")
                continue

            # if the path doesn't exist or if it's not in our show dir
            if not os.path.isfile(curLoc) or not os.path.normpath(curLoc).startswith(
                    os.path.normpath(self.location)):

                # check if downloaded files still exist, update our data if this has changed
                if not sickrage.app.config.skip_removed_files:
                    with curEp.lock:
                        # if it used to have a file associated with it and it doesn't anymore then set it to sickrage.EP_DEFAULT_DELETED_STATUS
                        if curEp.location and curEp.status in Quality.DOWNLOADED:

                            if sickrage.app.config.ep_default_deleted_status == ARCHIVED:
                                __, oldQuality = Quality.splitCompositeStatus(curEp.status)
                                new_status = Quality.compositeStatus(ARCHIVED, oldQuality)
                            else:
                                new_status = sickrage.app.config.ep_default_deleted_status

                            sickrage.app.log.debug(
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
                if sickrage.app.config.airdate_episodes:
                    with curEp.lock:
                        curEp.airdateModifyStamp()

    def downloadSubtitles(self):
        if not os.path.isdir(self.location):
            sickrage.app.log.debug(str(self.indexerid) + ": Show dir doesn't exist, can't download subtitles")
            return

        sickrage.app.log.debug("%s: Downloading subtitles" % self.indexerid)

        try:
            episodes = self.getAllEpisodes(has_location=True)
            if not episodes:
                sickrage.app.log.debug(
                    "%s: No episodes to download subtitles for %s" % (self.indexerid, self.name))
                return

            for episode in episodes:
                episode.downloadSubtitles()

        except Exception:
            sickrage.app.log.debug(
                "%s: Error occurred when downloading subtitles for %s" % (self.indexerid, self.name))
            sickrage.app.log.error(traceback.format_exc())

    def saveToDB(self, force_save=False):
        if not self.dirty and not force_save:
            return

        sickrage.app.log.debug("%i: Saving show to database: %s" % (self.indexerid, self.name))

        tv_show = {
            '_t': 'tv_shows',
            'indexer_id': self.indexerid,
            "indexer": self.indexer,
            "show_name": self.name,
            "location": self.location,
            "network": self.network,
            "genre": self.genre,
            "overview": self.overview,
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
            "skip_downloaded": self.skip_downloaded,
            "startyear": self.startyear,
            "lang": self.lang,
            "imdb_id": self.imdbid,
            "last_update": self.last_update,
            "last_refresh": self.last_refresh,
            "rls_ignore_words": self.rls_ignore_words,
            "rls_require_words": self.rls_require_words,
            "default_ep_status": self.default_ep_status,
            "sub_use_sr_metadata": self.subtitles_sr_metadata,
            "notify_list": self.notify_list,
            "search_delay": self.search_delay,
        }

        try:
            dbData = sickrage.app.main_db.get('tv_shows', self.indexerid)
            dbData.update(tv_show)
            sickrage.app.main_db.update(dbData)
        except RecordNotFound:
            sickrage.app.main_db.insert(tv_show)

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
        toReturn += "overview: " + self.overview + "\n"
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
                sickrage.app.log.info("Bad quality value: " + str(quality))

        result = re.sub(', $', '', result)

        if not len(result):
            result = 'None'

        return result

    def wantEpisode(self, season, episode, quality, manualSearch=False, downCurQuality=False):
        sickrage.app.log.debug("Checking if found episode %s S%02dE%02d is wanted at quality %s" % (
            self.name, season or 0, episode or 0, Quality.qualityStrings[quality]))

        # if the quality isn't one we want under any circumstances then just say no
        anyQualities, bestQualities = Quality.splitQuality(self.quality)
        sickrage.app.log.debug("Any, Best = [{}] [{}] Found = [{}]".format(
            self.qualitiesToString(anyQualities),
            self.qualitiesToString(bestQualities),
            self.qualitiesToString([quality]))
        )

        if quality not in anyQualities + bestQualities or quality is UNKNOWN:
            sickrage.app.log.debug("Don't want this quality, ignoring found episode")
            return False

        dbData = [x for x in sickrage.app.main_db.get_many('tv_episodes', self.indexerid)
                  if x['season'] == season and x['episode'] == episode]

        if not dbData or not len(dbData):
            sickrage.app.log.debug("Unable to find a matching episode in database, ignoring found episode")
            return False

        epStatus = int(dbData[0]["status"])
        epStatus_text = statusStrings[epStatus]

        sickrage.app.log.debug("Existing episode status: " + str(epStatus) + " (" + epStatus_text + ")")

        # if we know we don't want it then just say no
        if epStatus in Quality.ARCHIVED + [UNAIRED, SKIPPED, IGNORED] and not manualSearch:
            sickrage.app.log.debug(
                "Existing episode status is unaired/skipped/ignored/archived, ignoring found episode")
            return False

        curStatus, curQuality = Quality.splitCompositeStatus(epStatus)

        # if it's one of these then we want it as long as it's in our allowed initial qualities
        if epStatus in (WANTED, SKIPPED, UNKNOWN):
            sickrage.app.log.debug("Existing episode status is wanted/skipped/unknown, getting found episode")
            return True
        elif manualSearch:
            if (downCurQuality and quality >= curQuality) or (not downCurQuality and quality > curQuality):
                sickrage.app.log.debug(
                    "Usually ignoring found episode, but forced search allows the quality, getting found episode")
                return True

        # if we are re-downloading then we only want it if it's in our bestQualities list and better than what we
        # have, or we only have one bestQuality and we do not have that quality yet
        if epStatus in Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_PROPER and quality in bestQualities and (
                quality > curQuality or curQuality not in bestQualities):
            sickrage.app.log.debug(
                "Episode already exists but the found episode quality is wanted more, getting found episode")
            return True
        elif curQuality == UNKNOWN and manualSearch:
            sickrage.app.log.debug("Episode already exists but quality is Unknown, getting found episode")
            return True
        else:
            sickrage.app.log.debug(
                "Episode already exists and the found episode has same/lower quality, ignoring found episode")

        sickrage.app.log.debug("None of the conditions were met, ignoring found episode")
        return False

    def getOverview(self, epStatus):
        epStatus = try_int(epStatus) or UNKNOWN

        if epStatus == WANTED:
            return Overview.WANTED
        elif epStatus in (UNAIRED, UNKNOWN):
            return Overview.UNAIRED
        elif epStatus in (SKIPPED, IGNORED):
            return Overview.SKIPPED
        elif epStatus in Quality.ARCHIVED:
            return Overview.GOOD
        elif epStatus in Quality.FAILED:
            return Overview.WANTED
        elif epStatus in Quality.SNATCHED:
            return Overview.SNATCHED
        elif epStatus in Quality.SNATCHED_PROPER:
            return Overview.SNATCHED_PROPER
        elif epStatus in Quality.SNATCHED_BEST:
            return Overview.SNATCHED_BEST
        elif epStatus in Quality.DOWNLOADED:
            anyQualities, bestQualities = Quality.splitQuality(self.quality)
            epStatus, curQuality = Quality.splitCompositeStatus(epStatus)

            if bestQualities:
                maxBestQuality = max(bestQualities)
                minBestQuality = min(bestQualities)
            else:
                maxBestQuality = None
                minBestQuality = None

            # elif epStatus == DOWNLOADED and curQuality == Quality.UNKNOWN:
            #    return Overview.QUAL
            # if they don't want re-downloads then we call it good if they have anything
            if maxBestQuality is None:
                return Overview.GOOD
            # if the want only first match and already have one call it good
            elif self.skip_downloaded and curQuality in bestQualities:
                return Overview.GOOD
            # if they want only first match and current quality is higher than minimal best quality call it good
            elif self.skip_downloaded and minBestQuality is not None and curQuality > minBestQuality:
                return Overview.GOOD
            # if they have one but it's not the best they want then mark it as qual
            elif curQuality < maxBestQuality:
                return Overview.QUAL
            # if it's >= maxBestQuality then it's good
            else:
                return Overview.GOOD
        else:
            sickrage.app.log.error('Could not parse episode status into a valid overview status: {}'.format(epStatus))

    def mapIndexers(self):
        mapped = {}

        # init mapped indexers object
        for indexer in IndexerApi().indexers:
            mapped[indexer] = self.indexerid if int(indexer) == int(self.indexer) else 0

        # for each mapped entry
        for dbData in (x for x in sickrage.app.main_db.get_many('indexer_mapping', self.indexerid)
                       if x['indexer'] == self.indexer):

            # Check if its mapped with both tvdb and tvrage.
            if len([i for i in dbData if i is not None]) >= 4:
                sickrage.app.log.debug("Found indexer mapping in cache for show: " + self.name)
                mapped[int(dbData['mindexer'])] = int(dbData['mindexer_id'])
                return mapped
        else:
            for indexer in IndexerApi().indexers:
                if indexer == self.indexer:
                    mapped[indexer] = self.indexerid
                    continue

                lINDEXER_API_PARMS = IndexerApi(indexer).api_params.copy()
                lINDEXER_API_PARMS['custom_ui'] = ShowListUI
                t = IndexerApi(indexer).indexer(**lINDEXER_API_PARMS)

                try:
                    mapped_show = t[self.name]
                except Exception:
                    sickrage.app.log.debug("Unable to map " + IndexerApi(
                        self.indexer).name + "->" + IndexerApi(
                        indexer).name + " for show: " + self.name + ", skipping it")
                    continue

                if mapped_show and len(mapped_show) == 1:
                    sickrage.app.log.debug("Mapping " + IndexerApi(
                        self.indexer).name + "->" + IndexerApi(
                        indexer).name + " for show: " + self.name)

                    mapped[indexer] = int(mapped_show['id'])

                    sickrage.app.log.debug("Adding indexer mapping to DB for show: " + self.name)

                    dbData = [x for x in sickrage.app.main_db.get_many('indexer_mapping', self.indexerid)
                              if x['indexer'] == self.indexer and x['mindexer_id'] == int(mapped_show['id'])]

                    if not len(dbData):
                        sickrage.app.main_db.insert({
                            '_t': 'indexer_mapping',
                            'indexer_id': self.indexerid,
                            'indexer': self.indexer,
                            'mindexer_id': int(mapped_show['id']),
                            'mindexer': indexer
                        })

        return mapped

    def get_all_episodes_from_absolute_number(self, absolute_numbers):
        episodes = []
        season = None

        if len(absolute_numbers):
            for absolute_number in absolute_numbers:
                ep = self.getEpisode(absolute_number=absolute_number)
                if ep:
                    episodes.append(ep.episode)
                    season = ep.season

        return season, episodes

    def __getstate__(self):
        d = dict(self.__dict__)
        del d['lock']
        return d

    def __setstate__(self, d):
        d['lock'] = threading.Lock()
        self.__dict__.update(d)
