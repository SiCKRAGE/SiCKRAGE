# Author: duramato <matigonkas@outlook.com>
# URL: https://github.com/SiCKRAGETV/sickrage
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

from urllib import quote_plus

import logging
from sickbeard import tvcache
from sickbeard import helpers
from sickbeard.providers import generic
from sickbeard.common import USER_AGENT


class TORRENTPROJECTProvider(generic.TorrentProvider):
    def __init__(self):
        generic.TorrentProvider.__init__(self, "TorrentProject")

        self.supportsBacklog = True
        self.public = True
        self.ratio = 0
        self.urls = {'api': 'https://torrentproject.se/',}
        self.url = self.urls[b'api']
        self.headers.update({'User-Agent': USER_AGENT})
        self.minseed = None
        self.minleech = None
        self.cache = TORRENTPROJECTCache(self)

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_strings.keys():  # Mode = RSS, Season, Episode
            logging.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:
                if mode is not 'RSS':
                    logging.debug("Search string: %s " % search_string)

                searchURL = self.urls[b'api'] + "?s=%s&out=json&filter=2101&num=150" % quote_plus(
                    search_string.encode('utf-8'))

                logging.debug("Search URL: %s" % searchURL)
                torrents = self.getURL(searchURL, json=True)
                if not (torrents and "total_found" in torrents and int(torrents[b"total_found"]) > 0):
                    logging.debug("Data returned from provider does not contain any torrents")
                    continue

                del torrents[b"total_found"]

                results = []
                for i in torrents:
                    title = torrents[i][b"title"]
                    seeders = helpers.tryInt(torrents[i][b"seeds"], 1)
                    leechers = helpers.tryInt(torrents[i][b"leechs"], 0)
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode is not 'RSS':
                            logging.debug("Torrent doesn't meet minimum seeds & leechers not selecting : %s" % title)
                        continue

                    t_hash = torrents[i][b"torrent_hash"]
                    size = int(torrents[i][b"torrent_size"])

                    try:
                        assert seeders < 10
                        assert mode is not 'RSS'
                        logging.debug("Torrent has less than 10 seeds getting dyn trackers: " + title)
                        trackerUrl = self.urls[b'api'] + "" + t_hash + "/trackers_json"
                        jdata = self.getURL(trackerUrl, json=True)
                        assert jdata is not "maintenance"
                        download_url = "magnet:?xt=urn:btih:" + t_hash + "&dn=" + title + "".join(
                                ["&tr=" + s for s in jdata])
                    except (Exception, AssertionError):
                        download_url = "magnet:?xt=urn:btih:" + t_hash + "&dn=" + title + "&tr=udp://tracker.openbittorrent.com:80&tr=udp://tracker.coppersurfer.tk:6969&tr=udp://open.demonii.com:1337&tr=udp://tracker.leechers-paradise.org:6969&tr=udp://exodus.desync.com:6969"

                    if not all([title, download_url]):
                        continue

                    item = title, download_url, size, seeders, leechers

                    if mode is not 'RSS':
                        logging.debug("Found result: %s" % title)

                    items[mode].append(item)

            # For each search mode sort all the items by seeders
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class TORRENTPROJECTCache(tvcache.TVCache):
    def __init__(self, provider_obj):
        tvcache.TVCache.__init__(self, provider_obj)

        self.minTime = 20

    def _getRSSData(self):
        search_params = {'RSS': ['0day']}
        return {'entries': self.provider._doSearch(search_params)}


provider = TORRENTPROJECTProvider()
