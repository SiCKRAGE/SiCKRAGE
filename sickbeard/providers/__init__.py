# Author: Nic Wolfe <nic@wolfeden.ca>
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

import datetime
import itertools
import logging
import os
import random
import re
from base64 import b16encode, b32decode

from hachoir_core.stream import StringInputStream
from hachoir_parser import guessParser

import classes
import db
import helpers
import tvcache
from common import Quality, MULTI_EP_RESULT, SEASON_RESULT
from helper.encoding import ek
from helper.exceptions import ex
from name_parser.parser import NameParser, InvalidNameException, InvalidShowException


def sortedProviderList(randomize=False):
    initialList = providerList + newznabProviderList + torrentRssProviderList
    providerDict = dict(zip([x.getID() for x in initialList], initialList))

    newList = []

    # add all modules in the priority list, in order
    for curModule in PROVIDER_ORDER:
        if curModule in providerDict:
            newList.append(providerDict[curModule])

    # add all enabled providers first
    for curModule in providerDict:
        if providerDict[curModule] not in newList and providerDict[curModule].isEnabled():
            newList.append(providerDict[curModule])

    # add any modules that are missing from that list
    for curModule in providerDict:
        if providerDict[curModule] not in newList:
            newList.append(providerDict[curModule])

    if randomize:
        random.shuffle(newList)

    return newList

def makeProviderList():
    return [x.provider for x in
            [getProviderModule(y) for y in next(os.walk(os.path.dirname(__file__)))[2] if y.endswith('.py')] if x]

def getProviderModule(name):
    path = os.path.dirname(__file__)
    module = __import__(os.path.join(path, name))
    if issubclass(module, GenericProvider):
        return module

def getProviderClass(provider_id):
    providerMatch = [x for x in
                     providerList + newznabProviderList + torrentRssProviderList if
                     x.getID() == provider_id]

    if len(providerMatch) != 1:
        return None
    else:
        return providerMatch[0]


class GenericProvider(object):
    NZB = "nzb"
    TORRENT = "torrent"

    def __init__(self, name):
        # these need to be set in the subclass
        self.providerType = None
        self.name = name

        self.urls = {}
        self.url = ''

        self.public = False

        self.show = None

        self.supportsBacklog = False
        self.supportsAbsoluteNumbering = False
        self.anime_only = False

        self.search_mode = None
        self.search_fallback = False

        self.enabled = False
        self.enable_daily = False
        self.enable_backlog = False

        self.cache = tvcache.TVCache(self)

        self.headers = {}

        self.session = helpers._setUpSession()
        self.session.headers.update(self.headers)

        self.btCacheURLS = [
            'http://torcache.net/torrent/{torrent_hash}.torrent',
            'http://thetorrent.org/torrent/{torrent_hash}.torrent',
            'http://btdig.com/torrent/{torrent_hash}.torrent',
            # 'http://torrage.com/torrent/{torrent_hash}.torrent',
            # 'http://itorrents.org/torrent/{torrent_hash}.torrent',
        ]

        self.proper_strings = ['PROPER|REPACK|REAL']

    def getID(self):
        return GenericProvider.makeID(self.name)

    @staticmethod
    def makeID(name):
        return re.sub(r"[^\w\d_]", "_", name.strip().lower())

    def imageName(self):
        return self.getID() + '.png'

    # pylint: disable=R0201,W0612
    # Method could be a function, Unused variable
    def _checkAuth(self):
        return True

    def _doLogin(self):
        return True

    def isActive(self):
        return False

    def isEnabled(self):
        return self.enabled

    def getResult(self, episodes):
        """
        Returns a result of the correct type for this provider
        """

        if self.providerType == GenericProvider.NZB:
            result = classes.NZBSearchResult(episodes)
        elif self.providerType == GenericProvider.TORRENT:
            result = classes.TorrentSearchResult(episodes)
        else:
            result = classes.SearchResult(episodes)

        result.provider = self

        return result

    def getURL(self, url, post_data=None, params=None, timeout=30, json=False, needBytes=False):
        """
        By default this is just a simple urlopen call but this method should be overridden
        for providers with special URL requirements (like cookies)
        """

        return helpers.getURL(url, post_data=post_data, params=params, headers=self.headers, timeout=timeout,
                              session=self.session, json=json, needBytes=needBytes)

    def _makeURL(self, result):
        urls = []
        filename = ''
        if result.url.startswith('magnet'):
            try:
                torrent_hash = re.findall(r'urn:btih:([\w]{32,40})', result.url)[0].upper()

                try:
                    torrent_name = re.findall('dn=([^&]+)', result.url)[0]
                except Exception:
                    torrent_name = 'NO_DOWNLOAD_NAME'

                if len(torrent_hash) == 32:
                    torrent_hash = b16encode(b32decode(torrent_hash)).upper()

                if not torrent_hash:
                    logging.error("Unable to extract torrent hash from magnet: " + ex(result.url))
                    return urls, filename

                urls = random.shuffle(
                        [x.format(torrent_hash=torrent_hash, torrent_name=torrent_name) for x in self.btCacheURLS])
            except Exception:
                logging.error("Unable to extract torrent hash or name from magnet: " + ex(result.url))
                return urls, filename
        else:
            urls = [result.url]

        if self.providerType == GenericProvider.TORRENT:
            filename = ek(os.path.join, TORRENT_DIR,
                          helpers.sanitizeFileName(result.name) + '.' + self.providerType)

        elif self.providerType == GenericProvider.NZB:
            filename = ek(os.path.join, NZB_DIR,
                          helpers.sanitizeFileName(result.name) + '.' + self.providerType)

        return urls, filename

    def downloadResult(self, result):
        """
        Save the result to disk.
        """

        # check for auth
        if not self._doLogin():
            return False

        urls, filename = self._makeURL(result)

        for url in urls:
            if 'NO_DOWNLOAD_NAME' in url:
                continue

            if url.startswith('http'):
                self.headers.update({'Referer': '/'.join(url.split('/')[:3]) + '/'})

            logging.info("Downloading a result from " + self.name + " at " + url)

            # Support for Jackett/TorzNab
            if url.endswith(GenericProvider.TORRENT) and filename.endswith(GenericProvider.NZB):
                filename = filename.rsplit('.', 1)[0] + '.' + GenericProvider.TORRENT

            if helpers.download_file(url, filename, session=self.session, headers=self.headers):
                if self._verify_download(filename):
                    logging.info("Saved result to " + filename)
                    return True
                else:
                    logging.warning("Could not download %s" % url)
                    helpers.remove_file_failed(filename)

        if len(urls):
            logging.warning("Failed to download any results")

        return False

    def _verify_download(self, file_name=None):
        """
        Checks the saved file to see if it was actually valid, if not then consider the download a failure.
        """

        # primitive verification of torrents, just make sure we didn't get a text file or something
        if file_name.endswith(GenericProvider.TORRENT):
            try:
                for byte in helpers.readFileBuffered(file_name):
                    mime_type = guessParser(StringInputStream(byte))._getMimeType()
                    if mime_type == 'application/x-bittorrent':
                        return True
            except Exception as e:
                logging.debug("Failed to validate torrent file: {}".format(ex(e)))

            logging.debug("Result is not a valid torrent file")
            return False

        return True

    def searchRSS(self, episodes):
        return self.cache.findNeededEpisodes(episodes)

    def getQuality(self, item, anime=False):
        """
        Figures out the quality of the given RSS item node

        item: An elementtree.ElementTree element representing the <item> tag of the RSS feed

        Returns a Quality value obtained from the node's data
        """
        (title, url) = self._get_title_and_url(item)
        quality = Quality.sceneQuality(title, anime)
        return quality

    # pylint: disable=R0201,W0613
    # Method could be a function, Unused argument
    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):
        return []

    def _get_season_search_strings(self, episode):
        return [{}]

    def _get_episode_search_strings(self, eb_obj, add_string=''):
        return [{}]

    def _get_title_and_url(self, item):
        """
        Retrieves the title and URL data from the item XML node

        item: An elementtree.ElementTree element representing the <item> tag of the RSS feed

        Returns: A tuple containing two strings representing title and URL respectively
        """

        title = item.get('title', '')
        if title:
            title = '' + title.replace(' ', '.')

        url = item.get('link', '')
        if url:
            url = url.replace('&amp;', '&').replace('%26tr%3D', '&tr=')

        return title, url

    def _get_size(self, item):
        """Gets the size from the item"""
        logging.error("Provider type doesn't have _get_size() implemented yet")
        return -1

    def findSearchResults(self, show, episodes, search_mode, manualSearch=False, downCurQuality=False):

        self._checkAuth()
        self.show = show

        results = {}
        itemList = []

        searched_scene_season = None
        for epObj in episodes:
            # search cache for episode result
            cacheResult = self.cache.searchCache(epObj, manualSearch, downCurQuality)
            if cacheResult:
                if epObj.episode not in results:
                    results[epObj.episode] = cacheResult
                else:
                    results[epObj.episode].extend(cacheResult)

                # found result, search next episode
                continue

            # skip if season already searched
            if len(episodes) > 1 and search_mode == 'sponly' and searched_scene_season == epObj.scene_season:
                continue

            # mark season searched for season pack searches so we can skip later on
            searched_scene_season = epObj.scene_season

            search_strings = []
            if len(episodes) > 1 and search_mode == 'sponly':
                # get season search results
                search_strings = self._get_season_search_strings(epObj)
            elif search_mode == 'eponly':
                # get single episode search results
                search_strings = self._get_episode_search_strings(epObj)

            first = search_strings and isinstance(search_strings[0], dict) and 'rid' in search_strings[0]
            if first:
                logging.debug('First search_string has rid')

            for curString in search_strings:
                itemList += self._doSearch(curString, search_mode, len(episodes), epObj=epObj)
                if first:
                    first = False
                    if itemList:
                        logging.debug('First search_string had rid, and returned results, skipping query by string')
                        break
                    else:
                        logging.debug(
                            'First search_string had rid, but returned no results, searching with string query')

        # if we found what we needed already from cache then return results and exit
        if len(results) == len(episodes):
            return results

        # sort list by quality
        if len(itemList):
            items = {}
            itemsUnknown = []
            for item in itemList:
                quality = self.getQuality(item, anime=show.is_anime)
                if quality == Quality.UNKNOWN:
                    itemsUnknown += [item]
                else:
                    if quality not in items:
                        items[quality] = [item]
                    else:
                        items[quality].append(item)

            itemList = list(itertools.chain(*[v for (k, v) in sorted(items.iteritems(), reverse=True)]))
            itemList += itemsUnknown if itemsUnknown else []

        # filter results
        cl = []
        for item in itemList:
            (title, url) = self._get_title_and_url(item)

            # parse the file name
            try:
                myParser = NameParser(False)
                parse_result = myParser.parse(title)
            except InvalidNameException:
                logging.debug("Unable to parse the filename " + title + " into a valid episode")
                continue
            except InvalidShowException:
                logging.debug("Unable to parse the filename " + title + " into a valid show")
                continue

            showObj = parse_result.show
            quality = parse_result.quality
            release_group = parse_result.release_group
            version = parse_result.version

            addCacheEntry = False
            if not (showObj.air_by_date or showObj.sports):
                if search_mode == 'sponly':
                    if len(parse_result.episode_numbers):
                        logging.debug(
                                "This is supposed to be a season pack search but the result " + title + " is not a valid season pack, skipping it")
                        addCacheEntry = True
                    if len(parse_result.episode_numbers) and (
                                    parse_result.season_number not in set([ep.season for ep in episodes])
                            or not [ep for ep in episodes if ep.scene_episode in parse_result.episode_numbers]):
                        logging.debug(
                                "The result " + title + " doesn't seem to be a valid episode that we are trying to snatch, ignoring")
                        addCacheEntry = True
                else:
                    if not len(parse_result.episode_numbers) and parse_result.season_number and not [ep for ep in
                                                                                                     episodes if
                                                                                                     ep.season == parse_result.season_number and ep.episode in parse_result.episode_numbers]:
                        logging.debug(
                                "The result " + title + " doesn't seem to be a valid season that we are trying to snatch, ignoring")
                        addCacheEntry = True
                    elif len(parse_result.episode_numbers) and not [ep for ep in episodes if
                                                                    ep.season == parse_result.season_number and ep.episode in parse_result.episode_numbers]:
                        logging.debug(
                                "The result " + title + " doesn't seem to be a valid episode that we are trying to snatch, ignoring")
                        addCacheEntry = True

                if not addCacheEntry:
                    # we just use the existing info for normal searches
                    actual_season = parse_result.season_number
                    actual_episodes = parse_result.episode_numbers
            else:
                if not parse_result.is_air_by_date:
                    logging.debug(
                            "This is supposed to be a date search but the result " + title + " didn't parse as one, skipping it")
                    addCacheEntry = True
                else:
                    airdate = parse_result.air_date.toordinal()
                    myDB = db.DBConnection()
                    sql_results = myDB.select(
                            "SELECT season, episode FROM tv_episodes WHERE showid = ? AND airdate = ?",
                            [showObj.indexerid, airdate])

                    if len(sql_results) != 1:
                        logging.warning(
                                "Tried to look up the date for the episode " + title + " but the database didn't give proper results, skipping it")
                        addCacheEntry = True

                if not addCacheEntry:
                    actual_season = int(sql_results[0][b"season"])
                    actual_episodes = [int(sql_results[0][b"episode"])]

            # add parsed result to cache for usage later on
            if addCacheEntry:
                logging.debug("Adding item from search to cache: " + title)
                # pylint: disable=W0212
                # Access to a protected member of a client class
                ci = self.cache._addCacheEntry(title, url, parse_result=parse_result)
                if ci is not None:
                    cl.append(ci)
                continue

            # make sure we want the episode
            wantEp = True
            for epNo in actual_episodes:
                if not showObj.wantEpisode(actual_season, epNo, quality, manualSearch, downCurQuality):
                    wantEp = False
                    break

            if not wantEp:
                logging.info(
                        "Ignoring result " + title + " because we don't want an episode that is " +
                        Quality.qualityStrings[
                            quality])

                continue

            logging.debug("Found result " + title + " at " + url)

            # make a result object
            epObj = []
            for curEp in actual_episodes:
                epObj.append(showObj.getEpisode(actual_season, curEp))

            result = self.getResult(epObj)
            result.show = showObj
            result.url = url
            result.name = title
            result.quality = quality
            result.release_group = release_group
            result.version = version
            result.content = None
            result.size = self._get_size(item)

            if len(epObj) == 1:
                epNum = epObj[0].episode
                logging.debug("Single episode result.")
            elif len(epObj) > 1:
                epNum = MULTI_EP_RESULT
                logging.debug("Separating multi-episode result to check for later - result contains episodes: " + str(
                        parse_result.episode_numbers))
            elif len(epObj) == 0:
                epNum = SEASON_RESULT
                logging.debug("Separating full season result to check for later")

            if epNum not in results:
                results[epNum] = [result]
            else:
                results[epNum].append(result)

        # check if we have items to add to cache
        if len(cl) > 0:
            # pylint: disable=W0212
            # Access to a protected member of a client class
            myDB = self.cache._getDB()
            myDB.mass_action(cl)

        return results

    def findPropers(self, search_date=None):

        results = self.cache.listPropers(search_date)

        return [classes.Proper(x[b'name'], x[b'url'], datetime.datetime.fromtimestamp(x[b'time']), self.show) for x in
                results]

    def seedRatio(self):
        '''
        Provider should override this value if custom seed ratio enabled
        It should return the value of the provider seed ratio
        '''
        return ''
