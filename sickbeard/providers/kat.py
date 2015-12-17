# -*- coding: utf-8 -*-
# Author: Mr_Orange <mr_orange@hotmail.it>
# URL: http://code.google.com/p/sickbeard/
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

import xmltodict

import sickbeard
import logging
from sickbeard import tvcache
from sickbeard.common import USER_AGENT
from sickbeard.providers import generic
from xml.parsers.expat import ExpatError


class KATProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "KickAssTorrents")

        self.supportsBacklog = True
        self.public = True

        self.confirmed = True
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = KATCache(self)

        self.urls = {
            'base_url': 'https://kickass.unblocked.la/',
            'search': 'https://kickass.unblocked.la/%s/',
        }

        self.url = self.urls[b'base_url']
        self.headers.update({'User-Agent': USER_AGENT})

        self.search_params = {
            'q': '',
            'field': 'seeders',
            'sorder': 'desc',
            'rss': 1,
            'category': 'tv'
        }

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):
        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        # select the correct category
        anime = (self.show and self.show.anime) or (epObj and epObj.show and epObj.show.anime) or False
        self.search_params[b'category'] = ('tv', 'anime')[anime]

        for mode in search_strings.keys():
            logging.debug("Search Mode: %s" % mode)
            for search_string in search_strings[mode]:

                self.search_params[b'q'] = search_string.encode('utf-8') if mode is not 'RSS' else ''
                self.search_params[b'field'] = 'seeders' if mode is not 'RSS' else 'time_add'

                if mode is not 'RSS':
                    logging.debug("Search string: %s" % search_string)

                url_fmt_string = 'usearch' if mode is not 'RSS' else search_string
                try:
                    searchURL = self.urls[b'search'] % url_fmt_string + '?' + urlencode(self.search_params)
                    logging.debug("Search URL: %s" % searchURL)
                    data = self.getURL(searchURL)
                    # data = self.getURL(self.urls[('search', 'rss')[mode is 'RSS']], params=self.search_params)
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
                        try:
                            title = item[b'title']
                            # Use the torcache link kat provides,
                            # unless it is not torcache or we are not using blackhole
                            # because we want to use magnets if connecting direct to client
                            # so that proxies work.
                            download_url = item[b'enclosure']['@url']
                            if sickbeard.TORRENT_METHOD != "blackhole" or 'torcache' not in download_url:
                                download_url = item['torrent:magnetURI']

                            seeders = int(item['torrent:seeds'])
                            leechers = int(item['torrent:peers'])
                            verified = bool(int(item['torrent:verified']) or 0)
                            size = int(item['torrent:contentLength'])

                            info_hash = item['torrent:infoHash']
                            # link = item[b'link']

                        except (AttributeError, TypeError, KeyError):
                            continue

                        if not all([title, download_url]):
                            continue

                        # Filter unseeded torrent
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode is not 'RSS':
                                logging.debug(
                                    "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                        title, seeders, leechers))
                            continue

                        if self.confirmed and not verified:
                            if mode is not 'RSS':
                                logging.debug(
                                    "Found result " + title + " but that doesn't seem like a verified result so I'm ignoring it")
                            continue

                        item = title, download_url, size, seeders, leechers, info_hash
                        if mode is not 'RSS':
                            logging.debug("Found result: %s " % title)

                        items[mode].append(item)

                except Exception:
                    logging.error("Failed parsing provider. Traceback: %r" % traceback.format_exc())

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class KATCache(tvcache.TVCache):
    def __init__(self, provider_obj):
        tvcache.TVCache.__init__(self, provider_obj)

        # only poll KickAss every 10 minutes max
        self.minTime = 20

    def _getRSSData(self):
        search_params = {'RSS': ['tv', 'anime']}
        return {'entries': self.provider._doSearch(search_params)}


provider = KATProvider()
