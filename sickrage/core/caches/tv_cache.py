

# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
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
import time
import urllib2

from CodernityDB.database import RecordNotFound

import sickrage
from sickrage.core.common import Quality
from sickrage.core.exceptions import AuthException
from sickrage.core.helpers import findCertainShow, show_names
from sickrage.core.nameparser import InvalidNameException, InvalidShowException, NameParser
from sickrage.core.rssfeeds import getFeed


class TVCache(object):
    def __init__(self, provider, min_time=10, search_params=None):
        self.provider = provider
        self.providerID = self.provider.id
        self.min_time = min_time
        self.search_params = search_params or {'RSS': ['']}

    def clear(self):
        if self.shouldClearCache():
            [sickrage.srCore.cacheDB.db.delete(x['doc']) for x in sickrage.srCore.cacheDB.db.get_many('providers', self.providerID, with_doc=True)]

    def _get_title_and_url(self, item):
        return self.provider._get_title_and_url(item)

    def _get_rss_data(self):
        if self.search_params:
            return {'entries': self.provider.search(self.search_params)}

    def check_auth(self, data):
        return True

    def check_item(self, title, url):
        return True

    def update(self):
        # check if we should update
        if self.should_update():
            try:
                data = self._get_rss_data()
                if not self.check_auth(data):
                    return False

                # clear cache
                self.clear()

                # set updated
                self.last_update = datetime.datetime.today()

                [self._parseItem(item) for item in data['entries']]
            except AuthException as e:
                sickrage.srCore.srLogger.warning("Authentication error: {}".format(e.message))
                return False
            except Exception as e:
                sickrage.srCore.srLogger.debug(
                    "Error while searching {}, skipping: {}".format(self.provider.name, repr(e)))
                return False

        return True

    def getRSSFeed(self, url, params=None):
        handlers = []

        if sickrage.srCore.srConfig.PROXY_SETTING:
            sickrage.srCore.srLogger.debug("Using global proxy for url: " + url)
            scheme, address = urllib2.splittype(sickrage.srCore.srConfig.PROXY_SETTING)
            address = sickrage.srCore.srConfig.PROXY_SETTING if scheme else 'http://' + sickrage.srCore.srConfig.PROXY_SETTING
            handlers = [urllib2.ProxyHandler({'http': address, 'https': address})]

        return getFeed(url, params=params, handlers=handlers)

    def _translateTitle(self, title):
        return '' + title.replace(' ', '.')

    def _translateLinkURL(self, url):
        return url.replace('&amp;', '&')

    def _parseItem(self, item):
        title, url = self._get_title_and_url(item)

        self.check_item(title, url)

        if title and url:
            title = self._translateTitle(title)
            url = self._translateLinkURL(url)
            self.addCacheEntry(title, url)

        else:
            sickrage.srCore.srLogger.debug(
                "The data returned from the " + self.provider.name + " feed is incomplete, this result is unusable")

    @property
    def last_update(self):
        try:
            dbData = sickrage.srCore.cacheDB.db.get('lastUpdate', self.providerID, with_doc=True)['doc']
            lastTime = int(dbData["time"])
            if lastTime > int(time.mktime(datetime.datetime.today().timetuple())): lastTime = 0
        except RecordNotFound:
            lastTime = 0

        return datetime.datetime.fromtimestamp(lastTime)

    @last_update.setter
    def last_update(self, toDate):
        try:
            dbData = sickrage.srCore.cacheDB.db.get('lastUpdate', self.providerID, with_doc=True)['doc']
            dbData['time'] = int(time.mktime(toDate.timetuple()))
            sickrage.srCore.cacheDB.db.update(dbData)
        except RecordNotFound:
            sickrage.srCore.cacheDB.db.insert({
                '_t': 'lastUpdate',
                'provider': self.providerID,
                'time': int(time.mktime(toDate.timetuple()))
            })

    @property
    def last_search(self):
        try:
            dbData = sickrage.srCore.cacheDB.db.get('lastSearch', self.providerID, with_doc=True)['doc']
            lastTime = int(dbData["time"])
            if lastTime > int(time.mktime(datetime.datetime.today().timetuple())): lastTime = 0
        except RecordNotFound:
            lastTime = 0

        return datetime.datetime.fromtimestamp(lastTime)

    @last_search.setter
    def last_search(self, toDate):
        try:
            dbData = sickrage.srCore.cacheDB.db.get('lastSearch', self.providerID, with_doc=True)['doc']
            dbData['time'] = int(time.mktime(toDate.timetuple()))
            sickrage.srCore.cacheDB.db.update(dbData)
        except RecordNotFound:
            sickrage.srCore.cacheDB.db.insert({
                '_t': 'lastUpdate',
                'provider': self.providerID,
                'time': int(time.mktime(toDate.timetuple()))
            })

    def should_update(self):
        # if we've updated recently then skip the update
        if datetime.datetime.today() - self.last_update < datetime.timedelta(minutes=self.min_time):
            return False
        return True

    def shouldClearCache(self):
        # if daily search hasn't used our previous results yet then don't clear the cache
        if self.last_update > self.last_search:
            return False
        return True

    def addCacheEntry(self, name, url, parse_result=None, indexer_id=0):
        # check if we passed in a parsed result or should we try and create one
        if not parse_result:
            # create showObj from indexer_id if available
            showObj = None
            if indexer_id:
                showObj = findCertainShow(sickrage.srCore.SHOWLIST, indexer_id)

            try:
                myParser = NameParser(showObj=showObj)
                parse_result = myParser.parse(name)
                if not parse_result:
                    return
            except (InvalidShowException, InvalidNameException):
                sickrage.srCore.srLogger.debug("RSS ITEM:[{}] IGNORED!".format(name))
                return

        if not parse_result.series_name:
            return

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

            # get release group
            release_group = parse_result.release_group

            # get version
            version = parse_result.version

            if not len([x for x in sickrage.srCore.cacheDB.db.get_many('providers', self.providerID, with_doc=True)
                        if x['doc']['url'] == url]):
                sickrage.srCore.cacheDB.db.insert({
                    '_t': 'providers',
                    'provider': self.providerID,
                    'name': name,
                    'season': season,
                    'episodes': episodeText,
                    'indexerid': parse_result.show.indexerid,
                    'url': url,
                    'time': curTimestamp,
                    'quality': quality,
                    'release_group': release_group,
                    'version': version
                })

                sickrage.srCore.srLogger.debug("RSS ITEM:[%s] ADDED!", name)

    def list_propers(self, date=None):
        return [x['doc'] for x in sickrage.srCore.cacheDB.db.get_many('providers', self.providerID, with_doc=True)
                if ('.PROPER.' in x['doc']['name'] or '.REPACK.' in x['doc']['name'])
                and x['doc']['time'] >= str(int(time.mktime(date.timetuple())))
                and x['doc']['indexerid']]

    def search_cache(self, episode=None, manualSearch=False, downCurQuality=False):
        neededEps = {}

        if not episode:
            dbData = [x['doc'] for x in sickrage.srCore.cacheDB.db.get_many('providers', self.providerID, with_doc=True)]
        else:
            dbData = [x['doc'] for x in sickrage.srCore.cacheDB.db.get_many('providers', self.providerID, with_doc=True)
                      if x['doc']['indexerid'] == episode.show.indexerid
                      and x['doc']['season'] == episode.season
                      and "|" + str(episode.episode) + "|" in x['doc']['episodes']]

        # for each cache entry
        for curResult in dbData:
            # ignored/required words, and non-tv junk
            if not show_names.filterBadReleases(curResult["name"]):
                continue

            # get the show object, or if it's not one of our shows then ignore it
            showObj = findCertainShow(sickrage.srCore.SHOWLIST, int(curResult["indexerid"]))
            if not showObj:
                continue

            # skip if provider is anime only and show is not anime
            if self.provider.anime_only and not showObj.is_anime:
                sickrage.srCore.srLogger.debug("" + str(showObj.name) + " is not an anime, skiping")
                continue

            # get season and ep data (ignoring multi-eps for now)
            curSeason = int(curResult["season"])
            if curSeason == -1:
                continue

            curEp = curResult["episodes"].split("|")[1]
            if not curEp:
                continue

            curEp = int(curEp)

            curQuality = int(curResult["quality"])
            curReleaseGroup = curResult["release_group"]
            curVersion = curResult["version"]

            # if the show says we want that episode then add it to the list
            if not showObj.wantEpisode(curSeason, curEp, curQuality, manualSearch, downCurQuality):
                sickrage.srCore.srLogger.info(
                    "Skipping " + curResult["name"] + " because we don't want an episode that's " +
                    Quality.qualityStrings[curQuality])
                continue

            epObj = showObj.getEpisode(curSeason, curEp)

            # build a result object
            title = curResult["name"]
            url = curResult["url"]

            sickrage.srCore.srLogger.info("Found result " + title + " at " + url)

            result = self.provider.getResult([epObj])
            result.show = showObj
            result.url = url
            result.name = title
            result.quality = curQuality
            result.release_group = curReleaseGroup
            result.version = curVersion
            result.content = None
            result.size = self.provider._get_size(url)
            result.files = self.provider._get_files(url)

            # add it to the list
            if epObj not in neededEps:
                neededEps[epObj.episode] = [result]
            else:
                neededEps[epObj.episode].append(result)

        # datetime stamp this search so cache gets cleared
        self.last_search = datetime.datetime.today()

        return neededEps
