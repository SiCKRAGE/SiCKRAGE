# Author: echel0n <sickrage.tv@gmail.com>
# URL: http://github.com/SiCKRAGETV/SickRage/
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
import importlib
import io
import itertools
import os
import random
import re
import urllib
from base64 import b16encode, b32decode

import bencode
import requests
from feedparser import FeedParserDict
from hachoir_core.stream import StringInputStream
from hachoir_parser import guessParser
from tornado import gen

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.classes import NZBSearchResult, Proper, SearchResult, \
    TorrentSearchResult
from sickrage.core.common import MULTI_EP_RESULT, Quality, SEASON_RESULT
from sickrage.core.databases import main_db
from sickrage.core.exceptions import AuthException
from sickrage.core.helpers import _setUpSession, chmodAsParent, download_file, \
    findCertainShow, getURL, readFileBuffered, remove_file_failed, \
    sanitizeFileName, sanitizeSceneName
from sickrage.core.helpers.show_names import allPossibleShowNames
from sickrage.core.nameparser import InvalidNameException, InvalidShowException, \
    NameParser
from sickrage.core.scene_exceptions import get_scene_exceptions


class GenericProvider(object):
    NZB = 'nzb'
    TORRENT = 'torrent'
    types = [NZB, TORRENT]

    type = None

    def __init__(self, name):
        # these need to be set in the subclass
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
        self.cache = TVCache(self)
        self.headers = {}
        self.session = _setUpSession()
        self.session.headers.update(self.headers)
        self.proper_strings = ['PROPER|REPACK|REAL']

        self.btCacheURLS = [
            'http://torcache.net/torrent/{torrent_hash}.torrent',
            'http://thetorrent.org/torrent/{torrent_hash}.torrent',
            'http://btdig.com/torrent/{torrent_hash}.torrent',
            # 'http://torrage.com/torrent/{torrent_hash}.torrent',
            # 'http://itorrents.org/torrent/{torrent_hash}.torrent',
        ]

    @property
    def id(self):
        return self._makeID()

    @property
    def isActive(self):
        return False

    @property
    def isEnabled(self):
        return self.enabled

    @property
    def imageName(self):
        return self.id + '.png'

    def _makeID(self):
        return str(re.sub(r"[^\w\d_]", "_", self.name.strip().lower()))

    def _checkAuth(self):
        return True

    def _doLogin(self):
        return True

    @classmethod
    def get_subclasses(cls):
        yield cls
        if cls.__subclasses__():
            for sub in cls.__subclasses__():
                for s in sub.get_subclasses():
                    yield s

    def getResult(self, episodes):
        """
        Returns a result of the correct type for this provider
        """
        try:
            result = {'nzb': NZBSearchResult, 'torrent': TorrentSearchResult}[self.type](episodes)
        except:
            result = SearchResult(episodes)

        result.provider = self
        return result

    def getURL(self, url, post_data=None, params=None, timeout=30, json=False, needBytes=False):
        """
        By default this is just a simple urlopen call but this method should be overridden
        for providers with special URL requirements (like cookies)
        """

        return getURL(url, post_data=post_data, params=params, headers=self.headers, timeout=timeout,
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
                    sickrage.LOGGER.error("Unable to extract torrent hash from magnet: " + result.url)
                    return urls, filename

                urls = random.shuffle(
                        [x.format(torrent_hash=torrent_hash, torrent_name=torrent_name) for x in self.btCacheURLS])
            except Exception:
                sickrage.LOGGER.error("Unable to extract torrent hash or name from magnet: " + result.url)
                return urls, filename
        else:
            urls = [result.url]

        if self.type == self.TORRENT:
            filename = os.path.join(sickrage.TORRENT_DIR,
                                    sanitizeFileName(result.name) + '.' + self.type)

        elif self.type == self.NZB:
            filename = os.path.join(sickrage.NZB_DIR,
                                    sanitizeFileName(result.name) + '.' + self.type)

        return urls, filename

    def downloadResult(self, result):
        """
        Save the result to disk.
        """

        # check for auth
        if not self._doLogin:
            return False

        urls, filename = self._makeURL(result)

        for url in urls:
            if 'NO_DOWNLOAD_NAME' in url:
                continue

            if url.startswith('http'):
                self.headers.update({'Referer': '/'.join(url.split('/')[:3]) + '/'})

            sickrage.LOGGER.info("Downloading a result from " + self.name + " at " + url)

            # Support for Jackett/TorzNab
            if url.endswith(GenericProvider.TORRENT) and filename.endswith(GenericProvider.NZB):
                filename = filename.rsplit('.', 1)[0] + '.' + GenericProvider.TORRENT

            if download_file(url, filename, session=self.session, headers=self.headers):
                if self._verify_download(filename):
                    sickrage.LOGGER.info("Saved result to " + filename)
                    return True
                else:
                    sickrage.LOGGER.warning("Could not download %s" % url)
                    remove_file_failed(filename)

        if len(urls):
            sickrage.LOGGER.warning("Failed to download any results")

        return False

    def _verify_download(self, file_name=None):
        """
        Checks the saved file to see if it was actually valid, if not then consider the download a failure.
        """

        # primitive verification of torrents, just make sure we didn't get a text file or something
        if file_name.endswith(GenericProvider.TORRENT):
            try:
                for byte in readFileBuffered(file_name):
                    mime_type = guessParser(StringInputStream(byte))._getMimeType()
                    if mime_type == 'application/x-bittorrent':
                        return True
            except Exception as e:
                sickrage.LOGGER.debug("Failed to validate torrent file: {}".format(e))

            sickrage.LOGGER.debug("Result is not a valid torrent file")
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
        sickrage.LOGGER.error("Provider type doesn't have _get_size() implemented yet")
        return -1

    def findSearchResults(self, show, episodes, search_mode, manualSearch=False, downCurQuality=False):

        if not self._checkAuth:
            return

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
                sickrage.LOGGER.debug('First search_string has rid')

            for curString in search_strings:
                itemList += self._doSearch(curString, search_mode, len(episodes), epObj=epObj)
                if first:
                    first = False
                    if itemList:
                        sickrage.LOGGER.debug('First search_string had rid, and returned results, skipping query by string')
                        break
                    else:
                        sickrage.LOGGER.debug(
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
                sickrage.LOGGER.debug("Unable to parse the filename " + title + " into a valid episode")
                continue
            except InvalidShowException:
                sickrage.LOGGER.debug("Unable to parse the filename " + title + " into a valid show")
                continue

            showObj = parse_result.show
            quality = parse_result.quality
            release_group = parse_result.release_group
            version = parse_result.version

            addCacheEntry = False
            if not (showObj.air_by_date or showObj.sports):
                if search_mode == 'sponly':
                    if len(parse_result.episode_numbers):
                        sickrage.LOGGER.debug(
                                "This is supposed to be a season pack search but the result " + title + " is not a valid season pack, skipping it")
                        addCacheEntry = True
                    if len(parse_result.episode_numbers) and (
                                    parse_result.season_number not in set([ep.season for ep in episodes])
                            or not [ep for ep in episodes if ep.scene_episode in parse_result.episode_numbers]):
                        sickrage.LOGGER.debug(
                                "The result " + title + " doesn't seem to be a valid episode that we are trying to snatch, ignoring")
                        addCacheEntry = True
                else:
                    if not len(parse_result.episode_numbers) and parse_result.season_number and not [ep for ep in
                                                                                                     episodes if
                                                                                                     ep.season == parse_result.season_number and ep.episode in parse_result.episode_numbers]:
                        sickrage.LOGGER.debug(
                                "The result " + title + " doesn't seem to be a valid season that we are trying to snatch, ignoring")
                        addCacheEntry = True
                    elif len(parse_result.episode_numbers) and not [ep for ep in episodes if
                                                                    ep.season == parse_result.season_number and ep.episode in parse_result.episode_numbers]:
                        sickrage.LOGGER.debug(
                                "The result " + title + " doesn't seem to be a valid episode that we are trying to snatch, ignoring")
                        addCacheEntry = True

                if not addCacheEntry:
                    # we just use the existing info for normal searches
                    actual_season = parse_result.season_number
                    actual_episodes = parse_result.episode_numbers
            else:
                if not parse_result.is_air_by_date:
                    sickrage.LOGGER.debug(
                            "This is supposed to be a date search but the result " + title + " didn't parse as one, skipping it")
                    addCacheEntry = True
                else:
                    airdate = parse_result.air_date.toordinal()
                    sql_results = main_db.MainDB().select(
                            "SELECT season, episode FROM tv_episodes WHERE showid = ? AND airdate = ?",
                            [showObj.indexerid, airdate])

                    if len(sql_results) != 1:
                        sickrage.LOGGER.warning(
                                "Tried to look up the date for the episode " + title + " but the database didn't give proper results, skipping it")
                        addCacheEntry = True

                if not addCacheEntry:
                    actual_season = int(sql_results[0][b"season"])
                    actual_episodes = [int(sql_results[0][b"episode"])]

            # add parsed result to cache for usage later on
            if addCacheEntry:
                sickrage.LOGGER.debug("Adding item from search to cache: " + title)
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
                sickrage.LOGGER.info(
                        "Ignoring result " + title + " because we don't want an episode that is " +
                        Quality.qualityStrings[
                            quality])

                continue

            sickrage.LOGGER.debug("Found result " + title + " at " + url)

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
                sickrage.LOGGER.debug("Single episode result.")
            elif len(epObj) > 1:
                epNum = MULTI_EP_RESULT
                sickrage.LOGGER.debug("Separating multi-episode result to check for later - result contains episodes: " + str(
                        parse_result.episode_numbers))
            elif len(epObj) == 0:
                epNum = SEASON_RESULT
                sickrage.LOGGER.debug("Separating full season result to check for later")

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

        return [Proper(x[b'name'], x[b'url'], datetime.datetime.fromtimestamp(x[b'time']), self.show) for x in
                results]

    def seedRatio(self):
        '''
        Provider should override this value if custom seed ratio enabled
        It should return the value of the provider seed ratio
        '''
        return ''

    @classmethod
    def getDefaultProviders(cls):
        return ''

    @classmethod
    def getProvider(cls, name):
        providerMatch = [x for x in cls.getProviderList() if x.name == name]
        if len(providerMatch) == 1:
            return providerMatch[0]

    @classmethod
    def getProviderByID(cls, id):
        providerMatch = [x for x in cls.getProviderList() if x.id == id]
        if len(providerMatch) == 1:
            return providerMatch[0]

    @classmethod
    def getProviderList(cls, data=None):
        modules = []
        for type in GenericProvider.types:
            modules += cls.loadProviders(type)
        return modules

    @classmethod
    def loadProviders(cls, type):
        providers = []
        pregex = re.compile('^([^_]*?)\.py$', re.IGNORECASE)
        path = os.path.join(os.path.dirname(__file__), type)
        names = [pregex.match(m) for m in os.listdir(path)]
        providers += [cls.loadProvider(name.group(1), type) for name in names if name]
        return providers

    @classmethod
    def loadProvider(cls, name, type, *args, **kwargs):
        import inspect, sys
        sys.path.append(os.path.join(os.path.dirname(__file__), 'sickrage'))
        members = dict(
                inspect.getmembers(
                        importlib.import_module('.{}.{}'.format(type, name), 'sickrage.providers'),
                        lambda x: hasattr(x, 'type') and x not in [NZBProvider, TorrentProvider])
        )
        return [v for v in members.values() if hasattr(v, 'type') and v.type == type][0](
            *args, **kwargs)

class TorrentProvider(GenericProvider):
    type = GenericProvider.TORRENT

    def __init__(self, name):
        super(TorrentProvider, self).__init__(name)

    @property
    def isActive(self):
        return sickrage.USE_TORRENTS and self.isEnabled

    def _get_title_and_url(self, item):
        title = None
        download_url = None

        if isinstance(item, (dict, FeedParserDict)):
            title = item.get('title', '')
            download_url = item.get('url', '')
            if not download_url:
                download_url = item.get('link', '')
        elif isinstance(item, (list, tuple)) and len(item) > 1:
            title = item[0]
            download_url = item[1]

        # Temp global block `DIAMOND` releases
        if title and title.endswith('DIAMOND'):
            sickrage.LOGGER.info('Skipping DIAMOND release for mass fake releases.')
            title = download_url = 'FAKERELEASE'
        elif title:
            title = self._clean_title_from_provider(title)
        if download_url:
            download_url = download_url.replace('&amp;', '&')

        return title, download_url

    def _get_size(self, item):

        size = -1
        if isinstance(item, dict):
            size = item.get('size', -1)
        elif isinstance(item, (list, tuple)) and len(item) > 2:
            size = item[2]

        # Make sure we didn't select seeds/leechers by accident
        if not size or size < 1024 * 1024:
            size = -1

        return size

    def _get_season_search_strings(self, ep_obj):

        search_string = {'Season': []}
        for show_name in set(allPossibleShowNames(self.show)):
            if ep_obj.show.air_by_date or ep_obj.show.sports:
                ep_string = show_name + ' ' + str(ep_obj.airdate).split('-')[0]
            elif ep_obj.show.anime:
                ep_string = show_name + ' ' + "%d" % ep_obj.scene_absolute_number
            else:
                ep_string = show_name + ' S%02d' % int(ep_obj.scene_season)  # 1) showName.SXX

            search_string[b'Season'].append(ep_string.encode('utf-8').strip())

        return [search_string]

    def _get_episode_search_strings(self, ep_obj, add_string=''):

        search_string = {'Episode': []}

        if not ep_obj:
            return []

        for show_name in set(allPossibleShowNames(ep_obj.show)):
            ep_string = show_name + ' '
            if ep_obj.show.air_by_date:
                ep_string += str(ep_obj.airdate).replace('-', ' ')
            elif ep_obj.show.sports:
                ep_string += str(ep_obj.airdate).replace('-', ' ') + ('|', ' ')[
                    len(self.proper_strings) > 1] + ep_obj.airdate.strftime('%b')
            elif ep_obj.show.anime:
                ep_string += "%02d" % int(ep_obj.scene_absolute_number)
            else:
                ep_string += sickrage.NAMING_EP_TYPE[2] % {'seasonnumber': ep_obj.scene_season,
                                                                   'episodenumber': ep_obj.scene_episode}
            if add_string:
                ep_string = ep_string + ' %s' % add_string

            search_string[b'Episode'].append(ep_string.strip())

        return [search_string]

    @staticmethod
    def _clean_title_from_provider(title):
        return (title or '').replace(' ', '.')

    def findPropers(self, search_date=datetime.datetime.today()):

        results = []

        sqlResults = main_db.MainDB().select(
                'SELECT s.show_name, e.showid, e.season, e.episode, e.status, e.airdate FROM tv_episodes AS e' +
                ' INNER JOIN tv_shows AS s ON (e.showid = s.indexer_id)' +
                ' WHERE e.airdate >= ' + str(search_date.toordinal()) +
                ' AND e.status IN (' + ','.join(
                        [str(x) for x in Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_BEST]) + ')'
        )

        for sqlshow in sqlResults or []:
            show = findCertainShow(sickrage.showList, int(sqlshow[b"showid"]))
            if show:
                curEp = show.getEpisode(int(sqlshow[b"season"]), int(sqlshow[b"episode"]))
                for term in self.proper_strings:
                    searchString = self._get_episode_search_strings(curEp, add_string=term)

                    for item in self._doSearch(searchString[0]):
                        title, url = self._get_title_and_url(item)
                        results.append(Proper(title, url, datetime.datetime.today(), show))

        return results

    @classmethod
    def getProviderList(cls, data=None):
        return super(TorrentProvider, cls).loadProviders(GenericProvider.TORRENT)


class NZBProvider(GenericProvider):
    type = GenericProvider.NZB

    def __init__(self, name):
        super(NZBProvider, self).__init__(name)

    @property
    def isActive(self):
        return sickrage.USE_NZBS and self.isEnabled

    def _get_size(self, item):
        try:
            size = item.get('links')[1].get('length', -1)
        except IndexError:
            size = -1

        if not size:
            sickrage.LOGGER.debug("Size was not found in your provider response")

        return int(size)

    @classmethod
    def getProviderList(cls, data=None):
        return super(NZBProvider, cls).loadProviders(GenericProvider.NZB)


class TorrentRssProvider(TorrentProvider):
    type = GenericProvider.TORRENT

    def __init__(self,
                 name,
                 url,
                 cookies='',
                 titleTAG='title',
                 search_mode='eponly',
                 search_fallback=False,
                 enable_daily=False,
                 enable_backlog=False
                 ):
        super(TorrentRssProvider, self).__init__(name)

        self.cache = TorrentRssCache(self)

        self.urls = {'base_url': re.sub(r'/$', '', url)}

        self.url = self.urls['base_url']

        self.ratio = None
        self.supportsBacklog = False

        self.search_mode = search_mode
        self.search_fallback = search_fallback
        self.enable_daily = enable_daily
        self.enable_backlog = enable_backlog
        self.cookies = cookies
        self.titleTAG = titleTAG

    def configStr(self):
        return "%s|%s|%s|%s|%d|%s|%d|%d|%d" % (
            self.name,
            self.url,
            self.cookies,
            self.titleTAG,
            int(self.enabled),
            self.search_mode,
            int(self.search_fallback),
            int(self.enable_daily),
            int(self.enable_backlog)
        )

    def imageName(self):
        if os.path.isfile(os.path.join(sickrage.GUI_DIR, 'images', 'providers', self.id + '.png')):
            return '{}.png'.format(self.id)
        return 'torrentrss.png'

    def _get_title_and_url(self, item):

        title = item.get(self.titleTAG)
        if title:
            title = self._clean_title_from_provider(title)

        attempt_list = [lambda: item.get('torrent_magneturi'),

                        lambda: item.enclosures[0].href,

                        lambda: item.get('link')]

        url = None
        for cur_attempt in attempt_list:
            try:
                url = cur_attempt()
            except Exception:
                continue

            if title and url:
                break

        return title, url

    def validateRSS(self):

        try:
            if self.cookies:
                cookie_validator = re.compile(r"^(\w+=\w+)(;\w+=\w+)*$")
                if not cookie_validator.match(self.cookies):
                    return False, 'Cookie is not correctly formatted: ' + self.cookies

            # pylint: disable=W0212
            # Access to a protected member of a client class
            data = self.cache._getRSSData()['entries']
            if not data:
                return False, 'No items found in the RSS feed ' + self.url

            (title, url) = self._get_title_and_url(data[0])

            if not title:
                return False, 'Unable to get title from first item'

            if not url:
                return False, 'Unable to get torrent url from first item'

            if url.startswith('magnet:') and re.search(r'urn:btih:([\w]{32,40})', url):
                return True, 'RSS feed Parsed correctly'
            else:
                if self.cookies:
                    requests.utils.add_dict_to_cookiejar(self.session.cookies,
                                                         dict(x.rsplit('=', 1) for x in self.cookies.split(';')))
                torrent_file = self.getURL(url)
                try:
                    bencode.bdecode(torrent_file)
                except Exception as e:
                    self.dumpHTML(torrent_file)
                    return False, 'Torrent link is not a valid torrent file: {}'.format(e)

            return True, 'RSS feed Parsed correctly'

        except Exception as e:
            return False, 'Error when trying to load RSS: {}'.format(e)

    @staticmethod
    def dumpHTML(data):
        dumpName = os.path.join(sickrage.CACHE_DIR, 'custom_torrent.html')

        try:
            with io.open(dumpName, 'wb') as fileOut:
                fileOut.write(data)
            chmodAsParent(dumpName)
        except IOError as e:
            sickrage.LOGGER.error("Unable to save the file: %s " % repr(e))
            return False
        sickrage.LOGGER.info("Saved custom_torrent html dump %s " % dumpName)
        return True

    def seedRatio(self):
        return self.ratio

    @classmethod
    def getProviderList(cls, data=None):
        providerList = filter(lambda x: x, [cls.makeProvider(x) for x in data.split('!!!')])

        seen_values = set()
        providerListDeduped = []
        for d in providerList:
            value = d.name
            if value not in seen_values:
                providerListDeduped.append(d)
                seen_values.add(value)

        return filter(lambda l: l, providerList)

    @classmethod
    def makeProvider(cls, configString):
        if not configString:
            return None

        cookies = None
        titleTAG = 'title'
        search_mode = 'eponly'
        search_fallback = 0
        enable_daily = 0
        enable_backlog = 0

        try:
            values = configString.split('|')
            if len(values) == 9:
                name, url, cookies, titleTAG, enabled, search_mode, search_fallback, enable_daily, enable_backlog = values
            elif len(values) == 8:
                name, url, cookies, enabled, search_mode, search_fallback, enable_daily, enable_backlog = values
            else:
                name = values[0]
                url = values[1]
                enabled = values[4]
        except ValueError:
            sickrage.LOGGER.error("Skipping RSS Torrent provider string: '" + configString + "', incorrect format")
            return None

        newProvider = cls(name=name,
                          url=url,
                          cookies=cookies,
                          titleTAG=titleTAG,
                          search_mode=search_mode,
                          search_fallback=search_fallback,
                          enable_daily=enable_daily,
                          enable_backlog=enable_backlog)

        newProvider.enabled = enabled == '1'
        return newProvider


class NewznabProvider(NZBProvider):
    type = GenericProvider.NZB

    def __init__(self,
                 name,
                 url,
                 key='0',
                 catIDs='5030,5040',
                 search_mode='eponly',
                 search_fallback=False,
                 enable_daily=False,
                 enable_backlog=False
                 ):
        super(NewznabProvider, self).__init__(name)

        self.cache = NewznabCache(self)

        self.urls = {'base_url': url}

        self.url = self.urls['base_url']

        self.key = key

        self.search_mode = search_mode
        self.search_fallback = search_fallback
        self.enable_daily = enable_daily
        self.enable_backlog = enable_backlog

        # a 0 in the key spot indicates that no key is needed
        if self.key == '0':
            self.needs_auth = False
        else:
            self.needs_auth = True

        self.public = not self.needs_auth

        if catIDs:
            self.catIDs = catIDs
        else:
            self.catIDs = '5030,5040'

        self.supportsBacklog = True

        self.default = False
        self.last_search = datetime.datetime.now()

    def configStr(self):
        return self.name + '|' + self.url + '|' + self.key + '|' + self.catIDs + '|' + str(
                int(self.enabled)) + '|' + self.search_mode + '|' + str(int(self.search_fallback)) + '|' + str(
                int(self.enable_daily)) + '|' + str(int(self.enable_backlog))

    def imageName(self):
        if os.path.isfile(
                os.path.join(sickrage.GUI_DIR, 'images', 'providers', self.id + '.png')):
            return self.id + '.png'
        return 'newznab.png'

    def _getURL(self, url, post_data=None, params=None, timeout=30, json=False):
        return self.getURL(url, post_data=post_data, params=params, timeout=timeout, json=json)

    def get_newznab_categories(self):
        """
        Uses the newznab provider url and apikey to get the capabilities.
        Makes use of the default newznab caps param. e.a. http://yournewznab/api?t=caps&apikey=skdfiw7823sdkdsfjsfk
        Returns a tuple with (succes or not, array with dicts [{"id": "5070", "name": "Anime"},
        {"id": "5080", "name": "Documentary"}, {"id": "5020", "name": "Foreign"}...etc}], error message)
        """
        return_categories = []

        self._checkAuth()

        params = {"t": "caps"}
        if self.needs_auth and self.key:
            params[b'apikey'] = self.key

        try:
            data = self.cache.getRSSFeed("%s/api?%s" % (self.url, urllib.urlencode(params)))
        except Exception:
            sickrage.LOGGER.warning("Error getting html for [%s]" %
                            ("%s/api?%s" % (self.url, '&'.join("%s=%s" % (x, y) for x, y in params.iteritems()))))
            return (False, return_categories, "Error getting html for [%s]" %
                    ("%s/api?%s" % (self.url, '&'.join("%s=%s" % (x, y) for x, y in params.iteritems()))))

        if not self._checkAuthFromData(data):
            sickrage.LOGGER.debug("Error parsing xml")
            return False, return_categories, "Error parsing xml for [%s]" % (self.name)

        try:
            for category in data.feed.categories:
                if category.get('name') == 'TV':
                    return_categories.append(category)
                    for subcat in category.subcats:
                        return_categories.append(subcat)
        except Exception:
            sickrage.LOGGER.debug("[%s] does not list categories" % (self.name))
            return (False, return_categories, "[%s] does not list categories" % (self.name))

        return True, return_categories, ""

    def _get_season_search_strings(self, ep_obj):

        to_return = []
        params = {}
        if not ep_obj:
            return to_return

        params[b'maxage'] = (datetime.datetime.now() - datetime.datetime.combine(ep_obj.airdate,
                                                                                 datetime.datetime.min.time())).days + 1
        params[b'tvdbid'] = ep_obj.show.indexerid

        # season
        if ep_obj.show.air_by_date or ep_obj.show.sports:
            date_str = str(ep_obj.airdate).split('-')[0]
            params[b'season'] = date_str
            params[b'q'] = date_str.replace('-', '.')
        else:
            params[b'season'] = str(ep_obj.scene_season)

        save_q = ' ' + params[b'q'] if 'q' in params else ''

        # add new query strings for exceptions
        name_exceptions = list(
                set([ep_obj.show.name] + get_scene_exceptions(ep_obj.show.indexerid)))
        for cur_exception in name_exceptions:
            params[b'q'] = sanitizeSceneName(cur_exception) + save_q
            to_return.append(dict(params))

        return to_return

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        to_return = []
        params = {}
        if not ep_obj:
            return to_return

        params[b'maxage'] = (datetime.datetime.now() - datetime.datetime.combine(ep_obj.airdate,
                                                                                 datetime.datetime.min.time())).days + 1
        params[b'tvdbid'] = ep_obj.show.indexerid

        if ep_obj.show.air_by_date or ep_obj.show.sports:
            date_str = str(ep_obj.airdate)
            params[b'season'] = date_str.partition('-')[0]
            params[b'ep'] = date_str.partition('-')[2].replace('-', '/')
        else:
            params[b'season'] = ep_obj.scene_season
            params[b'ep'] = ep_obj.scene_episode

        # add new query strings for exceptions
        name_exceptions = list(
                set([ep_obj.show.name] + get_scene_exceptions(ep_obj.show.indexerid)))
        for cur_exception in name_exceptions:
            params[b'q'] = sanitizeSceneName(cur_exception)
            if add_string:
                params[b'q'] += ' ' + add_string

            to_return.append(dict(params))

        return to_return

    def _doGeneralSearch(self, search_string):
        return self._doSearch({'q': search_string})

    def _checkAuth(self):
        if self.needs_auth and not self.key:
            sickrage.LOGGER.warning("Your authentication credentials for " + self.name + " are missing, check your config.")
            return False
        return True

    def _checkAuthFromData(self, data):

        """

        :type data: dict
        """
        try:
            data[b'feed']
            data[b'entries']
        except (AttributeError, KeyError):
            return self._checkAuth()

        try:
            if int(data[b'bozo']) == 1:
                raise Exception(data[b'bozo_exception'])
        except (AttributeError, KeyError):
            pass

        try:
            err_code = data[b'feed'][b'error'][b'code']
            err_desc = data[b'feed'][b'error'][b'description']

            if int(err_code) == 100:
                raise AuthException("Your API key for " + self.name + " is incorrect, check your config.")
            elif int(err_code) == 101:
                raise AuthException("Your account on " + self.name + " has been suspended, contact the administrator.")
            elif int(err_code) == 102:
                raise AuthException(
                        "Your account isn't allowed to use the API on " + self.name + ", contact the administrator")
            raise Exception("Unknown error: %s" % err_desc)
        except (AttributeError, KeyError):
            pass

        return True

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        self._checkAuth()

        params = {"t": "tvsearch",
                  "maxage": (4, age)[age],
                  "limit": 100,
                  "offset": 0}

        if search_params:
            params.update(search_params)
            sickrage.LOGGER.debug('Search parameters: %s' % repr(search_params))

        # category ids
        if self.show and self.show.is_sports:
            params[b'cat'] = self.catIDs + ',5060'
        elif self.show and self.show.is_anime:
            params[b'cat'] = self.catIDs + ',5070'
        else:
            params[b'cat'] = self.catIDs

        params[b'cat'] = params[b'cat'].strip(', ')

        if self.needs_auth and self.key:
            params[b'apikey'] = self.key

        params[b'maxage'] = min(params[b'maxage'], sickrage.USENET_RETENTION)

        results = []
        offset = total = 0

        if 'lolo.sickrage.com' in self.url and params[b'maxage'] < 33:
            params[b'maxage'] = 33

        while total >= offset:
            search_url = self.url + 'api?' + urllib.urlencode(params)

            while (datetime.datetime.now() - self.last_search).seconds < 5:
                gen.sleep(1)

            sickrage.LOGGER.debug("Search url: %s" % search_url)

            data = self.cache.getRSSFeed(search_url)

            self.last_search = datetime.datetime.now()

            if not self._checkAuthFromData(data):
                break

            for item in data[b'entries']:

                (title, url) = self._get_title_and_url(item)

                if title and url:
                    results.append(item)

            # get total and offset attribs
            try:
                if total == 0:
                    total = int(data[b'feed'].newznab_response[b'total'] or 0)
                offset = int(data[b'feed'].newznab_response[b'offset'] or 0)
            except AttributeError:
                break

            # No items found, prevent from doing another search
            if total == 0:
                break

            if offset != params[b'offset']:
                sickrage.LOGGER.info("Tell your newznab provider to fix their bloody newznab responses")
                break

            params[b'offset'] += params[b'limit']
            if (total > int(params[b'offset'])) and (offset < 500):
                offset = int(params[b'offset'])
                # if there are more items available then the amount given in one call, grab some more
                sickrage.LOGGER.debug('%d' % (total - offset) + ' more items to be fetched from provider.' +
                              'Fetching another %d' % int(params[b'limit']) + ' items.')
            else:
                sickrage.LOGGER.debug('No more searches needed')
                break

        return results

    def findPropers(self, search_date=datetime.datetime.today()):
        results = []

        sqlResults = main_db.MainDB().select(
                'SELECT s.show_name, e.showid, e.season, e.episode, e.status, e.airdate FROM tv_episodes AS e' +
                ' INNER JOIN tv_shows AS s ON (e.showid = s.indexer_id)' +
                ' WHERE e.airdate >= ' + str(search_date.toordinal()) +
                ' AND (e.status IN (' + ','.join([str(x) for x in Quality.DOWNLOADED]) + ')' +
                ' OR (e.status IN (' + ','.join([str(x) for x in Quality.SNATCHED]) + ')))'
        )

        if not sqlResults:
            return []

        for sqlshow in sqlResults:
            self.show = findCertainShow(sickrage.showList, int(sqlshow[b"showid"]))
            if self.show:
                curEp = self.show.getEpisode(int(sqlshow[b"season"]), int(sqlshow[b"episode"]))
                searchStrings = self._get_episode_search_strings(curEp, add_string='PROPER|REPACK')
                for searchString in searchStrings:
                    for item in self._doSearch(searchString):
                        title, url = self._get_title_and_url(item)
                        if re.match(r'.*(REPACK|PROPER).*', title, re.I):
                            results.append(Proper(title, url, datetime.datetime.today(), self.show))

        return results

    @classmethod
    def getProviderList(cls, data=None):
        defaultList = [cls.makeProvider(x) for x in cls.getDefaultProviders().split('!!!')]
        providerList = filter(lambda x: x, [cls.makeProvider(x) for x in data.split('!!!')])

        seen_values = set()
        providerListDeduped = []
        for d in providerList:
            value = d.name
            if value not in seen_values:
                providerListDeduped.append(d)
                seen_values.add(value)

        providerList = providerListDeduped
        providerDict = dict(zip([x.name for x in providerList], providerList))

        for curDefault in defaultList:
            if not curDefault:
                continue

            if curDefault.name not in providerDict:
                curDefault.default = True
                providerList.append(curDefault)
            else:
                providerDict[curDefault.name].default = True
                providerDict[curDefault.name].name = curDefault.name
                providerDict[curDefault.name].url = curDefault.url
                providerDict[curDefault.name].needs_auth = curDefault.needs_auth
                providerDict[curDefault.name].search_mode = curDefault.search_mode
                providerDict[curDefault.name].search_fallback = curDefault.search_fallback
                providerDict[curDefault.name].enable_daily = curDefault.enable_daily
                providerDict[curDefault.name].enable_backlog = curDefault.enable_backlog

        return filter(lambda x: x, providerList)

    @classmethod
    def makeProvider(cls, configString):
        if not configString:
            return None

        search_mode = 'eponly'
        search_fallback = 0
        enable_daily = 0
        enable_backlog = 0

        try:
            values = configString.split('|')
            if len(values) == 9:
                name, url, key, catIDs, enabled, search_mode, search_fallback, enable_daily, enable_backlog = values
            else:
                name = values[0]
                url = values[1]
                key = values[2]
                catIDs = values[3]
                enabled = values[4]
        except ValueError:
            sickrage.LOGGER.error("Skipping Newznab provider string: '" + configString + "', incorrect format")
            return None

        newProvider = cls(name=name,
                          url=url,
                          key=key,
                          catIDs=catIDs,
                          search_mode=search_mode,
                          search_fallback=search_fallback,
                          enable_daily=enable_daily,
                          enable_backlog=enable_backlog)

        newProvider.enabled = enabled == '1'
        return newProvider

    @classmethod
    def getDefaultProviders(cls):
        # name|url|key|catIDs|enabled|search_mode|search_fallback|enable_daily|enable_backlog
        return 'NZB.Cat|https://nzb.cat/||5030,5040,5010|0|eponly|1|1|1!!!' + \
               'NZBGeek|https://api.nzbgeek.info/||5030,5040|0|eponly|0|0|0!!!' + \
               'NZBs.org|https://nzbs.org/||5030,5040|0|eponly|0|0|0!!!' + \
               'Usenet-Crawler|https://www.usenet-crawler.com/||5030,5040|0|eponly|0|0|0'


class TorrentRssCache(TVCache):
    def __init__(self, provider_obj):
        TVCache.__init__(self, provider_obj)
        self.minTime = 15

    def _getRSSData(self):
        sickrage.LOGGER.debug("Cache update URL: %s" % self.provider.url)

        if self.provider.cookies:
            self.provider.headers.update({'Cookie': self.provider.cookies})

        return self.getRSSFeed(self.provider.url)


class NewznabCache(TVCache):
    def __init__(self, provider_obj):

        TVCache.__init__(self, provider_obj)

        # only poll newznab providers every 30 minutes
        self.minTime = 30
        self.last_search = datetime.datetime.now()

    def _getRSSData(self):

        params = {"t": "tvsearch",
                  "cat": self.provider.catIDs + ',5060,5070',
                  "maxage": 4,
                  }

        if 'lolo.sickrage.com' in self.provider.url:
            params[b'maxage'] = 33

        if self.provider.needs_auth and self.provider.key:
            params[b'apikey'] = self.provider.key

        rss_url = self.provider.url + 'api?' + urllib.urlencode(params)

        while (datetime.datetime.now() - self.last_search).seconds < 5:
            gen.sleep(1)

        sickrage.LOGGER.debug("Cache update URL: %s " % rss_url)
        data = self.getRSSFeed(rss_url)

        self.last_search = datetime.datetime.now()

        return data

    def _checkAuth(self, data):
        return self.provider._checkAuthFromData(data)

    def _parseItem(self, item):
        title, url = self._get_title_and_url(item)

        self._checkItemAuth(title, url)

        if not title or not url:
            return None

        tvrageid = 0

        sickrage.LOGGER.debug("Attempting to add item from RSS to cache: %s" % title)
        return self._addCacheEntry(title, url, indexer_id=tvrageid)


def sortedProviderDict(randomize=False):
    from collections import OrderedDict

    sortedProviders = OrderedDict()

    providerOrder = sickrage.PROVIDER_ORDER

    if randomize:
        random.shuffle(providerOrder)

    for providerType in [GenericProvider.NZB, GenericProvider.TORRENT]:
        sortedProviders.update((key, sickrage.providersDict[providerType][key]) for key in providerOrder
                               if sickrage.providersDict[providerType].has_key(key))

    return sortedProviders
