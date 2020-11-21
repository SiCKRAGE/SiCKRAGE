# ##############################################################################
#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#  -
#  This file is part of SiCKRAGE.
#  -
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  -
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
# ##############################################################################


import datetime
import uuid
from time import sleep

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.enums import SearchFormat
from sickrage.core.helpers import convert_size, try_int
from sickrage.core.tv.show.helpers import find_show
from sickrage.search_providers import TorrentProvider


class RarbgProvider(TorrentProvider):
    def __init__(self):
        super(RarbgProvider, self).__init__("Rarbg", 'https://rarbg.com', False)

        self._urls.update({
            'api': 'http://torrentapi.org/pubapi_v2.php'
        })

        # custom settings
        self.custom_settings = {
            'sorting': 'seeders',
            'ranked': False,
            'minseed': 0,
            'minleech': 0
        }

        self.token = None
        self.token_expires = None

        self.app_id = 'sickrage-{}'.format(uuid.uuid1())

        self.proper_strings = ['PROPER', 'REPACK', 'REAL', 'RERIP']

        self.cache = TVCache(self)

    def login(self):
        if self.token and self.token_expires and datetime.datetime.now() < self.token_expires:
            return True

        login_params = {
            'get_token': 'get_token',
            'format': 'json',
            'app_id': self.app_id,
        }

        try:
            response = self.session.get(self.urls['api'], params=login_params, random_ua=True).json()
        except Exception as e:
            sickrage.app.log.warning("Unable to connect to provider")
            return False

        try:
            self.token = response.get('token')
        except ValueError:
            self.token = None

        self.token_expires = datetime.datetime.now() + datetime.timedelta(minutes=14) if self.token else None

        return self.token is not None

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []

        if not self.login():
            return results

        show_object = find_show(series_id, series_provider_id)
        if not show_object:
            return results

        # Search Params
        search_params = {
            'app_id': self.app_id,
            'category': 'tv',
            'min_seeders': int(self.custom_settings['minseed']),
            'min_leechers': int(self.custom_settings['minleech']),
            'limit': 100,
            'format': 'json_extended',
            'ranked': int(self.custom_settings['ranked']),
            'token': self.token,
            'sort': 'last',
            'mode': 'list',
        }

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: %s" % mode)

            if mode == 'RSS':
                search_params['search_string'] = None
                search_params['search_tvdb'] = None
            else:
                search_params['sort'] = self.custom_settings['sorting']
                search_params['mode'] = 'search'
                search_params['search_tvdb'] = series_id if not show_object.search_format == SearchFormat.COLLECTION else None

            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: %s " % search_string)
                    if self.custom_settings['ranked']:
                        sickrage.app.log.debug('Searching only ranked torrents')

                search_params['search_string'] = search_string

                # Check if token is still valid before search
                if not self.login():
                    continue

                # sleep 5 secs per request
                sleep(5)

                resp = self.session.get(self.urls['api'], params=search_params, random_ua=True)
                if not resp or not resp.content:
                    sickrage.app.log.debug("No data returned from provider")
                    continue

                try:
                    data = resp.json()
                except ValueError:
                    sickrage.app.log.debug("No data returned from provider")
                    continue

                error = data.get('error')
                error_code = data.get('error_code')
                if error:
                    # List of errors: https://github.com/rarbg/torrentapi/issues/1#issuecomment-114763312
                    if error_code == 5:
                        # 5 = Too many requests per second
                        log_level = sickrage.app.log.INFO
                    elif error_code not in (4, 8, 10, 12, 14, 20):
                        # 4 = Invalid token. Use get_token for a new one!
                        # 8, 10, 12, 14 = Cant find * in database. Are you sure this * exists?
                        # 20 = No results found
                        log_level = sickrage.app.log.WARNING
                    else:
                        log_level = sickrage.app.log.DEBUG

                    sickrage.app.log.log(log_level, '{msg} Code: {code}'.format(msg=error, code=error_code))
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

        if data.get('error'):
            if data.get('error_code') == 5:
                sickrage.app.log.info(data['error'])
            elif data.get('error_code') not in (4, 8, 10, 12, 14, 20):
                sickrage.app.log.warning(data['error'])
            else:
                sickrage.app.log.debug(data['error'])

            return results

        for item in data.get('torrent_results') or []:
            try:
                title = item['title']
                download_url = item['download']
                size = convert_size(item['size'], -1)
                seeders = item['seeders']
                leechers = item['leechers']

                if not all([title, download_url]):
                    continue

                results += [
                    {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                ]

                if mode != 'RSS':
                    sickrage.app.log.debug("Found result: {}".format(title))
            except Exception:
                sickrage.app.log.error("Failed parsing provider")

        return results
