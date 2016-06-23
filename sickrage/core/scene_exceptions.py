#!/usr/bin/env python2

# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
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

import datetime
import re
import threading
import time

import sickrage
from sickrage.core.databases import cache_db
from sickrage.core.helpers import full_sanitizeSceneName, sanitizeSceneName
from sickrage.indexers import srIndexerApi
from sickrage.indexers.adba.aniDBAbstracter import Anime

exception_dict = {}
anidb_exception_dict = {}
xem_exception_dict = {}

exceptionsCache = {}
exceptionsSeasonCache = {}

exceptionLock = threading.Lock()


def shouldRefresh(exList):
    """
    Check if we should refresh cache for items in exList

    :param exList: exception list to check if needs a refresh
    :return: True if refresh is needed
    """
    MAX_REFRESH_AGE_SECS = 86400  # 1 day

    rows = cache_db.CacheDB().select("SELECT last_refreshed FROM scene_exceptions_refresh WHERE list = ?", [exList])
    if rows:
        lastRefresh = int(rows[0]['last_refreshed'])
        return int(time.mktime(datetime.datetime.today().timetuple())) > lastRefresh + MAX_REFRESH_AGE_SECS
    else:
        return True


def setLastRefresh(exList):
    """
    Update last cache update time for shows in list

    :param exList: exception list to set refresh time
    """
    cache_db.CacheDB().upsert("scene_exceptions_refresh",
                              {'last_refreshed': int(time.mktime(datetime.datetime.today().timetuple()))},
                              {'list': exList})


def retrieve_exceptions(get_xem=True, get_anidb=True):
    """
    Looks up the exceptions on github, parses them into a dict, and inserts them into the
    scene_exceptions table in cache.db. Also clears the scene name cache.
    """

    for indexer in srIndexerApi().indexers:
        indexer_name = srIndexerApi(indexer).name

        if shouldRefresh(indexer_name):
            sickrage.srCore.srLogger.info("Checking for SiCKRAGE scene exception updates on {}".format(indexer_name))
            loc = srIndexerApi(indexer).config['scene_loc']

            try:
                # each exception is on one line with the format indexer_id: 'show name 1', 'show name 2', etc
                cur_line = None
                for cur_line in sickrage.srCore.srWebSession.get(loc).text.splitlines():
                    indexer_id, _, aliases = cur_line.partition(':')  # @UnusedVariable
                    if not aliases:
                        continue

                    # regex out the list of shows, taking \' into account
                    exception_dict[int(indexer_id)] = [{re.sub(r'\\(.)', r'\1', x): -1} for x in
                                                       re.findall(r"'(.*?)(?<!\\)',?", aliases)]
                if cur_line is None:
                    sickrage.srCore.srLogger.debug(
                        "Check scene exceptions update failed. Unable to update from: {}".format(loc))
                    continue

                # refreshed successfully
                setLastRefresh(indexer_name)
            except Exception:
                continue

    # XEM scene exceptions
    if get_xem:
        _xem_exceptions_fetcher()

    # AniDB scene exceptions
    if get_anidb:
        _anidb_exceptions_fetcher()

    sql_l = []
    for cur_indexer_id in exception_dict:
        sql_ex = cache_db.CacheDB().select("SELECT * FROM scene_exceptions WHERE indexer_id = ?;", [cur_indexer_id])
        existing_exceptions = [x["show_name"] for x in sql_ex]
        if not cur_indexer_id in exception_dict:
            continue

        for cur_exception_dict in exception_dict[cur_indexer_id]:
            for ex in cur_exception_dict.items():
                cur_exception, curSeason = ex
                if cur_exception not in existing_exceptions:
                    sql_l.append(
                        ["INSERT OR IGNORE INTO scene_exceptions (indexer_id, show_name, season) VALUES (?,?,?);",
                         [cur_indexer_id, cur_exception, curSeason]])
    if len(sql_l) > 0:
        cache_db.CacheDB().mass_action(sql_l)
        sickrage.srCore.srLogger.debug("Updated scene exceptions")
        del sql_l  # cleanup
    else:
        sickrage.srCore.srLogger.debug("No scene exceptions update needed")

    # cleanup
    exception_dict.clear()
    anidb_exception_dict.clear()
    xem_exception_dict.clear()


def get_scene_exceptions(indexer_id, season=-1):
    """
    Given a indexer_id, return a list of all the scene exceptions.
    """

    exceptionsList = []

    if indexer_id not in exceptionsCache or season not in exceptionsCache[indexer_id]:
        exceptions = cache_db.CacheDB().select(
            "SELECT show_name FROM scene_exceptions WHERE indexer_id = ? AND season = ?",
            [indexer_id, season])
        if exceptions:
            exceptionsList = list(set([cur_exception["show_name"] for cur_exception in exceptions]))

            if not indexer_id in exceptionsCache:
                exceptionsCache[indexer_id] = {}
            exceptionsCache[indexer_id][season] = exceptionsList
    else:
        exceptionsList = exceptionsCache[indexer_id][season]

    if season == 1:  # if we where looking for season 1 we can add generic names
        exceptionsList += get_scene_exceptions(indexer_id, season=-1)

    return exceptionsList


def get_all_scene_exceptions(indexer_id):
    """
    Get all scene exceptions for a show ID

    :param indexer_id: ID to check
    :return: dict of exceptions
    """
    exceptionsDict = {}

    exceptions = cache_db.CacheDB().select("SELECT show_name,season FROM scene_exceptions WHERE indexer_id = ?",
                                           [indexer_id])

    if exceptions:
        for cur_exception in exceptions:
            if not cur_exception["season"] in exceptionsDict:
                exceptionsDict[cur_exception["season"]] = []
            exceptionsDict[cur_exception["season"]].append(cur_exception["show_name"])

    return exceptionsDict


def get_scene_seasons(indexer_id):
    """
    return a list of season numbers that have scene exceptions
    """
    exceptionsSeasonList = []

    if indexer_id not in exceptionsSeasonCache:
        sqlResults = cache_db.CacheDB().select(
            "SELECT DISTINCT(season) AS season FROM scene_exceptions WHERE indexer_id = ?",
            [indexer_id])
        if sqlResults:
            exceptionsSeasonList = list(set([int(x["season"]) for x in sqlResults]))

            if not indexer_id in exceptionsSeasonCache:
                exceptionsSeasonCache[indexer_id] = {}

            exceptionsSeasonCache[indexer_id] = exceptionsSeasonList
    else:
        exceptionsSeasonList = exceptionsSeasonCache[indexer_id]

    return exceptionsSeasonList


def get_scene_exception_by_name(show_name):
    return get_scene_exception_by_name_multiple(show_name)[0]


def get_scene_exception_by_name_multiple(show_name):
    """
    Given a show name, return the indexerid of the exception, None if no exception
    is present.
    """

    # try the obvious case first
    exception_result = cache_db.CacheDB().select(
        "SELECT indexer_id, season FROM scene_exceptions WHERE LOWER(show_name) = ? ORDER BY season ASC",
        [show_name.lower()])
    if exception_result:
        return [(int(x["indexer_id"]), int(x["season"])) for x in exception_result]

    out = []
    all_exception_results = cache_db.CacheDB().select("SELECT show_name, indexer_id, season FROM scene_exceptions")

    for cur_exception in all_exception_results:

        cur_exception_name = cur_exception["show_name"]
        cur_indexer_id = int(cur_exception["indexer_id"])
        cur_season = int(cur_exception["season"])

        if show_name.lower() in (
                cur_exception_name.lower(),
                sanitizeSceneName(cur_exception_name).lower().replace('.', ' ')):
            sickrage.srCore.srLogger.debug("Scene exception lookup got indexer id " + str(cur_indexer_id) + ", using that")
            out.append((cur_indexer_id, cur_season))

    if out:
        return out

    return [(None, None)]


def update_scene_exceptions(indexer_id, scene_exceptions, season=-1):
    """
    Given a indexer_id, and a list of all show scene exceptions, update the db.
    """
    cache_db.CacheDB().action('DELETE FROM scene_exceptions WHERE indexer_id=? AND season=?', [indexer_id, season])

    sickrage.srCore.srLogger.info("Updating scene exceptions")

    # A change has been made to the scene exception list. Let's clear the cache, to make this visible
    if indexer_id in exceptionsCache:
        exceptionsCache[indexer_id] = {}
        exceptionsCache[indexer_id][season] = scene_exceptions

    for cur_exception in scene_exceptions:
        cache_db.CacheDB().action("INSERT INTO scene_exceptions (indexer_id, show_name, season) VALUES (?,?,?)",
                                  [indexer_id, cur_exception, season])


def _anidb_exceptions_fetcher():
    if shouldRefresh('anidb'):
        sickrage.srCore.srLogger.info("Checking for AniDB scene exception updates")
        for show in sickrage.srCore.SHOWLIST:
            if show.is_anime and show.indexer == 1:
                try:
                    anime = Anime(None, name=show.name, tvdbid=show.indexerid, autoCorrectName=True)
                except Exception:
                    continue
                else:
                    if anime.name and anime.name != show.name:
                        anidb_exception_dict[show.indexerid] = [{anime.name: -1}]

        setLastRefresh('anidb')

    for anidb_ex in anidb_exception_dict:
        if anidb_ex in exception_dict:
            exception_dict[anidb_ex] = exception_dict[anidb_ex] + anidb_exception_dict[anidb_ex]
        else:
            exception_dict[anidb_ex] = anidb_exception_dict[anidb_ex]

    return anidb_exception_dict


def _xem_exceptions_fetcher():
    if shouldRefresh('xem'):
        sickrage.srCore.srLogger.info("Checking for XEM scene exception updates")

        for indexer in srIndexerApi().indexers:

            url = "http://thexem.de/map/allNames?origin=%s&seasonNumbers=1" % srIndexerApi(indexer).config[
                'xem_origin']

            try:
                parsedJSON = sickrage.srCore.srWebSession.get(url, timeout=90).json()
            except Exception:
                sickrage.srCore.srLogger.debug("Check scene exceptions update failed for " + srIndexerApi(
                    indexer).name + ", Unable to get URL: " + url)
                continue

            if parsedJSON['result'] == 'failure':
                continue

            for indexerid, names in parsedJSON['data'].items():
                try:
                    xem_exception_dict[int(indexerid)] = names
                except Exception as e:
                    sickrage.srCore.srLogger.warning("XEM: Rejected entry: indexerid:{0}; names:{1}".format(indexerid, names))
                    sickrage.srCore.srLogger.debug("XEM: Rejected entry error message:{0}".format(str(e)))

        setLastRefresh('xem')

    for xem_ex in xem_exception_dict:
        if xem_ex in exception_dict:
            exception_dict[xem_ex] = exception_dict[xem_ex] + xem_exception_dict[xem_ex]
        else:
            exception_dict[xem_ex] = xem_exception_dict[xem_ex]

    return xem_exception_dict


def getSceneSeasons(indexer_id):
    """get a list of season numbers that have scene exceptions"""
    seasons = cache_db.CacheDB().select("SELECT DISTINCT season FROM scene_exceptions WHERE indexer_id = ?",
                                        [indexer_id])
    return [cur_exception["season"] for cur_exception in seasons]


def check_against_names(nameInQuestion, show, season=-1):
    showNames = []
    if season in [-1, 1]:
        showNames = [show.name]

    showNames.extend(get_scene_exceptions(show.indexerid, season=season))

    for showName in showNames:
        nameFromList = full_sanitizeSceneName(showName)
        if nameFromList == nameInQuestion:
            return True

    return False
