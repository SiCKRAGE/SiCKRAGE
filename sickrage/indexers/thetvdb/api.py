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

from __future__ import print_function, unicode_literals

import functools
import getpass
import os
import tempfile
import time

import imdbpie
import requests
import sickrage

try:
    import gzip
except ImportError:
    gzip = None

from ui import BaseUI
from exceptions import (tvdb_error, tvdb_shownotfound, tvdb_seasonnotfound, tvdb_episodenotfound,
                        tvdb_attributenotfound)


def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param ExceptionToCheck: the exception to check. may be a tuple of
        exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """

    def deco_retry(f):

        @functools.wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    msg = "{}, Retrying in {} seconds...".format(e, mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry


class ShowCache(dict):
    def __init__(self, maxsize=100):
        super(ShowCache, self).__init__()
        self.maxsize = maxsize
        self._stack = []

    def __setitem__(self, key, value):
        self._stack.append(key)
        if len(self._stack) >= self.maxsize:
            for o in self._stack[:-self.maxsize]:
                del self[o]
            self._stack = self._stack[-self.maxsize:]
        super(ShowCache, self).__setitem__(key, value)


class Show(dict):
    """Holds a dict of seasons, and show data.
    """

    def __init__(self, **kwargs):
        super(Show, self).__init__(**kwargs)
        self.data = {}

    # pickle freindly.
    def __getstate__(self):
        return self.__dict__

    # pickle freindly.
    def __setstate__(self, d):
        self.__dict__.update(d)

    def __repr__(self):
        return "<Show {} (containing {} seasons)>".format(
            self.data.get('seriesname', 'instance'),
            len(self)
        )

    def __getattr__(self, key):
        if key in self:
            # Key is an episode, return it
            return self[key]

        if key in self.data:
            # Non-numeric request is for show-data
            return self.data[key]

        raise AttributeError

    def __getitem__(self, key):
        if key in self:
            # Key is an episode, return it
            return dict.__getitem__(self, key)

        if key in self.data:
            # Non-numeric request is for show-data
            return dict.__getitem__(self.data, key)

        # Data wasn't found, raise appropriate error
        if isinstance(key, int) or key.isdigit():
            # Episode number x was not found
            raise tvdb_seasonnotfound("Could not find season {}".format(repr(key)))
        else:
            # If it's not numeric, it must be an attribute name, which
            # doesn't exist, so attribute error.
            raise tvdb_attributenotfound("Cannot find attribute {}".format(repr(key)))

    def airedOn(self, date):
        ret = self.search(date, 'firstaired')
        if len(ret) == 0:
            raise tvdb_episodenotfound("Could not find any episodes that aired on {}".format(date))
        return ret

    def search(self, term=None, key=None):
        """
        Search all episodes in show. Can search all data, or a specific key (for
        example, episodename)

        Always returns an array (can be empty). First index contains the first
        match, and so on.

        Each array index is an Episode() instance, so doing
        search_results[0]['episodename'] will retrieve the episode name of the
        first match.

        Search terms are converted to lower case (unicode) strings.
        """
        results = []
        for cur_season in self.values():
            searchresult = cur_season.search(term=term, key=key)
            if len(searchresult) != 0:
                results.extend(searchresult)

        return results


class Season(dict):
    def __init__(self):
        super(Season, self).__init__()

    def __repr__(self):
        return "<Season instance (containing {} episodes)>".format(
            len(self.keys())
        )

    def __getattr__(self, episode_number):
        if episode_number in self:
            return self[episode_number]
        raise AttributeError

    def __getitem__(self, episode_number):
        if episode_number not in self:
            raise tvdb_episodenotfound("Could not find episode {}".format(repr(episode_number)))
        else:
            return dict.__getitem__(self, episode_number)

    def search(self, term=None, key=None):
        """Search all episodes in season, returns a list of matching Episode
        instances.
        """
        results = []
        for ep in self.values():
            searchresult = ep.search(term=term, key=key)
            if searchresult is not None:
                results.append(
                    searchresult
                )
        return results


class Episode(dict):
    def __init__(self):
        super(Episode, self).__init__()

    def __repr__(self):
        seasno = int(self.get('airedseason', 0))
        epno = int(self.get('airedepisodenumber', 0))
        epname = self.get('episodename')
        if epname is not None:
            return "<Episode %02dx%02d - %s>" % (seasno, epno, epname)
        else:
            return "<Episode %02dx%02d>" % (seasno, epno)

    def __getattr__(self, key):
        if key in self:
            return self[key]
        raise AttributeError

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            raise tvdb_attributenotfound("Cannot find attribute {}".format(repr(key)))

    def search(self, term=None, key=None):
        """Search episode data for term, if it matches, return the Episode (self).
        The key parameter can be used to limit the search to a specific element,
        for example, episodename.

        This primarily for use use by Show.search and Season.search. See
        Show.search for further information on search
        """
        if term is None:
            raise TypeError("must supply string to search for (contents)")

        for cur_key, cur_value in self.items():
            cur_key, cur_value = cur_key.lower(), cur_value.lower()
            if key is not None and cur_key != key:
                # Do not search this key
                continue
            if cur_value.find(term.lower()) > -1:
                return self


class Actors(list):
    """Holds all Actor instances for a show
    """
    pass


class Actor(dict):
    """Represents a single actor. Should contain..

    id,
    image,
    name,
    role,
    sortorder
    """

    def __repr__(self):
        return "<Actor \"{}\">".format(self.get("name"))


class NetworkError(ValueError):
    pass


class Tvdb:
    """Create easy-to-use interface to name of season/episode name
    >>> t = Tvdb()
    >>> t['Scrubs'][1][24]['episodename']
    'My Last Day'
    """

    def __init__(self,
                 interactive=False,
                 select_first=False,
                 debug=False,
                 cache=True,
                 images=False,
                 actors=False,
                 custom_ui=None,
                 language=None,
                 apikey='F9C450E78D99172E',
                 useZip=False,
                 dvdorder=False,
                 proxy=None,
                 headers=None,
                 apitoken=None):

        """interactive (True/False):
            When True, uses built-in console UI is used to select the correct show.
            When False, the first search result is used.

        select_first (True/False):
            Automatically selects the first series search result (rather
            than showing the user a list of more than one series).
            Is overridden by interactive = False, or specifying a custom_ui

        debug (True/False) DEPRECATED:
             Replaced with proper use of logging module. To show debug messages:

        images (True/False):
            Retrieves the images for a show. These are accessed
            via the _images key of a Show(), for example:

            >>> Tvdb(images=True)['scrubs']['_images'].keys()
            ['fanart', 'poster', 'series', 'season']

        actors (True/False):
            Retrieves a list of the actors for a show. These are accessed
            via the _actors key of a Show(), for example:

            >>> t = Tvdb(actors=True)
            >>> t['scrubs']['_actors'][0]['name']
            'Zach Braff'

        custom_ui (tvdb_ui.BaseUI subclass):
            A callable subclass of tvdb_ui.BaseUI (overrides interactive option)

        language (2 character language abbreviation):
            The language of the returned data. Is also the language search
            uses. Default is "en" (English). For full list, run..

            >>> Tvdb().config['valid_languages'] #doctest: +ELLIPSIS
            ['da', 'fi', 'nl', ...]

        apikey (str/unicode):
            Override the default thetvdb.com API key. By default it will use
            thetvdb's own key (fine for small scripts), but you can use your
            own key if desired - this is recommended if you are embedding
            thetvdb in a larger application)
            See http://thetvdb.com/?tab=apiregister to get your own key

        forceConnect (bool):
            If true it will always try to connect to theTVDB.com even if we
            recently timed out. By default it will wait one minute before
            trying again, and any requests within that one minute window will
            return an exception immediately.

        useZip (bool):
            Download the zip archive where possibale, instead of the xml.
            This is only used when all episodes are pulled.
            And only the main language xml is used, the actor and banner xml are lost.
        """

        if headers is None:
            headers = {}

        self.shows = ShowCache()

        self.config = {'apikey': apikey, 'debug_enabled': debug, 'custom_ui': custom_ui, 'interactive': interactive,
                       'select_first': select_first, 'useZip': useZip, 'dvdorder': dvdorder, 'proxy': proxy,
                       'headers': headers, 'apitoken': apitoken, 'api': {}}

        if cache is True:
            self.config['cache_enabled'] = True
            self.config['cache_location'] = self._getTempDir()
        elif cache is False:
            self.config['cache_enabled'] = False
        elif isinstance(cache, basestring):
            self.config['cache_enabled'] = True
            self.config['cache_location'] = cache
        else:
            raise ValueError("Invalid value for Cache %r (type was {})".format(cache, type(cache)))

        self.config['headers'].update({'Content-type': 'application/json'})

        self.config['images_enabled'] = images
        self.config['actors_enabled'] = actors

        # api base urls
        self.config['api']['base'] = "https://api.thetvdb.com"

        # api-v2 urls
        self.config['api']['login'] = '{base}/login'.format(base=self.config['api']['base'])
        self.config['api']['refresh'] = '{base}/refresh_token'.format(base=self.config['api']['base'])
        self.config['api']['languages'] = '{base}/languages'.format(base=self.config['api']['base'])
        self.config['api']['getSeries'] = "{base}/search/series?name={{}}".format(base=self.config['api']['base'])
        self.config['api']['getSeriesIMDB'] = "{base}/search/series?imdbId={{}}".format(base=self.config['api']['base'])
        self.config['api']['getSeriesZap2It'] = "{base}/search/series?zap2itId={{}}".format(
            base=self.config['api']['base'])
        self.config['api']['series'] = "{base}/series/{{}}".format(base=self.config['api']['base'])
        self.config['api']['episodes'] = "{base}/series/{{}}/episodes".format(base=self.config['api']['base'])
        self.config['api']['episode_info'] = "{base}/episodes/{{}}".format(base=self.config['api']['base'])
        self.config['api']['actors'] = "{base}/series/{{}}/actors".format(base=self.config['api']['base'])
        self.config['api']['images'] = "{base}/series/{{}}/images/query?keyType={{}}".format(
            base=self.config['api']['base'])
        self.config['api']['imagesParams'] = "{base}/series/{{}}/images/query/params".format(
            base=self.config['api']['base'])
        self.config['api']['imagesPrefix'] = "http://thetvdb.com/banners/{}"
        self.config['api']['updated'] = "{base}/updated/query?fromTime={{}}".format(base=self.config['api']['base'])

        self.config['language'] = language
        if language not in self.languages:
            self.config['language'] = None

        if self.config['language']:
            self.config['headers'].update({
                'Accept-Language': self.config['language']
            })

    def _getTempDir(self):
        """Returns the [system temp dir]/thetvdb-u501 (or
        thetvdb-myuser)
        """
        if hasattr(os, 'getuid'):
            uid = os.getuid()
        else:
            # For Windows
            try:
                uid = getpass.getuser()
            except ImportError:
                return os.path.join(tempfile.gettempdir(), "thetvdb")

        return os.path.join(tempfile.gettempdir(), "thetvdb-{}".format(uid))

    def getToken(self, refresh=False):
        jwtResp = {'token': self.config['apitoken']}
        timeout = 10

        try:
            if refresh and self.config['apitoken']:
                jwtResp.update(**sickrage.srCore.srWebSession.post(self.config['api']['refresh'],
                                                                   headers={'Content-type': 'application/json'},
                                                                   timeout=timeout
                                                                   ).json())
            elif not self.config['apitoken']:
                jwtResp.update(**sickrage.srCore.srWebSession.post(self.config['api']['login'],
                                                                   json={'apikey': self.config['apikey']},
                                                                   headers={'Content-type': 'application/json'},
                                                                   timeout=timeout
                                                                   ).json())

            self.config['apitoken'] = jwtResp['token']
            self.config['headers']['authorization'] = 'Bearer {}'.format(jwtResp['token'])
        except Exception as e:
            self.config['headers']['authorization'] = self.config['apitoken'] = ""

    @retry(tvdb_error)
    def _loadUrl(self, url, params=None):
        data = {}

        try:
            # get api v2 token
            self.getToken()

            sickrage.srCore.srLogger.debug("Retrieving URL {}".format(url))

            # get response from theTVDB
            resp = sickrage.srCore.srWebSession.get(url,
                                                    cache=self.config['cache_enabled'],
                                                    headers=self.config['headers'],
                                                    params=params,
                                                    timeout=sickrage.srCore.srConfig.INDEXER_TIMEOUT)
            # handle requests exceptions
            resp.raise_for_status()
            data = resp.json()['data']
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                self.getToken(True)
                raise tvdb_error()
        except Exception as e:
            pass

        return data

    def _getetsrc(self, url, params=None):
        """Loads a URL using caching, returns an ElementTree of the source
        """

        def renameKeys(iterable):
            if type(iterable) is dict:
                for key in iterable.keys():
                    iterable[key.lower()] = iterable.pop(key)
                    if type(iterable[key.lower()]) is dict or type(iterable[key.lower()]) is list:
                        iterable[key.lower()] = renameKeys(iterable[key.lower()])
            elif type(iterable) is list:
                for item in iterable:
                    item = renameKeys(item)
            return iterable

        try:
            return renameKeys(self._loadUrl(url, params=params))
        except Exception as e:
            raise tvdb_error(e.message)

    def _setItem(self, sid, seas, ep, attrib, value):
        """Creates a new episode, creating Show(), Season() and
        Episode()s as required. Called by _getShowData to populate show

        Since the nice-to-use tvdb[1][24]['name] interface
        makes it impossible to do tvdb[1][24]['name] = "name"
        and still be capable of checking if an episode exists
        so we can raise tvdb_shownotfound, we have a slightly
        less pretty method of setting items.. but since the API
        is supposed to be read-only, this is the best way to
        do it!
        The problem is that calling tvdb[1][24]['episodename'] = "name"
        calls __getitem__ on tvdb[1], there is no way to check if
        tvdb.__dict__ should have a key "1" before we auto-create it
        """

        if sid not in self.shows:
            self.shows[sid] = Show()
        if seas not in self.shows[sid]:
            self.shows[sid][seas] = Season()
        if ep not in self.shows[sid][seas]:
            self.shows[sid][seas][ep] = Episode()
        self.shows[sid][seas][ep][attrib] = value

    def _setShowData(self, sid, key, value):
        """Sets self.shows[sid] to a new Show instance, or sets the data
        """

        if sid not in self.shows:
            self.shows[sid] = Show()
        self.shows[sid].data[key] = value

    def _delShow(self, sid):
        if sid in self.shows:
            del self.shows[sid]

    def _cleanData(self, data):
        """Cleans up strings returned by TheTVDB.com

        Issues corrected:
        - Replaces &amp; with &
        - Trailing whitespace
        """

        return data.replace("&amp;", "&").strip() if isinstance(data, basestring) else data

    def search(self, series=None, imdbid=None, zap2itid=None):
        """This searches TheTVDB.com for the series by name, imdbid, or zap2itid
        and returns the result list
        """

        data = []

        if series:
            sickrage.srCore.srLogger.debug("Searching for show by name: {}".format(series))
            return self._getetsrc(self.config['api']['getSeries'].format(series))
        elif imdbid:
            sickrage.srCore.srLogger.debug("Searching for show by imdbId: {}".format(imdbid))
            return self._getetsrc(self.config['api']['getSeriesIMDB'].format(imdbid))
        elif zap2itid:
            sickrage.srCore.srLogger.debug("Searching for show by zap2itId: {}".format(zap2itid))
            return self._getetsrc(self.config['api']['getSeriesZap2It'].format(zap2itid))

    def _getSeries(self, series):
        """This searches TheTVDB.com for the series name,
        If a custom_ui UI is configured, it uses this to select the correct
        series. If not, and interactive == True, ConsoleUI is used, if not
        BaseUI is used to select the first result.
        """
        allSeries = []

        try:
            allSeries += self.search(series)
            if not allSeries:
                raise tvdb_shownotfound
        except tvdb_shownotfound:
            # search via imdbId
            for x in imdbpie.Imdb().search_for_title(series):
                if x['title'].lower() == series.lower():
                    allSeries += self.search(imdbid=x['imdb_id'])

        if not allSeries:
            sickrage.srCore.srLogger.debug('Series result returned zero')
            raise tvdb_shownotfound("Show search returned zero results (cannot find show on theTVDB)")

        ui = BaseUI(config=self.config)
        if self.config['custom_ui'] is not None:
            CustomUI = self.config['custom_ui']
            ui = CustomUI(config=self.config)

        return ui.selectSeries(allSeries, series)

    def _parseImages(self, sid):
        sickrage.srCore.srLogger.debug('Getting season images for {}'.format(sid))

        params = self._getetsrc(self.config['api']['imagesParams'].format(sid))
        if not params:
            return

        for type in [x['keytype'] for x in params]:
            imagesEt = self._getetsrc(self.config['api']['images'].format(sid, type))
            if not imagesEt:
                continue

            images = {}
            for cur_image in imagesEt:
                image_id = cur_image['id']
                image_type = cur_image['keytype']
                image_subtype = cur_image['subkey']
                if image_type is None or image_subtype is None:
                    continue

                if image_type not in images:
                    images[image_type] = {}
                if image_subtype not in images[image_type]:
                    images[image_type][image_subtype] = {}
                if image_id not in images[image_type][image_subtype]:
                    images[image_type][image_subtype][image_id] = {}

                for k, v in cur_image.items():
                    if k is None or v is None:
                        continue

                    k = k.lower()
                    if k in ['filename', 'thumbnail']:
                        v = self.config['api']['imagesPrefix'].format(v)

                    images[image_type][image_subtype][image_id][k] = v

            self._setShowData(sid, "_images", images)

    def _parseActors(self, sid):
        sickrage.srCore.srLogger.debug("Getting actors for {}".format(sid))

        actorsEt = self._getetsrc(self.config['api']['actors'].format(sid))
        if not actorsEt:
            sickrage.srCore.srLogger.debug('Actors result returned zero')
            return

        cur_actors = Actors()
        for cur_actor in actorsEt:
            curActor = Actor()
            for k, v in cur_actor.items():
                if k is None or v is None:
                    continue

                k = k.lower()
                if k == "image":
                    v = self.config['api']['imagesPrefix'].format(v)
                else:
                    v = self._cleanData(v)

                curActor[k] = v

            cur_actors.append(curActor)

        self._setShowData(sid, '_actors', cur_actors)

    def _getShowData(self, sid, getEpInfo=False):
        """Takes a series ID, gets the episodes URL and parses the TVDB
        XML file into the shows dict in layout:
        shows[series_id][season_number][episode_number]
        """

        # Parse show information
        sickrage.srCore.srLogger.debug('Getting all series data for {}'.format(sid))

        seriesInfoEt = self._getetsrc(self.config['api']['series'].format(sid))
        if not seriesInfoEt:
            sickrage.srCore.srLogger.debug('Series result returned zero')
            raise tvdb_error("Series result returned zero")

        # get series data
        for k, v in seriesInfoEt.items():
            if v is not None:
                if k in ['banner', 'fanart', 'poster']:
                    v = self.config['api']['imagesPrefix'].format(v)
                elif isinstance(v, list):
                    v = '|'.join(v)
                else:
                    v = self._cleanData(v)

            self._setShowData(sid, k, v)

        # get episode data
        if getEpInfo:
            # Parse images
            self._parseImages(sid)

            # Parse actors
            self._parseActors(sid)

            # Parse episode data
            sickrage.srCore.srLogger.debug('Getting all episodes of {}'.format(sid))

            p = 1
            episodes = []
            while True:
                data = self._getetsrc(self.config['api']['episodes'].format(sid), params={'page': p})
                if not data: break
                episodes += data
                p += 1

            if not len(episodes):
                sickrage.srCore.srLogger.debug('Series results incomplete')
                return

            for cur_ep in episodes:
                try:
                    use_dvd = False
                    if self.config['dvdorder']:
                        sickrage.srCore.srLogger.debug('Using DVD ordering.')
                        use_dvd = all([cur_ep.get('dvdseason'), cur_ep.get('dvdepisodenumber')])

                    seasnum, epno = cur_ep.get('airedseason'), cur_ep.get('airedepisodenumber')
                    if use_dvd:
                        seasnum, epno = cur_ep.get('dvdseason'), cur_ep.get('dvdepisodenumber')

                    if seasnum is None or epno is None:
                        raise Exception
                except Exception as e:
                    sickrage.srCore.srLogger.warning("Episode has incomplete season/episode numbers, skipping!")
                    continue

                seas_no = int(float(seasnum))
                ep_no = int(float(epno))

                for k, v in cur_ep.items():
                    k = k.lower()

                    if v is not None:
                        if k == 'filename':
                            v = self.config['api']['imagesPrefix'].format(v)
                        elif isinstance(v, list):
                            v = '|'.join(v)
                        else:
                            v = self._cleanData(v)

                    self._setItem(sid, seas_no, ep_no, k, v)

        return self.shows[int(sid)]

    def updated(self, fromTime):
        return self._getetsrc(self.config['api']['updated'].format(fromTime))

    @property
    def languages(self):
        return {'el': 20, 'en': 7, 'zh': 27, 'it': 15, 'cs': 28, 'es': 16, 'ru': 22, 'nl': 13, 'pt': 26, 'no': 9,
                'tr': 21, 'pl': 18, 'fr': 17, 'hr': 31, 'de': 14, 'da': 10, 'fi': 11, 'hu': 19, 'ja': 25, 'he': 24,
                'ko': 32, 'sv': 8, 'sl': 30}

        # return {l['abbreviation']: l['id'] for l in self._getetsrc(self.config['api']['languages'])}

    def __getitem__(self, key):
        """
        Handles: tvdb_instance['seriesname'] calls
        """

        if isinstance(key, (int, long)):
            if key in self.shows:
                return self.shows[key]
            return self._getShowData(key, True)

        selected_series = self._getSeries(key)
        if isinstance(selected_series, dict):
            selected_series = [selected_series]

        # return show data
        return selected_series

    def __repr__(self):
        return repr(self.shows)
