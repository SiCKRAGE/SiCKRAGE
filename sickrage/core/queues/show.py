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
import os
import time
import traceback
from enum import Enum

import sickrage
from sickrage.core.common import EpisodeStatus
from sickrage.core.exceptions import CantRefreshShowException, CantRemoveShowException, CantUpdateShowException, EpisodeDeletedException, \
    MultipleShowObjectsException
from sickrage.core.queues import Queue, Task, TaskPriority
from sickrage.core.scene_numbering import xem_refresh
from sickrage.core.traktapi import TraktAPI
from sickrage.core.tv.show import TVShow
from sickrage.core.tv.show.helpers import find_show
from sickrage.core.websocket import WebSocketMessage
from sickrage.series_providers.exceptions import SeriesProviderAttributeNotFound, SeriesProviderException


class ShowQueue(Queue):
    def __init__(self):
        Queue.__init__(self, "SHOWQUEUE")

    @property
    def loading_show_list(self):
        return [x.series_id for x in self.tasks.copy().values() if x.is_loading]

    def _is_in_queue(self, series_id, actions):
        for task in self.tasks.copy().values():
            if task.is_queued() and task.series_id == series_id and task.action in actions:
                return True

        return False

    def _is_being(self, series_id, actions):
        for task in self.tasks.copy().values():
            if task.is_started() and task.series_id == series_id and task.action in actions:
                return True

        return False

    def is_queued_to_remove(self, series_id):
        return self._is_in_queue(series_id, [ShowTaskActions.REMOVE])

    def is_queued_to_add(self, series_id):
        return self._is_in_queue(series_id, [ShowTaskActions.ADD])

    def is_queued_to_update(self, series_id):
        return self._is_in_queue(series_id, [ShowTaskActions.UPDATE, ShowTaskActions.FORCEUPDATE])

    def is_queued_to_refresh(self, series_id):
        return self._is_in_queue(series_id, [ShowTaskActions.REFRESH])

    def is_queued_to_rename(self, series_id):
        return self._is_in_queue(series_id, [ShowTaskActions.RENAME])

    def is_queued_to_subtitle(self, series_id):
        return self._is_in_queue(series_id, [ShowTaskActions.SUBTITLE])

    def is_being_removed(self, series_id):
        return self._is_being(series_id, [ShowTaskActions.REMOVE])

    def is_being_added(self, series_id):
        return self._is_being(series_id, [ShowTaskActions.ADD])

    def is_being_updated(self, series_id):
        return self._is_being(series_id, [ShowTaskActions.UPDATE, ShowTaskActions.FORCEUPDATE])

    def is_being_refreshed(self, series_id):
        return self._is_being(series_id, [ShowTaskActions.REFRESH])

    def is_being_renamed(self, series_id):
        return self._is_being(series_id, [ShowTaskActions.RENAME])

    def is_being_subtitled(self, series_id):
        return self._is_being(series_id, [ShowTaskActions.SUBTITLE])

    def update_show(self, series_id, series_provider_id, force=False):
        show_obj = find_show(series_id, series_provider_id)

        if self.is_being_added(series_id):
            raise CantUpdateShowException("{} is still being added, please wait until it is finished before trying to update.".format(show_obj.name))

        if self.is_being_updated(series_id):
            raise CantUpdateShowException("{} is already being updated, can't update again until it's done.".format(show_obj.name))

        task_id = self.put(ShowTaskUpdate(series_id, series_provider_id, force))

        self.put(ShowTaskRefresh(series_id, series_provider_id, force=force), depend=[task_id])

    def refresh_show(self, series_id, series_provider_id, force=False):
        show_obj = find_show(series_id, series_provider_id)

        if (self.is_being_refreshed(series_id) or self.is_being_refreshed(series_id)) and not force:
            raise CantRefreshShowException("This show is already being refreshed or queued to be refreshed, skipping this request.")

        if show_obj.paused and not force:
            sickrage.app.log.debug('Skipping show [{}] because it is paused.'.format(show_obj.name))
            return

        sickrage.app.log.debug("Queueing show refresh for {}".format(show_obj.name))

        self.put(ShowTaskRefresh(series_id, series_provider_id, force=force))

    def rename_show_episodes(self, series_id, series_provider_id):
        self.put(ShowTaskRename(series_id, series_provider_id))

    def download_subtitles(self, series_id, series_provider_id):
        self.put(ShowTaskSubtitle(series_id, series_provider_id))

    def add_show(self, series_provider_id, series_id, showDir, default_status=None, quality=None, flatten_folders=None, lang=None, subtitles=None,
                 sub_use_sr_metadata=None, anime=None, search_format=None, dvd_order=None, paused=None, blacklist=None, whitelist=None,
                 default_status_after=None, scene=None, skip_downloaded=None):

        if lang is None:
            lang = sickrage.app.config.general.series_provider_default_language

        self.put(ShowTaskAdd(series_provider_id=series_provider_id,
                             series_id=series_id,
                             show_dir=showDir,
                             default_status=default_status,
                             quality=quality,
                             flatten_folders=not flatten_folders,
                             lang=lang,
                             subtitles=subtitles,
                             sub_use_sr_metadata=sub_use_sr_metadata,
                             anime=anime,
                             dvd_order=dvd_order,
                             search_format=search_format,
                             paused=paused,
                             blacklist=blacklist,
                             whitelist=whitelist,
                             default_status_after=default_status_after,
                             scene=scene,
                             skip_downloaded=skip_downloaded))

    def remove_show(self, series_id, series_provider_id, full=False):
        show_obj = find_show(series_id, series_provider_id)

        if not show_obj:
            raise CantRemoveShowException('Failed removing show: Show does not exist')
        elif not hasattr(show_obj, 'series_id'):
            raise CantRemoveShowException('Failed removing show: Show does not have an series_provider_id id')
        elif self._is_being(show_obj.series_id, (ShowTaskActions.REMOVE,)):
            raise CantRemoveShowException("{} is already queued to be removed".format(show_obj))

        # remove other queued actions for this show.
        self.remove_task(series_id)

        self.put(ShowTaskForceRemove(series_id=series_id, series_provider_id=series_provider_id, full=full))


class ShowTaskActions(Enum):
    REFRESH = 'Refresh'
    ADD = 'Add'
    UPDATE = 'Update'
    FORCEUPDATE = 'Force Update'
    RENAME = 'Rename'
    SUBTITLE = 'Subtitle'
    REMOVE = 'Remove Show'


class ShowTask(Task):
    """
    Represents an item in the queue waiting to be executed

    Can be either:
    - show being added (may or may not be associated with a show object)
    - show being refreshed
    - show being updated
    - show being force updated
    - show being subtitled
    """

    def __init__(self, series_id, series_provider_id, action):
        super(ShowTask, self).__init__(action.value, action)
        self.series_id = series_id
        self.series_provider_id = series_provider_id

    def is_in_queue(self):
        return self in sickrage.app.show_queue.queue

    @property
    def show_name(self):
        show_obj = find_show(self.series_id, self.series_provider_id)
        return show_obj.name if show_obj else str(self.series_id)

    @property
    def is_loading(self):
        return False

    def run(self):
        show_obj = find_show(self.series_id, self.series_provider_id)
        if show_obj:
            WebSocketMessage('SHOW_QUEUE_STATUS_UPDATED', {'seriesSlug': show_obj.slug, 'showQueueStatus': show_obj.show_queue_status}).push()
        else:
            WebSocketMessage('SHOW_QUEUE_STATUS_UPDATED',
                             {'seriesSlug': f'{self.series_id}-{self.series_provider_id.slug}', 'action': self.action.name}).push()

    def finish(self):
        show_obj = find_show(self.series_id, self.series_provider_id)
        if show_obj:
            WebSocketMessage('SHOW_QUEUE_STATUS_UPDATED', {'seriesSlug': show_obj.slug, 'showQueueStatus': show_obj.show_queue_status}).push()
        else:
            WebSocketMessage('SHOW_QUEUE_STATUS_UPDATED',
                             {'seriesSlug': f'{self.series_id}-{self.series_provider_id.slug}', 'action': self.action.name}).push()


class ShowTaskAdd(ShowTask):
    def __init__(self, series_provider_id, series_id, show_dir, default_status, quality, flatten_folders, lang, subtitles, sub_use_sr_metadata, anime,
                 dvd_order, search_format, paused, blacklist, whitelist, default_status_after, scene, skip_downloaded):
        super(ShowTaskAdd, self).__init__(series_id, series_provider_id, ShowTaskActions.ADD)

        self.show_dir = show_dir
        self.default_status = default_status
        self.quality = quality
        self.flatten_folders = flatten_folders
        self.lang = lang
        self.subtitles = subtitles
        self.sub_use_sr_metadata = sub_use_sr_metadata
        self.anime = anime
        self.search_format = search_format
        self.dvd_order = dvd_order
        self.paused = paused
        self.blacklist = blacklist
        self.whitelist = whitelist
        self.default_status_after = default_status_after
        self.scene = scene
        self.skip_downloaded = skip_downloaded
        self.priority = TaskPriority.HIGH

    @property
    def show_name(self):
        """
        Returns the show name if there is a show object created, if not returns
        the dir that the show is being added to.
        """

        show_obj = find_show(self.series_id, self.series_provider_id)
        return show_obj.name if show_obj else os.path.basename(self.show_dir)

    @property
    def is_loading(self):
        """
        Returns True if we've gotten far enough to have a show object, or False
        if we still only know the folder name.
        """
        if find_show(self.series_id, self.series_provider_id):
            return True

    def run(self):
        super(ShowTaskAdd, self).run()

        start_time = time.time()

        sickrage.app.log.info("Started adding show {} from show dir: {}".format(self.show_name, self.show_dir))

        s = sickrage.app.series_providers[self.series_provider_id].search(self.series_id,
                                                                          language=self.lang or sickrage.app.config.general.series_provider_default_language,
                                                                          enable_cache=False)

        if not s:
            sickrage.app.alerts.error(
                _("Unable to add show"),
                _("Unable to look up the show in {} on {} using ID {}, not using the NFO. Delete .nfo and try adding "
                  "manually again.").format(self.show_dir, sickrage.app.series_providers[self.series_provider_id].name, self.series_id)
            )

            if sickrage.app.config.trakt.enable:
                title = self.show_dir.split("/")[-1]

                data = {
                    'shows': [
                        {
                            'title': title,
                            'ids': {sickrage.app.series_providers[self.series_provider_id].trakt_id: self.series_id}
                        }
                    ]
                }

                TraktAPI()["sync/watchlist"].remove(data)

            return self._finish_early()

        # this usually only happens if they have an NFO in their show dir which gave us a series id that has no
        # proper english version of the show
        try:
            s.seriesname
        except AttributeError:
            sickrage.app.log.warning(
                f"Show in {self.show_dir} has no name on {sickrage.app.series_providers[self.series_provider_id].name}, "
                f"probably the wrong language used to search with")

            sickrage.app.alerts.error(_("Unable to add show"),
                                      _(f"Show in {self.show_dir} has no name on {sickrage.app.series_providers[self.series_provider_id].name}, "
                                        f"probably the wrong language. Delete .nfo and add manually in the correct language"))

            return self._finish_early()

        # if the show has no episodes/seasons
        if not len(s):
            sickrage.app.log.warning("Show " + str(s['seriesname']) + " is on " + str(
                sickrage.app.series_providers[self.series_provider_id].name) + "but contains no season/episode "
                                                                               "data.")
            sickrage.app.alerts.error(_("Unable to add show"),
                                      _("Show ") + str(s['seriesname']) + _(" is on ") + str(sickrage.app.series_providers[self.series_provider_id].name) + _(
                                          " but contains no season/episode data."))
            return self._finish_early()

        try:
            # add show to database
            show_obj = TVShow(self.series_id, self.series_provider_id, lang=self.lang, location=self.show_dir)

            # set up initial values
            show_obj.subtitles = self.subtitles if self.subtitles is not None else sickrage.app.config.subtitles.default
            show_obj.sub_use_sr_metadata = self.sub_use_sr_metadata if self.sub_use_sr_metadata is not None else False
            show_obj.quality = self.quality if self.quality is not None else sickrage.app.config.general.quality_default
            show_obj.flatten_folders = self.flatten_folders if self.flatten_folders is not None else sickrage.app.config.general.flatten_folders_default
            show_obj.scene = self.scene if self.scene is not None else sickrage.app.config.general.scene_default
            show_obj.anime = self.anime if self.anime is not None else sickrage.app.config.general.anime_default
            show_obj.dvd_order = self.dvd_order if self.dvd_order is not None else False
            show_obj.search_format = self.search_format if self.search_format is not None else sickrage.app.config.general.search_format_default
            show_obj.skip_downloaded = self.skip_downloaded if self.skip_downloaded is not None else sickrage.app.config.general.skip_downloaded_default
            show_obj.paused = self.paused if self.paused is not None else False

            # set up default new/missing episode status
            sickrage.app.log.info("Setting all current episodes to the specified default status: " + str(self.default_status))
            show_obj.default_ep_status = self.default_status

            # save to database
            show_obj.save()

            if show_obj.anime:
                if self.blacklist:
                    show_obj.release_groups.set_black_keywords(self.blacklist)
                if self.whitelist:
                    show_obj.release_groups.set_white_keywords(self.whitelist)
        except SeriesProviderException as e:
            sickrage.app.log.warning(
                _("Unable to add show due to an error with ") + sickrage.app.series_providers[self.series_provider_id].name + ": {}".format(e))
            sickrage.app.alerts.error(_("Unable to add show due to an error with ") + sickrage.app.series_providers[self.series_provider_id].name + "")
            return self._finish_early()
        except MultipleShowObjectsException:
            sickrage.app.log.warning(_("The show in ") + self.show_dir + _(" is already in your show list, skipping"))
            sickrage.app.alerts.error(_('Show skipped'),
                                      _("The show in ") + self.show_dir + _(" is already in your show list"))
            return self._finish_early()
        except Exception as e:
            sickrage.app.log.error(_("Error trying to add show: {}").format(e))
            sickrage.app.log.debug(traceback.format_exc())
            raise self._finish_early()

        try:
            sickrage.app.log.debug(_("Attempting to retrieve show info from IMDb"))
            show_obj.load_imdb_info()
        except Exception as e:
            sickrage.app.log.debug(_("Error loading IMDb info: {}").format(e))
            sickrage.app.log.debug(traceback.format_exc())

        try:
            show_obj.load_episodes_from_series_provider()
        except Exception as e:
            sickrage.app.log.debug(_("Error with ") + show_obj.series_provider.name + _(", not creating episode list: {}").format(e))
            sickrage.app.log.debug(traceback.format_exc())

        try:
            show_obj.load_episodes_from_dir()
        except Exception as e:
            sickrage.app.log.debug("Error searching dir for episodes: {}".format(e))
            sickrage.app.log.debug(traceback.format_exc())

        show_obj.write_metadata(force=True)
        show_obj.populate_cache()

        if sickrage.app.config.trakt.enable:
            # if there are specific episodes that need to be added by trakt
            sickrage.app.trakt_searcher.manage_new_show(show_obj)

            # add show to trakt.tv library
            if sickrage.app.config.trakt.sync:
                sickrage.app.trakt_searcher.add_show_to_trakt_library(show_obj)

            if sickrage.app.config.trakt.sync_watchlist:
                sickrage.app.log.info("update watchlist")
                sickrage.app.notification_providers['trakt'].update_watchlist(show_obj)

        # Retrieve scene exceptions
        show_obj.retrieve_scene_exceptions()

        # Load XEM data to DB for show
        xem_refresh(show_obj.series_id, show_obj.series_provider_id, force=True)

        # check if show has XEM mapping so we can determine if searches should go by scene numbering or series_provider_id
        # numbering.
        # if not self.scene and get_xem_numbering_for_show(show_obj.series_id, show_obj.series_provider_id):
        #     show_obj.scene = 1

        # if they set default ep status to WANTED then run the backlog to search for episodes
        if show_obj.default_ep_status == EpisodeStatus.WANTED:
            sickrage.app.log.info(_("Launching backlog for this show since it has episodes that are WANTED"))
            sickrage.app.backlog_searcher.search_backlog(show_obj.series_id, show_obj.series_provider_id)

        show_obj.default_ep_status = self.default_status_after

        show_obj.save()

        WebSocketMessage('SHOW_ADDED',
                         {'seriesSlug': show_obj.slug,
                          'series': show_obj.to_json(progress=True)}).push()

        sickrage.app.log.info("Finished adding show {} in {}s from show dir: {}".format(self.show_name, round(time.time() - start_time, 2), self.show_dir))

    def _finish_early(self):
        try:
            sickrage.app.show_queue.remove_show(self.series_id, self.series_provider_id)
        except CantRemoveShowException:
            WebSocketMessage('SHOW_REMOVED',
                             {'seriesSlug': f'{self.series_id}-{self.series_provider_id.slug}'}).push()


class ShowTaskRefresh(ShowTask):
    def __init__(self, series_id=None, series_provider_id=None, force=False):
        super(ShowTaskRefresh, self).__init__(series_id, series_provider_id, ShowTaskActions.REFRESH)

        # force refresh certain items
        self.force = force

    def run(self):
        super(ShowTaskRefresh, self).run()

        start_time = time.time()

        tv_show = find_show(self.series_id, self.series_provider_id)

        sickrage.app.log.info("Performing refresh for show: {}".format(tv_show.name))

        tv_show.refresh_dir()
        tv_show.write_metadata(force=self.force)
        tv_show.populate_cache(force=self.force)

        # Load XEM data to DB for show
        # xem_refresh(show.series_id, show.series_provider_id)

        tv_show.last_refresh = datetime.datetime.now()

        tv_show.save()

        WebSocketMessage('SHOW_REFRESHED',
                         {'seriesSlug': tv_show.slug,
                          'series': tv_show.to_json(episodes=True, details=True)}).push()

        sickrage.app.log.info("Finished refresh in {}s for show: {}".format(round(time.time() - start_time, 2), tv_show.name))


class ShowTaskRename(ShowTask):
    def __init__(self, series_id=None, series_provider_id=None):
        super(ShowTaskRename, self).__init__(series_id, series_provider_id, ShowTaskActions.RENAME)

    def run(self):
        super(ShowTaskRename, self).run()

        tv_show = find_show(self.series_id, self.series_provider_id)

        sickrage.app.log.info("Performing renames for show: {}".format(tv_show.name))

        if not os.path.isdir(tv_show.location):
            sickrage.app.log.warning("Can't perform rename on " + tv_show.name + " when the show dir is missing.")
            return

        ep_obj_rename_list = []

        for cur_ep_obj in (x for x in tv_show.episodes if x.location):
            # Only want to rename if we have a location
            if cur_ep_obj.location:
                if cur_ep_obj.related_episodes:
                    # do we have one of multi-episodes in the rename list already
                    have_already = False
                    for cur_related_ep in cur_ep_obj.related_episodes + [cur_ep_obj]:
                        if cur_related_ep in ep_obj_rename_list:
                            have_already = True
                            break
                    if not have_already:
                        ep_obj_rename_list.append(cur_ep_obj)
                else:
                    ep_obj_rename_list.append(cur_ep_obj)

        for cur_ep_obj in ep_obj_rename_list:
            cur_ep_obj.rename()

        WebSocketMessage('SHOW_RENAMED',
                         {'seriesSlug': tv_show.slug,
                          'series': tv_show.to_json(episodes=True, details=True)}).push()

        sickrage.app.log.info("Finished renames for show: {}".format(tv_show.name))


class ShowTaskSubtitle(ShowTask):
    def __init__(self, series_id=None, series_provider_id=None):
        super(ShowTaskSubtitle, self).__init__(series_id, series_provider_id, ShowTaskActions.SUBTITLE)

    def run(self):
        super(ShowTaskSubtitle, self).run()

        tv_show = find_show(self.series_id, self.series_provider_id)

        sickrage.app.log.info("Started downloading subtitles for show: {}".format(tv_show.name))

        tv_show.download_subtitles()

        WebSocketMessage('SHOW_SUBTITLED',
                         {'seriesSlug': tv_show.slug,
                          'series': tv_show.to_json(episodes=True, details=True)}).push()

        sickrage.app.log.info("Finished downloading subtitles for show: {}".format(tv_show.name))


class ShowTaskUpdate(ShowTask):
    def __init__(self, series_id=None, series_provider_id=None, force=False, action=ShowTaskActions.UPDATE):
        super(ShowTaskUpdate, self).__init__(series_id, series_provider_id, action if not force else ShowTaskActions.FORCEUPDATE)
        self.force = force

    def run(self):
        super(ShowTaskUpdate, self).run()

        show_obj = find_show(self.series_id, self.series_provider_id)

        start_time = time.time()

        sickrage.app.log.info("Performing updates for show: {}".format(show_obj.name))

        try:
            sickrage.app.log.debug("Retrieving show info from " + show_obj.series_provider.name + "")
            show_obj.load_from_series_provider(cache=False)
        except SeriesProviderAttributeNotFound as e:
            sickrage.app.log.warning("Data retrieved from " + show_obj.series_provider.name + " was incomplete, aborting: {}".format(e))
            return
        except SeriesProviderException as e:
            sickrage.app.log.warning("Unable to contact " + show_obj.series_provider.name + ", aborting: {}".format(e))
            return

        try:
            sickrage.app.log.debug("Attempting to retrieve show info from IMDb")
            show_obj.load_imdb_info()
        except Exception as e:
            sickrage.app.log.warning("Error loading IMDb info for {}: {}".format(show_obj.series_provider.name, e))

        # get episodes from database
        db_episodes = {}
        for data in show_obj.episodes:
            if data.season not in db_episodes:
                db_episodes[data.season] = {}
            db_episodes[data.season].update({data.episode: True})

        # get episodes from a series provider
        try:
            series_provider_episodes = show_obj.load_episodes_from_series_provider()
        except SeriesProviderException as e:
            sickrage.app.log.warning(
                "Unable to get info from " + show_obj.series_provider.name + ", the show info will not be refreshed: {}".format(e))
            series_provider_episodes = None

        if not series_provider_episodes:
            sickrage.app.log.warning("No data returned from " + show_obj.series_provider.name + ", unable to update this show")
        else:
            # for each ep we found on series_provider_id delete it from the DB list
            for curSeason in series_provider_episodes:
                for curEpisode in series_provider_episodes[curSeason]:
                    if curSeason in db_episodes and curEpisode in db_episodes[curSeason]:
                        del db_episodes[curSeason][curEpisode]

            # remaining episodes in the DB list are not on the series_provider_id, just delete them from the DB
            for curSeason in db_episodes:
                for curEpisode in db_episodes[curSeason]:
                    sickrage.app.log.info("Permanently deleting episode " + str(curSeason) + "x" + str(curEpisode) + " from the database")
                    try:
                        show_obj.delete_episode(curSeason, curEpisode)
                    except EpisodeDeletedException:
                        continue

        show_obj.retrieve_scene_exceptions()

        WebSocketMessage('SHOW_UPDATED',
                         {'seriesSlug': show_obj.slug,
                          'series': show_obj.to_json(episodes=True, details=True)}).push()

        sickrage.app.log.info("Finished updates in {}s for show: {}".format(round(time.time() - start_time, 2), show_obj.name))


class ShowTaskForceRemove(ShowTask):
    def __init__(self, series_id=None, series_provider_id=None, full=False):
        super(ShowTaskForceRemove, self).__init__(series_id, series_provider_id, ShowTaskActions.REMOVE)

        # lets make sure this happens before any other high priority actions
        self.priority = TaskPriority.EXTREME
        self.full = full

    @property
    def is_loading(self):
        """
        Returns false cause we are removing the show.
        """
        return False

    def run(self):
        super(ShowTaskForceRemove, self).run()

        show_obj = find_show(self.series_id, self.series_provider_id)

        sickrage.app.log.info("Removing show: {}".format(show_obj.name))

        show_obj.delete_show(full=self.full)

        if sickrage.app.config.trakt.enable:
            try:
                sickrage.app.trakt_searcher.remove_show_from_trakt_library(show_obj)
            except Exception as e:
                sickrage.app.log.warning("Unable to delete show from Trakt: %s. Error: %s" % (show_obj.name, e))

        WebSocketMessage('SHOW_REMOVED',
                         {'seriesSlug': show_obj.slug}).push()

        sickrage.app.log.info("Finished removing show: {}".format(show_obj.name))
