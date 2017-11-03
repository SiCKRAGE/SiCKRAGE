# coding=utf-8
#
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import re

from requests.compat import urljoin
from requests.utils import dict_from_cookiejar

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, try_int, convert_size
from sickrage.providers import TorrentProvider


class FileListProvider(TorrentProvider):
    def __init__(self):
        super(FileListProvider, self).__init__('FileList', 'http://filelist.ro', True)
        # Credentials
        self.username = None
        self.password = None

        # Torrent Stats
        self.minseed = None
        self.minleech = None

        # URLs
        self.urls.update({
            "login": "{base_url}/takelogin.php".format(**self.urls),
            "search": "{base_url}/browse.php".format(**self.urls),
        })

        # Proper Strings
        self.proper_strings = ["PROPER", "REPACK"]

        # Cache
        self.cache = TVCache(self)

    def login(self):
        if any(dict_from_cookiejar(sickrage.srCore.srWebSession.cookies).values()):
            return True

        login_params = {
            "username": self.username,
            "password": self.password
        }

        response = sickrage.srCore.srWebSession.post(self.urls["login"], data=login_params).text
        if not response:
            sickrage.srCore.srLogger.warning("Unable to connect to provider")
            return False

        if re.search("Invalid Username/password", response) \
                or re.search("<title>Login :: FileList.ro</title>", response) \
                or re.search("Login esuat!", response):
            sickrage.srCore.srLogger.warning("Invalid username or password. Check your settings")
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):
        results = []

        if not self.login():
            return results

        # Search Params
        search_params = {
            "search": "",
            "cat": 0
        }

        for mode in search_strings:
            sickrage.srCore.srLogger.debug("Search Mode: {0}".format(mode))

            for search_string in search_strings[mode]:
                if mode != "RSS":
                    sickrage.srCore.srLogger.debug("Search string: {}".format(search_string))

                search_params["search"] = search_string
                search_url = self.urls["search"]

                try:
                    data = sickrage.srCore.srWebSession.get(search_url, params=search_params).text
                    results += self.parse(data, mode)
                except Exception:
                    sickrage.srCore.srLogger.debug("No data returned from provider")

        return results

    def parse(self, data, mode):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []

        with bs4_parser(data, "html5lib") as html:
            torrent_rows = html.find_all("div", class_="torrentrow")

            # Continue only if at least one Release is found
            if not torrent_rows:
                sickrage.srCore.srLogger.debug("Data returned from provider does not contain any torrents")
                return results

            # "Type", "Name", "Download", "Files", "Comments", "Added", "Size", "Snatched", "Seeders", "Leechers", "Upped by"
            labels = []

            columns = html.find_all("div", class_="colhead")
            for index, column in enumerate(columns):
                lbl = column.get_text(strip=True)
                if lbl:
                    labels.append(str(lbl))
                else:
                    lbl = column.find("img")
                    if lbl:
                        if lbl.has_attr("alt"):
                            lbl = lbl['alt']
                            labels.append(str(lbl))
                    else:
                        if index == 3:
                            lbl = "Download"
                        else:
                            lbl = str(index)
                        labels.append(lbl)

            # Skip column headers
            for result in torrent_rows:
                try:
                    cells = result.find_all("div", class_="torrenttable")
                    if len(cells) < len(labels):
                        continue

                    title = cells[labels.index("Name")].find("a").find("b").get_text(strip=True)
                    download_url = urljoin(self.urls['base_url'],
                                           cells[labels.index("Download")].find("a")["href"])
                    if not all([title, download_url]):
                        continue

                    seeders = try_int(cells[labels.index("Seeders")].find("span").get_text(strip=True))
                    leechers = try_int(cells[labels.index("Leechers")].find("span").get_text(strip=True))

                    # Filter unseeded torrent
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode != "RSS":
                            sickrage.srCore.srLogger.debug("Discarding torrent because it doesn't meet the"
                                                           " minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                                           (title, seeders, leechers))
                        continue

                    torrent_size = cells[labels.index("Size")].find("span").get_text(strip=True)
                    size = convert_size(torrent_size, -1)

                    item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders,
                            'leechers': leechers, 'hash': None}
                    if mode != "RSS":
                        sickrage.srCore.srLogger.debug("Found result: {}".format(title))

                    results.append(item)
                except Exception:
                    sickrage.srCore.srLogger.error("Failed parsing provider")

        return results