#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
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

from __future__ import unicode_literals

import time
import datetime
import itertools
import urllib2

import sickbeard
from sickbeard import db
import logging
from sickbeard import helpers
from sickbeard.common import Quality
from sickbeard.rssfeeds import getFeed
from sickbeard import show_name_helpers
from sickrage.helper.encoding import ss
from sickrage.helper.exceptions import AuthException, ex
from sickbeard.name_parser.parser import NameParser, InvalidNameException, InvalidShowException


class CacheDBConnection(db.DBConnection):
    def __init__(self, providerName):
        db.DBConnection.__init__(self, "cache.db")

        # Create the table if it's not already there
        try:
            if not self.hasTable(providerName):
                self.action(
                        "CREATE TABLE [" + providerName + "] (name TEXT, season NUMERIC, episodes TEXT, indexerid NUMERIC, url TEXT, time NUMERIC, quality TEXT, release_group TEXT)")
            else:
                sqlResults = self.select(
                    "SELECT url, COUNT(url) AS count FROM [" + providerName + "] GROUP BY url HAVING count > 1")

                for cur_dupe in sqlResults:
                    self.action("DELETE FROM [" + providerName + "] WHERE url = ?", [cur_dupe[b"url"]])

            # add unique index to prevent further dupes from happening if one does not exist
            self.action("CREATE UNIQUE INDEX IF NOT EXISTS idx_url ON [" + providerName + "] (url)")

            # add release_group column to table if missing
            if not self.hasColumn(providerName, 'release_group'):
                self.addColumn(providerName, 'release_group', "TEXT", "")

            # add version column to table if missing
            if not self.hasColumn(providerName, 'version'):
                self.addColumn(providerName, 'version', "NUMERIC", "-1")

        except Exception as e:
            if str(e) != "table [" + providerName + "] already exists":
                raise

        # Create the table if it's not already there
        try:
            if not self.hasTable('lastUpdate'):
                self.action("CREATE TABLE lastUpdate (provider TEXT, time NUMERIC)")
        except Exception as e:
            if str(e) != "table lastUpdate already exists":
                raise


class TVCache(object):
    def __init__(self, provider):
        self.provider = provider
        self.providerID = self.provider.getID()
        self.providerDB = None
        self.minTime = 10

    def _getDB(self):
        # init provider database if not done already
        if not self.providerDB:
            self.providerDB = CacheDBConnection(self.providerID)

        return self.providerDB

    def _clearCache(self):
        if self.shouldClearCache():
            myDB = self._getDB()
            myDB.action("DELETE FROM [" + self.providerID + "] WHERE 1")

    def _get_title_and_url(self, item):
        return self.provider._get_title_and_url(item)

    def _getRSSData(self):
        return None

    def _checkAuth(self, data):
        return True

    def _checkItemAuth(self, title, url):
        return True

    def updateCache(self):
        # check if we should update
        if self.shouldUpdate():
            try:
                data = self._getRSSData()
                if not self._checkAuth(data):
                    return False

                # clear cache
                self._clearCache()

                # set updated
                self.setLastUpdate()

                cl = []
                for item in data[b'entries']:
                    ci = self._parseItem(item)
                    if ci is not None:
                        cl.append(ci)

                if len(cl) > 0:
                    myDB = self._getDB()
                    myDB.mass_action(cl)
            except AuthException as e:
                logging.error("Authentication error: {}".format(ex(e)))
                return False
            except Exception as e:
                logging.debug("Error while searching {}, skipping: {}".format(self.provider.name, repr(e)))
                return False

        return True

    def getRSSFeed(self, url):
        handlers = []

        if sickbeard.PROXY_SETTING:
            logging.debug("Using global proxy for url: " + url)
            scheme, address = urllib2.splittype(sickbeard.PROXY_SETTING)
            address = sickbeard.PROXY_SETTING if scheme else 'http://' + sickbeard.PROXY_SETTING
            handlers = [urllib2.ProxyHandler({'http': address, 'https': address})]
            self.provider.headers.update({'Referer': address})
        elif 'Referer' in self.provider.headers:
            self.provider.headers.pop('Referer')

        return getFeed(url, request_headers=self.provider.headers, handlers=handlers)

    def _translateTitle(self, title):
        return '' + title.replace(' ', '.')

    def _translateLinkURL(self, url):
        return url.replace('&amp;', '&')

    def _parseItem(self, item):
        title, url = self._get_title_and_url(item)

        self._checkItemAuth(title, url)

        if title and url:
            title = self._translateTitle(title)
            url = self._translateLinkURL(url)

            logging.debug("Attempting to add item to cache: " + title)
            return self._addCacheEntry(title, url)

        else:
            logging.debug(
                    "The data returned from the " + self.provider.name + " feed is incomplete, this result is unusable")

        return False

    def _getLastUpdate(self):
        myDB = self._getDB()
        sqlResults = myDB.select("SELECT time FROM lastUpdate WHERE provider = ?", [self.providerID])

        if sqlResults:
            lastTime = int(sqlResults[0][b"time"])
            if lastTime > int(time.mktime(datetime.datetime.today().timetuple())):
                lastTime = 0
        else:
            lastTime = 0

        return datetime.datetime.fromtimestamp(lastTime)

    def _getLastSearch(self):
        myDB = self._getDB()
        sqlResults = myDB.select("SELECT time FROM lastSearch WHERE provider = ?", [self.providerID])

        if sqlResults:
            lastTime = int(sqlResults[0][b"time"])
            if lastTime > int(time.mktime(datetime.datetime.today().timetuple())):
                lastTime = 0
        else:
            lastTime = 0

        return datetime.datetime.fromtimestamp(lastTime)

    def setLastUpdate(self, toDate=None):
        if not toDate:
            toDate = datetime.datetime.today()

        myDB = self._getDB()
        myDB.upsert("lastUpdate",
                    {'time': int(time.mktime(toDate.timetuple()))},
                    {'provider': self.providerID})

    def setLastSearch(self, toDate=None):
        if not toDate:
            toDate = datetime.datetime.today()

        myDB = self._getDB()
        myDB.upsert("lastSearch",
                    {'time': int(time.mktime(toDate.timetuple()))},
                    {'provider': self.providerID})

    lastUpdate = property(_getLastUpdate)
    lastSearch = property(_getLastSearch)

    def shouldUpdate(self):
        # if we've updated recently then skip the update
        if datetime.datetime.today() - self.lastUpdate < datetime.timedelta(minutes=self.minTime):
            logging.debug(
                "Last update was too soon, using old cache: " + str(self.lastUpdate) + ". Updated less then " + str(
                    self.minTime) + " minutes ago")
            return False

        return True

    def shouldClearCache(self):
        # if daily search hasn't used our previous results yet then don't clear the cache
        if self.lastUpdate > self.lastSearch:
            return False

        return True

    def _addCacheEntry(self, name, url, parse_result=None, indexer_id=0):

        # check if we passed in a parsed result or should we try and create one
        if not parse_result:

            # create showObj from indexer_id if available
            showObj = None
            if indexer_id:
                showObj = helpers.findCertainShow(sickbeard.showList, indexer_id)

            try:
                myParser = NameParser(showObj=showObj)
                parse_result = myParser.parse(name)
            except InvalidNameException:
                logging.debug("Unable to parse the filename " + name + " into a valid episode")
                return None
            except InvalidShowException:
                logging.debug("Unable to parse the filename " + name + " into a valid show")
                return None

            if not parse_result or not parse_result.series_name:
                return None

        # if we made it this far then lets add the parsed result to cache for usager later on
        season = parse_result.season_number if parse_result.season_number else 1
        episodes = parse_result.episode_numbers

        if season and episodes:
            # store episodes as a seperated string
            episodeText = "|" + "|".join(map(str, episodes)) + "|"

            # get the current timestamp
            curTimestamp = int(time.mktime(datetime.datetime.today().timetuple()))

            # get quality of release
            quality = parse_result.quality

            name = ss(name)

            # get release group
            release_group = parse_result.release_group

            # get version
            version = parse_result.version

            logging.debug("Added RSS item: [" + name + "] to cache: [" + self.providerID + "]")

            return [
                "INSERT OR IGNORE INTO [" + self.providerID + "] (name, season, episodes, indexerid, url, time, quality, release_group, version) VALUES (?,?,?,?,?,?,?,?,?)",
                [name, season, episodeText, parse_result.show.indexerid, url, curTimestamp, quality, release_group,
                 version]]

    def searchCache(self, episode, manualSearch=False, downCurQuality=False):
        neededEps = self.findNeededEpisodes(episode, manualSearch, downCurQuality)
        return neededEps[episode] if episode in neededEps else []

    def listPropers(self, date=None):
        myDB = self._getDB()
        sql = "SELECT * FROM [" + self.providerID + "] WHERE name LIKE '%.PROPER.%' OR name LIKE '%.REPACK.%'"

        if date != None:
            sql += " AND time >= " + str(int(time.mktime(date.timetuple())))

        propers_results = myDB.select(sql)
        return [x for x in propers_results if x[b'indexerid']]

    def findNeededEpisodes(self, episode, manualSearch=False, downCurQuality=False):
        neededEps = {}
        cl = []

        myDB = self._getDB()
        if not episode:
            sqlResults = myDB.select("SELECT * FROM [" + self.providerID + "]")
        elif type(episode) != list:
            sqlResults = myDB.select(
                    "SELECT * FROM [" + self.providerID + "] WHERE indexerid = ? AND season = ? AND episodes LIKE ?",
                    [episode.show.indexerid, episode.season, "%|" + str(episode.episode) + "|%"])
        else:
            for epObj in episode:
                cl.append([
                    "SELECT * FROM [" + self.providerID + "] WHERE indexerid = ? AND season = ? AND episodes LIKE ? AND quality IN (" + ",".join(
                            [str(x) for x in epObj.wantedQuality]) + ")",
                    [epObj.show.indexerid, epObj.season, "%|" + str(epObj.episode) + "|%"]])

            sqlResults = myDB.mass_action(cl, fetchall=True)
            sqlResults = list(itertools.chain(*sqlResults))

        # for each cache entry
        for curResult in sqlResults:
            # ignored/required words, and non-tv junk
            if not show_name_helpers.filterBadReleases(curResult[b"name"]):
                continue

            # get the show object, or if it's not one of our shows then ignore it
            showObj = helpers.findCertainShow(sickbeard.showList, int(curResult[b"indexerid"]))
            if not showObj:
                continue

            # skip if provider is anime only and show is not anime
            if self.provider.anime_only and not showObj.is_anime:
                logging.debug("" + str(showObj.name) + " is not an anime, skiping")
                continue

            # get season and ep data (ignoring multi-eps for now)
            curSeason = int(curResult[b"season"])
            if curSeason == -1:
                continue

            curEp = curResult[b"episodes"].split("|")[1]
            if not curEp:
                continue

            curEp = int(curEp)

            curQuality = int(curResult[b"quality"])
            curReleaseGroup = curResult[b"release_group"]
            curVersion = curResult[b"version"]

            # if the show says we want that episode then add it to the list
            if not showObj.wantEpisode(curSeason, curEp, curQuality, manualSearch, downCurQuality):
                logging.info("Skipping " + curResult[b"name"] + " because we don't want an episode that's " +
                            Quality.qualityStrings[curQuality])
                continue

            epObj = showObj.getEpisode(curSeason, curEp)

            # build a result object
            title = curResult[b"name"]
            url = curResult[b"url"]

            logging.info("Found result " + title + " at " + url)

            result = self.provider.getResult([epObj])
            result.show = showObj
            result.url = url
            result.name = title
            result.quality = curQuality
            result.release_group = curReleaseGroup
            result.version = curVersion
            result.content = None

            # add it to the list
            if epObj not in neededEps:
                neededEps[epObj] = [result]
            else:
                neededEps[epObj].append(result)

        # datetime stamp this search so cache gets cleared
        self.setLastSearch()

        return neededEps
