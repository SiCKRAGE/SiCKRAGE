# Author: echel0n <echel0n@sickrage.ca>
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import re
from urlparse import urljoin

from requests.utils import dict_from_cookiejar

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import bs4_parser, convert_size, try_int
from sickrage.providers import TorrentProvider


class TorrentBytesProvider(TorrentProvider):
    def __init__(self):
        super(TorrentBytesProvider, self).__init__("TorrentBytes", 'https://www.torrentbytes.net', True)

        self.urls.update({
            'login': '{base_url}/takelogin.php'.format(**self.urls),
            'search': '{base_url}/browse.php'.format(**self.urls),
        })

        self.username = None
        self.password = None

        self.minseed = None
        self.minleech = None
        self.freeleech = False

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = TVCache(self, min_time=20)

    def login(self):
        if any(dict_from_cookiejar(sickrage.srCore.srWebSession.cookies).values()):
            return True

        login_params = {'username': self.username,
                        'password': self.password,
                        'login': 'Log in!'}

        try:
            response = sickrage.srCore.srWebSession.post(self.urls['login'], data=login_params, timeout=30).text
        except Exception:
            sickrage.srCore.srLogger.warning("[{}]: Unable to connect to provider".format(self.name))
            return False

        if re.search('Username or password incorrect', response):
            sickrage.srCore.srLogger.warning(
                "[{}]: Invalid username or password. Check your settings".format(self.name))
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):
        results = []

        if not self.login():
            return results

        search_params = {"c33": 1, "c38": 1, "c32": 1, "c37": 1, "c41": 1}

        for mode in search_strings:
            sickrage.srCore.srLogger.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug("Search string: %s " % search_string)

                search_params["search"] = search_string

                try:
                    data = sickrage.srCore.srWebSession.get(self.urls['search'], params=search_params).text
                except Exception:
                    sickrage.srCore.srLogger.debug("No data returned from provider")
                    continue

                try:
                    with bs4_parser(data) as html:
                        torrent_table = html.find("table", border="1")
                        torrent_rows = torrent_table("tr") if torrent_table else []

                        # Continue only if at least one Release is found
                        if len(torrent_rows) < 2:
                            sickrage.srCore.srLogger.debug("Data returned from provider does not contain any torrents")
                            continue

                        # "Type", "Name", Files", "Comm.", "Added", "TTL", "Size", "Snatched", "Seeders", "Leechers"
                        labels = [label.get_text(strip=True) for label in torrent_rows[0]("td")]

                        for result in torrent_rows[1:]:
                            try:
                                cells = result("td")

                                link = cells[labels.index("Name")].find("a", href=re.compile(r"download.php\?id="))["href"]
                                download_url = urljoin(self.urls['base_url'], link)

                                title_element = cells[labels.index("Name")].find("a", href=re.compile(r"details.php\?id="))
                                title = title_element.get("title", "") or title_element.get_text(strip=True)
                                if not all([title, download_url]):
                                    continue

                                if self.freeleech:
                                    # Free leech torrents are marked with green [F L] in the title (i.e. <font color=green>[F&nbsp;L]</font>)
                                    freeleech = cells[labels.index("Name")].find("font", color="green")
                                    if not freeleech or freeleech.get_text(strip=True) != "[F\xa0L]":
                                        continue

                                seeders = try_int(cells[labels.index("Seeders")].get_text(strip=True))
                                leechers = try_int(cells[labels.index("Leechers")].get_text(strip=True))

                                # Filter unseeded torrent
                                if seeders < self.minseed or leechers < self.minleech:
                                    if mode != "RSS":
                                        sickrage.srCore.srLogger.debug(
                                            "Discarding torrent because it doesn't meet the minimum seeders or leechers: "
                                            "{} (S:{} L:{})".format(title, seeders, leechers))
                                        continue

                                torrent_size = cells[labels.index("Size")].get_text(strip=True)
                                size = convert_size(torrent_size, -1)

                                item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders,
                                        'leechers': leechers, 'hash': ''}

                                if mode != "RSS":
                                    sickrage.srCore.srLogger.debug("Found result: {}".format(title))

                                results.append(item)
                            except (AttributeError, TypeError, ValueError):
                                continue
                except Exception:
                    sickrage.srCore.srLogger.error("Failed parsing provider.")

        # Sort all the items by seeders if available
        results.sort(key=lambda k: try_int(k.get('seeders', 0)), reverse=True)

        return results
