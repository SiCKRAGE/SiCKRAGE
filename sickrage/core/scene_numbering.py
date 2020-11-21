# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
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
import traceback

from sqlalchemy import orm

import sickrage
from sickrage.core.databases.main import MainDB
from sickrage.core.exceptions import EpisodeNotFoundException
from sickrage.core.tv.show.helpers import find_show
from sickrage.core.websession import WebSession


def get_scene_numbering(series_id, series_provider_id, season, episode, fallback_to_xem=True):
    """
    Returns a tuple, (season, episode), with the scene numbering (if there is one),
    otherwise returns the xem numbering (if fallback_to_xem is set), otherwise
    returns the TVDB numbering.
    (so the return values will always be set)

    :param series_id: int
    :param season: int
    :param episode: int
    :param fallback_to_xem: bool If set (the default), check xem for matches if there is no local scene numbering
    :return: (int, int) a tuple with (season, episode)
    """
    show_obj = find_show(series_id, series_provider_id)
    if not show_obj:
        return -1, -1

    result = find_scene_numbering(series_id, series_provider_id, season, episode)
    if result:
        return result

    if fallback_to_xem:
        xem_result = find_xem_numbering(series_id, series_provider_id, season, episode)
        if xem_result:
            return xem_result

    return -1, -1


def get_scene_absolute_numbering(series_id, series_provider_id, absolute_number, fallback_to_xem=True):
    """
    Returns absolute number, with the scene numbering (if there is one),
    otherwise returns the xem numbering (if fallback_to_xem is set), otherwise
    returns the TVDB numbering.
    (so the return values will always be set)

    :param series_id: int
    ;param absolute_number: int
    :param fallback_to_xem: bool If set (the default), check xem for matches if there is no local scene numbering
    :return: int absolute number
    """
    show_obj = find_show(series_id, series_provider_id)
    if not show_obj:
        return -1

    result = find_scene_absolute_numbering(series_id, series_provider_id, absolute_number)
    if result:
        return result

    if fallback_to_xem:
        xem_result = find_xem_absolute_numbering(series_id, series_provider_id, absolute_number)
        if xem_result:
            return xem_result

    return -1


def get_series_provider_numbering(series_id, series_provider_id, scene_season, scene_episode, fallback_to_xem=True):
    """
    Returns a tuple, (season, episode) with the TVDB numbering for (sceneSeason, sceneEpisode)
    (this works like the reverse of get_scene_numbering)
    """
    session = sickrage.app.main_db.session()

    try:
        dbData = session.query(MainDB.TVEpisode).filter_by(
            series_id=series_id,
            series_provider_id=series_provider_id,
            scene_season=scene_season,
            scene_episode=scene_episode
        ).one()

        return dbData.season, dbData.episode
    except orm.exc.NoResultFound:
        if fallback_to_xem:
            return get_series_provider_numbering_from_xem_numbering(series_id, series_provider_id, scene_season, scene_episode)
        return -1, -1


def get_series_provider_absolute_numbering(series_id, series_provider_id, scene_absolute_number, fallback_to_xem=True, scene_season=None):
    """
    Returns a tuple, (season, episode, absolute_number) with the TVDB absolute numbering for (sceneAbsoluteNumber)
    (this works like the reverse of get_absolute_numbering)
    """
    session = sickrage.app.main_db.session()

    try:
        if scene_season is None:
            dbData = session.query(MainDB.TVEpisode).filter_by(
                series_id=series_id,
                series_provider_id=series_provider_id,
                scene_absolute_number=scene_absolute_number
            ).one()
        else:
            dbData = session.query(MainDB.TVEpisode).filter_by(
                series_id=series_id,
                series_provider_id=series_provider_id,
                scene_absolute_number=scene_absolute_number,
                scene_season=scene_season
            ).one()
        return dbData.absolute_number
    except (orm.exc.MultipleResultsFound, orm.exc.NoResultFound):
        if fallback_to_xem:
            return get_series_provider_absolute_numbering_from_xem_numbering(series_id, series_provider_id, scene_absolute_number, scene_season)

        return -1


def get_series_provider_numbering_from_xem_numbering(series_id, series_provider_id, xem_season, xem_episode):
    """
    Reverse of find_xem_numbering: lookup series_provider_id season and episode using xem numbering

    :param series_id: int
    :param xem_season: int
    :param xem_episode: int
    :return: (int, int) a tuple of (season, episode)
    """
    session = sickrage.app.main_db.session()

    xem_refresh(series_id, series_provider_id)

    try:
        dbData = session.query(MainDB.TVEpisode).filter_by(series_id=series_id, series_provider_id=series_provider_id, xem_season=xem_season,
                                                           xem_episode=xem_episode).one()
        return dbData.season, dbData.episode
    except (orm.exc.NoResultFound, orm.exc.MultipleResultsFound):
        return -1, -1


def get_series_provider_absolute_numbering_from_xem_numbering(series_id, series_provider_id, xem_absolute_number, xem_season=None):
    """
    Reverse of find_xem_numbering: lookup series_provider_id season and episode using xem numbering

    :param series_id: int
    :param xem_absolute_number: int
    :return: int
    """
    session = sickrage.app.main_db.session()

    xem_refresh(series_id, series_provider_id)

    try:
        if xem_season is None:
            dbData = session.query(MainDB.TVEpisode).filter_by(
                series_id=series_id,
                series_provider_id=series_provider_id,
                xem_absolute_number=xem_absolute_number).one()
        else:
            dbData = session.query(MainDB.TVEpisode).filter_by(
                series_id=series_id,
                series_provider_id=series_provider_id,
                xem_absolute_number=xem_absolute_number,
                xem_season=xem_season).one()
        return dbData.absolute_number
    except (orm.exc.MultipleResultsFound, orm.exc.NoResultFound):
        return -1


def get_scene_numbering_for_show(series_id, series_provider_id):
    """
    Returns a dict of (season, episode) : (sceneSeason, sceneEpisode) mappings
    for an entire show.  Both the keys and values of the dict are tuples.
    Will be empty if there are no scene numbers set
    """
    session = sickrage.app.main_db.session()

    result = {}

    for dbData in session.query(MainDB.TVEpisode).filter_by(series_id=series_id):
        if dbData.series_provider_id != series_provider_id or (dbData.scene_season or dbData.scene_episode) == -1:
            continue

        season = dbData.season
        episode = dbData.episode
        scene_season = dbData.scene_season
        scene_episode = dbData.scene_episode

        result[(season, episode)] = (scene_season, scene_episode)

    return result


def get_scene_absolute_numbering_for_show(series_id, series_provider_id):
    """
    Returns a dict of (season, episode) : (sceneSeason, sceneEpisode) mappings
    for an entire show.  Both the keys and values of the dict are tuples.
    Will be empty if there are no scene numbers set
    """
    session = sickrage.app.main_db.session()

    result = {}

    for dbData in session.query(MainDB.TVEpisode).filter_by(series_id=series_id):
        if dbData.series_provider_id != series_provider_id or dbData.scene_absolute_number == -1:
            continue

        absolute_number = dbData.absolute_number
        scene_absolute_number = dbData.scene_absolute_number

        result[absolute_number] = scene_absolute_number

    return result


def get_xem_numbering_for_show(series_id, series_provider_id):
    """
    Returns a dict of (season, episode) : (sceneSeason, sceneEpisode) mappings
    for an entire show.  Both the keys and values of the dict are tuples.
    Will be empty if there are no scene numbers set in xem
    """
    session = sickrage.app.main_db.session()

    xem_refresh(series_id, series_provider_id)

    result = {}

    for dbData in session.query(MainDB.TVEpisode).filter_by(series_id=series_id):
        if dbData.series_provider_id != series_provider_id or (dbData.xem_season or dbData.xem_episode) == -1:
            continue

        season = dbData.season
        episode = dbData.episode
        xem_season = dbData.xem_season
        xem_episode = dbData.xem_episode

        result[(season, episode)] = (xem_season, xem_episode)

    return result


def get_xem_absolute_numbering_for_show(series_id, series_provider_id):
    """
    Returns a dict of (season, episode) : (sceneSeason, sceneEpisode) mappings
    for an entire show.  Both the keys and values of the dict are tuples.
    Will be empty if there are no scene numbers set in xem
    """
    session = sickrage.app.main_db.session()

    xem_refresh(series_id, series_provider_id)

    result = {}

    for dbData in session.query(MainDB.TVEpisode).filter_by(series_id=series_id):
        if dbData.series_provider_id != series_provider_id or dbData.xem_absolute_number == -1:
            continue

        absolute_number = dbData.absolute_number
        xem_absolute_number = dbData.xem_absolute_number

        result[absolute_number] = xem_absolute_number

    return result


def find_scene_numbering(series_id, series_provider_id, season, episode):
    """
    Same as get_scene_numbering(), but returns None if scene numbering is not set
    """
    session = sickrage.app.main_db.session()

    try:
        dbData = session.query(MainDB.TVEpisode).filter_by(
            series_id=series_id,
            series_provider_id=series_provider_id,
            season=season,
            episode=episode
        ).filter(MainDB.TVEpisode.scene_season != -1 and MainDB.TVEpisode.scene_episode != -1).one()
        return dbData.scene_season, dbData.scene_episode
    except orm.exc.NoResultFound:
        return


def find_scene_absolute_numbering(series_id, series_provider_id, absolute_number):
    """
    Same as get_scene_numbering(), but returns None if scene numbering is not set
    """
    session = sickrage.app.main_db.session()

    try:
        dbData = session.query(MainDB.TVEpisode).filter_by(
            series_id=series_id,
            series_provider_id=series_provider_id,
            absolute_number=absolute_number
        ).filter(MainDB.TVEpisode.scene_absolute_number != -1).one()

        return dbData.scene_absolute_number
    except (orm.exc.MultipleResultsFound, orm.exc.NoResultFound):
        return


def find_xem_numbering(series_id, series_provider_id, season, episode):
    """
    Returns the scene numbering, as retrieved from xem.
    Refreshes/Loads as needed.

    :param series_id: int
    :param season: int
    :param episode: int
    :return: (int, int) a tuple of scene_season, scene_episode, or None if there is no special mapping.
    """
    session = sickrage.app.main_db.session()

    xem_refresh(series_id, series_provider_id)

    try:
        dbData = session.query(MainDB.TVEpisode).filter_by(
            series_id=series_id,
            series_provider_id=series_provider_id,
            season=season,
            episode=episode
        ).filter(MainDB.TVEpisode.xem_season != -1, MainDB.TVEpisode.xem_episode != -1).one()

        return dbData.xem_season, dbData.xem_episode
    except orm.exc.NoResultFound:
        return


def find_xem_absolute_numbering(series_id, series_provider_id, absolute_number):
    """
    Returns the scene numbering, as retrieved from xem.
    Refreshes/Loads as needed.

    :param series_id: int
    :param absolute_number: int
    :return: int
    """
    session = sickrage.app.main_db.session()

    xem_refresh(series_id, series_provider_id)

    try:
        dbData = session.query(MainDB.TVEpisode).filter_by(series_id=series_id, series_provider_id=series_provider_id,
                                                           absolute_number=absolute_number).filter(MainDB.TVEpisode.xem_absolute_number != -1).one()
        return dbData.xem_absolute_number
    except (orm.exc.NoResultFound, orm.exc.MultipleResultsFound):
        return


def set_scene_numbering(series_id, series_provider_id, season=None, episode=None, absolute_number=None, scene_season=None, scene_episode=None,
                        scene_absolute=None):
    """
    Set scene numbering for a season/episode or absolute.
    To clear the scene numbering, leave both scene_season and scene_episode or scene_absolute as None.
    """
    session = sickrage.app.main_db.session()

    if season and episode:
        if scene_season is not None and scene_episode is not None:
            if session.query(MainDB.TVEpisode).filter_by(series_id=series_id, series_provider_id=series_provider_id, scene_season=scene_season,
                                                         scene_episode=scene_episode).count():
                return False

        dbData = session.query(MainDB.TVEpisode).filter_by(series_id=series_id, series_provider_id=series_provider_id, season=season, episode=episode).one()
        dbData.scene_season = scene_season if scene_season is not None else -1
        dbData.scene_episode = scene_episode if scene_episode is not None else -1
    elif absolute_number:
        if scene_absolute is not None:
            if session.query(MainDB.TVEpisode).filter_by(series_id=series_id, series_provider_id=series_provider_id,
                                                         scene_absolute_number=scene_absolute).count():
                return False

        dbData = session.query(MainDB.TVEpisode).filter_by(series_id=series_id, series_provider_id=series_provider_id, absolute_number=absolute_number).one()
        dbData.scene_absolute_number = scene_absolute if scene_absolute is not None else -1

    session.commit()

    return True


def xem_refresh(series_id, series_provider_id, force=False):
    """
    Refresh data from xem for a tv show

    :param series_id: int
    :param series_provider_id: int
    :param force: boolean
    """
    max_refresh_age_secs = 86400  # 1 day

    show_object = find_show(series_id, series_provider_id)
    if not show_object:
        return

    if datetime.datetime.now() > (show_object.last_xem_refresh + datetime.timedelta(seconds=max_refresh_age_secs)) or force:
        sickrage.app.log.debug('Looking up XEM scene mapping for show %s on %s' % (series_id, show_object.series_provider.name))

        # mark xem refreshed
        show_object.last_xem_refresh = datetime.datetime.now()
        show_object.save()

        try:
            try:
                # XEM MAP URL
                url = "http://thexem.de/map/havemap?origin=%s" % show_object.series_provider.xem_origin
                parsed_json = WebSession().get(url).json()
                if not parsed_json or 'data' not in parsed_json:
                    raise ValueError
            except ValueError:
                sickrage.app.log.warning("Resulting JSON from XEM isn't correct, not parsing it")
                return

            if series_id not in map(int, parsed_json['data']):
                sickrage.app.log.info('No XEM data for show {} on {}'.format(show_object.name, show_object.series_provider.name))
                # for episode_object in show_object.episodes:
                #     episode_object.xem_season = -1
                #     episode_object.xem_episode = -1
                #     episode_object.xem_absolute_number = -1
                #     episode_object.save()
                return

            try:
                # XEM API URL
                url = "http://thexem.de/map/all?id={}&origin={}&destination=scene".format(series_id, show_object.series_provider.xem_origin)
                parsed_json = WebSession().get(url).json()
                if not parsed_json or 'result' not in parsed_json or 'data' not in parsed_json:
                    raise ValueError
            except ValueError:
                sickrage.app.log.warning("Resulting JSON from XEM isn't correct, not parsing it")
                return

            if 'success' not in parsed_json['result']:
                sickrage.app.log.info('No XEM data for show {} on {}'.format(show_object.name, show_object.series_provider.name))
                return

            for entry in parsed_json['data']:
                try:
                    episode_object = show_object.get_episode(season=entry[show_object.series_provider.xem_origin]['season'],
                                                             episode=entry[show_object.series_provider.xem_origin]['episode'])
                except EpisodeNotFoundException:
                    continue

                if 'scene' in entry:
                    episode_object.xem_season = entry['scene']['season']
                    episode_object.xem_episode = entry['scene']['episode']
                    episode_object.xem_absolute_number = entry['scene']['absolute']

                if 'scene_2' in entry:  # for doubles
                    episode_object.xem_season = entry['scene_2']['season']
                    episode_object.xem_episode = entry['scene_2']['episode']
                    episode_object.xem_absolute_number = entry['scene_2']['absolute']

                episode_object.save()
        except Exception as e:
            sickrage.app.log.debug("Exception while refreshing XEM data for show {} on {}: {}".format(series_id, show_object.series_provider.name, e))
            sickrage.app.log.debug(traceback.format_exc())


def get_absolute_number_from_season_and_episode(series_id, series_provider_id, season, episode):
    """
    Find the absolute number for a show episode

    :param series_id: Series ID
    :param series_provider_id: Series Provider ID
    :param season: Season number
    :param episode: Episode number
    :return: The absolute number
    """
    session = sickrage.app.main_db.session()

    absolute_number = None

    show_object = find_show(series_id, series_provider_id)
    if not show_object:
        return

    if season and episode:
        try:
            dbData = session.query(MainDB.TVEpisode).filter_by(series_id=series_id, series_provider_id=series_provider_id, season=season,
                                                               episode=episode).one()
            absolute_number = dbData.absolute_number
            sickrage.app.log.debug("Found absolute number %s for show %s S%02dE%02d" % (absolute_number, show_object.name, season, episode))
        except orm.exc.NoResultFound:
            sickrage.app.log.debug("No entries for absolute number for show %s S%02dE%02d" % (show_object.name, season, episode))

    return absolute_number
