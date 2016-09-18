# Author: echel0n <echel0n@sickrage.ca>
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
        super(WombleProvider, self).__init__("Womble's Index", 'newshost.co.za', False)

        self.urls.update({'rss': '{base_url}/rss'.format(base_url=self.urls['base_url'])})

        self.cache = WombleCache(self)


class WombleCache(tv_cache.TVCache):
    def __init__(self, provider_obj):
        tv_cache.TVCache.__init__(self, provider_obj)
        # only poll Womble's Index every 15 minutes max
        self.minTime = 15

    def updateCache(self):
        # check if we should update
        if self.should_update():
            # clear cache
            self._clear_cache()

            # set updated
            self.setLastUpdate()

            cl = []
            search_params_list = [{'sec': 'tv-x264'}, {'sec': 'tv-hd'}, {'sec': 'tv-sd'}, {'sec': 'tv-dvd'}]
            for search_params in search_params_list:
                search_params.update({'fr': 'false'})

                sickrage.srCore.srLogger.debug("Cache update URL: %s" % self.provider.urls['rss'])

                for item in self.getRSSFeed(self.provider.urls['rss'], params=search_params)['entries'] or []:
                    ci = self._parse_item(item)
                    if ci is not None:
                        cl.append(ci)

            if len(cl) > 0:
                self._get_db().mass_action(cl)
                del cl  # cleanup

        return True

    def _check_auth(self, data):
        return data if data['feed'] and data['feed']['title'] != 'Invalid Link' else None
