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
from base64 import b16encode, b32decode
from collections import OrderedDict
from time import sleep
from urlparse import urljoin
from xml.sax import SAXParseException

import bencode
import requests
from feedparser import FeedParserDict
from hachoir_core.stream import StringInputStream
from hachoir_parser import guessParser
from pynzb import nzb_parser
from requests.utils import add_dict_to_cookiejar

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.classes import NZBSearchResult, Proper, SearchResult, \
    TorrentSearchResult
from sickrage.core.common import MULTI_EP_RESULT, Quality, SEASON_RESULT, cpu_presets
from sickrage.core.helpers import chmodAsParent, \
    findCertainShow, sanitizeFileName, clean_url, bs4_parser, validate_url, try_int, convert_size
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
        self.supports_backlog = True
        self.supports_absolute_numbering = False
        self.anime_only = False
        self.search_mode = 'eponly'
        self.search_fallback = False
        self.enabled = False
        self.enable_daily = False
        self.enable_backlog = False
        self.cache = TVCache(self)
        self.proper_strings = ['PROPER|REPACK|REAL']
        self.search_separator = ' '

        # cookies
        self.enable_cookies = False
        self.cookies = ''
        self.rss_cookies = ''

    @property
    def id(self):
        return str(re.sub(r"[^\w\d_]", "_", self.name.strip().lower()))

    @property
    def isEnabled(self):
        return self.enabled

    @property
    def imageName(self):
        return ""

    @property
    def seed_ratio(self):
        return ''

    def _check_auth(self):
        return True

    def login(self):
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
        urls = [url]

        bt_cache_urls = [
            'https://torrentproject.se/torrent/{torrent_hash}.torrent',
            'https://btdig.com/torrent/{torrent_hash}.torrent',
            'https://torrage.info/torrent/{torrent_hash}.torrent',
            'https://thetorrent.org/torrent/{torrent_hash}.torrent',
            'https://itorrents.org/torrent/{torrent_hash}.torrent'
        ]

        if url.startswith('magnet'):
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

            urls = [x.format(torrent_hash=torrent_hash, torrent_name=torrent_name) for x in bt_cache_urls]

        random.shuffle(urls)

        return urls

    def make_filename(self, name):
        return ""

    def verify_result(self, result):
        """
        Save the result to disk.
        """

        # check for auth
        if not self.login():
            return False

        urls = self.make_url(result.url)

        for url in urls:
            if 'NO_DOWNLOAD_NAME' in url:
                continue

            headers = {}
            if url.startswith('http'):
                headers.update({
                    'Referer': '/'.join(url.split('/')[:3]) + '/'
                })

            sickrage.srCore.srLogger.info("Verifiying a result from " + self.name + " at " + url)

            result.content = sickrage.srCore.srWebSession.get(url, verify=False, cache=False, headers=headers).content
            if self._verify_content(result):
                if result.resultType == "torrent" and not result.provider.private:
                    # add public trackers to torrent result
                    result = result.provider.add_trackers(result)

                return result

            sickrage.srCore.srLogger.warning("Failed to verify result: %s" % url)

        result.content = None

        return result

    def _verify_content(self, result):
        """
        Checks the saved file to see if it was actually valid, if not then consider the download a failure.
        """

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

    def search(self, search_params, age=0, ep_obj=None):
        return []

    def _get_season_search_strings(self, episode):
        """
        Get season search strings.
        """
        search_string = {
            'Season': []
        }

        for show_name in allPossibleShowNames(episode.show, episode.scene_season):
            episode_string = show_name + ' '

            if episode.show.air_by_date or episode.show.sports:
                episode_string += str(episode.airdate).split('-')[0]
            elif episode.show.anime:
                episode_string += 'Season'
            else:
                episode_string += 'S{season:0>2}'.format(season=episode.scene_season)

            search_string['Season'].append(episode_string.strip())

        return [search_string]

    def _get_episode_search_strings(self, episode, add_string=''):
        """
        Get episode search strings.
        """
        if not episode:
            return []

        search_string = {
            'Episode': []
        }

        for show_name in allPossibleShowNames(episode.show, episode.scene_season):
            episode_string = show_name + self.search_separator
            episode_string_fallback = None

            if episode.show.air_by_date:
                episode_string += str(episode.airdate).replace('-', ' ')
            elif episode.show.sports:
                episode_string += str(episode.airdate).replace('-', ' ')
                episode_string += ('|', ' ')[len(self.proper_strings) > 1]
                episode_string += episode.airdate.strftime('%b')
            elif episode.show.anime:
                # If the showname is a season scene exception, we want to use the indexer episode number.
                if (episode.scene_season > 1 and
                            show_name in get_scene_exceptions(episode.show.indexerid, episode.scene_season)):
                    # This is apparently a season exception, let's use the scene_episode instead of absolute
                    ep = episode.scene_episode
                else:
                    ep = episode.scene_absolute_number
                episode_string_fallback = episode_string + '{episode:0>3}'.format(episode=ep)
                episode_string += '{episode:0>2}'.format(episode=ep)
            else:
                episode_string += sickrage.srCore.srConfig.NAMING_EP_TYPE[2] % {
                    'seasonnumber': episode.scene_season,
                    'episodenumber': episode.scene_episode,
                }

            if add_string:
                episode_string += self.search_separator + add_string
                if episode_string_fallback:
                    episode_string_fallback += self.search_separator + add_string

            search_string['Episode'].append(episode_string.strip())
            if episode_string_fallback:
                search_string['Episode'].append(episode_string_fallback.strip())

        return [search_string]

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
        if not self._check_auth:
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
                    itemList += self.search(curString, ep_obj=epObj)
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
                    dbData = [x['doc'] for x in
                              sickrage.srCore.mainDB.db.get_many('tv_episodes', showObj.indexerid, with_doc=True)
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
                results[epNum] += [result]

        return results

    def find_propers(self, search_date=None):
        results = self.cache.list_propers(search_date)

        return [Proper(x['name'], x['url'], datetime.datetime.fromtimestamp(x['time']), self.show) for x in
                results]

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
        return [v for v in members.values() if hasattr(v, 'type') and v.type == type][0](*args, **kwargs)


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
        if os.path.isfile(
                os.path.join(sickrage.srCore.srConfig.GUI_STATIC_DIR, 'images', 'providers', self.id + '.png')):
            return self.id + '.png'
        return self.type + '.png'

    @property
    def seed_ratio(self):
        """
        Provider should override this value if custom seed ratio enabled
        It should return the value of the provider seed ratio
        """
        return self.ratio

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
                resp = sickrage.srCore.srWebSession.get(url)
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
                resp = sickrage.srCore.srWebSession.get(url)
                torrent = bencode.bdecode(resp.content)

                for file in torrent['info']['files']:
                    files[file['path'][0]] = int(file['length'])
            except Exception:
                pass

        return files

    @staticmethod
    def _clean_title_from_provider(title):
        return (title or '').replace(' ', '.')

    def make_url(self, url):
        return super(TorrentProvider, self).make_url(url)

    def make_filename(self, name):
        return os.path.join(sickrage.srCore.srConfig.TORRENT_DIR,
                            '{}.torrent'.format(sanitizeFileName(name)))

    def _verify_content(self, result):
        """
        Checks the saved file to see if it was actually valid, if not then consider the download a failure.
        """

        try:
            parser = guessParser(StringInputStream(result.content))
            if parser and parser._getMimeType() == 'application/x-bittorrent':
                return True
        except Exception as e:
            sickrage.srCore.srLogger.debug("Failed to verify torrent result: {}".format(e.message))

        sickrage.srCore.srLogger.debug("Invalid torrent result")

    def add_trackers(self, result):
        """
        Adds public trackers to either torrent file or magnet link
        :param result: provider result
        :return: result
        """

        try:
            trackers_list = sickrage.srCore.srWebSession.get('https://cdn.sickrage.ca/torrent_trackers/').text.split()
        except Exception:
            trackers_list = []

        if trackers_list:
            if result.url.startswith('magnet:'):
                result.url += '&tr='.join(trackers_list)
            elif result.content:
                decoded_data = bencode.bdecode(result.content)
                for tracker in trackers_list:
                    if tracker not in decoded_data['announce-list']:
                        decoded_data['announce-list'].append([str(tracker)])
                result.content = bencode.bencode(decoded_data)

        return result

    def find_propers(self, search_date=datetime.datetime.today()):
        results = []

        for show in [s['doc'] for s in sickrage.srCore.mainDB.db.all('tv_shows', with_doc=True)]:
            for episode in [e['doc'] for e in
                            sickrage.srCore.mainDB.db.get_many('tv_episodes', show['indexer_id'], with_doc=True)]:
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
        if os.path.isfile(
                os.path.join(sickrage.srCore.srConfig.GUI_STATIC_DIR, 'images', 'providers', self.id + '.png')):
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
            resp = sickrage.srCore.srWebSession.get(url)

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
            resp = sickrage.srCore.srWebSession.get(url)

            for file in nzb_parser.parse(resp.content):
                total_length = 0
                for segment in file.segments:
                    total_length += int(segment.bytes)

                files[file.subject] = total_length
        except Exception:
            pass

        return files

    def make_url(self, url):
        return super(NZBProvider, self).make_url(url)

    def make_filename(self, name):
        return os.path.join(sickrage.srCore.srConfig.NZB_DIR,
                            '{}.nzb'.format(sanitizeFileName(name)))

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
                 default=False, ):
        super(TorrentRssProvider, self).__init__(name, clean_url(url), False)

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
        dumpName = os.path.join(sickrage.CACHE_DIR, 'custom_torrent.html')

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
                        providers += [TorrentRssProvider(cur_name, cur_url, cur_cookies, cur_title_tag)]
                except Exception:
                    continue
        except Exception:
            pass

        return providers

    @classmethod
    def getDefaultProviders(cls):
        return [
            cls('showRSS', 'showrss.info', '', 'title', 'eponly', False, False, False, True)
        ]


class NewznabProvider(NZBProvider):
    type = 'newznab'

    def __init__(self, name, url, key='0', catIDs='5030,5040', search_mode='eponly', search_fallback=False,
                 enable_daily=False, enable_backlog=False, default=False):
        super(NewznabProvider, self).__init__(name, clean_url(url), bool(key != '0'))

        self.key = key

        self.search_mode = search_mode
        self.search_fallback = search_fallback
        self.enable_daily = enable_daily
        self.enable_backlog = enable_backlog

        self.catIDs = catIDs
        self.default = default

        self.caps = False
        self.cap_tv_search = None
        self.force_query = False

        self.cache = TVCache(self, min_time=30)

    def set_caps(self, data):
        """
        Set caps.
        """
        if not data:
            return

        def _parse_cap(tag):
            elm = data.find(tag)
            return elm.get('supportedparams', 'True') if elm and elm.get('available') else ''

        self.cap_tv_search = _parse_cap('tv-search')
        # self.cap_search = _parse_cap('search')
        # self.cap_movie_search = _parse_cap('movie-search')
        # self.cap_audio_search = _parse_cap('audio-search')

        # self.caps = any([self.cap_tv_search, self.cap_search, self.cap_movie_search, self.cap_audio_search])
        self.caps = any([self.cap_tv_search])

    def get_newznab_categories(self, just_caps=False):
        """
        Use the newznab provider url and apikey to get the capabilities.

        Makes use of the default newznab caps param. e.a. http://yournewznab/api?t=caps&apikey=skdfiw7823sdkdsfjsfk
        Returns a tuple with (succes or not, array with dicts [{'id': '5070', 'name': 'Anime'},
        {'id': '5080', 'name': 'Documentary'}, {'id': '5020', 'name': 'Foreign'}...etc}], error message)
        """
        return_categories = []

        if not self._check_auth():
            return False, return_categories, 'Provider requires auth and your key is not set'

        url_params = {'t': 'caps'}
        if self.private and self.key:
            url_params['apikey'] = self.key

        try:
            response = sickrage.srCore.srWebSession.get(urljoin(self.urls['base_url'], 'api'), params=url_params).text
        except Exception:
            error_string = 'Error getting caps xml for [{}]'.format(self.name)
            sickrage.srCore.srLogger.warning(error_string)
            return False, return_categories, error_string

        with bs4_parser(response) as html:
            if not html.find('categories'):
                error_string = 'Error parsing caps xml for [{}]'.format(self.name)
                sickrage.srCore.srLogger.debug(error_string)
                return False, return_categories, error_string

            self.set_caps(html.find('searching'))
            if just_caps:
                return

            for category in html('category'):
                if 'TV' in category.get('name', '') and category.get('id', ''):
                    return_categories.append({'id': category['id'], 'name': category['name']})
                    for subcat in category('subcat'):
                        if subcat.get('name', '') and subcat.get('id', ''):
                            return_categories.append({'id': subcat['id'], 'name': subcat['name']})

            return True, return_categories, ''

    def _doGeneralSearch(self, search_string):
        return self.search({'q': search_string})

    def _check_auth(self):
        if self.private and not self.key:
            sickrage.srCore.srLogger.warning('Invalid api key for {}. Check your settings'.format(self.name))
            return False

        return True

    def _check_auth_from_data(self, data):
        """
        Check that the returned data is valid.

        :return: _check_auth if valid otherwise False if there is an error
        """
        if data('categories') + data('item'):
            return self._check_auth()

        try:
            err_desc = data.error.attrs['description']
            if not err_desc:
                raise Exception
        except (AttributeError, TypeError):
            return self._check_auth()

        sickrage.srCore.srLogger.info(err_desc)

        return False

    def search(self, search_strings, age=0, ep_obj=None):
        """
        Search indexer using the params in search_strings, either for latest releases, or a string/id search.

        :return: list of results in dict form
        """
        results = []

        if not self._check_auth():
            return results

        # For providers that don't have caps, or for which the t=caps is not working.
        if not self.caps:
            self.get_newznab_categories(just_caps=True)
            if not self.caps:
                return results

        for mode in search_strings:
            self.torznab = False
            search_params = {
                't': 'search',
                'limit': 100,
                'offset': 0,
                'cat': self.catIDs.strip(', ') or '5030,5040',
                'maxage': sickrage.srCore.srConfig.USENET_RETENTION
            }

            if self.private and self.key:
                search_params['apikey'] = self.key

            if mode != 'RSS':
                if (self.cap_tv_search or not self.cap_tv_search == 'True') and not self.force_query:
                    search_params['t'] = 'tvsearch'
                    search_params.update({'tvdbid': self.show.indexerid})

                if search_params['t'] == 'tvsearch':
                    if ep_obj.show.air_by_date or ep_obj.show.sports:
                        date_str = str(ep_obj.airdate)
                        search_params['season'] = date_str.partition('-')[0]
                        search_params['ep'] = date_str.partition('-')[2].replace('-', '/')
                    else:
                        search_params['season'] = ep_obj.scene_season
                        search_params['ep'] = ep_obj.scene_episode

                if mode == 'Season':
                    search_params.pop('ep', '')

            sickrage.srCore.srLogger.debug('Search mode: {0}'.format(mode))

            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    # If its a PROPER search, need to change param to 'search' so it searches using 'q' param
                    if any(proper_string in search_string for proper_string in self.proper_strings):
                        search_params['t'] = 'search'

                    sickrage.srCore.srLogger.debug("Search string: {}".format(search_string))

                    if search_params['t'] != 'tvsearch':
                        search_params['q'] = search_string

                sleep(cpu_presets[sickrage.srCore.srConfig.CPU_PRESET])

                try:
                    response = sickrage.srCore.srWebSession.get(urljoin(self.urls['base_url'], 'api'),
                                                                params=search_params).text
                except Exception:
                    sickrage.srCore.srLogger.debug('No data returned from provider')
                    continue

                with bs4_parser(response) as html:
                    if not self._check_auth_from_data(html):
                        return results

                    try:
                        self.torznab = 'xmlns:torznab' in html.rss.attrs
                    except AttributeError:
                        self.torznab = False

                    if not html('item'):
                        sickrage.srCore.srLogger.debug('No results returned from provider. Check chosen Newznab '
                                                       'search categories in provider settings and/or usenet '
                                                       'retention')
                        continue

                    for item in html('item'):
                        try:
                            title = item.title.get_text(strip=True)
                            download_url = None
                            if item.link:
                                if validate_url(item.link.get_text(strip=True)):
                                    download_url = item.link.get_text(strip=True)
                                elif validate_url(item.link.next.strip()):
                                    download_url = item.link.next.strip()

                            if not download_url and item.enclosure:
                                if validate_url(item.enclosure.get('url', '').strip()):
                                    download_url = item.enclosure.get('url', '').strip()

                            if not (title and download_url):
                                continue

                            seeders = leechers = -1
                            if 'gingadaddy' in self.urls['base_url']:
                                size_regex = re.search(r'\d*.?\d* [KMGT]B', str(item.description))
                                item_size = size_regex.group() if size_regex else -1
                            else:
                                item_size = item.size.get_text(strip=True) if item.size else -1
                                for attr in item('newznab:attr') + item('torznab:attr'):
                                    item_size = attr['value'] if attr['name'] == 'size' else item_size
                                    seeders = try_int(attr['value']) if attr['name'] == 'seeders' else seeders
                                    peers = try_int(attr['value']) if attr['name'] == 'peers' else None
                                    leechers = peers - seeders if peers else leechers

                            if not item_size or (self.torznab and (seeders is -1 or leechers is -1)):
                                continue

                            size = convert_size(item_size, -1)

                            item = {
                                'title': title,
                                'link': download_url,
                                'size': size,
                                'seeders': seeders,
                                'leechers': leechers,
                            }
                            if mode != 'RSS':
                                sickrage.srCore.srLogger.debug('Found result: {0}'.format(title))

                            results.append(item)
                        except (AttributeError, TypeError, KeyError, ValueError, IndexError):
                            sickrage.srCore.srLogger.error('Failed parsing provider')
                            continue

                # Since we arent using the search string,
                # break out of the search string loop
                if 'tvdbid' in search_params:
                    break

        # Reproces but now use force_query = True
        if not results and not self.force_query:
            self.force_query = True
            return self.search(search_strings, ep_obj=ep_obj)

        return results

    def find_propers(self, search_date=datetime.datetime.today()):
        results = []

        for show in [s['doc'] for s in sickrage.srCore.mainDB.db.all('tv_shows', with_doc=True)]:
            for episode in [e['doc'] for e in
                            sickrage.srCore.mainDB.db.get_many('tv_episodes', show['indexer_id'], with_doc=True)]:
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
                        cur_url = clean_url(cur_url)

                        provider = NewznabProvider(
                            cur_name,
                            cur_url,
                            cur_key,
                            cur_cat
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
            cls('DOGnzb', 'https://api.dognzb.cr', '', '5030,5040,5060,5070', 'eponly', False, False, False, True),
            cls('NZB.Cat', 'http://nzb.cat', '', '5030,5040,5010', 'eponly', True, True, True, True),
            cls('NZBGeek', 'http://api.nzbgeek.info', '', '5030,5040', 'eponly', False, False, False, True),
            cls('NZBs.org', 'http://nzbs.org', '', '5030,5040', 'eponly', False, False, False, True),
            cls('Usenet-Crawler', 'http://usenet-crawler.com', '', '5030,5040', 'eponly', False, False, False, True)
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
