# coding=utf-8
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE. If not, see <http://www.gnu.org/licenses/>.


from requests.compat import urlencode

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.exceptions import AuthException
from sickrage.core.helpers import try_int, convert_size
from sickrage.search_providers import TorrentProvider


class NorbitsProvider(TorrentProvider):
    def __init__(self):
        super(NorbitsProvider, self).__init__('Norbits', 'https://norbits.net', True)

        self._urls.update({
            'search': '{base_url}/api2.php?action=torrents'.format(**self._urls),
            'download': '{base_url}/download.php?'.format(**self._urls)
        })

        # custom settings
        self.custom_settings = {
            'username': '',
            'passkey': '',
            'minseed': 0,
            'minleech': 0
        }

        self.cache = TVCache(self, min_time=20)

    def _check_auth(self):
        if not self.custom_settings['username'] or not self.custom_settings['passkey']:
            raise AuthException(('Your authentication credentials for {} are '
                                 'missing, check your config.').format(self.name))

        return True

    @staticmethod
    def _check_auth_from_data(parsed_json):
        """ Check that we are authenticated. """

        if 'status' in parsed_json and 'message' in parsed_json and parsed_json.get('status') == 3:
            sickrage.app.log.warning('Invalid username or password. Check your settings')

        return True

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        """ Do the actual searching and JSON parsing"""

        results = []

        for mode in search_strings:
            sickrage.app.log.debug('Search Mode: {0}'.format(mode))
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug('Search string: {0}'.format(search_string))

                post_data = {
                    'username': self.custom_settings['username'],
                    'passkey': self.custom_settings['passkey'],
                    'category': '2',  # TV Category
                    'search': search_string,
                }

                self._check_auth()

                resp = self.session.post(self.urls['search'], data=post_data)
                if not resp or not resp.content:
                    sickrage.app.log.debug("No data returned from provider")
                    continue

                try:
                    data = resp.json()
                except ValueError:
                    sickrage.app.log.debug("No data returned from provider")
                    continue

                results += self.parse(data, mode)

        return results

    def parse(self, data, mode, **kwargs):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []

        if self._check_auth_from_data(data):
            json_items = data.get('data', '')
            if not json_items:
                sickrage.app.log.warning('Resulting JSON from provider is not correct, not parsing it')
                return results

            for item in json_items.get('torrents', []):
                try:
                    title = item.pop('name', '')
                    download_url = '{0}{1}'.format(
                        self.urls['download'], urlencode({'id': item.pop('id', ''), 'passkey': self.custom_settings['passkey']}))

                    if not all([title, download_url]):
                        continue

                    seeders = try_int(item.pop('seeders'))
                    leechers = try_int(item.pop('leechers'))
                    size = convert_size(item.pop('size', -1), -1)

                    results += [
                        {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                    ]

                    if mode != 'RSS':
                        sickrage.app.log.debug("Found result: {}".format(title))
                except Exception:
                    sickrage.app.log.error("Failed parsing provider")

        return results
