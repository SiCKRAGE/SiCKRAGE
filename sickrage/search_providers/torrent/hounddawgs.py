# coding=utf-8
# Author: Idan Gutman
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


import re
from urllib.parse import urljoin

from requests.utils import dict_from_cookiejar

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, convert_size, try_int
from sickrage.search_providers import TorrentProvider


class HoundDawgsProvider(TorrentProvider):
    def __init__(self):
        super(HoundDawgsProvider, self).__init__("HoundDawgs", 'https://hounddawgs.org', True)

        self._urls.update({
            'search': '{base_url}/torrents.php'.format(**self._urls),
            'login': '{base_url}/login.php'.format(**self._urls)
        })

        # custom settings
        self.custom_settings = {
            'username': '',
            'password': '',
            'freeleech': False,
            'ranked': False,
            'minseed': 0,
            'minleech': 0
        }

        self.cache = TVCache(self)

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {'username': self.custom_settings['username'],
                        'password': self.custom_settings['password'],
                        'keeplogged': 'on',
                        'login': 'Login'}

        try:
            response = self.session.post(self.urls['login'], data=login_params, timeout=30).text
        except Exception:
            sickrage.app.log.warning("Unable to connect to provider")
            return False

        if any([re.search('Dit brugernavn eller kodeord er forkert.', response),
                re.search('<title>Login :: HoundDawgs</title>', response),
                re.search('Dine cookies er ikke aktiveret.', response)]):
            sickrage.app.log.warning('Invalid username or password. Check your settings')
            return False

        return True

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []

        if not self.login():
            return results

        # Search Params
        search_params = {
            'filter_cat[85]': 1,
            'filter_cat[58]': 1,
            'filter_cat[57]': 1,
            'filter_cat[74]': 1,
            'filter_cat[92]': 1,
            'filter_cat[93]': 1,
            'order_by': 's3',
            'order_way': 'desc',
            'type': '',
            'userid': '',
            'searchstr': '',
            'searchimdb': '',
            'searchtags': ''
        }

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: %s " % search_string)
                    if self.custom_settings['ranked']:
                        sickrage.app.log.debug('Searching only ranked torrents')

                search_params['searchstr'] = search_string

                resp = self.session.get(self.urls['search'], params=search_params)
                if not resp or not resp.text:
                    sickrage.app.log.debug("No data returned from provider")
                    continue

                results += self.parse(resp.text, mode)

        return results

    def parse(self, data, mode, **kwargs):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []

        with bs4_parser(data) as html:
            torrent_table = html.find('table', {'id': 'torrent_table'})

            # Continue only if at least one release is found
            if not torrent_table:
                sickrage.app.log.debug('Data returned from provider does not contain any {}torrents',
                                       'ranked ' if self.custom_settings['ranked'] else '')
                return results

            torrent_body = torrent_table.find('tbody')
            torrent_rows = torrent_body.contents
            del torrent_rows[1::2]

            for row in torrent_rows[1:]:
                try:
                    torrent = row('td')
                    if len(torrent) <= 1:
                        break

                    all_as = (torrent[1])('a')
                    notinternal = row.find('img', src='/static//common/user_upload.png')
                    if self.custom_settings['ranked'] and notinternal:
                        sickrage.app.log.debug('Found a user uploaded release, Ignoring it..')
                        continue

                    freeleech = row.find('img', src='/static//common/browse/freeleech.png')
                    if self.custom_settings['freeleech'] and not freeleech:
                        continue

                    title = all_as[2].string
                    download_url = urljoin(self.urls['base_url'], all_as[0].attrs['href'])
                    if not all([title, download_url]):
                        continue

                    seeders = try_int((row('td')[6]).text.replace(',', ''))
                    leechers = try_int((row('td')[7]).text.replace(',', ''))

                    size = convert_size(row.find('td', class_='nobr').find_next_sibling('td').string, -1)

                    results += [
                        {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                    ]

                    if mode != 'RSS':
                        sickrage.app.log.debug("Found result: {}".format(title))
                except Exception:
                    sickrage.app.log.error("Failed parsing provider")

        return results
