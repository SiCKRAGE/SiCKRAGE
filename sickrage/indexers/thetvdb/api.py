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

import datetime
import functools
import getpass
import os
import pickle
import tempfile
import time
import urlparse

import imdbpie

import sickrage

try:
    import gzip
except ImportError:
    gzip = None

from ui import BaseUI
from exceptions import (tvdb_error, tvdb_shownotfound, tvdb_seasonnotfound, tvdb_episodenotfound,
                        tvdb_attributenotfound)


class Unauthorized(Exception):
    pass


def login_required(f):
    @functools.wraps(f)
    def wrapper(obj, *args, **kwargs):
        if not obj.logged_in:
            obj.login()

        try:
            return f(obj, *args, **kwargs)
        except Unauthorized:
            obj.login(True)
            return f(obj, *args, **kwargs)

    return wrapper


def to_lowercase(iterable):
    if type(iterable) is dict:
        for key in iterable.keys():
            iterable[key.lower()] = iterable.pop(key)
            if type(iterable[key.lower()]) is dict or type(iterable[key.lower()]) is list:
                iterable[key.lower()] = to_lowercase(iterable[key.lower()])
    elif type(iterable) is list:
        for item in iterable:
            item = to_lowercase(item)

    return iterable


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

    def __getstate__(self):
        return self.__dict__

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
            result = ep.search(term=term, key=key)
            if result is not None:
                results.append(result)

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
                 dvdorder=False,
                 proxy=None,
                 headers=None):

        if headers is None: headers = {}
        headers.update({'Content-type': 'application/json'})

        self.shows = ShowCache()
        if os.path.isfile(os.path.join(sickrage.DATA_DIR, 'thetvdb.db')):
            with open(os.path.join(sickrage.DATA_DIR, 'thetvdb.db'), 'rb') as fp:
                self.shows = pickle.load(fp)

        self.config = {'apikey': apikey, 'debug_enabled': debug, 'custom_ui': custom_ui, 'interactive': interactive,
                       'select_first': select_first, 'dvdorder': dvdorder, 'proxy': proxy, 'apitoken': None, 'api': {},
                       'headers': headers}

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

        # api base url
        self.config['api']['base'] = "https://api.thetvdb.com"

        # api-v2 urls
        self.config['api']['login'] = '/login'
        self.config['api']['refresh'] = '/refresh_token'
        self.config['api']['languages'] = '/languages'
        self.config['api']['getSeries'] = "/search/series?name={name}"
        self.config['api']['getSeriesIMDB'] = "/search/series?imdbId={id}"
        self.config['api']['getSeriesZap2It'] = "/search/series?zap2itId={id}"
        self.config['api']['series'] = "/series/{id}"
        self.config['api']['episodes'] = "/series/{id}/episodes"
        self.config['api']['episode_info'] = "/episodes/{id}"
        self.config['api']['actors'] = "/series/{id}/actors"
        self.config['api']['updated'] = "/updated/query?fromTime={time}"
        self.config['api']['images'] = "/series/{id}/images/query?keyType={type}"
        self.config['api']['imagesParams'] = "/series/{id}/images/query/params"
        self.config['api']['imagesPrefix'] = "http://thetvdb.com/banners/{id}"

        self.config['language'] = language
        if language not in self.languages:
            self.config['language'] = None

        if self.config['language']:
            self.config['headers'].update({
                'Accept-Language': self.config['language']
            })

    def login(self, refresh=False):
        try:
            if refresh and self.config['apitoken']:
                self.config['apitoken'] = self._request(
                    self.config['api']['refresh']
                ).json()['token']
            else:
                self.config['apitoken'] = self._request(
                    self.config['api']['login'],
                    json={'apikey': self.config['apikey']},
                ).json()['token']
        except Exception as e:
            self.logout()

    def logout(self):
        self.config['apitoken'] = None

    @property
    def logged_in(self):
        return self.config['apitoken'] is not None

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

    def _request(self, url, params=None, **kwargs):
        if self.config['apitoken']:
            self.config['headers']['authorization'] = 'Bearer {}'.format(self.config['apitoken'])

        # get response from theTVDB
        try:
            resp = sickrage.srCore.srWebSession.get(
                urlparse.urljoin(self.config['api']['base'], url),
                cache=self.config['cache_enabled'],
                headers=self.config['headers'],
                params=params,
                timeout=sickrage.srCore.srConfig.INDEXER_TIMEOUT,
                **kwargs
            )
        except Exception as e:
            raise tvdb_error(e.message)

        # handle requests exceptions
        if resp.status_code == 401:
            raise Unauthorized(resp.json()['Error'])
        elif resp.status_code >= 400:
            raise tvdb_error()

        try:
            return to_lowercase(resp.json())
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

        with open(os.path.join(sickrage.DATA_DIR, 'thetvdb.db'), 'wb') as fp:
            pickle.dump(self.shows, fp)

    def _setShowData(self, sid, key, value):
        """Sets self.shows[sid] to a new Show instance, or sets the data
        """

        if sid not in self.shows:
            self.shows[sid] = Show()

        self.shows[sid].data[key] = value

        with open(os.path.join(sickrage.DATA_DIR, 'thetvdb.db'), 'wb') as fp:
            pickle.dump(self.shows, fp)

    def _delShow(self, sid):
        if sid in self.shows:
            del self.shows[sid]

        with open(os.path.join(sickrage.DATA_DIR, 'thetvdb.db'), 'wb') as fp:
            pickle.dump(self.shows, fp)

    def _cleanData(self, data):
        """Cleans up strings returned by TheTVDB.com

        Issues corrected:
        - Replaces &amp; with &
        - Trailing whitespace
        """

        return data.replace("&amp;", "&").strip() if isinstance(data, basestring) else data

    @login_required
    def search(self, series=None, imdbid=None, zap2itid=None):
        """This searches TheTVDB.com for the series by name, imdbid, or zap2itid
        and returns the result list
        """

        if series:
            sickrage.srCore.srLogger.debug("Searching for show by name: {}".format(series))
            result = self._request(self.config['api']['getSeries'].format(name=series))
            return result['data']
        elif imdbid:
            sickrage.srCore.srLogger.debug("Searching for show by imdbId: {}".format(imdbid))
            result = self._request(self.config['api']['getSeriesIMDB'].format(id=imdbid))
            return result['data']
        elif zap2itid:
            sickrage.srCore.srLogger.debug("Searching for show by zap2itId: {}".format(zap2itid))
            result = self._request(self.config['api']['getSeriesZap2It'].format(id=zap2itid))
            return result['data']

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

    @login_required
    def _parseImages(self, sid):
        sickrage.srCore.srLogger.debug('Getting season images for {}'.format(sid))

        params = self._request(self.config['api']['imagesParams'].format(id=sid))['data']
        if not params:
            return

        images = {}
        for type in [x['keytype'] for x in params]:
            imagesEt = self._request(self.config['api']['images'].format(id=sid, type=type))['data']
            if not imagesEt:
                continue

            for cur_image in imagesEt:
                image_id = cur_image['id']
                image_type = cur_image['keytype']
                image_subtype = cur_image['subkey']
                if image_type is None or image_subtype is None:
                    continue

                if image_type not in images:
                    images[image_type] = {}

                for k, v in cur_image.items():
                    if k is None or v is None:
                        continue

                    k = k.lower()
                    if k in ['filename', 'thumbnail']:
                        v = self.config['api']['imagesPrefix'].format(id=v)
                        if 'season' in image_type:
                            if int(image_subtype) not in images[image_type]:
                                images[image_type][int(image_subtype)] = {}
                            images[image_type][int(image_subtype)][k] = v
                        else:
                            images[image_type][k] = v

        self._setShowData(sid, '_images', images)

    @login_required
    def _parseActors(self, sid):
        sickrage.srCore.srLogger.debug("Getting actors for {}".format(sid))

        actorsEt = self._request(self.config['api']['actors'].format(id=sid))['data']
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
                    v = self.config['api']['imagesPrefix'].format(id=v)
                else:
                    v = self._cleanData(v)

                curActor[k] = v

            cur_actors.append(curActor)

        self._setShowData(sid, '_actors', cur_actors)

    @login_required
    def _getShowData(self, sid, getEpInfo=False):
        """Takes a series ID, gets the episodes URL and parses the TVDB
        XML file into the shows dict in layout:
        shows[series_id][season_number][episode_number]
        """

        # Parse show information
        sickrage.srCore.srLogger.debug('Getting all series data for {}'.format(sid))

        seriesInfoEt = self._request(self.config['api']['series'].format(id=sid))['data']
        if not seriesInfoEt:
            sickrage.srCore.srLogger.debug("[{}]: Series result returned zero".format(sid))
            raise tvdb_error("[{}]: Series result returned zero".format(sid))

        # get series data
        for k, v in seriesInfoEt.items():
            if v is not None:
                if k in ['banner', 'fanart', 'poster']:
                    v = self.config['api']['imagesPrefix'].format(id=v)
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
                try:
                    episodes += self._request(self.config['api']['episodes'].format(id=sid), params={'page': p})['data']
                    p += 1
                except tvdb_error:
                    break

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
                            v = self.config['api']['imagesPrefix'].format(id=v)
                        elif isinstance(v, list):
                            v = '|'.join(v)
                        else:
                            v = self._cleanData(v)

                    self._setItem(sid, seas_no, ep_no, k, v)

        # set last updated
        self._setShowData(sid, 'last_updated', long(time.mktime(datetime.datetime.now().timetuple())))

        return self.shows[int(sid)]

    @login_required
    def updated(self, fromTime):
        return self._request(self.config['api']['updated'].format(time=fromTime))['data']

    @property
    def languages(self):
        return {'el': 20, 'en': 7, 'zh': 27, 'it': 15, 'cs': 28, 'es': 16, 'ru': 22, 'nl': 13, 'pt': 26, 'no': 9,
                'tr': 21, 'pl': 18, 'fr': 17, 'hr': 31, 'de': 14, 'da': 10, 'fi': 11, 'hu': 19, 'ja': 25, 'he': 24,
                'ko': 32, 'sv': 8, 'sl': 30}

        # return {l['abbreviation']: l['id'] for l in self._request(self.config['api']['languages'])}

    def __getitem__(self, key):
        if isinstance(key, (int, long)):
            if key in self.shows:
                fromTime = long(self.shows[key]['last_updated'])
                updated_shows = set(d["id"] for d in self.updated(fromTime) or {})
                if key not in updated_shows:
                    return self.shows[key]
            return self._getShowData(key, True)

        selected_series = self._getSeries(key)
        if isinstance(selected_series, dict):
            selected_series = [selected_series]

        # return show data
        return selected_series

    def __repr__(self):
        return repr(self.shows)
