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
import os
import re

from tornado.escape import json_decode

import sickrage
from sickrage.core.common import Quality, Qualities, EpisodeStatus
from sickrage.core.databases.main import MainDB
from sickrage.core.databases.main.schemas import IMDbInfoSchema, BlacklistSchema, WhitelistSchema
from sickrage.core.enums import SearchFormat, SeriesProviderID
from sickrage.core.exceptions import CantUpdateShowException, NoNFOException, CantRefreshShowException
from sickrage.core.helpers import checkbox_to_value, sanitize_file_name, make_dir, chmod_as_parent
from sickrage.core.helpers.anidb import short_group_names
from sickrage.core.media.util import series_image, SeriesImageType
from sickrage.core.queues.search import ManualSearchTask
from sickrage.core.tv.episode.helpers import find_episode
from sickrage.core.tv.show.helpers import get_show_list, find_show, find_show_by_slug
from sickrage.core.webserver.handlers.api.v2 import ApiV2BaseHandler
from sickrage.core.websocket import WebSocketMessage
from .schemas import *


class ApiV2SeriesHandler(ApiV2BaseHandler):
    def get(self, series_slug=None):
        """Get list of series or specific series information"
        ---
        tags: [Series]
        summary: Manually search for episodes on search providers
        description: Manually search for episodes on search providers
        parameters:
        - in: path
          schema:
            SeriesSlugPath
        responses:
          200:
            description: Success payload
            content:
              application/json:
                schema:
                  SeriesSuccessSchema
          400:
            description: Bad request; Check `errors` for any validation errors
            content:
              application/json:
                schema:
                  BadRequestSchema
          401:
            description: Returned if your JWT token is missing or expired
            content:
              application/json:
                schema:
                  NotAuthorizedSchema
          404:
            description: Returned if the given series slug does not exist or no series results.
            content:
              application/json:
                schema:
                  NotFoundSchema
        """

        if not series_slug:
            all_series = []

            for show in get_show_list():
                if sickrage.app.show_queue.is_being_removed(show.series_id):
                    continue

                all_series.append(show.to_json(progress=True))

            return self.json_response(all_series)

        series = find_show_by_slug(series_slug)
        if series is None:
            return self._not_found(error=f"Unable to find the specified series using slug: {series_slug}")

        return self.json_response(series.to_json(episodes=True, details=True))

    def post(self):
        data = json_decode(self.request.body)

        is_existing = data.get('isExisting', 'false')

        root_directory = data.get('rootDirectory', None)
        series_id = data.get('seriesId', None)
        series_name = data.get('seriesName', None)
        series_directory = data.get('seriesDirectory', None)
        first_aired = data.get('firstAired', None)
        series_provider_slug = data.get('seriesProviderSlug', None)
        series_provider_language = data.get('seriesProviderLanguage', None)
        default_status = data.get('defaultStatus', None)
        default_status_after = data.get('defaultStatusAfter', None)
        quality_preset = data.get('qualityPreset', None)
        allowed_qualities = data.get('allowedQualities', [])
        preferred_qualities = data.get('preferredQualities', [])
        subtitles = self._parse_boolean(data.get('subtitles', sickrage.app.config.subtitles.default))
        sub_use_sr_metadata = self._parse_boolean(data.get('subUseSrMetadata', 'false'))
        flatten_folders = self._parse_boolean(data.get('flattenFolders', sickrage.app.config.general.flatten_folders_default))
        is_anime = self._parse_boolean(data.get('isAnime', sickrage.app.config.general.anime_default))
        is_scene = self._parse_boolean(data.get('isScene', sickrage.app.config.general.scene_default))
        search_format = data.get('searchFormat', sickrage.app.config.general.search_format_default.name)
        dvd_order = self._parse_boolean(data.get('dvdOrder', 'false'))
        skip_downloaded = self._parse_boolean(data.get('skipDownloaded', sickrage.app.config.general.skip_downloaded_default))
        add_show_year = self._parse_boolean(data.get('addShowYear', 'false'))

        if not series_id:
            return self._bad_request(error=f"Missing seriesId parameter: {series_id}")

        series_provider_id = SeriesProviderID.by_slug(series_provider_slug)
        if not series_provider_id:
            return self._not_found(error="Unable to identify a series provider using provided slug")

        series = find_show(int(series_id), series_provider_id)
        if series:
            return self._bad_request(error=f"Already exists series: {series_id}")

        if is_existing and not series_directory:
            return self._bad_request(error="Missing seriesDirectory parameter")

        if not is_existing:
            series_directory = os.path.join(root_directory, sanitize_file_name(series_name))

            if first_aired:
                series_year = re.search(r'\d{4}', first_aired)
                if add_show_year and not re.match(r'.*\(\d+\)$', series_directory) and series_year:
                    series_directory = f"{series_directory} ({series_year.group()})"

            if os.path.isdir(series_directory):
                sickrage.app.alerts.error(_("Unable to add show"), _("Folder ") + series_directory + _(" exists already"))
                return self._bad_request(error=f"Show directory {series_directory} already exists!")

            if not make_dir(series_directory):
                sickrage.app.log.warning(f"Unable to create the folder {series_directory}, can't add the show")
                sickrage.app.alerts.error(_("Unable to add show"), _(f"Unable to create the folder {series_directory}, can't add the show"))
                return self._bad_request(error=f"Unable to create the show folder {series_directory}, can't add the show")

        chmod_as_parent(series_directory)

        try:
            new_quality = Qualities[quality_preset.upper()]
        except (AttributeError, KeyError):
            new_quality = Quality.combine_qualities([Qualities[x.upper()] for x in allowed_qualities], [Qualities[x.upper()] for x in preferred_qualities])

        sickrage.app.show_queue.add_show(series_provider_id=series_provider_id,
                                         series_id=int(series_id),
                                         showDir=series_directory,
                                         default_status=EpisodeStatus[default_status.upper()],
                                         default_status_after=EpisodeStatus[default_status_after.upper()],
                                         quality=new_quality,
                                         flatten_folders=flatten_folders,
                                         lang=series_provider_language,
                                         subtitles=subtitles,
                                         sub_use_sr_metadata=sub_use_sr_metadata,
                                         anime=is_anime,
                                         dvd_order=dvd_order,
                                         search_format=SearchFormat[search_format.upper()],
                                         paused=False,
                                         # blacklist=blacklist,
                                         # whitelist=whitelist,
                                         scene=is_scene,
                                         skip_downloaded=skip_downloaded)

        sickrage.app.alerts.message(_('Adding Show'), _(f'Adding the specified show into {series_directory}'))

        return self.json_response({'message': True})

    def patch(self, series_slug):
        warnings, errors = [], []

        do_update = False
        do_update_exceptions = False

        data = json_decode(self.request.body)

        series = find_show_by_slug(series_slug)
        if series is None:
            return self._bad_request(error=f"Unable to find the specified series using slug: {series_slug}")

        # if we changed the language then kick off an update
        if data.get('lang') is not None and data['lang'] != series.lang:
            do_update = True

        if data.get('paused') is not None:
            series.paused = checkbox_to_value(data['paused'])

        if data.get('anime') is not None:
            series.anime = checkbox_to_value(data['anime'])

        if data.get('scene') is not None:
            series.scene = checkbox_to_value(data['scene'])

        if data.get('searchFormat') is not None:
            series.search_format = SearchFormat[data['searchFormat']]

        if data.get('subtitles') is not None:
            series.subtitles = checkbox_to_value(data['subtitles'])

        if data.get('subUseSrMetadata') is not None:
            series.sub_use_sr_metadata = checkbox_to_value(data['subUseSrMetadata'])

        if data.get('defaultEpStatus') is not None:
            series.default_ep_status = int(data['defaultEpStatus'])

        if data.get('skipDownloaded') is not None:
            series.skip_downloaded = checkbox_to_value(data['skipDownloaded'])

        if data.get('sceneExceptions') is not None and set(data['sceneExceptions']) != set(series.scene_exceptions):
            do_update_exceptions = True

        if data.get('whitelist') is not None:
            shortwhitelist = short_group_names(data['whitelist'])
            series.release_groups.set_white_keywords(shortwhitelist)

        if data.get('blacklist') is not None:
            shortblacklist = short_group_names(data['blacklist'])
            series.release_groups.set_black_keywords(shortblacklist)

        if data.get('qualityPreset') is not None:
            try:
                new_quality = Qualities[data['qualityPreset']]
            except KeyError:
                new_quality = Quality.combine_qualities([Qualities[x] for x in data['allowedQualities']], [Qualities[x] for x in data['preferredQualities']])

            series.quality = new_quality

        if data.get('flattenFolders') is not None and bool(series.flatten_folders) != bool(data['flattenFolders']):
            series.flatten_folders = data['flattenFolders']
            try:
                sickrage.app.show_queue.refresh_show(series.series_id, series.series_provider_id, True)
            except CantRefreshShowException as e:
                errors.append(_(f"Unable to refresh this show: {e}"))

        if data.get('language') is not None:
            series.lang = data['language']

        if data.get('dvdOrder') is not None:
            series.dvd_order = checkbox_to_value(data['dvdOrder'])

        if data.get('rlsIgnoreWords') is not None:
            series.rls_ignore_words = data['rlsIgnoreWords']

        if data.get('rlsRequireWords') is not None:
            series.rls_require_words = data['rlsRequireWords']

        # series.search_delay = int(data['search_delay'])

        # if we change location clear the db of episodes, change it, write to db, and rescan
        if data.get('location') is not None and os.path.normpath(series.location) != os.path.normpath(data['location']):
            sickrage.app.log.debug(os.path.normpath(series.location) + " != " + os.path.normpath(data['location']))
            if not os.path.isdir(data['location']) and not sickrage.app.config.general.create_missing_show_dirs:
                warnings.append(f"New location {data['location']} does not exist")

            # don't bother if we're going to update anyway
            elif not do_update:
                # change it
                try:
                    series.location = data['location']
                    try:
                        sickrage.app.show_queue.refresh_show(series.series_id, series.series_provider_id, True)
                    except CantRefreshShowException as e:
                        errors.append(_(f"Unable to refresh this show: {e}"))
                        # grab updated info from TVDB
                        # showObj.loadEpisodesFromSeriesProvider()
                        # rescan the episodes in the new folder
                except NoNFOException:
                    warnings.append(_(
                        f"The folder at {data['location']} doesn't contain a tvshow.nfo - copy your files to that folder before you change the directory in SiCKRAGE."))

        # force the update
        if do_update:
            try:
                sickrage.app.show_queue.update_show(series.series_id, series.series_provider_id, force=True)
            except CantUpdateShowException as e:
                errors.append(_(f"Unable to update show: {e}"))

        if do_update_exceptions:
            try:
                series.scene_exceptions = set(data['sceneExceptions'].split(','))
            except CantUpdateShowException:
                warnings.append(_("Unable to force an update on scene exceptions of the show."))

        # if do_update_scene_numbering:
        #     try:
        #         xem_refresh(series.series_id, series.series_provider_id, True)
        #     except CantUpdateShowException:
        #         warnings.append(_("Unable to force an update on scene numbering of the show."))

        # commit changes to database
        series.save()

        return self.json_response(series.to_json(episodes=True, details=True))

    def delete(self, series_slug):
        data = json_decode(self.request.body)

        series = find_show_by_slug(series_slug)
        if series is None:
            return self._not_found(error=f"Unable to find the specified series using slug: {series_slug}")

        sickrage.app.show_queue.remove_show(series.series_id, series.series_provider_id, checkbox_to_value(data.get('delete')))

        return self.json_response({'message': True})


class ApiV2SeriesEpisodesHandler(ApiV2BaseHandler):
    def get(self, series_slug, *args, **kwargs):
        series = find_show_by_slug(series_slug)
        if series is None:
            return self._not_found(error=f"Unable to find the specified series using slug: {series_slug}")

        episodes = []
        for episode in series.episodes:
            episodes.append(episode.to_json())

        return self.json_response(episodes)


class ApiV2SeriesImagesHandler(ApiV2BaseHandler):
    def get(self, series_slug, *args, **kwargs):
        series = find_show_by_slug(series_slug)
        if series is None:
            return self._not_found(error=f"Unable to find the specified series using slug: {series_slug}")

        image = series_image(series.series_id, series.series_provider_id, SeriesImageType.POSTER_THUMB)
        return self.json_response({'poster': image.url})


class ApiV2SeriesImdbInfoHandler(ApiV2BaseHandler):
    def get(self, series_slug, *args, **kwargs):
        series = find_show_by_slug(series_slug)
        if series is None:
            return self._not_found(error=f"Unable to find the specified series using slug: {series_slug}")

        with sickrage.app.main_db.session() as session:
            imdb_info = session.query(MainDB.IMDbInfo).filter_by(imdb_id=series.imdb_id).one_or_none()
            json_data = IMDbInfoSchema().dump(imdb_info)

        return self.json_response(json_data)


class ApiV2SeriesBlacklistHandler(ApiV2BaseHandler):
    def get(self, series_slug, *args, **kwargs):
        series = find_show_by_slug(series_slug)
        if series is None:
            return self._not_found(error=f"Unable to find the specified series using slug: {series_slug}")

        with sickrage.app.main_db.session() as session:
            blacklist = session.query(MainDB.Blacklist).filter_by(series_id=series.series_id, series_provider_id=series.series_provider_id).one_or_none()
            json_data = BlacklistSchema().dump(blacklist)

        return self.json_response(json_data)


class ApiV2SeriesWhitelistHandler(ApiV2BaseHandler):
    def get(self, series_slug, *args, **kwargs):
        series = find_show_by_slug(series_slug)
        if series is None:
            return self._not_found(error=f"Unable to find the specified series using slug: {series_slug}")

        with sickrage.app.main_db.session() as session:
            whitelist = session.query(MainDB.Whitelist).filter_by(series_id=series.series_id, series_provider_id=series.series_provider_id).one_or_none()
            json_data = WhitelistSchema().dump(whitelist)

        return self.json_response(json_data)


class ApiV2SeriesRefreshHandler(ApiV2BaseHandler):
    def get(self, series_slug):
        force = self.get_argument('force', None)

        series = find_show_by_slug(series_slug)
        if series is None:
            return self._not_found(error=f"Unable to find the specified series using slug: {series_slug}")

        try:
            sickrage.app.show_queue.refresh_show(series.series_id, series.series_provider_id, force=bool(force))
        except CantUpdateShowException as e:
            return self._bad_request(error=_(f"Unable to refresh this show, error: {e}"))


class ApiV2SeriesUpdateHandler(ApiV2BaseHandler):
    def get(self, series_slug):
        force = self.get_argument('force', None)

        series = find_show_by_slug(series_slug)
        if series is None:
            return self._not_found(error=f"Unable to find the specified series using slug: {series_slug}")

        try:
            sickrage.app.show_queue.update_show(series.series_id, series.series_provider_id, force=bool(force))
        except CantUpdateShowException as e:
            return self._bad_request(error=_(f"Unable to update this show, error: {e}"))


class ApiV2SeriesEpisodesRenameHandler(ApiV2BaseHandler):
    def get(self, series_slug):
        """Get list of episodes to rename"
        ---
        tags: [Series]
        summary: Get list of episodes to rename
        description: Get list of episodes to rename
        parameters:
        - in: path
          schema:
            SeriesSlugPath
        responses:
          200:
            description: Success payload
            content:
              application/json:
                schema:
                  SeriesEpisodesRenameSuccessSchema
          400:
            description: Bad request; Check `errors` for any validation errors
            content:
              application/json:
                schema:
                  BadRequestSchema
          401:
            description: Returned if your JWT token is missing or expired
            content:
              application/json:
                schema:
                  NotAuthorizedSchema
        """
        if not series_slug:
            return self._bad_request(error="Missing series slug")

        rename_data = []

        series = find_show_by_slug(series_slug)
        if series is None:
            return self._not_found(error=f"Unable to find the specified series using slug: {series_slug}")

        if not os.path.isdir(series.location):
            return self._bad_request(error="Can't rename episodes when the show location does not exist")

        for episode in series.episodes:
            if not episode.location:
                continue

            current_location = episode.location[len(episode.show.location) + 1:]
            new_location = "{}.{}".format(episode.proper_path(), current_location.split('.')[-1])

            if current_location != new_location:
                rename_data.append({
                    'episodeId': episode.episode_id,
                    'season': episode.season,
                    'episode': episode.episode,
                    'currentLocation': current_location,
                    'newLocation': new_location,
                })

        return self.json_response(rename_data)

    def post(self, series_slug):
        """Rename list of episodes"
        ---
        tags: [Series]
        summary: Rename list of episodes
        description: Rename list of episodes
        parameters:
        - in: path
          schema:
            SeriesSlugPath
        responses:
          200:
            description: Success payload
            content:
              application/json:
                schema:
                  EpisodesRenameSuccessSchema
          400:
            description: Bad request; Check `errors` for any validation errors
            content:
              application/json:
                schema:
                  BadRequestSchema
          401:
            description: Returned if your JWT token is missing or expired
            content:
              application/json:
                schema:
                  NotAuthorizedSchema
        """
        data = json_decode(self.request.body)

        renamed_episodes = []

        series = find_show_by_slug(series_slug)
        if series is None:
            return self._not_found(error=f"Unable to find the specified series using slug: {series_slug}")

        if not os.path.isdir(series.location):
            return self._bad_request(error="Can't rename episodes when the show location does not exist")

        for episode_id in data.get('episodeIdList', []):
            episode = find_episode(episode_id, series.series_provider_id)
            if episode:
                episode.rename()
                renamed_episodes.append(episode.episode_id)

        if len(renamed_episodes) > 0:
            WebSocketMessage('SHOW_RENAMED', {'seriesSlug': series.slug}).push()

        return self.json_response(renamed_episodes)


class ApiV2SeriesEpisodesManualSearchHandler(ApiV2BaseHandler):
    def get(self, series_slug, episode_slug):
        """Episode Manual Search"
        ---
        tags: [Series]
        summary: Manually search for episode on search providers
        description: Manually search for episode on search providers
        parameters:
        - in: path
          schema:
            SeriesSlugPath
        - in: path
          schema:
            EpisodeSlugPath
        responses:
          200:
            description: Success payload
            content:
              application/json:
                schema:
                  EpisodesManualSearchSuccessSchema
          400:
            description: Bad request; Check `errors` for any validation errors
            content:
              application/json:
                schema:
                  BadRequestSchema
          401:
            description: Returned if your JWT token is missing or expired
            content:
              application/json:
                schema:
                  NotAuthorizedSchema
          404:
            description: Returned if the given episode slug does not exist or the search returns no results.
            content:
              application/json:
                schema:
                  NotFoundSchema
        """
        use_existing_quality = self.get_argument('useExistingQuality', None) or False

        # validation_errors = self._validate_schema(SeriesEpisodesManualSearchPath, self.request.path)
        # if validation_errors:
        #     return self._bad_request(error=validation_errors)
        #
        # validation_errors = self._validate_schema(SeriesEpisodesManualSearchSchema, self.request.arguments)
        # if validation_errors:
        #     return self._bad_request(error=validation_errors)
        #

        series = find_show_by_slug(series_slug)
        if series is None:
            return self._not_found(error=f"Unable to find the specified series using slug: {series_slug}")

        match = re.match(r'^s(?P<season>\d+)e(?P<episode>\d+)$', episode_slug)
        season_num = match.group('season')
        episode_num = match.group('episode')

        episode = series.get_episode(int(season_num), int(episode_num), no_create=True)
        if episode is None:
            return self._bad_request(error=f"Unable to find the specified episode using slug: {episode_slug}")

        # make a queue item for it and put it on the queue
        ep_queue_item = ManualSearchTask(int(episode.show.series_id),
                                         episode.show.series_provider_id,
                                         int(episode.season),
                                         int(episode.episode),
                                         bool(use_existing_quality))

        sickrage.app.search_queue.put(ep_queue_item)
        if not all([ep_queue_item.started, ep_queue_item.success]):
            return self.json_response({'success': True})

        return self._not_found(error=_(f"Unable to find season {season_num} episode {episode_num} for show {series.name} on search providers"))
