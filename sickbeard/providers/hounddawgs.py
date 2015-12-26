# Author: Idan Gutman
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
import traceback
import logging
from sickbeard import tvcache
from sickbeard.bs4_parser import BS4Parser

from sickbeard.providers import generic


class HoundDawgsProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "HoundDawgs")

        self.supportsBacklog = True

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = HoundDawgsCache(self)

        self.urls = {'base_url': 'https://hounddawgs.org/',
                     'search': 'https://hounddawgs.org/torrents.php',
                     'login': 'https://hounddawgs.org/login.php'}

        self.url = self.urls[b'base_url']

        self.search_params = {
            "filter_cat[85]": 1,
            "filter_cat[58]": 1,
            "filter_cat[57]": 1,
            "filter_cat[74]": 1,
            "filter_cat[92]": 1,
            "filter_cat[93]": 1,
            "order_by": "s3",
            "order_way": "desc",
            "type": '',
            "userid": '',
            "searchstr": '',
            "searchimdb": '',
            "searchtags": ''
        }

    def _doLogin(self):

        login_params = {'username': self.username,
                        'password': self.password,
                        'keeplogged': 'on',
                        'login': 'Login'}

        self.getURL(self.urls[b'base_url'], timeout=30)
        response = self.getURL(self.urls[b'login'], post_data=login_params, timeout=30)
        if not response:
            logging.warning("Unable to connect to provider")
            return False

        if re.search('Dit brugernavn eller kodeord er forkert.', response) \
                or re.search('<title>Login :: HoundDawgs</title>', response) \
                or re.search('Dine cookies er ikke aktiveret.', response):
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
                    logging.debug("Search string: %s " % search_string)

                self.search_params[b'searchstr'] = search_string

                data = self.getURL(self.urls[b'search'], params=self.search_params)

                strTableStart = "<table class=\"torrent_table"
                startTableIndex = data.find(strTableStart)
                trimmedData = data[startTableIndex:]
                if not trimmedData:
                    continue

                try:
                    with BS4Parser(trimmedData, features=["html5lib", "permissive"]) as html:
                        result_table = html.find('table', {'id': 'torrent_table'})

                        if not result_table:
                            logging.debug("Data returned from provider does not contain any torrents")
                            continue

                        result_tbody = result_table.find('tbody')
                        entries = result_tbody.contents
                        del entries[1::2]

                        for result in entries[1:]:

                            torrent = result.find_all('td')
                            if len(torrent) <= 1:
                                break

                            allAs = (torrent[1]).find_all('a')

                            try:
                                # link = self.urls[b'base_url'] + allAs[2].attrs[b'href']
                                # url = result.find('td', attrs={'class': 'quickdownload'}).find('a')
                                title = allAs[2].string
                                # Trimming title so accepted by scene check(Feature has been rewuestet i forum)
                                title = title.replace("custom.", "")
                                title = title.replace("CUSTOM.", "")
                                title = title.replace("Custom.", "")
                                title = title.replace("dk", "")
                                title = title.replace("DK", "")
                                title = title.replace("Dk", "")
                                title = title.replace("subs.", "")
                                title = title.replace("SUBS.", "")
                                title = title.replace("Subs.", "")

                                download_url = self.urls[b'base_url'] + allAs[0].attrs[b'href']
                                # FIXME
                                size = -1
                                seeders = 1
                                leechers = 0

                            except (AttributeError, TypeError):
                                continue

                            if not title or not download_url:
                                continue

                            # Filter unseeded torrent
                            # if seeders < self.minseed or leechers < self.minleech:
                            #    if mode is not 'RSS':
                            #        logging.debug(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers))
                            #    continue

                            item = title, download_url, size, seeders, leechers
                            if mode is not 'RSS':
                                logging.debug("Found result: %s " % title)

                            items[mode].append(item)

                except Exception as e:
                    logging.error("Failed parsing provider. Traceback: %s" % traceback.format_exc())

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class HoundDawgsCache(tvcache.TVCache):
    def __init__(self, provider_obj):
        tvcache.TVCache.__init__(self, provider_obj)

        # only poll HoundDawgs every 20 minutes max
        self.minTime = 20

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_strings)}


provider = HoundDawgsProvider()
