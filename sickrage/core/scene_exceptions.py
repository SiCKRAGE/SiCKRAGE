

# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
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

from CodernityDB.database import RecordNotFound

import sickrage
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

    try:
        dbData = sickrage.srCore.cacheDB.db.get('scene_exceptions_refresh', exList, with_doc=True)['doc']
        lastRefresh = int(dbData['last_refreshed'])
        return int(time.mktime(datetime.datetime.today().timetuple())) > lastRefresh + MAX_REFRESH_AGE_SECS
    except RecordNotFound:
        return True


def setLastRefresh(exList):
    """
    Update last cache update time for shows in list

    :param exList: exception list to set refresh time
    """
    try:
        dbData = sickrage.srCore.cacheDB.db.get('scene_exceptions_refresh', exList, with_doc=True)['doc']
        dbData['last_refreshed'] = int(time.mktime(datetime.datetime.today().timetuple()))
        sickrage.srCore.cacheDB.db.update(dbData)
    except RecordNotFound:
        sickrage.srCore.cacheDB.db.insert({
            '_t': 'scene_exceptions_refresh',
            'last_refreshed': int(time.mktime(datetime.datetime.today().timetuple())),
            'list': exList
        })


def retrieve_exceptions(get_xem=True, get_anidb=True):
    """
    Looks up the exceptions on github, parses them into a dict, and inserts them into the
    scene_exceptions table in cache.db. Also clears the scene name cache.
    """

    updated_exceptions = False

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

    for cur_indexer_id, cur_exception_dict in exception_dict.items():
        if not len(cur_exception_dict): continue

        try:
            existing_exceptions = [x['doc']["show_name"] for x in
                                   sickrage.srCore.cacheDB.db.get_many('scene_exceptions', cur_indexer_id, with_doc=True)]
        except RecordNotFound:
            continue

        for cur_exception, curSeason in dict([(key, d[key]) for d in cur_exception_dict for key in d]).items():
            if cur_exception not in existing_exceptions:
                updated_exceptions = True
                sickrage.srCore.cacheDB.db.insert({
                    '_t': 'scene_exceptions',
                    'indexer_id': cur_indexer_id,
                    'show_name': cur_exception,
                    'season': curSeason
                })

    if updated_exceptions:
        sickrage.srCore.srLogger.debug("Updated scene exceptions")
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
        try:
            exceptionsList = list(set([cur_exception['show_name'] for cur_exception in [x['doc'] for x in
                                                                                        sickrage.srCore.cacheDB.db.get_many(
                                                                                            'scene_exceptions',
                                                                                            indexer_id, with_doc=True)]
                                       if cur_exception['season'] == season]))

            if not indexer_id in exceptionsCache:
                exceptionsCache[indexer_id] = {}

            exceptionsCache[indexer_id][season] = exceptionsList
        except:
            pass
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

    for cur_exception in [x['doc'] for x in sickrage.srCore.cacheDB.db.get_many('scene_exceptions', indexer_id, with_doc=True)]:
        if not cur_exception['season'] in exceptionsDict:
            exceptionsDict[cur_exception['season']] = []
        exceptionsDict[cur_exception['season']].append(cur_exception['show_name'])

    return exceptionsDict


def get_scene_seasons(indexer_id):
    """
    return a list of season numbers that have scene exceptions
    """
    exceptionsSeasonList = []

    if indexer_id not in exceptionsSeasonCache:
        dbData = [x['doc'] for x in sickrage.srCore.cacheDB.db.get_many('scene_exceptions', indexer_id, with_doc=True)]

        exceptionsSeasonList = list(set([int(x['season']) for x in dbData]))
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

    out = []

    dbData = sorted([x['doc'] for x in sickrage.srCore.cacheDB.db.all('scene_exceptions', with_doc=True)], key=lambda d: d['season'])

    # try the obvious case first
    exception_result = [x for x in dbData if x['show_name'].lower() == show_name.lower()]
    if exception_result:
        return [(int(x['indexer_id']), int(x['season'])) for x in exception_result]

    for cur_exception in dbData:
        cur_exception_name = cur_exception['show_name']
        cur_indexer_id = int(cur_exception['indexer_id'])
        cur_season = int(cur_exception['season'])

        if show_name.lower() in (
                cur_exception_name.lower(),
                sanitizeSceneName(cur_exception_name).lower().replace('.', ' ')):
            sickrage.srCore.srLogger.debug(
                "Scene exception lookup got indexer id " + str(cur_indexer_id) + ", using that")
            out.append((cur_indexer_id, cur_season))

    if out:
        return out
    return [(None, None)]


def update_scene_exceptions(indexer_id, scene_exceptions, season=-1):
    """
    Given a indexer_id, and a list of all show scene exceptions, update the db.
    """
    [sickrage.srCore.cacheDB.db.delete(x['doc']) for x in sickrage.srCore.cacheDB.db.get_many('scene_exceptions', indexer_id, with_doc=True)
     if x['doc']['season'] == season]

    sickrage.srCore.srLogger.info("Updating scene exceptions")

    # A change has been made to the scene exception list. Let's clear the cache, to make this visible
    if indexer_id in exceptionsCache:
        exceptionsCache[indexer_id] = {}
    exceptionsCache[indexer_id][season] = scene_exceptions

    for cur_exception in scene_exceptions:
        sickrage.srCore.cacheDB.db.insert({
            '_t': 'scene_exceptions',
            'indexer_id': indexer_id,
            'show_name': cur_exception,
            'season': season
        })


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
                    sickrage.srCore.srLogger.warning(
                        "XEM: Rejected entry: indexerid:{0}; names:{1}".format(indexerid, names))
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
    return [x['doc']['season'] for x in sickrage.srCore.cacheDB.db.get_many('scene_exceptions', indexer_id, with_doc=True)]


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
