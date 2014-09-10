# -*- coding: latin-1 -*-
# Author: djoole <bobby.djoole@gmail.com>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

import traceback
import time
import re
import datetime
import sickbeard
import generic
from lib import requests
from sickbeard.common import USER_AGENT, Quality, cpu_presets
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import show_name_helpers
from sickbeard.bs4_parser import BS4Parser
from sickbeard import db

class T411Provider(generic.TorrentProvider):
    urls = {'base_url': 'http://www.t411.me/',
            'search': 'http://www.t411.me/torrents/search/?name=%s&cat=210&subcat=433&search=%s&submit=Recherche',
            'login_page': 'http://www.t411.me/users/login/',
            'download': 'http://www.t411.me/torrents/download/?id=%s',
    }

    def __init__(self):

        generic.TorrentProvider.__init__(self, "T411")

        self.supportsBacklog = True

        self.enabled = False
        self.username = None
        self.password = None
        self.ratio = None

        self.cache = T411Cache(self)

        self.url = self.urls['base_url']

        self.last_login_check = None

        self.login_opener = None

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 't411.png'

    def getQuality(self, item, anime=False):

        quality = Quality.sceneQuality(item[0], anime)
        return quality

    def getLoginParams(self):
        return {
            'login': self.username,
            'password': self.password,
            'remember': '1',
        }

    def loginSuccess(self, output):
        if "<span>Ratio: <strong class" in output.text:
            return True
        else:
            return False

    def _doLogin(self):

        now = time.time()

        if self.login_opener and self.last_login_check < (now - 3600):
            try:
                output = self.login_opener.open(self.urls['test'])
                if self.loginSuccess(output):
                    self.last_login_check = now
                    return True
                else:
                    self.login_opener = None
            except:
                self.login_opener = None

        if self.login_opener:
            return True

        try:
            login_params = self.getLoginParams()
            self.session = requests.Session()
            self.session.headers.update({'User-Agent': USER_AGENT})
            data = self.session.get(self.urls['login_page'], verify=False)
            output = self.session.post(self.urls['login_page'], data=login_params, verify=False)
            if self.loginSuccess(output):
                self.last_login_check = now
                self.login_opener = self.session
                return True

            error = 'unknown'
        except:
            error = traceback.format_exc()
            self.login_opener = None

        self.login_opener = None
        logger.log(u'Failed to login:' + str(error), logger.ERROR)
        return False

    def _get_season_search_strings(self, ep_obj):

        search_string = {'Season': []}
        for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
            if ep_obj.show.air_by_date or ep_obj.show.sports:
                ep_string = show_name + '.' + str(ep_obj.airdate).split('-')[0]
            elif ep_obj.show.anime:
                ep_string = show_name + '.' + "%d" % ep_obj.scene_absolute_number
            else:
                ep_string = show_name + '.S%02d' % int(ep_obj.scene_season)  #1) showName.SXX

            search_string['Season'].append(ep_string)

        return [search_string]

    def _get_episode_search_strings(self, ep_obj, add_string=''):

        search_string = {'Episode': []}

        if not ep_obj:
            return []

        if self.show.air_by_date:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + '.' + \
                            str(ep_obj.airdate).replace('-', '|')
                search_string['Episode'].append(ep_string)
        elif self.show.sports:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + '.' + \
                            str(ep_obj.airdate).replace('-', '|') + '|' + \
                            ep_obj.airdate.strftime('%b')
                search_string['Episode'].append(ep_string)
        elif self.show.anime:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + '.' + \
                            "%i" % int(ep_obj.scene_absolute_number)
                search_string['Episode'].append(ep_string)
        else:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = show_name_helpers.sanitizeSceneName(show_name) + '.' + \
                            sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season,
                                                                  'episodenumber': ep_obj.scene_episode}
                search_string['Episode'].append(re.sub('\s+', '.', ep_string))

        return [search_string]

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return []

        for mode in search_params.keys():

            for search_string in search_params[mode]:

                if search_string == '':
                    search_string2 = ''
                else:
                    search_string2 = '%40name+' + search_string + '+'
                    
                searchURL = self.urls['search'] % (search_string, search_string2)
                logger.log(u"" + self.name + " search page URL: " + searchURL, logger.DEBUG)

                data = self.getURL(searchURL)

                if not data:
                    continue

                try:
                    with BS4Parser(data.decode('iso-8859-1'), features=["html5lib", "permissive"]) as html:
                        resultsTable = html.find('table', attrs={'class': 'results'})

                        if not resultsTable:
                            logger.log(u"The Data returned from " + self.name + " do not contains any torrent",
                                       logger.DEBUG)
                            continue

                        entries = resultsTable.find("tbody").findAll("tr")

                        if len(entries) > 0:
                            for result in entries:

                                try:
                                    link = result.find('a', title=True)
                                    torrentName = link['title']
                                    torrent_name = str(torrentName)
                                    torrentId = result.find_all('td')[2].find_all('a')[0]['href'][1:].replace('torrents/nfo/?id=','')
                                    torrent_download_url = (self.urls['download'] % torrentId).encode('utf8')
                                except (AttributeError, TypeError):
                                    continue

                                if not torrent_name or not torrent_download_url:
                                    continue

                                item = torrent_name, torrent_download_url
                                logger.log(u"Found result: " + torrent_name + " (" + torrent_download_url + ")", logger.DEBUG)
                                items[mode].append(item)

                        else:
                            logger.log(u"The Data returned from " + self.name + " do not contains any torrent",
                                       logger.WARNING)
                            continue

                except Exception, e:
                    logger.log(u"Failed parsing " + self.name + " Traceback: " + traceback.format_exc(),
                               logger.ERROR)

            results += items[mode]

        return results

    def _get_title_and_url(self, item):

        title, url = item

        if title:
            title = u'' + title
            title = title.replace(' ', '.')

        if url:
            url = str(url).replace('&amp;', '&')

        return title, url

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


class T411Cache(tvcache.TVCache):
    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # Only poll T411 every 10 minutes max
        self.minTime = 10

    def _getDailyData(self):
        search_params = {'RSS': ['']}
        return self.provider._doSearch(search_params)


provider = T411Provider()
