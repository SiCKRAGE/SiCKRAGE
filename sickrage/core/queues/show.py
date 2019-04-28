# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import datetime
import os
import time
import traceback

from sqlalchemy import orm

import sickrage
from sickrage.core.common import WANTED
from sickrage.core.exceptions import CantRefreshShowException, \
    CantRemoveShowException, CantUpdateShowException, EpisodeDeletedException, \
    MultipleShowObjectsException
from sickrage.core.helpers import scrub
from sickrage.core.queues import srQueue, srQueueItem, srQueuePriorities
from sickrage.core.scene_numbering import xem_refresh, get_xem_numbering_for_show
from sickrage.core.traktapi import srTraktAPI
from sickrage.core.tv.show import TVShow
from sickrage.core.tv.show.helpers import load_imdb_info, load_episodes_from_indexer
from sickrage.indexers import IndexerApi
from sickrage.indexers.exceptions import indexer_attributenotfound, \
    indexer_error, indexer_exception


class ShowQueue(srQueue):
    def __init__(self):
        srQueue.__init__(self, "SHOWQUEUE")

    @property
    def loading_show_list(self):
        return self._get_loading_show_list()

    def _is_in_queue(self, show, actions):
        return show.indexer_id in [x.show.indexer_id if x.show else 0 for x in self.queue_items if
                                   x.action_id in actions] if show else False

    def _is_being(self, show, actions):
        for x in self.queue_items:
            if show == x.show and x.action_id in actions:
                return True
        return False

    def is_in_update_queue(self, show):
        return self._is_in_queue(show, [ShowQueueActions.UPDATE, ShowQueueActions.FORCEUPDATE])

    def is_in_refresh_queue(self, show):
        return self._is_in_queue(show, [ShowQueueActions.REFRESH])

    def is_in_rename_queue(self, show):
        return self._is_in_queue(show, [ShowQueueActions.RENAME])

    def is_in_subtitle_queue(self, show):
        return self._is_in_queue(show, [ShowQueueActions.SUBTITLE])

    def is_being_removed(self, show):
        return self._is_being(show, [ShowQueueActions.REMOVE])

    def is_being_added(self, show):
        return self._is_being(show, [ShowQueueActions.ADD])

    def is_being_updated(self, show):
        return self._is_being(show, [ShowQueueActions.UPDATE, ShowQueueActions.FORCEUPDATE])

    def is_being_refreshed(self, show):
        return self._is_being(show, [ShowQueueActions.REFRESH])

    def is_being_renamed(self, show):
        return self._is_being(show, [ShowQueueActions.RENAME])

    def is_being_subtitled(self, show):
        return self._is_being(show, [ShowQueueActions.SUBTITLE])

    def _get_queue_items(self):
        return self.queue_items

    def _get_loading_show_list(self):
        return [x for x in self._get_queue_items() if x.is_loading]

    def updateShow(self, show, indexer_update_only=False, force=False):
        if self.is_being_added(show):
            raise CantUpdateShowException("{} is still being added, please wait until it is finished before trying to "
                                          "update.".format(show.name))

        if self.is_being_updated(show):
            raise CantUpdateShowException("{} is already being updated, can't update again until "
                                          "it's done.".format(show.name))

        if self.is_in_update_queue(show):
            raise CantUpdateShowException("{} is in the process of being updated, can't update again until "
                                          "it's done.".format(show.name))

        if force:
            sickrage.app.io_loop.add_callback(self.put, QueueItemForceUpdate(show.indexer_id, indexer_update_only))
        else:
            sickrage.app.io_loop.add_callback(self.put, QueueItemUpdate(show.indexer_id, indexer_update_only))

    def refreshShow(self, show, force=False):
        if (self.is_being_refreshed(show) or self.is_in_refresh_queue(show)) and not force:
            raise CantRefreshShowException("This show is already being refreshed or queued to be refreshed, skipping "
                                           "this request.")

        if show.paused and not force:
            sickrage.app.log.debug('Skipping show [{}] because it is paused.'.format(show.name))
            return

        sickrage.app.log.debug("Queueing show refresh for {}".format(show.name))

        sickrage.app.io_loop.add_callback(self.put, QueueItemRefresh(show.indexer_id, force=force))

    def renameShowEpisodes(self, show):
        sickrage.app.io_loop.add_callback(self.put, QueueItemRename(show.indexer_id))

    def download_subtitles(self, show):
        sickrage.app.io_loop.add_callback(self.put, QueueItemSubtitle(show.indexer_id))

    def addShow(self, indexer, indexer_id, showDir, default_status=None, quality=None, flatten_folders=None,
                lang=None, subtitles=None, sub_use_sr_metadata=None, anime=None, scene=None, paused=None,
                blacklist=None, whitelist=None, default_status_after=None, skip_downloaded=None):

        if lang is None:
            lang = sickrage.app.config.indexer_default_language

        sickrage.app.io_loop.add_callback(self.put, QueueItemAdd(indexer=indexer,
                                                                 indexer_id=indexer_id,
                                                                 showDir=showDir,
                                                                 default_status=default_status,
                                                                 quality=quality,
                                                                 flatten_folders=flatten_folders,
                                                                 lang=lang,
                                                                 subtitles=subtitles,
                                                                 sub_use_sr_metadata=sub_use_sr_metadata,
                                                                 anime=anime,
                                                                 scene=scene,
                                                                 paused=paused,
                                                                 blacklist=blacklist,
                                                                 whitelist=whitelist,
                                                                 default_status_after=default_status_after,
                                                                 skip_downloaded=skip_downloaded))

    def removeShow(self, show, full=False):
        if not show:
            raise CantRemoveShowException('Failed removing show: Show does not exist')
        elif not hasattr(show, 'indexer_id'):
            raise CantRemoveShowException('Failed removing show: Show does not have an indexer id')
        elif self._is_in_queue(show, (ShowQueueActions.REMOVE,)):
            raise CantRemoveShowException("{} is already queued to be removed".format(show))

        # remove other queued actions for this show.
        for x in self.queue_items:
            if show.indexer_id == x.show.indexer_id:
                self.queue.remove(x)

        sickrage.app.io_loop.add_callback(self.put, QueueItemRemove(indexer_id=show.indexer_id, full=full))


class ShowQueueActions(object):
    def __init__(self):
        pass

    REFRESH = 1
    ADD = 2
    UPDATE = 3
    FORCEUPDATE = 4
    RENAME = 5
    SUBTITLE = 6
    REMOVE = 7

    names = {
        REFRESH: 'Refresh',
        ADD: 'Add',
        UPDATE: 'Update',
        FORCEUPDATE: 'Force Update',
        RENAME: 'Rename',
        SUBTITLE: 'Subtitle',
        REMOVE: 'Remove Show'
    }


class ShowQueueItem(srQueueItem):
    """
    Represents an item in the queue waiting to be executed

    Can be either:
    - show being added (may or may not be associated with a show object)
    - show being refreshed
    - show being updated
    - show being force updated
    - show being subtitled
    """

    def __init__(self, indexer_id, action_id):
        super(ShowQueueItem, self).__init__(ShowQueueActions.names[action_id], action_id)

        try:
            self.show = TVShow.query.filter_by(indexer_id=indexer_id).one()
        except orm.exc.NoResultFound:
            self.show = None

    def is_in_queue(self):
        return self in sickrage.app.show_queue.queue_items

    @property
    def show_name(self):
        return str(self.show.indexer_id)

    @property
    def is_loading(self):
        return False


class QueueItemAdd(ShowQueueItem):
    def __init__(self, indexer, indexer_id, showDir, default_status, quality, flatten_folders, lang, subtitles,
                 sub_use_sr_metadata, anime, scene, paused, blacklist, whitelist, default_status_after,
                 skip_downloaded):
        super(QueueItemAdd, self).__init__(None, ShowQueueActions.ADD)

        self.indexer = indexer
        self.indexer_id = indexer_id
        self.showDir = showDir
        self.default_status = default_status
        self.quality = quality
        self.flatten_folders = flatten_folders
        self.lang = lang
        self.subtitles = subtitles
        self.sub_use_sr_metadata = sub_use_sr_metadata
        self.anime = anime
        self.scene = scene
        self.paused = paused
        self.blacklist = blacklist
        self.whitelist = whitelist
        self.default_status_after = default_status_after
        self.skip_downloaded = skip_downloaded
        self.priority = srQueuePriorities.HIGH

    @property
    def show_name(self):
        """
        Returns the show name if there is a show object created, if not returns
        the dir that the show is being added to.
        """
        return self.show.name if self.show else os.path.basename(self.showDir)

    @property
    def is_loading(self):
        """
        Returns True if we've gotten far enough to have a show object, or False
        if we still only know the folder name.
        """
        if self.show is None:
            return True

    def run(self):
        start_time = time.time()

        sickrage.app.log.info("Started adding show {} from show dir: {}".format(self.show_name, self.showDir))

        index_name = IndexerApi(self.indexer).name

        # make sure the Indexer IDs are valid
        try:

            lINDEXER_API_PARMS = IndexerApi(self.indexer).api_params.copy()
            lINDEXER_API_PARMS['cache'] = False
            lINDEXER_API_PARMS['language'] = self.lang or sickrage.app.config.indexer_default_language

            sickrage.app.log.info("{}: {}".format(index_name, repr(lINDEXER_API_PARMS)))

            t = IndexerApi(self.indexer).indexer(**lINDEXER_API_PARMS)

            try:
                s = t[self.indexer_id]
            except indexer_error:
                s = None

            if not s:
                return self._finish_early()

            # this usually only happens if they have an NFO in their show dir which gave us a Indexer ID that has no proper english version of the show
            if not getattr(s, 'seriesname'):
                sickrage.app.log.warning(
                    "Show in {} has no name on {}, probably the wrong language used to search with".format(self.showDir,
                                                                                                           index_name))
                sickrage.app.alerts.error(_("Unable to add show"),
                                          _("Show in {} has no name on {}, probably the wrong language. Delete .nfo "
                                            "and add manually in the correct language").format(self.showDir,
                                                                                               index_name))
                return self._finish_early()

            # if the show has no episodes/seasons
            if not len(s):
                sickrage.app.log.warning("Show " + str(s['seriesname']) + " is on " + str(
                    IndexerApi(self.indexer).name) + " but contains no season/episode data.")
                sickrage.app.alerts.error(_("Unable to add show"),
                                          _("Show ") + str(s['seriesname']) + _(" is on ") + str(
                                              IndexerApi(
                                                  self.indexer).name) + _(
                                              " but contains no season/episode data."))
                return self._finish_early()
        except Exception as e:
            sickrage.app.log.error(
                "{}: Error while loading information from indexer {}. Error: {}".format(self.indexer_id, index_name, e))

            sickrage.app.alerts.error(
                _("Unable to add show"),
                _("Unable to look up the show in {} on {} using ID {}, not using the NFO. Delete .nfo and try adding "
                  "manually again.").format(self.showDir, index_name, self.indexer_id)
            )

            if sickrage.app.config.use_trakt:
                title = self.showDir.split("/")[-1]

                data = {
                    'shows': [
                        {
                            'title': title,
                            'ids': {IndexerApi(self.indexer).trakt_id: self.indexer_id}
                        }
                    ]
                }

                srTraktAPI()["sync/watchlist"].remove(data)

            return self._finish_early()

        try:
            self.show = TVShow(**{'indexer': self.indexer, 'indexer_id': self.indexer_id, 'lang': self.lang})

            self.show.load_from_indexer()

            # set up initial values
            self.show.location = self.showDir
            self.show.subtitles = self.subtitles or sickrage.app.config.subtitles_default
            self.show.sub_use_sr_metadata = self.sub_use_sr_metadata
            self.show.quality = self.quality or sickrage.app.config.quality_default
            self.show.flatten_folders = self.flatten_folders or sickrage.app.config.flatten_folders_default
            self.show.anime = self.anime or sickrage.app.config.anime_default
            self.show.scene = self.scene or sickrage.app.config.scene_default
            self.show.skip_downloaded = self.skip_downloaded or sickrage.app.config.skip_downloaded_default
            self.show.paused = self.paused or False

            # set up default new/missing episode status
            sickrage.app.log.info(
                "Setting all current episodes to the specified default status: " + str(self.default_status))

            self.show.default_ep_status = self.default_status

            if self.show.anime:
                if self.blacklist:
                    self.show.release_groups.set_black_keywords(self.blacklist)
                if self.whitelist:
                    self.show.release_groups.set_white_keywords(self.whitelist)

            sickrage.app.main_db.update(self.show)
        except indexer_exception as e:
            sickrage.app.log.warning(
                _("Unable to add show due to an error with ") + IndexerApi(self.indexer).name + ": {}".format(e))
            if self.show:
                sickrage.app.alerts.error(
                    _("Unable to add ") + str(self.show.name) + _(" due to an error with ") + IndexerApi(
                        self.indexer).name + "")
            else:
                sickrage.app.alerts.error(
                    _("Unable to add show due to an error with ") + IndexerApi(self.indexer).name + "")
            return self._finish_early()

        except MultipleShowObjectsException:
            sickrage.app.log.warning(_("The show in ") + self.showDir + _(" is already in your show list, skipping"))
            sickrage.app.alerts.error(_('Show skipped'),
                                      _("The show in ") + self.showDir + _(" is already in your show list"))
            return self._finish_early()

        except Exception as e:
            sickrage.app.log.error(_("Error trying to add show: {}").format(e))
            sickrage.app.log.debug(traceback.format_exc())
            raise self._finish_early()

        try:
            sickrage.app.log.debug(_("Attempting to retrieve show info from IMDb"))
            load_imdb_info(self.show.indexer_id)
        except Exception as e:
            sickrage.app.log.error(_("Error loading IMDb info: {}").format(e))

        try:
            load_episodes_from_indexer(self.show.indexer_id)
        except Exception as e:
            sickrage.app.log.error(
                _("Error with ") + IndexerApi(self.show.indexer).name + _(", not creating episode list: {}").format(e))
            sickrage.app.log.debug(traceback.format_exc())

        try:
            self.show.load_episodes_from_dir()
        except Exception as e:
            sickrage.app.log.debug("Error searching dir for episodes: {}".format(e))
            sickrage.app.log.debug(traceback.format_exc())

        # if they set default ep status to WANTED then run the backlog to search for episodes
        if self.show.default_ep_status == WANTED:
            sickrage.app.log.info(_("Launching backlog for this show since its episodes are WANTED"))
            sickrage.app.backlog_searcher.search_backlog([self.show])

        self.show.write_metadata(force=True)
        self.show.populate_cache()

        if sickrage.app.config.use_trakt:
            # if there are specific episodes that need to be added by trakt
            sickrage.app.trakt_searcher.manageNewShow(self.show)

            # add show to trakt.tv library
            if sickrage.app.config.trakt_sync:
                sickrage.app.trakt_searcher.addShowToTraktLibrary(self.show)

            if sickrage.app.config.trakt_sync_watchlist:
                sickrage.app.log.info("update watchlist")
                sickrage.app.notifier_providers['trakt'].update_watchlist(show_obj=self.show)

        # Load XEM data to DB for show
        xem_refresh(self.show.indexer_id, self.show.indexer, force=True)

        # check if show has XEM mapping so we can determin if searches should go by scene numbering or indexer
        # numbering.
        if not self.scene and get_xem_numbering_for_show(self.show.indexer_id, self.show.indexer):
            self.show.scene = 1

        self.show.default_ep_status = self.default_status_after

        self.show.save_to_db()

        sickrage.app.name_cache.build(self.show)

        sickrage.app.quicksearch_cache.add_show(self.show.indexer_id)

        sickrage.app.log.info(
            "Finished adding show {} in {}s from show dir: {}".format(self.show_name,
                                                                      round(time.time() - start_time, 2),
                                                                      self.showDir))

    def _finish_early(self):
        if self.show: sickrage.app.show_queue.removeShow(self.show)


class QueueItemRefresh(ShowQueueItem):
    def __init__(self, indexer_id=None, force=False):
        super(QueueItemRefresh, self).__init__(indexer_id, ShowQueueActions.REFRESH)

        # force refresh certain items
        self.force = force

    def run(self):
        start_time = time.time()

        sickrage.app.log.info("Performing refresh for show: {}".format(self.show.name))

        self.show.refresh_dir()

        self.show.write_metadata(force=self.force)
        self.show.populate_cache(force=self.force)

        # Load XEM data to DB for show
        # xem_refresh(self.show.indexer_id, self.show.indexer)

        self.show.last_refresh = datetime.date.today().toordinal()

        sickrage.app.log.info(
            "Finished refresh in {}s for show: {}".format(round(time.time() - start_time, 2), self.show.name))


class QueueItemRename(ShowQueueItem):
    def __init__(self, indexer_id=None):
        super(QueueItemRename, self).__init__(indexer_id, ShowQueueActions.RENAME)

    def run(self):
        sickrage.app.log.info("Performing renames for show: {}".format(self.show.name))

        if not os.path.isdir(self.show.location):
            sickrage.app.log.warning(
                "Can't perform rename on " + self.show.name + " when the show dir is missing.")
            return

        ep_obj_rename_list = []

        ep_obj_list = self.show.get_all_episodes(has_location=True)
        for cur_ep_obj in ep_obj_list:
            # Only want to rename if we have a location
            if cur_ep_obj.location:
                if cur_ep_obj.relatedEps:
                    # do we have one of multi-episodes in the rename list already
                    have_already = False
                    for cur_related_ep in cur_ep_obj.relatedEps + [cur_ep_obj]:
                        if cur_related_ep in ep_obj_rename_list:
                            have_already = True
                            break
                    if not have_already:
                        ep_obj_rename_list.append(cur_ep_obj)

                else:
                    ep_obj_rename_list.append(cur_ep_obj)

        for cur_ep_obj in ep_obj_rename_list:
            cur_ep_obj.rename()

        sickrage.app.log.info("Finished renames for show: {}".format(self.show.name))


class QueueItemSubtitle(ShowQueueItem):
    def __init__(self, indexer_id=None):
        super(QueueItemSubtitle, self).__init__(indexer_id, ShowQueueActions.SUBTITLE)

    def run(self):
        sickrage.app.log.info("Started downloading subtitles for show: {}".format(self.show.name))

        self.show.download_subtitles()

        sickrage.app.log.info("Finished downloading subtitles for show: {}".format(self.show.name))


class QueueItemUpdate(ShowQueueItem):
    def __init__(self, indexer_id=None, indexer_update_only=False, action_id=ShowQueueActions.UPDATE):
        super(QueueItemUpdate, self).__init__(indexer_id, action_id)
        self.indexer_update_only = indexer_update_only
        self.force = False

    def run(self):
        start_time = time.time()

        sickrage.app.log.info("Performing updates for show: {}".format(self.show.name))

        try:
            sickrage.app.log.debug("Retrieving show info from " + IndexerApi(self.show.indexer).name + "")
            self.show.load_from_indexer(cache=False)
        except indexer_error as e:
            sickrage.app.log.warning(
                "Unable to contact " + IndexerApi(self.show.indexer).name + ", aborting: {}".format(e))
            return
        except indexer_attributenotfound as e:
            sickrage.app.log.warning(
                "Data retrieved from " + IndexerApi(self.show.indexer).name + " was incomplete, aborting: {}".format(e))
            return

        try:
            if not self.indexer_update_only:
                sickrage.app.log.debug("Attempting to retrieve show info from IMDb")
                load_imdb_info(self.show.indexer_id)
        except Exception as e:
            sickrage.app.log.warning("Error loading IMDb info for {}: {}".format(IndexerApi(self.show.indexer).name, e))

        # get episode list from DB
        DBEpList = self.show.load_episodes_from_db()
        IndexerEpList = None

        # get episode list from TVDB
        try:
            IndexerEpList = load_episodes_from_indexer(self.show.indexer_id)
        except indexer_exception as e:
            sickrage.app.log.error("Unable to get info from " + IndexerApi(
                self.show.indexer).name + ", the show info will not be refreshed: {}".format(e))

        if not IndexerEpList:
            sickrage.app.log.error("No data returned from " + IndexerApi(
                self.show.indexer).name + ", unable to update this show")
        else:
            # for each ep we found on indexer delete it from the DB list
            for curSeason in IndexerEpList:
                for curEpisode in IndexerEpList[curSeason]:
                    if curSeason in DBEpList and curEpisode in DBEpList[curSeason]:
                        del DBEpList[curSeason][curEpisode]

            # remaining episodes in the DB list are not on the indexer, just delete them from the DB
            for curSeason in DBEpList:
                for curEpisode in DBEpList[curSeason]:
                    sickrage.app.log.info(
                        "Permanently deleting episode " + str(curSeason) + "x" + str(curEpisode) + " from the database")
                    try:
                        self.show.get_episode(curSeason, curEpisode).deleteEpisode()
                    except EpisodeDeletedException:
                        pass

        # cleanup
        scrub(DBEpList)
        scrub(IndexerEpList)

        sickrage.app.quicksearch_cache.update_show(self.show.indexer_id)

        sickrage.app.log.info(
            "Finished updates in {}s for show: {}".format(round(time.time() - start_time, 2), self.show.name))

        # refresh show
        if not self.indexer_update_only:
            sickrage.app.show_queue.refreshShow(self.show, self.force)


class QueueItemForceUpdate(QueueItemUpdate):
    def __init__(self, indexer_id=None, indexer_update_only=False):
        super(QueueItemForceUpdate, self).__init__(indexer_id, indexer_update_only, ShowQueueActions.FORCEUPDATE)
        self.indexer_update_only = indexer_update_only
        self.force = True


class QueueItemRemove(ShowQueueItem):
    def __init__(self, indexer_id=None, full=False):
        super(QueueItemRemove, self).__init__(indexer_id, ShowQueueActions.REMOVE)

        # lets make sure this happens before any other high priority actions
        self.priority = srQueuePriorities.EXTREME
        self.full = full

    @property
    def is_loading(self):
        """
        Returns false cause we are removing the show.
        """
        return False

    def run(self):
        sickrage.app.log.info("Removing show: {}".format(self.show.name))

        sickrage.app.quicksearch_cache.del_show(self.show.indexer_id)

        self.show.delete_show(full=self.full)

        if sickrage.app.config.use_trakt:
            try:
                sickrage.app.trakt_searcher.removeShowFromTraktLibrary(self.show)
            except Exception as e:
                sickrage.app.log.warning(
                    "Unable to delete show from Trakt: %s. Error: %s" % (self.show.name, e))

        sickrage.app.log.info("Finished removing show: {}".format(self.show.name))
