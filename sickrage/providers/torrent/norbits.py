# coding=utf-8
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from requests.compat import urlencode

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.exceptions import AuthException
from sickrage.core.helpers import try_int, convert_size
from sickrage.providers import TorrentProvider


class NorbitsProvider(TorrentProvider):
    def __init__(self):
        super(NorbitsProvider, self).__init__('Norbits', 'https://norbits.net', True)

        self.username = None
        self.passkey = None
        self.minseed = None
        self.minleech = None

        self.urls.update({
            'search': '{base_url}/api2.php?action=torrents'.format(**self.urls),
            'download': '{base_url}/download.php?'.format(**self.urls)
        })

        self.cache = TVCache(self, min_time=20)

    def _check_auth(self):
        if not self.username or not self.passkey:
            raise AuthException(('Your authentication credentials for {} are '
                                 'missing, check your config.').format(self.name))

        return True

    @staticmethod
    def _check_auth_from_data(parsed_json):
        """ Check that we are authenticated. """

        if 'status' in parsed_json and 'message' in parsed_json and parsed_json.get('status') == 3:
            sickrage.srCore.srLogger.warning('Invalid username or password. Check your settings')

        return True

    def search(self, search_params, age=0, ep_obj=None):  # pylint: disable=too-many-locals
        """ Do the actual searching and JSON parsing"""

        results = []

        for mode in search_params:

            sickrage.srCore.srLogger.debug('Search Mode: {0}'.format(mode))

            for search_string in search_params[mode]:
                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug('Search string: {0}'.format(search_string))

                post_data = {
                    'username': self.username,
                    'passkey': self.passkey,
                    'category': '2',  # TV Category
                    'search': search_string,
                }

                self._check_auth()

                parsed_json = sickrage.srCore.srWebSession.post(self.urls['search'], data=post_data).json()
                if not parsed_json:
                    return results

                if self._check_auth_from_data(parsed_json):
                    json_items = parsed_json.get('data', '')
                    if not json_items:
                        sickrage.srCore.srLogger.error('Resulting JSON from provider is not correct, not parsing it')

                    for item in json_items.get('torrents', []):
                        title = item.pop('name', '')
                        download_url = '{0}{1}'.format(
                            self.urls['download'], urlencode({'id': item.pop('id', ''), 'passkey': self.passkey}))

                        if not all([title, download_url]):
                            continue

                        seeders = try_int(item.pop('seeders', 0))
                        leechers = try_int(item.pop('leechers', 0))

                        if seeders < self.minseed or leechers < self.minleech:
                            sickrage.srCore.srLogger.debug('Discarding torrent because it does not meet '
                                                     'the minimum seeders or leechers: {0} (S:{1} L:{2})'.format
                                                     (title, seeders, leechers))
                            continue

                        info_hash = item.pop('info_hash', '')
                        size = convert_size(item.pop('size', -1), -1)

                        item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders,
                                'leechers': leechers, 'hash': info_hash}
                        if mode != 'RSS':
                            sickrage.srCore.srLogger.debug('Found result: {0}'.format(title))

                        results.append(item)

        # Sort all the items by seeders if available
        results.sort(key=lambda k: try_int(k.get('seeders', 0)), reverse=True)

        return results

    def parse(self, data, mode):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []