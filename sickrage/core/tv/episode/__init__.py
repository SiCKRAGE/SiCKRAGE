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

import os
import re
import threading
from xml.etree.ElementTree import ElementTree

from datetime import datetime, date

import sickrage
from core.common import Quality, UNKNOWN, UNAIRED, statusStrings, dateTimeFormat, SKIPPED, NAMING_EXTEND, \
    NAMING_LIMITED_EXTEND, NAMING_LIMITED_EXTEND_E_PREFIXED, NAMING_DUPLICATE, NAMING_SEPARATED_REPEAT
from core.databases import main_db
from core.exceptions import NoNFOException, \
    EpisodeNotFoundException, EpisodeDeletedException, MultipleEpisodesInDatabaseException
from core.helpers import isMediaFile, tryInt, replaceExtension, \
    rename_ep_file, touchFile, sanitizeSceneName, remove_non_release_groups, remove_extension, sanitizeFileName, \
    safe_getattr
from core.nameparser import NameParser, InvalidNameException, InvalidShowException
from core.processors.post_processor import PostProcessor
from core.scene_numbering import xem_refresh, get_scene_absolute_numbering, get_scene_numbering
from core.searchers import subtitle_searcher
from core.tv import dirty_setter
from core.updaters import tz_updater
from indexers.indexer_exceptions import indexer_seasonnotfound, indexer_error, indexer_episodenotfound
from notifiers import srNotifiers


class TVEpisode(object):
    def __init__(self, show, season, episode, file=""):
        self.lock = threading.Lock()
        self.dirty = True

        self._name = ""
        self._indexer = int(show.indexer)
        self._season = season
        self._episode = episode
        self._absolute_number = 0
        self._description = ""
        self._subtitles = []
        self._subtitles_searchcount = 0
        self._subtitles_lastsearch = str(datetime.min)
        self._airdate = date.fromordinal(1)
        self._hasnfo = False
        self._hastbn = False
        self._status = UNKNOWN
        self._indexerid = 0
        self._file_size = 0
        self._release_name = ""
        self._is_proper = False
        self._version = 0
        self._release_group = ""
        self._location = file

        self.show = show
        self.scene_season = 0
        self.scene_episode = 0
        self.scene_absolute_number = 0

        self.relatedEps = []
        self.checkForMetaFiles()
        self.wantedQuality = []

        self.populateEpisode(self.season, self.episode)

    name = property(lambda self: self._name, dirty_setter("_name"))
    season = property(lambda self: self._season, dirty_setter("_season"))
    episode = property(lambda self: self._episode, dirty_setter("_episode"))
    absolute_number = property(lambda self: self._absolute_number, dirty_setter("_absolute_number"))
    description = property(lambda self: self._description, dirty_setter("_description"))
    subtitles = property(lambda self: self._subtitles, dirty_setter("_subtitles"))
    subtitles_searchcount = property(lambda self: self._subtitles_searchcount,dirty_setter("_subtitles_searchcount"))
    subtitles_lastsearch = property(lambda self: self._subtitles_lastsearch, dirty_setter("_subtitles_lastsearch"))
    airdate = property(lambda self: self._airdate, dirty_setter("_airdate"))
    hasnfo = property(lambda self: self._hasnfo, dirty_setter("_hasnfo"))
    hastbn = property(lambda self: self._hastbn, dirty_setter("_hastbn"))
    status = property(lambda self: self._status, dirty_setter("_status"))
    indexer = property(lambda self: self._indexer, dirty_setter("_indexer"))
    indexerid = property(lambda self: self._indexerid, dirty_setter("_indexerid"))
    file_size = property(lambda self: self._file_size, dirty_setter("_file_size"))
    release_name = property(lambda self: self._release_name, dirty_setter("_release_name"))
    is_proper = property(lambda self: self._is_proper, dirty_setter("_is_proper"))
    version = property(lambda self: self._version, dirty_setter("_version"))
    release_group = property(lambda self: self._release_group, dirty_setter("_release_group"))

    def _set_location(self, new_location):
        if not os.path.isfile(new_location):
            return

        sickrage.srLogger.debug("Setter sets location to " + new_location)
        dirty_setter("_location")(self, new_location)

    location = property(lambda self: self._location, _set_location)

    def refreshSubtitles(self):
        """Look for subtitles files and refresh the subtitles property"""
        self.subtitles, save_subtitles = subtitle_searcher.subtitlesLanguages(self.location)
        if save_subtitles:
            self.saveToDB()

    def downloadSubtitles(self, force=False):
        if not os.path.isfile(self.location):
            sickrage.srLogger.debug("%s: Episode file doesn't exist, can't download subtitles for S%02dE%02d" %
                                         (self.show.indexerid, self.season or 0, self.episode or 0))
            return

        sickrage.srLogger.debug(
            "%s: Downloading subtitles for S%02dE%02d" % (
                self.show.indexerid, self.season or 0, self.episode or 0))

        subtitles_info = {'location': self.location, 'subtitles': self.subtitles,
                          'show.indexerid': self.show.indexerid,
                          'season': self.season,
                          'episode': self.episode, 'name': self.name, 'show.name': self.show.name,
                          'status': self.status}

        self.subtitles, newSubtitles = subtitle_searcher.downloadSubtitles(subtitles_info)

        self.subtitles_searchcount += 1 if self.subtitles_searchcount else 1
        self.subtitles_lastsearch = datetime.now().strftime(dateTimeFormat)
        self.saveToDB()

        if newSubtitles:
            subtitleList = ", ".join([subtitle_searcher.fromietf(newSub).name for newSub in newSubtitles])
            sickrage.srLogger.debug("%s: Downloaded %s subtitles for S%02dE%02d" %
                                         (self.show.indexerid, subtitleList, self.season or 0, self.episode or 0))

            srNotifiers.notify_subtitle_download(self.prettyName(), subtitleList)
        else:
            sickrage.srLogger.debug("%s: No subtitles downloaded for S%02dE%02d" %
                                         (self.show.indexerid, self.season or 0, self.episode or 0))

    def checkForMetaFiles(self):

        oldhasnfo = self.hasnfo
        oldhastbn = self.hastbn

        cur_nfo = False
        cur_tbn = False

        # check for nfo and tbn
        if os.path.isfile(self.location):
            for cur_provider in sickrage.srCore.metadataProviderDict.values():
                if cur_provider.episode_metadata:
                    new_result = cur_provider._has_episode_metadata(self)
                else:
                    new_result = False
                cur_nfo = new_result or cur_nfo

                if cur_provider.episode_thumbnails:
                    new_result = cur_provider._has_episode_thumb(self)
                else:
                    new_result = False
                cur_tbn = new_result or cur_tbn

        self.hasnfo = cur_nfo
        self.hastbn = cur_tbn

        # if either setting has changed return true, if not return false
        return oldhasnfo != self.hasnfo or oldhastbn != self.hastbn

    def populateEpisode(self, season, episode):
        # try loading episode from database
        if self.loadFromDB(season, episode):
            return True

        # try loading episode from NFO files
        if os.path.isfile(self.location):
            try:
                self.loadFromNFO(self.location)
                if self.hasnfo:
                    return True
            except NoNFOException:
                sickrage.srLogger.error("%s: There was an error loading the NFO for episode S%02dE%02d" % (
                    self.show.indexerid, season or 0, episode or 0))

        # try loading episode from indexers
        try:
            if self.loadFromIndexer(season, episode):
                return True
        except EpisodeDeletedException:
            self.deleteEpisode()

        # if we failed SQL *and* NFO, Indexers then fail
        raise EpisodeNotFoundException(
            "Couldn't find episode S%02dE%02d" % (season or 0, episode or 0))

    def loadFromDB(self, season, episode):
        sickrage.srLogger.debug("%s: Loading episode details from DB for episode %s S%02dE%02d" % (
            self.show.indexerid, self.show.name, season or 0, episode or 0))

        sqlResults = main_db.MainDB().select(
            "SELECT * FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?",
            [self.show.indexerid, season, episode])

        if len(sqlResults) > 1:
            raise MultipleEpisodesInDatabaseException("Your DB has two records for the same show somehow.")
        elif len(sqlResults) == 0:
            sickrage.srLogger.debug("%s: Episode S%02dE%02d not found in the database" % (
                self.show.indexerid, self.season or 0, self.episode or 0))
            return False
        else:
            self._season = season
            self._episode = episode
            self._name = sqlResults[0][b"name"] or self.name
            self._absolute_number = sqlResults[0][b"absolute_number"] or self.absolute_number
            self._description = sqlResults[0][b"description"] or self.description
            self._subtitles = sqlResults[0][b"subtitles"].split(",") or self.subtitles
            self._subtitles_searchcount = sqlResults[0][b"subtitles_searchcount"] or self.subtitles_searchcount
            self._subtitles_lastsearch = sqlResults[0][b"subtitles_lastsearch"] or self.subtitles_lastsearch
            self._airdate = date.fromordinal(int(sqlResults[0][b"airdate"])) or self.airdate
            self._status = tryInt(sqlResults[0][b"status"], self.status)
            self.location = os.path.normpath(sqlResults[0][b"location"]) or self.location
            self._file_size = tryInt(sqlResults[0][b"file_size"], self.file_size)
            self._indexerid = tryInt(sqlResults[0][b"indexerid"], self.indexerid)
            self._indexer = tryInt(sqlResults[0][b"indexer"], self.indexer)
            self._release_name = sqlResults[0][b"release_name"] or self.release_name
            self._release_group = sqlResults[0][b"release_group"] or self.release_group
            self._is_proper = tryInt(sqlResults[0][b"is_proper"], self.is_proper)
            self._version = tryInt(sqlResults[0][b"version"], self.version)

            xem_refresh(self.show.indexerid, self.show.indexer)

            self.scene_season = tryInt(sqlResults[0][b"scene_season"], self.scene_season)
            self.scene_episode = tryInt(sqlResults[0][b"scene_episode"], self.scene_episode)
            self.scene_absolute_number = tryInt(sqlResults[0][b"scene_absolute_number"], self.scene_absolute_number)

            if self.scene_absolute_number == 0:
                self.scene_absolute_number = get_scene_absolute_numbering(
                    self.show.indexerid,
                    self.show.indexer,
                    self.absolute_number
                )

            if self.scene_season == 0 or self.scene_episode == 0:
                self.scene_season, self.scene_episode = get_scene_numbering(
                    self.show.indexerid,
                    self.show.indexer,
                    self.season, self.episode
                )

            return True

    def loadFromIndexer(self, season=None, episode=None, cache=True, tvapi=None, cachedSeason=None):
        indexer_name = sickrage.srCore.INDEXER_API(self.indexer).name

        season = (self.season, season)[season is not None]
        episode = (self.episode, episode)[episode is not None]

        sickrage.srLogger.debug("{}: Loading episode details from {} for episode S{}E{}".format(
            self.show.indexerid, indexer_name, season or 0, episode or 0)
        )

        indexer_lang = self.show.lang

        try:
            if cachedSeason is None:
                if tvapi is None:
                    lINDEXER_API_PARMS = sickrage.srCore.INDEXER_API(self.indexer).api_params.copy()

                    if not cache:
                        lINDEXER_API_PARMS[b'cache'] = False

                    if indexer_lang:
                        lINDEXER_API_PARMS[b'language'] = indexer_lang

                    if self.show.dvdorder != 0:
                        lINDEXER_API_PARMS[b'dvdorder'] = True

                    t = sickrage.srCore.INDEXER_API(self.indexer).indexer(**lINDEXER_API_PARMS)
                else:
                    t = tvapi
                myEp = t[self.show.indexerid][season][episode]
            else:
                myEp = cachedSeason[episode]

        except (indexer_error, IOError) as e:
            sickrage.srLogger.debug("{} threw up an error: {}".format(indexer_name, e.message))

            # if the episode is already valid just log it, if not throw it up
            if self.name:
                sickrage.srLogger.debug(
                    "{} timed out but we have enough info from other sources, allowing the error".format(indexer_name))
                return
            else:
                sickrage.srLogger.error("{} timed out, unable to create the episode".format(indexer_name))
                return False

        except (indexer_episodenotfound, indexer_seasonnotfound):
            sickrage.srLogger.debug("Unable to find the episode on {}, has it been removed?".format(indexer_name))
            # if I'm no longer on the Indexers but I once was then delete myself from the DB
            if self.indexerid != -1:
                self.deleteEpisode()
            return

        self.name = safe_getattr(myEp, 'episodename', self.name)
        if not getattr(myEp, 'episodename'):
            sickrage.srLogger.info("This episode {} - S{}E{} has no name on {}. Setting to an empty string"
                                   .format(self.show.name, season or 0, episode or 0, indexer_name))

        if not getattr(myEp, 'absolute_number'):
            sickrage.srLogger.debug("This episode {} - S{}E{} has no absolute number on {}".format(
                self.show.name, season or 0, episode or 0, indexer_name))
        else:
            sickrage.srLogger.debug("{}: The absolute_number for S{}E{} is: {}".format(
                self.show.indexerid, season or 0, episode or 0, myEp[b"absolute_number"]))
            self.absolute_number = tryInt(safe_getattr(myEp, 'absolute_number'), self.absolute_number)

        self.season = season
        self.episode = episode

        xem_refresh(self.show.indexerid, self.show.indexer)

        self.scene_absolute_number = get_scene_absolute_numbering(
            self.show.indexerid,
            self.show.indexer,
            self.absolute_number
        )

        self.scene_season, self.scene_episode = get_scene_numbering(
            self.show.indexerid,
            self.show.indexer,
            self.season, self.episode
        )

        self.description = safe_getattr(myEp, 'overview', self.description)

        firstaired = safe_getattr(myEp, 'firstaired', str(date.fromordinal(1)))
        try:
            rawAirdate = [int(x) for x in safe_getattr(myEp, 'firstaired', str(date.fromordinal(1))).split("-")]
            self.airdate = date(rawAirdate[0], rawAirdate[1], rawAirdate[2])
        except (ValueError, IndexError):
            sickrage.srLogger.warning("Malformed air date of {} retrieved from {} for ({} - S{}E{})".format(
                firstaired, indexer_name, self.show.name, season or 0, episode or 0))
            # if I'm incomplete on the indexer but I once was complete then just delete myself from the DB for now
            if self.indexerid != -1:
                self.deleteEpisode()
            return False

        # early conversion to int so that episode doesn't get marked dirty
        self.indexerid = tryInt(safe_getattr(myEp, 'id'), self.indexerid)
        if self.indexerid is None:
            sickrage.srLogger.error("Failed to retrieve ID from " + sickrage.srCore.INDEXER_API(self.indexer).name)
            if self.indexerid != -1:
                self.deleteEpisode()
            return False

        # don't update show status if show dir is missing, unless it's missing on purpose
        if not os.path.isdir(
                self.show.location) and not sickrage.srConfig.CREATE_MISSING_SHOW_DIRS and not sickrage.srConfig.ADD_SHOWS_WO_DIR:
            sickrage.srLogger.info(
                "The show dir %s is missing, not bothering to change the episode statuses since it'd probably be invalid" % self.show.location)
            return

        if self.location:
            sickrage.srLogger.debug("%s: Setting status for S%02dE%02d based on status %s and location %s" %
                                    (self.show.indexerid, season or 0, episode or 0, statusStrings[self.status],
                                     self.location))

        if not os.path.isfile(self.location):
            if self.airdate >= date.today() or self.airdate == date.fromordinal(1):
                sickrage.srLogger.debug(
                    "Episode airs in the future or has no airdate, marking it %s" % statusStrings[
                        UNAIRED])
                self.status = UNAIRED
            elif self.status in [UNAIRED, UNKNOWN]:
                # Only do UNAIRED/UNKNOWN, it could already be snatched/ignored/skipped, or downloaded/archived to disconnected media
                sickrage.srLogger.debug(
                    "Episode has already aired, marking it %s" % statusStrings[self.show.default_ep_status])
                self.status = self.show.default_ep_status if self.season > 0 else SKIPPED  # auto-skip specials
            else:
                sickrage.srLogger.debug(
                    "Not touching status [ %s ] It could be skipped/ignored/snatched/archived" % statusStrings[
                        self.status])

        # if we have a media file then it's downloaded
        elif isMediaFile(self.location):
            # leave propers alone, you have to either post-process them or manually change them back
            if self.status not in Quality.SNATCHED_PROPER + Quality.DOWNLOADED + Quality.SNATCHED + Quality.ARCHIVED:
                sickrage.srLogger.debug(
                    "5 Status changes from " + str(self.status) + " to " + str(
                        Quality.statusFromName(self.location)))
                self.status = Quality.statusFromName(self.location, anime=self.show.is_anime)

        # shouldn't get here probably
        else:
            sickrage.srLogger.debug("6 Status changes from " + str(self.status) + " to " + str(UNKNOWN))
            self.status = UNKNOWN

        return True

    def loadFromNFO(self, location):

        if not os.path.isdir(self.show.location):
            sickrage.srLogger.info(
                str(
                    self.show.indexerid) + ": The show dir is missing, not bothering to try loading the episode NFO")
            return

        sickrage.srLogger.debug(
            str(
                self.show.indexerid) + ": Loading episode details from the NFO file associated with " + location)

        self.location = location

        if self.location != "":
            if self.status == UNKNOWN:
                if isMediaFile(self.location):
                    sickrage.srLogger.debug("7 Status changes from " + str(self.status) + " to " + str(
                        Quality.statusFromName(self.location, anime=self.show.is_anime)))
                    self.status = Quality.statusFromName(self.location, anime=self.show.is_anime)

            nfoFile = replaceExtension(self.location, "nfo")
            sickrage.srLogger.debug(str(self.show.indexerid) + ": Using NFO name " + nfoFile)

            self.hasnfo = False
            if os.path.isfile(nfoFile):
                try:
                    showXML = ElementTree(file=nfoFile)
                except (SyntaxError, ValueError) as e:
                    sickrage.srLogger.error(
                        "Error loading the NFO, backing up the NFO and skipping for now: {}".format(e.message))
                    try:
                        os.rename(nfoFile, nfoFile + ".old")
                    except Exception as e:
                        sickrage.srLogger.error(
                            "Failed to rename your episode's NFO file - you need to delete it or fix it: {}".format(
                                e.message))
                    raise NoNFOException("Error in NFO format")

                for epDetails in showXML.iter('episodedetails'):
                    if epDetails.findtext('season') is None or int(epDetails.findtext('season')) != self.season or \
                                    epDetails.findtext('episode') is None or int(epDetails.findtext('episode')) != self.episode:
                        sickrage.srLogger.debug(
                            "%s: NFO has an <episodedetails> block for a different episode - wanted S%02dE%02d but got S%02dE%02d" %
                            (
                                self.show.indexerid, self.season or 0, self.episode or 0,
                                epDetails.findtext('season') or 0,
                                epDetails.findtext('episode') or 0))
                        continue

                    if epDetails.findtext('title') is None or epDetails.findtext('aired') is None:
                        raise NoNFOException("Error in NFO format (missing episode title or airdate)")

                    self.name = epDetails.findtext('title')
                    self.episode = tryInt(epDetails.findtext('episode'))
                    self.season = tryInt(epDetails.findtext('season'))

                    xem_refresh(self.show.indexerid, self.show.indexer)

                    self.scene_absolute_number = get_scene_absolute_numbering(
                        self.show.indexerid,
                        self.show.indexer,
                        self.absolute_number
                    )

                    self.scene_season, self.scene_episode = get_scene_numbering(
                        self.show.indexerid,
                        self.show.indexer,
                        self.season, self.episode
                    )

                    self.description = epDetails.findtext('plot') or self.description

                    self.airdate = date.fromordinal(1)
                    if epDetails.findtext('aired'):
                        rawAirdate = [int(x) for x in epDetails.findtext('aired').split("-")]
                        self.airdate = date(rawAirdate[0], rawAirdate[1], rawAirdate[2])

                    self.hasnfo = True

            self.hastbn = False
            if os.path.isfile(replaceExtension(nfoFile, "tbn")):
                self.hastbn = True

    def __str__(self):
        toReturn = ""
        toReturn += "%r - S%02rE%02r - %r\n" % (self.show.name, self.season, self.episode, self.name)
        toReturn += "location: %r\n" % self.location
        toReturn += "description: %r\n" % self.description
        toReturn += "subtitles: %r\n" % ",".join(self.subtitles)
        toReturn += "subtitles_searchcount: %r\n" % self.subtitles_searchcount
        toReturn += "subtitles_lastsearch: %r\n" % self.subtitles_lastsearch
        toReturn += "airdate: %r (%r)\n" % (self.airdate.toordinal(), self.airdate)
        toReturn += "hasnfo: %r\n" % self.hasnfo
        toReturn += "hastbn: %r\n" % self.hastbn
        toReturn += "status: %r\n" % self.status
        return toReturn

    def createMetaFiles(self):

        if not os.path.isdir(self.show.location):
            sickrage.srLogger.info(
                str(self.show.indexerid) + ": The show dir is missing, not bothering to try to create metadata")
            return

        self.createNFO()
        self.createThumbnail()

        if self.checkForMetaFiles():
            self.saveToDB()

    def createNFO(self):

        result = False

        for cur_provider in sickrage.srCore.metadataProviderDict.values():
            result = cur_provider.create_episode_metadata(self) or result

        return result

    def createThumbnail(self):

        result = False

        for cur_provider in sickrage.srCore.metadataProviderDict.values():
            result = cur_provider.create_episode_thumb(self) or result

        return result

    def deleteEpisode(self, full=False):

        sickrage.srLogger.debug(
            "Deleting %s S%02dE%02d from the DB" % (self.show.name, self.season or 0, self.episode or 0))

        # remove myself from the show dictionary
        if self.show.getEpisode(self.season, self.episode, noCreate=True) == self:
            sickrage.srLogger.debug("Removing myself from my show's list")
            del self.show.episodes[self.season][self.episode]

        # delete myself from the DB
        sickrage.srLogger.debug("Deleting myself from the database")

        sql = "DELETE FROM tv_episodes WHERE showid=" + str(self.show.indexerid) + " AND season=" + str(
            self.season) + " AND episode=" + str(self.episode)
        main_db.MainDB().action(sql)

        data = sickrage.srCore.NOTIFIERS.trakt_notifier.trakt_episode_data_generate([(self.season, self.episode)])
        if sickrage.srConfig.USE_TRAKT and sickrage.srConfig.TRAKT_SYNC_WATCHLIST and data:
            sickrage.srLogger.debug("Deleting myself from Trakt")
            sickrage.srCore.NOTIFIERS.trakt_notifier.update_watchlist(self.show, data_episode=data, update="remove")

        if full:
            sickrage.srLogger.info('Attempt to delete episode file %s' % self.location)
            try:
                os.remove(self.location)
            except OSError as e:
                sickrage.srLogger.warning('Unable to delete %s: %s / %s' % (self.location, repr(e), str(e)))

        raise EpisodeDeletedException()

    def saveToDB(self, execute=True, forceSave=False):
        """
        Saves this episode to the database if any of its data has been changed since the last save.

        forceSave: If True it will save to the database even if no data has been changed since the
                    last save (aka if the record is not dirty).
        """

        if not self.dirty and not forceSave:
            sickrage.srLogger.debug(
                "{}: Not saving episode to db - record is not dirty".format(self.show.indexerid))
            return

        # set filesize of episode
        if self.location and os.path.isfile(self.location):
            self.file_size = os.path.getsize(self.location)

        # don't update the subtitle language when the srt file doesn't contain the alpha2 code
        if sickrage.srConfig.SUBTITLES_MULTI or not self.subtitles:
            self.subtitles = ",".join(self.subtitles)

        newValueDict = {"indexerid": self.indexerid,
                        "indexer": self.indexer,
                        "name": self.name,
                        "description": self.description,
                        "subtitles": self.subtitles,
                        "subtitles_searchcount": self.subtitles_searchcount,
                        "subtitles_lastsearch": self.subtitles_lastsearch,
                        "airdate": self.airdate.toordinal(),
                        "hasnfo": self.hasnfo,
                        "hastbn": self.hastbn,
                        "status": self.status,
                        "location": self.location,
                        "file_size": self.file_size,
                        "release_name": self.release_name,
                        "is_proper": self.is_proper,
                        "absolute_number": self.absolute_number,
                        "version": self.version,
                        "release_group": self.release_group}

        controlValueDict = {"showid": self.show.indexerid,
                            "season": self.season,
                            "episode": self.episode}

        # use a custom update/insert method to get the data into the DB
        if not execute:
            return "tv_episodes", newValueDict, controlValueDict

        main_db.MainDB().upsert("tv_episodes", newValueDict, controlValueDict)

    def fullPath(self):
        if self.location is None or self.location == "":
            return None
        else:
            return os.path.join(self.show.location, self.location)

    def createStrings(self, pattern=None):
        patterns = [
            '%S.N.S%SE%0E',
            '%S.N.S%0SE%E',
            '%S.N.S%SE%E',
            '%S.N.S%0SE%0E',
            '%SN S%SE%0E',
            '%SN S%0SE%E',
            '%SN S%SE%E',
            '%SN S%0SE%0E'
        ]

        strings = []
        if not pattern:
            for p in patterns:
                strings += [self._format_pattern(p)]
            return strings
        return self._format_pattern(pattern)

    def prettyName(self):
        """
        Returns the name of this episode in a "pretty" human-readable format. Used for logging
        and notifications and such.

        Returns: A string representing the episode's name and season/ep numbers
        """

        if self.show.anime and not self.show.scene:
            return self._format_pattern('%SN - %AB - %EN')
        elif self.show.air_by_date:
            return self._format_pattern('%SN - %AD - %EN')

        return self._format_pattern('%SN - %Sx%0E - %EN')

    def proper_path(self):
        """
        Figures out the path where this episode SHOULD live according to the renaming rules, relative from the show dir
        """

        anime_type = sickrage.srConfig.NAMING_ANIME
        if not self.show.is_anime:
            anime_type = 3

        result = self.formatted_filename(anime_type=anime_type)

        # if they want us to flatten it and we're allowed to flatten it then we will
        if self.show.flatten_folders and not sickrage.srConfig.NAMING_FORCE_FOLDERS:
            return result

        # if not we append the folder on and use that
        else:
            result = os.path.join(self.formatted_dir(), result)

        return result

    def rename(self):
        """
        Renames an episode file and all related files to the location and filename as specified
        in the naming settings.
        """

        if not os.path.isfile(self.location):
            sickrage.srLogger.warning(
                "Can't perform rename on " + self.location + " when it doesn't exist, skipping")
            return

        proper_path = self.proper_path()
        absolute_proper_path = os.path.join(self.show.location, proper_path)
        absolute_current_path_no_ext, file_ext = os.path.splitext(self.location)
        absolute_current_path_no_ext_length = len(absolute_current_path_no_ext)

        related_subs = []

        current_path = absolute_current_path_no_ext

        if absolute_current_path_no_ext.startswith(self.show.location):
            current_path = absolute_current_path_no_ext[len(self.show.location):]

        sickrage.srLogger.debug(
            "Renaming/moving episode from the base path " + self.location + " to " + absolute_proper_path)

        # if it's already named correctly then don't do anything
        if proper_path == current_path:
            sickrage.srLogger.debug(
                str(self.indexerid) + ": File " + self.location + " is already named correctly, skipping")
            return

        related_files = PostProcessor(self.location).list_associated_files(
            self.location, base_name_only=True, subfolders=True)

        # This is wrong. Cause of pp not moving subs.
        if self.show.subtitles and sickrage.srConfig.SUBTITLES_DIR != '':
            related_subs = PostProcessor(self.location).list_associated_files(
                sickrage.srConfig.SUBTITLES_DIR,
                subtitles_only=True,
                subfolders=True)
            absolute_proper_subs_path = os.path.join(sickrage.srConfig.SUBTITLES_DIR, self.formatted_filename())

        sickrage.srLogger.debug("Files associated to " + self.location + ": " + str(related_files))

        # move the ep file
        result = rename_ep_file(self.location, absolute_proper_path, absolute_current_path_no_ext_length)

        # move related files
        for cur_related_file in related_files:
            # We need to fix something here because related files can be in subfolders and the original code doesn't handle this (at all)
            cur_related_dir = os.path.dirname(os.path.abspath(cur_related_file))
            subfolder = cur_related_dir.replace(os.path.dirname(os.path.abspath(self.location)), '')
            # We now have a subfolder. We need to add that to the absolute_proper_path.
            # First get the absolute proper-path dir
            proper_related_dir = os.path.dirname(os.path.abspath(absolute_proper_path + file_ext))
            proper_related_path = absolute_proper_path.replace(proper_related_dir, proper_related_dir + subfolder)

            cur_result = rename_ep_file(cur_related_file, proper_related_path,
                                        absolute_current_path_no_ext_length + len(subfolder))
            if not cur_result:
                sickrage.srLogger.error(str(self.indexerid) + ": Unable to rename file " + cur_related_file)

        for cur_related_sub in related_subs:
            absolute_proper_subs_path = os.path.join(sickrage.srConfig.SUBTITLES_DIR, self.formatted_filename())
            cur_result = rename_ep_file(cur_related_sub, absolute_proper_subs_path,
                                        absolute_current_path_no_ext_length)
            if not cur_result:
                sickrage.srLogger.error(str(self.indexerid) + ": Unable to rename file " + cur_related_sub)

        # save the ep
        with self.lock:
            if result:
                self.location = absolute_proper_path + file_ext
                for relEp in self.relatedEps:
                    relEp.location = absolute_proper_path + file_ext

        # in case something changed with the metadata just do a quick check
        for curEp in [self] + self.relatedEps:
            curEp.checkForMetaFiles()

        # save any changes to the databas
        sql_l = []
        with self.lock:
            for relEp in [self] + self.relatedEps:
                sql_q = relEp.saveToDB(False)
                if sql_q:
                    sql_l.append(sql_q)
                    del sql_q  # cleanup

        if len(sql_l) > 0:
            main_db.MainDB().mass_upsert(sql_l)
            del sql_l  # cleanup

    def airdateModifyStamp(self):
        """
        Make the modify date and time of a file reflect the show air date and time.
        Note: Also called from postProcessor

        """

        if not self.show.airs and self.show.network:
            return

        airdate_ordinal = self.airdate.toordinal()
        if airdate_ordinal < 1:
            return

        airdatetime = tz_updater.parse_date_time(airdate_ordinal, self.show.airs, self.show.network)

        if sickrage.srConfig.FILE_TIMESTAMP_TIMEZONE == 'local':
            airdatetime = airdatetime.astimezone(tz_updater.sr_timezone)

        filemtime = datetime.fromtimestamp(os.path.getmtime(self.location)).replace(
            tzinfo=tz_updater.sr_timezone)

        if filemtime != airdatetime:
            import time

            airdatetime = airdatetime.timetuple()
            sickrage.srLogger.debug(str(self.show.indexerid) + ": About to modify date of '" + self.location +
                                         "' to show air date " + time.strftime("%b %d,%Y (%H:%M)", airdatetime))
            try:
                if touchFile(self.location, time.mktime(airdatetime)):
                    sickrage.srLogger.info(
                        str(self.show.indexerid) + ": Changed modify date of " + os.path.basename(self.location)
                        + " to show air date " + time.strftime("%b %d,%Y (%H:%M)", airdatetime))
                else:
                    sickrage.srLogger.error(
                        str(self.show.indexerid) + ": Unable to modify date of " + os.path.basename(
                            self.location)
                        + " to show air date " + time.strftime("%b %d,%Y (%H:%M)", airdatetime))
            except Exception:
                sickrage.srLogger.error(
                    str(self.show.indexerid) + ": Failed to modify date of '" + os.path.basename(self.location)
                    + "' to show air date " + time.strftime("%b %d,%Y (%H:%M)", airdatetime))

    def _ep_name(self):
        """
        Returns the name of the episode to use during renaming. Combines the names of related episodes.
        Eg. "Ep Name (1)" and "Ep Name (2)" becomes "Ep Name"
            "Ep Name" and "Other Ep Name" becomes "Ep Name & Other Ep Name"
        """

        multiNameRegex = r"(.*) \(\d{1,2}\)"

        self.relatedEps = sorted(self.relatedEps, key=lambda x: x.episode)

        singleName = True
        curGoodName = None

        for curName in [self.name] + [x.name for x in self.relatedEps]:
            match = re.match(multiNameRegex, curName)
            if not match:
                singleName = False
                break

            if curGoodName is None:
                curGoodName = match.group(1)
            elif curGoodName != match.group(1):
                singleName = False
                break

        if singleName:
            goodName = curGoodName
        else:
            goodName = self.name
            for relEp in self.relatedEps:
                goodName += " & " + relEp.name

        return goodName

    def _replace_map(self):
        """
        Generates a replacement map for this episode which maps all possible custom naming patterns to the correct
        value for this episode.

        Returns: A dict with patterns as the keys and their replacement values as the values.
        """

        ep_name = self._ep_name()

        def dot(name):
            return sanitizeSceneName(name)

        def us(name):
            return re.sub('[ -]', '_', name)

        def release_name(name):
            if name:
                name = remove_non_release_groups(remove_extension(name))
            return name

        def release_group(show, name):
            if name:
                name = remove_non_release_groups(remove_extension(name))
            else:
                return ""

            try:
                np = NameParser(name, showObj=show, naming_pattern=True)
                parse_result = np.parse(name)
            except (InvalidNameException, InvalidShowException) as e:
                sickrage.srLogger.debug("Unable to get parse release_group: {}".format(e.message))
                return ''

            if not parse_result.release_group:
                return ''
            return parse_result.release_group

        _, epQual = Quality.splitCompositeStatus(self.status)  # @UnusedVariable

        if sickrage.srConfig.NAMING_STRIP_YEAR:
            show_name = re.sub(r"\(\d+\)$", "", self.show.name).rstrip()
        else:
            show_name = self.show.name

        # try to get the release group
        rel_grp = {}
        rel_grp[b"SiCKRAGE"] = 'SiCKRAGE'
        if hasattr(self, 'location'):  # from the location name
            rel_grp[b'location'] = release_group(self.show, self.location)
            if not rel_grp[b'location']:
                del rel_grp[b'location']
        if hasattr(self, '_release_group'):  # from the release group field in db
            rel_grp[b'database'] = self.release_group
            if not rel_grp[b'database']:
                del rel_grp[b'database']
        if hasattr(self, 'release_name'):  # from the release name field in db
            rel_grp[b'release_name'] = release_group(self.show, self.release_name)
            if not rel_grp[b'release_name']:
                del rel_grp[b'release_name']

        # use release_group, release_name, location in that order
        if 'database' in rel_grp:
            relgrp = 'database'
        elif 'release_name' in rel_grp:
            relgrp = 'release_name'
        elif 'location' in rel_grp:
            relgrp = 'location'
        else:
            relgrp = 'SiCKRAGE'

        # try to get the release encoder to comply with scene naming standards
        encoder = Quality.sceneQualityFromName(self.release_name.replace(rel_grp[relgrp], ""), epQual)
        if encoder:
            sickrage.srLogger.debug("Found codec for '" + show_name + ": " + ep_name + "'.")

        return {
            '%SN': show_name,
            '%S.N': dot(show_name),
            '%S_N': us(show_name),
            '%EN': ep_name,
            '%E.N': dot(ep_name),
            '%E_N': us(ep_name),
            '%QN': Quality.qualityStrings[epQual],
            '%Q.N': dot(Quality.qualityStrings[epQual]),
            '%Q_N': us(Quality.qualityStrings[epQual]),
            '%SQN': Quality.sceneQualityStrings[epQual] + encoder,
            '%SQ.N': dot(Quality.sceneQualityStrings[epQual] + encoder),
            '%SQ_N': us(Quality.sceneQualityStrings[epQual] + encoder),
            '%S': str(self.season),
            '%0S': '%02d' % self.season,
            '%E': str(self.episode),
            '%0E': '%02d' % self.episode,
            '%XS': str(self.scene_season),
            '%0XS': '%02d' % self.scene_season,
            '%XE': str(self.scene_episode),
            '%0XE': '%02d' % self.scene_episode,
            '%AB': '%(#)03d' % {'#': self.absolute_number},
            '%XAB': '%(#)03d' % {'#': self.scene_absolute_number},
            '%RN': release_name(self.release_name),
            '%RG': rel_grp[relgrp],
            '%CRG': rel_grp[relgrp].upper(),
            '%AD': str(self.airdate).replace('-', ' '),
            '%A.D': str(self.airdate).replace('-', '.'),
            '%A_D': us(str(self.airdate)),
            '%A-D': str(self.airdate),
            '%Y': str(self.airdate.year),
            '%M': str(self.airdate.month),
            '%D': str(self.airdate.day),
            '%0M': '%02d' % self.airdate.month,
            '%0D': '%02d' % self.airdate.day,
            '%RT': "PROPER" if self.is_proper else "",
        }

    def _format_string(self, pattern, replace_map):
        """
        Replaces all template strings with the correct value
        """

        result_name = pattern

        # do the replacements
        for cur_replacement in sorted(replace_map.keys(), reverse=True):
            result_name = result_name.replace(cur_replacement,
                                              sanitizeFileName(replace_map[cur_replacement]))
            result_name = result_name.replace(cur_replacement.lower(),
                                              sanitizeFileName(replace_map[cur_replacement].lower()))

        return result_name

    def _format_pattern(self, pattern=None, multi=None, anime_type=None):
        """
        Manipulates an episode naming pattern and then fills the template in
        """

        if pattern is None:
            pattern = sickrage.srConfig.NAMING_PATTERN

        if multi is None:
            multi = sickrage.srConfig.NAMING_MULTI_EP

        if sickrage.srConfig.NAMING_CUSTOM_ANIME:
            if anime_type is None:
                anime_type = sickrage.srConfig.NAMING_ANIME
        else:
            anime_type = 3

        replace_map = self._replace_map()

        result_name = pattern

        # if there's no release group in the db, let the user know we replaced it
        if replace_map['%RG'] and replace_map['%RG'] != 'SiCKRAGE':
            if not hasattr(self, '_release_group'):
                sickrage.srLogger.debug(
                    "Episode has no release group, replacing it with '" + replace_map['%RG'] + "'")
                self.release_group = replace_map['%RG']  # if release_group is not in the db, put it there
            elif not self.release_group:
                sickrage.srLogger.debug(
                    "Episode has no release group, replacing it with '" + replace_map['%RG'] + "'")
                self.release_group = replace_map['%RG']  # if release_group is not in the db, put it there

        # if there's no release name then replace it with a reasonable facsimile
        if not replace_map['%RN']:

            if self.show.air_by_date or self.show.sports:
                result_name = result_name.replace('%RN', '%S.N.%A.D.%E.N-' + replace_map['%RG'])
                result_name = result_name.replace('%rn', '%s.n.%A.D.%e.n-' + replace_map['%RG'].lower())

            elif anime_type != 3:
                result_name = result_name.replace('%RN', '%S.N.%AB.%E.N-' + replace_map['%RG'])
                result_name = result_name.replace('%rn', '%s.n.%ab.%e.n-' + replace_map['%RG'].lower())

            else:
                result_name = result_name.replace('%RN', '%S.N.S%0SE%0E.%E.N-' + replace_map['%RG'])
                result_name = result_name.replace('%rn', '%s.n.s%0se%0e.%e.n-' + replace_map['%RG'].lower())

                # LOGGER.debug(u"Episode has no release name, replacing it with a generic one: " + result_name)

        if not replace_map['%RT']:
            result_name = re.sub('([ _.-]*)%RT([ _.-]*)', r'\2', result_name)

        # split off ep name part only
        name_groups = re.split(r'[\\/]', result_name)

        # figure out the double-ep numbering style for each group, if applicable
        for cur_name_group in name_groups:

            season_format = sep = ep_sep = ep_format = None

            season_ep_regex = r'''
                                (?P<pre_sep>[ _.-]*)
                                ((?:s(?:eason|eries)?\s*)?%0?S(?![._]?N))
                                (.*?)
                                (%0?E(?![._]?N))
                                (?P<post_sep>[ _.-]*)
                              '''
            ep_only_regex = r'(E?%0?E(?![._]?N))'

            # try the normal way
            season_ep_match = re.search(season_ep_regex, cur_name_group, re.I | re.X)
            ep_only_match = re.search(ep_only_regex, cur_name_group, re.I | re.X)

            # if we have a season and episode then collect the necessary data
            if season_ep_match:
                season_format = season_ep_match.group(2)
                ep_sep = season_ep_match.group(3)
                ep_format = season_ep_match.group(4)
                sep = season_ep_match.group('pre_sep')
                if not sep:
                    sep = season_ep_match.group('post_sep')
                if not sep:
                    sep = ' '

                # force 2-3-4 format if they chose to extend
                if multi in (NAMING_EXTEND, NAMING_LIMITED_EXTEND,
                             NAMING_LIMITED_EXTEND_E_PREFIXED):
                    ep_sep = '-'

                regex_used = season_ep_regex

            # if there's no season then there's not much choice so we'll just force them to use 03-04-05 style
            elif ep_only_match:
                season_format = ''
                ep_sep = '-'
                ep_format = ep_only_match.group(1)
                sep = ''
                regex_used = ep_only_regex

            else:
                continue

            # we need at least this much info to continue
            if not ep_sep or not ep_format:
                continue

            # start with the ep string, eg. E03
            ep_string = self._format_string(ep_format.upper(), replace_map)
            for other_ep in self.relatedEps:

                # for limited extend we only append the last ep
                if multi in (NAMING_LIMITED_EXTEND, NAMING_LIMITED_EXTEND_E_PREFIXED) and other_ep != \
                        self.relatedEps[
                            -1]:
                    continue

                elif multi == NAMING_DUPLICATE:
                    # add " - S01"
                    ep_string += sep + season_format

                elif multi == NAMING_SEPARATED_REPEAT:
                    ep_string += sep

                # add "E04"
                ep_string += ep_sep

                if multi == NAMING_LIMITED_EXTEND_E_PREFIXED:
                    ep_string += 'E'

                ep_string += other_ep._format_string(ep_format.upper(), other_ep._replace_map())

            if anime_type != 3:
                if self.absolute_number == 0:
                    curAbsolute_number = self.episode
                else:
                    curAbsolute_number = self.absolute_number

                if self.season != 0:  # dont set absolute numbers if we are on specials !
                    if anime_type == 1:  # this crazy person wants both ! (note: +=)
                        ep_string += sep + "%(#)03d" % {
                            "#": curAbsolute_number}
                    elif anime_type == 2:  # total anime freak only need the absolute number ! (note: =)
                        ep_string = "%(#)03d" % {"#": curAbsolute_number}

                    for relEp in self.relatedEps:
                        if relEp.absolute_number != 0:
                            ep_string += '-' + "%(#)03d" % {"#": relEp.absolute_number}
                        else:
                            ep_string += '-' + "%(#)03d" % {"#": relEp.episode}

            regex_replacement = None
            if anime_type == 2:
                regex_replacement = r'\g<pre_sep>' + ep_string + r'\g<post_sep>'
            elif season_ep_match:
                regex_replacement = r'\g<pre_sep>\g<2>\g<3>' + ep_string + r'\g<post_sep>'
            elif ep_only_match:
                regex_replacement = ep_string

            if regex_replacement:
                # fill out the template for this piece and then insert this piece into the actual pattern
                cur_name_group_result = re.sub('(?i)(?x)' + regex_used, regex_replacement, cur_name_group)
                # cur_name_group_result = cur_name_group.replace(ep_format, ep_string)
                # LOGGER.debug(u"found "+ep_format+" as the ep pattern using "+regex_used+" and replaced it with "+regex_replacement+" to result in "+cur_name_group_result+" from "+cur_name_group)
                result_name = result_name.replace(cur_name_group, cur_name_group_result)

        result_name = self._format_string(result_name, replace_map)

        sickrage.srLogger.debug("Formatting pattern: " + pattern + " -> " + result_name)

        return result_name

    def formatted_filename(self, pattern=None, multi=None, anime_type=None):
        """
        Just the filename of the episode, formatted based on the naming settings
        """

        if pattern is None:
            # we only use ABD if it's enabled, this is an ABD show, AND this is not a multi-ep
            if self.show.air_by_date and sickrage.srConfig.NAMING_CUSTOM_ABD and not self.relatedEps:
                pattern = sickrage.srConfig.NAMING_ABD_PATTERN
            elif self.show.sports and sickrage.srConfig.NAMING_CUSTOM_SPORTS and not self.relatedEps:
                pattern = sickrage.srConfig.NAMING_SPORTS_PATTERN
            elif self.show.anime and sickrage.srConfig.NAMING_CUSTOM_ANIME:
                pattern = sickrage.srConfig.NAMING_ANIME_PATTERN
            else:
                pattern = sickrage.srConfig.NAMING_PATTERN

        # split off the dirs only, if they exist
        name_groups = re.split(r'[\\/]', pattern)

        return sanitizeFileName(self._format_pattern(name_groups[-1], multi, anime_type))

    def formatted_dir(self, pattern=None, multi=None):
        """
        Just the folder name of the episode
        """

        if pattern is None:
            # we only use ABD if it's enabled, this is an ABD show, AND this is not a multi-ep
            if self.show.air_by_date and sickrage.srConfig.NAMING_CUSTOM_ABD and not self.relatedEps:
                pattern = sickrage.srConfig.NAMING_ABD_PATTERN
            elif self.show.sports and sickrage.srConfig.NAMING_CUSTOM_SPORTS and not self.relatedEps:
                pattern = sickrage.srConfig.NAMING_SPORTS_PATTERN
            elif self.show.anime and sickrage.srConfig.NAMING_CUSTOM_ANIME:
                pattern = sickrage.srConfig.NAMING_ANIME_PATTERN
            else:
                pattern = sickrage.srConfig.NAMING_PATTERN

        # split off the dirs only, if they exist
        name_groups = re.split(r'[\\/]', pattern)

        if len(name_groups) == 1:
            return ''
        else:
            return self._format_pattern(os.sep.join(name_groups[:-1]), multi)

    def __getstate__(self):
        d = dict(self.__dict__)
        del d[b'lock']
        return d

    def __setstate__(self, d):
        d[b'lock'] = threading.Lock()
        self.__dict__.update(d)
