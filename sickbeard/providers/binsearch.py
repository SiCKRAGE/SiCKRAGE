#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Author: echel0n <sickrage.tv@gmail.com>
# URL: http://www.github.com/sickragetv/sickrage/
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

import urllib
import re

from sickbeard.providers import generic

import logging
from sickbeard import tvcache


class BinSearchProvider(generic.NZBProvider):
    def __init__(self):
        generic.NZBProvider.__init__(self, "BinSearch")

        self.public = True
        self.cache = BinSearchCache(self)
        self.urls = {'base_url': 'https://www.binsearch.info/'}
        self.url = self.urls[b'base_url']


class BinSearchCache(tvcache.TVCache):
    def __init__(self, provider_obj):
        tvcache.TVCache.__init__(self, provider_obj)
        # only poll Binsearch every 30 minutes max
        self.minTime = 30

        # compile and save our regular expressions

        # this pulls the title from the URL in the description
        self.descTitleStart = re.compile(r'^.*https?://www\.binsearch\.info/.b=')
        self.descTitleEnd = re.compile('&amp;.*$')

        # these clean up the horrible mess of a title if the above fail
        self.titleCleaners = [
            re.compile(r'.?yEnc.?\(\d+/\d+\)$'),
            re.compile(r' \[\d+/\d+\] '),
        ]

    def _get_title_and_url(self, item):
        """
        Retrieves the title and URL data from the item XML node

        item: An elementtree.ElementTree element representing the <item> tag of the RSS feed

        Returns: A tuple containing two strings representing title and URL respectively
        """

        title = item.get('description')
        if title:
            title = '' + title
            if self.descTitleStart.match(title):
                title = self.descTitleStart.sub('', title)
                title = self.descTitleEnd.sub('', title)
                title = title.replace('+', '.')
            else:
                # just use the entire title, looks hard/impossible to parse
                title = item.get('title')
                if title:
                    for titleCleaner in self.titleCleaners:
                        title = titleCleaner.sub('', title)

        url = item.get('link')
        if url:
            url = url.replace('&amp;', '&')

        return (title, url)

    def updateCache(self):
        # check if we should update
        if self.shouldUpdate():
            # clear cache
            self._clearCache()

            # set updated
            self.setLastUpdate()

            cl = []
            for group in ['alt.binaries.hdtv', 'alt.binaries.hdtv.x264', 'alt.binaries.tv', 'alt.binaries.tvseries',
                          'alt.binaries.teevee']:
                url = self.provider.url + 'rss.php?'
                urlArgs = {'max': 1000, 'g': group}

                url += urllib.urlencode(urlArgs)

                logging.debug("Cache update URL: %s " % url)

                for item in self.getRSSFeed(url)['entries'] or []:
                    ci = self._parseItem(item)
                    if ci is not None:
                        cl.append(ci)

            if len(cl) > 0:
                myDB = self._getDB()
                myDB.mass_action(cl)

        return True

    def _checkAuth(self, data):
        return data if data[b'feed'] and data[b'feed'][b'title'] != 'Invalid Link' else None


provider = BinSearchProvider()
