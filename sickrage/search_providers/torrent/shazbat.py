# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.exceptions import AuthException
from sickrage.search_providers import TorrentProvider


class ShazbatProvider(TorrentProvider):
    def __init__(self):
        super(ShazbatProvider, self).__init__("Shazbat.tv", 'https://www.shazbat.tv', True)

        self._urls.update({
            'login': '{base_url}/login'.format(**self._urls)
        })

        self.supports_backlog = False

        # custom settings
        self.custom_settings = {
            'passkey': ''
        }

        self.cache = ShazbatCache(self, min_time=15)

    def _check_auth(self):
        if not self.custom_settings['passkey']:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def _check_auth_from_data(self, data):
        if not self.custom_settings['passkey']:
            self._check_auth()
        elif not (data['entries'] and data['feed']):
            sickrage.app.log.warning("Invalid username or password. Check your settings")

        return True


class ShazbatCache(TVCache):
    def _get_rss_data(self):
        rss_url = self.provider.urls['base_url'] + '/rss/recent?passkey=' + self.provider.custom_settings['passkey'] + '&fname=true'
        sickrage.app.log.debug("Cache update URL: %s" % rss_url)

        return self.get_rss_feed(rss_url)

    def _check_auth(self, data):
        return self.provider._check_auth_from_data(data)
