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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import urllib
import re

try:
    import xml.etree.cElementTree as etree
except ImportError:
    import elementtree.ElementTree as etree

import sickbeard
import generic

from sickbeard.common import Quality
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import helpers


class EZRSSProvider(generic.TorrentProvider):
    def __init__(self):

        self.urls = {'base_url': 'https://www.ezrss.it/'}

        self.url = self.urls['base_url']

        generic.TorrentProvider.__init__(self, "EZRSS")

        self.supportsBacklog = True
        self.enabled = False
        self.ratio = None

        self.cache = EZRSSCache(self)

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'ezrss.png'

    def getQuality(self, item, anime=False):

        try:
            quality = Quality.sceneQuality(item.filename, anime)
        except:
            quality = Quality.UNKNOWN

        return quality

    def findSearchResults(self, show, episodes, search_mode, manualSearch=False):

        self.show = show

        results = {}

        if show.air_by_date or show.sports:
            logger.log(self.name + u" doesn't support air-by-date or sports backloging because of limitations on their RSS search.",
                       logger.WARNING)
            return results

        results = generic.TorrentProvider.findSearchResults(self, show, episodes, search_mode, manualSearch)

        return results

    def _get_season_search_strings(self, ep_obj):

        params = {}

        params['show_name'] = helpers.sanitizeSceneName(self.show.name, ezrss=True).replace('.', ' ').encode('utf-8')

        if ep_obj.show.air_by_date or ep_obj.show.sports:
            params['season'] = str(ep_obj.airdate).split('-')[0]
        elif ep_obj.show.anime:
            params['season'] = "%d" % ep_obj.scene_absolute_number
        else:
            params['season'] = ep_obj.scene_season

        return [params]

    def _get_episode_search_strings(self, ep_obj, add_string=''):

        params = {}

        if not ep_obj:
            return params

        params['show_name'] = helpers.sanitizeSceneName(self.show.name, ezrss=True).replace('.', ' ').encode('utf-8')

        if self.show.air_by_date or self.show.sports:
            params['date'] = str(ep_obj.airdate)
        elif self.show.anime:
            params['episode'] = "%i" % int(ep_obj.scene_absolute_number)
        else:
            params['season'] = ep_obj.scene_season
            params['episode'] = ep_obj.scene_episode

        return [params]

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0):

        params = {"mode": "rss"}

        if search_params:
            params.update(search_params)

        search_url = self.url + 'search/index.php?' + urllib.urlencode(params)

        logger.log(u"Search string: " + search_url, logger.DEBUG)

        results = []
        for curItem in self.cache.getRSSFeed(search_url, items=['entries'])['entries'] or []:

            (title, url) = self._get_title_and_url(curItem)

            if title and url:
                logger.log(u"RSS Feed provider: [" + self.name + "] Attempting to add item to cache: " + title, logger.DEBUG)
                results.append(curItem)

        return results

    def _get_title_and_url(self, item):
        (title, url) = generic.TorrentProvider._get_title_and_url(self, item)

        try:
            new_title = self._extract_name_from_filename(item.filename)
        except:
            new_title = None

        if new_title:
            title = new_title
            logger.log(u"Extracted the name " + title + " from the torrent link", logger.DEBUG)

        return (title, url)

    def _extract_name_from_filename(self, filename):
        name_regex = '(.*?)\.?(\[.*]|\d+\.TPB)\.torrent$'
        logger.log(u"Comparing " + name_regex + " against " + filename, logger.DEBUG)
        match = re.match(name_regex, filename, re.I)
        if match:
            return match.group(1)
        return None

    def seedRatio(self):
        return self.ratio


class EZRSSCache(tvcache.TVCache):
    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # only poll EZRSS every 15 minutes max
        self.minTime = 15

    def _getRSSData(self):

        rss_url = self.provider.url + 'feed/'
        logger.log(self.provider.name + " cache update URL: " + rss_url, logger.DEBUG)

        return self.getRSSFeed(rss_url)

provider = EZRSSProvider()
