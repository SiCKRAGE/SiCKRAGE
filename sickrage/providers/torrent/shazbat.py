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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import sickrage
from sickrage.core.caches import tv_cache
from sickrage.core.exceptions import AuthException
from sickrage.providers import TorrentProvider


class ShazbatProvider(TorrentProvider):
    def __init__(self):

        super(ShazbatProvider, self).__init__("Shazbat.tv",'www.shazbat.tv')

        self.supportsBacklog = False

        self.passkey = None
        self.ratio = None
        self.options = None

        self.cache = ShazbatCache(self)

        self.urls.update({
            'login': '{base_url}/login'.format(base_url=self.urls['base_url'])
        })

    def _checkAuth(self):
        if not self.passkey:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def _checkAuthFromData(self, data):
        if not self.passkey:
            self._checkAuth()
        elif not (data['entries'] and data['feed']):
            sickrage.srCore.srLogger.warning("[{}]: Invalid username or password. Check your settings".format(self.name))

        return True

    def seedRatio(self):
        return self.ratio


class ShazbatCache(tv_cache.TVCache):
    def __init__(self, provider_obj):
        tv_cache.TVCache.__init__(self, provider_obj)

        # only poll Shazbat feed every 15 minutes max
        self.minTime = 15

    def _getRSSData(self):
        rss_url = self.provider.urls['base_url'] + 'rss/recent?passkey=' + self.provider.passkey + '&fname=true'
        sickrage.srCore.srLogger.debug("Cache update URL: %s" % rss_url)

        return self.getRSSFeed(rss_url)

    def _checkAuth(self, data):
        return self.provider._checkAuthFromData(data)
