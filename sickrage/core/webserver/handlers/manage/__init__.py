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
from functools import cmp_to_key

from tornado.escape import json_encode, json_decode
from tornado.web import authenticated

import sickrage
from sickrage.core.common import Overview
from sickrage.core.common import Quality, Qualities, EpisodeStatus
from sickrage.core.databases.main import MainDB
from sickrage.core.enums import SearchFormat, SeriesProviderID
from sickrage.core.exceptions import CantUpdateShowException, CantRefreshShowException, EpisodeNotFoundException, AnidbAdbaConnectionException, NoNFOException
from sickrage.core.helpers import try_int, checkbox_to_value, flatten
from sickrage.core.helpers.anidb import get_release_groups_for_anime, short_group_names
from sickrage.core.queues.search import BacklogSearchTask, FailedSearchTask
from sickrage.core.scene_numbering import xem_refresh
from sickrage.core.tv.show.helpers import find_show, get_show_list
from sickrage.core.webserver.handlers.base import BaseHandler
from sickrage.subtitles import Subtitles


def set_episode_status(series_id, eps, status, direct=None):
    if not status:
        err_msg = _("Invalid status")
        if direct:
            sickrage.app.alerts.error(_('Error'), err_msg)
        return False, err_msg

    show_obj = find_show(int(series_id))

    if not show_obj:
        err_msg = _("Error", "Show not in show list")
        if direct:
            sickrage.app.alerts.error(_('Error'), err_msg)
        return False, err_msg

    wanted = []
    trakt_data = []

    if eps:
        for curEp in eps.split('|'):
            if not curEp:
                sickrage.app.log.debug("curEp was empty when trying to setStatus")

            sickrage.app.log.debug("Attempting to set status on episode " + curEp + " to " + status.display_name)

            ep_info = curEp.split('x')

            if not all(ep_info):
                sickrage.app.log.debug("Something went wrong when trying to setStatus, epInfo[0]: %s, epInfo[1]: %s" % (ep_info[0], ep_info[1]))
                continue

            try:
                episode_object = show_obj.get_episode(int(ep_info[0]), int(ep_info[1]))
            except EpisodeNotFoundException as e:
                return False, _("Episode couldn't be retrieved")

            if status in [EpisodeStatus.WANTED, EpisodeStatus.FAILED]:
                # figure out what episodes are wanted so we can backlog them
                wanted += [(episode_object.season, episode_object.episode)]

            # don't let them mess up UNAIRED episodes
            if episode_object.status == EpisodeStatus.UNAIRED:
                sickrage.app.log.warning("Refusing to change status of " + curEp + " because it is UNAIRED")
                continue

            if status in EpisodeStatus.composites(EpisodeStatus.DOWNLOADED) and episode_object.status not in flatten(
                    [EpisodeStatus.composites(EpisodeStatus.SNATCHED), EpisodeStatus.composites(EpisodeStatus.SNATCHED_PROPER),
                     EpisodeStatus.composites(EpisodeStatus.SNATCHED_BEST), EpisodeStatus.composites(EpisodeStatus.DOWNLOADED),
                     EpisodeStatus.IGNORED]) and not os.path.isfile(episode_object.location):
                sickrage.app.log.warning("Refusing to change status of " + curEp + " to DOWNLOADED because it's not SNATCHED/DOWNLOADED")
                continue

            if status == EpisodeStatus.FAILED and episode_object.status not in flatten([
                EpisodeStatus.composites(EpisodeStatus.SNATCHED), EpisodeStatus.composites(EpisodeStatus.SNATCHED_PROPER),
                EpisodeStatus.composites(EpisodeStatus.SNATCHED_BEST), EpisodeStatus.composites(EpisodeStatus.DOWNLOADED),
                EpisodeStatus.composites(EpisodeStatus.ARCHIVED)]):
                sickrage.app.log.warning("Refusing to change status of " + curEp + " to FAILED because it's not SNATCHED/DOWNLOADED")
                continue

            if episode_object.status in flatten([EpisodeStatus.composites(EpisodeStatus.DOWNLOADED),
                                                 EpisodeStatus.composites(EpisodeStatus.ARCHIVED)]) and status == EpisodeStatus.WANTED:
                sickrage.app.log.info("Removing release_name for episode as you want to set a downloaded "
                                      "episode back to wanted, so obviously you want it replaced")
                episode_object.release_name = ""

            episode_object.status = status

            episode_object.save()

            trakt_data += [(episode_object.season, episode_object.episode)]

        data = sickrage.app.notification_providers['trakt'].trakt_episode_data_generate(trakt_data)
        if data and sickrage.app.config.trakt.enable and sickrage.app.config.trakt.sync_watchlist:
            if status in [EpisodeStatus.WANTED, EpisodeStatus.FAILED]:
                sickrage.app.log.debug("Add episodes, series_id: " + str(show_obj.series_id) + ", Title " + str(show_obj.name) + " to Watchlist")
                sickrage.app.notification_providers['trakt'].update_watchlist(show_obj, data_episode=data, update="add")
            elif status in flatten([EpisodeStatus.IGNORED, EpisodeStatus.SKIPPED, EpisodeStatus.composites(EpisodeStatus.DOWNLOADED),
                                    EpisodeStatus.composites(EpisodeStatus.ARCHIVED)]):
                sickrage.app.log.debug("Remove episodes, series_id: " + str(show_obj.series_id) + ", Title " + str(show_obj.name) + " from Watchlist")
                sickrage.app.notification_providers['trakt'].update_watchlist(show_obj, data_episode=data, update="remove")

    if status == EpisodeStatus.WANTED and not show_obj.paused:
        msg = _("Backlog was automatically started for the following seasons of ") + "<b>" + show_obj.name + "</b>:<br>"
        msg += '<ul>'

        for season, episode in wanted:
            if (show_obj.series_id, season, episode) in sickrage.app.search_queue.SNATCH_HISTORY:
                sickrage.app.search_queue.SNATCH_HISTORY.remove((show_obj.series_id, season, episode))

            sickrage.app.search_queue.put(BacklogSearchTask(show_obj.series_id, show_obj.series_provider_id, season, episode))
            msg += "<li>" + _("Season ") + str(season) + "</li>"
            sickrage.app.log.info("Sending backlog for " + show_obj.name + " season " + str(season) + " because some eps were set to wanted")

        msg += "</ul>"

        if wanted:
            sickrage.app.alerts.message(_("Backlog started"), msg)
    elif status == EpisodeStatus.WANTED and show_obj.paused:
        sickrage.app.log.info("Some episodes were set to wanted, but {} is paused. Not adding to Backlog until show is unpaused".format(show_obj.name))

    if status == EpisodeStatus.FAILED:
        msg = _(
            "Retrying Search was automatically started for the following season of ") + "<b>" + show_obj.name + "</b>:<br>"
        msg += '<ul>'

        for season, episode in wanted:
            if (show_obj.series_id, season, episode) in sickrage.app.search_queue.SNATCH_HISTORY:
                sickrage.app.search_queue.SNATCH_HISTORY.remove((show_obj.series_id, season, episode))

            sickrage.app.search_queue.put(FailedSearchTask(show_obj.series_id, show_obj.series_provider_id, season, episode))

            msg += "<li>" + _("Season ") + str(season) + "</li>"
            sickrage.app.log.info("Retrying Search for {} season {} because some eps were set to failed".format(show_obj.name, season))

        msg += "</ul>"

        if wanted:
            sickrage.app.alerts.message(_("Retry Search started"), msg)

    return True, ""


def edit_show(series_id, any_qualities, best_qualities, exceptions_list, location=None, flatten_folders=None, paused=None, direct_call=None,
              dvd_order=None, series_provider_language=None, subtitles=None, sub_use_sr_metadata=None, skip_downloaded=None, rls_ignore_words=None,
              search_format=None, rls_require_words=None, anime=None, blacklist=None, whitelist=None, scene=None, default_ep_status=None, quality_preset=None,
              search_delay=None):
    show_obj = find_show(int(series_id))
    if not show_obj:
        err_msg = _("Unable to find the specified show: ") + str(series_id)
        if direct_call:
            sickrage.app.alerts.error(_('Error'), err_msg)
        return False, err_msg

    flatten_folders = not checkbox_to_value(flatten_folders)  # UI inverts this value
    dvd_order = checkbox_to_value(dvd_order)
    skip_downloaded = checkbox_to_value(skip_downloaded)
    paused = checkbox_to_value(paused)
    anime = checkbox_to_value(anime)
    scene = checkbox_to_value(scene)
    subtitles = checkbox_to_value(subtitles)
    sub_use_sr_metadata = checkbox_to_value(sub_use_sr_metadata)

    series_provider_language = series_provider_language if series_provider_language else show_obj.lang

    # if we changed the language then kick off an update
    if series_provider_language == show_obj.lang:
        do_update = False
    else:
        do_update = True

    if show_obj.scene or show_obj.anime:
        do_update_scene_numbering = False
    else:
        do_update_scene_numbering = True

    show_obj.paused = paused
    show_obj.anime = anime
    show_obj.scene = scene
    show_obj.search_format = SearchFormat[search_format]
    show_obj.subtitles = subtitles
    show_obj.sub_use_sr_metadata = sub_use_sr_metadata
    show_obj.default_ep_status = EpisodeStatus[default_ep_status]
    show_obj.skip_downloaded = skip_downloaded

    # If directCall from mass_edit_update no scene exceptions handling or black and white list handling
    if direct_call:
        do_update_exceptions = False
    else:
        if set(exceptions_list) == set(show_obj.scene_exceptions):
            do_update_exceptions = False
        else:
            do_update_exceptions = True

        if anime:
            if whitelist:
                shortwhitelist = short_group_names(whitelist)
                show_obj.release_groups.set_white_keywords(shortwhitelist)
            else:
                show_obj.release_groups.set_white_keywords([])

            if blacklist:
                shortblacklist = short_group_names(blacklist)
                show_obj.release_groups.set_black_keywords(shortblacklist)
            else:
                show_obj.release_groups.set_black_keywords([])

    warnings, errors = [], []

    try:
        new_quality = Qualities[quality_preset]
    except KeyError:
        new_quality = Quality.combine_qualities([Qualities[x] for x in any_qualities], [Qualities[x] for x in best_qualities])

    show_obj.quality = new_quality

    # reversed for now
    if bool(show_obj.flatten_folders) != bool(flatten_folders):
        show_obj.flatten_folders = flatten_folders
        try:
            sickrage.app.show_queue.refresh_show(show_obj.series_id, show_obj.series_provider_id, True)
        except CantRefreshShowException as e:
            errors.append(_("Unable to refresh this show: {}").format(e))

    if not direct_call:
        show_obj.lang = series_provider_language
        show_obj.dvd_order = dvd_order
        show_obj.rls_ignore_words = rls_ignore_words.strip()
        show_obj.rls_require_words = rls_require_words.strip()
        show_obj.search_delay = int(search_delay)

    # if we change location clear the db of episodes, change it, write to db, and rescan
    if os.path.normpath(show_obj.location) != os.path.normpath(location):
        sickrage.app.log.debug(os.path.normpath(show_obj.location) + " != " + os.path.normpath(location))
        if not os.path.isdir(location) and not sickrage.app.config.general.create_missing_show_dirs:
            warnings.append("New location {} does not exist".format(location))

        # don't bother if we're going to update anyway
        elif not do_update:
            # change it
            try:
                show_obj.location = location
                try:
                    sickrage.app.show_queue.refresh_show(show_obj.series_id, show_obj.series_provider_id, True)
                except CantRefreshShowException as e:
                    errors.append(_("Unable to refresh this show:{}").format(e))
                    # grab updated info from TVDB
                    # showObj.loadEpisodesFromSeriesProvider()
                    # rescan the episodes in the new folder
            except NoNFOException:
                warnings.append(
                    _("The folder at %s doesn't contain a tvshow.nfo - copy your files to that folder before "
                      "you change the directory in SiCKRAGE.") % location)

    # force the update
    if do_update:
        try:
            sickrage.app.show_queue.update_show(show_obj.series_id, show_obj.series_provider_id, force=True)
        except CantUpdateShowException as e:
            errors.append(_("Unable to update show: {}").format(e))

    if do_update_exceptions:
        try:
            show_obj.update_scene_exceptions(exceptions_list)
        except CantUpdateShowException:
            warnings.append(_("Unable to force an update on scene exceptions of the show."))

    if do_update_scene_numbering:
        try:
            xem_refresh(show_obj.series_id, show_obj.series_provider_id, True)
        except CantUpdateShowException:
            warnings.append(_("Unable to force an update on scene numbering of the show."))

    # commit changes to database
    show_obj.save()

    if direct_call:
        return True if len(warnings) == 0 and len(errors) == 0 else False, json_encode({'warnings': warnings, 'errors': errors})

    if len(warnings) > 0:
        sickrage.app.alerts.message(
            _('{num_warnings:d} warning{plural} while saving changes:').format(num_warnings=len(warnings),
                                                                               plural="" if len(
                                                                                   warnings) == 1 else "s"),
            '<ul>' + '\n'.join(['<li>{0}</li>'.format(warning) for warning in warnings]) + "</ul>")

    if len(errors) > 0:
        sickrage.app.alerts.error(
            _('{num_errors:d} error{plural} while saving changes:').format(num_errors=len(errors),
                                                                           plural="" if len(errors) == 1 else "s"),
            '<ul>' + '\n'.join(['<li>{0}</li>'.format(error) for error in errors]) + "</ul>")

    return True, ""


class ManageHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        return self.redirect('/manage/massUpdate')


class ShowEpisodeStatusesHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        series_id = self.get_argument('series_id')
        which_status = self.get_argument('whichStatus')

        session = sickrage.app.main_db.session()

        result = {}
        for dbData in session.query(MainDB.TVEpisode).filter_by(series_id=int(series_id),
                                                                status=EpisodeStatus[which_status]).filter(MainDB.TVEpisode.season != 0):
            cur_season = int(dbData.season)
            cur_episode = int(dbData.episode)

            if cur_season not in result:
                result[cur_season] = {}

            result[cur_season][cur_episode] = dbData.name

        return self.write(json_encode(result))


class EpisodeStatusesHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        which_status = self.get_argument('whichStatus', None)

        ep_counts = {}
        show_names = {}
        sorted_show_ids = []
        status_list = []

        if which_status:
            which_status = EpisodeStatus[which_status]

        # if we have no status then this is as far as we need to go
        if which_status:
            for show in sorted(get_show_list(), key=lambda d: d.name):
                for episode in show.episodes:
                    if episode.season != 0 and episode.status == which_status:
                        if show.series_id not in ep_counts:
                            ep_counts[show.series_id] = 1
                        else:
                            ep_counts[show.series_id] += 1

                        show_names[show.series_id] = show.name
                        if show.series_id not in sorted_show_ids:
                            sorted_show_ids.append(show.series_id)

        return self.render('manage/episode_statuses.mako',
                           title="Episode Overview",
                           header="Episode Overview",
                           topmenu='manage',
                           whichStatus=which_status,
                           show_names=show_names,
                           ep_counts=ep_counts,
                           sorted_show_ids=sorted_show_ids,
                           controller='manage',
                           action='episode_statuses')


class ChangeEpisodeStatusesHandler(BaseHandler):
    @authenticated
    def post(self, *args, **kwargs):
        old_status = self.get_argument('oldStatus')
        new_status = self.get_argument('newStatus')

        session = sickrage.app.main_db.session()

        # make a list of all shows and their associated args
        to_change = {}
        for x in self.get_arguments('toChange'):
            series_id, what = x.split('-')

            if series_id not in to_change:
                to_change[series_id] = []

            to_change[series_id].append(what)

        for series_id in to_change:
            # get a list of all the eps we want to change if they just said "all"
            if 'all' in to_change[series_id]:
                all_eps = ['{}x{}'.format(x.season, x.episode) for x in
                           session.query(MainDB.TVEpisode).filter_by(series_id=int(series_id),
                                                                     status=EpisodeStatus[old_status]).filter(MainDB.TVEpisode.season != 0)]
                to_change[series_id] = all_eps

            set_episode_status(series_id=series_id, eps='|'.join(to_change[series_id]), status=EpisodeStatus[new_status], direct=True)

        return self.redirect('/manage/episodeStatuses/')


class SetEpisodeStatusHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')
        eps = self.get_argument('eps')
        status = self.get_argument('status')
        direct = bool(self.get_argument('direct', None))

        status, message = set_episode_status(series_id=show, eps=eps, status=EpisodeStatus[status], direct=direct)

        if direct:
            return json_encode({'result': 'success'}) if status is True else json_encode({'result': 'error', 'message': message})

        return self.redirect("/home/displayShow?show=" + show) if status is True else self._genericMessage(_("Error"), message)


class ShowSubtitleMissedHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        series_id = self.get_argument('series_id')
        which_subs = self.get_argument('whichSubs')

        session = sickrage.app.main_db.session()

        result = {}

        for dbData in session.query(MainDB.TVEpisode).filter_by(series_id=int(series_id)). \
                filter(MainDB.TVEpisode.status.endswith(4), MainDB.TVEpisode.season != 0):
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


class SubtitleMissedHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        which_subs = self.get_argument('whichSubs', None)

        ep_counts = {}
        show_names = {}
        sorted_show_ids = []
        status_results = []

        if which_subs:
            for s in get_show_list():
                if not s.subtitles == 1:
                    continue

                for e in s.episodes:
                    if e.season != 0 and (str(e.status).endswith('4') or str(e.status).endswith('6')):
                        status_results += [{
                            'show_name': s.name,
                            'series_id': s.series_id,
                            'subtitles': e.subtitles
                        }]

            for cur_status_result in sorted(status_results, key=lambda k: k['show_name']):
                if which_subs == 'all':
                    if not frozenset(Subtitles().wanted_languages()).difference(
                            cur_status_result["subtitles"].split(',')):
                        continue
                elif which_subs in cur_status_result["subtitles"]:
                    continue

                series_id = int(cur_status_result["series_id"])
                if series_id not in ep_counts:
                    ep_counts[series_id] = 1
                else:
                    ep_counts[series_id] += 1

                show_names[series_id] = cur_status_result["show_name"]
                if series_id not in sorted_show_ids:
                    sorted_show_ids.append(series_id)

        return self.render('manage/subtitles_missed.mako',
                           whichSubs=which_subs,
                           show_names=show_names,
                           ep_counts=ep_counts,
                           sorted_show_ids=sorted_show_ids,
                           title=_('Missing Subtitles'),
                           header=_('Missing Subtitles'),
                           topmenu='manage',
                           controller='manage',
                           action='subtitles_missed')


class DownloadSubtitleMissedHandler(BaseHandler):
    @authenticated
    def post(self, *args, **kwargs):
        session = sickrage.app.main_db.session()

        # make a list of all shows and their associated args
        to_download = {}
        for arg in self.get_arguments('toDownload'):
            series_id, what = arg.split('-')

            if series_id not in to_download:
                to_download[series_id] = []

            to_download[series_id].append(what)

        for series_id in to_download:
            # get a list of all the eps we want to download subtitles if they just said "all"
            if 'all' in to_download[series_id]:
                to_download[series_id] = ['{}x{}'.format(x.season, x.episode) for x in session.query(MainDB.TVEpisode).
                    filter_by(series_id=int(series_id)).filter(MainDB.TVEpisode.status.endswith(4), MainDB.TVEpisode.season != 0)]

            for epResult in to_download[series_id]:
                season, episode = epResult.split('x')

                show = find_show(int(series_id))
                show.get_episode(int(season), int(episode)).download_subtitles()

        return self.redirect('/manage/subtitleMissed/')


class BacklogShowHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        series_id = self.get_argument('series_id')
        series_provider_id = self.get_argument('series_provider_id')

        sickrage.app.backlog_searcher.search_backlog(int(series_id), SeriesProviderID[series_provider_id])

        return self.redirect("/manage/backlogOverview/")


class BacklogOverviewHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        show_counts = {}
        show_cats = {}
        show_results = {}

        for curShow in get_show_list():
            if curShow.paused:
                continue

            ep_cats = {}
            ep_counts = {
                Overview.SKIPPED: 0,
                Overview.WANTED: 0,
                Overview.LOW_QUALITY: 0,
                Overview.GOOD: 0,
                Overview.UNAIRED: 0,
                Overview.SNATCHED: 0,
                Overview.SNATCHED_PROPER: 0,
                Overview.SNATCHED_BEST: 0,
                Overview.MISSED: 0,
            }

            show_results[curShow.series_id] = []

            for curResult in sorted(curShow.episodes, key=lambda x: (x.season, x.episode), reverse=True):
                cur_ep_cat = curResult.overview or -1
                if cur_ep_cat:
                    ep_cats["{}x{}".format(curResult.season, curResult.episode)] = cur_ep_cat
                    ep_counts[cur_ep_cat] += 1

                show_results[curShow.series_id] += [curResult]

            show_counts[curShow.series_id] = ep_counts
            show_cats[curShow.series_id] = ep_cats

        return self.render('manage/backlog_overview.mako',
                           showCounts=show_counts,
                           showCats=show_cats,
                           showResults=show_results,
                           title=_('Backlog Overview'),
                           header=_('Backlog Overview'),
                           topmenu='manage',
                           controller='manage',
                           action='backlog_overview')


class EditShowHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        show = self.get_argument('show')

        groups = []

        show_obj = find_show(int(show))

        if not show_obj:
            err_string = _("Unable to find the specified show: ") + str(show)
            return self._genericMessage(_("Error"), err_string)

        if show_obj.is_anime:
            whitelist = show_obj.release_groups.whitelist
            blacklist = show_obj.release_groups.blacklist

            try:
                groups = get_release_groups_for_anime(show_obj.name)
            except AnidbAdbaConnectionException as e:
                sickrage.app.log.debug('Unable to get ReleaseGroups: {}'.format(e))

            return self.render('home/edit_show.mako',
                               show=show_obj,
                               quality=show_obj.quality,
                               scene_exceptions=[x.split('|')[0] for x in show_obj.scene_exceptions],
                               groups=groups,
                               whitelist=whitelist,
                               blacklist=blacklist,
                               title=_('Edit Show'),
                               header=_('Edit Show'),
                               controller='home',
                               action="edit_show")
        else:
            return self.render('home/edit_show.mako',
                               show=show_obj,
                               quality=show_obj.quality,
                               scene_exceptions=[x.split('|')[0] for x in show_obj.scene_exceptions],
                               title=_('Edit Show'),
                               header=_('Edit Show'),
                               controller='home',
                               action="edit_show")

    @authenticated
    def post(self, *args, **kwargs):
        show = self.get_argument('show')
        location = self.get_argument('location', None)
        any_qualities = self.get_arguments('anyQualities')
        best_qualities = self.get_arguments('bestQualities')
        exceptions_list = self.get_arguments('exceptions_list')
        flatten_folders = self.get_argument('flatten_folders', None)
        paused = self.get_argument('paused', None)
        direct_call = bool(self.get_argument('directCall', None))
        search_format = self.get_argument('search_format', None)
        dvd_order = self.get_argument('dvd_order', None)
        series_provider_language = self.get_argument('seriesProviderLanguage', None)
        subtitles = self.get_argument('subtitles', None)
        sub_use_sr_metadata = self.get_argument('sub_use_sr_metadata', None)
        scene = self.get_argument('scene', None)
        skip_downloaded = self.get_argument('skip_downloaded', None)
        rls_ignore_words = self.get_argument('rls_ignore_words', None)
        rls_require_words = self.get_argument('rls_require_words', None)
        anime = self.get_argument('anime', None)
        blacklist = self.get_argument('blacklist', None)
        whitelist = self.get_argument('whitelist', None)
        default_ep_status = self.get_argument('defaultEpStatus', None)
        quality_preset = self.get_argument('quality_preset', None)
        search_delay = self.get_argument('search_delay', None)

        status, message = edit_show(series_id=show, location=location, any_qualities=any_qualities, best_qualities=best_qualities,
                                    exceptions_list=exceptions_list,
                                    flatten_folders=flatten_folders, paused=paused, direct_call=direct_call, search_format=search_format,
                                    dvd_order=dvd_order, series_provider_language=series_provider_language, subtitles=subtitles,
                                    sub_use_sr_metadata=sub_use_sr_metadata,
                                    skip_downloaded=skip_downloaded, rls_ignore_words=rls_ignore_words, rls_require_words=rls_require_words, anime=anime,
                                    blacklist=blacklist, whitelist=whitelist, default_ep_status=default_ep_status, quality_preset=quality_preset,
                                    scene=scene, search_delay=search_delay)

        if direct_call:
            return json_encode({'result': 'success'}) if status is True else json_encode({'result': 'error', 'message': message})

        return self.redirect("/home/displayShow?show=" + show) if status is True else self._genericMessage(_("Error"), message)


class MassEditHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        to_edit = self.get_argument('toEdit')

        show_ids = list(map(int, to_edit.split("|")))
        show_list = []
        show_names = []
        for curID in show_ids:
            show_obj = find_show(curID)
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

        quality_all_same = True
        last_quality = None

        subtitles_all_same = True
        last_subtitles = None

        scene_all_same = True
        last_scene = None

        search_format_all_same = True
        last_search_format = None

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

            if scene_all_same:
                # if we had a value already and this value is different then they're not all the same
                if last_scene not in (None, curShow.scene):
                    scene_all_same = False
                else:
                    last_scene = curShow.scene

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

            if search_format_all_same:
                if last_search_format not in (None, curShow.search_format):
                    search_format_all_same = False
                else:
                    last_search_format = curShow.search_format

        skip_downloaded_value = last_skip_downloaded if skip_downloaded_all_same else None
        default_ep_status_value = last_default_ep_status if default_ep_status_all_same else None
        paused_value = last_paused if paused_all_same else None
        scene_value = last_scene if scene_all_same else None
        anime_value = last_anime if anime_all_same else None
        flatten_folders_value = last_flatten_folders if flatten_folders_all_same else None
        quality_value = last_quality if quality_all_same else None
        subtitles_value = last_subtitles if subtitles_all_same else None
        search_format_value = last_search_format if search_format_all_same else None

        return self.render('manage/mass_edit.mako',
                           showList=to_edit,
                           showNames=show_names,
                           skip_downloaded_value=skip_downloaded_value,
                           default_ep_status_value=default_ep_status_value,
                           paused_value=paused_value,
                           scene_value=scene_value,
                           anime_value=anime_value,
                           flatten_folders_value=flatten_folders_value,
                           quality_value=quality_value,
                           subtitles_value=subtitles_value,
                           search_format_value=search_format_value,
                           root_dir_list=root_dir_list,
                           title=_('Mass Edit'),
                           header=_('Mass Edit'),
                           topmenu='manage',
                           controller='manage',
                           action='mass_edit')

    @authenticated
    def post(self, *args, **kwargs):
        skip_downloaded = self.get_argument('skip_downloaded', None)
        scene = self.get_argument('scene', None)
        paused = self.get_argument('paused', None)
        default_ep_status = self.get_argument('default_ep_status', None)
        anime = self.get_argument('anime', None)
        flatten_folders = self.get_argument('flatten_folders', None)
        quality_preset = self.get_argument('quality_preset', None)
        subtitles = self.get_argument('subtitles', None)
        search_format = self.get_argument('search_format', None)
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

            show_obj = find_show(int(curShow))
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

            if scene == 'keep':
                new_scene = show_obj.scene
            else:
                new_scene = True if scene == 'enable' else False
            new_scene = 'on' if new_scene else 'off'

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

            if search_format == 'keep':
                new_search_format = show_obj.search_format
            else:
                new_search_format = search_format

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

            status, message = edit_show(series_id=curShow, location=new_show_dir, any_qualities=any_qualities, best_qualities=best_qualities,
                                        exceptions_list=[], default_ep_status=new_default_ep_status, skip_downloaded=new_skip_downloaded,
                                        flatten_folders=new_flatten_folders, paused=new_paused, search_format=new_search_format, subtitles=new_subtitles,
                                        anime=new_anime, scene=new_scene, direct_call=True)

            if status is False:
                cur_warnings += json_decode(message)['warnings']
                cur_errors += json_decode(message)['errors']

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
                                                                                   plural="" if len(warnings) == 1 else "s"), " ".join(warnings))

        if len(errors) > 0:
            sickrage.app.alerts.error(
                _('{num_errors:d} error{plural} while saving changes:').format(num_errors=len(errors),
                                                                               plural="" if len(errors) == 1 else "s"), " ".join(errors))

        return self.redirect("/manage/")


class MassUpdateHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        shows_list = sorted([x for x in get_show_list() if not sickrage.app.show_queue.is_being_removed(x.series_id)],
                            key=cmp_to_key(lambda x, y: x.name < y.name))

        return self.render('manage/mass_update.mako',
                           shows_list=shows_list,
                           title=_('Mass Update'),
                           header=_('Mass Update'),
                           topmenu='manage',
                           controller='manage',
                           action='mass_update')

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

            show_obj = find_show(int(curShowID))
            if show_obj is None:
                continue

            if curShowID in to_delete:
                sickrage.app.show_queue.remove_show(show_obj.series_id, show_obj.series_provider_id, True)
                # don't do anything else if it's being deleted
                continue

            if curShowID in to_remove:
                sickrage.app.show_queue.remove_show(show_obj.series_id, show_obj.series_provider_id)
                # don't do anything else if it's being remove
                continue

            if curShowID in to_update:
                try:
                    sickrage.app.show_queue.update_show(show_obj.series_id, show_obj.series_provider_id, force=True)
                    updates.append(show_obj.name)
                except CantUpdateShowException as e:
                    errors.append(_("Unable to update show: {}").format(e))

            # don't bother refreshing shows that were updated anyway
            if curShowID in to_refresh and curShowID not in to_update:
                try:
                    sickrage.app.show_queue.refresh_show(show_obj.series_id, show_obj.series_provider_id, True)
                    refreshes.append(show_obj.name)
                except CantRefreshShowException as e:
                    errors.append(_("Unable to refresh show ") + show_obj.name + ": {}".format(e))

            if curShowID in to_rename:
                sickrage.app.show_queue.rename_show_episodes(show_obj.series_id, show_obj.series_provider_id)
                renames.append(show_obj.name)

            if curShowID in to_subtitle:
                sickrage.app.show_queue.download_subtitles(show_obj.series_id, show_obj.series_provider_id)
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


class FailedDownloadsHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        limit = self.get_argument('limit', None) or 100

        session = sickrage.app.main_db.session()

        query = session.query(MainDB.FailedSnatch)
        if int(limit):
            query = session.query(MainDB.FailedSnatch).limit(int(limit))

        return self.render('manage/failed_downloads.mako',
                           limit=int(limit),
                           failedResults=query.all(),
                           title=_('Failed Downloads'),
                           header=_('Failed Downloads'),
                           topmenu='manage',
                           controller='manage',
                           action='failed_downloads')

    @authenticated
    def post(self, *args, **kwargs):
        to_remove = self.get_argument('toRemove', None)

        session = sickrage.app.main_db.session()

        if to_remove:
            to_remove = to_remove.split("|")
            session.query(MainDB.FailedSnatch).filter(MainDB.FailedSnatch.release.in_(to_remove)).delete(synchronize_session=False)
            session.commit()
            return self.redirect('/manage/failedDownloads/')
