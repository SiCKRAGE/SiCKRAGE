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

import sickrage
from sickrage.core.caches import tv_cache
from sickrage.providers import NZBProvider


class WombleProvider(NZBProvider):
    def __init__(self):
        super(WombleProvider, self).__init__("Womble's Index", 'newshost.co.za', False)

        self.cache = WombleCache(self, min_time=15)


class WombleCache(tv_cache.TVCache):
    def update(self):
        # check if we should update
        if self.should_update():
            # clear cache
            self.clear()

            # set updated
            self.last_update = datetime.datetime.today()

            for url in [self.provider.urls['base_url'] + '/rss/?sec=tv-x264&fr=false',
                        self.provider.urls['base_url'] + '/rss/?sec=tv-sd&fr=false',
                        self.provider.urls['base_url'] + '/rss/?sec=tv-dvd&fr=false',
                        self.provider.urls['base_url'] + '/rss/?sec=tv-hd&fr=false']:
                sickrage.srCore.srLogger.debug("Cache update URL: %s" % url)

                for item in self.getRSSFeed(url)['entries'] or []:
                    self._parseItem(item)

        return True

    def check_auth(self, data):
        return data if data['feed'] and data['feed']['title'] != 'Invalid Link' else None
