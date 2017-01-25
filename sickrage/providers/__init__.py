# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
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
from collections import OrderedDict
from xml.sax import SAXParseException

import bencode
import requests
import xmltodict
from feedparser import FeedParserDict
from hachoir_core.stream import StringInputStream
from hachoir_parser import guessParser
from pynzb import nzb_parser
from requests.utils import add_dict_to_cookiejar

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.classes import NZBSearchResult, Proper, SearchResult, \
    TorrentSearchResult
from sickrage.core.common import MULTI_EP_RESULT, Quality, SEASON_RESULT
from sickrage.core.exceptions import AuthException
from sickrage.core.helpers import chmodAsParent, \
    findCertainShow, remove_file_failed, \
    sanitizeFileName, sanitizeSceneName
from sickrage.core.helpers.show_names import allPossibleShowNames
from sickrage.core.nameparser import InvalidNameException, InvalidShowException, \
    NameParser
from sickrage.core.scene_exceptions import get_scene_exceptions


class GenericProvider(object):
    def __init__(self, name, url, private):
        self.name = name
        self.urls = {'base_url': url}
        self.private = private
        self.show = None
        self.supports_backlog = False
        self.supports_absolute_numbering = False
        self.anime_only = False
        self.search_mode = 'eponly'
        self.search_fallback = False
        self.enabled = False
        self.enable_daily = False
        self.enable_backlog = False
        self.cache = TVCache(self)
        self.proper_strings = ['PROPER|REPACK|REAL']

        self.enable_cookies = False
        self.cookies = ''
        self.rss_cookies = ''
        self.cookie_jar = dict()

    @property
    def id(self):
        return str(re.sub(r"[^\w\d_]", "_", self.name.strip().lower()))

    @property
    def isEnabled(self):
        return self.enabled

    @property
    def imageName(self):
        return ""

    def check_auth(self):
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
        return SearchResult(episodes)

    def make_url(self, url):
        urls = []

        btcache_urls = [
            'http://torrentproject.se/torrent/{torrent_hash}.torrent',
            'http://btdig.com/torrent/{torrent_hash}.torrent',
            'http://torrage.info/torrent/{torrent_hash}.torrent',
            'http://thetorrent.org/torrent/{torrent_hash}.torrent',
            'http://itorrents.org/torrent/{torrent_hash}.torrent'
        ]

        if url.startswith('magnet'):
            try:
                torrent_hash = str(re.findall(r'urn:btih:([\w]{32,40})', url)[0]).upper()

                try:
                    torrent_name = re.findall('dn=([^&]+)', url)[0]
                except Exception:
                    torrent_name = 'NO_DOWNLOAD_NAME'

                if len(torrent_hash) == 32:
                    torrent_hash = b16encode(b32decode(torrent_hash)).upper()

                if not torrent_hash:
                    sickrage.srCore.srLogger.error("Unable to extract torrent hash from magnet: " + url)
                    return urls

                urls = [x.format(torrent_hash=torrent_hash, torrent_name=torrent_name) for x in btcache_urls]
            except Exception:
                sickrage.srCore.srLogger.error("Unable to extract torrent hash or name from magnet: " + url)
                return urls
        else:
            urls = [url]

        random.shuffle(urls)
        return urls

    def make_filename(self, name):
        return ""

    def downloadResult(self, result):
        """
        Save the result to disk.
        """

        # check for auth
        if not self._doLogin:
            return False

        urls = self.make_url(result.url)
        filename = self.make_filename(result.name)

        for url in urls:
            if 'NO_DOWNLOAD_NAME' in url:
                continue

            sickrage.srCore.srLogger.info("Downloading a result from " + self.name + " at " + url)

            # Support for Jackett/TorzNab
            if url.endswith('torrent') and filename.endswith('nzb'):
                filename = filename.rsplit('.', 1)[0] + '.' + 'torrent'

            if sickrage.srCore.srWebSession.download(url,
                                                     filename,
                                                     headers=(None, {
                                                         'Referer': '/'.join(url.split('/')[:3]) + '/'
                                                     })[url.startswith('http')]):

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
        sickrage.srCore.srLogger.error("Provider type doesn't have ability to provide download size implemented yet")
        return -1

    def _get_files(self, url):
        """Gets dict of files with sizes from the item"""
        sickrage.srCore.srLogger.error("Provider type doesn't have _get_files() implemented yet")
        return {}

    def findSearchResults(self, show, episodes, search_mode, manualSearch=False, downCurQuality=False, cacheOnly=False):

        if not self.check_auth:
            return

        self.show = show

        results = {}
        itemList = []

        searched_scene_season = None
        for epObj in episodes:
            # search cache for episode result
            cacheResult = self.cache.search_cache(epObj, manualSearch, downCurQuality)
            if cacheResult:
                if epObj.episode not in results:
                    results[epObj.episode] = cacheResult[epObj.episode]
                else:
                    results[epObj.episode].extend(cacheResult[epObj.episode])

                # found result, search next episode
                continue

            # skip if season already searched
            if len(episodes) > 1 and search_mode == 'sponly' and searched_scene_season == epObj.scene_season:
                continue

            # mark season searched for season pack searches so we can skip later on
            searched_scene_season = epObj.scene_season

            # check if this is a cache only search
            if cacheOnly:
                continue

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
                try:
                    itemList += self.search(curString, search_mode, len(episodes), epObj=epObj)
                except SAXParseException:
                    continue

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
                    dbData = [x['doc'] for x in sickrage.srCore.mainDB.db.get_many('tv_episodes', showObj.indexerid, with_doc=True)
                              if x['doc']['airdate'] == airdate]

                    if len(dbData) != 1:
                        sickrage.srCore.srLogger.warning(
                            "Tried to look up the date for the episode " + title + " but the database didn't give proper results, skipping it")
                        addCacheEntry = True

                if not addCacheEntry:
                    actual_season = int(dbData[0]["season"])
                    actual_episodes = [int(dbData[0]["episode"])]

            # add parsed result to cache for usage later on
            if addCacheEntry:
                sickrage.srCore.srLogger.debug("Adding item from search to cache: " + title)
                self.cache.addCacheEntry(title, url, parse_result=parse_result)
                continue

            # make sure we want the episode
            wantEp = True
            for epNo in actual_episodes:
                if not showObj.wantEpisode(actual_season, epNo, quality, manualSearch, downCurQuality):
                    wantEp = False
                    break

            if not wantEp:
                sickrage.srCore.srLogger.info(
                    "RESULT:[{}] QUALITY:[{}] IGNORED!".format(title, Quality.qualityStrings[quality]))
                continue

            # make a result object
            epObjs = []
            for curEp in actual_episodes:
                epObjs.append(showObj.getEpisode(actual_season, curEp))

            result = self.getResult(epObjs)
            result.show = showObj
            result.url = url
            result.name = title
            result.quality = quality
            result.release_group = release_group
            result.version = version
            result.content = None
            result.size = self._get_size(url)
            result.files = self._get_files(url)

            sickrage.srCore.srLogger.debug(
                "FOUND RESULT:[{}] QUALITY:[{}] URL:[{}]".format(title, Quality.qualityStrings[quality], url))

            if len(epObjs) == 1:
                epNum = epObjs[0].episode
                sickrage.srCore.srLogger.debug("Single episode result.")
            elif len(epObjs) > 1:
                epNum = MULTI_EP_RESULT
                sickrage.srCore.srLogger.debug(
                    "Separating multi-episode result to check for later - result contains episodes: " + str(
                        parse_result.episode_numbers))
            elif len(epObjs) == 0:
                epNum = SEASON_RESULT
                sickrage.srCore.srLogger.debug("Separating full season result to check for later")

            if epNum not in results:
                results[epNum] = [result]
            else:
                results[epNum].append(result)

        return results

    def find_propers(self, search_date=None):

        results = self.cache.list_propers(search_date)

        return [Proper(x['name'], x['url'], datetime.datetime.fromtimestamp(x['time']), self.show) for x in
                results]

    def seed_ratio(self):
        '''
        Provider should override this value if custom seed ratio enabled
        It should return the value of the provider seed ratio
        '''
        return ''

    def add_cookies_from_ui(self):
        """
        Adds the cookies configured from UI to the providers requests session
        :return: A tuple with the the (success result, and a descriptive message in str)
        """

        # This is the generic attribute used to manually add cookies for provider authentication
        if self.enable_cookies and self.cookies:
            cookie_validator = re.compile(r'^(\w+=\w+)(;\w+=\w+)*$')
            if cookie_validator.match(self.cookies):
                add_dict_to_cookiejar(sickrage.srCore.srWebSession.cookies,
                                      dict(x.rsplit('=', 1) for x in self.cookies.split(';')))
                return True

        return False

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

    def __init__(self, name, url, private):
        super(TorrentProvider, self).__init__(name, url, private)
        self.ratio = None

    @property
    def isActive(self):
        return sickrage.srCore.srConfig.USE_TORRENTS and self.isEnabled

    @property
    def imageName(self):
        if os.path.isfile(os.path.join(sickrage.srCore.srConfig.GUI_DIR, 'images', 'providers', self.id + '.png')):
            return self.id + '.png'
        return self.type + '.png'

    def getResult(self, episodes):
        """
        Returns a result of the correct type for this provider
        """
        result = TorrentSearchResult(episodes)
        result.provider = self
        return result

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

    def _get_size(self, url):
        size = -1

        for url in self.make_url(url):
            try:
                resp = sickrage.srCore.srWebSession.get(url, raise_exceptions=False)
                torrent = bencode.bdecode(resp.content)

                total_length = 0
                for file in torrent['info']['files']:
                    total_length += int(file['length'])

                if total_length > 0:
                    size = total_length
                    break
            except Exception:
                pass

        return size

    def _get_files(self, url):
        files = {}

        for url in self.make_url(url):
            try:
                resp = sickrage.srCore.srWebSession.get(url, raise_exceptions=False)
                torrent = bencode.bdecode(resp.content)

                for file in torrent['info']['files']:
                    files[file['path'][0]] = int(file['length'])
            except Exception:
                pass

        return files

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
                ep_string += ' %s' % add_string

            search_string['Episode'].append(ep_string.strip())

        return [search_string]

    @staticmethod
    def _clean_title_from_provider(title):
        return (title or '').replace(' ', '.')

    def make_url(self, url):
        return super(TorrentProvider, self).make_url(url)

    def make_filename(self, name):
        return os.path.join(sickrage.srCore.srConfig.TORRENT_DIR,
                            '{}.{}'.format(sanitizeFileName(name), self.type))

    def find_propers(self, search_date=datetime.datetime.today()):
        results = []

        for show in [s['doc'] for s in sickrage.srCore.mainDB.db.all('tv_shows', with_doc=True)]:
            for episode in [e['doc'] for e in sickrage.srCore.mainDB.db.get_many('tv_episodes', show['indexer_id'], with_doc=True)]:
                if episode['airdate'] >= str(search_date.toordinal()) \
                        and episode['status'] in Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_BEST:

                    self.show = findCertainShow(sickrage.srCore.SHOWLIST, int(episode["showid"]))
                    if not show: continue

                    curEp = show.getEpisode(int(episode["season"]), int(episode["episode"]))
                    for term in self.proper_strings:
                        searchString = self._get_episode_search_strings(curEp, add_string=term)
                        for item in self.search(searchString[0]):
                            title, url = self._get_title_and_url(item)
                            results.append(Proper(title, url, datetime.datetime.today(), self.show))

        return results

    def seed_ratio(self):
        return self.ratio

    @classmethod
    def getProviders(cls):
        return super(TorrentProvider, cls).loadProviders(cls.type)


class NZBProvider(GenericProvider):
    type = 'nzb'

    def __init__(self, name, url, private):
        super(NZBProvider, self).__init__(name, url, private)
        self.api_key = ''
        self.username = ''

    @property
    def isActive(self):
        return sickrage.srCore.srConfig.USE_NZBS and self.isEnabled

    @property
    def imageName(self):
        if os.path.isfile(os.path.join(sickrage.srCore.srConfig.GUI_DIR, 'images', 'providers', self.id + '.png')):
            return self.id + '.png'
        return self.type + '.png'

    def getResult(self, episodes):
        """
        Returns a result of the correct type for this provider
        """
        result = NZBSearchResult(episodes)
        result.provider = self
        return result

    def _get_size(self, url):
        size = -1

        try:
            resp = sickrage.srCore.srWebSession.get(url, raise_exceptions=False)

            total_length = 0
            for file in nzb_parser.parse(resp.content):
                for segment in file.segments:
                    total_length += int(segment.bytes)

            if total_length > 0:
                size = total_length
        except Exception:
            pass

        return size

    def _get_files(self, url):
        files = {}

        try:
            resp = sickrage.srCore.srWebSession.get(url, raise_exceptions=False)

            for file in nzb_parser.parse(resp.content):
                total_length = 0
                for segment in file.segments:
                    total_length += int(segment.bytes)

                files[files.subject] = total_length
        except Exception:
            pass

        return files

    def make_url(self, url):
        return super(NZBProvider, self).make_url(url)

    def make_filename(self, name):
        return os.path.join(sickrage.srCore.srConfig.NZB_DIR,
                            '{}.{}'.format(sanitizeFileName(name), self.type))

    @classmethod
    def getProviders(cls):
        return super(NZBProvider, cls).loadProviders(cls.type)


class TorrentRssProvider(TorrentProvider):
    type = 'torrentrss'

    def __init__(self,
                 name,
                 url,
                 private,
                 cookies='',
                 titleTAG='title',
                 search_mode='eponly',
                 search_fallback=False,
                 enable_daily=False,
                 enable_backlog=False,
                 default=False, ):
        super(TorrentRssProvider, self).__init__(name, url, private)

        self.cache = TorrentRssCache(self)
        self.supports_backlog = False

        self.search_mode = search_mode
        self.search_fallback = search_fallback
        self.enable_daily = enable_daily
        self.enable_backlog = enable_backlog
        self.enable_cookies = True
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

            data = self.cache._get_rss_data()['entries']
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

    @classmethod
    def getProviders(cls):
        providers = cls.getDefaultProviders()

        try:
            for curProviderStr in sickrage.srCore.srConfig.CUSTOM_PROVIDERS.split('!!!'):
                if not len(curProviderStr):
                    continue

                try:
                    cur_type, curProviderData = curProviderStr.split('|', 1)
                    if cur_type == "torrentrss":
                        cur_name, cur_url, cur_cookies, cur_title_tag = curProviderData.split('|')
                        cur_url = sickrage.srCore.srConfig.clean_url(cur_url)

                        providers += [TorrentRssProvider(cur_name, cur_url, False, cur_cookies, cur_title_tag)]
                except Exception:
                    continue
        except Exception:
            pass

        return providers

    @classmethod
    def getDefaultProviders(cls):
        return [
            cls('showRSS', 'showrss.info', False, '', 'title', 'eponly', False, False, False, True)
        ]


class NewznabProvider(NZBProvider):
    type = 'newznab'

    def __init__(self,
                 name,
                 url,
                 private,
                 key='',
                 catIDs='5030,5040',
                 search_mode='eponly',
                 search_fallback=False,
                 enable_daily=False,
                 enable_backlog=False,
                 default=False):
        super(NewznabProvider, self).__init__(name, url, private)

        self.key = key

        self.search_mode = search_mode
        self.search_fallback = search_fallback
        self.enable_daily = enable_daily
        self.enable_backlog = enable_backlog
        self.supports_backlog = True

        self.catIDs = catIDs
        self.default = default

        self.cache = TVCache(self, min_time=30)

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

        self.check_auth()

        params = {"t": "caps"}
        if self.key:
            params['apikey'] = self.key

        try:
            resp = sickrage.srCore.srWebSession.get("{}api?{}".format(self.urls['base_url'], urllib.urlencode(params)))
            data = xmltodict.parse(resp.content)

            for category in data["caps"]["categories"]["category"]:
                if category.get('@name') == 'TV':
                    categories += [{"id": category['@id'], "name": category['@name']}]
                    categories += [{"id": x["@id"], "name": x["@name"]} for x in category["subcat"]]

            success = True
        except Exception as e:
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

    def check_auth(self):
        if self.private and not len(self.key):
            sickrage.srCore.srLogger.warning('Invalid api key for {}. Check your settings'.format(self.name))
            return False

        return True

    def _checkAuthFromData(self, data):

        """

        :type data: dict
        """
        if all([x in data for x in ['feed', 'entries']]):
            return self.check_auth()

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
            raise Exception("Error {}: {}".format(err_code, err_desc))
        except (AttributeError, KeyError):
            pass

        return False

    def search(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):
        results = []

        if not self.check_auth():
            return results

        params = {
            "t": "tvsearch",
            "maxage": min(age, sickrage.srCore.srConfig.USENET_RETENTION),
            "limit": 100,
            "offset": 0,
            "cat": self.catIDs or '5030,5040'
        }

        params.update(search_params)

        if self.key:
            params['apikey'] = self.key

        offset = total = 0
        last_search = datetime.datetime.now()
        while total >= offset:
            if (datetime.datetime.now() - last_search).seconds < 5:
                continue

            search_url = self.urls['base_url'] + '/api'
            sickrage.srCore.srLogger.debug("Search url: %s?%s" % (search_url, urllib.urlencode(params)))

            data = self.cache.getRSSFeed(search_url, params=params)

            last_search = datetime.datetime.now()

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
                break

        return results

    def find_propers(self, search_date=datetime.datetime.today()):
        results = []
        dbData = []

        for show in [s['doc'] for s in sickrage.srCore.mainDB.db.all('tv_shows', with_doc=True)]:
            for episode in [e['doc'] for e in sickrage.srCore.mainDB.db.get_many('tv_episodes', show['indexer_id'], with_doc=True)]:
                if episode['airdate'] >= str(search_date.toordinal()) \
                        and episode['status'] in Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_BEST:

                    self.show = findCertainShow(sickrage.srCore.SHOWLIST, int(show["showid"]))
                    if not self.show: continue

                    curEp = self.show.getEpisode(int(episode["season"]), int(episode["episode"]))
                    searchStrings = self._get_episode_search_strings(curEp, add_string='PROPER|REPACK')
                    for searchString in searchStrings:
                        for item in self.search(searchString):
                            title, url = self._get_title_and_url(item)
                            if re.match(r'.*(REPACK|PROPER).*', title, re.I):
                                results += [Proper(title, url, datetime.datetime.today(), self.show)]

        return results

    @classmethod
    def getProviders(cls):
        providers = cls.getDefaultProviders()

        try:
            for curProviderStr in sickrage.srCore.srConfig.CUSTOM_PROVIDERS.split('!!!'):
                if not len(curProviderStr):
                    continue

                try:
                    cur_type, curProviderData = curProviderStr.split('|', 1)

                    if cur_type == "newznab":
                        cur_name, cur_url, cur_key, cur_cat = curProviderData.split('|')
                        cur_url = sickrage.srCore.srConfig.clean_url(cur_url)

                        provider = NewznabProvider(
                            cur_name,
                            cur_url,
                            bool(not cur_key == 0),
                            key=cur_key,
                            catIDs=cur_cat
                        )

                        providers += [provider]
                except Exception:
                    continue
        except Exception:
            pass

        return providers

    @classmethod
    def getDefaultProviders(cls):
        return [
            cls('SickBeard', 'lolo.sickbeard.com', False, '', '5030,5040', 'eponly', False, False, False, True),
            cls('NZB.Cat', 'nzb.cat', True, '', '5030,5040,5010', 'eponly', True, True, True, True),
            cls('NZBGeek', 'api.nzbgeek.info', True, '', '5030,5040', 'eponly', False, False, False, True),
            cls('NZBs.org', 'nzbs.org', True, '', '5030,5040', 'eponly', False, False, False, True),
            cls('Usenet-Crawler', 'usenet-crawler.com', True, '', '5030,5040', 'eponly', False, False, False, True)
        ]


class TorrentRssCache(TVCache):
    def __init__(self, provider_obj):
        TVCache.__init__(self, provider_obj)
        self.min_time = 15

    def _get_rss_data(self):
        sickrage.srCore.srLogger.debug("Cache update URL: %s" % self.provider.urls['base_url'])

        if self.provider.cookies:
            self.provider.headers.update({'Cookie': self.provider.cookies})

        return self.getRSSFeed(self.provider.urls['base_url'])


class providersDict(dict):
    def __init__(self):
        super(providersDict, self).__init__()

        self.provider_order = []

        self[NZBProvider.type] = {}
        self[TorrentProvider.type] = {}
        self[NewznabProvider.type] = {}
        self[TorrentRssProvider.type] = {}

    def load(self):
        self[NZBProvider.type] = dict([(p.id, p) for p in NZBProvider.getProviders()])
        self[TorrentProvider.type] = dict([(p.id, p) for p in TorrentProvider.getProviders()])
        self[NewznabProvider.type] = dict([(p.id, p) for p in NewznabProvider.getProviders()])
        self[TorrentRssProvider.type] = dict([(p.id, p) for p in TorrentRssProvider.getProviders()])

    def sort(self, key=None, randomize=False):
        sorted_providers = []

        self.provider_order = [x for x in self.provider_order if x in self.all().keys()]
        self.provider_order += [x for x in self.all().keys() if x not in self.provider_order]

        if not key:
            key = self.provider_order

        if randomize:
            random.shuffle(key)

        for p in [self.enabled()[x] for x in key if x in self.enabled()]:
            sorted_providers.append(p)

        for p in [self.disabled()[x] for x in key if x in self.disabled()]:
            sorted_providers.append(p)

        return OrderedDict([(x.id, x) for x in sorted_providers])

    def enabled(self):
        return dict([(pID, pObj) for pID, pObj in self.all().items() if pObj.isEnabled])

    def disabled(self):
        return dict([(pID, pObj) for pID, pObj in self.all().items() if not pObj.isEnabled])

    def all(self):
        return dict(self.nzb().items() + self.torrent().items() + self.newznab().items() + self.torrentrss().items())

    def all_nzb(self):
        return dict(self.nzb().items() + self.newznab().items())

    def all_torrent(self):
        return dict(self.torrent().items() + self.torrentrss().items())

    def nzb(self):
        return self[NZBProvider.type]

    def torrent(self):
        return self[TorrentProvider.type]

    def newznab(self):
        return self[NewznabProvider.type]

    def torrentrss(self):
        return self[TorrentRssProvider.type]
