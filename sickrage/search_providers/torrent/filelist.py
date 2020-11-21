# coding=utf-8
#
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE. If not, see <http://www.gnu.org/licenses/>.
from urllib.parse import urljoin

from requests.utils import dict_from_cookiejar

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, try_int, convert_size
from sickrage.search_providers import TorrentProvider


class FileListProvider(TorrentProvider):
    def __init__(self):
        super(FileListProvider, self).__init__('FileList', 'https://filelist.ro', True)

        # URLs
        self._urls.update({
            "login": "{base_url}/takelogin.php".format(**self._urls),
            "search": "{base_url}/browse.php".format(**self._urls),
        })

        # custom settings
        self.custom_settings = {
            'username': '',
            'password': '',
            'minseed': 0,
            'minleech': 0
        }

        # Proper Strings
        self.proper_strings = ["PROPER", "REPACK"]

        # Cache
        self.cache = TVCache(self)

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {
            "username": self.custom_settings['username'],
            "password": self.custom_settings['password'],
            "ssl": 'yes'
        }

        try:
            response = self.session.post(self.urls["login"], data=login_params).text
        except Exception:
            sickrage.app.log.warning("Unable to connect to provider")
            self.session.cookies.clear()
            return False

        if 'logout.php' not in response:
            sickrage.app.log.warning("Invalid username or password. Check your settings")
            self.session.cookies.clear()
            return False

        return True

    def search(self, search_strings, age=0, series_id=None, series_provider_id=None, season=None, episode=None, **kwargs):
        results = []

        if not self.login():
            return results

        # Search Params
        search_params = {
            "search": "",
            "cat": 0
        }

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: {0}".format(mode))

            for search_string in search_strings[mode]:
                if mode != "RSS":
                    sickrage.app.log.debug("Search string: {}".format(search_string))
                    search_params["search"] = search_string

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
            torrent_rows = html.find_all("div", class_="torrentrow")

            # Continue only if at least one Release is found
            if not torrent_rows:
                sickrage.app.log.debug("Data returned from provider does not contain any torrents")
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

                    torrent_size = cells[labels.index("Size")].find("span").get_text(strip=True)
                    size = convert_size(torrent_size, -1)

                    results += [{
                        'title': title,
                        'link': download_url,
                        'size': size,
                        'seeders': seeders,
                        'leechers': leechers
                    }]

                    if mode != "RSS":
                        sickrage.app.log.debug("Found result: {}".format(title))
                except Exception:
                    sickrage.app.log.error("Failed parsing provider")

        return results
