# Author: Idan Gutman
# Modified by jkaberg, https://github.com/jkaberg for SceneAccess
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import re
import datetime
import time

import sickbeard
import generic
import urllib
from sickbeard.common import Quality, cpu_presets
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import db
from sickbeard import classes
from sickbeard import helpers
from sickbeard import show_name_helpers
from sickbeard.bs4_parser import BS4Parser
from unidecode import unidecode
from sickbeard.helpers import sanitizeSceneName


class SCCProvider(generic.TorrentProvider):

    def __init__(self):

        generic.TorrentProvider.__init__(self, "SceneAccess")

        self.supportsBacklog = True
        self.public = False

        self.enabled = False
        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = SCCCache(self)

        self.urls = {'base_url': 'https://sceneaccess.eu',
                'login': 'https://sceneaccess.eu/login',
                'detail': 'https://www.sceneaccess.eu/details?id=%s',
                'search': 'https://sceneaccess.eu/browse?search=%s&method=1&%s',
                'nonscene': 'https://sceneaccess.eu/nonscene?search=%s&method=1&c44=44&c45=44',
                'foreign': 'https://sceneaccess.eu/foreign?search=%s&method=1&c34=34&c33=33',
                'archive': 'https://sceneaccess.eu/archive?search=%s&method=1&c26=26',
                'download': 'https://www.sceneaccess.eu/%s',
                }

        self.url = self.urls['base_url']

        self.categories = "c27=27&c17=17&c11=11"

    def isEnabled(self):
        return self.enabled

    def _doLogin(self):

        login_params = {'username': self.username,
                        'password': self.password,
                        'submit': 'come on in',
        }


        response = self.getURL(self.urls['login'],  post_data=login_params, timeout=30)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('Username or password incorrect', response) \
                or re.search('<title>SceneAccess \| Login</title>', response):
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def _isSection(self, section, text):
        title = '<title>.+? \| %s</title>' % section
        return re.search(title, text, re.IGNORECASE)

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []

        if not self._doLogin():
            return results

        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_strings.keys():
            if mode != 'RSS':
                logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                searchURLS = []
                if search_mode == 'sponly':
                    searchURLS += [self.urls['archive'] % (urllib.quote(search_string))]
                else:
                    searchURLS += [self.urls['search'] % (urllib.quote(search_string), self.categories)]
                    searchURLS += [self.urls['nonscene'] % (urllib.quote(search_string))]
                    searchURLS += [self.urls['foreign'] % (urllib.quote(search_string))]

                for searchURL in searchURLS:
                    try:
                        logger.log(u"Search URL: %s" %  searchURL, logger.DEBUG)
                        data = self.getURL(searchURL)
                        time.sleep(cpu_presets[sickbeard.CPU_PRESET])
                    except Exception as e:
                        logger.log(u"Unable to fetch data. Error: %s" % repr(e), logger.WARNING)

                    if not data:
                        continue

                    with BS4Parser(data, features=["html5lib", "permissive"]) as html:
                        torrent_table = html.find('table', attrs={'id': 'torrents-table'})
                        torrent_rows = torrent_table.find_all('tr') if torrent_table else []

                        #Continue only if at least one Release is found
                        if len(torrent_rows) < 2:
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        for result in torrent_table.find_all('tr')[1:]:

                            try:
                                link = result.find('td', attrs={'class': 'ttr_name'}).find('a')
                                all_urls = result.find('td', attrs={'class': 'td_dl'}).find_all('a', limit=2)
                                # Foreign section contain two links, the others one
                                if self._isSection('Foreign', data):
                                    url = all_urls[1]
                                else:
                                    url = all_urls[0]

                                title = link.string
                                if re.search('\.\.\.', title):
                                    data = self.getURL(self.url + "/" + link['href'])
                                    if data:
                                        with BS4Parser(data) as details_html:
                                            title = re.search('(?<=").+(?<!")', details_html.title.string).group(0)
                                download_url = self.urls['download'] % url['href']
                                id = int(link['href'].replace('details?id=', ''))
                                seeders = int(result.find('td', attrs={'class': 'ttr_seeders'}).string)
                                leechers = int(result.find('td', attrs={'class': 'ttr_leechers'}).string)
                                #FIXME
                                size = -1
                            except (AttributeError, TypeError):
                                continue

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


class SCCCache(tvcache.TVCache):
    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # only poll SCC every 20 minutes max
        self.minTime = 20

    def _getRSSData(self):
        search_params = u''
        return {'entries': self.provider._doSearch(search_params)}

provider = SCCProvider()
