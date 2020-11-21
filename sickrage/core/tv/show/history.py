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
from sickrage.core.common import Quality, EpisodeStatus
from sickrage.core.databases.main import MainDB
from sickrage.core.exceptions import EpisodeNotFoundException
from sickrage.core.tv.show.helpers import get_show_list, find_show


class History:
    def clear(self):
        """
        Clear all the history
        """
        session = sickrage.app.main_db.session()
        session.query(MainDB.History).delete()
        session.commit()

    def get(self, limit=100, action=None):
        """
        :param limit: The maximum number of elements to return
        :param action: The type of action to filter in the history. Either 'downloaded' or 'snatched'. Anything else or
                        no value will return everything (up to ``limit``)
        :return: The last ``limit`` elements of type ``action`` in the history
        """

        session = sickrage.app.main_db.session()

        data = []

        action = action.lower() if isinstance(action, str) else ''
        limit = int(limit)

        if action == 'downloaded':
            actions = EpisodeStatus.composites(EpisodeStatus.DOWNLOADED)
        elif action == 'snatched':
            actions = EpisodeStatus.composites(EpisodeStatus.SNATCHED)
        else:
            actions = []

        for show in get_show_list():
            if limit == 0:
                if len(actions) > 0:
                    dbData = session.query(MainDB.History).filter_by(series_id=show.series_id).filter(
                        MainDB.History.action.in_(actions)).order_by(MainDB.History.date.desc())
                else:
                    dbData = session.query(MainDB.History).filter_by(series_id=show.series_id).order_by(MainDB.History.date.desc())
            else:
                if len(actions) > 0:
                    dbData = session.query(MainDB.History).filter_by(series_id=show.series_id).filter(
                        MainDB.History.action.in_(actions)).order_by(MainDB.History.date.desc()).limit(limit)
                else:
                    dbData = session.query(MainDB.History).filter_by(series_id=show.series_id).order_by(
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
                    'series_id': result.series_id,
                    'show_name': show.name
                })

        return data

    def trim(self):
        """
        Remove all elements older than 30 days from the history
        """

        session = sickrage.app.main_db.session()

        date = (datetime.today() - timedelta(days=30))
        session.query(MainDB.History).filter(MainDB.History.date < date).delete()
        session.commit()

    @staticmethod
    def _log_history_item(action, series_id, series_provider_id, season, episode, quality, resource, provider, version=-1, release_group=''):
        """
        Insert a history item in DB

        :param action: action taken (snatch, download, etc)
        :param series_id: series_id this entry is about
        :param quality: media quality
        :param resource: resource used
        :param provider: provider used
        :param version: tracked version of file (defaults to -1)
        """

        session = sickrage.app.main_db.session()

        logDate = datetime.today()
        resource = resource

        session.add(MainDB.History(**{
            'action': action,
            'date': logDate,
            'series_id': series_id,
            'series_provider_id': series_provider_id,
            'season': season,
            'episode': episode,
            'quality': quality,
            'resource': resource,
            'provider': provider,
            'version': version,
            'release_group': release_group or ''
        }))

        session.commit()

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

            action = Quality.composite_status(EpisodeStatus.SNATCHED, search_result.quality)

            resource = search_result.name

            release_group = search_result.release_group

            History._log_history_item(action, search_result.series_id, search_result.series_provider_id, search_result.season, episode, quality, resource,
                                      provider, version, release_group)

    @staticmethod
    def log_download(series_id, series_provider_id, season, episode, status, filename, new_ep_quality, release_group='', version=-1):
        """
        Log history of download

        :param episode: episode of show
        :param filename: file on disk where the download is
        :param new_ep_quality: Quality of download
        :param release_group: Release group
        :param version: Version of file (defaults to -1)
        """

        session = sickrage.app.main_db.session()

        provider = ''

        dbData = session.query(MainDB.History).filter(MainDB.History.resource.contains(os.path.basename(filename).rpartition(".")[0])).first()
        if dbData:
            provider = dbData.provider

        History._log_history_item(status, series_id, series_provider_id, season, episode, new_ep_quality, filename, provider, version, release_group)

    @staticmethod
    def log_subtitle(series_id, series_provider_id, season, episode, status, subtitle):
        """
        Log download of subtitle

        :param series_id: Showid of download
        :param season: Show season
        :param episode: Show episode
        :param status: Status of download
        :param subtitle: Result object
        """
        resource = subtitle.language.opensubtitles
        provider = subtitle.provider_name

        status, quality = Quality.split_composite_status(status)
        action = Quality.composite_status(EpisodeStatus.SUBTITLED, quality)

        History._log_history_item(action, series_id, series_provider_id, season, episode, quality, resource, provider)

    @staticmethod
    def log_failed(series_id, series_provider_id, season, episode, release, provider=None):
        """
        Log a failed download

        :param epObj: Episode object
        :param release: Release group
        :param provider: Provider used for snatch
        """
        show_object = find_show(series_id, series_provider_id)
        if not show_object:
            return

        episode_object = show_object.get_episode(season, episode)

        status, quality = Quality.split_composite_status(episode_object.status)
        action = Quality.composite_status(EpisodeStatus.FAILED, quality)

        History._log_history_item(action, series_id, series_provider_id, season, episode, quality, release, provider)


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

        session = sickrage.app.main_db.session()

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
                [FailedHistory.delete_logged_snatch(result.release, result.size, result.provider) for result in dbData]

            if len(set(x.provider for x in dbData)) == 1:
                sickrage.app.log.info("They're also from the same provider. Using it as well.")
                provider = dbData[0].provider
        else:
            size = dbData[0].size
            provider = dbData[0].provider

        if not FailedHistory.has_failed(release, size, provider):
            session.add(MainDB.FailedSnatch(**{'series_id': dbData[0].series_id,
                                               'series_provider_id': dbData[0].series_provider_id,
                                               'release': release,
                                               'size': size,
                                               'provider': provider}))
            session.commit()

        FailedHistory.delete_logged_snatch(release, size, provider)

        return log_str

    @staticmethod
    def log_success(release):
        session = sickrage.app.main_db.session()
        release = FailedHistory.prepare_failed_name(release)
        session.query(MainDB.FailedSnatchHistory).filter_by(release=release).delete()
        session.commit()

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
        :param session: Database session
        :return: True if a release has previously failed.
        """

        session = sickrage.app.main_db.session()
        release = FailedHistory.prepare_failed_name(release)
        return session.query(MainDB.FailedSnatch).filter_by(release=release, size=size, provider=provider).count() > 0

    @staticmethod
    def revert_failed_episode(series_id, series_provider_id, season, episode):
        """Restore the episodes of a failed download to their original state"""
        session = sickrage.app.main_db.session()

        show_object = find_show(series_id, series_provider_id)
        if not show_object:
            return

        episode_object = show_object.get_episode(season, episode)

        history_eps = dict((x.episode, x) for x in session.query(MainDB.FailedSnatchHistory).filter_by(series_id=series_id,
                                                                                                       series_provider_id=series_provider_id,
                                                                                                       season=season,
                                                                                                       episode=episode))

        try:
            sickrage.app.log.info("Reverting episode (%s, %s): %s" % (season, episode, episode_object.name))
            if episode in history_eps:
                sickrage.app.log.info("Found in history")
                episode_object.status = history_eps[episode].old_status
            else:
                sickrage.app.log.debug("WARNING: Episode not found in history. Setting it back to WANTED")
                episode_object.status = EpisodeStatus.WANTED
                episode_object.save()

        except EpisodeNotFoundException as e:
            sickrage.app.log.warning("Unable to create episode, please set its status manually: {}".format(e))

    @staticmethod
    def mark_failed(series_id, series_provider_id, season, episode):
        """
        Mark an episode as failed

        :param epObj: Episode object to mark as failed
        :return: empty string
        """
        log_str = ""

        show_object = find_show(series_id, series_provider_id)
        if not show_object:
            return log_str

        try:
            episode_object = show_object.get_episode(season, episode)
            quality = Quality.split_composite_status(episode_object.status)[1]
            episode_object.status = Quality.composite_status(EpisodeStatus.FAILED, quality)
            episode_object.save()
        except EpisodeNotFoundException as e:
            sickrage.app.log.warning("Unable to get episode, please set its status manually: {}".format(e))

        return log_str

    @staticmethod
    def log_snatch(search_result):
        """
        Logs a successful snatch

        :param search_result: Search result that was successful
        """
        logDate = datetime.today()
        release = FailedHistory.prepare_failed_name(search_result.name)
        provider = search_result.provider.name if search_result.provider else "unknown"

        session = sickrage.app.main_db.session()

        show_object = find_show(search_result.series_id, search_result.series_provider_id)

        for episode in search_result.episodes:
            episode_object = show_object.get_episode(search_result.season, episode)
            session.add(MainDB.FailedSnatchHistory(**{
                'date': logDate,
                'size': search_result.size,
                'release': release,
                'provider': provider,
                'series_id': search_result.series_id,
                'series_provider_id': search_result.series_provider_id,
                'season': search_result.season,
                'episode': episode,
                'old_status': episode_object.status
            }))
            session.commit()

    @staticmethod
    def delete_logged_snatch(release, size, provider):
        """
        Remove a snatch from history

        :param release: release to delete
        :param size: Size of release
        :param provider: Provider to delete it from
        """

        session = sickrage.app.main_db.session()
        release = FailedHistory.prepare_failed_name(release)
        session.query(MainDB.FailedSnatchHistory).filter_by(release=release, size=size, provider=provider).delete()
        session.commit()

    @staticmethod
    def trim_history():
        """Trims history table to 1 month of history from today"""

        session = sickrage.app.main_db.session()
        date = (datetime.today() - timedelta(days=30))
        session.query(MainDB.FailedSnatchHistory).filter(MainDB.FailedSnatchHistory.date < date).delete()
        session.commit()

    @staticmethod
    def find_failed_release(series_id, series_provider_id, season, episode):
        """
        Find releases in history by show ID and season.
        Return None for release if multiple found or no release found.
        """

        release = None
        provider = None

        session = sickrage.app.main_db.session()

        # Clear old snatches for this release if any exist
        session.query(MainDB.FailedSnatchHistory).filter_by(series_id=series_id,
                                                            series_provider_id=series_provider_id,
                                                            season=season,
                                                            episode=episode) \
            .filter(MainDB.FailedSnatchHistory.date < MainDB.FailedSnatchHistory.date).delete()

        session.commit()

        # Search for release in snatch history
        for dbData in session.query(MainDB.FailedSnatchHistory).filter_by(series_id=series_id,
                                                                          series_provider_id=series_provider_id,
                                                                          season=season,
                                                                          episode=episode):
            release = dbData.release
            provider = dbData.provider
            date = dbData.date

            # Clear any incomplete snatch records for this release if any exist
            session.query(MainDB.FailedSnatchHistory).filter_by(release=release).filter(MainDB.FailedSnatchHistory.date != date)

            # Found a previously failed release
            sickrage.app.log.debug("Failed release found for season (%s): (%s)" % (dbData.season, dbData.release))

            return release, provider

        # Release was not found
        sickrage.app.log.debug("No releases found for season (%s) of (%s)" % (season, series_id))

        return release, provider
