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
from abc import ABC
from urllib.parse import urlencode

from tornado.escape import json_encode, json_decode
from tornado.httputil import url_concat
from tornado.web import authenticated

import sickrage
from sickrage.core.common import SNATCHED, Quality, Overview
from sickrage.core.databases.main import MainDB
from sickrage.core.exceptions import CantUpdateShowException, CantRefreshShowException
from sickrage.core.helpers import try_int
from sickrage.core.helpers.tornado_http import TornadoHTTP
from sickrage.core.tv.episode import TVEpisode
from sickrage.core.tv.show.helpers import find_show, get_show_list
from sickrage.core.webserver.handlers.base import BaseHandler
from sickrage.subtitles import Subtitles


class ManageHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        return self.redirect('/manage/massUpdate')


class ShowEpisodeStatusesHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        indexer_id = self.get_argument('indexer_id')
        which_status = self.get_argument('whichStatus')

        status_list = [int(which_status)]
        if status_list[0] == SNATCHED:
            status_list = Quality.SNATCHED + Quality.SNATCHED_PROPER

        result = {}
        for dbData in self.db_session.query(TVEpisode).filter_by(showid=int(indexer_id)).filter(TVEpisode.season != 0, TVEpisode.status.in_(status_list)):
            cur_season = int(dbData.season)
            cur_episode = int(dbData.episode)

            if cur_season not in result:
                result[cur_season] = {}

            result[cur_season][cur_episode] = dbData.name

        return self.write(json_encode(result))


class EpisodeStatusesHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        which_status = self.get_argument('whichStatus', None)

        ep_counts = {}
        show_names = {}
        sorted_show_ids = []
        status_list = []

        if which_status:
            status_list = [int(which_status)]
            if int(which_status) == SNATCHED:
                status_list = Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST

        # if we have no status then this is as far as we need to go
        if len(status_list):
            for show in sorted(get_show_list(session=self.db_session), key=lambda d: d.name):
                for episode in show.episodes:
                    if episode.season != 0 and episode.status in status_list:
                        if show.indexer_id not in ep_counts:
                            ep_counts[show.indexer_id] = 1
                        else:
                            ep_counts[show.indexer_id] += 1

                        show_names[show.indexer_id] = show.name
                        if show.indexer_id not in sorted_show_ids:
                            sorted_show_ids.append(show.indexer_id)

        return self.render(
            "/manage/episode_statuses.mako",
            title="Episode Overview",
            header="Episode Overview",
            topmenu='manage',
            whichStatus=which_status,
            show_names=show_names,
            ep_counts=ep_counts,
            sorted_show_ids=sorted_show_ids,
            controller='manage',
            action='episode_statuses'
        )


class ChangeEpisodeStatusesHandler(BaseHandler, ABC):
    @authenticated
    async def post(self, *args, **kwargs):
        old_status = self.get_argument('oldStatus')
        new_status = self.get_argument('newStatus')

        status_list = [int(old_status)]
        if status_list[0] == SNATCHED:
            status_list = Quality.SNATCHED + Quality.SNATCHED_PROPER

        # make a list of all shows and their associated args
        to_change = {}
        for x in self.get_arguments('toChange'):
            indexer_id, what = x.split('-')

            if indexer_id not in to_change:
                to_change[indexer_id] = []

            to_change[indexer_id].append(what)

        for cur_indexer_id in to_change:
            # get a list of all the eps we want to change if they just said "all"
            if 'all' in to_change[cur_indexer_id]:
                all_eps = ['{}x{}'.format(x.season, x.episode) for x in
                           self.db_session.query(TVEpisode).filter_by(showid=int(cur_indexer_id)).filter(TVEpisode.status.in_(status_list),
                                                                                                         TVEpisode.season != 0)]
                to_change[cur_indexer_id] = all_eps

            await TornadoHTTP().get(
                url_concat(
                    self.get_url("/home/setStatus"),
                    dict(show=cur_indexer_id, eps='|'.join(to_change[cur_indexer_id]), status=new_status, direct=True)
                )
            )

        return self.redirect('/manage/episodeStatuses/')


class ShowSubtitleMissedHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        indexer_id = self.get_argument('indexer_id')
        which_subs = self.get_argument('whichSubs')

        result = {}
        for dbData in self.db_session.query(TVEpisode).filter_by(showid=int(indexer_id)).filter(TVEpisode.status.endswith(4),
                                                                                                TVEpisode.season != 0):
            if which_subs == 'all':
                if not frozenset(Subtitles().wanted_languages()).difference(dbData.subtitles.split(',')):
                    continue
            elif which_subs in dbData.subtitles:
                continue

            cur_season = dbData.season
            cur_episode = dbData.episode

            if cur_season not in result:
                result[cur_season] = {}

            if cur_episode not in result[cur_season]:
                result[cur_season][cur_episode] = {}

            result[cur_season][cur_episode]["name"] = dbData.name

            result[cur_season][cur_episode]["subtitles"] = dbData.subtitles

        return self.write(json_encode(result))


class SubtitleMissedHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        which_subs = self.get_argument('whichSubs', None)

        ep_counts = {}
        show_names = {}
        sorted_show_ids = []
        status_results = []

        if which_subs:
            for s in get_show_list(session=self.db_session):
                if not s.subtitles == 1:
                    continue

                for e in s.episodes:
                    if e.season != 0 and (str(e.status).endswith('4') or str(e.status).endswith('6')):
                        status_results += [{
                            'show_name': s.name,
                            'indexer_id': s.indexer_id,
                            'subtitles': e.subtitles
                        }]

            for cur_status_result in sorted(status_results, key=lambda k: k['show_name']):
                if which_subs == 'all':
                    if not frozenset(Subtitles().wanted_languages()).difference(
                            cur_status_result["subtitles"].split(',')):
                        continue
                elif which_subs in cur_status_result["subtitles"]:
                    continue

                cur_indexer_id = int(cur_status_result["indexer_id"])
                if cur_indexer_id not in ep_counts:
                    ep_counts[cur_indexer_id] = 1
                else:
                    ep_counts[cur_indexer_id] += 1

                show_names[cur_indexer_id] = cur_status_result["show_name"]
                if cur_indexer_id not in sorted_show_ids:
                    sorted_show_ids.append(cur_indexer_id)

        return self.render(
            "/manage/subtitles_missed.mako",
            whichSubs=which_subs,
            show_names=show_names,
            ep_counts=ep_counts,
            sorted_show_ids=sorted_show_ids,
            title=_('Missing Subtitles'),
            header=_('Missing Subtitles'),
            topmenu='manage',
            controller='manage',
            action='subtitles_missed'
        )


class DownloadSubtitleMissedHandler(BaseHandler, ABC):
    @authenticated
    def post(self, *args, **kwargs):
        # make a list of all shows and their associated args
        to_download = {}
        for arg in self.get_arguments('toDownload'):
            indexer_id, what = arg.split('-')

            if indexer_id not in to_download:
                to_download[indexer_id] = []

            to_download[indexer_id].append(what)

        for cur_indexer_id in to_download:
            # get a list of all the eps we want to download subtitles if they just said "all"
            if 'all' in to_download[cur_indexer_id]:
                to_download[cur_indexer_id] = ['{}x{}'.format(x.season, x.episode) for x in
                                               self.db_session.query(TVEpisode).filter_by(showid=int(cur_indexer_id)).filter(
                                                   TVEpisode.status.endswith(4), TVEpisode.season != 0)]

            for epResult in to_download[cur_indexer_id]:
                season, episode = epResult.split('x')

                show = find_show(int(cur_indexer_id), session=self.db_session)
                show.get_episode(int(season), int(episode)).download_subtitles()

        return self.redirect('/manage/subtitleMissed/')


class BacklogShowHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        indexer_id = self.get_argument('indexer_id')

        sickrage.app.backlog_searcher.search_backlog(int(indexer_id))

        return self.redirect("/manage/backlogOverview/")


class BacklogOverviewHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        show_counts = {}
        show_cats = {}
        show_results = {}

        for curShow in get_show_list(session=self.db_session):
            if curShow.paused:
                continue

            ep_cats = {}
            ep_counts = {
                Overview.SKIPPED: 0,
                Overview.WANTED: 0,
                Overview.QUAL: 0,
                Overview.GOOD: 0,
                Overview.UNAIRED: 0,
                Overview.SNATCHED: 0,
                Overview.SNATCHED_PROPER: 0,
                Overview.SNATCHED_BEST: 0,
                Overview.MISSED: 0,
            }

            show_results[curShow.indexer_id] = []

            for curResult in sorted(curShow.episodes, key=lambda x: (x.season, x.episode), reverse=True):
                cur_ep_cat = curShow.get_overview(int(curResult.status or -1))
                if cur_ep_cat:
                    ep_cats["{}x{}".format(curResult.season, curResult.episode)] = cur_ep_cat
                    ep_counts[cur_ep_cat] += 1

                show_results[curShow.indexer_id] += [curResult]

            show_counts[curShow.indexer_id] = ep_counts
            show_cats[curShow.indexer_id] = ep_cats

        return self.render(
            "/manage/backlog_overview.mako",
            showCounts=show_counts,
            showCats=show_cats,
            showResults=show_results,
            title=_('Backlog Overview'),
            header=_('Backlog Overview'),
            topmenu='manage',
            controller='manage',
            action='backlog_overview'
        )


class MassEditHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        to_edit = self.get_argument('toEdit')

        show_ids = list(map(int, to_edit.split("|")))
        show_list = []
        show_names = []
        for curID in show_ids:
            show_obj = find_show(curID, session=self.db_session)
            if show_obj:
                show_list.append(show_obj)
                show_names.append(show_obj.name)

        skip_downloaded_all_same = True
        last_skip_downloaded = None

        flatten_folders_all_same = True
        last_flatten_folders = None

        paused_all_same = True
        last_paused = None

        default_ep_status_all_same = True
        last_default_ep_status = None

        anime_all_same = True
        last_anime = None

        sports_all_same = True
        last_sports = None

        quality_all_same = True
        last_quality = None

        subtitles_all_same = True
        last_subtitles = None

        scene_all_same = True
        last_scene = None

        air_by_date_all_same = True
        last_air_by_date = None

        root_dir_list = []

        for curShow in show_list:
            cur_root_dir = os.path.dirname(curShow.location)
            if cur_root_dir not in root_dir_list:
                root_dir_list.append(cur_root_dir)

            if skip_downloaded_all_same:
                # if we had a value already and this value is different then they're not all the same
                if last_skip_downloaded not in (None, curShow.skip_downloaded):
                    skip_downloaded_all_same = False
                else:
                    last_skip_downloaded = curShow.skip_downloaded

            # if we know they're not all the same then no point even bothering
            if paused_all_same:
                # if we had a value already and this value is different then they're not all the same
                if last_paused not in (None, curShow.paused):
                    paused_all_same = False
                else:
                    last_paused = curShow.paused

            if default_ep_status_all_same:
                if last_default_ep_status not in (None, curShow.default_ep_status):
                    default_ep_status_all_same = False
                else:
                    last_default_ep_status = curShow.default_ep_status

            if anime_all_same:
                # if we had a value already and this value is different then they're not all the same
                if last_anime not in (None, curShow.is_anime):
                    anime_all_same = False
                else:
                    last_anime = curShow.anime

            if flatten_folders_all_same:
                if last_flatten_folders not in (None, curShow.flatten_folders):
                    flatten_folders_all_same = False
                else:
                    last_flatten_folders = curShow.flatten_folders

            if quality_all_same:
                if last_quality not in (None, curShow.quality):
                    quality_all_same = False
                else:
                    last_quality = curShow.quality

            if subtitles_all_same:
                if last_subtitles not in (None, curShow.subtitles):
                    subtitles_all_same = False
                else:
                    last_subtitles = curShow.subtitles

            if scene_all_same:
                if last_scene not in (None, curShow.scene):
                    scene_all_same = False
                else:
                    last_scene = curShow.scene

            if sports_all_same:
                if last_sports not in (None, curShow.sports):
                    sports_all_same = False
                else:
                    last_sports = curShow.sports

            if air_by_date_all_same:
                if last_air_by_date not in (None, curShow.air_by_date):
                    air_by_date_all_same = False
                else:
                    last_air_by_date = curShow.air_by_date

        skip_downloaded_value = last_skip_downloaded if skip_downloaded_all_same else None
        default_ep_status_value = last_default_ep_status if default_ep_status_all_same else None
        paused_value = last_paused if paused_all_same else None
        anime_value = last_anime if anime_all_same else None
        flatten_folders_value = last_flatten_folders if flatten_folders_all_same else None
        quality_value = last_quality if quality_all_same else None
        subtitles_value = last_subtitles if subtitles_all_same else None
        scene_value = last_scene if scene_all_same else None
        sports_value = last_sports if sports_all_same else None
        air_by_date_value = last_air_by_date if air_by_date_all_same else None

        return self.render(
            "/manage/mass_edit.mako",
            showList=to_edit,
            showNames=show_names,
            skip_downloaded_value=skip_downloaded_value,
            default_ep_status_value=default_ep_status_value,
            paused_value=paused_value,
            anime_value=anime_value,
            flatten_folders_value=flatten_folders_value,
            quality_value=quality_value,
            subtitles_value=subtitles_value,
            scene_value=scene_value,
            sports_value=sports_value,
            air_by_date_value=air_by_date_value,
            root_dir_list=root_dir_list,
            title=_('Mass Edit'),
            header=_('Mass Edit'),
            topmenu='manage',
            controller='manage',
            action='mass_edit'
        )

    @authenticated
    async def post(self, *args, **kwargs):
        skip_downloaded = self.get_argument('skip_downloaded', None)
        paused = self.get_argument('paused', None)
        default_ep_status = self.get_argument('default_ep_status', None)
        anime = self.get_argument('anime', None)
        sports = self.get_argument('sports', None)
        scene = self.get_argument('scene', None)
        flatten_folders = self.get_argument('flatten_folders', None)
        quality_preset = self.get_argument('quality_preset', None)
        subtitles = self.get_argument('subtitles', None)
        air_by_date = self.get_argument('air_by_date', None)
        any_qualities = self.get_arguments('anyQualities')
        best_qualities = self.get_arguments('bestQualities')
        to_edit = self.get_argument('toEdit', None)

        i = 0
        dir_map = {}
        while True:
            cur_arg = self.get_argument('orig_root_dir_{}'.format(i), None)
            if not cur_arg:
                break

            end_dir = self.get_argument('new_root_dir_{}'.format(i))
            dir_map[cur_arg] = end_dir

            i += 1

        show_ids = to_edit.split("|")
        warnings, errors = [], []
        for curShow in show_ids:
            cur_warnings = []
            cur_errors = []

            show_obj = find_show(int(curShow), session=self.db_session)
            if not show_obj:
                continue

            cur_root_dir = os.path.dirname(show_obj.location)
            cur_show_dir = os.path.basename(show_obj.location)
            if cur_root_dir in dir_map and cur_root_dir != dir_map[cur_root_dir]:
                new_show_dir = os.path.join(dir_map[cur_root_dir], cur_show_dir)
                sickrage.app.log.info(
                    "For show " + show_obj.name + " changing dir from " + show_obj.location + " to " + new_show_dir)
            else:
                new_show_dir = show_obj.location

            if skip_downloaded == 'keep':
                new_skip_downloaded = show_obj.skip_downloaded
            else:
                new_skip_downloaded = True if skip_downloaded == 'enable' else False
            new_skip_downloaded = 'on' if new_skip_downloaded else 'off'

            if paused == 'keep':
                new_paused = show_obj.paused
            else:
                new_paused = True if paused == 'enable' else False
            new_paused = 'on' if new_paused else 'off'

            if default_ep_status == 'keep':
                new_default_ep_status = show_obj.default_ep_status
            else:
                new_default_ep_status = default_ep_status

            if anime == 'keep':
                new_anime = show_obj.anime
            else:
                new_anime = True if anime == 'enable' else False
            new_anime = 'on' if new_anime else 'off'

            if sports == 'keep':
                new_sports = show_obj.sports
            else:
                new_sports = True if sports == 'enable' else False
            new_sports = 'on' if new_sports else 'off'

            if scene == 'keep':
                new_scene = show_obj.is_scene
            else:
                new_scene = True if scene == 'enable' else False
            new_scene = 'on' if new_scene else 'off'

            if air_by_date == 'keep':
                new_air_by_date = show_obj.air_by_date
            else:
                new_air_by_date = True if air_by_date == 'enable' else False
            new_air_by_date = 'on' if new_air_by_date else 'off'

            if flatten_folders == 'keep':
                new_flatten_folders = show_obj.flatten_folders
            else:
                new_flatten_folders = True if flatten_folders == 'enable' else False
            new_flatten_folders = 'on' if new_flatten_folders else 'off'

            if subtitles == 'keep':
                new_subtitles = show_obj.subtitles
            else:
                new_subtitles = True if subtitles == 'enable' else False

            new_subtitles = 'on' if new_subtitles else 'off'

            if quality_preset == 'keep':
                any_qualities, best_qualities = Quality.split_quality(show_obj.quality)
            elif try_int(quality_preset, None):
                best_qualities = []

            post_data = {
                'show': curShow,
                'location': new_show_dir,
                'anyQualities': any_qualities,
                'bestQualities': best_qualities,
                'exceptions_list': [],
                'defaultEpStatus': new_default_ep_status,
                'skip_downloaded': new_skip_downloaded,
                'flatten_folders': new_flatten_folders,
                'paused': new_paused,
                'sports': new_sports,
                'subtitles': new_subtitles,
                'anime': new_anime,
                'scene': new_scene,
                'air_by_date': new_air_by_date,
                'directCall': 'true'
            }

            response = await TornadoHTTP().post(
                self.get_url("/home/editShow"),
                body=urlencode(post_data, True)
            )

            if response.body:
                cur_warnings += json_decode(response.body)['warnings']
                cur_errors += json_decode(response.body)['errors']

            if cur_warnings:
                sickrage.app.log.warning("Warnings: " + str(cur_warnings))
                warnings.append('<b>%s:</b>\n<ul>' % show_obj.name + ' '.join(
                    ['<li>%s</li>' % warning for warning in cur_warnings]) + "</ul>")

            if cur_errors:
                sickrage.app.log.error("Errors: " + str(cur_errors))
                errors.append('<b>%s:</b>\n<ul>' % show_obj.name + ' '.join(
                    ['<li>%s</li>' % error for error in cur_errors]) + "</ul>")

        if len(warnings) > 0:
            sickrage.app.alerts.message(
                _('{num_warnings:d} warning{plural} while saving changes:').format(num_warnings=len(warnings),
                                                                                   plural="" if len(
                                                                                       warnings) == 1 else "s"),
                " ".join(warnings))

        if len(errors) > 0:
            sickrage.app.alerts.error(
                _('{num_errors:d} error{plural} while saving changes:').format(num_errors=len(errors),
                                                                               plural="" if len(errors) == 1 else "s"),
                " ".join(errors))

        return self.redirect("/manage/")


class MassUpdateHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        return self.render(
            '/manage/mass_update.mako',
            title=_('Mass Update'),
            header=_('Mass Update'),
            topmenu='manage',
            controller='manage',
            action='mass_update'
        )

    @authenticated
    def post(self, *args, **kwargs):
        to_update = self.get_argument('toUpdate', '')
        to_refresh = self.get_argument('toRefresh', '')
        to_rename = self.get_argument('toRename', '')
        to_delete = self.get_argument('toDelete', '')
        to_remove = self.get_argument('toRemove', '')
        to_metadata = self.get_argument('toMetadata', '')
        to_subtitle = self.get_argument('toSubtitle', '')

        to_update = to_update.split('|') if len(to_update) else []
        to_refresh = to_refresh.split('|') if len(to_refresh) else []
        to_rename = to_rename.split('|') if len(to_rename) else []
        to_delete = to_delete.split('|') if len(to_delete) else []
        to_remove = to_remove.split('|') if len(to_remove) else []
        to_metadata = to_metadata.split('|') if len(to_metadata) else []
        to_subtitle = to_subtitle.split('|') if len(to_subtitle) else []

        errors = []
        refreshes = []
        updates = []
        renames = []
        subtitles = []

        for curShowID in set(to_update + to_refresh + to_rename + to_subtitle + to_delete + to_remove + to_metadata):
            if curShowID == '':
                continue

            show_obj = find_show(int(curShowID), session=self.db_session)
            if show_obj is None:
                continue

            if curShowID in to_delete:
                sickrage.app.show_queue.remove_show(show_obj.indexer_id, True)
                # don't do anything else if it's being deleted
                continue

            if curShowID in to_remove:
                sickrage.app.show_queue.remove_show(show_obj.indexer_id)
                # don't do anything else if it's being remove
                continue

            if curShowID in to_update:
                try:
                    sickrage.app.show_queue.update_show(show_obj.indexer_id, force=True)
                    updates.append(show_obj.name)
                except CantUpdateShowException as e:
                    errors.append(_("Unable to update show: {}").format(e))

            # don't bother refreshing shows that were updated anyway
            if curShowID in to_refresh and curShowID not in to_update:
                try:
                    sickrage.app.show_queue.refresh_show(show_obj.indexer_id, True)
                    refreshes.append(show_obj.name)
                except CantRefreshShowException as e:
                    errors.append(_("Unable to refresh show ") + show_obj.name + ": {}".format(e))

            if curShowID in to_rename:
                sickrage.app.show_queue.rename_show_episodes(show_obj.indexer_id)
                renames.append(show_obj.name)

            if curShowID in to_subtitle:
                sickrage.app.show_queue.download_subtitles(show_obj.indexer_id)
                subtitles.append(show_obj.name)

        if errors:
            sickrage.app.alerts.error(_("Errors encountered"), '<br >\n'.join(errors))

        message_detail = ""

        if updates:
            message_detail += _("<br><b>Updates</b><br><ul><li>")
            message_detail += "</li><li>".join(updates)
            message_detail += "</li></ul>"

        if refreshes:
            message_detail += _("<br><b>Refreshes</b><br><ul><li>")
            message_detail += "</li><li>".join(refreshes)
            message_detail += "</li></ul>"

        if renames:
            message_detail += _("<br><b>Renames</b><br><ul><li>")
            message_detail += "</li><li>".join(renames)
            message_detail += "</li></ul>"

        if subtitles:
            message_detail += _("<br><b>Subtitles</b><br><ul><li>")
            message_detail += "</li><li>".join(subtitles)
            message_detail += "</li></ul>"

        if updates + refreshes + renames + subtitles:
            sickrage.app.alerts.message(_("The following actions were queued:"), message_detail)

        return self.redirect('/manage/massUpdate')


class FailedDownloadsHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        limit = self.get_argument('limit', None) or 100

        if int(limit) == 0:
            dbData = self.db_session.query(MainDB.FailedSnatch).all()
        else:
            dbData = self.db_session.query(MainDB.FailedSnatch).limit(int(limit)).all()

        return self.render(
            "/manage/failed_downloads.mako",
            limit=int(limit),
            failedResults=dbData,
            title=_('Failed Downloads'),
            header=_('Failed Downloads'),
            topmenu='manage',
            controller='manage',
            action='failed_downloads'
        )

    @authenticated
    def post(self, *args, **kwargs):
        to_remove = self.get_argument('toRemove', None)
        if to_remove:
            to_remove = to_remove.split("|")
            self.db_session.query(MainDB.FailedSnatch).filter(MainDB.FailedSnatch.release.in_(to_remove)).delete(synchronize_session=False)
            return self.redirect('/manage/failedDownloads/')
