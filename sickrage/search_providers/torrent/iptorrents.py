# Author: seedboy
# URL: https://github.com/seedboy
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

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, convert_size, validate_url
from sickrage.search_providers import TorrentProvider


class IPTorrentsProvider(TorrentProvider):
    def __init__(self):
        super(IPTorrentsProvider, self).__init__("IPTorrents", 'https://iptorrents.eu', True)

        self._urls.update({
            'login': '{base_url}/torrents'.format(**self._urls),
            'search': '{base_url}/t?%s%s&q=%s&qf=#torrents'.format(**self._urls)
        })

        self.enable_cookies = True
        self.required_cookies = ('uid', 'pass')

        # custom settings
        self.custom_settings = {
            'username': '',
            'password': '',
            'custom_url': '',
            'freeleech': False,
            'minseed': 0,
            'minleech': 0
        }

        self.categories = '73=&60='

        self.cache = TVCache(self, min_time=10)

    def login(self):
        return self.cookie_login('sign in')

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []

        if not self.login():
            return results

        freeleech = '&free=on' if self.custom_settings['freeleech'] else ''

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: %s " % search_string)

                # URL with 50 tv-show results, or max 150 if adjusted in IPTorrents profile
                search_url = self.urls['search'] % (self.categories, freeleech, search_string)
                search_url += ';o=seeders' if mode != 'RSS' else ''

                if self.custom_settings['custom_url']:
                    if not validate_url(self.custom_settings['custom_url']):
                        sickrage.app.log.warning("Invalid custom url: {}".format(self.custom_settings['custom_url']))
                        return results

                    search_url = urljoin(self.custom_settings['custom_url'], search_url.split(self.urls['base_url'])[1])

                resp = self.session.get(search_url)
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

        data = re.sub(r'(?im)<button.+?<[/]button>', '', data, 0)

        with bs4_parser(data) as html:
            torrent_table = html.find('table', id='torrents')
            torrents = torrent_table('tr') if torrent_table else []

            # Continue only if one Release is found
            if len(torrents) < 2 or html.find(text='No Torrents Found!'):
                sickrage.app.log.debug("Data returned from provider does not contain any torrents")
                return results

            for torrent in torrents[1:]:
                try:
                    title = torrent('td')[1].find('a').text
                    download_url = self.urls['base_url'] + torrent('td')[3].find('a')['href']
                    if not all([title, download_url]):
                        continue

                    size = convert_size(torrent('td')[5].text, -1)
                    seeders = int(torrent('td')[7].contents[0])
                    leechers = int(torrent('td')[8].contents[0])

                    results += [{
                        'title': title,
                        'link': download_url,
                        'size': size,
                        'seeders': seeders,
                        'leechers': leechers
                    }]

                    if mode != 'RSS':
                        sickrage.app.log.debug("Found result: {}".format(title))
                except Exception:
                    sickrage.app.log.error("Failed parsing provider")

        return results
