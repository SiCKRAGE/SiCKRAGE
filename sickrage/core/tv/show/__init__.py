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


import datetime
import glob
import os
import re
import shutil
import stat
import traceback

import send2trash
from sqlalchemy import orm, Column, Integer, Boolean, Text
from sqlalchemy.orm import relationship, object_session
from unidecode import unidecode

import sickrage
from sickrage.core.api import ApiError
from sickrage.core.api.imdb import IMDbAPI
from sickrage.core.blackandwhitelist import BlackAndWhiteList
from sickrage.core.caches.image_cache import ImageCache
from sickrage.core.common import Quality, SKIPPED, WANTED, UNKNOWN, DOWNLOADED, IGNORED, SNATCHED, SNATCHED_PROPER, \
    UNAIRED, ARCHIVED, statusStrings, Overview
from sickrage.core.databases.main import MainDB, MainDBBase
from sickrage.core.exceptions import ShowNotFoundException, \
    EpisodeNotFoundException, EpisodeDeletedException, MultipleEpisodesInDatabaseException
from sickrage.core.helpers import list_media_files, is_media_file, try_int, safe_getattr
from sickrage.core.nameparser import NameParser, InvalidNameException, InvalidShowException
from sickrage.core.tv.episode import TVEpisode
from sickrage.indexers import IndexerApi
from sickrage.indexers.config import INDEXER_TVRAGE
from sickrage.indexers.exceptions import indexer_attributenotfound


class TVShow(MainDBBase):
    __tablename__ = 'tv_shows'

    indexer_id = Column(Integer, index=True, primary_key=True)
    indexer = Column(Integer, index=True, primary_key=True)
    name = Column(Text, default='')
    location = Column(Text, default='')
    network = Column(Text, default='')
    genre = Column(Text, default='')
    overview = Column(Text, default='')
    classification = Column(Text, default='Scripted')
    runtime = Column(Integer, default=0)
    quality = Column(Integer, default=-1)
    airs = Column(Text, default='')
    status = Column(Text, default='')
    flatten_folders = Column(Boolean, default=0)
    paused = Column(Boolean, default=0)
    air_by_date = Column(Boolean, default=0)
    anime = Column(Boolean, default=0)
    scene = Column(Boolean, default=0)
    sports = Column(Boolean, default=0)
    subtitles = Column(Boolean, default=0)
    dvdorder = Column(Boolean, default=0)
    skip_downloaded = Column(Boolean, default=0)
    startyear = Column(Integer, default=0)
    lang = Column(Text, default='')
    imdb_id = Column(Text, default='')
    rls_ignore_words = Column(Text, default='')
    rls_require_words = Column(Text, default='')
    default_ep_status = Column(Integer, default=SKIPPED)
    sub_use_sr_metadata = Column(Boolean, default=0)
    notify_list = Column(Text, default='')
    search_delay = Column(Integer, default=0)
    last_update = Column(Integer, default=datetime.datetime.now().toordinal())
    last_refresh = Column(Integer, default=datetime.datetime.now().toordinal())
    last_backlog_search = Column(Integer, default=datetime.datetime.now().toordinal())
    last_proper_search = Column(Integer, default=datetime.datetime.now().toordinal())

    episodes = relationship('TVEpisode', uselist=True, backref='tv_shows', lazy='joined')
    imdb_info = relationship('IMDbInfo', uselist=False, backref='tv_shows', lazy='joined')

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
    def airs_next(self):
        _airs_next = datetime.date.min
        for episode_object in self.episodes:
            if episode_object.season != 0 and episode_object.status in [UNAIRED, WANTED] and episode_object.airdate >= datetime.date.today() and _airs_next == datetime.date.min:
                _airs_next = episode_object.airdate
        return _airs_next

    @property
    def airs_prev(self):
        _airs_prev = datetime.date.min
        for episode_object in self.episodes:
            if episode_object.season != 0 and episode_object.status != UNAIRED and episode_object.airdate < datetime.date.today() > _airs_prev:
                _airs_prev = episode_object.airdate
        return _airs_prev

    @property
    def episodes_unaired(self):
        _episodes_unaired = 0
        for episode_object in self.episodes:
            if episode_object.season != 0 and episode_object.status == UNAIRED:
                _episodes_unaired += 1
        return _episodes_unaired

    @property
    def episodes_snatched(self):
        _episodes_snatched = 0
        for episode_object in self.episodes:
            if episode_object.season != 0 and episode_object.status in Quality.SNATCHED + Quality.SNATCHED_BEST + Quality.SNATCHED_PROPER:
                _episodes_snatched += 1
        return _episodes_snatched

    @property
    def episodes_downloaded(self):
        _episodes_downloaded = 0
        for episode_object in self.episodes:
            if episode_object.season != 0 and episode_object.status in Quality.DOWNLOADED + Quality.ARCHIVED:
                _episodes_downloaded += 1
        return _episodes_downloaded

    @property
    def episodes_special(self):
        _episodes_specials = 0
        for episode_object in self.episodes:
            if episode_object.season == 0:
                _episodes_specials += 1
        return _episodes_specials

    @property
    def episodes_special_unaired(self):
        _episodes_specials_unaired = 0
        for episode_object in self.episodes:
            if episode_object.season == 0 and episode_object.status == UNAIRED:
                _episodes_specials_unaired += 1
        return _episodes_specials_unaired

    @property
    def episodes_special_downloaded(self):
        _episodes_special_downloaded = 0
        for episode_object in self.episodes:
            if episode_object.season == 0 and episode_object.status in Quality.DOWNLOADED + Quality.ARCHIVED:
                _episodes_special_downloaded += 1
        return _episodes_special_downloaded

    @property
    def episodes_special_snatched(self):
        _episodes_special_snatched = 0
        for episode_object in self.episodes:
            if episode_object.season == 0 and episode_object.status in Quality.SNATCHED + Quality.SNATCHED_BEST + Quality.SNATCHED_PROPER:
                _episodes_special_snatched += 1
        return _episodes_special_snatched

    @property
    def total_size(self):
        _total_size = 0
        for episode_object in self.episodes:
            _total_size += episode_object.file_size
        return _total_size

    @property
    def network_logo_name(self):
        return unidecode(self.network).lower()

    @property
    def release_groups(self):
        if self.is_anime:
            return BlackAndWhiteList(self.indexer_id)

    def load_from_indexer(self, cache=True, tvapi=None):
        if self.indexer is not INDEXER_TVRAGE:
            sickrage.app.log.debug(
                str(self.indexer_id) + ": Loading show info from " + IndexerApi(self.indexer).name)

            t = tvapi
            if not t:
                lINDEXER_API_PARMS = IndexerApi(self.indexer).api_params.copy()
                lINDEXER_API_PARMS['cache'] = cache

                lINDEXER_API_PARMS['language'] = self.lang or sickrage.app.config.indexer_default_language

                if self.dvdorder != 0:
                    lINDEXER_API_PARMS['dvdorder'] = True

                t = IndexerApi(self.indexer).indexer(**lINDEXER_API_PARMS)

            myEp = t[self.indexer_id]
            if not myEp:
                return

            try:
                self.name = myEp['seriesname'].strip()
            except AttributeError:
                raise indexer_attributenotfound("Found %s, but attribute 'seriesname' was empty." % self.indexer_id)

            self.overview = safe_getattr(myEp, 'overview', self.overview)
            self.classification = safe_getattr(myEp, 'classification', self.classification)
            self.genre = safe_getattr(myEp, 'genre', self.genre)
            self.network = safe_getattr(myEp, 'network', self.network)
            self.runtime = try_int(safe_getattr(myEp, 'runtime', self.runtime))
            self.imdb_id = safe_getattr(myEp, 'imdbid', self.imdb_id)

            try:
                self.airs = (safe_getattr(myEp, 'airsdayofweek') + " " + safe_getattr(myEp, 'airstime')).strip()
            except:
                self.airs = ''

            try:
                self.startyear = try_int(str(safe_getattr(myEp, 'firstaired') or datetime.date.min).split('-')[0])
            except:
                self.startyear = 0

            self.status = safe_getattr(myEp, 'status', self.status)
        else:
            sickrage.app.log.warning(str(self.indexer_id) + ": NOT loading info from " + IndexerApi(self.indexer).name + " as it is temporarily disabled.")

        object_session(self).commit()

    def load_episodes_from_indexer(self, cache=True):
        scanned_eps = {}

        l_indexer_api_parms = IndexerApi(self.indexer).api_params.copy()
        l_indexer_api_parms['cache'] = cache

        l_indexer_api_parms['language'] = self.lang or sickrage.app.config.indexer_default_language

        if self.dvdorder != 0:
            l_indexer_api_parms['dvdorder'] = True

        t = IndexerApi(self.indexer).indexer(**l_indexer_api_parms)

        sickrage.app.log.debug(
            str(self.indexer_id) + ": Loading all episodes from " + IndexerApi(self.indexer).name + "..")

        for season in t[self.indexer_id]:
            scanned_eps[season] = {}
            for episode in t[self.indexer_id][season]:
                # need some examples of wtf episode 0 means to decide if we want it or not
                if episode == 0:
                    continue

                try:
                    episode_obj = self.get_episode(season, episode)
                except EpisodeNotFoundException:
                    object_session(self).add(TVEpisode(**{'showid': self.indexer_id,
                                                          'indexer': self.indexer,
                                                          'season': season,
                                                          'episode': episode,
                                                          'location': ''}))
                    object_session(self).commit()
                    episode_obj = self.get_episode(season, episode)

                sickrage.app.log.debug("%s: Loading info from %s for episode S%02dE%02d" % (
                    self.indexer_id, IndexerApi(self.indexer).name, season or 0, episode or 0
                ))

                try:
                    episode_obj.populate_episode(season, episode, tvapi=t)
                except EpisodeNotFoundException:
                    continue

                scanned_eps[season][episode] = True

        # Done updating save last update date
        self.last_update = datetime.date.today().toordinal()

        object_session(self).commit()

        return scanned_eps

    def get_all_episodes(self, season=None, has_location=False):
        results = []

        for x in self.episodes:
            if season and x.season != season:
                continue
            if has_location and x.location == '':
                continue
            results += [x]

        ep_list = []
        for cur_ep in self.episodes:
            cur_ep.related_episodes = []
            if cur_ep.location:
                # if there is a location, check if it's a multi-episode (share_location > 0) and put them in related_episodes
                if len([r for r in results
                        if r.showid == cur_ep.showid and
                           r.season == cur_ep.season and
                           r.location != '' and
                           r.location == cur_ep.location and
                           r.episode != cur_ep.episode]) > 0:

                    related_eps_result = object_session(self).query(TVEpisode).filter_by(showid=self.indexer_id, season=cur_ep.season,
                                                                                         location=cur_ep.location).filter(
                        TVEpisode.episode != cur_ep.episode).order_by(TVEpisode.episode)

                    for cur_related_ep in related_eps_result:
                        try:
                            related_ep = self.get_episode(int(cur_related_ep.season), int(cur_related_ep.episode))
                            if related_ep not in cur_ep.related_episodes:
                                cur_ep.related_episodes.append(related_ep)
                        except EpisodeNotFoundException:
                            pass

            ep_list.append(cur_ep)

        return ep_list

    def get_episode(self, season=None, episode=None, absolute_number=None):
        from sickrage.core.tv.episode import TVEpisode

        if all([absolute_number is not None, season is None, episode is None]):
            try:
                dbData = object_session(self).query(TVEpisode).filter_by(showid=self.indexer_id,
                                                                         absolute_number=absolute_number).filter(TVEpisode.season != 0).one()
                episode = dbData.episode
                season = dbData.season

                sickrage.app.log.debug("Found episode by absolute_number %s which is S%02dE%02d" % (absolute_number, season or 0, episode or 0))

                return dbData
            except orm.exc.MultipleResultsFound:
                sickrage.app.log.warning("Multiple entries for absolute number: " + str(absolute_number) + " in show: " + self.name + " found ")
                raise MultipleEpisodesInDatabaseException
            except orm.exc.NoResultFound:
                sickrage.app.log.debug("No entries for absolute number: " + str(absolute_number) + " in show: " + self.name + " found.")
                raise EpisodeNotFoundException

        try:
            return object_session(self).query(TVEpisode).filter_by(showid=self.indexer_id, season=season, episode=episode).one()
        except orm.exc.NoResultFound:
            raise EpisodeNotFoundException

    def write_show_nfo(self, force=False):
        result = False

        if not os.path.isdir(self.location):
            sickrage.app.log.info(str(self.indexer_id) + ": Show dir doesn't exist, skipping NFO generation")
            return False

        sickrage.app.log.debug(str(self.indexer_id) + ": Writing NFOs for show")
        for cur_provider in sickrage.app.metadata_providers.values():
            result = cur_provider.create_show_metadata(self, force) or result

        return result

    def write_metadata(self, show_only=False, force=False):
        if not os.path.isdir(self.location):
            sickrage.app.log.info(str(self.indexer_id) + ": Show dir doesn't exist, skipping NFO generation")
            return

        self.get_images()

        self.write_show_nfo(force)

        if not show_only:
            self.write_episode_nfos(force)
            self.update_episode_video_metadata()

    def write_episode_nfos(self, force=False):
        if not os.path.isdir(self.location):
            sickrage.app.log.info(str(self.indexer_id) + ": Show dir doesn't exist, skipping NFO generation")
            return

        sickrage.app.log.debug(str(self.indexer_id) + ": Writing NFOs for all episodes")

        for episode_obj in self.episodes:
            if episode_obj.location == '':
                continue

            sickrage.app.log.debug(str(self.indexer_id) + ": Retrieving/creating episode S%02dE%02d" % (episode_obj.season or 0, episode_obj.episode or 0))

            episode_obj.create_meta_files(force)

    def update_episode_video_metadata(self):
        if not os.path.isdir(self.location):
            sickrage.app.log.info(str(self.indexer_id) + ": Show dir doesn't exist, skipping video metadata updating")
            return

        sickrage.app.log.debug(str(self.indexer_id) + ": Updating video metadata for all episodes")

        for episode_obj in self.episodes:
            if episode_obj.location == '':
                continue

            sickrage.app.log.debug(
                str(self.indexer_id) + ": Updating video metadata for episode S%02dE%02d" % (episode_obj.season, episode_obj.episode))

            episode_obj.update_video_metadata()

    # find all media files in the show folder and create episodes for as many as possible
    def load_episodes_from_dir(self):
        if not os.path.isdir(self.location):
            sickrage.app.log.debug(str(self.indexer_id) + ": Show dir doesn't exist, not loading episodes from disk")
            return

        sickrage.app.log.debug(str(self.indexer_id) + ": Loading all episodes from the show directory " + self.location)

        # get file list
        media_files = list_media_files(self.location)

        # create TVEpisodes from each media file (if possible)
        for mediaFile in media_files:
            curEpisode = None

            sickrage.app.log.debug(str(self.indexer_id) + ": Creating episode from " + mediaFile)
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
                parse_result = NameParser(False, show_id=self.indexer_id).parse(ep_file_name)
            except (InvalidNameException, InvalidShowException):
                parse_result = None

            if ' ' not in ep_file_name and parse_result and parse_result.release_group:
                sickrage.app.log.debug("Name " + ep_file_name + " gave release group of " + parse_result.release_group + ", seems valid")
                curEpisode.release_name = ep_file_name
                object_session(self).commit()

            # store the reference in the show
            if self.subtitles and sickrage.app.config.use_subtitles:
                try:
                    curEpisode.refresh_subtitles()
                except Exception:
                    sickrage.app.log.error("%s: Could not refresh subtitles" % self.indexer_id)
                    sickrage.app.log.debug(traceback.format_exc())

    def load_imdb_info(self):
        imdb_info_mapper = {
            'imdbvotes': 'votes',
            'imdbrating': 'rating',
            'totalseasons': 'seasons',
            'imdbid': 'imdb_id'
        }

        if not self.imdb_id:
            try:
                resp = IMDbAPI().search_by_imdb_title(self.name)
            except ApiError as e:
                sickrage.app.log.error('{!r}'.format(e))
                resp = {}

            for x in resp.get('Search', []):
                try:
                    if int(x.get('Year'), 0) == self.startyear and x.get('Title') in self.name:
                        self.imdb_id = x.get('imdbID')
                        object_session(self).commit()
                        break
                except:
                    continue

        if self.imdb_id:
            sickrage.app.log.debug(str(self.indexer_id) + ": Obtaining IMDb info")

            try:
                imdb_info = IMDbAPI().search_by_imdb_id(self.imdb_id)
            except ApiError as e:
                imdb_info = None
                sickrage.app.log.error('{!r}'.format(e))

            if not imdb_info:
                sickrage.app.log.debug(str(self.indexer_id) + ': Unable to obtain IMDb info')
                return

            imdb_info = dict((k.lower(), v) for k, v in imdb_info.items())
            for column in imdb_info.copy():
                if column in imdb_info_mapper:
                    imdb_info[imdb_info_mapper[column]] = imdb_info[column]

                if column not in MainDB.IMDbInfo.__table__.columns.keys():
                    del imdb_info[column]

            if not all([imdb_info.get('imdb_id'), imdb_info.get('votes'), imdb_info.get('rating'), imdb_info.get('genre')]):
                sickrage.app.log.debug(str(self.indexer_id) + ': IMDb info obtained does not meet our requirements')
                return

            sickrage.app.log.debug(str(self.indexer_id) + ": Obtained IMDb info ->" + str(imdb_info))

            # save imdb info to database
            imdb_info.update({
                'indexer_id': self.indexer_id,
                'last_update': datetime.date.today().toordinal()
            })

            try:
                dbData = object_session(self).query(MainDB.IMDbInfo).filter_by(indexer_id=self.indexer_id).one()
                dbData.update(**imdb_info)
            except orm.exc.NoResultFound:
                object_session(self).add(MainDB.IMDbInfo(**imdb_info))
            finally:
                object_session(self).commit()

    def get_images(self, fanart=None, poster=None):
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

    def make_ep_from_file(self, filename):
        if not os.path.isfile(filename):
            sickrage.app.log.info(str(self.indexer_id) + ": That isn't even a real file dude... " + filename)
            return None

        sickrage.app.log.debug(str(self.indexer_id) + ": Creating episode object from " + filename)

        try:
            parse_result = NameParser(validate_show=False).parse(filename, skip_scene_detection=True)
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
        root_ep = None

        for curEpNum in parse_result.episode_numbers:
            episode = int(curEpNum)

            sickrage.app.log.debug("%s: %s parsed to %s S%02dE%02d" % (self.indexer_id, filename, self.name, season or 0, episode or 0))

            check_quality_again = False

            try:
                episode_obj = self.get_episode(season, episode)
            except EpisodeNotFoundException:
                object_session(self).add(TVEpisode(**{'showid': self.indexer_id,
                                                      'indexer': self.indexer,
                                                      'season': season,
                                                      'episode': episode,
                                                      'location': filename}))
                object_session(self).commit()
                episode_obj = self.get_episode(season, episode)

            # if there is a new file associated with this ep then re-check the quality
            if episode_obj.location and os.path.normpath(episode_obj.location) != os.path.normpath(filename):
                sickrage.app.log.debug("The old episode had a different file associated with it, I will re-check "
                                       "the quality based on the new filename " + filename)
                check_quality_again = True

            # if the sizes are the same then it's probably the same file
            old_size = episode_obj.file_size
            episode_obj.location = filename
            same_file = old_size and episode_obj.file_size == old_size
            episode_obj.checkForMetaFiles()

            if root_ep is None:
                root_ep = episode_obj
            else:
                if episode_obj not in root_ep.related_episodes:
                    root_ep.related_episodes.append(episode_obj)

            # if it's a new file then
            if not same_file:
                episode_obj.release_name = ''

            # if they replace a file on me I'll make some attempt at re-checking the quality unless I know it's the
            # same file
            if check_quality_again and not same_file:
                new_quality = Quality.name_quality(filename, self.is_anime)
                sickrage.app.log.debug("Since this file has been renamed")

                episode_obj.status = Quality.composite_status(DOWNLOADED, new_quality)

            # check for status/quality changes as long as it's a new file
            elif not same_file and is_media_file(
                    filename) and episode_obj.status not in Quality.DOWNLOADED + Quality.ARCHIVED + [IGNORED]:
                old_status, old_quality = Quality.split_composite_status(episode_obj.status)
                new_quality = Quality.name_quality(filename, self.is_anime)

                new_status = None

                # if it was snatched and now exists then set the status correctly
                if old_status == SNATCHED and old_quality <= new_quality:
                    sickrage.app.log.debug(
                        "STATUS: this ep used to be snatched with quality " + Quality.qualityStrings[
                            old_quality] +
                        " but a file exists with quality " + Quality.qualityStrings[new_quality] +
                        " so I'm setting the status to DOWNLOADED")
                    new_status = DOWNLOADED

                # if it was snatched proper and we found a higher quality one then allow the status change
                elif old_status == SNATCHED_PROPER and old_quality < new_quality:
                    sickrage.app.log.debug(
                        "STATUS: this ep used to be snatched proper with quality " + Quality.qualityStrings[
                            old_quality] +
                        " but a file exists with quality " + Quality.qualityStrings[new_quality] +
                        " so I'm setting the status to DOWNLOADED")
                    new_status = DOWNLOADED

                elif old_status not in (SNATCHED, SNATCHED_PROPER):
                    new_status = DOWNLOADED

                if new_status is not None:
                    sickrage.app.log.debug(
                        "STATUS: we have an associated file, so setting the status from " + str(
                            episode_obj.status) + " to DOWNLOADED/" + str(
                            Quality.status_from_name(filename, anime=self.is_anime)))
                    episode_obj.status = Quality.composite_status(new_status, new_quality)

        # creating metafiles on the root should be good enough
        if root_ep:
            root_ep.create_meta_files()

        object_session(self).commit()

        return root_ep

    def delete_show(self, full=False):
        # choose delete or trash action
        action = ('delete', 'trash')[sickrage.app.config.trash_remove_show]

        # remove from tv episodes table
        object_session(self).query(TVEpisode).filter_by(showid=self.indexer_id).delete()

        # remove from tv shows table
        object_session(self).query(self.__class__).filter_by(indexer_id=self.indexer_id).delete()

        # remove from imdb info table
        object_session(self).query(MainDB.IMDbInfo).filter_by(indexer_id=self.indexer_id).delete()

        # remove from xem scene table
        object_session(self).query(MainDB.XEMRefresh).filter_by(indexer_id=self.indexer_id).delete()

        # remove from scene numbering table
        object_session(self).query(MainDB.SceneNumbering).filter_by(indexer_id=self.indexer_id).delete()

        # clear the cache
        image_cache_dir = os.path.join(sickrage.app.cache_dir, 'images')
        for cache_file in glob.glob(os.path.join(image_cache_dir, str(self.indexer_id) + '.*')):
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
            sickrage.app.log.debug("Removing show: {}, {} from watchlist".format(self.indexer_id, self.name))
            sickrage.app.notifier_providers['trakt'].update_watchlist(self, update="remove")

    def populate_cache(self, force=False):
        sickrage.app.log.debug("Checking & filling cache for show " + self.name)
        ImageCache().fill_cache(self, force)

    def refresh_dir(self):
        # make sure the show dir is where we think it is unless dirs are created on the fly
        if not os.path.isdir(self.location) and not sickrage.app.config.create_missing_show_dirs:
            return False

        # load from dir
        try:
            self.load_episodes_from_dir()
        except Exception as e:
            sickrage.app.log.debug("Error searching dir for episodes: {}".format(e))
            sickrage.app.log.debug(traceback.format_exc())

        # run through all locations from DB, check that they exist
        sickrage.app.log.debug(str(self.indexer_id) + ": Loading all episodes with a location from the database")

        for curEp in self.episodes:
            if curEp.location == '':
                continue

            curLoc = os.path.normpath(curEp.location)
            season = int(curEp.season)
            episode = int(curEp.episode)

            # if the path doesn't exist or if it's not in our show dir
            if not os.path.isfile(curLoc) or not os.path.normpath(curLoc).startswith(os.path.normpath(self.location)):
                # check if downloaded files still exist, update our data if this has changed
                if not sickrage.app.config.skip_removed_files:
                    # if it used to have a file associated with it and it doesn't anymore then set it to
                    # EP_DEFAULT_DELETED_STATUS
                    if curEp.location and curEp.status in Quality.DOWNLOADED:
                        if sickrage.app.config.ep_default_deleted_status == ARCHIVED:
                            __, oldQuality = Quality.split_composite_status(curEp.status)
                            new_status = Quality.composite_status(ARCHIVED, oldQuality)
                        else:
                            new_status = sickrage.app.config.ep_default_deleted_status

                        sickrage.app.log.debug("%s: Location for S%02dE%02d doesn't exist, "
                                               "removing it and changing our status to %s" % (self.indexer_id,
                                                                                              season or 0,
                                                                                              episode or 0,
                                                                                              statusStrings[new_status]))

                        curEp.status = new_status
                        curEp.subtitles = ''
                        curEp.subtitles_searchcount = 0
                        curEp.subtitles_lastsearch = 0

                    curEp.location = ''
                    curEp.hasnfo = False
                    curEp.hastbn = False
                    curEp.release_name = ''
            else:
                if curEp.status in Quality.ARCHIVED:
                    __, oldQuality = Quality.split_composite_status(curEp.status)
                    curEp.status = Quality.composite_status(DOWNLOADED, oldQuality)

                # the file exists, set its modify file stamp
                if sickrage.app.config.airdate_episodes:
                    curEp.airdateModifyStamp()

    def download_subtitles(self):
        if not os.path.isdir(self.location):
            sickrage.app.log.debug(str(self.indexer_id) + ": Show dir doesn't exist, can't download subtitles")
            return

        sickrage.app.log.debug("%s: Downloading subtitles" % self.indexer_id)

        try:
            for episode in self.episodes:
                episode.download_subtitles()
        except Exception:
            sickrage.app.log.error("%s: Error occurred when downloading subtitles for %s" % (self.indexer_id, self.name))

    def qualitiesToString(self, qualities=None):
        if qualities is None:
            qualities = []

        result = ''
        for quality in qualities:
            if quality in Quality.qualityStrings:
                result += Quality.qualityStrings[quality] + ', '
            else:
                sickrage.app.log.info("Bad quality value: " + str(quality))

        result = re.sub(', $', '', result)

        if not len(result):
            result = 'None'

        return result

    def want_episode(self, season, episode, quality, manualSearch=False, downCurQuality=False):
        try:
            episode_object = self.get_episode(season, episode)
        except EpisodeNotFoundException:
            sickrage.app.log.debug("Unable to find a matching episode in database, ignoring found episode")
            return False

        sickrage.app.log.debug("Checking if found episode %s S%02dE%02d is wanted at quality %s" % (
            self.name, episode_object.season or 0, episode_object.episode or 0, Quality.qualityStrings[quality]))

        # if the quality isn't one we want under any circumstances then just say no
        any_qualities, best_qualities = Quality.split_quality(self.quality)
        sickrage.app.log.debug("Any, Best = [{}] [{}] Found = [{}]".format(
            self.qualitiesToString(any_qualities),
            self.qualitiesToString(best_qualities),
            self.qualitiesToString([quality]))
        )

        if quality not in any_qualities + best_qualities or quality is UNKNOWN:
            sickrage.app.log.debug("Don't want this quality, ignoring found episode")
            return False

        ep_status = int(episode_object.status)
        ep_status_text = statusStrings[ep_status]

        sickrage.app.log.debug("Existing episode status: " + str(ep_status) + " (" + ep_status_text + ")")

        # if we know we don't want it then just say no
        if ep_status in Quality.ARCHIVED + [UNAIRED, SKIPPED, IGNORED] and not manualSearch:
            sickrage.app.log.debug("Existing episode status is unaired/skipped/ignored/archived, ignoring found episode")
            return False

        cur_status, cur_quality = Quality.split_composite_status(ep_status)

        # if it's one of these then we want it as long as it's in our allowed initial qualities
        if ep_status == WANTED:
            sickrage.app.log.debug("Existing episode status is WANTED, getting found episode")
            return True
        elif manualSearch:
            if (downCurQuality and quality >= cur_quality) or (not downCurQuality and quality > cur_quality):
                sickrage.app.log.debug("Usually ignoring found episode, but forced search allows the quality, getting found episode")
                return True

        # if we are re-downloading then we only want it if it's in our bestQualities list and better than what we
        # have, or we only have one bestQuality and we do not have that quality yet
        if ep_status in Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_PROPER and quality in best_qualities and (
                quality > cur_quality or cur_quality not in best_qualities):
            sickrage.app.log.debug("Episode already exists but the found episode quality is wanted more, getting found episode")
            return True
        elif cur_quality == UNKNOWN and manualSearch:
            sickrage.app.log.debug("Episode already exists but quality is Unknown, getting found episode")
            return True
        else:
            sickrage.app.log.debug("Episode already exists and the found episode has same/lower quality, ignoring found episode")

        sickrage.app.log.debug("None of the conditions were met, ignoring found episode")
        return False

    def get_overview(self, epStatus):
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
            anyQualities, bestQualities = Quality.split_quality(self.quality)
            epStatus, curQuality = Quality.split_composite_status(epStatus)

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

    def get_all_episodes_from_absolute_number(self, absolute_numbers):
        episodes = []
        season = None

        if len(absolute_numbers):
            for absolute_number in absolute_numbers:
                try:
                    ep = self.get_episode(absolute_number=absolute_number)
                    episodes.append(ep.episode)
                    season = ep.season
                except (EpisodeNotFoundException, MultipleEpisodesInDatabaseException):
                    continue

        return season, episodes

    def __str__(self):
        toReturn = ""
        toReturn += "indexer_id: " + str(self.indexer_id) + "\n"
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
