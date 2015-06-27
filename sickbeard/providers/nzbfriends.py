# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

import urllib
import datetime

import sickbeard
import generic

from sickbeard import classes, show_name_helpers, helpers

from sickbeard import exceptions, logger
from sickbeard import scene_exceptions
from sickbeard.common import *
from sickbeard import tvcache
from lib.dateutil.parser import parse as parseDate


class Nzbfriends(generic.NZBProvider):

    def __init__(self):

        generic.NZBProvider.__init__(self, "Nzbfriends")

        self.supportsBacklog = True

        self.enabled = False

        self.cache = NzbfriendsCache(self)

        self.urls = {'base_url': 'http://nzbfriends.com/'}

        self.url = self.urls['base_url']

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'nzbfriends.png'

    def _get_season_search_strings(self, ep_obj):
        return [x for x in show_name_helpers.makeSceneSeasonSearchString(self.show, ep_obj)]

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        return [x for x in show_name_helpers.makeSceneSearchString(self.show, ep_obj)]

    def _get_title_and_url(self, item):
        title = item.get('title')
        if title:
            title = u'' + title.replace(' ', '.')

        url = item.get('link')
        if url:
            url = url.replace('&amp;', '&')
            url = url.replace('/release/', '/download/')

        return title, url

    def _doSearch(self, search_string, search_mode='eponly', epcount=0, age=0, epObj=None):
        #http://nzbindex.com/rss/?q=German&sort=agedesc&minsize=100&complete=1&max=50&more=1

        params = {
            "q": search_string.encode('utf-8')
        }

        search_url = self.url + "rss/?" + urllib.urlencode(params)

        logger.log(u"Search url: " + search_url, logger.DEBUG)

        results = []
        for curItem in self.cache.getRSSFeed(search_url, items=['entries'])['entries'] or []:
            (title, url) = self._get_title_and_url(curItem)

            if title and url:
                results.append(curItem)
            else:
                logger.log(
                    u"The data returned from the " + self.name + " is incomplete, this result is unusable",
                    logger.DEBUG)

        return results

    def findPropers(self, search_date=datetime.datetime.today()):
        results = []

        myDB = db.DBConnection()
        sqlResults = myDB.select(
            'SELECT s.show_name, e.showid, e.season, e.episode, e.status, e.airdate FROM tv_episodes AS e' +
            ' INNER JOIN tv_shows AS s ON (e.showid = s.indexer_id)' +
            ' WHERE e.airdate >= ' + str(search_date.toordinal()) +
            ' AND (e.status IN (' + ','.join([str(x) for x in Quality.DOWNLOADED]) + ')' +
            ' OR (e.status IN (' + ','.join([str(x) for x in Quality.SNATCHED]) + ')))'
        )

        if not sqlResults:
            return []

        for sqlshow in sqlResults:
            self.show = helpers.findCertainShow(sickbeard.showList, int(sqlshow["showid"]))
            if self.show:
                curEp = self.show.getEpisode(int(sqlshow["season"]), int(sqlshow["episode"]))
                searchStrings = self._get_episode_search_strings(curEp, add_string='PROPER|REPACK')
                for searchString in searchStrings:
                    for item in self._doSearch(searchString):
                        title, url = self._get_title_and_url(item)
                        if(re.match(r'.*(REPACK|PROPER).*', title, re.I)):
                             results.append(classes.Proper(title, url, datetime.datetime.today(), self.show))

        return results


class NzbfriendsCache(tvcache.TVCache):

    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # only poll Fanzub every 20 minutes max
        self.minTime = 20

    def _getRSSData(self):

        params = {

        }

        rss_url = self.provider.url + 'rss/?' + urllib.urlencode(params)

        logger.log(self.provider.name + u" cache update URL: " + rss_url, logger.DEBUG)

        return self.getRSSFeed(rss_url)

provider = Nzbfriends()
