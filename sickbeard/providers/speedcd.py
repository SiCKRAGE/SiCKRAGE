# Author: Mr_Orange
# URL: https://github.com/mr-orange/Sick-Beard
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

import re
import datetime
import sickbeard
import generic

from sickbeard.common import Quality
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import db
from sickbeard import classes
from sickbeard import helpers
from sickbeard import show_name_helpers
from sickbeard.helpers import sanitizeSceneName


class SpeedCDProvider(generic.TorrentProvider):

    def __init__(self):

        generic.TorrentProvider.__init__(self, "Speedcd")

        self.supportsBacklog = True
        self.public = False

        self.enabled = False
        self.username = None
        self.password = None
        self.ratio = None
        self.freeleech = False
        self.minseed = None
        self.minleech = None

        self.cache = SpeedCDCache(self)

        self.urls = {'base_url': 'http://speed.cd/',
                'login': 'http://speed.cd/take_login.php',
                'detail': 'http://speed.cd/t/%s',
                'search': 'http://speed.cd/V3/API/API.php',
                'download': 'http://speed.cd/download.php?torrent=%s',
                }

        self.url = self.urls['base_url']

        self.categories = {'Season': {'c14': 1}, 'Episode': {'c2': 1, 'c49': 1}, 'RSS': {'c14': 1, 'c2': 1, 'c49': 1}}

    def isEnabled(self):
        return self.enabled

    def _doLogin(self):

        login_params = {'username': self.username,
                        'password': self.password
        }

        response = self.getURL(self.urls['login'],  post_data=login_params, timeout=30)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('Incorrect username or Password. Please try again.', response):
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return results

        for mode in search_params.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                search_string = '+'.join(search_string.split())

                post_data = dict({'/browse.php?': None, 'cata': 'yes', 'jxt': 4, 'jxw': 'b', 'search': search_string},
                                 **self.categories[mode])

                parsedJSON = self.getURL(self.urls['search'], post_data=post_data, json=True)
                if not parsedJSON:
                    continue

                try:
                    torrents = parsedJSON.get('Fs', [])[0].get('Cn', {}).get('torrents', [])
                except:
                    continue

                for torrent in torrents:

                    if self.freeleech and not torrent['free']:
                        continue

                    title = re.sub('<[^>]*>', '', torrent['name'])
                    download_url = self.urls['download'] % (torrent['id'])
                    seeders = int(torrent['seed'])
                    leechers = int(torrent['leech'])
                    #FIXME
                    size = -1

                    if not all([title, download_url]):
                        continue

                    #Filter unseeded torrent
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode != 'RSS':
                            logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                        continue

                    item = title, download_url, size, seeders, leechers
                    if mode != 'RSS':
                        logger.log(u"Found result: %s " % title, logger.DEBUG)

                    items[mode].append(item)

            #For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def findPropers(self, search_date=datetime.datetime.today()):

        results = []

        myDB = db.DBConnection()
        sqlResults = myDB.select(
            'SELECT s.show_name, e.showid, e.season, e.episode, e.status, e.airdate FROM tv_episodes AS e' +
            ' INNER JOIN tv_shows AS s ON (e.showid = s.indexer_id)' +
            ' WHERE e.airdate >= ' + str(search_date.toordinal()) +
            ' AND (e.status IN (' + ','.join([str(x) for x in Quality.DOWNLOADED]) + ')' +
            ' OR (e.status IN (' + ','.join([str(x) for x in Quality.SNATCHED]) + ')))'
        )

        if not sqlResults:
            return []

        for sqlshow in sqlResults:
            self.show = helpers.findCertainShow(sickbeard.showList, int(sqlshow["showid"]))
            if self.show:
                curEp = self.show.getEpisode(int(sqlshow["season"]), int(sqlshow["episode"]))

                searchString = self._get_episode_search_strings(curEp, add_string='PROPER|REPACK')

                for item in self._doSearch(searchString[0]):
                    title, url = self._get_title_and_url(item)
                    results.append(classes.Proper(title, url, datetime.datetime.today(), self.show))

        return results

    def seedRatio(self):
        return self.ratio


class SpeedCDCache(tvcache.TVCache):
    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # only poll Speedcd every 20 minutes max
        self.minTime = 20

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}

provider = SpeedCDProvider()
