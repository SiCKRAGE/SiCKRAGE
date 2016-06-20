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
from xml.parsers.expat import ExpatError

import xmltodict

import sickrage
from sickrage.core.caches import tv_cache
from sickrage.core.helpers import tryInt
from sickrage.providers import TorrentProvider


class ExtraTorrentProvider(TorrentProvider):
    def __init__(self):
        super(ExtraTorrentProvider, self).__init__("ExtraTorrent",'extratorrent.cc')

        self.urls.update({
            'rss': '{base_url}/rss.xml'.format(base_url=self.urls['base_url'])
        })

        self.supportsBacklog = True

        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = ExtraTorrentCache(self)

        self.search_params = {'cid': 8}

    def search(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_strings.keys():
            sickrage.srCore.srLogger.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug("Search string: %s " % search_string)

                try:
                    self.search_params.update({'type': ('search', 'rss')[mode == 'RSS'], 'search': search_string})

                    try:
                        data = sickrage.srCore.srWebSession.get(self.urls['rss'], params=self.search_params).text
                    except Exception:
                        sickrage.srCore.srLogger.debug("No data returned from provider")
                        continue

                    if not data.startswith('<?xml'):
                        sickrage.srCore.srLogger.info('Expected xml but got something else, is your mirror failing?')
                        continue

                    try:
                        data = xmltodict.parse(data)
                    except ExpatError:
                        sickrage.srCore.srLogger.error(
                            "Failed parsing provider. Traceback: %r\n%r" % (traceback.format_exc(), data))
                        continue

                    if not all([data, 'rss' in data, 'channel' in data['rss'], 'item' in data['rss']['channel']]):
                        sickrage.srCore.srLogger.debug("Malformed rss returned, skipping")
                        continue

                    # https://github.com/martinblech/xmltodict/issues/111
                    entries = data['rss']['channel']['item']
                    entries = entries if isinstance(entries, list) else [entries]

                    for item in entries:
                        title = item['title'].decode('utf-8')
                        # info_hash = item['info_hash']
                        size = int(item['size'])
                        seeders = tryInt(item['seeders'], 0)
                        leechers = tryInt(item['leechers'], 0)
                        download_url = item['enclosure']['@url'] if 'enclosure' in item else self._magnet_from_details(
                            item['link'])

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

                except (AttributeError, TypeError, KeyError, ValueError):
                    sickrage.srCore.srLogger.error("Failed parsing provider. Traceback: %r" % traceback.format_exc())

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def _magnet_from_details(self, link):
        try:
            details = sickrage.srCore.srWebSession.get(link).text
            return re.search(r'href="(magnet.*?)"', details).group(1) or ''
        except Exception:
            return ''

    def seedRatio(self):
        return self.ratio


class ExtraTorrentCache(tv_cache.TVCache):
    def __init__(self, provider_obj):
        tv_cache.TVCache.__init__(self, provider_obj)

        self.minTime = 30

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider.search(search_strings)}
