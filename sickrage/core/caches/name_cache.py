# Author: echel0n <sickrage.tv@gmail.com>
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
import threading
import time

import sickrage
from sickrage.core.databases import cache_db
from sickrage.core.helpers import full_sanitizeSceneName
from sickrage.core.scene_exceptions import retrieve_exceptions, get_scene_seasons, get_scene_exceptions


class nameCache(object):
    def __init__(self, *args, **kwargs):
        self.name = "NAMECACHE"
        self.amActive = False
        self.lastUpdate = datetime.datetime.fromtimestamp(int(time.mktime(datetime.datetime.today().timetuple())))
        self.minTime = sickrage.NAMECACHE_FREQ
        self.cache = {}

    def run(self, force=False):
        """
        Runs the postprocessor
        :param force: Forces run (reserved for future use)
        :return: Returns when done without a return state/code
        """

        if self.amActive:
            return

        self.amActive = True

        origThreadName = threading.currentThread().getName()

        threading.currentThread().setName(self.name)
        self.buildNameCache()
        threading.currentThread().setName(origThreadName)

        self.amActive = False

    def shouldUpdate(self):
        # if we've updated recently then skip the update
        if datetime.datetime.today() - self.lastUpdate < datetime.timedelta(minutes=self.minTime):
            return True

        sickrage.LOGGER.debug(
            "Last update was too soon, using old name cache: " + str(self.lastUpdate) + ". Updated less then " + str(
                self.minTime) + " minutes ago")

    def addNameToCache(self, name, indexer_id=0):
        """
        Adds the show & tvdb id to the scene_names table in cache.db.

        :param name: The show name to cache
        :param indexer_id: the TVDB id that this show should be cached with (can be None/0 for unknown)
        """
        # standardize the name we're using to account for small differences in providers
        name = full_sanitizeSceneName(name)
        if name not in self.cache:
            self.cache[name] = int(indexer_id)
            cache_db.CacheDB().action("INSERT OR REPLACE INTO scene_names (indexer_id, name) VALUES (?, ?)",
                                      [indexer_id, name])

    def retrieveNameFromCache(self, name):
        """
        Looks up the given name in the scene_names table in cache.db.

        :param name: The show name to look up.
        :return: the TVDB id that resulted from the cache lookup or None if the show wasn't found in the cache
        """
        name = full_sanitizeSceneName(name)
        if name in self.cache:
            return int(self.cache[name])

    def clearCache(self, indexerid=0):
        """
        Deletes all "unknown" entries from the cache (names with indexer_id of 0).
        """
        cache_db.CacheDB().action("DELETE FROM scene_names WHERE indexer_id = ? OR indexer_id = ?", (indexerid, 0))

        toRemove = [key for key, value in self.cache.iteritems() if value == 0 or value == indexerid]
        for key in toRemove:
            del self.cache[key]

    def saveNameCacheToDb(self):
        """Commit cache to database file"""

        for name, indexer_id in self.cache.items():
            cache_db.CacheDB().action("INSERT OR REPLACE INTO scene_names (indexer_id, name) VALUES (?, ?)",
                                      [indexer_id, name])

    def buildNameCache(self, show=None):
        """Build internal name cache

        :param show: Specify show to build name cache for, if None, just do all shows
        """

        if self.shouldUpdate():
            if not show:
                retrieve_exceptions()
                for show in sickrage.showList:
                    sickrage.LOGGER.info("Building internal name cache for all shows")
                    self.buildNameCache(show)
            else:
                self.lastUpdate = datetime.datetime.fromtimestamp(
                        int(time.mktime(datetime.datetime.today().timetuple()))
                )

                sickrage.LOGGER.debug("Building internal name cache for [{}]".format(show.name))
                self.clearCache(show.indexerid)
                for curSeason in [-1] + get_scene_seasons(show.indexerid):
                    for name in list(set(get_scene_exceptions(
                            show.indexerid, season=curSeason) + [show.name])):

                        name = full_sanitizeSceneName(name)
                        if name not in self.cache:
                            self.cache[name] = int(show.indexerid)

                sickrage.LOGGER.debug("Internal name cache for [{}] set to: [{}]".format(
                        show.name, [key for key, value in self.cache.items() if value == show.indexerid][0]))
