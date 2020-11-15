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
from abc import ABC

from tornado.escape import json_decode

import sickrage
from sickrage.core.common import Quality
from sickrage.core.databases.main import MainDB, IMDbInfoSchema, WhitelistSchema, BlacklistSchema
from sickrage.core.exceptions import CantUpdateShowException, NoNFOException, CantRefreshShowException
from sickrage.core.helpers import checkbox_to_value, sanitize_file_name, make_dir, chmod_as_parent
from sickrage.core.helpers.anidb import short_group_names
from sickrage.core.media.util import showImage
from sickrage.core.tv.show.helpers import get_show_list, find_show
from sickrage.core.webserver.handlers.api.v2 import APIv2BaseHandler
from sickrage.indexers import IndexerApi


class SeriesHandler(APIv2BaseHandler, ABC):
    def get(self, series_id=None, *args, **kwargs):
        if not series_id:
            all_series = {}

            for show in get_show_list():
                if sickrage.app.show_queue.is_being_removed(show.indexer_id):
                    continue

                all_series[show.indexer_id] = show.to_json(progress=True)

            return self.write_json(all_series)

        series = find_show(int(series_id))
        if not series:
            return self.send_error(404, reason="Unable to find the specified series: {}".format(series_id))

        return self.write_json(series.to_json(episodes=True, details=True))

    def post(self):
        data = json_decode(self.request.body)

        is_existing = data.get('isExisting', None)

        root_directory = data.get('rootDirectory', None)
        series_id = data.get('seriesId', None)
        series_name = data.get('seriesName', None)
        series_directory = data.get('seriesDirectory', None)
        first_aired = data.get('firstAired', None)
        indexer_slug = data.get('indexerSlug', None)
        indexer_language = data.get('indexerLanguage', None)
        default_status = data.get('defaultStatus', None)
        default_status_after = data.get('defaultStatusAfter', None)
        quality_preset = data.get('qualityPreset', None)
        any_qualities = data.get('anyQualities', [])
        best_qualities = data.get('bestQualities', [])
        subtitles = data.get('subtitles', None)
        sub_use_sr_metadata = data.get('subUseSrMetadata', None)
        flatten_folders = data.get('flattenFolders', None)
        is_anime = data.get('isAnime', None)
        is_scene = data.get('isScene', None)
        search_format = data.get('searchFormat', None)
        dvd_order = data.get('dvdOrder', None)
        skip_downloaded = data.get('skipDownloaded', None)
        add_show_year = data.get('addShowYear', None)

        series = find_show(int(series_id))
        if series:
            return self.send_error(400, reason="Already exists series: {}".format(series_id))

        if is_existing and not series_directory:
            return self.send_error(400, reason="Missing seriesDirectory parameter")

        if not is_existing:
            series_directory = os.path.join(root_directory, sanitize_file_name(series_name))

            series_year = re.search(r'\d{4}', first_aired)
            if add_show_year and not re.match(r'.*\(\d+\)$', series_directory) and series_year:
                series_directory = f"{series_directory} ({series_year.group()})"

            if os.path.isdir(series_directory):
                sickrage.app.alerts.error(_("Unable to add show"), _("Folder ") + series_directory + _(" exists already"))
                return self.send_error(400, reason=f"Show directory {series_directory} already exists!")

            if not make_dir(series_directory):
                sickrage.app.log.warning(f"Unable to create the folder {series_directory}, can't add the show")
                sickrage.app.alerts.error(_("Unable to add show"), _(f"Unable to create the folder {series_directory}, can't add the show"))
                return self.send_error(400, reason=f"Unable to create the show folder {series_directory}, can't add the show")

        chmod_as_parent(series_directory)

        new_quality = quality_preset
        if not new_quality:
            new_quality = Quality.combine_qualities(map(int, any_qualities), map(int, best_qualities))

        sickrage.app.show_queue.add_show(indexer=int(IndexerApi().indexers_by_slug[indexer_slug]['id']),
                                         indexer_id=int(series_id),
                                         showDir=series_directory,
                                         default_status=int(default_status),
                                         quality=int(new_quality),
                                         flatten_folders=checkbox_to_value(flatten_folders),
                                         lang=indexer_language,
                                         subtitles=checkbox_to_value(subtitles),
                                         sub_use_sr_metadata=checkbox_to_value(sub_use_sr_metadata),
                                         anime=checkbox_to_value(is_anime),
                                         dvdorder=checkbox_to_value(dvd_order),
                                         search_format=int(search_format),
                                         paused=False,
                                         # blacklist=blacklist,
                                         # whitelist=whitelist,
                                         default_status_after=int(default_status_after),
                                         scene=checkbox_to_value(is_scene),
                                         skip_downloaded=checkbox_to_value(skip_downloaded))

        sickrage.app.alerts.message(_('Adding Show'), _(f'Adding the specified show into {series_directory}'))

        return self.write_json({'message': 'successful'})

    def patch(self, series_id):
        warnings, errors = [], []

        do_update = False
        do_update_exceptions = False

        data = json_decode(self.request.body)

        series = find_show(int(series_id))
        if not series:
            return self.send_error(404, error="Unable to find the specified show: {}".format(series_id))

        # if we changed the language then kick off an update
        if data.get('lang') is not None and data['lang'] != series.lang:
            do_update = True

        if data.get('paused') is not None:
            series.paused = checkbox_to_value(data['paused'])

        if data.get('anime') is not None:
            series.anime = checkbox_to_value(data['anime'])

        if data.get('scene') is not None:
            series.scene = checkbox_to_value(data['scene'])

        if data.get('search_format') is not None:
            series.search_format = int(data['search_format'])

        if data.get('subtitles') is not None:
            series.subtitles = checkbox_to_value(data['subtitles'])

        if data.get('sub_use_sr_metadata') is not None:
            series.sub_use_sr_metadata = checkbox_to_value(data['sub_use_sr_metadata'])

        if data.get('default_ep_status') is not None:
            series.default_ep_status = int(data['default_ep_status'])

        if data.get('skip_downloaded') is not None:
            series.skip_downloaded = checkbox_to_value(data['skip_downloaded'])

        if data.get('scene_exceptions') is not None and set(data['scene_exceptions']) != set(series.scene_exceptions):
            do_update_exceptions = True

        if data.get('whitelist') is not None:
            shortwhitelist = short_group_names(data['whitelist'])
            series.release_groups.set_white_keywords(shortwhitelist)

        if data.get('blacklist') is not None:
            shortblacklist = short_group_names(data['blacklist'])
            series.release_groups.set_black_keywords(shortblacklist)

        if data.get('quality_preset') is not None:
            new_quality = int(data['quality_preset'])
            if new_quality == 0 and data.get('allowed_qualities') is not None and data.get('preferred_qualities') is not None:
                new_quality = Quality.combine_qualities(list(map(int, data['allowed_qualities'])), list(map(int, data['preferred_qualities'])))
            series.quality = new_quality

        if data.get('flatten_folders') is not None and bool(series.flatten_folders) != bool(data['flatten_folders']):
            series.flatten_folders = data['flatten_folders']
            try:
                sickrage.app.show_queue.refresh_show(series.indexer_id, True)
            except CantRefreshShowException as e:
                errors.append(_("Unable to refresh this show: {}").format(e))

        if data.get('language') is not None:
            series.lang = data['language']

        if data.get('dvdorder') is not None:
            series.dvdorder = checkbox_to_value(data['dvdorder'])

        if data.get('rls_ignore_words') is not None:
            series.rls_ignore_words = data['rls_ignore_words']

        if data.get('rls_require_words') is not None:
            series.rls_require_words = data['rls_require_words']

        # series.search_delay = int(data['search_delay'])

        # if we change location clear the db of episodes, change it, write to db, and rescan
        if data.get('location') is not None and os.path.normpath(series.location) != os.path.normpath(data['location']):
            sickrage.app.log.debug(os.path.normpath(series.location) + " != " + os.path.normpath(data['location']))
            if not os.path.isdir(data['location']) and not sickrage.app.config.create_missing_show_dirs:
                warnings.append("New location {} does not exist".format(data['location']))

            # don't bother if we're going to update anyway
            elif not do_update:
                # change it
                try:
                    series.location = data['location']
                    try:
                        sickrage.app.show_queue.refresh_show(series.indexer_id, True)
                    except CantRefreshShowException as e:
                        errors.append(_("Unable to refresh this show:{}").format(e))
                        # grab updated info from TVDB
                        # showObj.loadEpisodesFromIndexer()
                        # rescan the episodes in the new folder
                except NoNFOException:
                    warnings.append(_("The folder at {} doesn't contain a tvshow.nfo - copy your files to that folder before you change the directory in "
                                      "SiCKRAGE.").format(data['location']))

        # force the update
        if do_update:
            try:
                sickrage.app.show_queue.update_show(series.indexer_id, force=True)
            except CantUpdateShowException as e:
                errors.append(_("Unable to update show: {}").format(e))

        if do_update_exceptions:
            try:
                series.scene_exceptions = set(data['scene_exceptions'].split(','))
            except CantUpdateShowException:
                warnings.append(_("Unable to force an update on scene exceptions of the show."))

        # if do_update_scene_numbering:
        #     try:
        #         xem_refresh(series.indexer_id, series.indexer, True)
        #     except CantUpdateShowException:
        #         warnings.append(_("Unable to force an update on scene numbering of the show."))

        # commit changes to database
        series.save()

        return self.write_json(series.to_json(episodes=True, details=True))

    def delete(self, series_id):
        data = json_decode(self.request.body)

        series = find_show(int(series_id))
        if not series:
            return self.send_error(404, error="Unable to find the specified show: {}".format(series_id))

        sickrage.app.show_queue.remove_show(series.indexer_id, checkbox_to_value(data.get('delete')))

        return self.write_json({'message': 'successful'})


class SeriesEpisodesHandler(APIv2BaseHandler, ABC):
    def get(self, series_id, *args, **kwargs):
        series = find_show(int(series_id))
        if not series:
            return self.send_error(404, error="Unable to find the specified series: {}".format(series_id))

        episodes = []
        for episode in series.episodes:
            episodes.append(episode.to_json())

        return self.write_json(episodes)


class SeriesImagesHandler(APIv2BaseHandler, ABC):
    def get(self, series_id, *args, **kwargs):
        image = showImage(int(series_id), 'poster_thumb')
        return self.write_json({'poster': image.url})


class SeriesImdbInfoHandler(APIv2BaseHandler, ABC):
    def get(self, series_id, *args, **kwargs):
        with sickrage.app.main_db.session() as session:
            imdb_info = session.query(MainDB.IMDbInfo).filter_by(indexer_id=int(series_id)).one_or_none()
            json_data = IMDbInfoSchema().dump(imdb_info)

        return self.write_json(json_data)


class SeriesBlacklistHandler(APIv2BaseHandler, ABC):
    def get(self, series_id, *args, **kwargs):
        with sickrage.app.main_db.session() as session:
            blacklist = session.query(MainDB.Blacklist).filter_by(show_id=int(series_id)).one_or_none()
            json_data = BlacklistSchema().dump(blacklist)

        return self.write_json(json_data)


class SeriesWhitelistHandler(APIv2BaseHandler, ABC):
    def get(self, series_id, *args, **kwargs):
        with sickrage.app.main_db.session() as session:
            whitelist = session.query(MainDB.Whitelist).filter_by(show_id=int(series_id)).one_or_none()
            json_data = WhitelistSchema().dump(whitelist)

        return self.write_json(json_data)


class SeriesRefreshHandler(APIv2BaseHandler, ABC):
    def get(self, series_id):
        force = self.get_argument('force', None)

        series = find_show(int(series_id))
        if series is None:
            return self.send_error(404, reason="Unable to find the specified series: {}".format(series_id))

        try:
            sickrage.app.show_queue.refresh_show(series.indexer_id, force=bool(force))
        except CantUpdateShowException as e:
            return self.send_error(400, reason=_("Unable to refresh this show, error: {}".format(e)))


class SeriesUpdateHandler(APIv2BaseHandler, ABC):
    def get(self, series_id):
        force = self.get_argument('force', None)

        series = find_show(int(series_id))
        if series is None:
            return self.send_error(404, reason="Unable to find the specified series: {}".format(series_id))

        try:
            sickrage.app.show_queue.update_show(series.indexer_id, force=bool(force))
        except CantUpdateShowException as e:
            return self.send_error(400, reason=_("Unable to update this show, error: {}".format(e)))


