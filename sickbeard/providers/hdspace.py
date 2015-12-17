# Author: Idan Gutman
# Modified by jkaberg, https://github.com/jkaberg for SceneAccess
# Modified by 7ca for HDSpace
# URL: http://code.google.com/p/sickbeard/
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
import urllib
import requests
from bs4 import BeautifulSoup

import logging
from sickbeard import tvcache
from sickbeard.providers import generic


class HDSpaceProvider(generic.TorrentProvider):
    def __init__(self):
        generic.TorrentProvider.__init__(self, "HDSpace")

        self.supportsBacklog = True

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = HDSpaceCache(self)

        self.urls = {'base_url': 'https://hd-space.org/',
                     'login': 'https://hd-space.org/index.php?page=login',
                     'search': 'https://hd-space.org/index.php?page=torrents&search=%s&active=1&options=0',
                     'rss': 'https://hd-space.org/rss_torrents.php?feed=dl'}

        self.categories = [15, 21, 22, 24, 25, 40]  # HDTV/DOC 1080/720, bluray, remux
        self.urls[b'search'] += '&category='
        for cat in self.categories:
            self.urls[b'search'] += str(cat) + '%%3B'
            self.urls[b'rss'] += '&cat[]=' + str(cat)
        self.urls[b'search'] = self.urls[b'search'][:-4]  # remove extra %%3B

        self.url = self.urls[b'base_url']

    def _checkAuth(self):

        if not self.username or not self.password:
            logging.warning("Invalid username or password. Check your settings")

        return True

    def _doLogin(self):

        if 'pass' in requests.utils.dict_from_cookiejar(self.session.cookies):
            return True

        login_params = {'uid': self.username,
                        'pwd': self.password}

        response = self.getURL(self.urls[b'login'], post_data=login_params, timeout=30)
        if not response:
            logging.warning("Unable to connect to provider")
            return False

        if re.search('Password Incorrect', response):
            logging.warning("Invalid username or password. Check your settings")
            return False

        return True

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return results

        for mode in search_strings.keys():
            logging.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:

                if mode is not 'RSS':
                    searchURL = self.urls[b'search'] % (urllib.quote_plus(search_string.replace('.', ' ')),)
                else:
                    searchURL = self.urls[b'search'] % ''

                logging.debug("Search URL: %s" % searchURL)
                if mode is not 'RSS':
                    logging.debug("Search string: %s" % search_string)

                data = self.getURL(searchURL)
                if not data or 'please try later' in data:
                    logging.debug("No data returned from provider")
                    continue

                # Search result page contains some invalid html that prevents html parser from returning all data.
                # We cut everything before the table that contains the data we are interested in thus eliminating
                # the invalid html portions
                try:
                    data = data.split('<div id="information"></div>')[1]
                    index = data.index('<table')
                except ValueError:
                    logging.error("Could not find main torrent table")
                    continue

                html = BeautifulSoup(data[index:], 'html5lib')
                if not html:
                    logging.debug("No html data parsed from provider")
                    continue

                torrents = html.findAll('tr')
                if not torrents:
                    continue

                # Skip column headers
                for result in torrents[1:]:
                    if len(result.contents) < 10:
                        # skip extraneous rows at the end
                        continue

                    try:
                        dl_href = result.find('a', attrs={'href': re.compile(r'download.php.*')})['href']
                        title = re.search('f=(.*).torrent', dl_href).group(1).replace('+', '.')
                        download_url = self.urls[b'base_url'] + dl_href
                        seeders = int(result.find('span', attrs={'class': 'seedy'}).find('a').text)
                        leechers = int(result.find('span', attrs={'class': 'leechy'}).find('a').text)
                        size = re.match(r'.*?([0-9]+,?\.?[0-9]* [KkMmGg]+[Bb]+).*', str(result), re.DOTALL).group(1)

                        if not all([title, download_url]):
                            continue

                        # Filter unseeded torrent
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode is not 'RSS':
                                logging.debug(
                                    "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                        title, seeders, leechers))
                            continue

                        item = title, download_url, size, seeders, leechers
                        if mode is not 'RSS':
                            logging.debug("Found result: %s " % title)

                        items[mode].append(item)

                    except (AttributeError, TypeError, KeyError, ValueError):
                        continue

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio

    def _convertSize(self, size):
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


class HDSpaceCache(tvcache.TVCache):
    def __init__(self, provider_obj):
        tvcache.TVCache.__init__(self, provider_obj)

        # only poll HDSpace every 10 minutes max
        self.minTime = 10

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_strings)}


provider = HDSpaceProvider()
