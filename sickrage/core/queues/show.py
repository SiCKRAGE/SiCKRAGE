#!/usr/bin/env python2

# Author: echel0n <sickrage.tv@gmail.com>
# URL: http://github.com/SiCKRAGETV/SickRage/
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

import traceback

import sickrage
from core.blackandwhitelist import BlackAndWhiteList
from core.common import WANTED
from core.databases import main_db
from core.exceptions import CantRefreshShowException, \
    CantRemoveShowException, CantUpdateShowException, EpisodeDeletedException, \
    MultipleShowObjectsException, ShowDirectoryNotFoundException
from core.queues import GenericQueue, QueueItem, QueuePriorities
from core.scene_numbering import xem_refresh, get_xem_numbering_for_show
from core.trakt import TraktAPI
from core.tv.show import TVShow
from core.ui import notifications
from indexers.indexer_exceptions import indexer_attributenotfound, \
    indexer_error, indexer_exception


class srShowQueue(GenericQueue):
    def __init__(self, *args, **kwargs):
        super(srShowQueue, self).__init__()
        self.queue_name = "SHOWQUEUE"

    def run(self, force=False):
        super(srShowQueue, self).run(force)

    @property
    def loadingShowList(self):
        return self._getLoadingShowList()

    def _isInQueue(self, show, actions):
        if not show:
            return False

        return show.indexerid in [x.show.indexerid if x.show else 0 for x in self.queue if x.action_id in actions]

    def _isBeingSomethinged(self, show, actions):
        return not (not (self.currentItem is not None) or not (show == self.currentItem.show)) and \
               self.currentItem.action_id in actions

    def isInUpdateQueue(self, show):
        return self._isInQueue(show, (ShowQueueActions.UPDATE, ShowQueueActions.FORCEUPDATE))

    def isInRefreshQueue(self, show):
        return self._isInQueue(show, (ShowQueueActions.REFRESH,))

    def isInRenameQueue(self, show):
        return self._isInQueue(show, (ShowQueueActions.RENAME,))

    def isInSubtitleQueue(self, show):
        return self._isInQueue(show, (ShowQueueActions.SUBTITLE,))

    def isBeingAdded(self, show):
        return self._isBeingSomethinged(show, (ShowQueueActions.ADD,))

    def isBeingUpdated(self, show):
        return self._isBeingSomethinged(show, (ShowQueueActions.UPDATE, ShowQueueActions.FORCEUPDATE))

    def isBeingRefreshed(self, show):
        return self._isBeingSomethinged(show, (ShowQueueActions.REFRESH,))

    def isBeingRenamed(self, show):
        return self._isBeingSomethinged(show, (ShowQueueActions.RENAME,))

    def isBeingSubtitled(self, show):
        return self._isBeingSomethinged(show, (ShowQueueActions.SUBTITLE,))

    def _getLoadingShowList(self):
        return [x for x in self.queue + [self.currentItem] if not (not x or not x.isLoading)]

    def updateShow(self, show, force=False):

        if self.isBeingAdded(show):
            raise CantUpdateShowException(
                str(show.name) + " is still being added, wait until it is finished before you update.")

        if self.isBeingUpdated(show):
            raise CantUpdateShowException(
                str(
                    show.name) + " is already being updated by Post-processor or manually started, can't update again until it's done.")

        if self.isInUpdateQueue(show):
            raise CantUpdateShowException(
                str(
                    show.name) + " is in process of being updated by Post-processor or manually started, can't update again until it's done.")

        if force:
            return self.add_item(QueueItemForceUpdate(show))
        return self.add_item(QueueItemUpdate(show))

    def refreshShow(self, show, force=False):

        if self.isBeingRefreshed(show) and not force:
            raise CantRefreshShowException("This show is already being refreshed, not refreshing again.")

        if (self.isBeingUpdated(show) or self.isInUpdateQueue(show)) and not force:
            sickrage.srLogger.debug(
                "A refresh was attempted but there is already an update queued or in progress. Since updates do a refresh at the end anyway I'm skipping this request.")
            return

        sickrage.srLogger.debug("Queueing show refresh for " + show.name)
        return self.add_item(QueueItemRefresh(show, force=force))

    def renameShowEpisodes(self, show, force=False):
        return self.add_item(QueueItemRename(show))

    def downloadSubtitles(self, show, force=False):
        return self.add_item(QueueItemSubtitle(show))

    def addShow(self, indexer, indexer_id, showDir, default_status=None, quality=None, flatten_folders=None,
                lang=None, subtitles=None, anime=None, scene=None, paused=None, blacklist=None, whitelist=None,
                default_status_after=None, archive=None):

        if lang is None:
            lang = sickrage.srConfig.INDEXER_DEFAULT_LANGUAGE

        return self.add_item(QueueItemAdd(indexer, indexer_id, showDir, default_status, quality, flatten_folders, lang,
                                          subtitles, anime, scene, paused, blacklist, whitelist, default_status_after,
                                          archive))

    def removeShow(self, show, full=False):
        if self._isInQueue(show, (ShowQueueActions.REMOVE,)):
            raise CantRemoveShowException("This show is already queued to be removed")
        elif show is None:
            raise CantRemoveShowException

        # remove other queued actions for this show.
        for x in self.queue:
            if show.indexerid == x.show.indexerid and x != self.currentItem:
                self.queue.remove(x)

        return self.add_item(QueueItemRemove(show=show, full=full))


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


class ShowQueueItem(QueueItem):
    """
    Represents an item in the queue waiting to be executed

    Can be either:
    - show being added (may or may not be associated with a show object)
    - show being refreshed
    - show being updated
    - show being force updated
    - show being subtitled
    """

    def __init__(self, action_id, show):
        super(ShowQueueItem, self).__init__(ShowQueueActions.names[action_id], action_id)
        self.show = show

    def finish(self):
        self.show.flushEpisodes()
        super(ShowQueueItem, self).finish()

    def isInQueue(self):
        return self in sickrage.srCore.SHOWQUEUE.queue + [
            sickrage.srCore.SHOWQUEUE.currentItem]  # @UndefinedVariable

    def _getName(self):
        return str(self.show.indexerid)

    def _isLoading(self):
        return False

    show_name = property(_getName)
    isLoading = property(_isLoading)


class QueueItemAdd(ShowQueueItem):
    def __init__(self, indexer, indexer_id, showDir, default_status, quality, flatten_folders, lang, subtitles, anime,
                 scene, paused, blacklist, whitelist, default_status_after, archive):

        self.indexer = indexer
        self.indexer_id = indexer_id
        self.showDir = showDir
        self.default_status = default_status
        self.quality = quality
        self.flatten_folders = flatten_folders
        self.lang = lang
        self.subtitles = subtitles
        self.anime = anime
        self.scene = scene
        self.paused = paused
        self.blacklist = blacklist
        self.whitelist = whitelist
        self.default_status_after = default_status_after
        self.archive = archive

        self.show = None

        # this will initialize self.show to None
        ShowQueueItem.__init__(self, ShowQueueActions.ADD, self.show)

        # Process add show in priority
        self.priority = QueuePriorities.HIGH

    def _getName(self):
        """
        Returns the show name if there is a show object created, if not returns
        the dir that the show is being added to.
        """
        if self.show is None:
            return self.showDir
        return self.show.name

    show_name = property(_getName)

    def _isLoading(self):
        """
        Returns True if we've gotten far enough to have a show object, or False
        if we still only know the folder name.
        """
        if self.show is None:
            return True
        return False

    isLoading = property(_isLoading)

    def run(self):
        ShowQueueItem.run(self)

        sickrage.srLogger.info("Started adding show {}".format(self.showDir))

        index_name = sickrage.srCore.INDEXER_API(self.indexer).name

        # update internal name cache
        sickrage.srCore.NAMECACHE.buildNameCache()

        # make sure the Indexer IDs are valid
        try:

            lINDEXER_API_PARMS = sickrage.srCore.INDEXER_API(self.indexer).api_params.copy()
            if self.lang:
                lINDEXER_API_PARMS[b'language'] = self.lang

            sickrage.srLogger.info("{}: {}".format(index_name, repr(lINDEXER_API_PARMS)))

            t = sickrage.srCore.INDEXER_API(self.indexer).indexer(**lINDEXER_API_PARMS)
            s = t[self.indexer_id]

            # this usually only happens if they have an NFO in their show dir which gave us a Indexer ID that has no proper english version of the show
            if getattr(s, 'seriesname', None) is None:
                sickrage.srLogger.error(
                    "Show in {} has no name on {}, probably the wrong language used to search with".format(self.showDir,
                                                                                                           index_name))
                notifications.error("Unable to add show",
                                    "Show in {} has no name on {}, probably the wrong language. Delete .nfo and add manually in the correct language".format(
                                        self.showDir, index_name))
                return self._finishEarly()

            # if the show has no episodes/seasons
            if not s:
                sickrage.srLogger.error("Show " + str(s[b'seriesname']) + " is on " + str(
                    sickrage.srCore.INDEXER_API(self.indexer).name) + " but contains no season/episode data.")
                notifications.error("Unable to add show",
                                    "Show " + str(s[b'seriesname']) + " is on " + str(sickrage.srCore.INDEXER_API(
                                        self.indexer).name) + " but contains no season/episode data.")
                return self._finishEarly()
        except Exception as e:
            sickrage.srLogger.error(
                "{}: Error while loading information from indexer {}. Error: {}".format(self.indexer_id, index_name,
                                                                                        e.message))

            notifications.error(
                "Unable to add show",
                "Unable to look up the show in {} on {} using ID {}, not using the NFO. Delete .nfo and try adding manually again.".format(
                    self.showDir, index_name, self.indexer_id)
            )

            if sickrage.srConfig.USE_TRAKT:

                trakt_id = sickrage.srCore.INDEXER_API(self.indexer).config[b'trakt_id']
                trakt_api = TraktAPI(sickrage.srConfig.SSL_VERIFY, sickrage.srConfig.TRAKT_TIMEOUT)

                title = self.showDir.split("/")[-1]
                data = {
                    'shows': [
                        {
                            'title': title,
                            'ids': {}
                        }
                    ]
                }
                if trakt_id == 'tvdb_id':
                    data[b'shows'][0][b'ids'][b'tvdb'] = self.indexer_id
                else:
                    data[b'shows'][0][b'ids'][b'tvrage'] = self.indexer_id

                trakt_api.traktRequest("sync/watchlist/remove", data, method='POST')

            return self._finishEarly()

        try:
            self.show = TVShow(self.indexer, self.indexer_id, self.lang)
            self.show.loadFromIndexer()

            # set up initial values
            self.show.location = self.showDir
            self.show.subtitles = self.subtitles or sickrage.srConfig.SUBTITLES_DEFAULT
            self.show.quality = self.quality or sickrage.srConfig.QUALITY_DEFAULT
            self.show.flatten_folders = self.flatten_folders or sickrage.srConfig.FLATTEN_FOLDERS_DEFAULT
            self.show.anime = self.anime or sickrage.srConfig.ANIME_DEFAULT
            self.show.scene = self.scene or sickrage.srConfig.SCENE_DEFAULT
            self.show.archive_firstmatch = self.archive or sickrage.srConfig.ARCHIVE_DEFAULT
            self.show.paused = self.paused or False

            # set up default new/missing episode status
            sickrage.srLogger.info(
                "Setting all current episodes to the specified default status: " + str(self.default_status))
            self.show.default_ep_status = self.default_status

            if self.show.anime:
                self.show.release_groups = BlackAndWhiteList(self.show.indexerid)
                if self.blacklist:
                    self.show.release_groups.set_black_keywords(self.blacklist)
                if self.whitelist:
                    self.show.release_groups.set_white_keywords(self.whitelist)

                    # # be smartish about this
                    # if self.show.genre and "talk show" in self.show.genre.lower():
                    #     self.show.air_by_date = 1
                    # if self.show.genre and "documentary" in self.show.genre.lower():
                    #     self.show.air_by_date = 0
                    # if self.show.classification and "sports" in self.show.classification.lower():
                    #     self.show.sports = 1

        except indexer_exception as e:
            sickrage.srLogger.error(
                "Unable to add show due to an error with " + sickrage.srCore.INDEXER_API(
                    self.indexer).name + ": {}".format(e.message))
            if self.show:
                notifications.error(
                    "Unable to add " + str(self.show.name) + " due to an error with " + sickrage.srCore.INDEXER_API(
                        self.indexer).name + "")
            else:
                notifications.error(
                    "Unable to add show due to an error with " + sickrage.srCore.INDEXER_API(self.indexer).name + "")
            return self._finishEarly()

        except MultipleShowObjectsException:
            sickrage.srLogger.warning("The show in " + self.showDir + " is already in your show list, skipping")
            notifications.error('Show skipped', "The show in " + self.showDir + " is already in your show list")
            return self._finishEarly()

        except Exception as e:
            sickrage.srLogger.error("Error trying to add show: {}".format(e.message))
            sickrage.srLogger.debug(traceback.format_exc())
            raise self._finishEarly()

        sickrage.srLogger.debug("Retrieving show info from TMDb")
        try:
            self.show.loadTMDbInfo()
        except Exception as e:
            sickrage.srLogger.error("Error loading TMDb info: {}".format(e.message))
            try:
                sickrage.srLogger.debug("Attempting to retrieve show info from IMDb")
                self.show.loadIMDbInfo()
            except Exception as e:
                sickrage.srLogger.error("Error loading IMDb info: {}".format(e.message))

        # Load XEM data to DB for show
        xem_refresh(self.show.indexerid, self.show.indexer, force=True)

        # check if show has XEM mapping so we can determin if searches should go by scene numbering or indexer numbering.
        if not self.scene and get_xem_numbering_for_show(self.show.indexerid, self.show.indexer):
            self.show.scene = 1

        try:
            self.show.saveToDB()
        except Exception as e:
            sickrage.srLogger.error("Error saving the show to the database: {}".format(e.message))
            sickrage.srLogger.debug(traceback.format_exc())
            raise self._finishEarly()

        # add it to the show list
        sickrage.srCore.SHOWLIST.append(self.show)

        try:
            self.show.loadEpisodesFromIndexer()
        except Exception as e:
            sickrage.srLogger.error(
                "Error with " + sickrage.srCore.INDEXER_API(
                    self.show.indexer).name + ", not creating episode list: {}".format(e.message))
            sickrage.srLogger.debug(traceback.format_exc())

        try:
            self.show.loadEpisodesFromDir()
        except Exception as e:
            sickrage.srLogger.error("Error searching dir for episodes: {}".format(e.message))
            sickrage.srLogger.debug(traceback.format_exc())

        # if they set default ep status to WANTED then run the backlog to search for episodes
        if self.show.default_ep_status == WANTED:
            sickrage.srLogger.info("Launching backlog for this show since its episodes are WANTED")
            sickrage.srCore.BACKLOGSEARCHER.searchBacklog([self.show])

        self.show.writeMetadata()
        self.show.updateMetadata()
        self.show.populateCache()

        if sickrage.srConfig.USE_TRAKT:
            # if there are specific episodes that need to be added by trakt
            sickrage.srCore.TRAKTSEARCHER.manageNewShow(self.show)

            # add show to trakt.tv library
            if sickrage.srConfig.TRAKT_SYNC:
                sickrage.srCore.TRAKTSEARCHER.addShowToTraktLibrary(self.show)

            if sickrage.srConfig.TRAKT_SYNC_WATCHLIST:
                sickrage.srLogger.info("update watchlist")
                sickrage.srCore.NOTIFIERS.trakt_notifier.update_watchlist(show_obj=self.show)

        # After initial add, set to default_status_after.
        sickrage.srLogger.info(
            "Setting all future episodes to the specified default status: " + str(self.default_status_after))
        self.show.default_ep_status = self.default_status_after

        self.show.saveToDB()

        sickrage.srLogger.info("Finished adding show {}".format(self.showDir))

    def _finishEarly(self):
        if self.show is not None:
            sickrage.srCore.SHOWQUEUE.removeShow(self.show)


class QueueItemRefresh(ShowQueueItem):
    def __init__(self, show=None, force=False):
        ShowQueueItem.__init__(self, ShowQueueActions.REFRESH, show)

        # do refreshes first because they're quick
        self.priority = QueuePriorities.NORMAL

        # force refresh certain items
        self.force = force

    def run(self):
        ShowQueueItem.run(self)

        sickrage.srLogger.info("Performing refresh for show: {}".format(self.show.name))

        self.show.refreshDir()
        self.show.writeMetadata()
        if self.force:
            self.show.updateMetadata()
        self.show.populateCache()

        # Load XEM data to DB for show
        xem_refresh(self.show.indexerid, self.show.indexer)

        sickrage.srLogger.info("Finished refresh for show: {}".format(self.show.name))


class QueueItemRename(ShowQueueItem):
    def __init__(self, show=None):
        ShowQueueItem.__init__(self, ShowQueueActions.RENAME, show)

    def run(self):

        ShowQueueItem.run(self)

        sickrage.srLogger.info("Performing renames for show: {}".format(self.show.name))

        try:
            self.show.location
        except ShowDirectoryNotFoundException:
            sickrage.srLogger.warning(
                "Can't perform rename on " + self.show.name + " when the show dir is missing.")
            return

        ep_obj_rename_list = []

        ep_obj_list = self.show.getAllEpisodes(has_location=True)
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

        sickrage.srLogger.info("Finished renames for show: {}".format(self.show.name))


class QueueItemSubtitle(ShowQueueItem):
    def __init__(self, show=None):
        ShowQueueItem.__init__(self, ShowQueueActions.SUBTITLE, show)

    def run(self):
        ShowQueueItem.run(self)

        sickrage.srLogger.info("Started downloading subtitles for show: {}".format(self.show.name))
        self.show.downloadSubtitles()
        sickrage.srLogger.info("Finished downloading subtitles for show: {}".format(self.show.name))


class QueueItemUpdate(ShowQueueItem):
    def __init__(self, action_id=None, show=None):
        super(QueueItemUpdate, self).__init__(ShowQueueActions.UPDATE, show)
        self.force = False

    def run(self):
        ShowQueueItem.run(self)

        sickrage.srLogger.info("Performing updates for show: {}".format(self.show.name))

        sickrage.srLogger.debug(
            "Retrieving show info from " + sickrage.srCore.INDEXER_API(self.show.indexer).name + "")
        try:
            self.show.loadFromIndexer(cache=not self.force)
        except indexer_error as e:
            sickrage.srLogger.warning(
                "Unable to contact " + sickrage.srCore.INDEXER_API(self.show.indexer).name + ", aborting: {}".format(
                    e))
            return
        except indexer_attributenotfound as e:
            sickrage.srLogger.error("Data retrieved from " + sickrage.srCore.INDEXER_API(
                self.show.indexer).name + " was incomplete, aborting: {}".format(e.message))
            return

        sickrage.srLogger.debug("Retrieving show info from TMDb")
        try:
            self.show.loadTMDbInfo()
        except Exception as e:
            sickrage.srLogger.error("Error loading TMDb info: {}".format(e.message))
            sickrage.srLogger.debug(traceback.format_exc())
            try:
                sickrage.srLogger.debug("Attempting to retrieve show info from IMDb")
                self.show.loadIMDbInfo()
            except Exception as e:
                sickrage.srLogger.error("Error loading IMDb info: {}".format(e.message))
                sickrage.srLogger.debug(traceback.format_exc())

        # have to save show before reading episodes from db
        try:
            self.show.saveToDB()
        except Exception as e:
            sickrage.srLogger.error("Error saving show info to the database: {}".format(e.message))
            sickrage.srLogger.debug(traceback.format_exc())

        # get episode list from DB
        DBEpList = self.show.loadEpisodesFromDB()

        # get episode list from TVDB
        try:
            IndexerEpList = self.show.loadEpisodesFromIndexer(cache=not self.force)
        except indexer_exception as e:
            sickrage.srLogger.error("Unable to get info from " + sickrage.srCore.INDEXER_API(
                self.show.indexer).name + ", the show info will not be refreshed: {}".format(e.message))
            IndexerEpList = None

        if IndexerEpList is None:
            sickrage.srLogger.error("No data returned from " + sickrage.srCore.INDEXER_API(
                self.show.indexer).name + ", unable to update this show")
        else:
            # for each ep we found on the Indexer delete it from the DB list
            sql_l = []
            for curSeason in IndexerEpList:
                for curEpisode in IndexerEpList[curSeason]:
                    sql_q = self.show.getEpisode(curSeason, curEpisode).saveToDB(False)
                    if sql_q:
                        sql_l.append(sql_q)
                        del sql_q  # cleanup

                    try:
                        del DBEpList[curSeason][curEpisode]
                    except:
                        pass

            if len(sql_l) > 0:
                main_db.MainDB().mass_upsert(sql_l)
                del sql_l  # cleanup

            # remaining episodes in the DB list are not on the indexer, just delete them from the DB
            for curSeason in DBEpList:
                for curEpisode in DBEpList[curSeason]:
                    sickrage.srLogger.info("Permanently deleting episode " + str(curSeason) + "x" + str(
                        curEpisode) + " from the database")

                    try:
                        self.show.getEpisode(curSeason, curEpisode).deleteEpisode()
                    except EpisodeDeletedException:
                        pass

        # cleanup
        del DBEpList
        del IndexerEpList

        sickrage.srLogger.info("Finished updates for show: {}".format(self.show.name))

        # refresh show
        sickrage.srCore.SHOWQUEUE.refreshShow(self.show, self.force)


class QueueItemForceUpdate(QueueItemUpdate):
    def __init__(self, show=None):
        super(QueueItemForceUpdate, self).__init__(ShowQueueActions.FORCEUPDATE, show)
        self.force = True


class QueueItemRemove(ShowQueueItem):
    def __init__(self, show=None, full=False):
        super(QueueItemRemove, self).__init__(ShowQueueActions.REMOVE, show)

        # lets make sure this happens before any other high priority actions
        self.priority = QueuePriorities.HIGH + QueuePriorities.HIGH
        self.full = full

    def run(self):
        ShowQueueItem.run(self)

        sickrage.srLogger.info("Removing show: {}".format(self.show.name))

        self.show.deleteShow(full=self.full)

        if sickrage.srConfig.USE_TRAKT:
            try:
                sickrage.srCore.TRAKTSEARCHER.removeShowFromTraktLibrary(self.show)
            except Exception as e:
                sickrage.srLogger.warning("Unable to delete show from Trakt: %s. Error: %s" % (self.show.name, e))

        sickrage.srLogger.info("Finished removing show: {}".format(self.show.name))
