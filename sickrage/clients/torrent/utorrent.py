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

import re

import sickrage
from sickrage.clients import TorrentClient
from sickrage.core.tv.show.helpers import find_show


class uTorrentAPI(TorrentClient):
    def __init__(self, host=None, username=None, password=None):
        super(uTorrentAPI, self).__init__('uTorrent', host, username, password)
        self.url = self.host + 'gui/'

    def _request(self, method='get', data=None, params=None, *args, **kwargs):
        # Workaround for uTorrent 2.2.1
        # Need a odict but only supported in 2.7+ and sickrage is 2.6+
        ordered_params = {'token': self.auth}

        for k, v in params.items() or {}:
            ordered_params.update({k: v})

        return super(uTorrentAPI, self)._request(method=method, params=ordered_params, data=data, *args, **kwargs)

    def _get_auth(self):
        self.auth = None

        self.response = self.session.get(self.url + 'token.html',
                                         timeout=120, auth=(self.username, self.password),
                                         verify=bool(sickrage.app.config.torrent.verify_cert))

        if self.response and self.response.text:
            auth_match = re.findall("<div.*?>(.*?)</", self.response.text)
            if auth_match:
                self.auth = auth_match[0]
                self.cookies = self.response.cookies

        return self.auth

    def _add_torrent_uri(self, result):
        params = {'action': 'add-url', 's': result.url[:1024]}
        return self._request(params=params, cookies=self.cookies)

    def _add_torrent_file(self, result):
        params = {'action': 'add-file'}
        files = {'torrent_file': (result.name + '.torrent', result.content)}
        return self._request(method='post', params=params, files=files, cookies=self.cookies)

    def _set_torrent_label(self, result):
        label = sickrage.app.config.torrent.label
        show_object = find_show(result.series_id, result.series_provider_id)

        if show_object.is_anime:
            label = sickrage.app.config.torrent.label_anime

        params = {'action': 'setprops',
                  'hash': result.hash,
                  's': 'label',
                  'v': label}

        return self._request(params=params, cookies=self.cookies)

    def _set_torrent_ratio(self, result):
        ratio = None
        if result.ratio:
            ratio = result.ratio

        if ratio:
            params = {'action': 'setprops',
                      'hash': result.hash,
                      's': 'seed_override',
                      'v': '1'}

            if self._request(params=params, cookies=self.cookies):
                params = {'action': 'setprops',
                          'hash': result.hash,
                          's': 'seed_ratio',
                          'v': float(ratio) * 10}

                return self._request(params=params, cookies=self.cookies)
            else:
                return False

        return True

    def _set_torrent_seed_time(self, result):
        if sickrage.app.config.torrent.seed_time:
            time = 3600 * float(sickrage.app.config.torrent.seed_time)
            params = {'action': 'setprops',
                      'hash': result.hash,
                      's': 'seed_override',
                      'v': '1'}

            if self._request(params=params, cookies=self.cookies):
                params = {'action': 'setprops',
                          'hash': result.hash,
                          's': 'seed_time',
                          'v': time}

                return self._request(params=params, cookies=self.cookies)
            else:
                return False
        else:
            return True

    def _set_torrent_priority(self, result):
        if result.priority == 1:
            params = {'action': 'queuetop', 'hash': result.hash}
            return self._request(params=params, cookies=self.cookies)
        else:
            return True

    def _set_torrent_pause(self, result):
        if sickrage.app.config.torrent.paused:
            params = {'action': 'pause', 'hash': result.hash}
        else:
            params = {'action': 'start', 'hash': result.hash}

        return self._request(params=params, cookies=self.cookies)
