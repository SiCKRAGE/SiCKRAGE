# Author: carlneuhaus
# URL: https://github.com/carlneuhaus
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

import re
from sickbeard.providers import generic
from sickbeard import logger
from sickbeard import tvcache
from sickbeard.bs4_parser import BS4Parser
from sickrage.helper.exceptions import AuthException, ex


class All4NothinProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "All4Nothin")

        self.supportsBacklog = True


        self.username = None
        self.password = None

        self.cache = All4NothinCache(self)

        self.urls = {'base_url': 'https://all4nothin.net/',
                     'login': 'https://all4nothin.net/takelogin.php/',
                     'search': 'https://all4nothin.net/browse.php'
                     '?search=%s&cat=%s&blah=0'}

        self.url = self.urls['base_url']

        self.categories = '0'

    def _checkAuth(self):

        if not self.username or not self.password:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def _doLogin(self):

        login_params = {'username': self.username,
                        'password': self.password}

        self.getURL(self.urls['login'], timeout=30)
        response = self.getURL(self.urls['login'], post_data=login_params, timeout=30)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('Username or password incorrect', response):
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': []}

        if not self._doLogin():
            return results

        for mode in search_params.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_params[mode]:

                logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                # URL with 16 tv-show results
                searchURL = self.urls['search'] % (search_string, self.categories)
                logger.log(u"Search URL: %s" %  searchURL, logger.DEBUG)

                data = self.getURL(searchURL)
                if not data:
                    continue

                if "Search results" not in data:
                    logger.log(u"Data returned from provider does not contain any torrents")
                    continue

                try:
                    data = data.split('<h2>Search results for', 1)[1]
                    with BS4Parser(data, features=["html5lib", "permissive"]) as html:
                        if not html:
                            logger.log(u"No data returned from provider", logger.DEBUG)
                            continue

                        if html.find(text='Nothing found!'):
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        torrent_table = html.find('table', attrs={'border': '1'})
                        torrents = torrent_table.find_all('tr') if torrent_table else []

                        # Continue only if one Release is found
                        if len(torrents) < 2:
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        for result in torrents[1:]:
                            try:
                                title = result.find_all('td')[1].find('a').text
                                download_url = self.urls['base_url'] + result.find_all('td')[7].find('a')['href']
                            except (AttributeError, TypeError, KeyError):
                                continue

                            if not all([title, download_url]):
                                continue

                            item = title, download_url
                            logger.log(u"Found result: %s " % title, logger.DEBUG)

                            items[mode].append(item)

                except Exception as e:
                    logger.log(u"Failed parsing provider. Error: %r" % ex(e), logger.ERROR)

            results += items[mode]

        return results


class All4NothinCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # Only poll ALl4Nothin every 10 minutes max
        self.minTime = 10

provider = All4NothinProvider()
