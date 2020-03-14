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
import re
import threading
import time

from adba.aniDBAbstracter import Anime
from sqlalchemy import orm

import sickrage
from sickrage.core.databases.cache import CacheDB
from sickrage.core.helpers import sanitize_scene_name, strip_accents
from sickrage.core.tv.show.helpers import get_show_list
from sickrage.core.websession import WebSession
from sickrage.indexers import IndexerApi

exception_dict = {}
anidb_exception_dict = {}
xem_exception_dict = {}

exceptionsCache = {}

exceptionLock = threading.Lock()


def load_scene_exceptions():
    session = sickrage.app.cache_db.session()

    for cur_exception in session.query(CacheDB.SceneException):
        exceptions_list = list({cur_exception.show_name, strip_accents(cur_exception.show_name), strip_accents(cur_exception.show_name).replace("'", " ")})

        if cur_exception.indexer_id not in exceptionsCache:
            exceptionsCache[cur_exception.indexer_id] = {}
        if cur_exception.season not in exceptionsCache[cur_exception.indexer_id]:
            exceptionsCache[cur_exception.indexer_id][cur_exception.season] = []

        exceptionsCache[cur_exception.indexer_id][cur_exception.season] += exceptions_list
        exceptionsCache[cur_exception.indexer_id][cur_exception.season] = list(set(exceptionsCache[cur_exception.indexer_id][cur_exception.season]))

    if not len(exceptionsCache):
        retrieve_scene_exceptions()


def should_refresh(ex_list):
    """
    Check if we should refresh cache for items in ex_list

    :param ex_list: exception list to check if needs a refresh
    :return: True if refresh is needed
    """

    session = sickrage.app.cache_db.session()

    max_refresh_age_secs = 86400  # 1 day

    try:
        query = session.query(CacheDB.SceneExceptionRefresh).filter_by(exception_list=ex_list).one()
        last_refresh = int(query.last_refreshed)
        return int(time.mktime(datetime.datetime.today().timetuple())) > last_refresh + max_refresh_age_secs
    except orm.exc.NoResultFound:
        return True


def set_last_refresh(ex_list):
    """
    Update last cache update time for shows in list

    :param ex_list: exception list to set refresh time
    """

    session = sickrage.app.cache_db.session()

    try:
        query = session.query(CacheDB.SceneExceptionRefresh).filter_by(exception_list=ex_list).one()
        query.last_refreshed = int(time.mktime(datetime.datetime.today().timetuple()))
    except orm.exc.NoResultFound:
        session.add(CacheDB.SceneExceptionRefresh(**{
            'last_refreshed': int(time.mktime(datetime.datetime.today().timetuple())),
            'exception_list': ex_list
        }))
    finally:
        session.commit()


def retrieve_scene_exceptions(get_xem=True, get_anidb=True, force=False):
    """
    Looks up the exceptions on github, parses them into a dict, and inserts them into the
    scene_exceptions table in cache db and also clears the scene name cache.
    """

    session = sickrage.app.cache_db.session()

    updated_exceptions = False

    for indexer in IndexerApi().indexers:
        indexer_name = IndexerApi(indexer).name

        if should_refresh(indexer_name) or force:
            sickrage.app.log.info("Checking for SiCKRAGE scene exception updates on {}".format(indexer_name))
            loc = IndexerApi(indexer).config['scene_loc']

            try:
                # each exception is on one line with the format indexer_id: 'show name 1', 'show name 2', etc
                cur_line = None
                for cur_line in WebSession().get(loc).text.splitlines():
                    indexer_id, __, aliases = cur_line.partition(':')
                    if not aliases:
                        continue

                    # regex out the list of shows, taking \' into account
                    exception_dict[int(indexer_id)] = [{re.sub(r'\\(.)', r'\1', x): -1} for x in
                                                       re.findall(r"'(.*?)(?<!\\)',?", aliases)]
                if cur_line is None:
                    sickrage.app.log.debug(
                        "Check scene exceptions update failed. Unable to update from: {}".format(loc))
                    continue

                # refreshed successfully
                set_last_refresh(indexer_name)
            except Exception:
                continue

    # XEM scene exceptions
    if get_xem:
        _xem_exceptions_fetcher(force)

    # AniDB scene exceptions
    if get_anidb:
        _anidb_exceptions_fetcher(force)

    for cur_indexer_id, cur_exception_dict in exception_dict.copy().items():
        if not len(cur_exception_dict):
            continue

        existing_exceptions = [x.show_name for x in session.query(CacheDB.SceneException).filter_by(indexer_id=cur_indexer_id)]

        sql_t = []

        for cur_exception, curSeason in dict([(key, d[key]) for d in cur_exception_dict for key in d]).items():
            if cur_exception not in existing_exceptions:
                sql_t.append({
                    'indexer_id': cur_indexer_id,
                    'show_name': cur_exception,
                    'season': curSeason
                })
                updated_exceptions = True

        session.bulk_insert_mappings(CacheDB.SceneException, sql_t)
        session.commit()

    if updated_exceptions:
        sickrage.app.log.debug("Updated scene exceptions")

    # cleanup
    exception_dict.clear()
    anidb_exception_dict.clear()
    xem_exception_dict.clear()


def get_scene_exceptions(indexer_id, season=-1):
    """
    Given a indexer_id, return a list of all the scene exceptions.
    """

    session = sickrage.app.cache_db.session()

    exceptions_list = []

    if indexer_id not in exceptionsCache or season not in exceptionsCache[indexer_id]:
        try:
            for cur_exception in session.query(CacheDB.SceneException).filter_by(indexer_id=indexer_id, season=season):
                exceptions_list.append(cur_exception.show_name)
                exceptions_list.append(strip_accents(cur_exception.show_name))
                exceptions_list.append(strip_accents(cur_exception.show_name).replace("'", " "))

            if indexer_id not in exceptionsCache:
                exceptionsCache[indexer_id] = {}
            if season not in exceptionsCache[indexer_id]:
                exceptionsCache[indexer_id][season] = []

            exceptionsCache[indexer_id][season] = list(set(exceptions_list))
        except:
            pass
    else:
        exceptions_list = exceptionsCache[indexer_id][season]

    if season == 1:  # if we where looking for season 1 we can add generic names
        exceptions_list += get_scene_exceptions(indexer_id, season=-1)

    return exceptions_list


def get_scene_exception_by_name(show_name):
    """
    Given a show name, return the indexer_id of the exception, None if no exception
    is present.
    """

    session = sickrage.app.cache_db.session()

    # try the obvious case first
    query = session.query(CacheDB.SceneException).filter_by(show_name=show_name.lower()).order_by(CacheDB.SceneException.season).one_or_none()
    if query:
        sickrage.app.log.debug("Scene exception lookup got indexer ID {}, using that".format(query.indexer_id))
        return query.indexer_id, query.season

    # FIXME: Handle show names that are encoded in byte format
    for cur_exception in session.query(CacheDB.SceneException).order_by(CacheDB.SceneException.season):
        cur_exception_name = cur_exception.show_name
        cur_indexer_id = int(cur_exception.indexer_id)
        cur_season = int(cur_exception.season)

        if show_name.lower() == sanitize_scene_name(cur_exception_name).lower().replace('.', ' '):
            sickrage.app.log.debug("Scene exception lookup got indexer ID {}, using that".format(cur_indexer_id))
            return cur_indexer_id, cur_season


def update_scene_exceptions(indexer_id, scene_exceptions, season=-1):
    """
    Given a indexer_id, and a list of all show scene exceptions, update the db.
    """

    session = sickrage.app.cache_db.session()

    session.query(CacheDB.SceneException).filter_by(indexer_id=indexer_id, season=season).delete()
    session.commit()

    sickrage.app.log.info("Updating scene exceptions")

    # A change has been made to the scene exception list. Let's clear the cache, to make this visible
    if indexer_id in exceptionsCache:
        exceptionsCache[indexer_id] = {}

    exceptionsCache[indexer_id][season] = scene_exceptions

    sql_t = []

    for cur_exception in scene_exceptions:
        sql_t.append({
            'indexer_id': indexer_id,
            'show_name': cur_exception,
            'season': season
        })

    session.bulk_insert_mappings(CacheDB.SceneException, sql_t)
    session.commit()


def _anidb_exceptions_fetcher(force=False):
    if should_refresh('anidb') or force:
        sickrage.app.log.info("Checking for AniDB scene exception updates")
        for show in get_show_list():
            if show.is_anime and show.indexer == 1:
                try:
                    anime = Anime(None, name=show.name, tvdbid=show.indexer_id, autoCorrectName=True)
                except Exception:
                    continue
                else:
                    if anime.name and anime.name != show.name:
                        anidb_exception_dict[show.indexer_id] = [{anime.name: -1}]

        set_last_refresh('anidb')

    for anidb_ex in anidb_exception_dict:
        if anidb_ex in exception_dict:
            exception_dict[anidb_ex] = exception_dict[anidb_ex] + anidb_exception_dict[anidb_ex]
        else:
            exception_dict[anidb_ex] = anidb_exception_dict[anidb_ex]

    return anidb_exception_dict


def _xem_exceptions_fetcher(force=False):
    if should_refresh('xem') or force:
        sickrage.app.log.info("Checking for XEM scene exception updates")

        for indexer in IndexerApi().indexers:
            url = "http://thexem.de/map/allNames?origin=%s&seasonNumbers=1" % IndexerApi(indexer).config[
                'xem_origin']

            try:
                parsedJSON = WebSession().get(url, timeout=90).json()
            except Exception:
                sickrage.app.log.debug("Check scene exceptions update failed for " + IndexerApi(
                    indexer).name + ", Unable to get URL: " + url)
                continue

            if parsedJSON['result'] == 'failure':
                continue

            for indexer_id, names in parsedJSON['data'].items():
                try:
                    xem_exception_dict[int(indexer_id)] = names
                except Exception as e:
                    sickrage.app.log.warning(
                        "XEM: Rejected entry: indexer_id:{0}; names:{1}".format(indexer_id, names))
                    sickrage.app.log.debug("XEM: Rejected entry error message:{}".format(e))

        set_last_refresh('xem')

    for xem_ex in xem_exception_dict:
        if xem_ex in exception_dict:
            exception_dict[xem_ex] = exception_dict[xem_ex] + xem_exception_dict[xem_ex]
        else:
            exception_dict[xem_ex] = xem_exception_dict[xem_ex]

    return xem_exception_dict
