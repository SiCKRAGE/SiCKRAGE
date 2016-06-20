
# Author: Mr_Orange <mr_orange@hotmail.it>
# URL: http://github.com/SiCKRAGETV/SickRage/
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

import traceback
from urllib import urlencode
from xml.parsers.expat import ExpatError

import xmltodict

import sickrage
from sickrage.core.caches import tv_cache
from sickrage.core.helpers import convert_size
from sickrage.providers import TorrentProvider


class KATProvider(TorrentProvider):
    def __init__(self):
        super(KATProvider, self).__init__("KickAssTorrents", 'kickass.unblocked.la')

        self.supportsBacklog = True

        self.confirmed = True
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = KATCache(self)

        self.urls.update({
            'search': '{base_url}/%s/'.format(base_url=self.urls['base_url'])
        })

        self.search_params = {
            'q': '',
            'field': 'seeders',
            'sorder': 'desc',
            'rss': 1,
            'category': 'tv'
        }

    def search(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):
        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        # select the correct category
        anime = (self.show and self.show.anime) or (epObj and epObj.show and epObj.show.anime) or False
        self.search_params['category'] = ('tv', 'anime')[anime]

        for mode in search_strings.keys():
            sickrage.srCore.srLogger.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:

                self.search_params['q'] = search_string.encode('utf-8') if mode != 'RSS' else ''
                self.search_params['field'] = 'seeders' if mode != 'RSS' else 'time_add'

                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug("Search string: %s" % search_string)

                url_fmt_string = 'usearch' if mode != 'RSS' else search_string
                try:
                    searchURL = self.urls['search'] % url_fmt_string + '?' + urlencode(self.search_params)
                    sickrage.srCore.srLogger.debug("Search URL: %s" % searchURL)

                    try:
                        data = sickrage.srCore.srWebSession.get(searchURL).text
                    except Exception:
                        sickrage.srCore.srLogger.debug("No data returned from provider")
                        continue

                    if not data.startswith('<?xml'):
                        sickrage.srCore.srLogger.info('Expected xml but got something else, is your mirror failing?')
                        continue

                    try:
                        data = xmltodict.parse(data)
                    except ExpatError:
                        sickrage.srCore.srLogger.error("Failed parsing provider. Traceback: %r\n%r" % (traceback.format_exc(), data))
                        continue

                    if not all([data, 'rss' in data, 'channel' in data['rss'], 'item' in data['rss']['channel']]):
                        sickrage.srCore.srLogger.debug("Malformed rss returned, skipping")
                        continue

                    # https://github.com/martinblech/xmltodict/issues/111
                    entries = data['rss']['channel']['item']
                    entries = entries if isinstance(entries, list) else [entries]

                    for item in entries:
                        try:
                            title = item['title']
                            # Use the torcache link kat provides,
                            # unless it is not torcache or we are not using blackhole
                            # because we want to use magnets if connecting direct to client
                            # so that proxies work.
                            download_url = item['enclosure']['@url']
                            if sickrage.srCore.srConfig.TORRENT_METHOD != "blackhole" or 'torcache' not in download_url:
                                download_url = item['torrent:magnetURI']

                            seeders = int(item['torrent:seeds'])
                            leechers = int(item['torrent:peers'])
                            verified = bool(int(item['torrent:verified']) or 0)
                            size = convert_size(item['torrent:contentLength'])

                            info_hash = item['torrent:infoHash']
                        except (AttributeError, TypeError, KeyError):
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

                        if self.confirmed and not verified:
                            if mode != 'RSS':
                                sickrage.srCore.srLogger.debug(
                                        "Found result " + title + " but that doesn't seem like a verified result so I'm ignoring it")
                            continue

                        item = title, download_url, size, seeders, leechers, info_hash
                        if mode != 'RSS':
                            sickrage.srCore.srLogger.debug("Found result: %s " % title)

                        items[mode].append(item)

                except Exception:
                    sickrage.srCore.srLogger.error("Failed parsing provider. Traceback: %r" % traceback.format_exc())

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class KATCache(tv_cache.TVCache):
    def __init__(self, provider_obj):
        tv_cache.TVCache.__init__(self, provider_obj)

        # only poll KickAss every 10 minutes max
        self.minTime = 20

    def _getRSSData(self):
        search_params = {'RSS': ['tv', 'anime']}
        return {'entries': self.provider.search(search_params)}
