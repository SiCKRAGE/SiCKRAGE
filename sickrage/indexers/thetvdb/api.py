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

from __future__ import print_function, unicode_literals

import functools
import getpass
import json
import os
import pickle
import tempfile
import time
import zipfile

import imdbpie
import requests
import xmltodict

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
    def __init__(self, filename, maxsize=100):
        super(ShowCache, self).__init__()
        self.filename = filename
        self.maxsize = maxsize
        self._stack = []

    def load(self):
        if os.path.isfile(self.filename):
            try:
                return pickle.load(open(self.filename, 'rb'))
            except:
                os.remove(self.filename)
                return pickle.load(open(self.filename, 'rb'))

        return self

    def save(self):
        pickle.dump(self, open(self.filename, 'wb'))

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
        seasno = int(self.get('seasonnumber', 0))
        epno = int(self.get('episodenumber', 0))
        epname = self.get('episodename')
        if epname is not None:
            return "<Episode %02dx%02d - {}>".format(seasno, epno, epname)
        else:
            return "<Episode %02dx%02d>".format(seasno, epno)

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
                 banners=False,
                 actors=False,
                 custom_ui=None,
                 language='all',
                 apikey='F9C450E78D99172E',
                 useZip=False,
                 dvdorder=False,
                 proxy=None,
                 headers=None,
                 apitoken=None,
                 apiver=2):

        """interactive (True/False):
            When True, uses built-in console UI is used to select the correct show.
            When False, the first search result is used.

        select_first (True/False):
            Automatically selects the first series search result (rather
            than showing the user a list of more than one series).
            Is overridden by interactive = False, or specifying a custom_ui

        debug (True/False) DEPRECATED:
             Replaced with proper use of logging module. To show debug messages:

        banners (True/False):
            Retrieves the banners for a show. These are accessed
            via the _banners key of a Show(), for example:

            >>> Tvdb(banners=True)['scrubs']['_banners'].keys()
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

        self.shows = ShowCache(os.path.abspath(os.path.join(sickrage.DATA_DIR, 'thetvdb.db'))).load()

        self.config = {}

        self.config['apikey'] = apikey

        self.config['debug_enabled'] = debug  # show debugging messages

        self.config['custom_ui'] = custom_ui

        self.config['interactive'] = interactive  # prompt for correct series?

        self.config['select_first'] = select_first

        self.config['useZip'] = useZip

        self.config['dvdorder'] = dvdorder

        self.config['proxy'] = proxy

        self.config['headers'] = headers

        self.config['apitoken'] = apitoken

        self.config['apiver'] = apiver

        self.config['api'] = {1: {}, 2: {}}

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

        self.config['banners_enabled'] = banners
        self.config['actors_enabled'] = actors

        self.config['valid_languages'] = [
            "da", "fi", "nl", "de", "it", "es", "fr", "pl", "hu", "el", "tr",
            "ru", "he", "ja", "pt", "zh", "cs", "sl", "hr", "ko", "en", "sv", "no"
        ]

        self.config['langabbv_to_id'] = {'el': 20, 'en': 7, 'zh': 27,
                                         'it': 15, 'cs': 28, 'es': 16, 'ru': 22, 'nl': 13, 'pt': 26, 'no': 9,
                                         'tr': 21, 'pl': 18, 'fr': 17, 'hr': 31, 'de': 14, 'da': 10, 'fi': 11,
                                         'hu': 19, 'ja': 25, 'he': 24, 'ko': 32, 'sv': 8, 'sl': 30}
        self.config['language'] = language
        if language not in self.config['valid_languages']:
            self.config['language'] = 'all'

        # api base urls
        self.config['api'][1]['base'] = "http://thetvdb.com"
        self.config['api'][2]['base'] = "https://api-beta.thetvdb.com"

        # api-v1 urls
        self.config['api'][1]['getSeries'] = "{base}/api/GetSeries.php?seriesname={{}}".format(
            base=self.config['api'][1]['base'])
        self.config['api'][1]['getSeriesIMDB'] = "{base}/api/GetSeriesByRemoteID.php?imdbid={{}}".format(
            base=self.config['api'][1]['base'])
        self.config['api'][1]['getSeriesZap2It'] = "{base}/api/GetSeriesByRemoteID.php?zap2itid={{}}".format(
            base=self.config['api'][1]['base'])
        self.config['api'][1]['epInfo'] = "{base}/api/{apikey}/series/{{}}/all/{{}}.xml".format(
            base=self.config['api'][1]['base'], apikey=self.config['apikey'])
        self.config['api'][1]['epInfo_zip'] = "{base}/api/{apikey}/series/{{}}/all/{{}}.zip".format(
            base=self.config['api'][1]['base'], apikey=self.config['apikey'])
        self.config['api'][1]['seriesInfo'] = "{base}/api/{apikey}/series/{{}}/{{}}.xml".format(
            base=self.config['api'][1]['base'], apikey=self.config['apikey'])
        self.config['api'][1]['actorsInfo'] = "{base}/api/{apikey}/series/{{}}/actors.xml".format(
            base=self.config['api'][1]['base'], apikey=self.config['apikey'])
        self.config['api'][1]['seriesBanner'] = "{base}/api/{apikey}/series/{{}}/banners.xml".format(
            base=self.config['api'][1]['base'], apikey=self.config['apikey'])
        self.config['api'][1]['artworkPrefix'] = "{base}/banners/{{}}".format(base=self.config['api'][1]['base'])
        self.config['api'][1]['updates_all'] = "{base}/api/{apikey}/updates_all.zip".format(
            base=self.config['api'][1]['base'], apikey=self.config['apikey'])
        self.config['api'][1]['updates_month'] = "{base}/api/{apikey}/updates_month.zip".format(
            base=self.config['api'][1]['base'], apikey=self.config['apikey'])
        self.config['api'][1]['updates_week'] = "{base}/api/{apikey}/updates_week.zip".format(
            base=self.config['api'][1]['base'], apikey=self.config['apikey'])
        self.config['api'][1]['updates_day'] = "{base}/api/{apikey}/updates_day.zip".format(
            base=self.config['api'][1]['base'], apikey=self.config['apikey'])

        # api-v2 urls
        self.config['api'][2]['login'] = '{base}/login'.format(base=self.config['api'][2]['base'])
        self.config['api'][2]['refresh'] = '{base}/refresh_token'.format(base=self.config['api'][2]['base'])
        self.config['api'][2]['getSeries'] = "{base}/search/series?name={{}}".format(
            base=self.config['api'][2]['base'])
        self.config['api'][2]['getSeriesIMDB'] = "{base}/search/series?imdbId={{}}".format(
            base=self.config['api'][2]['base'])
        self.config['api'][2]['getSeriesZap2It'] = "{base}/search/series?zap2itId={{}}".format(
            base=self.config['api'][2]['base'])
        self.config['api'][2]['epInfo'] = "{base}/api/{apikey}/series/{{}}/all/{{}}.xml".format(
            base=self.config['api'][1]['base'], apikey=self.config['apikey'])
        self.config['api'][2]['epInfo_zip'] = "{base}/api/{apikey}/series/{{}}/all/{{}}.zip".format(
            base=self.config['api'][1]['base'], apikey=self.config['apikey'])
        self.config['api'][2]['seriesInfo'] = "{base}/api/{apikey}/series/{{}}/{{}}.xml".format(
            base=self.config['api'][1]['base'], apikey=self.config['apikey'])
        self.config['api'][2]['actorsInfo'] = "{base}/api/{apikey}/series/{{}}/actors.xml".format(
            base=self.config['api'][1]['base'], apikey=self.config['apikey'])
        self.config['api'][2]['seriesBanner'] = "{base}/api/{apikey}/series/{{}}/banners.xml".format(
            base=self.config['api'][1]['base'], apikey=self.config['apikey'])
        self.config['api'][2]['artworkPrefix'] = "{base}/banners/{{}}".format(base=self.config['api'][1]['base'])
        self.config['api'][2]['updates_all'] = "{base}/api/{apikey}/updates_all.zip".format(
            base=self.config['api'][1]['base'], apikey=self.config['apikey'])
        self.config['api'][2]['updates_month'] = "{base}/api/{apikey}/updates_month.zip".format(
            base=self.config['api'][1]['base'], apikey=self.config['apikey'])
        self.config['api'][2]['updates_week'] = "{base}/api/{apikey}/updates_week.zip".format(
            base=self.config['api'][1]['base'], apikey=self.config['apikey'])
        self.config['api'][2]['updates_day'] = "{base}/api/{apikey}/updates_day.zip".format(
            base=self.config['api'][1]['base'], apikey=self.config['apikey'])

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
                jwtResp.update(**sickrage.srCore.srWebSession.post(self.config['api'][self.config['apiver']]['refresh'],
                                                                   headers={'Content-type': 'application/json'},
                                                                   timeout=timeout
                                                                   ).json())
            elif not self.config['apitoken']:
                jwtResp.update(**sickrage.srCore.srWebSession.post(self.config['api'][self.config['apiver']]['login'],
                                                                   json={'apikey': self.config['apikey']},
                                                                   headers={'Content-type': 'application/json'},
                                                                   timeout=timeout
                                                                   ).json())

            self.config['apitoken'] = jwtResp['token']
            self.config['headers']['authorization'] = 'Bearer {}'.format(jwtResp['token'])
        except Exception as e:
            self.config['headers']['authorization'] = self.config['apitoken'] = ""

    @retry(tvdb_error)
    def _loadUrl(self, url, params=None, language=None):
        try:
            # get api v2 token
            if self.config['apiver'] == 2:
                self.getToken()

            self.config['headers'].update({
                'Accept-Language': language or self.config['language']
            })

            sickrage.srCore.srLogger.debug("Retrieving URL {}".format(url))

            # get response from theTVDB
            resp = sickrage.srCore.srWebSession.get(url,
                                                    cache=self.config['cache_enabled'],
                                                    headers=self.config['headers'],
                                                    params=params,
                                                    raise_exceptions=False,
                                                    timeout=sickrage.srCore.srConfig.INDEXER_TIMEOUT)
            # handle requests exceptions
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                self.getToken(True)
                raise tvdb_error("HTTP Error {}: Session token expired, retrieving new token".format(e.errno))
            elif e.response.status_code == 404:
                return tvdb_error("HTTP Error {}: Show not found".format(e.errno))
            raise tvdb_error("HTTP Error {}: while loading URL {}".format(e.errno, url))
        except requests.exceptions.ConnectionError as e:
            raise tvdb_error("Connection error {} while loading URL {}".format(e.message, url))
        except requests.exceptions.Timeout as e:
            raise tvdb_error("Connection timed out {} while loading URL {}".format(e.message, url))
        except Exception as e:
            raise tvdb_error("Unknown exception while loading URL {}: {}".format(url, repr(e)))

        try:
            if 'application/zip' in resp.headers.get("Content-Type", ''):
                try:
                    import StringIO
                    sickrage.srCore.srLogger.debug("We received a zip file unpacking now ...")
                    return json.loads(json.dumps(xmltodict.parse(
                        zipfile.ZipFile(StringIO.StringIO(resp.content)).read(
                            "{}.xml".format(language or self.config['language']))))
                    )
                except zipfile.BadZipfile:
                    raise tvdb_error("Bad zip file received from theTVDB.com, could not read it")

            try:
                return resp.json()
            except:
                return json.loads(json.dumps(xmltodict.parse(resp.content)))
        except:
            pass

    def _getetsrc(self, url, params=None, language=None):
        """Loads a URL using caching, returns an ElementTree of the source
        """

        def keys2lower(in_dict):
            if type(in_dict) is dict:
                out_dict = {}
                for key, item in in_dict.items():
                    out_dict[key.lower()] = keys2lower(item)
                return out_dict
            elif type(in_dict) is list:
                return [keys2lower(obj) for obj in in_dict]

            return in_dict

        try:
            return keys2lower(self._loadUrl(url, params=params, language=language)).values()[0]
        except Exception as e:
            raise tvdb_error(e)

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

    def _cleanData(self, data):
        """Cleans up strings returned by TheTVDB.com

        Issues corrected:
        - Replaces &amp; with &
        - Trailing whitespace
        """

        return data.replace("&amp;", "&").strip()

    def search(self, series=None, imdbid=None, zap2itid=None):
        """This searches TheTVDB.com for the series by name, imdbid, or zap2itid
        and returns the result list
        """

        data = []

        if series:
            sickrage.srCore.srLogger.debug("Searching for show by name: {}".format(series))
            for v in self.config['api']:
                r = self._getetsrc(self.config['api'][v]['getSeries'].format(series))
                if isinstance(r, dict): r = r['series']
                if isinstance(r, list): data += r
        elif imdbid:
            sickrage.srCore.srLogger.debug("Searching for show by imdbId: {}".format(imdbid))
            for v in self.config['api']:
                r = self._getetsrc(self.config['api'][v]['getSeriesIMDB'].format(imdbid))
                if isinstance(r, dict): r = r['series']
                if isinstance(r, list): data += r
        elif zap2itid:
            sickrage.srCore.srLogger.debug("Searching for show by zap2itId: {}".format(zap2itid))
            for v in self.config['api']:
                r = self._getetsrc(self.config['api'][v]['getSeriesZap2It'].format(zap2itid))
                if isinstance(r, dict): r = r['series']
                if isinstance(r, list): data += r

        return data

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

    def _parseBanners(self, sid):
        """Parses banners XML, from
        http://thetvdb.com/api/[APIKEY]/series/[SERIES ID]/banners.xml

        Banners are retrieved using t['show name]['_banners'], for example:

        >>> t = Tvdb(banners = True)
        >>> t['scrubs']['_banners'].keys()
        ['fanart', 'poster', 'series', 'season']
        >>> t['scrubs']['_banners']['poster']['680x1000']['35308']['_bannerpath']
        'http://thetvdb.com/banners/posters/76156-2.jpg'
        >>>

        Any key starting with an underscore has been processed (not the raw
        data from the XML)

        This interface will be improved in future versions.
        """
        sickrage.srCore.srLogger.debug('Getting season banners for {}'.format(sid))
        bannersEt = self._getetsrc(self.config['api'][self.config['apiver']]['seriesBanner'].format(sid))

        if not bannersEt:
            sickrage.srCore.srLogger.debug('Banners result returned zero')
            return

        banners = {}
        for cur_banner in bannersEt['banner'] if isinstance(bannersEt['banner'], list) else [bannersEt['banner']]:
            bid = cur_banner['id']
            btype = cur_banner['bannertype']
            btype2 = cur_banner['bannertype2']
            if btype is None or btype2 is None:
                continue
            if not btype in banners:
                banners[btype] = {}
            if not btype2 in banners[btype]:
                banners[btype][btype2] = {}
            if not bid in banners[btype][btype2]:
                banners[btype][btype2][bid] = {}

            for k, v in cur_banner.items():
                if k is None or v is None:
                    continue

                k, v = k.lower(), v.lower()
                banners[btype][btype2][bid][k] = v

            for k, v in banners[btype][btype2][bid].items():
                if k.endswith("path"):
                    new_key = "_{}".format(k)
                    new_url = self.config['api'][self.config['apiver']]['artworkPrefix'].format(v)
                    banners[btype][btype2][bid][new_key] = new_url

        self._setShowData(sid, "_banners", banners)

        # save persistent data
        self.shows.save()

    def _parseActors(self, sid):
        """Parsers actors XML, from
        http://thetvdb.com/api/[APIKEY]/series/[SERIES ID]/actors.xml

        Actors are retrieved using t['show name]['_actors'], for example:

        >>> t = Tvdb(actors = True)
        >>> actors = t['scrubs']['_actors']
        >>> type(actors)
        <class 'thetvdb.Actors'>
        >>> type(actors[0])
        <class 'thetvdb.Actor'>
        >>> actors[0]
        <Actor "Zach Braff">
        >>> sorted(actors[0].keys())
        ['id', 'image', 'name', 'role', 'sortorder']
        >>> actors[0]['name']
        'Zach Braff'
        >>> actors[0]['image']
        'http://thetvdb.com/banners/actors/43640.jpg'

        Any key starting with an underscore has been processed (not the raw
        data from the XML)
        """
        sickrage.srCore.srLogger.debug("Getting actors for {}".format(sid))
        actorsEt = self._getetsrc(self.config['api'][self.config['apiver']]['actorsInfo'].format(sid))

        if not actorsEt:
            sickrage.srCore.srLogger.debug('Actors result returned zero')
            return

        cur_actors = Actors()
        for cur_actor in actorsEt['actor'] if isinstance(actorsEt['actor'], list) else [actorsEt['actor']]:
            curActor = Actor()
            for k, v in cur_actor.items():
                if k is None or v is None:
                    continue

                k = k.lower()
                if k == "image":
                    v = self.config['api'][self.config['apiver']]['artworkPrefix'].format(v)
                else:
                    v = self._cleanData(v)

                curActor[k] = v
            cur_actors.append(curActor)

        self._setShowData(sid, '_actors', cur_actors)

        # save persistent data
        self.shows.save()

    def _getShowData(self, sid, language, getEpInfo=False):
        """Takes a series ID, gets the epInfo URL and parses the TVDB
        XML file into the shows dict in layout:
        shows[series_id][season_number][episode_number]
        """

        if self.config['language'] is None:
            sickrage.srCore.srLogger.debug('Config language is none, using show language')
            if language is None:
                raise tvdb_error("config['language'] was None, this should not happen")
            getShowInLanguage = language
        else:
            sickrage.srCore.srLogger.debug(
                'Configured language {} override show language of {}'.format(
                    self.config['language'],
                    language
                )
            )
            getShowInLanguage = self.config['language']

        # Parse show information
        sickrage.srCore.srLogger.debug('Getting all series data for {}'.format(sid))

        seriesInfoEt = None
        for v in self.config['api']:
            seriesInfoEt = self._getetsrc(self.config['api'][v]['seriesInfo'].format(sid, getShowInLanguage))
            if seriesInfoEt:
                break

        if not seriesInfoEt:
            sickrage.srCore.srLogger.debug('Series result returned zero')
            raise tvdb_error("Series result returned zero")

        # get series data
        for k, v in seriesInfoEt['series'].items():
            if v is not None:
                if k in ['banner', 'fanart', 'poster']:
                    v = self.config['api'][self.config['apiver']]['artworkPrefix'].format(v)
                else:
                    v = self._cleanData(v)

            self._setShowData(sid, k, v)

        # get episode data
        if getEpInfo:
            # Parse banners
            if self.config['banners_enabled']:
                self._parseBanners(sid)

            # Parse actors
            if self.config['actors_enabled']:
                self._parseActors(sid)

            # Parse episode data
            sickrage.srCore.srLogger.debug('Getting all episodes of {}'.format(sid))

            epsEt = None
            for v in self.config['api']:
                url = self.config['api'][v]['epInfo'].format(sid, language)
                if self.config['useZip']:
                    url = self.config['api'][v]['epInfo_zip'].format(sid, language)

                epsEt = self._getetsrc(url, language=language)
                if epsEt:
                    break

            if not epsEt:
                sickrage.srCore.srLogger.debug('Series results incomplete')

            if epsEt and 'episode' in epsEt:
                episodes = epsEt['episode']
                if not isinstance(episodes, list):
                    episodes = [episodes]

                for cur_ep in episodes:
                    if self.config['dvdorder']:
                        sickrage.srCore.srLogger.debug('Using DVD ordering.')
                        use_dvd = cur_ep['dvd_season'] is not None and cur_ep['dvd_episodenumber'] is not None
                    else:
                        use_dvd = False

                    if use_dvd:
                        seasnum, epno = cur_ep['dvd_season'], cur_ep['dvd_episodenumber']
                    else:
                        seasnum, epno = cur_ep['seasonnumber'], cur_ep['episodenumber']

                    if seasnum is None or epno is None:
                        sickrage.srCore.srLogger.warning(
                            "An episode has incomplete season/episode number (season: %r, episode: %r)".format(
                                seasnum, epno))
                        continue  # Skip to next episode

                    # float() is because https://github.com/dbr/tvnamer/issues/95 - should probably be fixed in TVDB data
                    seas_no = int(float(seasnum))
                    ep_no = int(float(epno))

                    for k, v in cur_ep.items():
                        k = k.lower()

                        if v is not None:
                            if k == 'filename':
                                v = self.config['api'][self.config['apiver']]['artworkPrefix'].format(v)
                            else:
                                v = self._cleanData(v)

                        self._setItem(sid, seas_no, ep_no, k, v)

        # save persistent data
        self.shows.save()

        return self.shows[int(sid)]

    def __getitem__(self, key):
        """
        Handles: tvdb_instance['seriesname'] calls
        """

        if isinstance(key, (int, long)):
            if key in self.shows:
                return self.shows[key]
            return self._getShowData(key, self.config['language'], True)

        selected_series = self._getSeries(key)
        if isinstance(selected_series, dict):
            selected_series = [selected_series]

        # return show data
        return selected_series

    def __repr__(self):
        return repr(self.shows)
