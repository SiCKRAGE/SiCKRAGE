# -*- coding: latin-1 -*-
# Author: adaur <adaur.underground@gmail.com>
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
from sickrage.core.helpers import try_int
from sickrage.providers import TorrentProvider


class XthorProvider(TorrentProvider):
    def __init__(self):
        super(XthorProvider, self).__init__("Xthor", "https://xthor.tk", True)

        self.urls.update({
            'search': "https://api.xthor.tk"
        })

        self.passkey = None

        self.minseed = None
        self.minleech = None
        self.confirmed = False
        self.freeleech = None

        self.subcategories = [433, 637, 455, 639]

        self.cache = TVCache(self)

    def _check_auth(self):
        if self.passkey:
            return True

        sickrage.app.log.warning(
            'Your authentication credentials for {} are missing, check your config.'.format(self.name))

        return False

    def search(self, search_strings, age=0, show_id=None, season=None, episode=None, **kwargs):
        results = []

        # check for auth
        if not self._check_auth:
            return results

        for mode in search_strings:
            search_params = {
                'passkey': self.passkey
            }

            if self.freeleech:
                search_params['freeleech'] = 1

            sickrage.app.log.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: %s " % search_string)
                    search_params['search'] = search_string

                try:
                    data = self.session.get(self.urls['search'], params=search_params).json()
                    results += self.parse(data, mode)
                except Exception:
                    sickrage.app.log.debug("No data returned from provider")

        return results

    def parse(self, data, mode, **kwargs):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []

        error_code = data.pop('error', {})
        if error_code.get('code'):
            if error_code.get('code') != 2:
                sickrage.app.log.warning('{0}', error_code.get('descr', 'Error code 2 - no description available'))
            return results

        account_ok = data.pop('user', {}).get('can_leech')
        if not account_ok:
            sickrage.app.log.warning('Sorry, your account is not allowed to download, check your ratio')
            return results

        torrent_rows = data.pop('torrents', {})

        if not torrent_rows:
            sickrage.app.log.debug('Provider has no results for this search')
            return results

        for row in torrent_rows:
            try:
                title = row.get('name')
                download_url = row.get('download_link')
                if not all([title, download_url]):
                    continue

                seeders = try_int(row.get('seeders'))
                leechers = try_int(row.get('leechers'))

                size = try_int(row.get('size'), -1)

                results += [
                    {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                ]

                if mode != 'RSS':
                    sickrage.app.log.debug("Found result: {}".format(title))
            except Exception:
                sickrage.app.log.error("Failed parsing provider.")

        return results
