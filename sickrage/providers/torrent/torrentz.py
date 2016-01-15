# Author: Dustyn Gibson <miigotu@gmail.com>
# URL: https://github.com/SiCKRAGETV/SickRage
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
import traceback
from urllib import quote_plus
from xml.parsers.expat import ExpatError

import xmltodict
from tornado import gen

import sickrage
from sickrage.core.caches import tv_cache
from sickrage.core.common import cpu_presets
from sickrage.providers import TorrentProvider


class TORRENTZProvider(TorrentProvider):
    def __init__(self):

        super(TORRENTZProvider, self).__init__("Torrentz")
        self.public = True
        self.supportsBacklog = True
        self.confirmed = True
        self.ratio = None
        self.minseed = None
        self.minleech = None
        self.cache = TORRENTZCache(self)
        self.urls = {'verified': 'https://torrentz.eu/feed_verified',
                     'feed': 'https://torrentz.eu/feed',
                     'base': 'https://torrentz.eu/'}
        self.url = self.urls['base']

    def seedRatio(self):
        return self.ratio

    @staticmethod
    def _split_description(description):
        match = re.findall(r'[0-9]+', description)
        return int(match[0]) * 1024 ** 2, int(match[1]), int(match[2])

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):
        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_strings:
            for search_string in search_strings[mode]:
                search_url = self.urls['verified'] if self.confirmed else self.urls['feed']
                if mode is not 'RSS':
                    search_url += '?q=' + quote_plus(search_string)

                sickrage.LOGGER.info(search_url)
                data = self.getURL(search_url)
                if not data:
                    sickrage.LOGGER.info('Seems to be down right now!')
                    continue

                if not data.startswith("<?xml"):
                    sickrage.LOGGER.debug('Wrong data returned from: ' + search_url)
                    continue

                if not data.startswith('<?xml'):
                    sickrage.LOGGER.info('Expected xml but got something else, is your mirror failing?')
                    continue

                try:
                    data = xmltodict.parse(data)
                except ExpatError:
                    sickrage.LOGGER.error("Failed parsing provider. Traceback: %r\n%r" % (traceback.format_exc(), data))
                    continue

                if not all([data, 'rss' in data, 'channel' in data[b'rss'], 'item' in data[b'rss'][b'channel']]):
                    sickrage.LOGGER.debug("Malformed rss returned or no results, skipping")
                    continue

                gen.sleep(cpu_presets[sickrage.CPU_PRESET])

                # https://github.com/martinblech/xmltodict/issues/111
                entries = data[b'rss'][b'channel'][b'item']
                entries = entries if isinstance(entries, list) else [entries]

                for item in entries:
                    try:
                        if 'tv' not in item[b'category']:
                            continue
                    except:
                        continue

                    title = item.get('title', '').rsplit(' ', 1)[0].replace(' ', '.')
                    t_hash = item.get('guid', '').rsplit('/', 1)[-1]

                    if not all([title, t_hash]):
                        continue

                    # TODO: Add method to generic provider for building magnet from hash.
                    download_url = "magnet:?xt=urn:btih:" + t_hash + "&dn=" + title + "&tr=udp://tracker.openbittorrent.com:80&tr=udp://tracker.coppersurfer.tk:6969&tr=udp://open.demonii.com:1337&tr=udp://tracker.leechers-paradise.org:6969&tr=udp://exodus.desync.com:6969"
                    size, seeders, leechers = self._split_description(item.get('description', ''))

                    # Filter unseeded torrent
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode is not 'RSS':
                            sickrage.LOGGER.debug(
                                    "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                            title, seeders, leechers))
                        continue

                    items[mode].append((title, download_url, size, seeders, leechers))

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)
            results += items[mode]

        return results


class TORRENTZCache(tv_cache.TVCache):
    def __init__(self, provider_obj):
        tv_cache.TVCache.__init__(self, provider_obj)

        # only poll every 15 minutes max
        self.minTime = 15

    def _getRSSData(self):
        return {'entries': self.provider._doSearch({'RSS': ['']})}
