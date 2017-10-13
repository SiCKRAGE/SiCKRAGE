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

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers.show_names import makeSceneSearchString, \
    makeSceneSeasonSearchString
from sickrage.providers import NZBProvider


class OmgwtfnzbsProvider(NZBProvider):
    def __init__(self):
        super(OmgwtfnzbsProvider, self).__init__("omgwtfnzbs", 'http://omgwtfnzbs.me', True)

        self.username = None
        self.api_key = None
        self.cache = OmgwtfnzbsCache(self, min_time=20)

        self.urls.update({
            'api': 'api.{base_url}/json'.format(**self.urls),
            'rss': 'rss.{base_url}/rss-download.php'.format(**self.urls)
        })

    def _check_auth(self):
        if not self.username or not self.api_key:
            sickrage.srCore.srLogger.warning("Invalid api key. Check your settings")

        return True

    def _check_auth_from_data(self, parsed_data, is_XML=True):
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

    def search(self, search_strings, age=0, ep_obj=None):
        results = []

        if not self._check_auth():
            return results

        search_params = {
            'user': self.username,
            'api': self.api_key,
            'eng': 1,
            'catid': '19,20',  # SD,HD
            'retention': sickrage.srCore.srConfig.USENET_RETENTION
        }

        for mode in search_strings:
            sickrage.srCore.srLogger.debug('Search Mode: {}'.format(mode))
            for search_string in search_strings[mode]:
                search_params['search'] = search_string
                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug('Search string: {}'.format(search_string))

                data = sickrage.srCore.srWebSession.get(self.urls['api'], params=search_params).json()
                if not data:
                    sickrage.srCore.srLogger.debug('No data returned from provider')
                    continue

                if not self._check_auth_from_data(data, is_XML=False):
                    continue

                for item in data:
                    if not self._get_title_and_url(item):
                        continue

                    sickrage.srCore.srLogger.debug('Found result: {}'.format(item.get('release')))
                    results.append(item)

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

        return title, url

    def _get_rss_data(self):
        search_params = {
            'user': self.provider.username,
            'api': self.provider.api_key,
            'eng': 1,
            'catid': '19,20'  # SD,HD
        }

        return self.getRSSFeed(self.provider.urls['rss'], params=search_params)
