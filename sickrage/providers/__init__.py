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
from base64 import b16encode, b32decode, b64decode
from collections import OrderedDict, defaultdict
from time import sleep
from urlparse import urljoin
from xml.sax import SAXParseException

import bencode
from feedparser import FeedParserDict
from requests.utils import add_dict_to_cookiejar, dict_from_cookiejar

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.classes import NZBSearchResult, SearchResult, TorrentSearchResult
from sickrage.core.common import MULTI_EP_RESULT, Quality, SEASON_RESULT, cpu_presets
from sickrage.core.helpers import chmodAsParent, findCertainShow, sanitizeFileName, clean_url, bs4_parser, validate_url, \
    try_int, convert_size
from sickrage.core.helpers.show_names import allPossibleShowNames
from sickrage.core.nameparser import InvalidNameException, InvalidShowException, NameParser
from sickrage.core.scene_exceptions import get_scene_exceptions
from sickrage.core.websession import WebSession


class GenericProvider(object):
    def __init__(self, name, url, private):
        self.name = name
        self.urls = {'base_url': url}
        self.private = private
        self.supports_backlog = True
        self.supports_absolute_numbering = False
        self.anime_only = False
        self.search_mode = 'eponly'
        self.search_fallback = False
        self.enabled = False
        self.enable_daily = False
        self.enable_backlog = False
        self.cache = TVCache(self)
        self.proper_strings = ['PROPER|REPACK|REAL|RERIP']
        self.search_separator = ' '

        # cookies
        self.enable_cookies = False
        self.required_cookies = []
        self.cookies = ''

        self.session = WebSession()

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

    @property
    def isAlive(self):
        return True

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

    def getResult(self, episodes=None):
        """
        Returns a result of the correct type for this provider
        """
        return SearchResult(episodes)

    def get_content(self, url):
        if self.login():
            headers = {}
            if url.startswith('http'):
                headers = {'Referer': '/'.join(url.split('/')[:3]) + '/'}

            try:
                return self.session.get(url, verify=False, headers=headers).content
            except Exception:
                pass

    def make_filename(self, name):
        return ""

    def get_quality(self, item, anime=False):
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
                episode_string += sickrage.app.naming_ep_type[2] % {
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
        sickrage.app.log.debug("Provider type doesn't have ability to provide download size implemented yet")
        return -1

    def _get_result_stats(self, item):
        # Get seeders/leechers stats
        seeders = item.get('seeders', -1)
        leechers = item.get('leechers', -1)
        return try_int(seeders, -1), try_int(leechers, -1)

    def findSearchResults(self, show, episodes, search_mode, manualSearch=False, downCurQuality=False, cacheOnly=False):
        results = {}
        itemList = []

        if not self._check_auth:
            return results

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
                sickrage.app.log.debug('First search_string has rid')

            for curString in search_strings:
                try:
                    itemList += self.search(curString, ep_obj=epObj)
                except SAXParseException:
                    continue

                if first:
                    first = False
                    if itemList:
                        sickrage.app.log.debug(
                            'First search_string had rid, and returned results, skipping query by string')
                        break
                    else:
                        sickrage.app.log.debug(
                            'First search_string had rid, but returned no results, searching with string query')

        # if we found what we needed already from cache then return results and exit
        if len(results) == len(episodes):
            return results

        # sort list by quality
        if itemList:
            # categorize the items into lists by quality
            items = defaultdict(list)
            for item in itemList:
                items[self.get_quality(item, anime=show.is_anime)].append(item)

            # temporarily remove the list of items with unknown quality
            unknown_items = items.pop(Quality.UNKNOWN, [])

            # make a generator to sort the remaining items by descending quality
            items_list = (items[quality] for quality in sorted(items, reverse=True))

            # unpack all of the quality lists into a single sorted list
            items_list = list(itertools.chain(*items_list))

            # extend the list with the unknown qualities, now sorted at the bottom of the list
            items_list.extend(unknown_items)

        # filter results
        for item in itemList:
            result = self.getResult()

            result.name, result.url = self._get_title_and_url(item)

            # ignore invalid urls
            if not validate_url(result.url) and not result.url.startswith('magnet'):
                continue

            try:
                parse_result = NameParser().parse(result.name)
            except (InvalidNameException, InvalidShowException) as e:
                sickrage.app.log.debug("{}".format(e))
                continue

            result.show = parse_result.show
            result.quality = parse_result.quality
            result.release_group = parse_result.release_group
            result.version = parse_result.version
            result.size = self._get_size(item)
            result.seeders, result.leechers = self._get_result_stats(item)

            sickrage.app.log.debug("Adding item from search to cache: " + result.name)
            self.cache.addCacheEntry(result.name, result.url, result.seeders, result.leechers, result.size)

            if not result.show:
                continue

            if not (result.show.air_by_date or result.show.sports):
                if search_mode == 'sponly':
                    if len(parse_result.episode_numbers):
                        sickrage.app.log.debug(
                            "This is supposed to be a season pack search but the result " + result.name + " is not a valid season pack, skipping it")
                        continue
                    if len(parse_result.episode_numbers) and (
                            parse_result.season_number not in set([ep.season for ep in episodes])
                            or not [ep for ep in episodes if ep.scene_episode in parse_result.episode_numbers]):
                        sickrage.app.log.debug(
                            "The result " + result.name + " doesn't seem to be a valid episode that we are trying to snatch, ignoring")
                        continue
                else:
                    if not len(parse_result.episode_numbers) and parse_result.season_number and not [ep for ep in
                                                                                                     episodes if
                                                                                                     ep.season == parse_result.season_number and ep.episode in parse_result.episode_numbers]:
                        sickrage.app.log.debug(
                            "The result " + result.name + " doesn't seem to be a valid season that we are trying to snatch, ignoring")
                        continue
                    elif len(parse_result.episode_numbers) and not [ep for ep in episodes if
                                                                    ep.season == parse_result.season_number and ep.episode in parse_result.episode_numbers]:
                        sickrage.app.log.debug(
                            "The result " + result.name + " doesn't seem to be a valid episode that we are trying to snatch, ignoring")
                        continue

                # we just use the existing info for normal searches
                actual_season = parse_result.season_number
                actual_episodes = parse_result.episode_numbers
            else:
                if not parse_result.is_air_by_date:
                    sickrage.app.log.debug(
                        "This is supposed to be a date search but the result " + result.name + " didn't parse as one, skipping it")
                    continue
                else:
                    airdate = parse_result.air_date.toordinal()
                    dbData = [x for x in sickrage.app.main_db.get_many('tv_episodes', result.show.indexerid)
                              if x['airdate'] == airdate]

                    if len(dbData) != 1:
                        sickrage.app.log.warning(
                            "Tried to look up the date for the episode " + result.name + " but the database didn't give proper results, skipping it")
                        continue

                    actual_season = int(dbData[0]["season"])
                    actual_episodes = [int(dbData[0]["episode"])]

            # make sure we want the episode
            wantEp = False
            for epNo in actual_episodes:
                if result.show.wantEpisode(actual_season, epNo, result.quality, manualSearch, downCurQuality):
                    wantEp = True

            if not wantEp:
                sickrage.app.log.info(
                    "RESULT:[{}] QUALITY:[{}] IGNORED!".format(result.name, Quality.qualityStrings[result.quality]))
                continue

            # make a result object
            result.episodes = []
            for curEp in actual_episodes:
                result.episodes.append(result.show.getEpisode(actual_season, curEp))

            sickrage.app.log.debug(
                "FOUND RESULT:[{}] QUALITY:[{}] URL:[{}]".format(result.name, Quality.qualityStrings[result.quality],
                                                                 result.url))

            if len(result.episodes) == 1:
                epNum = result.episodes[0].episode
                sickrage.app.log.debug("Single episode result.")
            elif len(result.episodes) > 1:
                epNum = MULTI_EP_RESULT
                sickrage.app.log.debug(
                    "Separating multi-episode result to check for later - result contains episodes: " + str(
                        parse_result.episode_numbers))
            elif len(result.episodes) == 0:
                epNum = SEASON_RESULT
                sickrage.app.log.debug("Separating full season result to check for later")

            if epNum not in results:
                results[epNum] = [result]
            else:
                results[epNum] += [result]

        return results

    def find_propers(self, episodes):
        results = []

        for episode in episodes:
            show = findCertainShow(int(episode["showid"]))
            if not show:
                continue

            ep_obj = show.getEpisode(int(episode["season"]), int(episode["episode"]))
            for term in self.proper_strings:
                search_strngs = self._get_episode_search_strings(ep_obj, add_string=term)
                for item in self.search(search_strngs[0], ep_obj=ep_obj):
                    result = self.getResult([ep_obj])
                    result.name, result.url = self._get_title_and_url(item)
                    if not validate_url(result.url) and not result.url.startswith('magnet'):
                        continue

                    result.seeders, result.leechers = self._get_result_stats(item)
                    result.size = self._get_size(item)
                    result.date = datetime.datetime.today()
                    result.show = show
                    results.append(result)

        return results

    def add_cookies_from_ui(self):
        """
        Add the cookies configured from UI to the providers requests session.
        :return: dict
        """

        if isinstance(self, TorrentRssProvider) and not self.cookies:
            return {'result': True,
                    'message': 'This is a TorrentRss provider without any cookies provided. '
                               'Cookies for this provider are considered optional.'}

        # This is the generic attribute used to manually add cookies for provider authentication
        if not self.enable_cookies:
            return {'result': False,
                    'message': 'Adding cookies is not supported for provider: {}'.format(self.name)}

        if not self.cookies:
            return {'result': False,
                    'message': 'No Cookies added from ui for provider: {}'.format(self.name)}

        cookie_validator = re.compile(r'^([\w%]+=[\w%]+)(;[\w%]+=[\w%]+)*$')
        if not cookie_validator.match(self.cookies):
            sickrage.app.alerts.message(
                'Failed to validate cookie for provider {}'.format(self.name),
                'Cookie is not correctly formatted: {}'.format(self.cookies))

            return {'result': False,
                    'message': 'Cookie is not correctly formatted: {}'.format(self.cookies)}

        if not all(req_cookie in [x.rsplit('=', 1)[0] for x in self.cookies.split(';')] for req_cookie in
                   self.required_cookies):
            return {'result': False,
                    'message': "You haven't configured the required cookies. Please login at {provider_url}, "
                               "and make sure you have copied the following cookies: {required_cookies!r}"
                        .format(provider_url=self.name, required_cookies=self.required_cookies)}

        # cookie_validator got at least one cookie key/value pair, let's return success
        add_dict_to_cookiejar(self.session.cookies,
                              dict(x.rsplit('=', 1) for x in self.cookies.split(';')))

        return {'result': True,
                'message': ''}

    def check_required_cookies(self):
        """
        Check if we have the required cookies in the requests sessions object.

        Meaning that we've already successfully authenticated once, and we don't need to go through this again.
        Note! This doesn't mean the cookies are correct!
        """
        if not hasattr(self, 'required_cookies'):
            # A reminder for the developer, implementing cookie based authentication.
            sickrage.app.log.error(
                'You need to configure the required_cookies attribute, for the provider: {}'.format(self.name))
            return False
        return all(
            dict_from_cookiejar(self.session.cookies).get(cookie) for cookie in self.required_cookies)

    def cookie_login(self, check_login_text, check_url=None):
        """
        Check the response for text that indicates a login prompt.

        In that case, the cookie authentication was not successful.
        :param check_login_text: A string that's visible when the authentication failed.
        :param check_url: The url to use to test the login with cookies. By default the providers home page is used.

        :return: False when authentication was not successful. True if successful.
        """
        check_url = check_url or self.urls['base_url']

        if self.check_required_cookies():
            # All required cookies have been found within the current session, we don't need to go through this again.
            return True

        if self.cookies:
            result = self.add_cookies_from_ui()
            if not result['result']:
                sickrage.app.alerts.notifications.message(result['message'])
                sickrage.app.log.warning(result['message'])
                return False
        else:
            sickrage.app.log.warning('Failed to login, you will need to add your cookies in the provider '
                                     'settings')

            sickrage.app.alerts.notifications.error(
                'Failed to auth with {provider}'.format(provider=self.name),
                'You will need to add your cookies in the provider settings')
            return False

        response = self.session.get(check_url)
        if any([not response, not (response.text and response.status_code == 200),
                check_login_text.lower() in response.text.lower()]):
            sickrage.app.log.warning('Please configure the required cookies for this provider. Check your '
                                     'provider settings')

            sickrage.app.alerts.notifications.error(
                'Wrong cookies for {}'.format(self.name),
                'Check your provider settings'
            )
            self.session.cookies.clear()
            return False
        else:
            return True

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
        return sickrage.app.config.use_torrents and self.isEnabled

    @property
    def imageName(self):
        if os.path.isfile(
                os.path.join(sickrage.app.config.gui_static_dir, 'images', 'providers', self.id + '.png')):
            return self.id + '.png'
        return self.type + '.png'

    @property
    def seed_ratio(self):
        """
        Provider should override this value if custom seed ratio enabled
        It should return the value of the provider seed ratio
        """
        return self.ratio

    def getResult(self, episodes=None):
        """
        Returns a result of the correct type for this provider
        """
        result = TorrentSearchResult(episodes)
        result.provider = self
        return result

    def get_content(self, url):
        result = None

        def verify_torrent(content):
            try:
                if bencode.bdecode(content).get('info'):
                    return content
            except Exception:
                pass

        if url.startswith('magnet'):
            # try iTorrents
            info_hash = str(re.findall(r'urn:btih:([\w]{32,40})', url)[0]).upper()
            if len(info_hash) == 32:
                info_hash = b16encode(b32decode(info_hash)).upper()

            if info_hash:
                torrent_url = "https://itorrents.org/torrent/{info_hash}.torrent".format(info_hash=info_hash)
                result = verify_torrent(super(TorrentProvider, self).get_content(torrent_url))

                # try api
                if not result and sickrage.app.config.enable_api:
                    try:
                        # add to external database
                        sickrage.app.api.add_torrent_cache_result(url)
                        result = verify_torrent(
                            b64decode(sickrage.app.api.get_torrent_cache_results(info_hash)).strip())
                    except Exception:
                        pass

        if not result:
            result = verify_torrent(super(TorrentProvider, self).get_content(url))

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
            sickrage.app.log.info('Skipping DIAMOND release for mass fake releases.')
            title = download_url = 'FAKERELEASE'
        else:
            title = self._clean_title_from_provider(title)

        download_url = download_url.replace('&amp;', '&')

        return title, download_url

    def _get_size(self, item):
        return item.get('size', -1)

    def download_result(self, result):
        """
        Downloads a result to the appropriate black hole folder.

        :param result: SearchResult instance to download.
        :return: boolean, True on success
        """

        if not result.content:
            return False

        filename = self.make_filename(result.name)

        sickrage.app.log.info("Saving TORRENT to " + filename)

        # write content to torrent file
        with io.open(filename, 'wb') as f:
            f.write(result.content)

        return True

    @staticmethod
    def _clean_title_from_provider(title):
        return (title or '').replace(' ', '.')

    def make_filename(self, name):
        return os.path.join(sickrage.app.config.torrent_dir, '{}.torrent'.format(sanitizeFileName(name)))

    def add_trackers(self, result):
        """
        Adds public trackers to either torrent file or magnet link
        :param result: SearchResult
        :return: SearchResult
        """

        try:
            trackers_list = self.session.get('https://cdn.sickrage.ca/torrent_trackers/').text.split()
        except Exception:
            trackers_list = []

        if trackers_list:
            # adds public torrent trackers to magnet url
            if result.url.startswith('magnet:'):
                result.url += '&tr='.join(trackers_list)

            # adds public torrent trackers to content
            if result.content:
                decoded_data = bencode.bdecode(result.content)
                if not decoded_data.get('announce-list'):
                    decoded_data[b'announce-list'] = []

                for tracker in trackers_list:
                    if tracker not in decoded_data['announce-list']:
                        decoded_data['announce-list'].append([str(tracker)])
                result.content = bencode.bencode(decoded_data)

        return result

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
        return sickrage.app.config.use_nzbs and self.isEnabled

    @property
    def imageName(self):
        if os.path.isfile(
                os.path.join(sickrage.app.config.gui_static_dir, 'images', 'providers', self.id + '.png')):
            return self.id + '.png'
        return self.type + '.png'

    def getResult(self, episodes=None):
        """
        Returns a result of the correct type for this provider
        """
        result = NZBSearchResult(episodes)
        result.provider = self
        return result

    def _get_size(self, item):
        return item.get('size', -1)

    def download_result(self, result):
        """
        Downloads a result to the appropriate black hole folder.

        :param result: SearchResult instance to download.
        :return: boolean, True on success
        """

        if not result.content:
            return False

        filename = self.make_filename(result.name)

        # Support for Jackett/TorzNab
        if (result.url.endswith('torrent') or result.url.startswith('magnet')) and self.type in ['nzb', 'newznab']:
            filename = filename.rsplit('.', 1)[0] + '.' + 'torrent'

        if result.resultType == "nzb":
            sickrage.app.log.info("Saving NZB to " + filename)

            # write content to torrent file
            with io.open(filename, 'wb') as f:
                f.write(result.content)

            return True
        elif result.resultType == "nzbdata":
            filename = os.path.join(sickrage.app.config.nzb_dir, result.name + ".nzb")

            sickrage.app.log.info("Saving NZB to " + filename)

            # save the data to disk
            try:
                with io.open(filename, 'w') as fileOut:
                    fileOut.write(result.extraInfo[0])

                chmodAsParent(filename)

                return True
            except EnvironmentError as e:
                sickrage.app.log.error("Error trying to save NZB to black hole: {}".format(e.message))

    def make_filename(self, name):
        return os.path.join(sickrage.app.config.nzb_dir, '{}.nzb'.format(sanitizeFileName(name)))

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
        torrent_file = None

        try:
            add_cookie = self.add_cookies_from_ui()
            if not add_cookie.get('result'):
                return add_cookie

            data = self.cache._get_rss_data()['entries']
            if not data:
                return {'result': False,
                        'message': 'No items found in the RSS feed {}'.format(self.urls['base_url'])}

            (title, url) = self._get_title_and_url(data[0])

            if not title:
                return {'result': False,
                        'message': 'Unable to get title from first item'}

            if not url:
                return {'result': False,
                        'message': 'Unable to get torrent url from first item'}

            if url.startswith('magnet:') and re.search(r'urn:btih:([\w]{32,40})', url):
                return {'result': True,
                        'message': 'RSS feed Parsed correctly'}
            else:
                try:
                    torrent_file = self.session.get(url).content
                    bencode.bdecode(torrent_file)
                except Exception as e:
                    if data: self.dumpHTML(torrent_file)
                    return {'result': False,
                            'message': 'Torrent link is not a valid torrent file: {}'.format(e.message)}

            return {'result': True,
                    'message': 'RSS feed Parsed correctly'}

        except Exception as e:
            return {'result': False,
                    'message': 'Error when trying to load RSS: {}'.format(e.message)}

    @staticmethod
    def dumpHTML(data):
        dumpName = os.path.join(sickrage.app.cache_dir, 'custom_torrent.html')

        try:
            with io.open(dumpName, 'wb') as fileOut:
                fileOut.write(data)

            chmodAsParent(dumpName)

            sickrage.app.log.info("Saved custom_torrent html dump %s " % dumpName)
        except IOError as e:
            sickrage.app.log.error("Unable to save the file: %s " % repr(e))
            return False

        return True

    @classmethod
    def getProviders(cls):
        providers = cls.getDefaultProviders()

        try:
            for curProviderStr in sickrage.app.config.custom_providers.split('!!!'):
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
            response = self.session.get(urljoin(self.urls['base_url'], 'api'), params=url_params).text
        except Exception:
            error_string = 'Error getting caps xml for [{}]'.format(self.name)
            sickrage.app.log.warning(error_string)
            return False, return_categories, error_string

        with bs4_parser(response) as html:
            if not html.find('categories'):
                error_string = 'Error parsing caps xml for [{}]'.format(self.name)
                sickrage.app.log.debug(error_string)
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
            sickrage.app.log.warning('Invalid api key for {}. Check your settings'.format(self.name))
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

        sickrage.app.log.info(err_desc)

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
                'maxage': sickrage.app.config.usenet_retention
            }

            if self.private and self.key:
                search_params['apikey'] = self.key

            if mode != 'RSS':
                if (self.cap_tv_search or not self.cap_tv_search == 'True') and not self.force_query:
                    search_params['t'] = 'tvsearch'
                    search_params.update({'tvdbid': ep_obj.show.indexerid})

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

            sickrage.app.log.debug('Search mode: {0}'.format(mode))

            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    # If its a PROPER search, need to change param to 'search' so it searches using 'q' param
                    if any(proper_string in search_string for proper_string in self.proper_strings):
                        search_params['t'] = 'search'

                    sickrage.app.log.debug("Search string: {}".format(search_string))

                    if search_params['t'] != 'tvsearch':
                        search_params['q'] = search_string

                sleep(cpu_presets[sickrage.app.config.cpu_preset])

                try:
                    data = self.session.get(urljoin(self.urls['base_url'], 'api'), params=search_params).text
                    results += self.parse(data, mode)
                except Exception:
                    sickrage.app.log.debug('No data returned from provider')
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

    def parse(self, data, mode):
        results = []

        with bs4_parser(data) as html:
            if not self._check_auth_from_data(html):
                return results

            try:
                self.torznab = 'xmlns:torznab' in html.rss.attrs
            except AttributeError:
                self.torznab = False

            if not html('item'):
                sickrage.app.log.debug('No results returned from provider. Check chosen Newznab '
                                       'search categories in provider settings and/or usenet '
                                       'retention')
                return results

            for item in html('item'):
                try:
                    title = item.title.get_text(strip=True)
                    download_url = None
                    if item.link:
                        url = item.link.get_text(strip=True)
                        if validate_url(url) or url.startswith('magnet'):
                            download_url = url

                        if not download_url:
                            url = item.link.next.strip()
                            if validate_url(url) or url.startswith('magnet'):
                                download_url = url

                    if not download_url and item.enclosure:
                        url = item.enclosure.get('url', '').strip()
                        if validate_url(url) or url.startswith('magnet'):
                            download_url = url

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

                    results += [
                        {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                    ]

                    if mode != 'RSS':
                        sickrage.app.log.debug('Found result: {}'.format(title))
                except (AttributeError, TypeError, KeyError, ValueError, IndexError):
                    sickrage.app.log.error('Failed parsing provider')

        return results

    @classmethod
    def getProviders(cls):
        providers = cls.getDefaultProviders()

        try:
            for curProviderStr in sickrage.app.config.custom_providers.split('!!!'):
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
            cls('NZB.Cat', 'https://nzb.cat', '', '5030,5040,5010', 'eponly', True, True, True, True),
            cls('NZBGeek', 'https://api.nzbgeek.info', '', '5030,5040', 'eponly', False, False, False, True),
            cls('NZBs.org', 'https://nzbs.org', '', '5030,5040', 'eponly', False, False, False, True),
            cls('Usenet-Crawler', 'https://api.usenet-crawler.com', '', '5030,5040', 'eponly', False, False, False, True)
        ]


class TorrentRssCache(TVCache):
    def __init__(self, provider_obj):
        TVCache.__init__(self, provider_obj)
        self.min_time = 15

    def _get_rss_data(self):
        sickrage.app.log.debug("Cache update URL: %s" % self.provider.urls['base_url'])

        if self.provider.cookies:
            add_dict_to_cookiejar(self.provider.session.cookies,
                                  dict(x.rsplit('=', 1) for x in self.provider.cookies.split(';')))

        return self.getRSSFeed(self.provider.urls['base_url'])


class SearchProviders(dict):
    def __init__(self):
        super(SearchProviders, self).__init__()

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
