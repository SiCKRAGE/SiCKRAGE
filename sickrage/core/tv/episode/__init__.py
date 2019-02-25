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
import os
import re
import threading
from collections import OrderedDict
from xml.etree.ElementTree import ElementTree

import sickrage
from sickrage.core.common import Quality, UNKNOWN, UNAIRED, statusStrings, dateTimeFormat, SKIPPED, NAMING_EXTEND, \
    NAMING_LIMITED_EXTEND, NAMING_LIMITED_EXTEND_E_PREFIXED, NAMING_DUPLICATE, NAMING_SEPARATED_REPEAT
from sickrage.core.exceptions import NoNFOException, \
    EpisodeNotFoundException, EpisodeDeletedException
from sickrage.core.helpers import is_media_file, try_int, replaceExtension, \
    touchFile, sanitizeSceneName, remove_non_release_groups, remove_extension, sanitizeFileName, \
    safe_getattr, make_dirs, move_file, delete_empty_folders
from sickrage.core.nameparser import NameParser, InvalidNameException, InvalidShowException
from sickrage.core.processors.post_processor import PostProcessor
from sickrage.core.scene_numbering import get_scene_absolute_numbering, get_scene_numbering
from sickrage.indexers import IndexerApi
from sickrage.indexers.exceptions import indexer_seasonnotfound, indexer_error, indexer_episodenotfound
from sickrage.notifiers import Notifiers
from sickrage.subtitles import subtitle_extensions, download_subtitles, refresh_subtitles, subtitle_code_filter, \
    name_from_code


class TVEpisode(object):
    def __init__(self, show, season, episode, file=""):
        self.lock = threading.Lock()
        self.dirty = True

        self._name = ""
        self._indexer = int(show.indexer)
        self._season = season
        self._episode = episode
        self._absolute_number = 0
        self._scene_season = 0
        self._scene_episode = 0
        self._scene_absolute_number = 0
        self._description = ""
        self._subtitles = []
        self._subtitles_searchcount = 0
        self._subtitles_lastsearch = str(datetime.datetime.min)
        self._airdate = datetime.date.fromordinal(1)
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

        self.populateEpisode(self.season, self.episode)

        self.relatedEps = []
        self.checkForMetaFiles()
        self.wantedQuality = []

    @property
    def name(self):
        return self._name or ""

    @name.setter
    def name(self, value):
        if self._name != value:
            self.dirty = True
        self._name = value

    @property
    def season(self):
        return self._season

    @season.setter
    def season(self, value):
        if self._season != value:
            self.dirty = True
        self._season = value

    @property
    def episode(self):
        return self._episode

    @episode.setter
    def episode(self, value):
        if self._episode != value:
            self.dirty = True
        self._episode = value

    @property
    def absolute_number(self):
        return self._absolute_number

    @absolute_number.setter
    def absolute_number(self, value):
        if self._absolute_number != value:
            self.dirty = True
        self._absolute_number = value

    @property
    def scene_season(self):
        if self._scene_season:
            return self._scene_season
        return self._season

    @scene_season.setter
    def scene_season(self, value):
        self._scene_season = value

    @property
    def scene_episode(self):
        if self._scene_episode:
            return self._scene_episode
        return self._episode

    @scene_episode.setter
    def scene_episode(self, value):
        self._scene_episode = value

    @property
    def scene_absolute_number(self):
        if self._scene_absolute_number:
            return self._scene_absolute_number
        return self._absolute_number

    @scene_absolute_number.setter
    def scene_absolute_number(self, value):
        self._scene_absolute_number = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        if self._description != value:
            self.dirty = True
        self._description = value

    @property
    def subtitles(self):
        return self._subtitles

    @subtitles.setter
    def subtitles(self, value):
        if self._subtitles != value:
            self.dirty = True
        self._subtitles = value

    @property
    def subtitles_searchcount(self):
        return self._subtitles_searchcount

    @subtitles_searchcount.setter
    def subtitles_searchcount(self, value):
        if self._subtitles_searchcount != value:
            self.dirty = True
        self._subtitles_searchcount = value

    @property
    def subtitles_lastsearch(self):
        return self._subtitles_lastsearch

    @subtitles_lastsearch.setter
    def subtitles_lastsearch(self, value):
        if self._subtitles_lastsearch != value:
            self.dirty = True
        self._subtitles_lastsearch = value

    @property
    def airdate(self):
        return self._airdate

    @airdate.setter
    def airdate(self, value):
        if self._airdate != value:
            self.dirty = True
        self._airdate = value

    @property
    def hasnfo(self):
        return self._hasnfo

    @hasnfo.setter
    def hasnfo(self, value):
        if self._hasnfo != value:
            self.dirty = True
        self._hasnfo = value

    @property
    def hastbn(self):
        return self._hastbn

    @hastbn.setter
    def hastbn(self, value):
        if self._hastbn != value:
            self.dirty = True
        self._hastbn = value

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if self._status != value:
            self.dirty = True
        self._status = value

    @property
    def indexer(self):
        return self._indexer

    @indexer.setter
    def indexer(self, value):
        if self._indexer != value:
            self.dirty = True
        self._indexer = value

    @property
    def indexerid(self):
        return self._indexerid

    @indexerid.setter
    def indexerid(self, value):
        if self._indexerid != value:
            self.dirty = True
        self._indexerid = value

    @property
    def file_size(self):
        return self._file_size

    @file_size.setter
    def file_size(self, value):
        if self._file_size != value:
            self.dirty = True
        self._file_size = value

    @property
    def release_name(self):
        return self._release_name

    @release_name.setter
    def release_name(self, value):
        if self._release_name != value:
            self.dirty = True
        self._release_name = value

    @property
    def is_proper(self):
        return self._is_proper

    @is_proper.setter
    def is_proper(self, value):
        if self._is_proper != value:
            self.dirty = True
        self._is_proper = value

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, value):
        if self._version != value:
            self.dirty = True
        self._version = value

    @property
    def release_group(self):
        return self._release_group

    @release_group.setter
    def release_group(self, value):
        if self._release_group != value:
            self.dirty = True
        self._release_group = value

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, new_location):
        if os.path.isfile(new_location):
            self.file_size = os.path.getsize(new_location)
            sickrage.app.log.debug("{}: Episode location set to {}".format(self.show.indexerid, new_location))
            self.dirty = True
        self._location = new_location

    def refreshSubtitles(self):
        """Look for subtitles files and refresh the subtitles property"""
        self.subtitles, save_subtitles = refresh_subtitles(self)
        if save_subtitles:
            self.save_to_db()

    def download_subtitles(self):
        if not os.path.isfile(self.location):
            sickrage.app.log.debug("%s: Episode file doesn't exist, can't download subtitles for S%02dE%02d" %
                                   (self.show.indexerid, self.season or 0, self.episode or 0))
            return

        sickrage.app.log.debug(
            "%s: Downloading subtitles for S%02dE%02d" % (
                self.show.indexerid, self.season or 0, self.episode or 0))

        self.subtitles, newSubtitles = download_subtitles(self)

        self.subtitles_searchcount += 1 if self.subtitles_searchcount else 1
        self.subtitles_lastsearch = datetime.datetime.now().strftime(dateTimeFormat)
        self.save_to_db()

        if newSubtitles:
            subtitleList = ", ".join([name_from_code(newSub) for newSub in newSubtitles])
            sickrage.app.log.debug("%s: Downloaded %s subtitles for S%02dE%02d" %
                                   (self.show.indexerid, subtitleList, self.season or 0, self.episode or 0))

            Notifiers.mass_notify_subtitle_download(self.pretty_name(), subtitleList)
        else:
            sickrage.app.log.debug("%s: No subtitles downloaded for S%02dE%02d" %
                                   (self.show.indexerid, self.season or 0, self.episode or 0))

        return newSubtitles

    def checkForMetaFiles(self):

        oldhasnfo = self.hasnfo
        oldhastbn = self.hastbn

        cur_nfo = False
        cur_tbn = False

        # check for nfo and tbn
        if os.path.isfile(self.location):
            for cur_provider in sickrage.app.metadata_providers.values():
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
        # attempt populating episode
        success = {'nfo': False,
                   'indexer': False,
                   'db': False}

        for method, func in OrderedDict([
            ('db', lambda: self.load_from_db(season, episode)),
            ('nfo', lambda: self.loadFromNFO(self.location)),
            ('indexer', lambda: self.load_from_indexer(season, episode)),
        ]).items():

            try:
                success[method] = func()
            except NoNFOException:
                sickrage.app.log.error("%s: There was an error loading the NFO for episode S%02dE%02d" % (
                    self.show.indexerid, season or 0, episode or 0))
            except EpisodeDeletedException:
                pass

            # confirm if we successfully populated the episode
            if any(success.values()):
                return True

        # we failed to populate the episode
        raise EpisodeNotFoundException("Couldn't find episode S%02dE%02d" % (season or 0, episode or 0))

    def load_from_db(self, season, episode):
        sickrage.app.log.debug("%s: Loading episode details from DB for episode %s S%02dE%02d" % (
            self.show.indexerid, self.show.name, season or 0, episode or 0))

        dbData = [x for x in sickrage.app.main_db.get_many('tv_episodes', self.show.indexerid)
                  if x['season'] == season and x['episode'] == episode]

        if len(dbData) > 1:
            for ep in dbData:
                sickrage.app.main_db.delete(ep)
            return False
        elif len(dbData) == 0:
            sickrage.app.log.debug("%s: Episode S%02dE%02d not found in the database" % (
                self.show.indexerid, self.season or 0, self.episode or 0))
            return False
        else:
            self._season = season
            self._episode = episode
            self._name = dbData[0].get("name", self.name)
            self._absolute_number = dbData[0].get("absolute_number", self.absolute_number)
            self._description = dbData[0].get("description", self.description)
            self._subtitles = dbData[0].get("subtitles", self.subtitles).split(",")
            self._subtitles_searchcount = dbData[0].get("subtitles_searchcount", self.subtitles_searchcount)
            self._subtitles_lastsearch = dbData[0].get("subtitles_lastsearch", self.subtitles_lastsearch)
            self._airdate = datetime.date.fromordinal(int(dbData[0].get("airdate", self.airdate)))
            self._status = try_int(dbData[0]["status"], self.status)
            self.location = dbData[0].get("location", self.location)
            self._file_size = try_int(dbData[0]["file_size"], self.file_size)
            self._indexerid = try_int(dbData[0]["indexerid"], self.indexerid)
            self._indexer = try_int(dbData[0]["indexer"], self.indexer)
            self._release_name = dbData[0].get("release_name", self.release_name)
            self._release_group = dbData[0].get("release_group", self.release_group)
            self._is_proper = try_int(dbData[0]["is_proper"], self.is_proper)
            self._version = try_int(dbData[0]["version"], self.version)

            self._scene_season = try_int(dbData[0]["scene_season"], self.scene_season)
            self._scene_episode = try_int(dbData[0]["scene_episode"], self.scene_episode)
            self._scene_absolute_number = try_int(dbData[0]["scene_absolute_number"], self.scene_absolute_number)

            if self._scene_absolute_number == 0:
                self._scene_absolute_number = get_scene_absolute_numbering(
                    self.show.indexerid,
                    self.show.indexer,
                    self.absolute_number
                )

            if self._scene_season == 0 or self._scene_episode == 0:
                self._scene_season, self._scene_episode = get_scene_numbering(
                    self.show.indexerid,
                    self.show.indexer,
                    self.season, self.episode
                )

            return True

    def load_from_indexer(self, season=None, episode=None, cache=True, tvapi=None, cachedSeason=None):
        indexer_name = IndexerApi(self.indexer).name

        season = (self.season, season)[season is not None]
        episode = (self.episode, episode)[episode is not None]

        sickrage.app.log.debug("{}: Loading episode details from {} for episode S{:02d}E{:02d}".format(
            self.show.indexerid, indexer_name, season or 0, episode or 0)
        )

        indexer_lang = self.show.lang or sickrage.app.config.indexer_default_language

        try:
            if cachedSeason is None:
                t = tvapi
                if not t:
                    lINDEXER_API_PARMS = IndexerApi(self.indexer).api_params.copy()
                    lINDEXER_API_PARMS['cache'] = cache

                    lINDEXER_API_PARMS['language'] = indexer_lang

                    if self.show.dvdorder != 0:
                        lINDEXER_API_PARMS['dvdorder'] = True

                    t = IndexerApi(self.indexer).indexer(**lINDEXER_API_PARMS)
                myEp = t[self.show.indexerid][season][episode]
            else:
                myEp = cachedSeason[episode]

        except (indexer_error, IOError) as e:
            sickrage.app.log.debug("{} threw up an error: {}".format(indexer_name, e))

            # if the episode is already valid just log it, if not throw it up
            if self.name:
                sickrage.app.log.debug(
                    "{} timed out but we have enough info from other sources, allowing the error".format(indexer_name))
                return False
            else:
                sickrage.app.log.error("{} timed out, unable to create the episode".format(indexer_name))
                return False

        except (indexer_episodenotfound, indexer_seasonnotfound):
            sickrage.app.log.debug(
                "Unable to find the episode on {}, has it been removed?".format(indexer_name))

            # if I'm no longer on the Indexers but I once was then delete myself from the DB
            if self.indexerid != -1:
                self.deleteEpisode()
            return False

        self.name = safe_getattr(myEp, 'episodename', self.name)
        if not myEp.get('episodename'):
            sickrage.app.log.info(
                "This episode {} - S{:02d}E{:02d} has no name on {}. Setting to an empty string"
                    .format(self.show.name, season or 0, episode or 0, indexer_name))

        if not myEp.get('absolutenumber'):
            sickrage.app.log.debug("This episode {} - S{:02d}E{:02d} has no absolute number on {}".format(
                self.show.name, season or 0, episode or 0, indexer_name))
        else:
            sickrage.app.log.debug("{}: The absolute_number for S{:02d}E{:02d} is: {}".format(
                self.show.indexerid, season or 0, episode or 0, myEp["absolutenumber"]))
            self.absolute_number = try_int(safe_getattr(myEp, 'absolutenumber'), self.absolute_number)

        self.season = season
        self.episode = episode

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

        firstaired = safe_getattr(myEp, 'firstaired') or datetime.date.fromordinal(1)
        try:
            rawAirdate = [int(x) for x in str(firstaired).split("-")]
            self.airdate = datetime.date(rawAirdate[0], rawAirdate[1], rawAirdate[2])
        except (ValueError, IndexError):
            sickrage.app.log.warning(
                "Malformed air date of {} retrieved from {} for ({} - S{:02d}E{:02d})".format(
                    firstaired, indexer_name, self.show.name, season or 0, episode or 0))
            # if I'm incomplete on the indexer but I once was complete then just delete myself from the DB for now
            if self.indexerid != -1:
                self.deleteEpisode()
            return False

        # early conversion to int so that episode doesn't get marked dirty
        self.indexerid = try_int(safe_getattr(myEp, 'id'), self.indexerid)
        if self.indexerid is None:
            sickrage.app.log.warning("Failed to retrieve ID from " + IndexerApi(self.indexer).name)
            if self.indexerid != -1:
                self.deleteEpisode()
            return False

        # don't update show status if show dir is missing, unless it's missing on purpose
        if not os.path.isdir(
                self.show.location) and not sickrage.app.config.create_missing_show_dirs and not sickrage.app.config.add_shows_wo_dir:
            sickrage.app.log.info("The show dir %s is missing, not bothering to change the episode statuses since "
                                  "it'd probably be invalid" % self.show.location)
            return False

        if self.location:
            sickrage.app.log.debug("%s: Setting status for S%02dE%02d based on status %s and location %s" %
                                   (self.show.indexerid, season or 0, episode or 0, statusStrings[self.status],
                                    self.location))

        if not os.path.isfile(self.location):
            if self.airdate >= datetime.date.today() or self.airdate == datetime.date.fromordinal(1):
                sickrage.app.log.debug(
                    "Episode airs in the future or has no airdate, marking it %s" % statusStrings[
                        UNAIRED])
                self.status = UNAIRED
            elif self.status in [UNAIRED, UNKNOWN]:
                # Only do UNAIRED/UNKNOWN, it could already be snatched/ignored/skipped, or downloaded/archived to
                # disconnected media
                sickrage.app.log.debug(
                    "Episode has already aired, marking it %s" % statusStrings[self.show.default_ep_status])
                self.status = self.show.default_ep_status if self.season > 0 else SKIPPED  # auto-skip specials
            else:
                sickrage.app.log.debug(
                    "Not touching status [ %s ] It could be skipped/ignored/snatched/archived" % statusStrings[
                        self.status])

        # if we have a media file then it's downloaded
        elif is_media_file(self.location):
            # leave propers alone, you have to either post-process them or manually change them back
            if self.status not in Quality.SNATCHED_PROPER + Quality.DOWNLOADED + Quality.SNATCHED + Quality.ARCHIVED:
                sickrage.app.log.debug(
                    "5 Status changes from " + str(self.status) + " to " + str(
                        Quality.statusFromName(self.location)))
                self.status = Quality.statusFromName(self.location, anime=self.show.is_anime)

        # shouldn't get here probably
        else:
            sickrage.app.log.debug("6 Status changes from " + str(self.status) + " to " + str(UNKNOWN))
            self.status = UNKNOWN

        return True

    def loadFromNFO(self, location):
        if not os.path.isdir(self.show.location):
            sickrage.app.log.info(
                "{}: The show dir is missing, not bothering to try loading the episode NFO".format(self.show.indexerid))
            return False

        sickrage.app.log.debug(
            "{}: Loading episode details from the NFO file associated with {}".format(self.show.indexerid, location))

        if os.path.isfile(location):
            self.location = location
            if self.status == UNKNOWN:
                if is_media_file(self.location):
                    sickrage.app.log.debug("7 Status changes from " + str(self.status) + " to " + str(
                        Quality.statusFromName(self.location, anime=self.show.is_anime)))
                    self.status = Quality.statusFromName(self.location, anime=self.show.is_anime)

            nfoFile = replaceExtension(self.location, "nfo")
            sickrage.app.log.debug(str(self.show.indexerid) + ": Using NFO name " + nfoFile)

            self.hasnfo = False
            if os.path.isfile(nfoFile):
                try:
                    showXML = ElementTree(file=nfoFile)
                except (SyntaxError, ValueError) as e:
                    sickrage.app.log.error(
                        "Error loading the NFO, backing up the NFO and skipping for now: {}".format(e))
                    try:
                        os.rename(nfoFile, nfoFile + ".old")
                    except Exception as e:
                        sickrage.app.log.warning(
                            "Failed to rename your episode's NFO file - you need to delete it or fix it: {}".format(e))
                    raise NoNFOException("Error in NFO format")

                for epDetails in showXML.iter('episodedetails'):
                    if epDetails.findtext('season') is None or int(
                            epDetails.findtext('season')) != self.season or epDetails.findtext(
                        'episode') is None or int(epDetails.findtext('episode')) != self.episode:
                        sickrage.app.log.debug(
                            "%s: NFO has an <episodedetails> block for a different episode - wanted S%02dE%02d but got S%02dE%02d" %
                            (
                                self.show.indexerid, self.season or 0, self.episode or 0,
                                epDetails.findtext('season') or 0,
                                epDetails.findtext('episode') or 0))
                        continue

                    if epDetails.findtext('title') is None or epDetails.findtext('aired') is None:
                        raise NoNFOException("Error in NFO format (missing episode title or airdate)")

                    self.name = epDetails.findtext('title')
                    self.episode = try_int(epDetails.findtext('episode'))
                    self.season = try_int(epDetails.findtext('season'))

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

                    self.airdate = datetime.date.fromordinal(1)
                    if epDetails.findtext('aired'):
                        rawAirdate = [int(x) for x in epDetails.findtext('aired').split("-")]
                        self.airdate = datetime.date(rawAirdate[0], rawAirdate[1], rawAirdate[2])

                    self.hasnfo = True

            self.hastbn = False
            if os.path.isfile(replaceExtension(nfoFile, "tbn")):
                self.hastbn = True

        return self.hasnfo

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

    def createMetaFiles(self, force=False):

        if not os.path.isdir(self.show.location):
            sickrage.app.log.info(
                str(self.show.indexerid) + ": The show dir is missing, not bothering to try to create metadata")
            return

        self.createNFO(force)
        self.createThumbnail(force)

        if self.checkForMetaFiles():
            self.save_to_db()

    def createNFO(self, force=False):

        result = False

        for cur_provider in sickrage.app.metadata_providers.values():
            result = cur_provider.create_episode_metadata(self, force) or result

        return result

    def createThumbnail(self, force=False):

        result = False

        for cur_provider in sickrage.app.metadata_providers.values():
            result = cur_provider.create_episode_thumb(self, force) or result

        return result

    def deleteEpisode(self, full=False):

        sickrage.app.log.debug(
            "Deleting %s S%02dE%02d from the DB" % (self.show.name, self.season or 0, self.episode or 0))

        # remove myself from the show dictionary
        if self.show.get_episode(self.season, self.episode, noCreate=True) == self:
            sickrage.app.log.debug("Removing myself from my show's list")
            del self.show.episodes[self.season][self.episode]

        # delete myself from the DB
        sickrage.app.log.debug("Deleting myself from the database")

        [sickrage.app.main_db.delete(x) for x in
         sickrage.app.main_db.get_many('tv_episodes', self.show.indexerid)
         if x['season'] == self.season and x['episode'] == self.episode]

        data = sickrage.app.notifier_providers['trakt'].trakt_episode_data_generate([(self.season, self.episode)])
        if sickrage.app.config.use_trakt and sickrage.app.config.trakt_sync_watchlist and data:
            sickrage.app.log.debug("Deleting myself from Trakt")
            sickrage.app.notifier_providers['trakt'].update_watchlist(self.show, data_episode=data, update="remove")

        if full and os.path.isfile(self.location):
            sickrage.app.log.info('Attempt to delete episode file %s' % self.location)
            try:
                os.remove(self.location)
            except OSError as e:
                sickrage.app.log.warning('Unable to delete %s: %s / %s' % (self.location, repr(e), str(e)))

        raise EpisodeDeletedException()

    def save_to_db(self, force_save=False):
        """
        Saves this episode to the database if any of its data has been changed since the last save.

        force_save: If True it will save to the database even if no data has been changed since the
                    last save (aka if the record is not dirty).
        """

        if not self.dirty and not force_save:
            return

        sickrage.app.log.debug("%i: Saving episode to database: %s" % (self.show.indexerid, self.name))

        tv_episode = {
            '_t': 'tv_episodes',
            "showid": self.show.indexerid,
            "season": self.season,
            "episode": self.episode,
            "scene_season": self.scene_season,
            "scene_episode": self.scene_episode,
            "indexerid": self.indexerid,
            "indexer": self.indexer,
            "name": self.name,
            "description": self.description,
            "subtitles": ",".join(self.subtitles),
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
            "scene_absolute_number": self.scene_absolute_number,
            "version": self.version,
            "release_group": self.release_group
        }

        for x in sickrage.app.main_db.get_many('tv_episodes', self.show.indexerid):
            if x['indexerid'] == self.indexerid:
                x.update(tv_episode)
                sickrage.app.main_db.update(x)
                break
        else:
            sickrage.app.main_db.insert(tv_episode)

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

    def pretty_name(self):
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

        anime_type = sickrage.app.config.naming_anime
        if not self.show.is_anime:
            anime_type = 3

        result = self.formatted_filename(anime_type=anime_type)

        # if they want us to flatten it and we're allowed to flatten it then we will
        if self.show.flatten_folders and not sickrage.app.config.naming_force_folders:
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
            sickrage.app.log.warning(
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

        sickrage.app.log.debug(
            "Renaming/moving episode from the base path " + self.location + " to " + absolute_proper_path)

        # if it's already named correctly then don't do anything
        if proper_path == current_path:
            sickrage.app.log.debug(
                str(self.indexerid) + ": File " + self.location + " is already named correctly, skipping")
            return

        related_files = PostProcessor(self.location).list_associated_files(self.location, subfolders=True)

        # This is wrong. Cause of pp not moving subs.
        if self.show.subtitles and sickrage.app.config.subtitles_dir:
            subs_path = os.path.join(sickrage.app.config.subtitles_dir, os.path.basename(self.location))
            related_subs = PostProcessor(self.location).list_associated_files(subs_path, subtitles_only=True,
                                                                              subfolders=True, rename=True)

        sickrage.app.log.debug("Files associated to " + self.location + ": " + str(related_files))

        # move the ep file
        result = self.rename_ep_file(self.location, absolute_proper_path, absolute_current_path_no_ext_length)

        # move related files
        for cur_related_file in related_files:
            # We need to fix something here because related files can be in subfolders and the original code doesn't handle this (at all)
            cur_related_dir = os.path.dirname(os.path.abspath(cur_related_file))
            subfolder = cur_related_dir.replace(os.path.dirname(os.path.abspath(self.location)), '')
            # We now have a subfolder. We need to add that to the absolute_proper_path.
            # First get the absolute proper-path dir
            proper_related_dir = os.path.dirname(os.path.abspath(absolute_proper_path + file_ext))
            proper_related_path = absolute_proper_path.replace(proper_related_dir, proper_related_dir + subfolder)

            cur_result = self.rename_ep_file(cur_related_file, proper_related_path,
                                             absolute_current_path_no_ext_length + len(subfolder))
            if not cur_result:
                sickrage.app.log.warning(str(self.indexerid) + ": Unable to rename file " + cur_related_file)

        for cur_related_sub in related_subs:
            absolute_proper_subs_path = os.path.join(sickrage.app.config.subtitles_dir, self.formatted_filename())
            cur_result = self.rename_ep_file(cur_related_sub, absolute_proper_subs_path,
                                             absolute_current_path_no_ext_length)
            if not cur_result:
                sickrage.app.log.warning(str(self.indexerid) + ": Unable to rename file " + cur_related_sub)

        # save the ep
        with self.lock:
            if result:
                self.location = absolute_proper_path + file_ext
                for relEp in self.relatedEps:
                    relEp.location = absolute_proper_path + file_ext

        # in case something changed with the metadata just do a quick check
        for curEp in [self] + self.relatedEps:
            curEp.checkForMetaFiles()

        # save any changes to the database
        with self.lock:
            for relEp in [self] + self.relatedEps:
                relEp.save_to_db()

    def airdateModifyStamp(self):
        """
        Make the modify date and time of a file reflect the show air date and time.
        Note: Also called from postProcessor

        """

        if not all([sickrage.app.config.airdate_episodes, self.airdate, self.location, self.show, self.show.airs,
                    self.show.network]): return

        try:
            airdate_ordinal = self.airdate.toordinal()
            if airdate_ordinal < 1:
                return

            airdatetime = sickrage.app.tz_updater.parse_date_time(airdate_ordinal, self.show.airs, self.show.network)

            if sickrage.app.config.file_timestamp_timezone == 'local':
                airdatetime = airdatetime.astimezone(sickrage.app.tz)

            filemtime = datetime.datetime.fromtimestamp(os.path.getmtime(self.location)).replace(
                tzinfo=sickrage.app.tz)

            if filemtime != airdatetime:
                import time

                airdatetime = airdatetime.timetuple()
                sickrage.app.log.debug(
                    str(self.show.indexerid) + ": About to modify date of '" + self.location +
                    "' to show air date " + time.strftime("%b %d,%Y (%H:%M)", airdatetime))
                try:
                    if touchFile(self.location, time.mktime(airdatetime)):
                        sickrage.app.log.info(
                            str(self.show.indexerid) + ": Changed modify date of " + os.path.basename(self.location)
                            + " to show air date " + time.strftime("%b %d,%Y (%H:%M)", airdatetime))
                    else:
                        sickrage.app.log.warning(
                            str(self.show.indexerid) + ": Unable to modify date of " + os.path.basename(
                                self.location)
                            + " to show air date " + time.strftime("%b %d,%Y (%H:%M)", airdatetime))
                except Exception:
                    sickrage.app.log.warning(
                        str(self.show.indexerid) + ": Failed to modify date of '" + os.path.basename(self.location)
                        + "' to show air date " + time.strftime("%b %d,%Y (%H:%M)", airdatetime))
        except Exception:
            sickrage.app.log.warning(
                "{}: Failed to modify date of '{}'".format(self.show.indexerid, os.path.basename(self.location)))

    def _ep_name(self):
        """
        Returns the name of the episode to use during renaming. Combines the names of related episodes.
        Eg. "Ep Name (1)" and "Ep Name (2)" becomes "Ep Name"
            "Ep Name" and "Other Ep Name" becomes "Ep Name & Other Ep Name"
        """

        multi_name_regex = r"(.*) \(\d{1,2}\)"

        single_name = True
        cur_good_name = None

        for curName in [self.name] + [x.name for x in sorted(self.relatedEps, key=lambda k: k.episode)]:
            match = re.match(multi_name_regex, curName)
            if not match:
                single_name = False
                break

            if cur_good_name is None:
                cur_good_name = match.group(1)
            elif cur_good_name != match.group(1):
                single_name = False
                break

        if single_name:
            good_name = cur_good_name or self.name
        else:
            good_name = self.name
            if len(self.relatedEps):
                good_name = "MultiPartEpisode"
            # for relEp in self.relatedEps:
            #     good_name += " & " + relEp.name

        return good_name

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

                try:
                    parse_result = NameParser(name, showObj=show, naming_pattern=True).parse(name)
                    if parse_result.release_group:
                        return parse_result.release_group
                except (InvalidNameException, InvalidShowException) as e:
                    sickrage.app.log.debug("Unable to get parse release_group: {}".format(e))

            return ''

        __, epQual = Quality.splitCompositeStatus(self.status)

        if sickrage.app.config.naming_strip_year:
            show_name = re.sub(r"\(\d+\)$", "", self.show.name).rstrip()
        else:
            show_name = self.show.name

        # try to get the release group
        rel_grp = {"SiCKRAGE": 'SiCKRAGE'}
        if hasattr(self, 'location'):  # from the location name
            rel_grp['location'] = release_group(self.show, self.location)
            if not rel_grp['location']:
                del rel_grp['location']
        if hasattr(self, '_release_group'):  # from the release group field in db
            rel_grp['database'] = self.release_group
            if not rel_grp['database']:
                del rel_grp['database']
        if hasattr(self, 'release_name'):  # from the release name field in db
            rel_grp['release_name'] = release_group(self.show, self.release_name)
            if not rel_grp['release_name']:
                del rel_grp['release_name']

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
            sickrage.app.log.debug("Found codec for '" + show_name + ": " + ep_name + "'.")

        return {
            '%SN': show_name,
            '%S.N': dot(show_name),
            '%S_N': us(show_name),
            '%EN': ep_name,
            '%E.N': dot(ep_name),
            '%E_N': us(ep_name),
            '%L': str(getattr(self.show, 'lang', sickrage.app.config.indexer_default_language)),
            '%QN': Quality.qualityStrings[epQual],
            '%Q.N': dot(Quality.qualityStrings[epQual]),
            '%Q_N': us(Quality.qualityStrings[epQual]),
            '%SQN': Quality.sceneQualityStrings[epQual] + encoder,
            '%SQ.N': dot(Quality.sceneQualityStrings[epQual] + encoder),
            '%SQ_N': us(Quality.sceneQualityStrings[epQual] + encoder),
            '%SY': str(self.show.startyear),
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
            pattern = sickrage.app.config.naming_pattern

        if multi is None:
            multi = sickrage.app.config.naming_multi_ep

        if sickrage.app.config.naming_custom_anime:
            if anime_type is None:
                anime_type = sickrage.app.config.naming_anime
        else:
            anime_type = 3

        replace_map = self._replace_map()

        result_name = pattern

        # if there's no release group in the db, let the user know we replaced it
        if replace_map['%RG'] and replace_map['%RG'] != 'SiCKRAGE':
            if not hasattr(self, '_release_group'):
                sickrage.app.log.debug(
                    "Episode has no release group, replacing it with '" + replace_map['%RG'] + "'")
                self.release_group = replace_map['%RG']  # if release_group is not in the db, put it there
            elif not self.release_group:
                sickrage.app.log.debug(
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
                                ((?:s(?:eason|eries)?\s*)?%0?S(?![._]?N|Y))
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
                        self.relatedEps[-1]:
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
                        ep_string += sep + "%(#)03d" % {"#": curAbsolute_number}
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

        sickrage.app.log.debug("Formatting pattern: " + pattern + " -> " + result_name)

        return result_name

    def formatted_filename(self, pattern=None, multi=None, anime_type=None):
        """
        Just the filename of the episode, formatted based on the naming settings
        """

        if pattern is None:
            # we only use ABD if it's enabled, this is an ABD show, AND this is not a multi-ep
            if self.show.air_by_date and sickrage.app.config.naming_custom_abd and not self.relatedEps:
                pattern = sickrage.app.config.naming_abd_pattern
            elif self.show.sports and sickrage.app.config.naming_custom_sports and not self.relatedEps:
                pattern = sickrage.app.config.naming_sports_pattern
            elif self.show.anime and sickrage.app.config.naming_custom_anime:
                pattern = sickrage.app.config.naming_anime_pattern
            else:
                pattern = sickrage.app.config.naming_pattern

        # split off the dirs only, if they exist
        name_groups = re.split(r'[\\/]', pattern)

        return sanitizeFileName(self._format_pattern(name_groups[-1], multi, anime_type))

    def formatted_dir(self, pattern=None, multi=None):
        """
        Just the folder name of the episode
        """

        if pattern is None:
            # we only use ABD if it's enabled, this is an ABD show, AND this is not a multi-ep
            if self.show.air_by_date and sickrage.app.config.naming_custom_abd and not self.relatedEps:
                pattern = sickrage.app.config.naming_abd_pattern
            elif self.show.sports and sickrage.app.config.naming_custom_sports and not self.relatedEps:
                pattern = sickrage.app.config.naming_sports_pattern
            elif self.show.anime and sickrage.app.config.naming_custom_anime:
                pattern = sickrage.app.config.naming_anime_pattern
            else:
                pattern = sickrage.app.config.naming_pattern

        # split off the dirs only, if they exist
        name_groups = re.split(r'[\\/]', pattern)

        if len(name_groups) == 1:
            return ''
        else:
            return self._format_pattern(os.sep.join(name_groups[:-1]), multi)

    def rename_ep_file(self, cur_path, new_path, old_path_length=0):
        """
        Creates all folders needed to move a file to its new location, renames it, then cleans up any folders
        left that are now empty.

        :param  cur_path: The absolute path to the file you want to move/rename
        :param new_path: The absolute path to the destination for the file WITHOUT THE EXTENSION
        :param old_path_length: The length of media file path (old name) WITHOUT THE EXTENSION
        """

        # new_dest_dir, new_dest_name = os.path.split(new_path)

        if old_path_length == 0 or old_path_length > len(cur_path):
            # approach from the right
            cur_file_name, cur_file_ext = os.path.splitext(cur_path)
        else:
            # approach from the left
            cur_file_ext = cur_path[old_path_length:]
            cur_file_name = cur_path[:old_path_length]

        if cur_file_ext[1:] in subtitle_extensions:
            # Extract subtitle language from filename
            sublang = os.path.splitext(cur_file_name)[1][1:]

            # Check if the language extracted from filename is a valid language
            if sublang in subtitle_code_filter():
                cur_file_ext = '.' + sublang + cur_file_ext

        # put the extension on the incoming file
        new_path += cur_file_ext

        make_dirs(os.path.dirname(new_path))

        # move the file
        try:
            sickrage.app.log.info("Renaming file from %s to %s" % (cur_path, new_path))
            move_file(cur_path, new_path)
        except (OSError, IOError) as e:
            sickrage.app.log.warning("Failed renaming %s to %s : %r" % (cur_path, new_path, e))
            return False

        # clean up any old folders that are empty
        delete_empty_folders(os.path.dirname(cur_path))

        return True

    def __getstate__(self):
        d = dict(self.__dict__)
        del d['lock']
        return d

    def __setstate__(self, d):
        d['lock'] = threading.Lock()
        self.__dict__.update(d)
