# Author: Idan Gutman
# Modified by jkaberg, https://github.com/jkaberg for SceneAccess
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

import re
import traceback
import urllib

import requests

import sickrage
from core.caches import tv_cache
from core.helpers import bs4_parser
from providers import TorrentProvider


class HDTorrentsProvider(TorrentProvider):
    def __init__(self):
        super(HDTorrentsProvider, self).__init__("HDTorrents")

        self.supportsBacklog = True

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.urls = {'base_url': 'https://hd-torrents.org',
                     'login': 'https://hd-torrents.org/login.php',
                     'search': 'https://hd-torrents.org/torrents.php?search=%s&active=1&options=0%s',
                     'rss': 'https://hd-torrents.org/torrents.php?search=&active=1&options=0%s',
                     'home': 'https://hd-torrents.org/%s'}

        self.url = self.urls['base_url']

        self.categories = "&category[]=59&category[]=60&category[]=30&category[]=38"
        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = HDTorrentsCache(self)

    def _checkAuth(self):

        if not self.username or not self.password:
            sickrage.srLogger.warning("Invalid username or password. Check your settings")

        return True

    def _doLogin(self):

        if any(requests.utils.dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {'uid': self.username,
                        'pwd': self.password,
                        'submit': 'Confirm'}

        response = self.getURL(self.urls['login'], post_data=login_params, timeout=30)
        if not response:
            sickrage.srLogger.warning("Unable to connect to provider")
            return False

        if re.search('You need cookies enabled to log in.', response):
            sickrage.srLogger.warning("Invalid username or password. Check your settings")
            return False

        return True

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return results

        for mode in search_strings.keys():
            sickrage.srLogger.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:

                if mode is not 'RSS':
                    searchURL = self.urls['search'] % (urllib.quote_plus(search_string), self.categories)
                else:
                    searchURL = self.urls['rss'] % self.categories

                sickrage.srLogger.debug("Search URL: %s" % searchURL)
                if mode is not 'RSS':
                    sickrage.srLogger.debug("Search string: %s" % search_string)

                data = self.getURL(searchURL)
                if not data or 'please try later' in data:
                    sickrage.srLogger.debug("No data returned from provider")
                    continue

                # Search result page contains some invalid html that prevents html parser from returning all data.
                # We cut everything before the table that contains the data we are interested in thus eliminating
                # the invalid html portions
                try:
                    index = data.lower().ind
                    '<table class="mainblockcontenttt"'
                except ValueError:
                    sickrage.srLogger.error("Could not find table of torrents mainblockcontenttt")
                    continue

                data = urllib.unquote(data[index:].encode('utf-8')).decode('utf-8').replace('\t', '')

                with bs4_parser(data) as html:
                    if not html:
                        sickrage.srLogger.debug("No html data parsed from provider")
                        continue

                    empty = html.find('No torrents here')
                    if empty:
                        sickrage.srLogger.debug("Data returned from provider does not contain any torrents")
                        continue

                    tables = html.find('table', attrs={'class': 'mainblockcontenttt'})
                    if not tables:
                        sickrage.srLogger.error("Could not find table of torrents mainblockcontenttt")
                        continue

                    torrents = tables.findChildren('tr')
                    if not torrents:
                        continue

                    # Skip column headers
                    for result in torrents[1:]:
                        try:
                            cells = result.findChildren('td', attrs={
                                'class': re.compile(r'(green|yellow|red|mainblockcontent)')})
                            if not cells:
                                continue

                            title = download_url = seeders = leechers = size = None
                            for cell in cells:
                                try:
                                    if None is title and cell.get('title') and cell.get('title') in 'Download':
                                        title = re.search('f=(.*).torrent', cell.a[b'href']).group(1).replace('+', '.')
                                        title = title.decode('utf-8')
                                        download_url = self.urls['home'] % cell.a[b'href']
                                        continue
                                    if None is seeders and cell.get('class')[0] and cell.get('class')[
                                        0] in 'green' 'yellow' 'red':
                                        seeders = int(cell.text)
                                        if not seeders:
                                            seeders = 1
                                            continue
                                    elif None is leechers and cell.get('class')[0] and cell.get('class')[
                                        0] in 'green' 'yellow' 'red':
                                        leechers = int(cell.text)
                                        if not leechers:
                                            leechers = 0
                                            continue

                                    # Need size for failed downloads handling
                                    if size is None:
                                        if re.match(r'[0-9]+,?\.?[0-9]* [KkMmGg]+[Bb]+', cell.text):
                                            size = self._convertSize(cell.text)
                                            if not size:
                                                size = -1

                                except Exception:
                                    sickrage.srLogger.error("Failed parsing provider. Traceback: %s" % traceback.format_exc())

                            if not all([title, download_url]):
                                continue

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode is not 'RSS':
                                    sickrage.srLogger.debug(
                                            "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                                    title, seeders, leechers))
                                continue

                            item = title, download_url, size, seeders, leechers
                            if mode is not 'RSS':
                                sickrage.srLogger.debug("Found result: %s " % title)

                            items[mode].append(item)

                        except (AttributeError, TypeError, KeyError, ValueError):
                            continue

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio

    @staticmethod
    def _convertSize(size):
        size, modifier = size.split(' ')
        size = float(size)
        if modifier in 'KB':
            size = size * 1024
        elif modifier in 'MB':
            size = size * 1024 ** 2
        elif modifier in 'GB':
            size = size * 1024 ** 3
        elif modifier in 'TB':
            size = size * 1024 ** 4
        return int(size)


class HDTorrentsCache(tv_cache.TVCache):
    def __init__(self, provider_obj):
        tv_cache.TVCache.__init__(self, provider_obj)

        # only poll HDTorrents every 10 minutes max
        self.minTime = 10

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_strings)}
