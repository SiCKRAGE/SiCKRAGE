# Author: Idan Gutman
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
import traceback
import datetime
import time
import urlparse
import sickbeard
import generic
from sickbeard.common import Quality, cpu_presets
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import db
from sickbeard import classes
from sickbeard import helpers
from sickbeard import show_name_helpers
from sickbeard.exceptions import ex, AuthException
from sickbeard import clients
import requests
from requests import exceptions
from sickbeard.bs4_parser import BS4Parser
from unidecode import unidecode
from sickbeard.helpers import sanitizeSceneName


class FreshOnTVProvider(generic.TorrentProvider):

    def __init__(self):

        generic.TorrentProvider.__init__(self, "FreshOnTV")

        self.supportsBacklog = True

        self.enabled = False
        self._uid = None
        self._hash = None
        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None
        self.freeleech = False

        self.cache = FreshOnTVCache(self)

        self.urls = {'base_url': 'https://freshon.tv/',
                'login': 'https://freshon.tv/login.php?action=makelogin',
                'detail': 'https://freshon.tv/details.php?id=%s',
                'search': 'https://freshon.tv/browse.php?incldead=%s&words=0&cat=0&search=%s',
                'download': 'https://freshon.tv/download.php?id=%s&type=torrent',
                }

        self.url = self.urls['base_url']

        self.cookies = None

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'freshontv.png'

    def getQuality(self, item, anime=False):

        quality = Quality.sceneQuality(item[0], anime)
        return quality

    def _checkAuth(self):

        if not self.username or not self.password:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def _doLogin(self):
        if any(requests.utils.dict_from_cookiejar(self.session.cookies).values()):
            return True

        if self._uid and self._hash:
            requests.utils.add_dict_to_cookiejar(self.session.cookies, self.cookies)
        else:
            login_params = {'username': self.username,
                            'password': self.password,
                            'login': 'submit'
            }

            if not self.session:
                self.session = requests.Session()

            try:
                response = self.session.post(self.urls['login'], data=login_params, timeout=30)
            except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
                logger.log(u'Unable to connect to ' + self.name + ' provider: ' + ex(e), logger.ERROR)
                return False

            if re.search('/logout.php', response.text):
                logger.log(u'Login to ' + self.name + ' was successful.', logger.DEBUG)

                try:
                    if requests.utils.dict_from_cookiejar(self.session.cookies)['uid'] and requests.utils.dict_from_cookiejar(self.session.cookies)['pass']:
                        self._uid = requests.utils.dict_from_cookiejar(self.session.cookies)['uid']
                        self._hash = requests.utils.dict_from_cookiejar(self.session.cookies)['pass']

                        self.cookies = {'uid': self._uid,
                                        'pass': self._hash
                        }
                        return True
                except:
                    logger.log(u'Unable to obtain cookie for FreshOnTV', logger.WARNING)
                    return False

            else:
                logger.log(u'Login to ' + self.name + ' was unsuccessful.', logger.DEBUG)
                if re.search('Username does not exist in the userbase or the account is not confirmed yet.', response.text):
                    logger.log(u'Invalid username or password for ' + self.name + ' Check your settings', logger.ERROR)

                if re.search('DDoS protection by CloudFlare', response.text):
                    logger.log(u'Unable to login to ' + self.name + ' due to CloudFlare DDoS javascript check.', logger.ERROR)

                    return False


    def _get_season_search_strings(self, ep_obj):

        search_string = {'Season': []}
        for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
            if ep_obj.show.air_by_date or ep_obj.show.sports:
                ep_string = show_name + '.' + str(ep_obj.airdate).split('-')[0]
            elif ep_obj.show.anime:
                ep_string = show_name + '.' + "%d" % ep_obj.scene_absolute_number
            else:
                ep_string = show_name + '.S%02d' % int(ep_obj.scene_season)  #1) showName SXX

            search_string['Season'].append(ep_string)

        return [search_string]

    def _get_episode_search_strings(self, ep_obj, add_string=''):

        search_string = {'Episode': []}

        if not ep_obj:
            return []

        if self.show.air_by_date:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            str(ep_obj.airdate).replace('-', '|')
                search_string['Episode'].append(ep_string)
        elif self.show.sports:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            str(ep_obj.airdate).replace('-', '|') + '|' + \
                            ep_obj.airdate.strftime('%b')
                search_string['Episode'].append(ep_string)
        elif self.show.anime:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            "%i" % int(ep_obj.scene_absolute_number)
                search_string['Episode'].append(ep_string)
        else:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = show_name_helpers.sanitizeSceneName(show_name) + ' ' + \
                            sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season,
                                                                  'episodenumber': ep_obj.scene_episode} + ' %s' % add_string

                search_string['Episode'].append(re.sub('\s+', ' ', ep_string))

        return [search_string]

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        freeleech = '3' if self.freeleech else '0'

        if not self._doLogin():
            return results

        for mode in search_params.keys():
            for search_string in search_params[mode]:

                if isinstance(search_string, unicode):
                    search_string = unidecode(search_string)

                searchURL = self.urls['search'] % (freeleech, search_string)
                logger.log(u"Search string: " + searchURL, logger.DEBUG)
                init_html = self.getURL(searchURL)
                max_page_number = 0

                if not init_html:
                    logger.log(u"The opening search response from " + self.name + " is empty.",logger.DEBUG)
                    continue

                try:
                    with BS4Parser(init_html, features=["html5lib", "permissive"]) as init_soup:

                        #Check to see if there is more than 1 page of results
                        pager = init_soup.find('div', {'class': 'pager'})
                        if pager:
                            page_links = pager.find_all('a', href=True)
                        else:
                            page_links = []

                        if len(page_links) > 0:
                            for lnk in page_links:
                                link_text = lnk.text.strip()
                                if link_text.isdigit():
                                    page_int = int(link_text)
                                    if page_int > max_page_number:
                                        max_page_number = page_int

                        #limit page number to 15 just in case something goes wrong
                        if max_page_number > 15:
                            max_page_number = 15
                        #limit RSS search
                        if max_page_number > 3 and mode is 'RSS':
                            max_page_number = 3
                except:
                    logger.log(u"BS4 parser unable to process response " + self.name + " Traceback: " + traceback.format_exc(), logger.ERROR)
                    continue

                data_response_list = []
                data_response_list.append(init_html)

                #Freshon starts counting pages from zero, even though it displays numbers from 1
                if max_page_number > 1:
                    for i in range(1, max_page_number):

                        time.sleep(1)
                        page_searchURL = searchURL + '&page=' + str(i)
                        logger.log(u"Search string: " + page_searchURL, logger.DEBUG)
                        page_html = self.getURL(page_searchURL)

                        if not page_html:
                            logger.log(u"The search response for page number " + str(i) + " is empty." + self.name,logger.DEBUG)
                            continue

                        data_response_list.append(page_html)

                try:

                    for data_response in data_response_list:

                        with BS4Parser(data_response, features=["html5lib", "permissive"]) as html:

                            torrent_rows = html.findAll("tr", {"class": re.compile('torrent_[0-9]*')})

                            #Continue only if a Release is found
                            if len(torrent_rows) == 0:
                                logger.log(u"The Data returned from " + self.name + " does not contain any torrent", logger.DEBUG)
                                continue

                            for individual_torrent in torrent_rows:

                                #skip if torrent has been nuked due to poor quality
                                if individual_torrent.find('img', alt='Nuked') != None:
                                    continue

                                try:
                                    title = individual_torrent.find('a', {'class': 'torrent_name_link'})['title']
                                except:
                                    logger.log(u"Unable to parse torrent title " + self.name + " Traceback: " + traceback.format_exc(), logger.DEBUG)
                                    continue

                                try:
                                    details_url = individual_torrent.find('a', {'class': 'torrent_name_link'})['href']
                                    id = int((re.match('.*?([0-9]+)$', details_url).group(1)).strip())
                                    download_url = self.urls['download'] % (str(id))
                                except:
                                    logger.log(u"Unable to parse torrent id & download url  " + self.name + " Traceback: " + traceback.format_exc(), logger.DEBUG)
                                    continue

                                try:
                                    seeders = int(individual_torrent.find('td', {'class': 'table_seeders'}).find('span').text.strip())
                                except:
                                    logger.log(u"Unable to parse torrent seeders content  " + self.name + " Traceback: " + traceback.format_exc(), logger.DEBUG)
                                    seeders = 1
                                try:
                                    leechers = int(individual_torrent.find('td', {'class': 'table_leechers'}).find('a').text.strip())
                                except:
                                    logger.log(u"Unable to parse torrent leechers content " + self.name + " Traceback: " + traceback.format_exc(), logger.DEBUG)
                                    leechers = 0

                                #Filter unseeded torrent
                                if mode != 'RSS' and (seeders < self.minseed or leechers < self.minleech):
                                    continue

                                if not title or not download_url:
                                    continue

                                item = title, download_url, id, seeders, leechers
                                logger.log(u"Found result: " + title + " (" + searchURL + ")", logger.DEBUG)

                                items[mode].append(item)

                except Exception as e:
                    logger.log(u"Failed parsing " + " Traceback: " + traceback.format_exc(), logger.DEBUG)

            #For each search mode sort all the items by seeders
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def _get_title_and_url(self, item):

        title, url, id, seeders, leechers = item

        if title:
            title = self._clean_title_from_provider(title)

        if url:
            url = str(url).replace('&amp;', '&')

        return (title, url)

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


class FreshOnTVCache(tvcache.TVCache):
    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # poll delay in minutes
        self.minTime = 20

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}

provider = FreshOnTVProvider()
