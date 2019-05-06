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
from sickrage.core.tv.episode.helpers import find_episode
from sickrage.core.tv.show.helpers import get_show_list
from sickrage.core.common import Quality, SNATCHED, SUBTITLED, FAILED, WANTED
from sickrage.core.databases.main import MainDB
from sickrage.core.exceptions import EpisodeNotFoundException


class History:
    date_format = '%Y%m%d%H%M%S'

    def clear(self):
        """
        Clear all the history
        """
        sickrage.app.main_db.delete(MainDB.History)

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

        for show in get_show_list():
            if limit == 0:
                if len(actions) > 0:
                    dbData = sickrage.app.main_db.session().query(MainDB.History).filter_by(showid=show.indexer_id).filter(
                        MainDB.History.action.in_(actions)).order_by(MainDB.History.date.desc())
                else:
                    dbData = sickrage.app.main_db.session().query(MainDB.History).filter_by(showid=show.indexer_id).order_by(MainDB.History.date.desc())
            else:
                if len(actions) > 0:
                    dbData = sickrage.app.main_db.session().query(MainDB.History).filter_by(showid=show.indexer_id).filter(
                        MainDB.History.action.in_(actions)).order_by(MainDB.History.date.desc()).limit(limit)
                else:
                    dbData = sickrage.app.main_db.session().query(MainDB.History).filter_by(showid=show.indexer_id).order_by(
                        MainDB.History.date.desc()).limit(limit)

            for result in dbData:
                data.append({
                    'action': result.action,
                    'date': int(result.date),
                    'provider': result.provider,
                    'quality': result.quality,
                    'resource': result.resource,
                    'episode_id': result.episode_id,
                    'show_id': result.showid,
                    'show_name': show.name
                })

        return data

    def trim(self):
        """
        Remove all elements older than 30 days from the history
        """

        date = (datetime.today() - timedelta(days=30)).strftime(History.date_format)
        sickrage.app.main_db.delete(MainDB.History, MainDB.History.date < date)

    @staticmethod
    def _log_history_item(action, showid, episode_id, quality, resource, provider, version=-1):
        """
        Insert a history item in DB

        :param action: action taken (snatch, download, etc)
        :param showid: showid this entry is about
        :param episode_id: show episode ID
        :param quality: media quality
        :param resource: resource used
        :param provider: provider used
        :param version: tracked version of file (defaults to -1)
        """
        logDate = datetime.today().strftime(History.date_format)
        resource = resource

        sickrage.app.main_db.add(MainDB.History(**{
            'action': action,
            'date': logDate,
            'showid': showid,
            'episode_id': episode_id,
            'quality': quality,
            'resource': resource,
            'provider': provider,
            'version': version
        }))

    @staticmethod
    def log_snatch(search_result):
        """
        Log history of snatch

        :param search_result: search result object
        """
        for episode_id in search_result.episode_ids:
            quality = search_result.quality
            version = search_result.version

            provider = search_result.provider.name if search_result.provider else "unknown"

            action = Quality.composite_status(SNATCHED, search_result.quality)

            resource = search_result.name

            History._log_history_item(action, search_result.show_id, episode_id, quality, resource, provider, version)

    @staticmethod
    def log_download(show_id, episode_id, filename, new_ep_quality, release_group=None, version=-1):
        """
        Log history of download

        :param episode: episode of show
        :param filename: file on disk where the download is
        :param new_ep_quality: Quality of download
        :param release_group: Release group
        :param version: Version of file (defaults to -1)
        """

        quality = new_ep_quality
        provider = release_group or -1

        action = find_episode(show_id, episode_id).status

        History._log_history_item(action, show_id, episode_id, quality, filename, provider, version)

    @staticmethod
    def log_subtitle(show_id, episode_id, status, subtitleResult):
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

        History._log_history_item(action, show_id, episode_id, quality, resource, provider)

    @staticmethod
    def log_failed(show_id, episode_id, release, provider=None):
        """
        Log a failed download

        :param epObj: Episode object
        :param release: Release group
        :param provider: Provider used for snatch
        """
        status, quality = Quality.split_composite_status(find_episode(show_id, episode_id).status)
        action = Quality.composite_status(FAILED, quality)

        History._log_history_item(action, show_id, episode_id, quality, release, provider)


class FailedHistory(object):
    @staticmethod
    def prepare_failed_name(release):
        """Standardizes release name for failed DB"""

        fixed = unquote(release)
        if fixed.endswith(".nzb"):
            fixed = fixed.rpartition(".")[0]

        fixed = re.sub(r"[\.\-\+\ ]", "_", fixed)
        fixed = fixed

        return fixed

    @staticmethod
    def log_failed(release):
        log_str = ""
        size = -1
        provider = ""

        release = FailedHistory.prepare_failed_name(release)

        dbData = sickrage.app.main_db.session().query(MainDB.FailedSnatchHistory).filter_by(release=release).all()

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
                [FailedHistory.delete_logged_snatch(result.release, result.size, result.provider) for result in dbData]

            if len(set(x.provider for x in dbData)) == 1:
                sickrage.app.log.info("They're also from the same provider. Using it as well.")
                provider = dbData[0].provider
        else:
            size = dbData[0].size
            provider = dbData[0].provider

        if not FailedHistory.has_failed(release, size, provider):
            sickrage.app.main_db.add(MainDB.FailedSnatch(**{
                'release': release,
                'size': size,
                'provider': provider
            }))

        FailedHistory.delete_logged_snatch(release, size, provider)

        return log_str

    @staticmethod
    def log_success(release):
        release = FailedHistory.prepare_failed_name(release)
        sickrage.app.main_db.delete(MainDB.FailedSnatchHistory, release=release)

    @staticmethod
    def has_failed(release, size, provider="%"):
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

        release = FailedHistory.prepare_failed_name(release)
        return sickrage.app.main_db.session().query(MainDB.FailedSnatch).filter_by(release=release, size=size, provider=provider).count() > 0

    @staticmethod
    def revert_failed_episode(show_id, episode_id):
        """Restore the episodes of a failed download to their original state"""
        history_eps = dict(
            (x.episode, x) for x in sickrage.app.main_db.session().query(MainDB.FailedSnatchHistory).filter_by(showid=show_id, episode_id=episode_id))

        episode_obj = find_episode(show_id, episode_id)

        try:
            sickrage.app.log.info(
                "Reverting episode (%s, %s): %s" % (episode_obj.season, episode_obj.episode, episode_obj.name))
            if episode_obj.episode in history_eps:
                sickrage.app.log.info("Found in history")
                episode_obj.status = history_eps[episode_obj.episode].old_status
            else:
                sickrage.app.log.debug("WARNING: Episode not found in history. Setting it back to WANTED")
                episode_obj.status = WANTED

        except EpisodeNotFoundException as e:
            sickrage.app.log.warning("Unable to create episode, please set its status manually: {}".format(e))

    @staticmethod
    def mark_failed(epObj):
        """
        Mark an episode as failed

        :param epObj: Episode object to mark as failed
        :return: empty string
        """
        log_str = ""

        try:
            quality = Quality.split_composite_status(epObj.status)[1]
            epObj.status = Quality.composite_status(FAILED, quality)
        except EpisodeNotFoundException as e:
            sickrage.app.log.warning(
                "Unable to get episode, please set its status manually: {}".format(e))

        return log_str

    @staticmethod
    def log_snatch(search_result):
        """
        Logs a successful snatch

        :param search_result: Search result that was successful
        """
        logDate = datetime.today().strftime(History.date_format)
        release = FailedHistory.prepare_failed_name(search_result.name)
        provider = search_result.provider.name if search_result.provider else "unknown"

        for episode_id in search_result.episode_ids:
            sickrage.app.main_db.add(MainDB.FailedSnatchHistory(**{
                'date': logDate,
                'size': search_result.size,
                'release': release,
                'provider': provider,
                'showid': search_result.show_id,
                'episode_id': episode_id,
                'old_status': find_episode(search_result.show_id, episode_id).status
            }))

    @staticmethod
    def delete_logged_snatch(release, size, provider):
        """
        Remove a snatch from history

        :param release: release to delete
        :param size: Size of release
        :param provider: Provider to delete it from
        """
        release = FailedHistory.prepare_failed_name(release)
        sickrage.app.main_db.delete(MainDB.FailedSnatchHistory, release=release, size=size, provider=provider)

    @staticmethod
    def trim_history():
        """Trims history table to 1 month of history from today"""
        date = str((datetime.today() - timedelta(days=30)).strftime(History.date_format))
        sickrage.app.main_db.delete(MainDB.FailedSnatchHistory, MainDB.FailedSnatchHistory.date < date)

    @staticmethod
    def find_failed_release(show_id, episode_id):
        """
        Find releases in history by show ID and season.
        Return None for release if multiple found or no release found.
        """

        release = None
        provider = None

        # Clear old snatches for this release if any exist
        sickrage.app.main_db.delete(MainDB.FailedSnatchHistory,
                                    MainDB.FailedSnatchHistory.date < MainDB.FailedSnatchHistory.date,
                                    showid=show_id, episode_id=episode_id)

        # Search for release in snatch history
        episode_obj = find_episode(show_id, episode_id)
        for dbData in sickrage.app.main_db.session().query(MainDB.FailedSnatchHistory).filter_by(showid=show_id, episode_id=episode_id):
            release = str(dbData.release)
            provider = str(dbData.provider)
            date = dbData.date

            # Clear any incomplete snatch records for this release if any exist
            sickrage.app.main_db.delete(MainDB.FailedSnatchHistory, MainDB.FailedSnatchHistory.date != date,
                                        release=release)

            # Found a previously failed release
            sickrage.app.log.debug(
                "Failed release found for season (%s): (%s)" % (episode_obj.season, dbData["release"]))

            return release, provider

        # Release was not found
        sickrage.app.log.debug(
            "No releases found for season (%s) of (%s)" % (episode_obj.season, show_id))

        return release, provider
