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

import re
import urllib
from datetime import datetime
from datetime import timedelta

import sickrage
from sickrage.core.common import Quality, SNATCHED, SUBTITLED, FAILED, WANTED
from sickrage.core.exceptions import EpisodeNotFoundException


class History:
    date_format = '%Y%m%d%H%M%S'

    def clear(self):
        """
        Clear all the history
        """
        [sickrage.srCore.mainDB.db.delete(x['doc']) for x in sickrage.srCore.mainDB.db.all('history', with_doc=True)]

    def get(self, limit=100, action=None):
        """
        :param limit: The maximum number of elements to return
        :param action: The type of action to filter in the history. Either 'downloaded' or 'snatched'. Anything else or
                        no value will return everything (up to ``limit``)
        :return: The last ``limit`` elements of type ``action`` in the history
        """

        data = []

        action = action.lower() if isinstance(action, str) else ''
        limit = int(limit)

        if action == 'downloaded':
            actions = Quality.DOWNLOADED
        elif action == 'snatched':
            actions = Quality.SNATCHED
        else:
            actions = []

        for tv_show in [x['doc'] for x in sickrage.srCore.mainDB.db.all('tv_shows', with_doc=True)]:
            if limit == 0:
                if len(actions) > 0:
                    dbData = [x['doc'] for x in
                              sickrage.srCore.mainDB.db.get_many('history', tv_show['indexer_id'], with_doc=True)
                              if x['doc']['action'] in actions]
                else:
                    dbData = [x['doc'] for x in
                              sickrage.srCore.mainDB.db.get_many('history', tv_show['indexer_id'], with_doc=True)]
            else:
                if len(actions) > 0:
                    dbData = [x['doc'] for x in
                              sickrage.srCore.mainDB.db.get_many('history', tv_show['indexer_id'], limit, with_doc=True)
                              if x['doc']['action'] in actions]
                else:
                    dbData = [x['doc'] for x in
                              sickrage.srCore.mainDB.db.get_many('history', tv_show['indexer_id'], limit,
                                                                 with_doc=True)]

            for result in dbData:
                data.append({
                    'action': result['action'],
                    'date': result['date'],
                    'episode': result['episode'],
                    'provider': result['provider'],
                    'quality': result['quality'],
                    'resource': result['resource'],
                    'season': result['season'],
                    'show_id': result['showid'],
                    'show_name': tv_show['show_name']
                })

        return sorted(data, key=lambda d: d['date'], reverse=True)

    def trim(self):
        """
        Remove all elements older than 30 days from the history
        """

        date = (datetime.today() - timedelta(days=30)).strftime(History.date_format)
        for dbData in [x['doc'] for x in sickrage.srCore.mainDB.db.all('history', with_doc=True)
                       if x['doc']['date'] < date]: sickrage.srCore.mainDB.db.delete(dbData)

    @staticmethod
    def _logHistoryItem(action, showid, season, episode, quality, resource, provider, version=-1):
        """
        Insert a history item in DB

        :param action: action taken (snatch, download, etc)
        :param showid: showid this entry is about
        :param season: show season
        :param episode: show episode
        :param quality: media quality
        :param resource: resource used
        :param provider: provider used
        :param version: tracked version of file (defaults to -1)
        """
        logDate = datetime.today().strftime(History.date_format)
        resource = resource

        sickrage.srCore.mainDB.db.insert({
            '_t': 'history',
            'action': action,
            'date': logDate,
            'showid': showid,
            'season': season,
            'episode': episode,
            'quality': quality,
            'resource': resource,
            'provider': provider,
            'version': version
        })

    @staticmethod
    def logSnatch(searchResult):
        """
        Log history of snatch

        :param searchResult: search result object
        """
        for curEpObj in searchResult.episodes:

            showid = int(curEpObj.show.indexerid)
            season = int(curEpObj.season)
            episode = int(curEpObj.episode)
            quality = searchResult.quality
            version = searchResult.version

            providerClass = searchResult.provider
            if providerClass is not None:
                provider = providerClass.name
            else:
                provider = "unknown"

            action = Quality.compositeStatus(SNATCHED, searchResult.quality)

            resource = searchResult.name

            History._logHistoryItem(action, showid, season, episode, quality, resource, provider, version)

    @staticmethod
    def logDownload(episode, filename, new_ep_quality, release_group=None, version=-1):
        """
        Log history of download

        :param episode: episode of show
        :param filename: file on disk where the download is
        :param new_ep_quality: Quality of download
        :param release_group: Release group
        :param version: Version of file (defaults to -1)
        """
        showid = int(episode.show.indexerid)
        season = int(episode.season)
        epNum = int(episode.episode)

        quality = new_ep_quality

        # store the release group as the provider if possible
        if release_group:
            provider = release_group
        else:
            provider = -1

        action = episode.status

        History._logHistoryItem(action, showid, season, epNum, quality, filename, provider, version)

    @staticmethod
    def logSubtitle(showid, season, episode, status, subtitleResult):
        """
        Log download of subtitle

        :param showid: Showid of download
        :param season: Show season
        :param episode: Show episode
        :param status: Status of download
        :param subtitleResult: Result object
        """
        resource = subtitleResult.language.opensubtitles
        provider = subtitleResult.provider_name

        status, quality = Quality.splitCompositeStatus(status)
        action = Quality.compositeStatus(SUBTITLED, quality)

        History._logHistoryItem(action, showid, season, episode, quality, resource, provider)

    @staticmethod
    def logFailed(epObj, release, provider=None):
        """
        Log a failed download

        :param epObj: Episode object
        :param release: Release group
        :param provider: Provider used for snatch
        """
        showid = int(epObj.show.indexerid)
        season = int(epObj.season)
        epNum = int(epObj.episode)
        status, quality = Quality.splitCompositeStatus(epObj.status)
        action = Quality.compositeStatus(FAILED, quality)

        History._logHistoryItem(action, showid, season, epNum, quality, release, provider)


class FailedHistory(object):
    @staticmethod
    def prepareFailedName(release):
        """Standardizes release name for failed DB"""

        fixed = urllib.unquote(release)
        if fixed.endswith(".nzb"):
            fixed = fixed.rpartition(".")[0]

        fixed = re.sub("[\.\-\+\ ]", "_", fixed)
        fixed = fixed

        return fixed

    @staticmethod
    def logFailed(release):
        log_str = ""
        size = -1
        provider = ""

        release = FailedHistory.prepareFailedName(release)

        dbData = [x['doc'] for x in sickrage.srCore.failedDB.db.all('history', with_doc=True) if
                  x['doc']['release'] == release]

        if len(dbData) == 0:
            sickrage.srCore.srLogger.warning("{}, Release not found in snatch history.".format(release))
        elif len(dbData) > 1:
            sickrage.srCore.srLogger.warning("Multiple logged snatches found for release")
            sizes = len(set(x["size"] for x in dbData))
            providers = len(set(x["provider"] for x in dbData))
            if sizes == 1:
                sickrage.srCore.srLogger.warning("However, they're all the same size. Continuing with found size.")
                size = dbData[0]["size"]
            else:
                sickrage.srCore.srLogger.warning(
                    "They also vary in size. Deleting the logged snatches and recording this release with no size/provider")
                for result in dbData:
                    FailedHistory.deleteLoggedSnatch(result["release"], result["size"], result["provider"])

            if providers == 1:
                sickrage.srCore.srLogger.info("They're also from the same provider. Using it as well.")
                provider = dbData[0]["provider"]
        else:
            size = dbData[0]["size"]
            provider = dbData[0]["provider"]

        if not FailedHistory.hasFailed(release, size, provider):
            sickrage.srCore.failedDB.db.insert({
                '_t': 'failed',
                'release': release,
                'size': size,
                'provider': provider
            })

        FailedHistory.deleteLoggedSnatch(release, size, provider)

        return log_str

    @staticmethod
    def logSuccess(release):
        release = FailedHistory.prepareFailedName(release)
        for dbData in [x['doc'] for x in sickrage.srCore.failedDB.db.all('history', with_doc=True)
                       if x['doc']['release'] == release]: sickrage.srCore.failedDB.db.delete(dbData)

    @staticmethod
    def hasFailed(release, size, provider="%"):
        """
        Returns True if a release has previously failed.

        If provider is given, return True only if the release is found
        with that specific provider. Otherwise, return True if the release
        is found with any provider.

        :param release: Release name to record failure
        :param size: Size of release
        :param provider: Specific provider to search (defaults to all providers)
        :return: True if a release has previously failed.
        """

        release = FailedHistory.prepareFailedName(release)
        dbData = [x['doc'] for x in sickrage.srCore.failedDB.db.get_many('failed', release, with_doc=True)
                  if x['doc']['size'] == size
                  and x['doc']['provider'] == provider]

        return len(dbData) > 0

    @staticmethod
    def revertFailedEpisode(epObj):
        """Restore the episodes of a failed download to their original state"""
        dbData = [x['doc'] for x in sickrage.srCore.failedDB.db.all('history', with_doc=True)
                  if x['doc']['showid'] == epObj.show.indexerid
                  and x['doc']['season'] == epObj.season]

        history_eps = dict([(res["episode"], res) for res in dbData])

        try:
            sickrage.srCore.srLogger.info("Reverting episode (%s, %s): %s" % (epObj.season, epObj.episode, epObj.name))
            with epObj.lock:
                if epObj.episode in history_eps:
                    sickrage.srCore.srLogger.info("Found in history")
                    epObj.status = history_eps[epObj.episode]['old_status']
                else:
                    sickrage.srCore.srLogger.warning("WARNING: Episode not found in history. Setting it back to WANTED")
                    epObj.status = WANTED
                    epObj.saveToDB()

        except EpisodeNotFoundException as e:
            sickrage.srCore.srLogger.warning(
                "Unable to create episode, please set its status manually: {}".format(e.message))

    @staticmethod
    def markFailed(epObj):
        """
        Mark an episode as failed

        :param epObj: Episode object to mark as failed
        :return: empty string
        """
        log_str = ""

        try:
            with epObj.lock:
                quality = Quality.splitCompositeStatus(epObj.status)[1]
                epObj.status = Quality.compositeStatus(FAILED, quality)
                epObj.saveToDB()

        except EpisodeNotFoundException as e:
            sickrage.srCore.srLogger.warning(
                "Unable to get episode, please set its status manually: {}".format(e.message))

        return log_str

    @staticmethod
    def logSnatch(searchResult):
        """
        Logs a successful snatch

        :param searchResult: Search result that was successful
        """
        logDate = datetime.today().strftime(History.date_format)
        release = FailedHistory.prepareFailedName(searchResult.name)

        providerClass = searchResult.provider
        if providerClass is not None:
            provider = providerClass.name
        else:
            provider = "unknown"

        show_obj = searchResult.episodes[0].show

        for episode in searchResult.episodes:
            sickrage.srCore.failedDB.db.insert({
                '_t': 'history',
                'date': logDate,
                'size': searchResult.size,
                'release': release,
                'provider': provider,
                'showid': show_obj.indexerid,
                'season': episode.season,
                'episode': episode.episode,
                'old_status': episode.status
            })

    @staticmethod
    def deleteLoggedSnatch(release, size, provider):
        """
        Remove a snatch from history

        :param release: release to delete
        :param size: Size of release
        :param provider: Provider to delete it from
        """
        release = FailedHistory.prepareFailedName(release)
        for dbData in [x['doc'] for x in sickrage.srCore.failedDB.db.all('history', with_doc=True)
                       if x['doc']['release'] == release
                       and x['doc']['size'] == size
                       and x['doc']['provider'] == provider]: sickrage.srCore.failedDB.db.delete(dbData)

    @staticmethod
    def trimHistory():
        """Trims history table to 1 month of history from today"""
        date = str((datetime.today() - timedelta(days=30)).strftime(History.date_format))
        for dbData in [x['doc'] for x in sickrage.srCore.failedDB.db.all('history', with_doc=True) if
                       x['doc']['date'] < date]:
            sickrage.srCore.failedDB.db.delete(dbData)

    @staticmethod
    def findFailedRelease(epObj):
        """
        Find releases in history by show ID and season.
        Return None for release if multiple found or no release found.
        """

        release = None
        provider = None

        # Clear old snatches for this release if any exist
        dbData = sorted(
            [x['doc'] for x in sickrage.srCore.failedDB.db.get_many('history', epObj.show.indexerid, with_doc=True)
             if x['doc']['season'] == epObj.season
             and x['doc']['episode'] == epObj.episode], key=lambda d: d['date'])

        [sickrage.srCore.failedDB.db.delete(x) for x in dbData[1::]]

        # Search for release in snatch history
        for dbData in [x['doc'] for x in
                       sickrage.srCore.failedDB.db.get_many('history', epObj.show.indexerid, with_doc=True)
                       if x['doc']['season'] == epObj.season
                       and x['doc']['episode'] == epObj.episode]:

            release = str(dbData["release"])
            provider = str(dbData["provider"])
            date = dbData["date"]

            # Clear any incomplete snatch records for this release if any exist
            for x in [x['doc'] for x in sickrage.srCore.failedDB.db.all('history', with_doc=True)]:
                if x['release'] == release and x['date'] != date: sickrage.srCore.failedDB.db.delete(x)

            # Found a previously failed release
            sickrage.srCore.srLogger.debug(
                "Failed release found for season (%s): (%s)" % (epObj.season, dbData["release"]))

            return release, provider

        # Release was not found
        sickrage.srCore.srLogger.debug(
            "No releases found for season (%s) of (%s)" % (epObj.season, epObj.show.indexerid))

        return release, provider
