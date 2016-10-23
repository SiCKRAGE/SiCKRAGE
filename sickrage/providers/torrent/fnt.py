# -*- coding: latin-1 -*-
# Author: raver2046 <raver2046@gmail.com> from djoole <bobby.djoole@gmail.com>
# URL: https://sickrage.ca
#
# This file is part of SickRage.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import re
import traceback

import requests
import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser
from sickrage.providers import TorrentProvider


class FNTProvider(TorrentProvider):
    def __init__(self):
        super(FNTProvider, self).__init__("FNT",'fnt.nu', True)

        self.supports_backlog = True

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = TVCache(self, min_time=10)

        self.urls.update({
            'search': '{base_url}/torrents/recherche/'.format(base_url=self.urls['base_url']),
            'login': '{base_url}/account-login.php'.format(base_url=self.urls['base_url'])
        })

    def login(self):
        if any(requests.utils.dict_from_cookiejar(sickrage.srCore.srWebSession.cookies).values()):
            return True

        login_params = {'username': self.username,
                        'password': self.password,
                        'submit': 'Se loguer'
                        }

        try:
            response = sickrage.srCore.srWebSession.post(self.urls['login'], data=login_params, timeout=30).text
        except Exception:
            sickrage.srCore.srLogger.warning("[{}]: Unable to connect to provider".format(self.name))
            return False

        if re.search('Pseudo ou mot de passe non valide', response):
            sickrage.srCore.srLogger.warning("[{}]: Invalid username or password. Check your settings".format(self.name))
            return False

        return True

    def search(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):
        results = []

        search_params = {
            "afficher": 1, "c118": 1, "c129": 1, "c119": 1, "c120": 1, "c121": 1, "c126": 1,
            "c137": 1, "c138": 1, "c146": 1, "c122": 1, "c110": 1, "c109": 1, "c135": 1, "c148": 1,
            "c153": 1, "c149": 1, "c150": 1, "c154": 1, "c155": 1, "c156": 1, "c114": 1,
            "visible": 1, "freeleech": 0, "nuke": 1, "3D": 0, "sort": "size", "order": "desc"
        }

        items = {'Season': [], 'Episode': [], 'RSS': []}

        # check for auth
        if not self.login():
            return results

        for mode in search_strings.keys():
            sickrage.srCore.srLogger.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug("Search string: %s " % search_string)

                search_params['recherche'] = search_string

                try:
                    data = sickrage.srCore.srWebSession.get(self.urls['search'], params=search_params).text
                except Exception:
                    sickrage.srCore.srLogger.debug("No data returned from provider")
                    continue

                try:
                    with bs4_parser(data) as html:
                        result_table = html.find('table', {'id': 'tablealign3bis'})

                        if not result_table:
                            sickrage.srCore.srLogger.debug("Data returned from provider does not contain any torrents")
                            continue

                        if result_table:
                            rows = result_table.findAll("tr", {"class": "ligntorrent"})

                            for row in rows:
                                link = row.findAll('td')[1].find("a", href=re.compile("fiche_film"))

                                if link:
                                    try:
                                        title = link.text
                                        download_url = self.urls['base_url'] + "/" + \
                                                       row.find("a", href=re.compile(r"download\.php"))['href']
                                    except (AttributeError, TypeError):
                                        continue

                                    try:
                                        detailseedleech = link['mtcontent']
                                        seeders = int(
                                            detailseedleech.split("<font color='#00b72e'>")[1].split("</font>")[0])
                                        leechers = int(
                                            detailseedleech.split("<font color='red'>")[1].split("</font>")[0])
                                        # FIXME
                                        size = -1
                                    except Exception:
                                        sickrage.srCore.srLogger.debug(
                                            "Unable to parse torrent id & seeders & leechers. Traceback: %s " % traceback.format_exc())
                                        continue

                                    if not all([title, download_url]):
                                        continue

                                    # Filter unseeded torrent
                                    if seeders < self.minseed or leechers < self.minleech:
                                        if mode != 'RSS':
                                            sickrage.srCore.srLogger.debug(
                                                "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                                    title, seeders, leechers))
                                        continue

                                    item = title, download_url, size, seeders, leechers
                                    if mode != 'RSS':
                                        sickrage.srCore.srLogger.debug("Found result: %s " % title)

                                    items[mode].append(item)

                except Exception as e:
                    sickrage.srCore.srLogger.error("Failed parsing provider. Traceback: %s" % traceback.format_exc())

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seed_ratio(self):
        return self.ratio
