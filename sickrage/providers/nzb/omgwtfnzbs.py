

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
import urllib

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.classes import Proper
from sickrage.core.helpers.show_names import makeSceneSearchString, \
    makeSceneSeasonSearchString
from sickrage.providers import NZBProvider


class OmgwtfnzbsProvider(NZBProvider):
    def __init__(self):
        super(OmgwtfnzbsProvider, self).__init__("omgwtfnzbs", 'omgwtfnzbs.me', True)

        self.username = None
        self.api_key = None
        self.cache = OmgwtfnzbsCache(self, min_time=20)

        self.urls.update({
            'search': 'api.{base_url}/json/?catid=19,20'.format(base_url=self.urls['base_url']),
            'rss': 'rss.{base_url}/rss-download.php?catid=19,20'.format(base_url=self.urls['base_url'])
        })

        self.supports_backlog = True

    def _check_auth(self):
        if not self.username or not self.api_key:
            sickrage.srCore.srLogger.warning("Invalid api key. Check your settings")

        return True

    def _checkAuthFromData(self, parsed_data, is_XML=True):
        if parsed_data is None:
            return self._check_auth()

        if is_XML:
            # provider doesn't return xml on error
            return True

        if 'notice' in parsed_data:
            description_text = parsed_data.get('notice')

            if 'information is incorrect' in parsed_data.get('notice'):
                sickrage.srCore.srLogger.warning("Invalid api key. Check your settings")
            elif '0 results matched your terms' in parsed_data.get('notice'):
                sickrage.srCore.srLogger.debug("Unknown error: %s" % description_text)
            return False

        return True

    def _get_season_search_strings(self, ep_obj):
        return [x for x in makeSceneSeasonSearchString(self.show, ep_obj)]

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        return [x for x in makeSceneSearchString(self.show, ep_obj)]

    def _get_title_and_url(self, item):
        return item['release'], item['getnzb']

    def _get_size(self, item):
        try:
            size = int(item['sizebytes'])
        except (ValueError, TypeError, AttributeError, KeyError):
            return -1

        return size

    def search(self, search, search_mode='eponly', epcount=0, retention=0, epObj=None):
        results = []
        if not self._check_auth():
            return results

        params = {
            'user': self.username,
            'api': self.api_key,
            'eng': 1,
            'retention': sickrage.srCore.srConfig.USENET_RETENTION,
            'search': search
        }

        sickrage.srCore.srLogger.debug("Search url: %s?%s" % (self.urls['search'], urllib.urlencode(params)))

        try:
            parsedJSON = sickrage.srCore.srWebSession.get(self.urls['search'], params=params).json()
        except Exception:
            return []

        if self._checkAuthFromData(parsedJSON, is_XML=False):
            for item in parsedJSON:
                if not self._get_title_and_url(item):
                    continue

                sickrage.srCore.srLogger.debug("Found result: %s " % item.get('release'))
                results.append(item)

        return results

    def find_propers(self, search_date=None):
        search_terms = ['.PROPER.', '.REPACK.']
        results = []

        for term in search_terms:
            for item in self.search(term, retention=4):
                if 'usenetage' in item:

                    title, url = self._get_title_and_url(item)
                    try:
                        result_date = datetime.datetime.fromtimestamp(int(item['usenetage']))
                    except Exception:
                        result_date = None

                    if result_date:
                        results.append(Proper(title, url, result_date, self.show))

        return results


class OmgwtfnzbsCache(TVCache):
    def _get_title_and_url(self, item):
        """
        Retrieves the title and URL data from the item XML node

        item: An elementtree.ElementTree element representing the <item> tag of the RSS feed

        Returns: A tuple containing two strings representing title and URL respectively
        """

        title = item.get('title', '').replace(' ', '.')
        url = item.get('link', '').replace('&amp;', '&')

        return (title, url)

    def _get_rss_data(self):
        params = {
            'user': self.provider.username,
            'api': self.provider.api_key,
            'eng': 1
        }

        return self.getRSSFeed(self.provider.urls['rss'], params=params)
