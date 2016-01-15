# Author: echel0n <sickrage.tv@gmail.com>
# URL: http://github.com/SiCKRAGETV/SickRage/
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
from sickrage.core.caches import tv_cache
from sickrage.providers import NZBProvider


class WombleProvider(NZBProvider):
    def __init__(self):
        super(WombleProvider, self).__init__("Womble's Index")
        self.public = True
        self.cache = WombleCache(self)
        self.urls = {'base_url': 'http://newshost.co.za/'}
        self.url = self.urls['base_url']


class WombleCache(tv_cache.TVCache):
    def __init__(self, provider_obj):
        tv_cache.TVCache.__init__(self, provider_obj)
        # only poll Womble's Index every 15 minutes max
        self.minTime = 15

    def updateCache(self):
        # check if we should update
        if self.shouldUpdate():
            # clear cache
            self._clearCache()

            # set updated
            self.setLastUpdate()

            cl = []
            for url in [self.provider.url + 'rss/?sec=tv-x264&fr=false',
                        self.provider.url + 'rss/?sec=tv-sd&fr=false',
                        self.provider.url + 'rss/?sec=tv-dvd&fr=false',
                        self.provider.url + 'rss/?sec=tv-hd&fr=false']:
                sickrage.LOGGER.debug("Cache update URL: %s" % url)

                for item in self.getRSSFeed(url)['entries'] or []:
                    ci = self._parseItem(item)
                    if ci is not None:
                        cl.append(ci)

            if len(cl) > 0:
                myDB = self._getDB()
                myDB.mass_action(cl)

        return True

    def _checkAuth(self, data):
        return data if data[b'feed'] and data[b'feed'][b'title'] != 'Invalid Link' else None
