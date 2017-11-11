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

import time

from requests.auth import AuthBase
from requests.utils import dict_from_cookiejar

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.providers import TorrentProvider


class T411Provider(TorrentProvider):
    def __init__(self):
        super(T411Provider, self).__init__("T411", 'http://www.t411.al', True)

        self.urls.update({
            'search': '{base_url}/torrents/search/%s?cid=%s&limit=100'.format(**self.urls),
            'rss': '{base_url}/torrents/top/today'.format(**self.urls),
            'login': '{base_url}/auth'.format(**self.urls),
            'download': '{base_url}/torrents/download/%s'.format(**self.urls)
        })

        self.username = None
        self.password = None

        self.token = None
        self.tokenLastUpdate = None

        self.subcategories = [433, 637, 455, 639]

        self.minseed = 0
        self.minleech = 0
        self.confirmed = False

        self.cache = TVCache(self, min_time=10)

    def login(self):
        if any(dict_from_cookiejar(sickrage.app.wsession.cookies).values()):
            return True

        if self.token is not None:
            if time.time() < (self.tokenLastUpdate + 30 * 60):
                return True

        login_params = {'username': self.username,
                        'password': self.password}

        try:
            response = sickrage.app.wsession.post(self.urls['login'], data=login_params, timeout=30,
                                                         auth=T411Auth(self.token)).json()
        except Exception:
            sickrage.app.log.warning("Unable to connect to provider".format(self.name))
            return False

        if 'token' in response:
            self.token = response['token']
            self.tokenLastUpdate = time.time()
            self.uid = response['uid'].encode('ascii', 'ignore')
            return True
        else:
            sickrage.app.log.warning("Token not found in authentication response")
            return False

    def search(self, search_params, age=0, ep_obj=None):
        results = []

        if not self.login():
            return results

        for mode in search_params.keys():
            sickrage.app.log.debug("Search Mode: %s" % mode)
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: %s " % search_string)

                searchURLS = \
                    ([self.urls['search'] % (search_string, u) for u in self.subcategories], [self.urls['rss']])[
                        mode == 'RSS']
                for searchURL in searchURLS:
                    try:
                        data = sickrage.app.wsession.get(searchURL, auth=T411Auth(self.token)).json()
                        results += self.parse(data, mode)
                    except Exception:
                        sickrage.app.log.debug("No data returned from provider")

        return results

    def parse(self, data, mode):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []

        if 'torrents' not in data and mode != 'RSS':
            sickrage.app.log.debug("Data returned from provider does not contain any torrents")
            return results

        torrents = data['torrents'] if mode != 'RSS' else data

        if not torrents:
            sickrage.app.log.debug("Data returned from provider does not contain any torrents")
            return results

        for torrent in torrents:
            if mode == 'RSS' and int(torrent['category']) not in self.subcategories:
                continue

            try:
                title = torrent['name']
                torrent_id = torrent['id']
                download_url = (self.urls['download'] % torrent_id).encode('utf8')
                if not all([title, download_url]):
                    continue

                size = int(torrent['size'])
                seeders = int(torrent['seeders'])
                leechers = int(torrent['leechers'])
                verified = bool(torrent['isVerified'])

                if self.confirmed and not verified and mode != 'RSS':
                    sickrage.app.log.debug(
                        "Found result " + title + " but that doesn't seem like a verified result so I'm ignoring it")
                    continue

                item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders,
                        'leechers': leechers, 'hash': ''}

                if mode != 'RSS':
                    sickrage.app.log.debug("Found result: {}".format(title))

                results.append(item)
            except Exception:
                sickrage.app.log.error("Failed parsing provider.")

        return results


class T411Auth(AuthBase):
    """Attaches HTTP Authentication to the given Request object."""

    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = self.token
        return r
