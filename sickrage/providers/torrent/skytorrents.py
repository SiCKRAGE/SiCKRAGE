# coding=utf-8
# URL: https://sickrage.ca
#
# This file is part of SiCKRAGE.
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
# along with SiCKRAGE. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import re
from urlparse import urljoin

import feedparser

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import validate_url, try_int, convert_size
from sickrage.providers import TorrentProvider


class SkyTorrents(TorrentProvider):
    def __init__(self):
        super(SkyTorrents, self).__init__('SkyTorrents', 'https://www.skytorrents.in', False)
        self.minseed = None
        self.minleech = None

        self.urls.update({
            "search": "{base_url}/rss/all".format(**self.urls)
        })

        self.custom_url = ""

        self.cache = TVCache(self, search_params={"RSS": [""]})

        self.regex = re.compile(
            '(?P<seeders>\d+) seeder\(s\), (?P<leechers>\d+) leecher\(s\), (\d+) file\(s\) (?P<size>[^\]]*)')

    def search(self, search_strings, age=0, ep_obj=None):
        results = []

        """
            sorting
            ss: relevance
            ed: seeds desc
            ea: seeds asc
            pd: peers desc
            pa: peers asc
            sd: big > small
            sa: small > big
            ad: added desc (latest)
            aa: added asc (oldest)
        """
        for mode in search_strings:
            sickrage.srCore.srLogger.debug("Search Mode: {0}".format(mode))
            for search_string in search_strings[mode]:
                if mode != "RSS":
                    sickrage.srCore.srLogger.debug("Search string: {0}".format
                                                   (search_string))

                search_url = urljoin(self.urls["search"],
                                     "{sorting}/{page}/{search_string}".format(sorting=("ed", "ad")[mode == "RSS"],
                                                                               page=1, search_string=search_string))

                if self.custom_url:
                    if not validate_url(self.custom_url):
                        sickrage.srCore.srLogger.warning("Invalid custom url: {0}".format(self.custom_url))
                        return results
                    search_url = urljoin(self.custom_url, search_url.split(self.urls['base_url'])[1])

                data = sickrage.srCore.srWebSession.get(search_url).text
                if not data:
                    sickrage.srCore.srLogger.debug("URL did not return results/data, if the results are on the site "
                                                   "maybe try a custom url, or a different one")
                    continue

                if not data.startswith("<rss"):
                    sickrage.srCore.srLogger.info("Expected rss but got something else, is your mirror failing?")
                    continue

                feed = feedparser.parse(data)
                for item in feed.entries:
                    try:
                        title = item.title
                        download_url = item.link
                        if not (title and download_url):
                            continue

                        info = self.regex.search(item.description)
                        if not info:
                            continue

                        seeders = try_int(info.group("seeders"))
                        leechers = try_int(info.group("leechers"))
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != "RSS":
                                sickrage.srCore.srLogger.debug(
                                    "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                    (title, seeders, leechers))
                            continue

                        category = item.category
                        if category != 'all':
                            sickrage.srCore.srLogger.warning(
                                'skytorrents.in has added categories! Please report this so it can be updated: Category={cat}, '
                                'Title={title}'.format(cat=category, title=title))

                        size = convert_size(info.group('size'), -1)
                        info_hash = download_url.rsplit('/', 2)[1]

                        item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders,
                                'leechers': leechers, 'hash': info_hash}
                        if mode != "RSS":
                            sickrage.srCore.srLogger.debug("Found result: {}".format(title))

                        results.append(item)

                    except (AttributeError, TypeError, KeyError, ValueError):
                        continue

        return results

    def parse(self, data, mode):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []