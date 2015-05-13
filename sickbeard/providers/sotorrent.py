# -*- coding: latin-1 -*-
# Author: Staros https://github.com/JohnDooe
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

import traceback
import re
import datetime
import time
from lib.requests.auth import AuthBase
import sickbeard
import generic

from lib import requests
from lib.requests import exceptions

from sickbeard.common import Quality
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import show_name_helpers
from sickbeard import db
from sickbeard import helpers
from sickbeard import classes
from sickbeard.helpers import sanitizeSceneName
from sickbeard.exceptions import ex
from sickbeard.bs4_parser import BS4Parser


class SOTORRENTProvider(generic.TorrentProvider):
    def __init__(self):
        generic.TorrentProvider.__init__(self, "sotorrent")

        self.supportsBacklog = True
        self.enabled = False
        self.username = None
        self.password = None
        self.ratio = None

        self.urls = {'base_url': 'https://www.so-torrent.com/',
                     'search': 'https://so-torrent.com/sphinx.php?q=%s&%s',
                     'login': 'https://so-torrent.com/connect.php',
                     'download': 'https://so-torrent.com/get.php?id=',
        }

        self.url = self.urls['base_url']

        # SPORT / ANIME / OTHER / PACK
        self.subcat = ["c77=1", "c10=1&c88=1", "c94=1&c74=1&c75=1&c72=1&c73=1", "c71=1&c85=1"]

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'sotorrent.png'

    def getQuality(self, item, anime=False):
        quality = Quality.sceneQuality(item[0], anime)
        return quality

    def _doLogin(self):

        login_params = {
                    'username': self.username,
                    'password': self.password,
                    'submit': ' Se Connecter ',
        }

        self.session = requests.Session()

        try:
            response = self.session.post(self.urls['login'], data=login_params, headers=self.headers, timeout=30, verify=False)
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError), e:
            logger.log(u'Unable to connect to ' + self.name + ' provider: ' + ex(e), logger.ERROR)
            return False

        if re.search('Login Incorrect', response.text) \
                or response.status_code == 401:
            logger.log(u'Invalid username or password for ' + self.name + ' Check your settings', logger.ERROR)
            return False

        return True

    def _get_season_search_strings(self, ep_obj):

        search_string = {'Season': []}
        for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
            if ep_obj.show.air_by_date or ep_obj.show.sports:
                ep_string = show_name + '.' + str(ep_obj.airdate).split('-')[0]
            elif ep_obj.show.anime:
                ep_string = show_name + '.' + "%d" % ep_obj.scene_absolute_number
            else:
                ep_string = show_name + '.S%02d' % int(ep_obj.scene_season)

            search_string['Season'].append(ep_string)

        return [search_string]

    def _get_episode_search_strings(self, ep_obj, add_string=''):

        search_string = {'Episode': []}

        if not ep_obj:
            return []

        if self.show.air_by_date:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + '.' + str(ep_obj.airdate).replace('-', '|')
                search_string['Episode'].append(ep_string)
        elif self.show.sports:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + '.' + str(ep_obj.airdate).replace('-', '|') + '|' + ep_obj.airdate.strftime('%b')
                search_string['Episode'].append(ep_string)
        elif self.show.anime:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + '.' + "%i" % int(ep_obj.scene_absolute_number)
                search_string['Episode'].append(ep_string)
        else:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = show_name_helpers.sanitizeSceneName(show_name) + '.' + \
                            sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season,
                                                                  'episodenumber': ep_obj.scene_episode} + ' %s' % add_string

                search_string['Episode'].append(re.sub('\s+', '.', ep_string))

        return [search_string]

    def get_episode_params_url(self, type_show):
        """
            return the params needed for search 
        """
        if(type_show == "Season"):
            return self.subcat[3]
        elif(self.show.sports):
            return self.subcat[0]
        elif(self.show.anime):
            return self.subcat[1]
        else:
            return self.subcat[2]


    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        logger.log(u"_doSearch started with ... {0}".format(str(search_params)), logger.DEBUG)

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for type_show in search_params.keys():

            i_params = self.get_episode_params_url(type_show)

            for search_string in search_params[type_show]:

                search_url = self.urls['search'] % (search_string, i_params)

                data = self.getURL(search_url)
                try:
                    with BS4Parser(data, features=["html5lib", "permissive"]) as html:
                        torrent_table = html.find("table", {"id" : "torrent_list"})
                        if torrent_table:
                            logger.log(u"So-torrent found shows ! " , logger.DEBUG)  
                            torrent_rows = torrent_table.findAll("tr", {"id" : "infos_sphinx"})

                            for row in torrent_rows:
                                release = row.strong.string
                                id_search = row.find("img", {"alt" : "+"})
                                id_torrent = id_search['id'].replace('expandoGif', '')
                                download_url = "{0}{1}".format(self.urls['download'], id_torrent)

                                item = release, download_url
                                logger.log(u"Found result: {0} ({1})".format(release.replace(' ','.'), search_url), logger.DEBUG)

                                items[type_show].append(item)
                except Exception, e:
                    logger.log(u"Failed parsing {0} Traceback: {1}".format(self.name, traceback.format_exc()), logger.ERROR)
                    continue
                results += items[type_show]
        return results

    def _get_title_and_url(self, item):

        title, url = item
        if title:
            title += u''
            title = title.replace(' ', '.')
            title = self._clean_title_from_provider(title)

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


provider = SOTORRENTProvider()
