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
import threading
import traceback

import send2trash
import sqlalchemy
from adba.aniDBAbstracter import Anime
from sqlalchemy import orm
from unidecode import unidecode

import sickrage
from sickrage.core.blackandwhitelist import BlackAndWhiteList
from sickrage.core.caches.image_cache import ImageCache
from sickrage.core.common import Quality, Qualities, EpisodeStatus
from sickrage.core.databases.main import MainDB
from sickrage.core.databases.main.schemas import TVShowSchema, IMDbInfoSchema, BlacklistSchema, WhitelistSchema
from sickrage.core.enums import SeriesProviderID
from sickrage.core.exceptions import ShowNotFoundException, EpisodeNotFoundException, EpisodeDeletedException, MultipleEpisodesInDatabaseException
from sickrage.core.helpers import list_media_files, is_media_file, try_int, safe_getattr, flatten
from sickrage.core.media.util import series_image, SeriesImageType
from sickrage.core.tv.episode import TVEpisode
from sickrage.series_providers.exceptions import SeriesProviderAttributeNotFound, SeriesProviderException


class TVShowID(object):
    def __init__(self, series_id, series_provider_id):
        self.series_id = series_id
        self.series_provider_id = series_provider_id

    @property
    def slug(self):
        return f'{self.series_id}-{self.series_provider_id.slug}'


class TVShow(object):
    def __init__(self, series_id, series_provider_id, lang='en', location=''):
        self.lock = threading.Lock()
        self._episodes = {}

        with sickrage.app.main_db.session() as session:
            try:
                query = session.query(MainDB.TVShow).filter_by(series_id=series_id, series_provider_id=series_provider_id).one()
                self._data_local = query.as_dict()
            except orm.exc.NoResultFound:
                self._data_local = MainDB.TVShow().as_dict()
                self._data_local.update(**{
                    'series_id': series_id,
                    'series_provider_id': series_provider_id,
                    'lang': lang,
                    'location': location
                })

                self.load_from_series_provider()

        sickrage.app.shows.update({(self.series_id, self.series_provider_id): self})

    @property
    def slug(self):
        return f'{self.series_id}-{self.series_provider_id.slug}'

    @property
    def series_id(self):
        return self._data_local['series_id']

    @series_id.setter
    def series_id(self, value):
        self._data_local['series_id'] = value

    @property
    def series_provider_id(self):
        return self._data_local['series_provider_id']

    @series_provider_id.setter
    def series_provider_id(self, value):
        self._data_local['series_provider_id'] = value

    @property
    def tvdb_id(self):
        if self.series_provider_id == SeriesProviderID.THETVDB:
            return self.series_id

    @property
    def name(self):
        return self._data_local['name']

    @name.setter
    def name(self, value):
        self._data_local['name'] = value

    @property
    def location(self):
        return self._data_local['location']

    @location.setter
    def location(self, value):
        self._data_local['location'] = value

    @property
    def network(self):
        return self._data_local['network']

    @network.setter
    def network(self, value):
        self._data_local['network'] = value

    @property
    def genre(self):
        return self._data_local['genre']

    @genre.setter
    def genre(self, value):
        self._data_local['genre'] = value

    @property
    def overview(self):
        return self._data_local['overview']

    @overview.setter
    def overview(self, value):
        self._data_local['overview'] = value

    @property
    def classification(self):
        return self._data_local['classification']

    @classification.setter
    def classification(self, value):
        self._data_local['classification'] = value

    @property
    def runtime(self):
        return self._data_local['runtime']

    @runtime.setter
    def runtime(self, value):
        self._data_local['runtime'] = value

    @property
    def quality(self):
        return self._data_local['quality']

    @quality.setter
    def quality(self, value):
        self._data_local['quality'] = value

    @property
    def airs(self):
        return self._data_local['airs']

    @airs.setter
    def airs(self, value):
        self._data_local['airs'] = value

    @property
    def status(self):
        return self._data_local['status']

    @status.setter
    def status(self, value):
        self._data_local['status'] = value

    @property
    def flatten_folders(self):
        return self._data_local['flatten_folders']

    @flatten_folders.setter
    def flatten_folders(self, value):
        self._data_local['flatten_folders'] = value

    @property
    def paused(self):
        return self._data_local['paused']

    @paused.setter
    def paused(self, value):
        self._data_local['paused'] = value

    @property
    def scene(self):
        return self._data_local['scene']

    @scene.setter
    def scene(self, value):
        self._data_local['scene'] = value

    @property
    def anime(self):
        return self._data_local['anime']

    @anime.setter
    def anime(self, value):
        self._data_local['anime'] = value

    @property
    def search_format(self):
        return self._data_local['search_format']

    @search_format.setter
    def search_format(self, value):
        self._data_local['search_format'] = value

    @property
    def subtitles(self):
        return self._data_local['subtitles']

    @subtitles.setter
    def subtitles(self, value):
        self._data_local['subtitles'] = value

    @property
    def dvd_order(self):
        return self._data_local['dvd_order']

    @dvd_order.setter
    def dvd_order(self, value):
        self._data_local['dvd_order'] = value

    @property
    def skip_downloaded(self):
        return self._data_local['skip_downloaded']

    @skip_downloaded.setter
    def skip_downloaded(self, value):
        self._data_local['skip_downloaded'] = value

    @property
    def startyear(self):
        return self._data_local['startyear']

    @startyear.setter
    def startyear(self, value):
        self._data_local['startyear'] = value

    @property
    def lang(self):
        return self._data_local['lang']

    @lang.setter
    def lang(self, value):
        self._data_local['lang'] = value

    @property
    def imdb_id(self):
        return self._data_local['imdb_id']

    @imdb_id.setter
    def imdb_id(self, value):
        self._data_local['imdb_id'] = value

    @property
    def rls_ignore_words(self):
        return self._data_local['rls_ignore_words']

    @rls_ignore_words.setter
    def rls_ignore_words(self, value):
        self._data_local['rls_ignore_words'] = value

    @property
    def rls_require_words(self):
        return self._data_local['rls_require_words']

    @rls_require_words.setter
    def rls_require_words(self, value):
        self._data_local['rls_require_words'] = value

    @property
    def default_ep_status(self):
        return self._data_local['default_ep_status']

    @default_ep_status.setter
    def default_ep_status(self, value):
        self._data_local['default_ep_status'] = value

    @property
    def sub_use_sr_metadata(self):
        return self._data_local['sub_use_sr_metadata']

    @sub_use_sr_metadata.setter
    def sub_use_sr_metadata(self, value):
        self._data_local['sub_use_sr_metadata'] = value

    @property
    def notify_list(self):
        return self._data_local['notify_list']

    @notify_list.setter
    def notify_list(self, value):
        self._data_local['notify_list'] = value

    @property
    def search_delay(self):
        return self._data_local['search_delay']

    @search_delay.setter
    def search_delay(self, value):
        self._data_local['search_delay'] = value

    @property
    def scene_exceptions(self):
        if self._data_local['scene_exceptions']:
            return list(filter(None, self._data_local['scene_exceptions'].split(',')))
        return []

    @scene_exceptions.setter
    def scene_exceptions(self, value):
        self._data_local['scene_exceptions'] = ','.join(value)

    @property
    def last_update(self):
        return self._data_local['last_update']

    @last_update.setter
    def last_update(self, value):
        self._data_local['last_update'] = value

    @property
    def last_refresh(self):
        return self._data_local['last_refresh']

    @last_refresh.setter
    def last_refresh(self, value):
        self._data_local['last_refresh'] = value

    @property
    def last_backlog_search(self):
        return self._data_local['last_backlog_search']

    @last_backlog_search.setter
    def last_backlog_search(self, value):
        self._data_local['last_backlog_search'] = value

    @property
    def last_proper_search(self):
        return self._data_local['last_proper_search']

    @last_proper_search.setter
    def last_proper_search(self, value):
        self._data_local['last_proper_search'] = value

    @property
    def last_scene_exceptions_refresh(self):
        return self._data_local['last_scene_exceptions_refresh']

    @last_scene_exceptions_refresh.setter
    def last_scene_exceptions_refresh(self, value):
        self._data_local['last_scene_exceptions_refresh'] = value

    @property
    def last_xem_refresh(self):
        return self._data_local['last_xem_refresh']

    @last_xem_refresh.setter
    def last_xem_refresh(self, value):
        self._data_local['last_xem_refresh'] = value

    @property
    def series_provider(self):
        return sickrage.app.series_providers[self.series_provider_id]

    @property
    def episodes(self):
        if not self._episodes:
            with sickrage.app.main_db.session() as session:
                for x in session.query(MainDB.TVEpisode).filter_by(series_id=self.series_id, series_provider_id=self.series_provider_id):
                    self._episodes[x.episode_id] = TVEpisode(series_id=x.series_id, series_provider_id=x.series_provider_id, season=x.season, episode=x.episode)
        return list(self._episodes.values())

    @property
    def imdb_info(self):
        with sickrage.app.main_db.session() as session:
            return session.query(MainDB.IMDbInfo).filter_by(series_id=self.series_id).one_or_none()

    @property
    def is_anime(self):
        return int(self.anime) > 0

    @property
    def airs_next(self):
        _airs_next = datetime.date.min

        with sickrage.app.main_db.session() as session:
            query = session.query(
                MainDB.TVEpisode
            ).filter_by(
                series_id=self.series_id, series_provider_id=self.series_provider_id
            ).filter(
                MainDB.TVEpisode.season > 0,
                MainDB.TVEpisode.airdate >= datetime.date.today(),
                MainDB.TVEpisode.status.in_([EpisodeStatus.UNAIRED, EpisodeStatus.WANTED])
            ).order_by(
                MainDB.TVEpisode.airdate
            ).first()

            if query:
                _airs_next = query.airdate

        return _airs_next

    @property
    def airs_prev(self):
        _airs_prev = datetime.date.min

        with sickrage.app.main_db.session() as session:
            query = session.query(
                MainDB.TVEpisode
            ).filter_by(
                series_id=self.series_id, series_provider_id=self.series_provider_id
            ).filter(
                MainDB.TVEpisode.season > 0,
                MainDB.TVEpisode.airdate < datetime.date.today(),
                MainDB.TVEpisode.status != EpisodeStatus.UNAIRED
            ).order_by(
                sqlalchemy.desc(MainDB.TVEpisode.airdate)
            ).first()

            if query:
                _airs_prev = query.airdate

        return _airs_prev

    @property
    def episodes_unaired(self):
        with sickrage.app.main_db.session() as session:
            query = session.query(
                MainDB.TVEpisode.season, MainDB.TVEpisode.status
            ).filter_by(
                series_id=self.series_id, series_provider_id=self.series_provider_id
            ).filter(
                MainDB.TVEpisode.status == EpisodeStatus.UNAIRED
            )

            if not sickrage.app.config.gui.display_show_specials:
                query = query.filter(MainDB.TVEpisode.season > 0)

        return query.count()

    @property
    def episodes_snatched(self):
        with sickrage.app.main_db.session() as session:
            query = session.query(
                MainDB.TVEpisode.season, MainDB.TVEpisode.status
            ).filter_by(
                series_id=self.series_id, series_provider_id=self.series_provider_id
            ).filter(
                MainDB.TVEpisode.status.in_(flatten([EpisodeStatus.composites(EpisodeStatus.SNATCHED), EpisodeStatus.composites(EpisodeStatus.SNATCHED_BEST),
                                                     EpisodeStatus.composites(EpisodeStatus.SNATCHED_PROPER)]))
            )

            if not sickrage.app.config.gui.display_show_specials:
                query = query.filter(MainDB.TVEpisode.season > 0)

        return query.count()

    @property
    def episodes_downloaded(self):
        with sickrage.app.main_db.session() as session:
            query = session.query(
                MainDB.TVEpisode.season, MainDB.TVEpisode.status
            ).filter_by(
                series_id=self.series_id, series_provider_id=self.series_provider_id
            ).filter(
                MainDB.TVEpisode.status.in_(flatten([EpisodeStatus.composites(EpisodeStatus.DOWNLOADED), EpisodeStatus.composites(EpisodeStatus.ARCHIVED)]))
            )

            if not sickrage.app.config.gui.display_show_specials:
                query = query.filter(MainDB.TVEpisode.season > 0)

        return query.count()

    @property
    def episodes_special(self):
        with sickrage.app.main_db.session() as session:
            query = session.query(
                MainDB.TVEpisode.season
            ).filter_by(
                series_id=self.series_id, series_provider_id=self.series_provider_id
            ).filter(
                MainDB.TVEpisode.season == 0
            )

        return query.count()

    @property
    def episodes_total(self):
        with sickrage.app.main_db.session() as session:
            query = session.query(
                MainDB.TVEpisode.season, MainDB.TVEpisode.status
            ).filter_by(
                series_id=self.series_id, series_provider_id=self.series_provider_id
            ).filter(
                MainDB.TVEpisode.status != EpisodeStatus.UNAIRED
            )

            if not sickrage.app.config.gui.display_show_specials:
                query = query.filter(MainDB.TVEpisode.season > 0)

        return query.count()

    @property
    def new_episodes(self):
        cur_date = datetime.date.today()
        cur_date += datetime.timedelta(days=1)
        cur_time = datetime.datetime.now(sickrage.app.tz)

        new_episodes = []
        for episode_object in self.episodes:
            if episode_object.status != EpisodeStatus.UNAIRED or episode_object.season == 0 or not episode_object.airdate > datetime.date.min:
                continue

            air_date = episode_object.airdate
            air_date += datetime.timedelta(days=episode_object.show.search_delay)
            if not cur_date >= air_date:
                continue

            if episode_object.show.airs and episode_object.show.network:
                # This is how you assure it is always converted to local time
                air_time = sickrage.app.tz_updater.parse_date_time(episode_object.airdate,
                                                                   episode_object.show.airs,
                                                                   episode_object.show.network).astimezone(sickrage.app.tz)

                # filter out any episodes that haven't started airing yet,
                # but set them to the default status while they are airing
                # so they are snatched faster
                if air_time > cur_time:
                    continue

            new_episodes += [episode_object]

        return new_episodes

    @property
    def total_size(self):
        _total_size = 0
        _related_episodes = set()
        for episode_object in self.episodes:
            [_related_episodes.add(related_episode.episode_id) for related_episode in episode_object.related_episodes]
            if episode_object.episode_id not in _related_episodes:
                _total_size += episode_object.file_size
        return _total_size

    @property
    def network_logo_name(self):
        return unidecode(self.network).lower()

    @property
    def release_groups(self):
        if self.is_anime:
            return BlackAndWhiteList(self.series_id, self.series_provider_id)

    @property
    def poster(self):
        return series_image(self.series_id, self.series_provider_id, SeriesImageType.POSTER).url

    @property
    def banner(self):
        return series_image(self.series_id, self.series_provider_id, SeriesImageType.BANNER).url

    @property
    def allowed_qualities(self):
        allowed_qualities, __ = Quality.split_quality(self.quality)
        return allowed_qualities

    @property
    def preferred_qualities(self):
        __, preferred_qualities = Quality.split_quality(self.quality)
        return preferred_qualities

    @property
    def show_queue_status(self):
        if sickrage.app.show_queue.is_being_added(self.series_id):
            return {
                'action': 'ADD',
                'message': _('This show is in the process of being downloaded - the info below is incomplete.')
            }
        elif sickrage.app.show_queue.is_being_removed(self.series_id):
            return {
                'action': 'REMOVE',
                'message': _('This show is in the process of being removed.')
            }
        elif sickrage.app.show_queue.is_being_updated(self.series_id):
            return {
                'action': 'UPDATE',
                'message': _('The information on this page is in the process of being updated.')
            }
        elif sickrage.app.show_queue.is_being_refreshed(self.series_id):
            return {
                'action': 'REFRESH',
                'message': _('The episodes below are currently being refreshed from disk')
            }
        elif sickrage.app.show_queue.is_being_subtitled(self.series_id):
            return {
                'action': 'SUBTITLE',
                'message': _('Currently downloading subtitles for this show')
            }
        elif sickrage.app.show_queue.is_queued_to_refresh(self.series_id):
            return {
                'action': 'REFRESH_QUEUE',
                'message': _('This show is queued to be refreshed.')
            }
        elif sickrage.app.show_queue.is_queued_to_update(self.series_id):
            return {
                'action': 'UPDATE_QUEUE',
                'message': _('This show is queued and awaiting an update.')
            }
        elif sickrage.app.show_queue.is_queued_to_subtitle(self.series_id):
            return {
                'action': 'SUBTITLE_QUEUE',
                'message': _('This show is queued and awaiting subtitles download.')
            }

        return {}

    @property
    def is_loading(self):
        return self.show_queue_status.get('action') == 'ADD'

    @property
    def is_removing(self):
        return self.show_queue_status.get('action') == 'REMOVE'

    def save(self):
        with self.lock, sickrage.app.main_db.session() as session:
            sickrage.app.log.debug("{0:d}: Saving to database: {1}".format(self.series_id, self.name))

            try:
                query = session.query(MainDB.TVShow).filter_by(series_id=self.series_id, series_provider_id=self.series_provider_id).one()
                query.update(**self._data_local)
            except orm.exc.NoResultFound:
                session.add(MainDB.TVShow(**self._data_local))
            finally:
                session.commit()

    def delete(self):
        with self.lock, sickrage.app.main_db.session() as session:
            session.query(MainDB.TVShow).filter_by(series_id=self.series_id, series_provider_id=self.series_provider_id).delete()
            session.commit()

    def flush_episodes(self):
        self._episodes.clear()

    def load_from_series_provider(self, cache=True):
        sickrage.app.log.debug(str(self.series_id) + ": Loading show info from " + self.series_provider.name)

        series_provider_language = self.lang or sickrage.app.config.general.series_provider_default_language

        myEp = self.series_provider.search(self.series_id, language=series_provider_language, enable_cache=cache)
        if not myEp:
            raise SeriesProviderException

        try:
            self.name = myEp['seriesname'].strip()
        except AttributeError:
            raise SeriesProviderAttributeNotFound("Found %s, but attribute 'seriesname' was empty." % self.series_id)

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

        self.save()

    def load_episodes_from_series_provider(self, cache=True):
        scanned_eps = {}

        series_provider_language = self.lang or sickrage.app.config.general.series_provider_default_language

        sickrage.app.log.debug(str(self.series_id) + ": Loading all episodes from " + self.series_provider.name + "..")

        # flush episodes from cache so we can reload from database
        self.flush_episodes()

        series_provider_data = self.series_provider.search(self.series_id, language=series_provider_language, enable_cache=cache)
        if not series_provider_data:
            raise SeriesProviderException

        for season in series_provider_data:
            scanned_eps[season] = {}
            for episode in series_provider_data[season]:
                # need some examples of wtf episode 0 means to decide if we want it or not
                if episode == 0:
                    continue

                try:
                    episode_obj = self.get_episode(season, episode)
                except EpisodeNotFoundException:
                    continue
                else:
                    try:
                        episode_obj.load_from_series_provider(season, episode)
                        episode_obj.save()
                    except EpisodeDeletedException:
                        sickrage.app.log.info("The episode was deleted, skipping the rest of the load")
                        continue

                scanned_eps[season][episode] = True

        # Done updating save last update date
        self.last_update = datetime.datetime.now()

        self.save()

        return scanned_eps

    def get_episode(self, season=None, episode=None, absolute_number=None, location=None, no_create=False):
        try:
            if season is None and episode is None and absolute_number is not None:
                with sickrage.app.main_db.session() as session:
                    query = session.query(MainDB.TVEpisode).filter_by(series_id=self.series_id, series_provider_id=self.series_provider_id,
                                                                      absolute_number=absolute_number).one()
                    sickrage.app.log.debug("Found episode by absolute_number %s which is S%02dE%02d" % (absolute_number, query.season, query.episode))
                    season = query.season
                    episode = query.episode

            for tv_episode in self.episodes:
                if tv_episode.season == season and tv_episode.episode == episode:
                    return tv_episode
            else:
                if no_create:
                    return None

                tv_episode = TVEpisode(series_id=self.series_id,
                                       series_provider_id=self.series_provider_id,
                                       season=season,
                                       episode=episode,
                                       location=location or '')

                self._episodes[tv_episode.episode_id] = tv_episode
                return tv_episode
        except orm.exc.MultipleResultsFound:
            if absolute_number is not None:
                sickrage.app.log.debug("Multiple entries for absolute number: " + str(absolute_number) + " in show: " + self.name + " found ")
            raise MultipleEpisodesInDatabaseException
        except orm.exc.NoResultFound:
            if absolute_number is not None:
                sickrage.app.log.debug("No entries for absolute number: " + str(absolute_number) + " in show: " + self.name + " found.")
            raise EpisodeNotFoundException

    def delete_episode(self, season, episode, full=False):
        episode_object = self.get_episode(season, episode, no_create=True)
        if not episode_object:
            return

        data = sickrage.app.notification_providers['trakt'].trakt_episode_data_generate([(episode_object.season, episode_object.episode)])
        if sickrage.app.config.trakt.enable and sickrage.app.config.trakt.sync_watchlist and data:
            sickrage.app.log.debug("Deleting episode from Trakt")
            sickrage.app.notification_providers['trakt'].update_watchlist(self, data_episode=data, update="remove")

        if full and os.path.isfile(episode_object.location):
            sickrage.app.log.info('Attempt to delete episode file %s' % episode_object.location)

            try:
                os.remove(episode_object.location)
            except OSError as e:
                sickrage.app.log.warning('Unable to delete episode file %s: %s / %s' % (episode_object.location, repr(e), str(e)))

        # delete episode from show episode cache
        sickrage.app.log.debug("Deleting %s S%02dE%02d from the shows episode cache" % (self.name, episode_object.season or 0, episode_object.episode or 0))
        try:
            del self._episodes[episode_object.episode_id]
        except KeyError:
            pass

        # delete episode from database
        sickrage.app.log.debug("Deleting %s S%02dE%02d from the DB" % (self.name, episode_object.season or 0, episode_object.episode or 0))
        episode_object.delete()

        raise EpisodeDeletedException()

    def write_show_nfo(self, force=False):
        result = False

        if not os.path.isdir(self.location):
            sickrage.app.log.info(str(self.series_id) + ": Show dir doesn't exist, skipping NFO generation")
            return False

        sickrage.app.log.debug(str(self.series_id) + ": Writing NFOs for show")
        for cur_provider in sickrage.app.metadata_providers.values():
            result = cur_provider.create_show_metadata(self, force) or result

        return result

    def write_metadata(self, show_only=False, force=False):
        if not os.path.isdir(self.location):
            sickrage.app.log.info(str(self.series_id) + ": Show dir doesn't exist, skipping NFO generation")
            return

        self.get_images()

        self.write_show_nfo(force)

        if not show_only:
            self.write_episode_nfos(force)
            self.update_episode_video_metadata()

    def write_episode_nfos(self, force=False):
        if not os.path.isdir(self.location):
            sickrage.app.log.info(str(self.series_id) + ": Show dir doesn't exist, skipping NFO generation")
            return

        sickrage.app.log.debug(str(self.series_id) + ": Writing NFOs for all episodes")

        for episode_obj in self.episodes:
            if episode_obj.location == '':
                continue

            sickrage.app.log.debug(str(self.series_id) + ": Retrieving/creating episode S%02dE%02d" % (episode_obj.season or 0, episode_obj.episode or 0))

            episode_obj.create_meta_files(force)

    def update_episode_video_metadata(self):
        if not os.path.isdir(self.location):
            sickrage.app.log.info(str(self.series_id) + ": Show dir doesn't exist, skipping video metadata updating")
            return

        sickrage.app.log.debug(str(self.series_id) + ": Updating video metadata for all episodes")

        for episode_obj in self.episodes:
            if episode_obj.location == '':
                continue

            sickrage.app.log.debug(str(self.series_id) + ": Updating video metadata for episode S%02dE%02d" % (episode_obj.season, episode_obj.episode))

            episode_obj.update_video_metadata()

    # find all media files in the show folder and create episodes for as many as possible
    def load_episodes_from_dir(self):
        from sickrage.core.nameparser import NameParser, InvalidNameException, InvalidShowException

        if not os.path.isdir(self.location):
            sickrage.app.log.debug(str(self.series_id) + ": Show dir doesn't exist, not loading episodes from disk")
            return

        sickrage.app.log.debug(str(self.series_id) + ": Loading all episodes from the show directory " + self.location)

        # get file list
        media_files = list_media_files(self.location)

        # create TVEpisodes from each media file (if possible)
        for mediaFile in media_files:
            curEpisode = None

            sickrage.app.log.debug(str(self.series_id) + ": Creating episode from " + mediaFile)
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
                parse_result = NameParser(False, series_id=self.series_id, series_provider_id=self.series_provider_id).parse(ep_file_name)
            except (InvalidNameException, InvalidShowException):
                parse_result = None

            if ' ' not in ep_file_name and parse_result and parse_result.release_group:
                sickrage.app.log.debug("Name " + ep_file_name + " gave release group of " + parse_result.release_group + ", seems valid")
                curEpisode.release_name = ep_file_name
                self.save()

            # store the reference in the show
            if self.subtitles and sickrage.app.config.subtitles.enable:
                try:
                    curEpisode.refresh_subtitles()
                except Exception:
                    sickrage.app.log.error("%s: Could not refresh subtitles" % self.series_id)
                    sickrage.app.log.debug(traceback.format_exc())

    def load_imdb_info(self):
        imdb_info_mapper = {
            'imdbvotes': 'votes',
            'imdbrating': 'rating',
            'totalseasons': 'seasons',
            'imdbid': 'imdb_id'
        }

        if not re.search(r'^tt\d+$', self.imdb_id) and self.name:
            resp = sickrage.app.api.imdb.search_by_imdb_title(self.name)
            if not resp:
                resp = {}

            for x in resp.get('Search', []):
                try:
                    if int(x.get('Year'), 0) == self.startyear and x.get('Title') in self.name:
                        if re.search(r'^tt\d+$', x.get('imdbID', '')):
                            self.imdb_id = x.get('imdbID')
                            self.save()
                            break
                except Exception:
                    continue

        if re.search(r'^tt\d+$', self.imdb_id):
            sickrage.app.log.debug(str(self.series_id) + ": Obtaining IMDb info")

            imdb_info = sickrage.app.api.imdb.search_by_imdb_id(self.imdb_id)
            if not imdb_info:
                sickrage.app.log.debug(str(self.series_id) + ': Unable to obtain IMDb info')
                return

            imdb_info = dict((k.lower(), v) for k, v in imdb_info.items())
            for column in imdb_info.copy():
                if column in imdb_info_mapper:
                    imdb_info[imdb_info_mapper[column]] = imdb_info[column]

                if column not in MainDB.IMDbInfo.__table__.columns.keys():
                    del imdb_info[column]

            if not all([imdb_info.get('imdb_id'), imdb_info.get('votes'), imdb_info.get('rating'), imdb_info.get('genre')]):
                sickrage.app.log.debug(str(self.series_id) + ': IMDb info obtained does not meet our requirements')
                return

            sickrage.app.log.debug(str(self.series_id) + ": Obtained IMDb info ->" + str(imdb_info))

            # save imdb info to database
            imdb_info.update({
                'series_id': self.series_id,
                'last_update': datetime.datetime.now()
            })

            with sickrage.app.main_db.session() as session:
                try:
                    dbData = session.query(MainDB.IMDbInfo).filter_by(series_id=self.series_id).one()
                    dbData.update(**imdb_info)
                except orm.exc.NoResultFound:
                    session.add(MainDB.IMDbInfo(**imdb_info))
                finally:
                    self.save()

    def get_images(self, fanart=None, poster=None):
        fanart_result = poster_result = banner_result = False
        season_posters_result = season_banners_result = season_all_poster_result = season_all_banner_result = False

        for cur_provider in sickrage.app.metadata_providers.values():
            fanart_result = cur_provider.create_fanart(self) or fanart_result
            poster_result = cur_provider.create_poster(self) or poster_result
            banner_result = cur_provider.create_banner(self) or banner_result

            season_posters_result = cur_provider.create_season_posters(self) or season_posters_result
            season_banners_result = cur_provider.create_season_banners(self) or season_banners_result
            season_all_poster_result = cur_provider.create_season_all_poster(self) or season_all_poster_result
            season_all_banner_result = cur_provider.create_season_all_banner(self) or season_all_banner_result

        return fanart_result or poster_result or banner_result or season_posters_result or season_banners_result or season_all_poster_result or season_all_banner_result

    def make_ep_from_file(self, filename):
        from sickrage.core.nameparser import NameParser, InvalidNameException, InvalidShowException

        if not os.path.isfile(filename):
            sickrage.app.log.info(str(self.series_id) + ": That isn't even a real file dude... " + filename)
            return None

        sickrage.app.log.debug(str(self.series_id) + ": Creating episode object from " + filename)

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

            sickrage.app.log.debug("%s: %s parsed to %s S%02dE%02d" % (self.series_id, filename, self.name, int(season or 0), int(episode or 0)))

            check_quality_again = False

            try:
                episode_obj = self.get_episode(season, episode, location=filename)
            except EpisodeNotFoundException:
                sickrage.app.log.warning("{}: Unable to figure out what this file is, skipping {}".format(self.series_id, filename))
                continue

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

                episode_obj.status = Quality.composite_status(EpisodeStatus.DOWNLOADED, new_quality)

            # check for status/quality changes as long as it's a new file
            elif not same_file and is_media_file(
                    filename) and episode_obj.status not in flatten([EpisodeStatus.composites(EpisodeStatus.DOWNLOADED),
                                                                     EpisodeStatus.composites(EpisodeStatus.ARCHIVED), EpisodeStatus.IGNORED]):
                old_status, old_quality = Quality.split_composite_status(episode_obj.status)
                new_quality = Quality.name_quality(filename, self.is_anime)

                new_status = None

                # if it was snatched and now exists then set the status correctly
                if old_status == EpisodeStatus.SNATCHED and old_quality <= new_quality:
                    sickrage.app.log.debug(
                        "STATUS: this ep used to be snatched with quality " + old_quality.display_name +
                        " but a file exists with quality " + new_quality.display_name +
                        " so I'm setting the status to DOWNLOADED")
                    new_status = EpisodeStatus.DOWNLOADED

                # if it was snatched proper and we found a higher quality one then allow the status change
                elif old_status == EpisodeStatus.SNATCHED_PROPER and old_quality < new_quality:
                    sickrage.app.log.debug(
                        "STATUS: this ep used to be snatched proper with quality " + old_quality.display_name +
                        " but a file exists with quality " + new_quality.display_name +
                        " so I'm setting the status to DOWNLOADED")
                    new_status = EpisodeStatus.DOWNLOADED

                elif old_status not in (EpisodeStatus.SNATCHED, EpisodeStatus.SNATCHED_PROPER):
                    new_status = EpisodeStatus.DOWNLOADED

                if new_status is not None:
                    sickrage.app.log.debug(
                        "STATUS: we have an associated file, so setting the status from " + str(
                            episode_obj.status) + " to DOWNLOADED/" + str(Quality.status_from_name(filename, anime=self.is_anime)))
                    episode_obj.status = Quality.composite_status(new_status, new_quality)

            # save episode data to database
            episode_obj.save()

        # creating metafiles on the root should be good enough
        if root_ep:
            root_ep.create_meta_files()

        # save show data to database
        self.save()

        return root_ep

    def delete_show(self, full=False):
        # choose delete or trash action
        action = ('delete', 'trash')[sickrage.app.config.general.trash_remove_show]

        # remove from database
        with sickrage.app.main_db.session() as session:
            series = session.query(MainDB.TVShow).filter_by(series_id=self.series_id, series_provider_id=self.series_provider_id).one()
            session.delete(series)
            session.commit()

        # remove episodes from show episode cache
        self.flush_episodes()

        # remove from show cache if found
        try:
            del sickrage.app.shows[(self.series_id, self.series_provider_id)]
        except KeyError:
            pass

        # clear the cache
        image_cache_dir = os.path.join(sickrage.app.cache_dir, 'images')
        for cache_file in glob.glob(os.path.join(image_cache_dir, str(self.series_id) + '.*')):
            sickrage.app.log.info('Attempt to %s cache file %s' % (action, cache_file))
            try:
                if sickrage.app.config.general.trash_remove_show:
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

                    if sickrage.app.config.general.trash_remove_show:
                        send2trash.send2trash(self.location)
                    else:
                        shutil.rmtree(self.location)

                    sickrage.app.log.info('%s show folder %s' %
                                          (('Deleted', 'Trashed')[sickrage.app.config.general.trash_remove_show],
                                           self.location))
            except OSError as e:
                sickrage.app.log.warning('Unable to %s %s: %s / %s' % (action, self.location, repr(e), str(e)))

        if sickrage.app.config.trakt.enable and sickrage.app.config.trakt.sync_watchlist:
            sickrage.app.log.debug("Removing show: {}, {} from watchlist".format(self.series_id, self.name))
            sickrage.app.notification_providers['trakt'].update_watchlist(self, update="remove")

    def populate_cache(self, force=False):
        sickrage.app.log.debug("Checking & filling cache for show " + self.name)
        ImageCache().fill_cache(self, force)

    def refresh_dir(self):
        # make sure the show dir is where we think it is unless dirs are created on the fly
        if not os.path.isdir(self.location) and not sickrage.app.config.general.create_missing_show_dirs:
            return False

        # load from dir
        try:
            self.load_episodes_from_dir()
        except Exception as e:
            sickrage.app.log.debug("Error searching dir for episodes: {}".format(e))
            sickrage.app.log.debug(traceback.format_exc())

        # run through all locations from DB, check that they exist
        sickrage.app.log.debug(str(self.series_id) + ": Loading all episodes with a location from the database")

        for curEp in self.episodes:
            if curEp.location == '':
                continue

            curLoc = os.path.normpath(curEp.location)
            season = int(curEp.season)
            episode = int(curEp.episode)

            # if the path doesn't exist or if it's not in our show dir
            if not os.path.isfile(curLoc) or not os.path.normpath(curLoc).startswith(os.path.normpath(self.location)):
                # check if downloaded files still exist, update our data if this has changed
                if not sickrage.app.config.general.skip_removed_files:
                    # if it used to have a file associated with it and it doesn't anymore then set it to
                    # EP_DEFAULT_DELETED_STATUS
                    if curEp.location and curEp.status in EpisodeStatus.composites(EpisodeStatus.DOWNLOADED):
                        if sickrage.app.config.general.ep_default_deleted_status == EpisodeStatus.ARCHIVED:
                            __, oldQuality = Quality.split_composite_status(curEp.status)
                            new_status = Quality.composite_status(EpisodeStatus.ARCHIVED, oldQuality)
                        else:
                            new_status = sickrage.app.config.general.ep_default_deleted_status

                        sickrage.app.log.debug("%s: Location for S%02dE%02d doesn't exist, "
                                               "removing it and changing our status to %s" % (self.series_id,
                                                                                              season or 0, episode or 0,
                                                                                              new_status.display_name))

                        curEp.status = new_status
                        curEp.subtitles = ''
                        curEp.subtitles_searchcount = 0
                        curEp.subtitles_lastsearch = datetime.datetime.min

                    curEp.location = ''
                    curEp.hasnfo = False
                    curEp.hastbn = False
                    curEp.release_name = ''
            else:
                if curEp.status in EpisodeStatus.composites(EpisodeStatus.ARCHIVED):
                    __, oldQuality = Quality.split_composite_status(curEp.status)
                    curEp.status = Quality.composite_status(EpisodeStatus.DOWNLOADED, oldQuality)

                # the file exists, set its modify file stamp
                if sickrage.app.config.general.airdate_episodes:
                    curEp.airdate_modify_stamp()

            # save episode to database
            curEp.save()

    def download_subtitles(self):
        if not os.path.isdir(self.location):
            sickrage.app.log.debug(str(self.series_id) + ": Show dir doesn't exist, can't download subtitles")
            return

        sickrage.app.log.debug("%s: Downloading subtitles" % self.series_id)

        try:
            for episode in self.episodes:
                episode.download_subtitles()
        except Exception:
            sickrage.app.log.error("%s: Error occurred when downloading subtitles for %s" % (self.series_id, self.name))

    def qualitiesToString(self, qualities=None):
        if qualities is None:
            qualities = []

        result = ''
        for quality in qualities:
            if quality in Qualities:
                result += quality.display_name + ', '

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
            self.name, episode_object.season or 0, episode_object.episode or 0, quality.display_name))

        # if the quality isn't one we want under any circumstances then just say no
        any_qualities, best_qualities = Quality.split_quality(self.quality)
        sickrage.app.log.debug("Any, Best = [{}] [{}] Found = [{}]".format(
            self.qualitiesToString(any_qualities),
            self.qualitiesToString(best_qualities),
            self.qualitiesToString([quality]))
        )

        if quality not in any_qualities + best_qualities or quality is EpisodeStatus.UNKNOWN:
            sickrage.app.log.debug("Don't want this quality, ignoring found episode")
            return False

        ep_status, ep_quality = Quality.split_composite_status(episode_object.status)

        sickrage.app.log.debug(f"Existing episode status: {ep_status.display_name}")

        # if we know we don't want it then just say no
        if ep_status in flatten(
                [EpisodeStatus.composites(EpisodeStatus.ARCHIVED), EpisodeStatus.UNAIRED, EpisodeStatus.SKIPPED, EpisodeStatus.IGNORED]) and not manualSearch:
            sickrage.app.log.debug("Existing episode status is unaired/skipped/ignored/archived, ignoring found episode")
            return False

        # if it's one of these then we want it as long as it's in our allowed initial qualities
        if ep_status == EpisodeStatus.WANTED:
            sickrage.app.log.debug("Existing episode status is WANTED, getting found episode")
            return True
        elif manualSearch:
            if (downCurQuality and quality >= ep_quality) or (not downCurQuality and quality > ep_quality):
                sickrage.app.log.debug("Usually ignoring found episode, but forced search allows the quality, getting found episode")
                return True

        # if we are re-downloading then we only want it if it's in our bestQualities list and better than what we
        # have, or we only have one bestQuality and we do not have that quality yet
        if ep_status in flatten([EpisodeStatus.composites(EpisodeStatus.DOWNLOADED), EpisodeStatus.composites(EpisodeStatus.SNATCHED),
                                 EpisodeStatus.composites(EpisodeStatus.SNATCHED_PROPER)]) and quality in best_qualities and (
                quality > ep_quality or ep_quality not in best_qualities):
            sickrage.app.log.debug("Episode already exists but the found episode quality is wanted more, getting found episode")
            return True
        elif ep_quality == EpisodeStatus.UNKNOWN and manualSearch:
            sickrage.app.log.debug("Episode already exists but quality is Unknown, getting found episode")
            return True
        else:
            sickrage.app.log.debug("Episode already exists and the found episode has same/lower quality, ignoring found episode")

        sickrage.app.log.debug("None of the conditions were met, ignoring found episode")
        return False

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

    def retrieve_scene_exceptions(self, get_anidb=True, force=False):
        """
        Looks up the exceptions on SR API.
        """

        max_refresh_age_secs = 86400  # 1 day

        if not datetime.datetime.now() > (self.last_scene_exceptions_refresh + datetime.timedelta(seconds=max_refresh_age_secs)) and not force:
            return

        try:
            sickrage.app.log.debug("Retrieving scene exceptions from SiCKRAGE API for show: {}".format(self.name))

            scene_exceptions = sickrage.app.api.scene_exceptions.search_by_id(self.series_id)
            if not scene_exceptions or 'data' not in scene_exceptions:
                sickrage.app.log.debug("No scene exceptions found from SiCKRAGE API for show: {}".format(self.name))
            else:
                self.scene_exceptions = set(self.scene_exceptions + scene_exceptions['data']['exceptions'].split(','))

            if get_anidb and self.is_anime and self.series_provider_id == 1:
                try:
                    sickrage.app.log.info("Retrieving AniDB scene exceptions for show: {}".format(self.name))
                    anime = Anime(None, name=self.name, tvdbid=self.series_id, autoCorrectName=True)
                    if anime and anime.name != self.name:
                        anidb_scene_exceptions = ['{}|-1'.format(anime.name)]
                        self.scene_exceptions = set(self.scene_exceptions + anidb_scene_exceptions)
                except Exception:
                    pass

            self.last_scene_exceptions_refresh = datetime.datetime.now()
            self.save()
        except Exception as e:
            sickrage.app.log.debug("Check scene exceptions update failed from SiCKRAGE API for show: {}".format(self.name))

    def get_scene_exception_by_name(self, exception_name):
        for x in self.scene_exceptions:
            if exception_name in x:
                scene_name, scene_season = x.split('|')
                return scene_name, int(scene_season)

    def get_scene_exceptions_by_season(self, season=-1):
        scene_exceptions = []

        for scene_exception in self.scene_exceptions:
            try:
                scene_name, scene_season = scene_exception.split('|')
                if season == int(scene_season):
                    scene_exceptions.append(scene_name)
            except ValueError:
                pass

        return scene_exceptions

    def update_scene_exceptions(self, scene_exceptions, season=-1):
        self.scene_exceptions = set([x + '|{}'.format(season) for x in scene_exceptions])
        self.save()

    def __unicode__(self):
        to_return = ""
        to_return += "series_id: {}\n".format(self.series_id)
        to_return += "series_provider_id: {}\n".format(self.series_provider_id.display_name)
        to_return += "name: {}\n".format(self.name)
        to_return += "location: {}\n".format(self.location)
        if self.network:
            to_return += "network: {}\n".format(self.network)
        if self.airs:
            to_return += "airs: {}\n".format(self.airs)
        to_return += "status: {}\n".format(self.status)
        to_return += "startyear: {}\n".format(self.startyear)
        if self.genre:
            to_return += "genre: {}\n".format(self.genre)
        to_return += "overview: {}\n".format(self.overview)
        to_return += "classification: {}\n".format(self.classification)
        to_return += "runtime: {}\n".format(self.runtime)
        to_return += "quality: {}\n".format(self.quality)
        to_return += "search format: {}\n".format(self.search_format.display_name)
        to_return += "anime: {}\n".format(self.is_anime)
        return to_return

    def to_json(self, episodes=False, progress=False, details=False):
        with sickrage.app.main_db.session() as session:
            series = session.query(MainDB.TVShow).filter_by(series_id=self.series_id, series_provider_id=self.series_provider_id).one_or_none()
            json_data = TVShowSchema().dump(series)

            json_data['seriesSlug'] = self.slug

            json_data['isLoading'] = self.is_loading
            json_data['isRemoving'] = self.is_removing

            # images section
            json_data['images'] = {
                'poster': self.poster,
                'banner': self.banner
            }

            # qualities section
            json_data['qualities'] = {
                'allowedQualities': [x.name for x in self.allowed_qualities],
                'preferredQualities': [x.name for x in self.preferred_qualities]
            }

            # show queue status
            json_data['showQueueStatus'] = self.show_queue_status

            if details:
                # imdb info section
                imdb_info = session.query(MainDB.IMDbInfo).filter_by(series_id=self.series_id, imdb_id=self.imdb_id).one_or_none()
                json_data['imdbInfo'] = IMDbInfoSchema().dump(imdb_info)

                # anime section
                blacklist = session.query(MainDB.Blacklist).filter_by(series_id=self.series_id, series_provider_id=self.series_provider_id).one_or_none()
                whitelist = session.query(MainDB.Whitelist).filter_by(series_id=self.series_id, series_provider_id=self.series_provider_id).one_or_none()
                json_data['blacklist'] = BlacklistSchema().dump(blacklist)
                json_data['whitelist'] = WhitelistSchema().dump(whitelist)

            # progress section
            if progress:
                episodes_snatched = self.episodes_snatched
                episodes_downloaded = self.episodes_downloaded
                episodes_total = self.episodes_total
                progressbar_percent = int(episodes_downloaded * 100 / episodes_total if episodes_total > 0 else 1)

                progress_text = '?'
                progress_tip = _("no data")
                if episodes_total != 0:
                    progress_text = str(episodes_downloaded)
                    progress_tip = _("Downloaded: ") + str(episodes_downloaded)
                    if episodes_snatched > 0:
                        progress_text = progress_text + "+" + str(episodes_snatched)
                        progress_tip = progress_tip + "&#013;" + _("Snatched: ") + str(episodes_snatched)

                    progress_text = progress_text + " / " + str(episodes_total)
                    progress_tip = progress_tip + "&#013;" + _("Total: ") + str(episodes_total)

                json_data['progress'] = {
                    'text': progress_text,
                    'tip': progress_tip,
                    'percent': progressbar_percent
                }

            # episodes section
            if episodes:
                json_data['episodes'] = {ep.episode_id: ep.to_json() for ep in self.episodes}

            return json_data
