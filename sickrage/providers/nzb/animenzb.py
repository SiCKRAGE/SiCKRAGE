#!/usr/bin/env python2

# Author: echel0n <sickrage.tv@gmail.com>
# URL: http://www.github.com/sickragetv/sickrage/
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
import urllib

import sickrage
from sickrage.core.caches import tv_cache
from sickrage.core.classes import Proper
from sickrage.core.helpers import show_names
from sickrage.providers import NZBProvider


class AnimeNZBProvider(NZBProvider):
    def __init__(self):
        super(AnimeNZBProvider, self).__init__("AnimeNZB")

        self.supportsBacklog = False
        self.public = True
        self.supportsAbsoluteNumbering = True
        self.anime_only = True

        self.cache = animenzbCache(self)

        self.urls = {'base_url': 'http://animenzb.com//'}

        self.url = self.urls['base_url']

    def _get_season_search_strings(self, ep_obj):
        return [x for x in show_names.makeSceneSeasonSearchString(self.show, ep_obj)]

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        return [x for x in show_names.makeSceneSearchString(self.show, ep_obj)]

    def _doSearch(self, search_string, search_mode='eponly', epcount=0, age=0, epObj=None):

        sickrage.LOGGER.debug("Search string: %s " % search_string)

        if self.show and not self.show.is_anime:
            return []

        params = {
            "cat": "anime",
            "q": search_string.encode('utf-8'),
            "max": "100"
        }

        searchURL = self.url + "rss?" + urllib.urlencode(params)
        sickrage.LOGGER.debug("Search URL: %s" % searchURL)
        results = []
        for curItem in self.cache.getRSSFeed(searchURL)['entries'] or []:
            (title, url) = self._get_title_and_url(curItem)

            if title and url:
                results.append(curItem)
                sickrage.LOGGER.debug("Found result: %s " % title)

        # For each search mode sort all the items by seeders if available if available
        results.sort(key=lambda tup: tup[0], reverse=True)

        return results

    def findPropers(self, date=None):

        results = []

        for item in self._doSearch("v2|v3|v4|v5"):

            (title, url) = self._get_title_and_url(item)

            if item.has_key('published_parsed') and item[b'published_parsed']:
                result_date = item.published_parsed
                if result_date:
                    result_date = datetime.datetime(*result_date[0:6])
            else:
                continue

            if not date or result_date > date:
                search_result = Proper(title, url, result_date, self.show)
                results.append(search_result)

        return results


class animenzbCache(tv_cache.TVCache):
    def __init__(self, provider_obj):
        tv_cache.TVCache.__init__(self, provider_obj)

        # only poll animenzb every 20 minutes max
        self.minTime = 20

    def _getRSSData(self):
        params = {
            "cat": "anime".encode('utf-8'),
            "max": "100".encode('utf-8')
        }

        rss_url = self.provider.url + 'rss?' + urllib.urlencode(params)

        return self.getRSSFeed(rss_url)
