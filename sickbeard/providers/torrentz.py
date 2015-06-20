# Author: Dustyn Gibson <miigotu@gmail.com>
# URL: https://github.com/junalmeida/Sick-Beard
# Ported by :Matigonkas
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

import urllib

import re
import time
import requests
from requests.exceptions import Timeout, ConnectTimeout

import generic

import sickbeard
from sickbeard.common import *
from sickbeard import logger
from sickbeard import tvcache
from sickbeard.show_name_helpers import allPossibleShowNames
from sickbeard.helpers import sanitizeSceneName
from bs4 import BeautifulSoup

class TORRENTZProvider(generic.TorrentProvider):

    def __init__(self):

        generic.TorrentProvider.__init__(self, "Torrentz")

        self.supportsBacklog = True

        self.confirmed = False
        self.cache = TORRENTZCache(self)

        self.urls = {'verified': 'https://torrentz.eu/feed_verified?p=%d',
                         'feed': 'https://torrentz.eu/feed?p=%d',
                         'base': 'https://torrentz.eu/',
                    }
        self.session = requests.Session()

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'torrentz.png'

    def _get_season_search_strings(self, epObj, season=None):
        if not epObj or season:
            return []

        strings = []
        for title in set(allPossibleShowNames(epObj.show)):
            if epObj.show.air_by_date or epObj.show.sports:
                season = str(epObj.airdate).split('-')[0]
            elif epObj.show.anime:
                season = '%d' % epObj.scene_absolute_number
            else:
                season = 'S%02d' % epObj.season

            strings.append(u'%s %s' % (sanitizeSceneName(title), season))

        return strings

    def _get_episode_search_strings(self, epObj, add_string=''):
        if not epObj:
            return []

        strings = []
        for title in set(allPossibleShowNames(epObj.show)):
            if epObj.show.air_by_date or epObj.show.sports:
                season = str(epObj.airdate).replace('-', ' ')
            elif epObj.show.anime:
                episode = '%d' % epObj.scene_absolute_number
            else:
                episode = 'S%02dE%02d' % (epObj.season, epObj.episode)

            if add_string:
                episode += ' ' + add_string

            strings.append([u'%s %s' % (sanitizeSceneName(title), episode)])

        return strings

    def _split_description(self, description):
        match = re.findall(r'[0-9]+', description)
        return (int(match[0]) *1024 * 1024, match[1], match[2])

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):
        items = []
        for search_string in search_strings:
            if self.confirmed:
                search = self.urls['verified']
            else:
                search = self.urls['feed']
            if 'RSS' not in search_string:
                search +=  'q=' + urllib.quote_plus(search_string)

            for p in range(0,2):
                try:
                    time.sleep(cpu_presets[sickbeard.CPU_PRESET])
                    page = self.getURL(search % p, timeout=10)
                except ConnectTimeout, Timeout:
                    logger.log('Seems to be down right now!')
                    continue

                if not page or not page.startswith("<?xml"):
                    logger.log('Wrong data returned from: ' + search % p, logger.WARNING)
                    continue

                data = BeautifulSoup(page)
                for item in data.find_all('item'):
                    if 'tv' not in item.category.text:
                        continue

                    title = item.title.text
                    url = item.guid.text.split('/')[-1]
                    dsize, seeds, peers = self._split_description(item.description.text)

                    # Have to get the details page to get the correct title
                    try:
                        time.sleep(cpu_presets[sickbeard.CPU_PRESET])
                        details = self.getURL(self.urls['base'] + url, timeout=10)
                    except ConnectTimeout, Timeout:
                        logger.log('Seems to be down right now!')
                        continue

                    if details and details.startswith('<!DOCTYPE html>'):
                        dpage = BeautifulSoup(details)
                        title = dpage.find('dt').a['href'].split('/')[-2]
                        del dpage

                    logger.log('Adding item: ' + str(title, url, dsize, seeds, peers), logger.DEBUG)
                    items.append((title, url, dsize, seeds, peers))
        return items

    def _get_size(self, item):
        title, url, size, seeders, leechers = item
        return size

    def _get_title_and_url(self, item):

        title, url, size, seeders, leechers = item

        if title:
            title = self._clean_title_from_provider(title)

        if url:
            url = url.replace('&amp;', '&')

        return (title, url)

class TORRENTZCache(tvcache.TVCache):

    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # only poll every 15 minutes max
        self.minTime = 15

    def _getRSSData(self):
         params = {'RSS': ['rss']}
         return {'entries': self.provider._doSearch(params)}

provider = TORRENTZProvider()
