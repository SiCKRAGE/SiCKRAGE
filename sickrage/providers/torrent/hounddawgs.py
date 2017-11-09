# Author: Idan Gutman
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import re

from requests.utils import dict_from_cookiejar

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser
from sickrage.providers import TorrentProvider


class HoundDawgsProvider(TorrentProvider):
    def __init__(self):
        super(HoundDawgsProvider, self).__init__("HoundDawgs", 'http://hounddawgs.org', True)

        self.urls.update({
            'search': '{base_url}/torrents.php'.format(**self.urls),
            'login': '{base_url}/login.php'.format(**self.urls)
        })

        self.username = None
        self.password = None

        self.minseed = None
        self.minleech = None

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

        self.cache = TVCache(self, min_time=20)

    def login(self):
        if any(dict_from_cookiejar(sickrage.app.wsession.cookies).values()):
            return True

        login_params = {'username': self.username,
                        'password': self.password,
                        'keeplogged': 'on',
                        'login': 'Login'}

        try:
            response = sickrage.app.wsession.post(self.urls['login'], data=login_params, timeout=30).text
        except Exception:
            sickrage.app.log.warning("Unable to connect to provider".format(self.name))
            return False

        if re.search('Dit brugernavn eller kodeord er forkert.', response) \
                or re.search('<title>Login :: HoundDawgs</title>', response) \
                or re.search('Dine cookies er ikke aktiveret.', response):
            sickrage.app.log.warning(
                "Invalid username or password. Check your settings".format(self.name))
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):
        results = []

        if not self.login():
            return results

        for mode in search_strings.keys():
            sickrage.app.log.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: %s " % search_string)

                self.search_params['searchstr'] = search_string

                try:
                    data = sickrage.app.wsession.get(self.urls['search'], params=self.search_params).text
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

        with bs4_parser(data[data.find("<table class=\"torrent_table")]) as html:
            result_table = html.find('table', {'id': 'torrent_table'})

            if not result_table:
                sickrage.app.log.debug("Data returned from provider does not contain any torrents")
                return results

            result_tbody = result_table.find('tbody')
            entries = result_tbody.contents
            del entries[1::2]

            for result in entries[1:]:

                torrent = result.find_all('td')
                if len(torrent) <= 1:
                    break

                allAs = (torrent[1]).find_all('a')

                try:
                    # link = self.urls['base_url'] + allAs[2].attrs['href']
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

                    download_url = self.urls['base_url'] + allAs[0].attrs['href']
                    # FIXME
                    size = -1
                    seeders = 1
                    leechers = 0

                    if not title or not download_url:
                        continue

                    item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders,
                            'leechers': leechers, 'hash': ''}

                    if mode != 'RSS':
                        sickrage.app.log.debug("Found result: {}".format(title))

                    results.append(item)
                except Exception:
                    sickrage.app.log.error("Failed parsing provider")

        return results