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

import urllib
from datetime import datetime

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.classes import Proper
from sickrage.core.helpers.show_names import makeSceneSearchString, \
    makeSceneSeasonSearchString
from sickrage.providers import NZBProvider


class OmgwtfnzbsProvider(NZBProvider):
    def __init__(self):
        super(OmgwtfnzbsProvider, self).__init__("omgwtfnzbs")

        self.username = None
        self.api_key = None
        self.cache = OmgwtfnzbsCache(self)

        self.urls = {'base_url': 'https://omgwtfnzbs.org/'}
        self.url = self.urls['base_url']

        self.supportsBacklog = True

    def _checkAuth(self):

        if not self.username or not self.api_key:
            sickrage.LOGGER.warning("Invalid api key. Check your settings")

        return True

    def _checkAuthFromData(self, parsed_data, is_XML=True):

        if parsed_data is None:
            return self._checkAuth()

        if is_XML:
            # provider doesn't return xml on error
            return True
        else:
            parsedJSON = parsed_data

            if 'notice' in parsedJSON:
                description_text = parsedJSON.get('notice')

                if 'information is incorrect' in parsedJSON.get('notice'):
                    sickrage.LOGGER.warning("Invalid api key. Check your settings")

                elif '0 results matched your terms' in parsedJSON.get('notice'):
                    return True

                else:
                    sickrage.LOGGER.debug("Unknown error: %s" % description_text)
                    return False

            return True

    def _get_season_search_strings(self, ep_obj):
        return [x for x in makeSceneSeasonSearchString(self.show, ep_obj)]

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        return [x for x in makeSceneSearchString(self.show, ep_obj)]

    def _get_title_and_url(self, item):
        return (item[b'release'], item[b'getnzb'])

    def _get_size(self, item):
        try:
            size = int(item[b'sizebytes'])
        except (ValueError, TypeError, AttributeError, KeyError):
            return -1

        return size

    def _doSearch(self, search, search_mode='eponly', epcount=0, retention=0, epObj=None):

        self._checkAuth()

        params = {'user': self.username,
                  'api': self.api_key,
                  'eng': 1,
                  'catid': '19,20',  # SD,HD
                  'retention': sickrage.USENET_RETENTION,
                  'search': search}

        if retention or not params[b'retention']:
            params[b'retention'] = retention

        searchURL = 'https://api.omgwtfnzbs.org/json/?' + urllib.urlencode(params)
        sickrage.LOGGER.debug("Search string: %s" % params)
        sickrage.LOGGER.debug("Search URL: %s" % searchURL)

        parsedJSON = self.getURL(searchURL, json=True)
        if not parsedJSON:
            return []

        if self._checkAuthFromData(parsedJSON, is_XML=False):
            results = []

            for item in parsedJSON:
                if 'release' in item and 'getnzb' in item:
                    sickrage.LOGGER.debug("Found result: %s " % item.get('title'))
                    results.append(item)

            return results

        return []

    def findPropers(self, search_date=None):
        search_terms = ['.PROPER.', '.REPACK.']
        results = []

        for term in search_terms:
            for item in self._doSearch(term, retention=4):
                if 'usenetage' in item:

                    title, url = self._get_title_and_url(item)
                    try:
                        result_date = datetime.fromtimestamp(int(item[b'usenetage']))
                    except Exception:
                        result_date = None

                    if result_date:
                        results.append(Proper(title, url, result_date, self.show))

        return results


class OmgwtfnzbsCache(TVCache):
    def __init__(self, provider_obj):
        TVCache.__init__(self, provider_obj)
        self.minTime = 20

    def _get_title_and_url(self, item):
        """
        Retrieves the title and URL data from the item XML node

        item: An elementtree.ElementTree element representing the <item> tag of the RSS feed

        Returns: A tuple containing two strings representing title and URL respectively
        """

        title = item.get('title')
        if title:
            title = '' + title
            title = title.replace(' ', '.')

        url = item.get('link')
        if url:
            url = url.replace('&amp;', '&')

        return (title, url)

    def _getRSSData(self):
        params = {'user': self.provider.username,
                  'api': self.provider.api_key,
                  'eng': 1,
                  'catid': '19,20'}  # SD,HD

        rss_url = 'https://rss.omgwtfnzbs.org/rss-download.php?' + urllib.urlencode(params)

        sickrage.LOGGER.debug("Cache update URL: %s" % rss_url)

        return self.getRSSFeed(rss_url)
