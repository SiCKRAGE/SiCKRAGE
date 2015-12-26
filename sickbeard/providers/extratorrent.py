# Author: duramato <matigonkas@outlook.com>
# Author: miigotu
# URL: https://github.com/SiCKRAGETV/sickrage
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
import traceback
import xmltodict
from xml.parsers.expat import ExpatError

import logging
from sickbeard import tvcache
from sickbeard import helpers
from sickbeard.common import USER_AGENT
from sickbeard.providers import generic


class ExtraTorrentProvider(generic.TorrentProvider):
    def __init__(self):
        generic.TorrentProvider.__init__(self, "ExtraTorrent")

        self.urls = {
            'index': 'http://extratorrent.cc',
            'rss': 'http://extratorrent.cc/rss.xml',
        }

        self.url = self.urls[b'index']

        self.supportsBacklog = True
        self.public = True
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = ExtraTorrentCache(self)
        self.headers.update({'User-Agent': USER_AGENT})
        self.search_params = {'cid': 8}

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_strings.keys():
            logging.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:

                if mode is not 'RSS':
                    logging.debug("Search string: %s " % search_string)

                try:
                    self.search_params.update({'type': ('search', 'rss')[mode is 'RSS'], 'search': search_string})
                    data = self.getURL(self.urls[b'rss'], params=self.search_params)
                    if not data:
                        logging.debug("No data returned from provider")
                        continue

                    if not data.startswith('<?xml'):
                        logging.info('Expected xml but got something else, is your mirror failing?')
                        continue

                    try:
                        data = xmltodict.parse(data)
                    except ExpatError:
                        logging.error("Failed parsing provider. Traceback: %r\n%r" % (traceback.format_exc(), data))
                        continue

                    if not all([data, 'rss' in data, 'channel' in data[b'rss'], 'item' in data[b'rss'][b'channel']]):
                        logging.debug("Malformed rss returned, skipping")
                        continue

                    # https://github.com/martinblech/xmltodict/issues/111
                    entries = data[b'rss'][b'channel'][b'item']
                    entries = entries if isinstance(entries, list) else [entries]

                    for item in entries:
                        title = item[b'title'].decode('utf-8')
                        # info_hash = item[b'info_hash']
                        size = int(item[b'size'])
                        seeders = helpers.tryInt(item[b'seeders'], 0)
                        leechers = helpers.tryInt(item[b'leechers'], 0)
                        download_url = item[b'enclosure']['@url'] if 'enclosure' in item else self._magnet_from_details(
                                item[b'link'])

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
                    logging.error("Failed parsing provider. Traceback: %r" % traceback.format_exc())

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def _magnet_from_details(self, link):
        details = self.getURL(link)
        if not details:
            return ''

        match = re.search(r'href="(magnet.*?)"', details)
        if not match:
            return ''

        return match.group(1)

    def seedRatio(self):
        return self.ratio


class ExtraTorrentCache(tvcache.TVCache):
    def __init__(self, provider_obj):
        tvcache.TVCache.__init__(self, provider_obj)

        self.minTime = 30

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_strings)}


provider = ExtraTorrentProvider()
