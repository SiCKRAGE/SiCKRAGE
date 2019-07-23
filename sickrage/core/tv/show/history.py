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
from datetime import datetime
from datetime import timedelta
from urllib.parse import unquote

import sickrage
from sickrage.core.common import Quality, SNATCHED, SUBTITLED, FAILED, WANTED
from sickrage.core.databases.main import MainDB
from sickrage.core.exceptions import EpisodeNotFoundException
from sickrage.core.tv.show.helpers import get_show_list, find_show


class History:
    @MainDB.with_session
    def clear(self, session=None):
        """
        Clear all the history
        """
        session.query(MainDB.History).delete()

    @MainDB.with_session
    def get(self, limit=100, action=None, session=None):
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
                    dbData = session.query(MainDB.History).filter_by(showid=show.indexer_id).filter(
                        MainDB.History.action.in_(actions)).order_by(MainDB.History.date.desc())
                else:
                    dbData = session.query(MainDB.History).filter_by(showid=show.indexer_id).order_by(MainDB.History.date.desc())
            else:
                if len(actions) > 0:
                    dbData = session.query(MainDB.History).filter_by(showid=show.indexer_id).filter(
                        MainDB.History.action.in_(actions)).order_by(MainDB.History.date.desc()).limit(limit)
                else:
                    dbData = session.query(MainDB.History).filter_by(showid=show.indexer_id).order_by(
                        MainDB.History.date.desc()).limit(limit)

            for result in dbData:
                data.append({
                    'action': result.action,
                    'date': result.date,
                    'provider': result.provider,
                    'release_group': result.release_group,
                    'quality': result.quality,
                    'resource': result.resource,
                    'season': result.season,
                    'episode': result.episode,
                    'show_id': result.showid,
                    'show_name': show.name
                })

        return data

    @MainDB.with_session
    def trim(self, session=None):
        """
        Remove all elements older than 30 days from the history
        """

        date = (datetime.today() - timedelta(days=30))
        session.query(MainDB.History).filter(MainDB.History.date < date).delete()

    @staticmethod
    @MainDB.with_session
    def _log_history_item(action, showid, season, episode, quality, resource, provider, version=-1, release_group='', session=None):
        """
        Insert a history item in DB

        :param action: action taken (snatch, download, etc)
        :param showid: showid this entry is about
        :param quality: media quality
        :param resource: resource used
        :param provider: provider used
        :param version: tracked version of file (defaults to -1)
        """
        logDate = datetime.today()
        resource = resource

        session.add(MainDB.History(**{
            'action': action,
            'date': logDate,
            'showid': showid,
            'season': season,
            'episode': episode,
            'quality': quality,
            'resource': resource,
            'provider': provider,
            'version': version,
            'release_group': release_group or ''
        }))

    @staticmethod
    def log_snatch(search_result):
        """
        Log history of snatch

        :param search_result: search result object
        """
        for episode in search_result.episodes:
            quality = search_result.quality
            version = search_result.version

            provider = search_result.provider.name if search_result.provider else "unknown"

            action = Quality.composite_status(SNATCHED, search_result.quality)

            resource = search_result.name

            release_group = search_result.release_group

            History._log_history_item(action, search_result.show_id, search_result.season, episode, quality, resource, provider, version, release_group)

    @staticmethod
    @MainDB.with_session
    def log_download(show_id, season, episode, status, filename, new_ep_quality, release_group='', version=-1, session=None):
        """
        Log history of download

        :param episode: episode of show
        :param filename: file on disk where the download is
        :param new_ep_quality: Quality of download
        :param release_group: Release group
        :param version: Version of file (defaults to -1)
        """

        provider = ''

        dbData = session.query(MainDB.History).filter(MainDB.History.resource.contains(os.path.basename(filename).rpartition(".")[0])).first()
        if dbData:
            provider = dbData.provider

        History._log_history_item(status, show_id, season, episode, new_ep_quality, filename, provider, version, release_group)

    @staticmethod
    def log_subtitle(show_id, season, episode, status, subtitle):
        """
        Log download of subtitle

        :param showid: Showid of download
        :param season: Show season
        :param episode: Show episode
        :param status: Status of download
        :param subtitleResult: Result object
        """
        resource = subtitle.language.opensubtitles
        provider = subtitle.provider_name

        status, quality = Quality.split_composite_status(status)
        action = Quality.composite_status(SUBTITLED, quality)

        History._log_history_item(action, show_id, season, episode, quality, resource, provider)

    @staticmethod
    @MainDB.with_session
    def log_failed(show_id, season, episode, release, provider=None, session=None):
        """
        Log a failed download

        :param epObj: Episode object
        :param release: Release group
        :param provider: Provider used for snatch
        """
        show_object = find_show(show_id, session=session)
        episode_object = show_object.get_episode(season, episode)

        status, quality = Quality.split_composite_status(episode_object.status)
        action = Quality.composite_status(FAILED, quality)

        History._log_history_item(action, show_id, season, episode, quality, release, provider, session=session)


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
    @MainDB.with_session
    def log_failed(release, session=None):
        log_str = ""
        size = -1
        provider = ""

        release = FailedHistory.prepare_failed_name(release)

        dbData = session.query(MainDB.FailedSnatchHistory).filter_by(release=release)

        if dbData.count() == 0:
            sickrage.app.log.warning("{}, Release not found in snatch history.".format(release))
        elif dbData.count() > 1:
            sickrage.app.log.warning("Multiple logged snatches found for release")

            if len(set(x.size for x in dbData)) == 1:
                sickrage.app.log.warning("However, they're all the same size. Continuing with found size.")
                size = dbData[0].size
            else:
                sickrage.app.log.warning("They also vary in size. Deleting the logged snatches and recording this release with no size/provider")
                [FailedHistory.delete_logged_snatch(result.release, result.size, result.provider, session=session) for result in dbData]

            if len(set(x.provider for x in dbData)) == 1:
                sickrage.app.log.info("They're also from the same provider. Using it as well.")
                provider = dbData[0].provider
        else:
            size = dbData[0].size
            provider = dbData[0].provider

        if not FailedHistory.has_failed(release, size, provider, session=session):
            session.add(MainDB.FailedSnatch(**{'release': release, 'size': size, 'provider': provider}))

        FailedHistory.delete_logged_snatch(release, size, provider, session=session)

        return log_str

    @staticmethod
    @MainDB.with_session
    def log_success(release, session=None):
        release = FailedHistory.prepare_failed_name(release)
        session.query(MainDB.FailedSnatchHistory).filter_by(release=release).delete()

    @staticmethod
    @MainDB.with_session
    def has_failed(release, size, provider="%", session=None):
        """
        Returns True if a release has previously failed.

        If provider is given, return True only if the release is found
        with that specific provider. Otherwise, return True if the release
        is found with any provider.

        :param release: Release name to record failure
        :param size: Size of release
        :param provider: Specific provider to search (defaults to all providers)
        :param session: Database session
        :return: True if a release has previously failed.
        """

        release = FailedHistory.prepare_failed_name(release)
        return session.query(MainDB.FailedSnatch).filter_by(release=release, size=size, provider=provider).count() > 0

    @staticmethod
    @MainDB.with_session
    def revert_failed_episode(show_id, season, episode, session=None):
        """Restore the episodes of a failed download to their original state"""
        history_eps = dict((x.episode, x) for x in session.query(MainDB.FailedSnatchHistory).filter_by(showid=show_id, season=season, episode=episode))

        show_object = find_show(show_id, session=session)
        episode_object = show_object.get_episode(season, episode)

        try:
            sickrage.app.log.info("Reverting episode (%s, %s): %s" % (season, episode, episode_object.name))
            if episode in history_eps:
                sickrage.app.log.info("Found in history")
                episode_object.status = history_eps[episode].old_status
            else:
                sickrage.app.log.debug("WARNING: Episode not found in history. Setting it back to WANTED")
                episode_object.status = WANTED

        except EpisodeNotFoundException as e:
            sickrage.app.log.warning("Unable to create episode, please set its status manually: {}".format(e))

    @staticmethod
    @MainDB.with_session
    def mark_failed(show_id, season, episode, session=None):
        """
        Mark an episode as failed

        :param epObj: Episode object to mark as failed
        :return: empty string
        """
        log_str = ""

        show_object = find_show(show_id, session=session)
        episode_object = show_object.get_episode(season, episode)

        try:
            quality = Quality.split_composite_status(episode_object.status)[1]
            episode_object.status = Quality.composite_status(FAILED, quality)
        except EpisodeNotFoundException as e:
            sickrage.app.log.warning("Unable to get episode, please set its status manually: {}".format(e))

        return log_str

    @staticmethod
    @MainDB.with_session
    def log_snatch(search_result, session=None):
        """
        Logs a successful snatch

        :param search_result: Search result that was successful
        """
        logDate = datetime.today()
        release = FailedHistory.prepare_failed_name(search_result.name)
        provider = search_result.provider.name if search_result.provider else "unknown"

        show_object = find_show(search_result.show_id, session=session)

        for episode in search_result.episodes:
            episode_object = show_object.get_episode(search_result.season, episode)
            session.add(MainDB.FailedSnatchHistory(**{
                'date': logDate,
                'size': search_result.size,
                'release': release,
                'provider': provider,
                'showid': search_result.show_id,
                'season': search_result.season,
                'episode': episode,
                'old_status': episode_object.status
            }))

    @staticmethod
    @MainDB.with_session
    def delete_logged_snatch(release, size, provider, session=None):
        """
        Remove a snatch from history

        :param release: release to delete
        :param size: Size of release
        :param provider: Provider to delete it from
        """
        release = FailedHistory.prepare_failed_name(release)
        session.query(MainDB.FailedSnatchHistory).filter_by(release=release, size=size, provider=provider).delete()

    @staticmethod
    @MainDB.with_session
    def trim_history(session=None):
        """Trims history table to 1 month of history from today"""
        date = (datetime.today() - timedelta(days=30))
        session.query(MainDB.FailedSnatchHistory).filter(MainDB.FailedSnatchHistory.date < date).delete()

    @staticmethod
    @MainDB.with_session
    def find_failed_release(show_id, season, episode, session=None):
        """
        Find releases in history by show ID and season.
        Return None for release if multiple found or no release found.
        """

        release = None
        provider = None

        # Clear old snatches for this release if any exist
        session.query(MainDB.FailedSnatchHistory).filter_by(showid=show_id, season=season, episode=episode).filter(
            MainDB.FailedSnatchHistory.date < MainDB.FailedSnatchHistory.date).delete()

        # Search for release in snatch history
        for dbData in session.query(MainDB.FailedSnatchHistory).filter_by(showid=show_id, season=season, episode=episode):
            release = dbData.release
            provider = dbData.provider
            date = dbData.date

            # Clear any incomplete snatch records for this release if any exist
            session.query(MainDB.FailedSnatchHistory).filter_by(release=release).filter(MainDB.FailedSnatchHistory.date != date)

            # Found a previously failed release
            sickrage.app.log.debug("Failed release found for season (%s): (%s)" % (dbData.season, dbData.release))

            return release, provider

        # Release was not found
        sickrage.app.log.debug("No releases found for season (%s) of (%s)" % (season, show_id))

        return release, provider
