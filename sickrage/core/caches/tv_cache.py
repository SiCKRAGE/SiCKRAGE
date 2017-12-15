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

import feedparser
from CodernityDB.database import RecordNotFound

import sickrage
from sickrage.core.common import Quality
from sickrage.core.exceptions import AuthException
from sickrage.core.helpers import findCertainShow, show_names
from sickrage.core.nameparser import InvalidNameException, NameParser, InvalidShowException
from sickrage.core.websession import WebSession


class TVCache(object):
    def __init__(self, provider, min_time=10, search_params=None):
        self.provider = provider
        self.providerID = self.provider.id
        self.min_time = min_time
        self.search_params = search_params or {'RSS': ['']}

    def clear(self):
        if self.shouldClearCache():
            [sickrage.app.cache_db.delete(x) for x in
             sickrage.app.cache_db.get_many('providers', self.providerID)]

    def _get_title_and_url(self, item):
        return self.provider._get_title_and_url(item)

    def _get_result_stats(self, item):
        return self.provider._get_result_stats(item)

    def _get_size(self, item):
        return self.provider._get_size(item)

    def _get_rss_data(self):
        if self.search_params:
            return {'entries': self.provider.search(self.search_params)}

    def _check_auth(self, data):
        return True

    def check_item(self, title, url):
        return True

    def update(self):
        # check if we should update
        if self.should_update():
            try:
                data = self._get_rss_data()
                if not self._check_auth(data):
                    return False

                # clear cache
                self.clear()

                # set updated
                self.last_update = datetime.datetime.today()

                [self._parseItem(item) for item in data['entries']]
            except AuthException as e:
                sickrage.app.log.warning("Authentication error: {}".format(e.message))
                return False
            except Exception as e:
                sickrage.app.log.debug(
                    "Error while searching {}, skipping: {}".format(self.provider.name, repr(e)))
                return False

        return True

    def getRSSFeed(self, url, params=None):
        try:
            if self.provider.login():
                resp = WebSession().get(url, params=params).text
                return feedparser.parse(resp)
        except Exception as e:
            sickrage.app.log.debug("RSS Error: {}".format(e.message))

        return feedparser.FeedParserDict()

    def _translateTitle(self, title):
        return '' + title.replace(' ', '.')

    def _translateLinkURL(self, url):
        return url.replace('&amp;', '&')

    def _parseItem(self, item):
        title, url = self._get_title_and_url(item)
        seeders, leechers = self._get_result_stats(item)
        size = self._get_size(item)

        self.check_item(title, url)

        if title and url:
            self.addCacheEntry(self._translateTitle(title), self._translateLinkURL(url), seeders, leechers, size)
        else:
            sickrage.app.log.debug(
                "The data returned from the " + self.provider.name + " feed is incomplete, this result is unusable")

    @property
    def last_update(self):
        try:
            dbData = sickrage.app.cache_db.get('lastUpdate', self.providerID)
            lastTime = int(dbData["time"])
            if lastTime > int(time.mktime(datetime.datetime.today().timetuple())): lastTime = 0
        except RecordNotFound:
            lastTime = 0

        return datetime.datetime.fromtimestamp(lastTime)

    @last_update.setter
    def last_update(self, toDate):
        try:
            dbData = sickrage.app.cache_db.get('lastUpdate', self.providerID)
            dbData['time'] = int(time.mktime(toDate.timetuple()))
            sickrage.app.cache_db.update(dbData)
        except RecordNotFound:
            sickrage.app.cache_db.insert({
                '_t': 'lastUpdate',
                'provider': self.providerID,
                'time': int(time.mktime(toDate.timetuple()))
            })

    @property
    def last_search(self):
        try:
            dbData = sickrage.app.cache_db.get('lastSearch', self.providerID)
            lastTime = int(dbData["time"])
            if lastTime > int(time.mktime(datetime.datetime.today().timetuple())): lastTime = 0
        except RecordNotFound:
            lastTime = 0

        return datetime.datetime.fromtimestamp(lastTime)

    @last_search.setter
    def last_search(self, toDate):
        try:
            dbData = sickrage.app.cache_db.get('lastSearch', self.providerID)
            dbData['time'] = int(time.mktime(toDate.timetuple()))
            sickrage.app.cache_db.update(dbData)
        except RecordNotFound:
            sickrage.app.cache_db.insert({
                '_t': 'lastUpdate',
                'provider': self.providerID,
                'time': int(time.mktime(toDate.timetuple()))
            })

    def should_update(self):
        if sickrage.app.developer: return True

        # if we've updated recently then skip the update
        if datetime.datetime.today() - self.last_update < datetime.timedelta(minutes=self.min_time):
            return False
        return True

    def shouldClearCache(self):
        # if daily search hasn't used our previous results yet then don't clear the cache
        if self.last_update > self.last_search:
            return False
        return True

    def addCacheEntry(self, name, url, seeders, leechers, size):
        # check for existing entry in cache
        if len([x for x in sickrage.app.cache_db.get_many('providers', self.providerID)
                if x['url'] == url]): return

        try:
            # parse release name
            parse_result = NameParser(validate_show=sickrage.app.config.enable_rss_cache_valid_shows).parse(name)
            if parse_result.series_name and parse_result.quality != Quality.UNKNOWN:
                season = parse_result.season_number if parse_result.season_number else 1
                episodes = parse_result.episode_numbers

                if season and episodes:
                    # store episodes as a seperated string
                    episodeText = "|" + "|".join(map(str, episodes)) + "|"

                    # get quality of release
                    quality = parse_result.quality

                    # get release group
                    release_group = parse_result.release_group

                    # get version
                    version = parse_result.version

                    dbData = {
                        '_t': 'providers',
                        'provider': self.providerID,
                        'name': name,
                        'season': season,
                        'episodes': episodeText,
                        'indexerid': parse_result.indexerid,
                        'url': url,
                        'time': int(time.mktime(datetime.datetime.today().timetuple())),
                        'quality': quality,
                        'release_group': release_group,
                        'version': version,
                        'seeders': seeders,
                        'leechers': leechers,
                        'size': size
                    }

                    # add to internal database
                    sickrage.app.cache_db.insert(dbData)

                    # add to external database
                    if sickrage.app.config.enable_api_providers_cache and not self.provider.private:
                        try:
                            sickrage.app.api.add_cache_result(dbData)
                        except Exception:
                            pass

                    sickrage.app.log.debug("SEARCH RESULT:[%s] ADDED TO CACHE!", name)
        except (InvalidShowException, InvalidNameException):
            pass

    def search_cache(self, ep_obj=None, manualSearch=False, downCurQuality=False):
        neededEps = {}
        dbData = []

        # get data from external database
        if sickrage.app.config.enable_api_providers_cache and not self.provider.private:
            try:
                dbData += sickrage.app.api.get_cache_results(self.providerID, ep_obj.show.indexerid)
            except Exception:
                pass

        # get data from internal database
        dbData += [x for x in sickrage.app.cache_db.get_many('providers', self.providerID)]

        # sort data by criteria
        dbData = [x for x in dbData if x['indexerid'] == ep_obj.show.indexerid and x['season'] == ep_obj.season
                  and "|" + str(ep_obj.episode) + "|" in x['episodes']] if ep_obj else dbData

        # for each cache entry
        for curResult in dbData:
            result = self.provider.getResult()

            # ignored/required words, and non-tv junk
            if not show_names.filterBadReleases(curResult["name"]):
                continue

            # get the show object, or if it's not one of our shows then ignore it
            showObj = findCertainShow(int(curResult["indexerid"]))
            if not showObj:
                continue

            # skip if provider is anime only and show is not anime
            if self.provider.anime_only and not showObj.is_anime:
                sickrage.app.log.debug("" + str(showObj.name) + " is not an anime, skiping")
                continue

            # get season and ep data (ignoring multi-eps for now)
            curSeason = int(curResult["season"])
            if curSeason == -1:
                continue

            curEp = curResult["episodes"].split("|")[1]
            if not curEp:
                continue

            curEp = int(curEp)

            result.quality = int(curResult["quality"])
            result.release_group = curResult["release_group"]
            result.version = curResult["version"]

            # if the show says we want that episode then add it to the list
            if not showObj.wantEpisode(curSeason, curEp, result.quality, manualSearch, downCurQuality):
                sickrage.app.log.info(
                    "Skipping " + curResult["name"] + " because we don't want an episode that's " +
                    Quality.qualityStrings[result.quality])
                continue

            result.episodes = [showObj.getEpisode(curSeason, curEp)]

            # build a result object
            result.name = curResult["name"]
            result.url = curResult["url"]

            sickrage.app.log.info("Found result " + result.name + " at " + result.url)

            result.show = showObj
            result.seeders = curResult.get("seeders", -1)
            result.leechers = curResult.get("leechers", -1)
            result.size = curResult.get("size", -1)
            result.content = None

            # add it to the list
            if result.episodes[0].episode not in neededEps:
                neededEps[result.episodes[0].episode] = [result]
            else:
                neededEps[result.episodes[0].episode] += [result]

        # datetime stamp this search so cache gets cleared
        self.last_search = datetime.datetime.today()

        return neededEps
