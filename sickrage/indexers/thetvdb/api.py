# ##############################################################################
#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#  -
#  This file is part of SiCKRAGE.
#  -
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  -
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
# ##############################################################################


import functools
import json
import re
import time
from base64 import urlsafe_b64decode
from collections import OrderedDict
from datetime import datetime
from operator import itemgetter
from urllib.parse import urljoin, quote

import requests
from six import text_type

import sickrage
from sickrage.core.websession import WebSession

try:
    import gzip
except ImportError:
    gzip = None

from sickrage.indexers.thetvdb.exceptions import (tvdb_seasonnotfound,
                                                  tvdb_episodenotfound, tvdb_attributenotfound, tvdb_unauthorized)


def login_required(f):
    @functools.wraps(f)
    def wrapper(obj, *args, **kwargs):
        if not obj.jwt_token:
            obj.authenticate()

        for i in range(3):
            try:
                return f(obj, *args, **kwargs)
            except tvdb_unauthorized:
                obj.authenticate()

        sickrage.app.log.debug("Unable to authenticate to TheTVDB")

    return wrapper


def to_lowercase(iterable):
    if type(iterable) is dict:
        for key in iterable.copy().keys():
            iterable[key.lower()] = iterable.pop(key)
            if type(iterable[key.lower()]) is dict or type(iterable[key.lower()]) is list:
                iterable[key.lower()] = to_lowercase(iterable[key.lower()])
    elif type(iterable) is list:
        for i, item in enumerate(iterable.copy()):
            iterable[i] = to_lowercase(item)

    return iterable


class BaseUI:
    """Default UI, which auto-selects first results
    """

    def __init__(self, config, log=None):
        self.config = config

    def selectSeries(self, allSeries, series=None):
        return allSeries[0]


class ShowCache(OrderedDict):
    def __init__(self, *args, **kwargs):
        self.maxsize = 100
        super(ShowCache, self).__init__(*args, **kwargs)

    def __setitem__(self, key, value, dict_setitem=dict.__setitem__):
        super(ShowCache, self).__setitem__(key, value)
        while len(self) > self.maxsize:
            self.pop(list(self.keys())[0], None)


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
            # Key is an season, return it
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
            # Season number x was not found
            raise tvdb_seasonnotfound("Could not find season {}".format(repr(key)))
        else:
            # If it's not numeric, it must be an attribute name, which
            # doesn't exist, so attribute error.
            raise tvdb_attributenotfound("Cannot find show attribute {}".format(repr(key)))

    def airedOn(self, date):
        ret = self.search(str(date), 'firstaired')
        if len(ret) == 0:
            sickrage.app.log.debug("Could not find any episodes on TheTVDB that aired on {}".format(date))
            return None
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
        self.data = {}

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, d):
        self.__dict__.update(d)

    def __repr__(self):
        return "<Season instance (containing {} episodes)>".format(
            len(self.keys())
        )

    def __getattr__(self, key):
        if key in self:
            return self[key]

        if key in self.data:
            # Non-numeric request is for season-data
            return self.data[key]

        raise AttributeError

    def __getitem__(self, key):
        if key in self:
            # Key is an episode, return it
            return dict.__getitem__(self, key)

        if key in self.data:
            # Non-numeric request is for season-data
            return dict.__getitem__(self.data, key)

        if isinstance(key, int) or key.isdigit():
            raise tvdb_episodenotfound("Could not find episode {}".format(repr(key)))
        else:
            raise tvdb_attributenotfound("Cannot find season attribute {}".format(repr(key)))

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
            raise tvdb_attributenotfound("Cannot find episode attribute {}".format(repr(key)))

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
            if isinstance(cur_value, dict) or key is None or cur_value is None:
                continue

            cur_key, cur_value = str(cur_key).lower(), str(cur_value).lower()
            if cur_key != key:
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


class Tvdb:
    """Create easy-to-use interface to name of season/episode name
    """

    def __init__(self):
        self.config = {
            'api': {
                'version': '3.0.0',
                'lang': 'en',
                'base': "https://api.thetvdb.com",
                'login': '/login',
                'refresh': '/refresh_token',
                'languages': '/languages',
                'getSeries': "/search/series?name={name}",
                'getSeriesIMDB': "/search/series?imdbId={id}",
                'getSeriesZap2It': "/search/series?zap2itId={id}",
                'series': "/series/{id}",
                'episodes': "/series/{id}/episodes",
                'episode_info': "/episodes/{id}",
                'actors': "/series/{id}/actors",
                'updated': "/updated/query?fromTime={time}",
                'images': {
                    'fanart': "/series/{id}/images/query?keyType=fanart&subKey=graphical",
                    'banner': "/series/{id}/images/query?keyType=fanart&subKey=text",
                    'poster': "/series/{id}/images/query?keyType=poster",
                    'series': "/series/{id}/images/query?keyType=series",
                    'season': "/series/{id}/images/query?keyType=season&subKey={season}",
                    'seasonwide': "/series/{id}/images/query?keyType=seasonwide&subKey={season}",
                    'params': "/series/{id}/images/query/params",
                    'prefix': "https://www.thetvdb.com/banners/{value}"
                }
            }
        }

        self.shows = ShowCache()

    def settings(self,
                 debug=False,
                 cache=True,
                 custom_ui=None,
                 language=None,
                 apikey='F9C450E78D99172E',
                 dvdorder=False,
                 proxy=None,
                 headers=None):

        self.config.update({'apikey': apikey, 'debug_enabled': debug, 'custom_ui': custom_ui, 'cache_enabled': cache,
                            'dvdorder': dvdorder, 'proxy': proxy, 'headers': headers or {},
                            'language': language if language in self.languages else None})

    @property
    def jwt_token(self):
        return getattr(self, '_jwt_token', None)

    @jwt_token.setter
    def jwt_token(self, value):
        if self.jwt_token != value:
            setattr(self, '_jwt_token', value)
            self.jwt_payload = self.get_jwt_payload(self.jwt_token)

    @property
    def jwt_payload(self):
        return getattr(self, '_jwt_payload', {})

    @jwt_payload.setter
    def jwt_payload(self, value):
        if self.jwt_payload != value:
            setattr(self, '_jwt_payload', value)

    @property
    def jwt_expiration(self):
        return self.jwt_payload.get('exp', time.time())

    @property
    def jwt_time_remaining(self):
        return max(self.jwt_expiration - time.time(), 0)

    @property
    def jwt_is_expired(self):
        return self.jwt_expiration <= time.time()

    def logout(self):
        self.jwt_token = None

    def _refresh(self):
        resp = self._request('get', self.config['api']['refresh'])
        if resp and 'token' in resp:
            self.jwt_token = resp['token']

    def _login(self):
        resp = self._request('post', self.config['api']['login'], json={'apikey': self.config['apikey']})
        if resp and 'token' in resp:
            self.jwt_token = resp['token']

    def authenticate(self):
        try:
            if not self.jwt_token or self.jwt_is_expired:
                return self._login()
            elif self.jwt_time_remaining < 7200:
                return self._refresh()
        except Exception as e:
            self.logout()

    def jwt_decode(self, data):
        # make sure data is binary
        if isinstance(data, text_type):
            sickrage.app.log.debug('Encoding the JWT token as UTF-8')
            data = data.encode('utf-8')

        # pad the data to a multiple of 4 bytes
        remainder = len(data) % 4
        if remainder > 0:
            length = 4 - remainder
            sickrage.app.log.debug('Padding the JWT with {x} bytes'.format(x=length))
            data += b'=' * length

        # base64 decode the data
        data = urlsafe_b64decode(data)

        # convert the decoded json to a string
        data = data.decode('utf-8')

        # return the json string as a dict
        result = json.loads(data)
        sickrage.app.log.info('JWT Successfully decoded')
        return result

    def get_jwt_payload(self, token):
        result = {}

        try:
            __, payload, __ = token.split('.')
        except AttributeError:
            sickrage.app.log.debug('Unable to extract payload from JWT: {}'.format(token))
        else:
            result = self.jwt_decode(payload)
            sickrage.app.log.debug('Payload extracted from JWT: {}'.format(result))
        finally:
            return result

    def _request(self, method, url, lang=None, **kwargs):
        self.config['headers'].update({'Authorization': 'Bearer {}'.format(self.jwt_token)})
        self.config['headers'].update({'Content-type': 'application/json'})
        self.config['headers'].update({'Accept-Language': lang or self.config['language']})
        self.config['headers'].update({'Accept': 'application/vnd.thetvdb.v{}'.format(self.config['api']['version'])})

        if not self.health:
            return None

        resp = WebSession(cache=self.config['cache_enabled']).request(
            method, urljoin(self.config['api']['base'], url), headers=self.config['headers'],
            timeout=sickrage.app.config.indexer_timeout, verify=False, **kwargs
        )

        if resp and resp.content:
            try:
                data = resp.json()
            except ValueError:
                sickrage.app.log.debug("Unable to parse data from TheTVDB")
                return None

            return to_lowercase(data)

        if resp is not None:
            if resp.status_code == 401:
                raise tvdb_unauthorized(resp.text)
            elif resp.status_code == 504:
                sickrage.app.log.debug("Unable to connect to TheTVDB")
                return None

            if 'application/json' in resp.headers.get('content-type', ''):
                err_msg = resp.json().get('Error', resp.text)
                sickrage.app.log.debug("Unable to get data from TheTVDB, Code: {code} Error: {err_msg!r}".format(code=resp.status_code, err_msg=err_msg))
                return None

    def _set_item(self, sid, seas, ep, attrib, value):
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

    def _set_show_data(self, sid, key, value):
        """Sets self.shows[sid] to a new Show instance, or sets the data
        """

        if sid not in self.shows:
            self.shows[sid] = Show()

        self.shows[sid].data[key] = value

    def _clean_data(self, data):
        """Cleans up strings returned by TheTVDB.com

        Issues corrected:
        - Replaces &amp; with &
        - Trailing whitespace
        """

        return data.replace("&amp;", "&").strip() if isinstance(data, str) else data

    @login_required
    def search(self, series):
        """This searches TheTVDB.com for the series by name, imdbid, or zap2itid
        and returns the result list
        """

        if not re.search(r'tt\d+', series):
            sickrage.app.log.debug("Searching for show by name: {}".format(series))
            resp = self._request('get', self.config['api']['getSeries'].format(name=quote(series)))
            if resp and 'data' in resp:
                return resp['data']
        else:
            sickrage.app.log.debug("Searching for show by imdbId: {}".format(series))
            resp = self._request('get', self.config['api']['getSeriesIMDB'].format(id=series))
            if resp and 'data' in resp:
                return resp['data']
            # elif zap2itid:
            #    sickrage.app.log.debug("Searching for show by zap2itId: {}".format(zap2itid))
            #    return self._request('get', self.config['api']['getSeriesZap2It'].format(id=zap2itid))['data']

    def _get_series(self, series):
        """This searches TheTVDB.com for the series name,
        If a custom_ui UI is configured, it uses this to select the correct
        series. If not, and interactive == True, ConsoleUI is used, if not
        BaseUI is used to select the first result.
        """
        allSeries = self.search(series)
        if not allSeries:
            sickrage.app.log.debug('Show search returned zero results, cannot find show on TheTVDB')
            return None

        ui = BaseUI(config=self.config)
        if self.config['custom_ui'] is not None:
            ui = self.config['custom_ui'](config=self.config)

        return ui.selectSeries(allSeries, series)

    @login_required
    def _get_show_data(self, sid):
        """Takes a series ID, gets the episodes URL and parses the TVDB
        XML file into the shows dict in layout:
        shows[series_id][season_number][episode_number]
        """

        # Parse show information
        sickrage.app.log.debug('[{}]: Getting all series data from TheTVDB'.format(sid))

        # get series info in english
        resp = self._request('get', self.config['api']['series'].format(id=sid), lang=self.config['api']['lang'])
        if not resp or 'data' not in resp:
            sickrage.app.log.debug("[{}]: Unable to locate show on TheTVDB".format(sid))
            return None

        series_info = resp['data']

        # translate if required to provided language
        if not self.config['language'] == self.config['api']['lang']:
            resp = self._request('get', self.config['api']['series'].format(id=sid))
            if resp and 'data' in resp:
                series_info.update((k, v) for k, v in resp['data'].items() if v)

        # get series data
        for k, v in series_info.items():
            if v is not None:
                if k in ['banner', 'fanart', 'poster']:
                    v = self.config['api']['images']['prefix'].format(value=v)
                elif isinstance(v, list):
                    v = '|'.join(v)
                else:
                    v = self._clean_data(v)

            self._set_show_data(sid, k, v)

        # Parse episode data
        sickrage.app.log.debug('[{}]: Getting episode data from TheTVDB'.format(sid))

        episodes = []
        page = pages = 1

        while True:
            if page > pages:
                break

            episode_info = self._request('get', self.config['api']['episodes'].format(id=sid), lang=self.config['api']['lang'], params={'page': page})
            if not episode_info or 'links' not in episode_info or 'data' not in episode_info:
                break

            pages = episode_info['links']['last']

            # translate if required to provided language
            if not self.config['language'] == self.config['api']['lang']:
                intl_episode_info = self._request('get', self.config['api']['episodes'].format(id=sid), params={'page': page})
                if not intl_episode_info or 'data' not in intl_episode_info:
                    break

                for d1, d2 in zip(episode_info['data'], intl_episode_info['data']):
                    d1.update((k, v) for k, v in d2.items() if v)
                    episodes.append(d1)
            else:
                episodes += episode_info['data']

            page += 1

        if not len(episodes):
            sickrage.app.log.debug('Series {} results incomplete on TheTVDB'.format(sid))
            return None

        episode_incomplete = False
        for cur_ep in episodes:
            use_dvd = False

            if self.config['dvdorder']:
                sickrage.app.log.debug('Using DVD ordering.')
                use_dvd = all([cur_ep.get('dvdseason'), cur_ep.get('dvdepisodenumber')])

            seasnum, epno = cur_ep.get('airedseason'), cur_ep.get('airedepisodenumber')
            if use_dvd:
                seasnum, epno = cur_ep.get('dvdseason'), cur_ep.get('dvdepisodenumber')

            if seasnum is None or epno is None:
                episode_incomplete = True
                continue

            seas_no = int(float(seasnum))
            ep_no = int(float(epno))

            for k, v in cur_ep.items():
                k = k.lower()
                if v is not None:
                    if isinstance(v, list):
                        v = '|'.join(v)
                    else:
                        v = self._clean_data(v)

                self._set_item(sid, seas_no, ep_no, k, v)

            # add episode image url
            image_url = self.config['api']['images']['prefix'].format(value='episodes/{}/{}.jpg'.format(sid, cur_ep['id']))
            self._set_item(sid, seas_no, ep_no, 'filename', image_url)

        if episode_incomplete:
            sickrage.app.log.debug("{}: Series has incomplete season/episode numbers".format(sid))

        # set last updated
        self._set_show_data(sid, 'last_updated', int(time.mktime(datetime.now().timetuple())))

        return self.shows[int(sid)]

    @login_required
    def image_key_types(self, sid, season=None, language='en'):
        key_types = {}

        resp = self._request('get', self.config['api']['images']['params'].format(id=sid), language)
        if not resp or 'data' not in resp:
            return key_types

        for item in resp['data']:
            key_type = item['keytype']
            resolution = item['resolution']
            subkey = item['subkey']

            has_image = False
            if season and "season" in key_type:
                if season in subkey:
                    has_image = True
            elif key_type in ['fanart', 'series', 'poster']:
                if 'graphical' in subkey or len(resolution):
                    has_image = True

            if language not in key_types:
                key_types.update({
                    key_type: has_image
                })

        return key_types

    @login_required
    def images(self, sid, key_type='poster', season=None):
        sickrage.app.log.debug('Getting {} images for {}'.format(key_type, sid))

        images = []

        for language in [self.config['api']['lang'], self.config['language']]:
            key_types = self.image_key_types(sid, season, language)
            if not key_types or key_type not in key_types:
                continue

            if not season:
                resp = self._request('get', self.config['api']['images'][key_type].format(id=sid), language)
                if resp and 'data' in resp:
                    images = resp['data']
            else:
                resp = self._request('get', self.config['api']['images'][key_type].format(id=sid, season=season), language)
                if resp and 'data' in resp:
                    images = resp['data']

        # unable to retrieve images in languages wanted
        if not images:
            return []

        for i, image in enumerate(images):
            if season and int(image['subkey']) != season:
                continue
            image["score"] = image["ratingsinfo"]["average"] * image["ratingsinfo"]["count"]
            for k, v in image.items():
                if not all([k, v]):
                    continue
                v = (v, self.config['api']['images']['prefix'].format(value=v))[k in ['filename', 'thumbnail']]
                images[i][k] = v

        return [item for item in sorted(images, key=itemgetter("score"), reverse=True)]

    @login_required
    def actors(self, sid):
        sickrage.app.log.debug("Getting actors for {}".format(sid))

        cur_actors = Actors()

        resp = self._request('get', self.config['api']['actors'].format(id=sid))
        if not resp or 'data' not in resp:
            sickrage.app.log.debug('Actors result returned zero')
            return cur_actors

        for cur_actor in resp['data']:
            cur_actor = Actor()
            for k, v in cur_actor.items():
                if not all([k, v]):
                    continue
                v = (v, self.config['api']['images']['prefix'].format(value=v))[k == 'image']
                cur_actor[k] = v

            cur_actors.append(cur_actor)

        return cur_actors

    @login_required
    def updated(self, fromTime):
        resp = self._request('get', self.config['api']['updated'].format(time=fromTime))
        if resp and 'data' in resp:
            return resp['data']

    @property
    def languages(self):
        return {'el': 20, 'en': 7, 'zh': 27, 'it': 15, 'cs': 28, 'es': 16, 'ru': 22, 'nl': 13, 'pt': 26, 'no': 9,
                'tr': 21, 'pl': 18, 'fr': 17, 'hr': 31, 'de': 14, 'da': 10, 'fi': 11, 'hu': 19, 'ja': 25, 'he': 24,
                'ko': 32, 'sv': 8, 'sl': 30}

        # return {l['abbreviation']: l['id'] for l in self._request('get', self.config['api']['languages'])}

    @property
    def health(self):
        for i in range(3):
            try:
                health = requests.get(urljoin(self.config['api']['base'], 'health'), verify=False, timeout=30).ok
            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
                pass
            else:
                break
        else:
            health = False

        if not health:
            sickrage.app.log.debug("TheTVDB API server is currently unreachable")
            return False

        return True

    def __getitem__(self, key):
        if isinstance(key, int):
            if key in self.shows:
                if self.config['cache_enabled']:
                    return self.shows[key]
                del self.shows[key]
            return self._get_show_data(key)
        return self._get_series(key)

    def __repr__(self):
        return repr(self.shows)
