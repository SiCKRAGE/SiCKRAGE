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


import re
from datetime import datetime
from datetime import timedelta
from urllib.parse import unquote

import sickrage
from sickrage.core.common import Quality, SNATCHED, SUBTITLED, FAILED, WANTED
from sickrage.core.databases.main import MainDB
from sickrage.core.exceptions import EpisodeNotFoundException


class History:
    date_format = '%Y%m%d%H%M%S'

    def clear(self):
        """
        Clear all the history
        """
        MainDB().delete(MainDB.History)

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

        for show in sickrage.app.showlist:
            if limit == 0:
                if len(actions) > 0:
                    dbData = MainDB.History.query.filter_by(showid=show.indexerid).filter(
                        MainDB.History.action.in_(actions)).order_by(MainDB.History.date.desc())
                else:
                    dbData = MainDB.History.query.filter_by(showid=show.indexerid).order_by(MainDB.History.date.desc())
            else:
                if len(actions) > 0:
                    dbData = MainDB.History.query.filter_by(showid=show.indexerid).filter(
                        MainDB.History.action.in_(actions)).order_by(MainDB.History.date.desc()).limit(limit)
                else:
                    dbData = MainDB.History.query.filter_by(showid=show.indexerid).order_by(
                        MainDB.History.date.desc()).limit(
                        limit)

            for result in dbData:
                data.append({
                    'action': result.action,
                    'date': int(result.date),
                    'episode': result.episode,
                    'provider': result.provider,
                    'quality': result.quality,
                    'resource': result.resource,
                    'season': result.season,
                    'show_id': result.showid,
                    'show_name': show.name
                })

        return data

    def trim(self):
        """
        Remove all elements older than 30 days from the history
        """

        date = (datetime.today() - timedelta(days=30)).strftime(History.date_format)
        MainDB().delete(MainDB.History, MainDB.History.data < date)

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

        MainDB().add(MainDB.History(**{
            'action': action,
            'date': logDate,
            'showid': showid,
            'season': season,
            'episode': episode,
            'quality': quality,
            'resource': resource,
            'provider': provider,
            'version': version
        }))

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

            action = Quality.composite_status(SNATCHED, searchResult.quality)

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

        status, quality = Quality.split_composite_status(status)
        action = Quality.composite_status(SUBTITLED, quality)

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
        status, quality = Quality.split_composite_status(epObj.status)
        action = Quality.composite_status(FAILED, quality)

        History._logHistoryItem(action, showid, season, epNum, quality, release, provider)


class FailedHistory(object):
    @staticmethod
    def prepareFailedName(release):
        """Standardizes release name for failed DB"""

        fixed = unquote(release)
        if fixed.endswith(".nzb"):
            fixed = fixed.rpartition(".")[0]

        fixed = re.sub(r"[\.\-\+\ ]", "_", fixed)
        fixed = fixed

        return fixed

    @staticmethod
    def logFailed(release):
        log_str = ""
        size = -1
        provider = ""

        release = FailedHistory.prepareFailedName(release)

        dbData = MainDB.FailedSnatchHistory.query.filter_by(release=release).all()

        if len(dbData) == 0:
            sickrage.app.log.warning("{}, Release not found in snatch history.".format(release))
        elif len(dbData) > 1:
            sickrage.app.log.warning("Multiple logged snatches found for release")

            if len(set(x.size for x in dbData)) == 1:
                sickrage.app.log.warning("However, they're all the same size. Continuing with found size.")
                size = dbData[0].size
            else:
                sickrage.app.log.warning("They also vary in size. Deleting the logged snatches and recording this "
                                         "release with no size/provider")
                [FailedHistory.deleteLoggedSnatch(result.release, result.size, result.provider) for result in dbData]

            if len(set(x.provider for x in dbData)) == 1:
                sickrage.app.log.info("They're also from the same provider. Using it as well.")
                provider = dbData[0].provider
        else:
            size = dbData[0]["size"]
            provider = dbData[0]["provider"]

        if not FailedHistory.hasFailed(release, size, provider):
            MainDB().add(MainDB.FailedSnatch(**{
                'release': release,
                'size': size,
                'provider': provider
            }))

        FailedHistory.deleteLoggedSnatch(release, size, provider)

        return log_str

    @staticmethod
    def logSuccess(release):
        release = FailedHistory.prepareFailedName(release)
        MainDB().delete(MainDB.FailedSnatchHistory, release=release)

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
        return MainDB.FailedSnatch.query.filter_by(release=release, size=size, provider=provider).count() > 0

    @staticmethod
    def revertFailedEpisode(epObj):
        """Restore the episodes of a failed download to their original state"""
        history_eps = dict(
            [(res.episode, res) for res in
             MainDB.FailedSnatchHistory.query.filter_by(showid=epObj.show.indexerid, season=epObj.season)]
        )

        try:
            sickrage.app.log.info("Reverting episode (%s, %s): %s" % (epObj.season, epObj.episode, epObj.name))
            with epObj.lock:
                if epObj.episode in history_eps:
                    sickrage.app.log.info("Found in history")
                    epObj.status = history_eps[epObj.episode].old_status
                else:
                    sickrage.app.log.debug("WARNING: Episode not found in history. Setting it back to WANTED")
                    epObj.status = WANTED
                    epObj.save_to_db()

        except EpisodeNotFoundException as e:
            sickrage.app.log.warning("Unable to create episode, please set its status manually: {}".format(e))

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
                quality = Quality.split_composite_status(epObj.status)[1]
                epObj.status = Quality.composite_status(FAILED, quality)
                epObj.save_to_db()

        except EpisodeNotFoundException as e:
            sickrage.app.log.warning(
                "Unable to get episode, please set its status manually: {}".format(e))

        return log_str

    @staticmethod
    def logSnatch(searchResult):
        """
        Logs a successful snatch

        :param searchResult: Search result that was successful
        """
        logDate = datetime.today().strftime(History.date_format)
        release = FailedHistory.prepareFailedName(searchResult.name)

        provider = "unknown"
        providerClass = searchResult.provider
        if providerClass is not None:
            provider = providerClass.name

        show_obj = searchResult.episodes[0].show

        for episode in searchResult.episodes:
            MainDB().add(MainDB.FailedSnatchHistory(**{
                'date': logDate,
                'size': searchResult.size,
                'release': release,
                'provider': provider,
                'showid': show_obj.indexerid,
                'season': episode.season,
                'episode': episode.episode,
                'old_status': episode.status
            }))

    @staticmethod
    def deleteLoggedSnatch(release, size, provider):
        """
        Remove a snatch from history

        :param release: release to delete
        :param size: Size of release
        :param provider: Provider to delete it from
        """
        release = FailedHistory.prepareFailedName(release)
        MainDB().delete(MainDB.FailedSnatchHistory, release=release, size=size, provider=provider)

    @staticmethod
    def trimHistory():
        """Trims history table to 1 month of history from today"""
        date = str((datetime.today() - timedelta(days=30)).strftime(History.date_format))
        MainDB().delete(MainDB.FailedSnatchHistory, MainDB.FailedSnatchHistory.date < date)

    @staticmethod
    def findFailedRelease(epObj):
        """
        Find releases in history by show ID and season.
        Return None for release if multiple found or no release found.
        """

        release = None
        provider = None

        # Clear old snatches for this release if any exist
        MainDB().delete(MainDB.FailedSnatchHistory, MainDB.FailedSnatchHistory.date < MainDB.FailedSnatchHistory.date,
                        showid=epObj.show.indexerid, season=epObj.season, episode=epObj.episode)

        # Search for release in snatch history
        for dbData in MainDB.FailedSnatchHistory.query(showid=epObj.show.indexerid, season=epObj.season,
                                                       episode=epObj.episode):
            release = str(dbData.release)
            provider = str(dbData.provider)
            date = dbData.date

            # Clear any incomplete snatch records for this release if any exist
            MainDB().delete(MainDB.FailedSnatchHistory, MainDB.FailedSnatchHistory.date != date, release=release)

            # Found a previously failed release
            sickrage.app.log.debug(
                "Failed release found for season (%s): (%s)" % (epObj.season, dbData["release"]))

            return release, provider

        # Release was not found
        sickrage.app.log.debug(
            "No releases found for season (%s) of (%s)" % (epObj.season, epObj.show.indexerid))

        return release, provider
