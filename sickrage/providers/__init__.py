# Author: echel0n <echel0n@sickrage.ca>
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
import time
import urllib
from base64 import b16encode, b32decode
from collections import OrderedDict

import bencode
import requests
import xmltodict
from feedparser import FeedParserDict
from hachoir_core.stream import StringInputStream
from hachoir_parser import guessParser

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.classes import NZBSearchResult, Proper, SearchResult, \
    TorrentSearchResult
from sickrage.core.common import MULTI_EP_RESULT, Quality, SEASON_RESULT
from sickrage.core.databases import main_db
from sickrage.core.exceptions import AuthException
from sickrage.core.helpers import chmodAsParent, \
    findCertainShow, remove_file_failed, \
    sanitizeFileName, sanitizeSceneName
from sickrage.core.helpers.show_names import allPossibleShowNames
from sickrage.core.nameparser import InvalidNameException, InvalidShowException, \
    NameParser
from sickrage.core.scene_exceptions import get_scene_exceptions


class GenericProvider(object):
    def __init__(self, name, url):
        self.name = name
        self.urls = {'base_url': url}
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
        self.proper_strings = ['PROPER|REPACK|REAL']
        self.private = False

        self.btCacheURLS = [
            'http://torcache.net/torrent/{torrent_hash}.torrent',
            'http://thetorrent.org/torrent/{torrent_hash}.torrent',
            'http://btdig.com/torrent/{torrent_hash}.torrent',
            # 'http://torrage.com/torrent/{torrent_hash}.torrent',
            # 'http://itorrents.org/torrent/{torrent_hash}.torrent',
        ]

    @property
    def id(self):
        return str(re.sub(r"[^\w\d_]", "_", self.name.strip().lower()))

    @property
    def isEnabled(self):
        return self.enabled

    @property
    def imageName(self):
        return ""

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
            result = {'nzb': NZBSearchResult, 'torrent': TorrentSearchResult}[getattr(self, 'type')](episodes)
        except:
            result = SearchResult(episodes)

        result.provider = self
        return result

    def make_url(self, result):
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
                    sickrage.srCore.srLogger.error("Unable to extract torrent hash from magnet: " + result.url)
                    return urls, filename

                urls = random.shuffle(
                    [x.format(torrent_hash=torrent_hash, torrent_name=torrent_name) for x in self.btCacheURLS])
            except Exception:
                sickrage.srCore.srLogger.error("Unable to extract torrent hash or name from magnet: " + result.url)
                return urls, filename
        else:
            urls = [result.url]

        return urls, filename

    def downloadResult(self, result):
        """
        Save the result to disk.
        """

        # check for auth
        if not self._doLogin:
            return False

        urls, filename = self.make_url(result)

        for url in urls:
            if 'NO_DOWNLOAD_NAME' in url:
                continue

            sickrage.srCore.srLogger.info("Downloading a result from " + self.name + " at " + url)

            # Support for Jackett/TorzNab
            if url.endswith('torrent') and filename.endswith('nzb'):
                filename = filename.rsplit('.', 1)[0] + '.' + 'torrent'

            if sickrage.srCore.srWebSession.download(url, filename,
                                                     headers=(None, {'Referer': '/'.join(url.split('/')[:3]) + '/'})[
                                                         url.startswith('http')]):

                if self._verify_download(filename):
                    sickrage.srCore.srLogger.info("Saved result to " + filename)
                    return True
                else:
                    sickrage.srCore.srLogger.warning("Could not download %s" % url)
                    remove_file_failed(filename)

        if len(urls):
            sickrage.srCore.srLogger.warning("Failed to download any results")

        return False

    def _verify_download(self, file_name=None):
        """
        Checks the saved file to see if it was actually valid, if not then consider the download a failure.
        """

        # primitive verification of torrents, just make sure we didn't get a text file or something
        if file_name.endswith('torrent'):
            try:
                with open(file_name, 'rb') as file:
                    mime_type = guessParser(StringInputStream(file.read()))._getMimeType()
                    if mime_type == 'application/x-bittorrent':
                        return True
            except Exception as e:
                sickrage.srCore.srLogger.debug("Failed to validate torrent file: {}".format(e.message))

            sickrage.srCore.srLogger.debug("Result is not a valid torrent file")
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

    def search(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):
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

        title = item.get('title', '').replace(' ', '.')
        url = item.get('link', '').replace('&amp;', '&').replace('%26tr%3D', '&tr=')

        return title, url

    def _get_size(self, item):
        """Gets the size from the item"""
        sickrage.srCore.srLogger.error("Provider type doesn't have _get_size() implemented yet")
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
                sickrage.srCore.srLogger.debug('First search_string has rid')

            for curString in search_strings:
                itemList += self.search(curString, search_mode, len(episodes), epObj=epObj)
                if first:
                    first = False
                    if itemList:
                        sickrage.srCore.srLogger.debug(
                            'First search_string had rid, and returned results, skipping query by string')
                        break
                    else:
                        sickrage.srCore.srLogger.debug(
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

            itemList = list(itertools.chain(*[v for (k, v) in sorted(items.items(), reverse=True)]))
            itemList += itemsUnknown or []

        # filter results
        cl = []
        for item in itemList:
            (title, url) = self._get_title_and_url(item)

            # parse the file name
            try:
                myParser = NameParser(False)
                parse_result = myParser.parse(title)
            except InvalidNameException:
                sickrage.srCore.srLogger.debug("Unable to parse the filename " + title + " into a valid episode")
                continue
            except InvalidShowException:
                sickrage.srCore.srLogger.debug("Unable to parse the filename " + title + " into a valid show")
                continue

            showObj = parse_result.show
            quality = parse_result.quality
            release_group = parse_result.release_group
            version = parse_result.version

            addCacheEntry = False
            if not (showObj.air_by_date or showObj.sports):
                if search_mode == 'sponly':
                    if len(parse_result.episode_numbers):
                        sickrage.srCore.srLogger.debug(
                            "This is supposed to be a season pack search but the result " + title + " is not a valid season pack, skipping it")
                        addCacheEntry = True
                    if len(parse_result.episode_numbers) and (
                                    parse_result.season_number not in set([ep.season for ep in episodes])
                            or not [ep for ep in episodes if ep.scene_episode in parse_result.episode_numbers]):
                        sickrage.srCore.srLogger.debug(
                            "The result " + title + " doesn't seem to be a valid episode that we are trying to snatch, ignoring")
                        addCacheEntry = True
                else:
                    if not len(parse_result.episode_numbers) and parse_result.season_number and not [ep for ep in
                                                                                                     episodes if
                                                                                                     ep.season == parse_result.season_number and ep.episode in parse_result.episode_numbers]:
                        sickrage.srCore.srLogger.debug(
                            "The result " + title + " doesn't seem to be a valid season that we are trying to snatch, ignoring")
                        addCacheEntry = True
                    elif len(parse_result.episode_numbers) and not [ep for ep in episodes if
                                                                    ep.season == parse_result.season_number and ep.episode in parse_result.episode_numbers]:
                        sickrage.srCore.srLogger.debug(
                            "The result " + title + " doesn't seem to be a valid episode that we are trying to snatch, ignoring")
                        addCacheEntry = True

                if not addCacheEntry:
                    # we just use the existing info for normal searches
                    actual_season = parse_result.season_number
                    actual_episodes = parse_result.episode_numbers
            else:
                if not parse_result.is_air_by_date:
                    sickrage.srCore.srLogger.debug(
                        "This is supposed to be a date search but the result " + title + " didn't parse as one, skipping it")
                    addCacheEntry = True
                else:
                    airdate = parse_result.air_date.toordinal()
                    sql_results = main_db.MainDB().select(
                        "SELECT season, episode FROM tv_episodes WHERE showid = ? AND airdate = ?",
                        [showObj.indexerid, airdate])

                    if len(sql_results) != 1:
                        sickrage.srCore.srLogger.warning(
                            "Tried to look up the date for the episode " + title + " but the database didn't give proper results, skipping it")
                        addCacheEntry = True

                if not addCacheEntry:
                    actual_season = int(sql_results[0]["season"])
                    actual_episodes = [int(sql_results[0]["episode"])]

            # add parsed result to cache for usage later on
            if addCacheEntry:
                sickrage.srCore.srLogger.debug("Adding item from search to cache: " + title)
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
                sickrage.srCore.srLogger.info("RESULT:[{}] QUALITY:[{}] IGNORED!".format(title, Quality.qualityStrings[quality]))
                continue

            sickrage.srCore.srLogger.debug("FOUND RESULT:[{}] URL:[{}]".format(title, url))

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
                sickrage.srCore.srLogger.debug("Single episode result.")
            elif len(epObj) > 1:
                epNum = MULTI_EP_RESULT
                sickrage.srCore.srLogger.debug(
                    "Separating multi-episode result to check for later - result contains episodes: " + str(
                        parse_result.episode_numbers))
            elif len(epObj) == 0:
                epNum = SEASON_RESULT
                sickrage.srCore.srLogger.debug("Separating full season result to check for later")

            if epNum not in results:
                results[epNum] = [result]
            else:
                results[epNum].append(result)

        # check if we have items to add to cache
        if len(cl) > 0:
            self.cache._getDB().mass_action(cl)
            del cl  # cleanup

        return results

    def findPropers(self, search_date=None):

        results = self.cache.listPropers(search_date)

        return [Proper(x['name'], x['url'], datetime.datetime.fromtimestamp(x['time']), self.show) for x in
                results]

    def seedRatio(self):
        '''
        Provider should override this value if custom seed ratio enabled
        It should return the value of the provider seed ratio
        '''
        return ''

    @classmethod
    def getDefaultProviders(cls):
        pass

    @classmethod
    def getProvider(cls, name):
        providerMatch = [x for x in cls.getProviders() if x.name == name]
        if len(providerMatch) == 1:
            return providerMatch[0]

    @classmethod
    def getProviderByID(cls, id):
        providerMatch = [x for x in cls.getProviders() if x.id == id]
        if len(providerMatch) == 1:
            return providerMatch[0]

    @classmethod
    def getProviders(cls):
        modules = [TorrentProvider.type, NZBProvider.type]
        for type in []:
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
        import inspect
        members = dict(
            inspect.getmembers(
                importlib.import_module('.{}.{}'.format(type, name), 'sickrage.providers'),
                lambda x: hasattr(x, 'type') and x not in [NZBProvider, TorrentProvider])
        )
        return [v for v in members.values() if hasattr(v, 'type') and v.type == type][0](
            *args, **kwargs)


class TorrentProvider(GenericProvider):
    type = 'torrent'

    def __init__(self, name, url):
        super(TorrentProvider, self).__init__(name, url)

    @property
    def isActive(self):
        return sickrage.srCore.srConfig.USE_TORRENTS and self.isEnabled

    @property
    def imageName(self):
        if os.path.isfile(os.path.join(sickrage.srCore.srConfig.GUI_DIR, 'images', 'providers', self.id + '.png')):
            return self.id + '.png'
        return self.type + '.png'

    def _get_title_and_url(self, item):
        title, download_url = '', ''
        if isinstance(item, (dict, FeedParserDict)):
            title = item.get('title', '')
            download_url = item.get('url', item.get('link', ''))
        elif isinstance(item, (list, tuple)) and len(item) > 1:
            title = item[0]
            download_url = item[1]

        # Temp global block `DIAMOND` releases
        if title.endswith('DIAMOND'):
            sickrage.srCore.srLogger.info('Skipping DIAMOND release for mass fake releases.')
            title = download_url = 'FAKERELEASE'
        else:
            title = self._clean_title_from_provider(title)

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

            search_string['Season'].append(ep_string.encode('utf-8').strip())

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
                ep_string += sickrage.srCore.srConfig.NAMING_EP_TYPE[2] % {'seasonnumber': ep_obj.scene_season,
                                                                           'episodenumber': ep_obj.scene_episode}
            if add_string:
                ep_string = ep_string + ' %s' % add_string

            search_string['Episode'].append(ep_string.strip())

        return [search_string]

    @staticmethod
    def _clean_title_from_provider(title):
        return (title or '').replace(' ', '.')

    def make_url(self, result):
        urls, filename = super(TorrentProvider, self).make_url(result)
        filename = os.path.join(sickrage.srCore.srConfig.TORRENT_DIR,
                                sanitizeFileName(result.name) + '.' + self.type)

        return urls, filename

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
            show = findCertainShow(sickrage.srCore.SHOWLIST, int(sqlshow["showid"]))
            if show:
                curEp = show.getEpisode(int(sqlshow["season"]), int(sqlshow["episode"]))
                for term in self.proper_strings:
                    searchString = self._get_episode_search_strings(curEp, add_string=term)

                    for item in self.search(searchString[0]):
                        title, url = self._get_title_and_url(item)
                        results.append(Proper(title, url, datetime.datetime.today(), show))

        return results

    @classmethod
    def getProviders(cls):
        return super(TorrentProvider, cls).loadProviders(cls.type)


class NZBProvider(GenericProvider):
    type = 'nzb'

    def __init__(self, name, url):
        super(NZBProvider, self).__init__(name, url)
        self.api_key = None
        self.username = None

    @property
    def isActive(self):
        return sickrage.srCore.srConfig.USE_NZBS and self.isEnabled

    @property
    def imageName(self):
        if os.path.isfile(os.path.join(sickrage.srCore.srConfig.GUI_DIR, 'images', 'providers', self.id + '.png')):
            return self.id + '.png'
        return self.type + '.png'

    def _get_size(self, item):
        try:
            size = item.get('links')[1].get('length', -1)
        except IndexError:
            size = -1

        if not size:
            sickrage.srCore.srLogger.debug("Size was not found in your provider response")

        return int(size)

    def make_url(self, result):
        urls, filename = super(NZBProvider, self).make_url(result)
        filename = os.path.join(sickrage.srCore.srConfig.NZB_DIR,
                                sanitizeFileName(result.name) + '.' + self.type)
        return urls, filename

    @classmethod
    def getProviders(cls):
        return super(NZBProvider, cls).loadProviders(cls.type)


class TorrentRssProvider(TorrentProvider):
    type = 'torrentrss'

    def __init__(self,
                 name,
                 url,
                 cookies='',
                 titleTAG='title',
                 search_mode='eponly',
                 search_fallback=False,
                 enable_daily=False,
                 enable_backlog=False,
                 default=False):
        super(TorrentRssProvider, self).__init__(name, url)

        self.cache = TorrentRssCache(self)
        self.ratio = None
        self.supportsBacklog = False

        self.search_mode = search_mode
        self.search_fallback = search_fallback
        self.enable_daily = enable_daily
        self.enable_backlog = enable_backlog
        self.cookies = cookies
        self.titleTAG = titleTAG
        self.default = default

    def _get_title_and_url(self, item):

        title = item.get(self.titleTAG, '')
        title = self._clean_title_from_provider(title)

        attempt_list = [lambda: item.get('torrent_magneturi'),

                        lambda: item.enclosures[0].href,

                        lambda: item.get('link')]

        url = ''
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
                return False, 'No items found in the RSS feed ' + self.urls['base_url']

            (title, url) = self._get_title_and_url(data[0])

            if not title:
                return False, 'Unable to get title from first item'

            if not url:
                return False, 'Unable to get torrent url from first item'

            if url.startswith('magnet:') and re.search(r'urn:btih:([\w]{32,40})', url):
                return True, 'RSS feed Parsed correctly'
            else:
                if self.cookies:
                    requests.utils.add_dict_to_cookiejar(sickrage.srCore.srWebSession.cookies,
                                                         dict(x.rsplit('=', 1) for x in self.cookies.split(';')))

                try:
                    torrent_file = sickrage.srCore.srWebSession.get(url).text
                except Exception:
                    return False, 'Unable to get torrent from url'

                try:
                    bencode.bdecode(torrent_file)
                except Exception as e:
                    self.dumpHTML(torrent_file)
                    return False, 'Torrent link is not a valid torrent file: {}'.format(e.message)

            return True, 'RSS feed Parsed correctly'

        except Exception as e:
            return False, 'Error when trying to load RSS: {}'.format(e.message)

    @staticmethod
    def dumpHTML(data):
        dumpName = os.path.join(sickrage.srCore.srConfig.CACHE_DIR, 'custom_torrent.html')

        try:
            with io.open(dumpName, 'wb') as fileOut:
                fileOut.write(data)
            chmodAsParent(dumpName)
        except IOError as e:
            sickrage.srCore.srLogger.error("Unable to save the file: %s " % repr(e))
            return False
        sickrage.srCore.srLogger.info("Saved custom_torrent html dump %s " % dumpName)
        return True

    def seedRatio(self):
        return self.ratio

    @classmethod
    def getProviders(cls):
        return cls.getDefaultProviders()

    @classmethod
    def getDefaultProviders(cls):
        return [
            cls('showRSS', 'showrss.info', None, 'title', 'eponly', True, True, True, True)
        ]


class NewznabProvider(NZBProvider):
    type = 'newznab'

    def __init__(self,
                 name,
                 url,
                 key=None,
                 catIDs='5030,5040',
                 search_mode='eponly',
                 search_fallback=False,
                 enable_daily=False,
                 enable_backlog=False,
                 default=False):
        super(NewznabProvider, self).__init__(name, url)

        self.cache = NewznabCache(self)
        self.search_mode = search_mode
        self.search_fallback = search_fallback
        self.enable_daily = enable_daily
        self.enable_backlog = enable_backlog
        self.key = key
        self.supportsBacklog = True
        self.catIDs = catIDs
        self.default = default
        self.last_search = datetime.datetime.now()

    def get_newznab_categories(self):
        """
        Uses the newznab provider url and apikey to get the capabilities.
        Makes use of the default newznab caps param. e.a. http://yournewznab/api?t=caps&apikey=skdfiw7823sdkdsfjsfk
        Returns a tuple with (succes or not, array with dicts [{"id": "5070", "name": "Anime"},
        {"id": "5080", "name": "Documentary"}, {"id": "5020", "name": "Foreign"}...etc}], error message)
        """
        success = False
        categories = []
        message = ""

        self._checkAuth()

        params = {"t": "caps"}
        if self.key:
            params['apikey'] = self.key

        try:
            data = xmltodict.parse(
                sickrage.srCore.srWebSession.get("{}api?{}".format(self.urls['base_url'], urllib.urlencode(params))))

            for category in data["caps"]["categories"]["category"]:
                if category.get('@name') == 'TV':
                    categories += [{"id": category['@id'], "name": category['@name']}]
                    categories += [{"id": x["@id"], "name": x["@name"]} for x in category["subcat"]]

            success = True
        except Exception:
            sickrage.srCore.srLogger.debug("[%s] failed to list categories" % self.name)
            message = "[%s] failed to list categories" % self.name

        return success, categories, message

    def _get_season_search_strings(self, ep_obj):

        to_return = []
        params = {}
        if not ep_obj:
            return to_return

        params['maxage'] = (datetime.datetime.now() - datetime.datetime.combine(ep_obj.airdate,
                                                                                datetime.datetime.min.time())).days + 1
        params['tvdbid'] = ep_obj.show.indexerid

        # season
        if ep_obj.show.air_by_date or ep_obj.show.sports:
            date_str = str(ep_obj.airdate).split('-')[0]
            params['season'] = date_str
            params['q'] = date_str.replace('-', '.')
        else:
            params['season'] = str(ep_obj.scene_season)

        save_q = ' ' + params['q'] if 'q' in params else ''

        # add new query strings for exceptions
        name_exceptions = list(
            set([ep_obj.show.name] + get_scene_exceptions(ep_obj.show.indexerid)))
        for cur_exception in name_exceptions:
            params['q'] = sanitizeSceneName(cur_exception) + save_q
            to_return.append(dict(params))

        return to_return

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        to_return = []
        params = {}
        if not ep_obj:
            return to_return

        params['maxage'] = (datetime.datetime.now() - datetime.datetime.combine(ep_obj.airdate,
                                                                                datetime.datetime.min.time())).days + 1
        params['tvdbid'] = ep_obj.show.indexerid

        if ep_obj.show.air_by_date or ep_obj.show.sports:
            date_str = str(ep_obj.airdate)
            params['season'] = date_str.partition('-')[0]
            params['ep'] = date_str.partition('-')[2].replace('-', '/')
        else:
            params['season'] = ep_obj.scene_season
            params['ep'] = ep_obj.scene_episode

        # add new query strings for exceptions
        name_exceptions = list(
            set([ep_obj.show.name] + get_scene_exceptions(ep_obj.show.indexerid)))
        for cur_exception in name_exceptions:
            params['q'] = sanitizeSceneName(cur_exception)
            if add_string:
                params['q'] += ' ' + add_string

            to_return.append(dict(params))

        return to_return

    def _doGeneralSearch(self, search_string):
        return self.search({'q': search_string})

    def _checkAuth(self):
        return True

    def _checkAuthFromData(self, data):

        """

        :type data: dict
        """
        if not all([x in data for x in ['feed', 'entries']]):
            return self._checkAuth()

        try:
            if int(data['bozo']) == 1:
                raise data['bozo_exception']
        except (AttributeError, KeyError):
            pass

        try:
            err_code = data['feed']['error']['code']
            err_desc = data['feed']['error']['description']

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

    def search(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        self._checkAuth()

        params = {
            "t": "tvsearch",
            "maxage": min(age, sickrage.srCore.srConfig.USENET_RETENTION),
            "limit": 100,
            "offset": 0,
            "cat": self.catIDs.strip(', ') or '5030,5040'
        }.update(search_params)

        if self.key:
            params['apikey'] = self.key

        sickrage.srCore.srLogger.debug('[{}] Search parameters: {}'.format(self.name, repr(params)))

        results = []
        offset = total = 0
        while total >= offset:
            search_url = self.urls['base_url'] + '/api?' + urllib.urlencode(params)

            while (datetime.datetime.now() - self.last_search).seconds < 5:
                time.sleep(1)

            sickrage.srCore.srLogger.debug("Search url: %s" % search_url)

            data = self.cache.getRSSFeed(search_url)

            self.last_search = datetime.datetime.now()

            if not self._checkAuthFromData(data):
                break

            for item in data['entries']:

                (title, url) = self._get_title_and_url(item)

                if title and url:
                    results.append(item)

            # get total and offset attribs
            try:
                if total == 0:
                    total = int(data['feed'].newznab_response['total'] or 0)
                offset = int(data['feed'].newznab_response['offset'] or 0)
            except AttributeError:
                break

            # No items found, prevent from doing another search
            if total == 0:
                break

            if offset != params['offset']:
                sickrage.srCore.srLogger.info("Tell your newznab provider to fix their bloody newznab responses")
                break

            params['offset'] += params['limit']
            if (total > int(params['offset'])) and (offset < 500):
                offset = int(params['offset'])
                # if there are more items available then the amount given in one call, grab some more
                sickrage.srCore.srLogger.debug('%d' % (total - offset) + ' more items to be fetched from provider.' +
                                               'Fetching another %d' % int(params['limit']) + ' items.')
            else:
                sickrage.srCore.srLogger.debug('No more searches needed')
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
            self.show = findCertainShow(sickrage.srCore.SHOWLIST, int(sqlshow["showid"]))
            if self.show:
                curEp = self.show.getEpisode(int(sqlshow["season"]), int(sqlshow["episode"]))
                searchStrings = self._get_episode_search_strings(curEp, add_string='PROPER|REPACK')
                for searchString in searchStrings:
                    for item in self.search(searchString):
                        title, url = self._get_title_and_url(item)
                        if re.match(r'.*(REPACK|PROPER).*', title, re.I):
                            results.append(Proper(title, url, datetime.datetime.today(), self.show))

        return results

    @classmethod
    def getProviders(cls):
        return cls.getDefaultProviders()

    @classmethod
    def getDefaultProviders(cls):
        return [
            cls('NZB.Cat', 'nzb.cat', None, '5030,5040,5010', 'eponly', True, True, True, True),
            cls('NZBGeek', 'api.nzbgeek.info', None, '5030,5040', 'eponly', False, False, False, True),
            cls('NZBs.org', 'nzbs.org', None, '5030,5040', 'eponly', False, False, False, True),
            cls('Usenet-Crawler', 'www.usenet-crawler.com', None, '5030,5040', 'eponly', False, False, False,
                True)
        ]


class TorrentRssCache(TVCache):
    def __init__(self, provider_obj):
        TVCache.__init__(self, provider_obj)
        self.minTime = 15

    def _getRSSData(self):
        sickrage.srCore.srLogger.debug("Cache update URL: %s" % self.provider.url)

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
                  "cat": self.provider.catIDs.strip(',', ''),
                  "maxage": 4,
                  }

        if self.provider.key:
            params['apikey'] = self.provider.key

        rss_url = self.provider.url + 'api?' + urllib.urlencode(params)

        while (datetime.datetime.now() - self.last_search).seconds < 5:
            time.sleep(1)

        sickrage.srCore.srLogger.debug("Cache update URL: %s " % rss_url)
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

        return self._addCacheEntry(title, url, indexer_id=tvrageid)


class providersDict(dict):
    def __init__(self):
        super(providersDict, self).__init__()

        self.filename = os.path.abspath(os.path.join(sickrage.DATA_DIR, 'providers.db'))

        self[NZBProvider.type] = dict([(p.id, p) for p in NZBProvider.getProviders()])
        self[TorrentProvider.type] = dict([(p.id, p) for p in TorrentProvider.getProviders()])
        self[NewznabProvider.type] = dict([(p.id, p) for p in NewznabProvider.getProviders()])
        self[TorrentRssProvider.type] = dict([(p.id, p) for p in TorrentRssProvider.getProviders()])

        self.provider_order = []
        self.sort()

    def sync(self):
        remove = []

        # find
        for p in self.provider_order:
            if p not in self.all():
                remove.append(p)

        # remove
        for r in remove:
            self.provider_order.pop(self.provider_order.index(r))

    def sort(self, key=None, randomize=False):
        sorted_providers = []

        if not key:
            key = self.provider_order or [x.id for x in self.all().values()]

        if randomize:
            random.shuffle(key)

        for p in [self.all()[x] for x in key]:
            (lambda: sorted_providers.append(p), lambda: sorted_providers.insert(0, p))[p.isEnabled]()

        self.provider_order = [x.id for x in sorted_providers]
        return OrderedDict([(x.id, x) for x in sorted_providers])

    def enabled(self):
        return dict([(pID, pObj) for pID, pObj in self.all().items() if pObj.isEnabled])

    def disabled(self):
        return dict([(pID, pObj) for pID, pObj in self.all().items() if not pObj.isEnabled])

    def all(self):
        return reduce(lambda a, b: a.update(b) or a, [
            self.nzb(),
            self.torrent(),
            self.newznab(),
            self.torrentrss()
        ], {})

    def all_nzb(self):
        return reduce(lambda a, b: a.update(b) or a, [
            self.nzb(),
            self.newznab()
        ], {})

    def all_torrent(self):
        return reduce(lambda a, b: a.update(b) or a, [
            self.torrent(),
            self.torrentrss()
        ], {})

    def nzb(self):
        return self[NZBProvider.type]

    def newznab(self):
        return self[NewznabProvider.type]

    def torrent(self):
        return self[TorrentProvider.type]

    def torrentrss(self):
        return self[TorrentRssProvider.type]
