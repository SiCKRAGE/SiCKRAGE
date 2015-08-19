# Author: Giovanni Borri
# Modified by gborri, https://github.com/gborri for TNTVillage
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
import sickbeard
import generic
from sickbeard.common import Quality
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import db
from sickbeard import classes
from sickbeard import helpers
from sickbeard import show_name_helpers
from sickbeard.exceptions import ex, AuthException
from sickbeard import clients
import requests
from requests.exceptions import RequestException
from sickbeard.bs4_parser import BS4Parser
from unidecode import unidecode
from sickbeard.helpers import sanitizeSceneName
from sickbeard.name_parser.parser import NameParser, InvalidNameException, InvalidShowException

category_excluded = {
              'Sport' : 22,
              'Teatro' : 23,
              'Video Musicali' : 21,
              'Film' : 4,
              'Musica' : 2,
              'Students Releases' : 13,
              'E Books' : 3,
              'Linux' : 6,
              'Macintosh' : 9,
              'Windows Software' : 10,
              'Pc Game' : 11,
              'Playstation 2' : 12,
              'Wrestling' : 24,
              'Varie' : 25,
              'Xbox' : 26,
              'Immagini sfondi' : 27,
              'Altri Giochi' : 28,
              'Fumetteria' : 30,
              'Trash' : 31,
              'PlayStation 1' : 32,
              'PSP Portable' : 33,
              'A Book' : 34,
              'Podcast' : 35,
              'Edicola' : 36,
              'Mobile' : 37,
             }

class TNTVillageProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "TNTVillage")

        self.supportsBacklog = True

        self.enabled = False
        self._uid = None
        self._hash = None
        self.username = None
        self.password = None
        self.ratio = None
        self.cat = None
        self.page = 10
        self.subtitle = None
        self.minseed = None
        self.minleech = None

        self.hdtext = [
                       ' - Versione 720p',
                       ' Versione 720p',
                       ' V 720p',
                       ' V 720',
                       ' V HEVC',
                       ' V  HEVC',
                       ' V 1080',
                       ' Versione 1080p',
                       ' 720p HEVC',
                       ' Ver 720',
                       ' 720p HEVC',
                       ' 720p',
                      ]

        self.category_dict = {
                              'Serie TV' : 29,
                              'Cartoni' : 8,
                              'Anime' : 7,
                              'Programmi e Film TV' : 1,
                              'Documentari' : 14,
                              'All' : 0, 
                             }

        self.urls = {'base_url' : 'http://forum.tntvillage.scambioetico.org',
            'login' : 'http://forum.tntvillage.scambioetico.org/index.php?act=Login&CODE=01',
            'detail' : 'http://forum.tntvillage.scambioetico.org/index.php?showtopic=%s',
            'search' : 'http://forum.tntvillage.scambioetico.org/?act=allreleases&%s',
            'search_page' : 'http://forum.tntvillage.scambioetico.org/?act=allreleases&st={0}&{1}',
            'download' : 'http://forum.tntvillage.scambioetico.org/index.php?act=Attach&type=post&id=%s',
        }

        self.sub_string = ['sub', 'softsub']

        self.url = self.urls['base_url']

        self.cache = TNTVillageCache(self)

        self.categories = "cat=29"

        self.cookies = None

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'tntvillage.png'

    def getQuality(self, item, anime=False):

        quality = Quality.sceneQuality(item[0], anime)
        return quality

    def _checkAuth(self):

        if not self.username or not self.password:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def _doLogin(self):

        login_params = {'UserName': self.username,
                        'PassWord': self.password,
                        'CookieDate': 0,
                        'submit': 'Connettiti al Forum',
        }

        try:
            response = self.session.post(self.urls['login'], data=login_params, timeout=30)
        except RequestException as e:
            logger.log(u'Unable to connect to ' + self.name + ' provider: ' + ex(e), logger.ERROR)
            return False

        if re.search('Sono stati riscontrati i seguenti errori', response.text) \
        or re.search('<title>Connettiti</title>', response.text) \
        or response.status_code == 401:
            logger.log(u'Invalid username or password for ' + self.name + ' Check your settings', logger.ERROR)
            return False

        return True

    def _get_season_search_strings(self, ep_obj):

        search_string = {'Season': []}
        for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
            if ep_obj.show.air_by_date or ep_obj.show.sports:
                ep_string = show_name + ' ' + str(ep_obj.airdate).split('-')[0]
            elif ep_obj.show.anime:
                ep_string = show_name + ' ' + "%d" % ep_obj.scene_absolute_number
            else:
                ep_string = show_name + ' S%02d' % int(ep_obj.scene_season)  #1) showName SXX
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

    def _reverseQuality(self, quality):

        quality_string = ''

        if quality == Quality.SDTV:
            quality_string = ' HDTV x264'
        if quality == Quality.SDDVD:
            quality_string = ' DVDRIP'
        elif quality == Quality.HDTV:
            quality_string = ' 720p HDTV x264'
        elif quality == Quality.FULLHDTV:
            quality_string = ' 1080p HDTV x264'
        elif quality == Quality.RAWHDTV:
            quality_string = ' 1080i HDTV mpeg2'
        elif quality == Quality.HDWEBDL:
            quality_string = ' 720p WEB-DL h264'
        elif quality == Quality.FULLHDWEBDL:
            quality_string = ' 1080p WEB-DL h264'
        elif quality == Quality.HDBLURAY:
            quality_string = ' 720p Bluray x264'
        elif quality == Quality.FULLHDBLURAY:
            quality_string = ' 1080p Bluray x264'

        return quality_string

    def _episodeQuality(self,torrent_rows):
        """
            Return The quality from the scene episode HTML row.
        """
        file_quality=''

        img_all = (torrent_rows.find_all('td'))[1].find_all('img')
        
        if len(img_all) > 0:
            for img_type in img_all:
                try:
                    file_quality = file_quality + " " + img_type['src'].replace("style_images/mkportal-636/","").replace(".gif","").replace(".png","")
                except Exception:
                    logger.log(u"Failed parsing " + self.name + " Traceback: "  + traceback.format_exc(), logger.ERROR)

        else:
            file_quality = (torrent_rows.find_all('td'))[1].get_text()
            logger.log(u"Episode quality: " + str(file_quality), logger.DEBUG)

        checkName = lambda list, func: func([re.search(x, file_quality, re.I) for x in list])

        dvdOptions = checkName(["dvd", "dvdrip", "dvdmux", "DVD9", "DVD5"], any)
        bluRayOptions = checkName(["BD","BDmux", "BDrip", "BRrip", "Bluray"], any)
        sdOptions = checkName(["h264", "divx", "XviD", "tv", "TVrip", "SATRip", "DTTrip", "Mpeg2"], any)
        hdOptions = checkName(["720p"], any)
        fullHD = checkName(["1080p", "fullHD"], any)

        if len(img_all) > 0:
            file_quality = (torrent_rows.find_all('td'))[1].get_text()

        webdl = checkName(["webdl", "webmux", "webrip", "dl-webmux", "web-dlmux", "webdl-mux", "web-dl", "webdlmux", "dlmux"], any)

        logger.log(u"Episode options: dvdOptions: " + str(dvdOptions) + ", bluRayOptions: " + str(bluRayOptions) + \
                   ", sdOptions: " + str(sdOptions) + ", hdOptions: " + str(hdOptions) + ", fullHD: " + str(fullHD) + ", webdl: " + str(webdl), logger.DEBUG)

        if sdOptions and not dvdOptions and not fullHD and not hdOptions:
            return Quality.SDTV
        elif dvdOptions:
            return Quality.SDDVD
        elif hdOptions and not bluRayOptions and not fullHD and not webdl:
            return Quality.HDTV
        elif not hdOptions and not bluRayOptions and fullHD and not webdl:
            return Quality.FULLHDTV
        elif hdOptions and not bluRayOptions and not fullHD and webdl:
            return Quality.HDWEBDL
        elif not hdOptions and not bluRayOptions and fullHD and webdl:
            return Quality.FULLHDWEBDL
        elif bluRayOptions and hdOptions and not fullHD:
            return Quality.HDBLURAY
        elif bluRayOptions and fullHD and not hdOptions:
            return Quality.FULLHDBLURAY
        else:
            return Quality.UNKNOWN

    def _is_italian(self, torrent_rows):

        name = str(torrent_rows.find_all('td')[1].find('b').find('span'))
        if not name or name is 'None':
            return False

        subFound = italian = False
        for sub in self.sub_string:
            if re.search(sub, name, re.I):
                subFound = True
            else:
                continue

            if re.search("ita", name.split(sub)[0], re.I):
                logger.log(u"Found Italian release", logger.DEBUG)
                italian = True
                break

        if not subFound and re.search("ita", name, re.I):
            logger.log(u"Found Italian release", logger.DEBUG)
            italian = True
        
        return italian

    def _is_season_pack(self, name):

        try:
            myParser = NameParser(tryIndexers=True, trySceneExceptions=True)
            parse_result = myParser.parse(name)
        except InvalidNameException:
            logger.log(u"Unable to parse the filename " + str(name) + " into a valid episode", logger.DEBUG)
            return False
        except InvalidShowException:
            logger.log(u"Unable to parse the filename " + str(name) + " into a valid show", logger.DEBUG)
            return False

        myDB = db.DBConnection()
        sql_selection="select count(*) as count from tv_episodes where showid = ? and season = ?"
        episodes = myDB.select(sql_selection, [parse_result.show.indexerid, parse_result.season_number])
        if int(episodes[0]['count']) == len(parse_result.episode_numbers):
            return True

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        self.categories = "cat=" + str(self.cat)

        if not self._doLogin():
            return results

        for mode in search_params.keys():
            for search_string in search_params[mode]:

                if isinstance(search_string, unicode):
                    search_string = unidecode(search_string)

                if mode == 'RSS':
                    self.page = 2

                last_page=0
                y=int(self.page)

                if search_string == '':
                    continue

                search_string = str(search_string).replace('.', ' ')

                for x in range(0,y):
                    z=x*20
                    if last_page:
                        break	

                    if mode != 'RSS':
                        searchURL = (self.urls['search_page'] + '&filter={2}').format(z,self.categories,search_string)
                    else:
                        searchURL = self.urls['search_page'].format(z,self.categories)

                    logger.log(u"Search string: " + searchURL, logger.DEBUG)

                    data = self.getURL(searchURL)
                    if not data:
                        logger.log(u"Received no data from the server", logger.DEBUG)
                        continue

                    try:
                        with BS4Parser(data, features=["html5lib", "permissive"]) as html:
                            torrent_table = html.find('table', attrs = {'class' : 'copyright'})
                            torrent_rows = torrent_table.find_all('tr') if torrent_table else []

                            #Continue only if one Release is found
                            if len(torrent_rows)<3:
                                logger.log(u"The server returned no torrents", logger.DEBUG)
                                last_page=1
                                continue

                            logger.log(u"Parsing results from page " + str(x+1), logger.DEBUG)

                            if len(torrent_rows) < 42:
                                last_page=1

                            for result in torrent_table.find_all('tr')[2:]:

                                try:
                                    link = result.find('td').find('a')
                                    title = link.string
                                    id = ((result.find_all('td')[8].find('a'))['href'])[-8:]
                                    download_url = self.urls['download'] % (id)
                                    leechers = result.find_all('td')[3].find_all('td')[1].text
                                    leechers = int(leechers.strip('[]'))
                                    seeders = result.find_all('td')[3].find_all('td')[2].text
                                    seeders = int(seeders.strip('[]'))
                                except (AttributeError, TypeError):
                                    continue

                                if mode != 'RSS' and (seeders < self.minseed or leechers < self.minleech):
                                    continue

                                if not title or not download_url:
                                    continue

                                filename_qt = self._reverseQuality(self._episodeQuality(result))
                                for text in self.hdtext:
                                    title1 = title
                                    title = title.replace(text,filename_qt)
                                    if title != title1:
                                        break

                                if Quality.nameQuality(title) == Quality.UNKNOWN:
                                    title += filename_qt 

                                if not self._is_italian(result) and not self.subtitle:
                                    logger.log(u"Subtitled, skipping "  + title + "(" + searchURL + ")", logger.DEBUG)
                                    continue

                                if self._is_season_pack(title):
                                    title = re.sub(r'([Ee][\d{1,2}\-?]+)', '', title)

                                item = title, download_url, id, seeders, leechers
                                logger.log(u"Found result: " + title + "(" + searchURL + ")", logger.DEBUG)

                                items[mode].append(item)

                    except Exception:
                        logger.log(u"Failed parsing " + self.name + " Traceback: " + traceback.format_exc(), logger.ERROR)

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
            self.show = curshow = helpers.findCertainShow(sickbeard.showList, int(sqlshow["showid"]))
            if not self.show: continue
            curEp = curshow.getEpisode(int(sqlshow["season"]), int(sqlshow["episode"]))

            searchString = self._get_episode_search_strings(curEp, add_string='PROPER|REPACK')

            for item in self._doSearch(searchString[0]):
                title, url = self._get_title_and_url(item)
                results.append(classes.Proper(title, url, datetime.datetime.today(), self.show))

        return results

    def seedRatio(self):
        return self.ratio


class TNTVillageCache(tvcache.TVCache):
    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # only poll TNTVillage every 30 minutes max
        self.minTime = 30

    def _getRSSData(self):
        search_params = {'RSS': []}
        return {'entries': self.provider._doSearch(search_params)}


provider = TNTVillageProvider()
