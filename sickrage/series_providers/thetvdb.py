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
from datetime import datetime
from operator import itemgetter
from urllib.parse import urljoin, quote

import requests
from six import text_type

import sickrage
from sickrage.core.enums import SeriesProviderID
from sickrage.core.websession import WebSession
from sickrage.series_providers import SeriesProvider
from sickrage.series_providers.exceptions import SeriesProviderNotAuthorized

try:
    import gzip
except ImportError:
    gzip = None


def login_required(f):
    @functools.wraps(f)
    def wrapper(obj, *args, **kwargs):
        if not obj.jwt_token:
            obj.authenticate()

        for i in range(3):
            try:
                return f(obj, *args, **kwargs)
            except SeriesProviderNotAuthorized:
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


class TheTVDBActors(list):
    """Holds all Actor instances for a show
    """
    pass


class TheTVDBActor(dict):
    """Represents a single actor. Should contain..

    id,
    image,
    name,
    role,
    sortorder
    """

    def __repr__(self):
        return "<Actor \"{}\">".format(self.get("name"))


class TheTVDB(SeriesProvider):
    """Create easy-to-use interface to name of season/episode name
    """

    def __init__(self):
        super(TheTVDB, self).__init__(SeriesProviderID.THETVDB)
        self.apikey = 'F9C450E78D99172E'
        self.trakt_id = 'tvdb'
        self.xem_origin = 'tvdb'
        self.icon = 'thetvdb16.png'
        self.show_url = 'http://thetvdb.com/?tab=series&id='
        self.dvd_order = False

        self.api = {
            'version': '3.0.0',
            'base': "https://api.thetvdb.com",
            'login': '/login',
            'refresh': '/refresh_token',
            'languages': '/languages',
            'languageInfo': '/languages/{id}',
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
        resp = self._request('get', self.api['refresh'])
        if resp and 'token' in resp:
            self.jwt_token = resp['token']

    def _login(self):
        resp = self._request('post', self.api['login'], json={'apikey': self.apikey})
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

    def _request(self, method, url, language='en', **kwargs):
        self.headers.update({'Authorization': 'Bearer {}'.format(self.jwt_token)})
        self.headers.update({'Content-type': 'application/json'})
        self.headers.update({'Accept-Language': language})
        self.headers.update({'Accept': 'application/vnd.thetvdb.v{}'.format(self.api['version'])})

        if not self.health:
            return None

        if sickrage.app.config.general.proxy_setting and sickrage.app.config.general.proxy_series_providers:
            proxy = sickrage.app.config.general.proxy_setting

        resp = WebSession(cache=self.cache).request(
            method, urljoin(self.api['base'], url), headers=self.headers,
            timeout=sickrage.app.config.general.series_provider_timeout, verify=False, **kwargs
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
                raise SeriesProviderNotAuthorized(resp.text)
            elif resp.status_code == 504:
                sickrage.app.log.debug("Unable to connect to TheTVDB")
                return None

            if 'application/json' in resp.headers.get('content-type', ''):
                err_msg = resp.json().get('Error', resp.text)
                sickrage.app.log.debug("Unable to get data from TheTVDB, Code: {code} Error: {err_msg!r}".format(code=resp.status_code, err_msg=err_msg))
                return None

    def _clean_data(self, data):
        """Cleans up strings returned by TheTVDB.com

        Issues corrected:
        - Replaces &amp; with &
        - Trailing whitespace
        """

        return data.replace("&amp;", "&").strip() if isinstance(data, str) else data

    @login_required
    def search(self, series, language='en', enable_cache=True):
        """This searches TheTVDB.com for the series by name, imdbid, or zap2itid
        and returns the result list
        """

        search_result = None

        if isinstance(series, int):
            if series in self.cache:
                if enable_cache:
                    search_result = self.cache[series]
            if not search_result:
                search_result = self._get_show_data(series, language=language)
        elif not re.search(r'tt\d+', series):
            sickrage.app.log.debug("Searching for show by name: {}".format(series))
            resp = self._request('get', self.api['getSeries'].format(name=quote(series), language=language))
            if resp and 'data' in resp:
                search_result = resp['data']
        else:
            sickrage.app.log.debug("Searching for show by imdbId: {}".format(series))
            resp = self._request('get', self.api['getSeriesIMDB'].format(id=series), language=language)
            if resp and 'data' in resp:
                if len(resp['data']) == 1:
                    search_result = resp['data'][0]

        if not search_result:
            sickrage.app.log.debug(f'Series search for {series} returned zero results, cannot find series on TheTVDB')

        return search_result

    @login_required
    def _get_show_data(self, sid, language='en'):
        """Takes a series ID, gets the episodes URL and parses the TVDB
        """

        languages = ['en']
        if language and language not in languages:
            languages.append(language)

        series_info = {}

        # Parse show information
        sickrage.app.log.debug('[{}]: Getting all series data from TheTVDB'.format(sid))

        for _language in languages:
            resp = self._request('get', self.api['series'].format(id=sid), language=_language)
            if not resp or 'data' not in resp:
                sickrage.app.log.debug("[{}]: Unable to locate show on TheTVDB".format(sid))
                return None

            series_info.update((k, v) for k, v in resp['data'].items() if v != '')

        # get series data
        for k, v in series_info.items():
            if v is not None:
                if k in ['banner', 'fanart', 'poster']:
                    v = self.api['images']['prefix'].format(value=v)
                elif isinstance(v, list):
                    v = '|'.join(v)
                else:
                    v = self._clean_data(v)

            self.cache.add_show_data(sid, k, v)

        # Parse episode data
        sickrage.app.log.debug('[{}]: Getting episode data from TheTVDB'.format(sid))

        episode_info = {}
        page = pages = 1

        while True:
            if page > pages:
                break

            for _language in languages:
                resp = self._request('get', self.api['episodes'].format(id=sid), language=_language, params={'page': page})
                if not resp or 'links' not in resp or 'data' not in resp:
                    break

                pages = resp['links']['last']

                for result in resp['data']:
                    if result['id'] not in episode_info:
                        episode_info[result['id']] = {}

                    episode_info[result['id']].update((k, v) for k, v in result.items() if v != '')

            page += 1

        if not len(episode_info):
            sickrage.app.log.debug('Series {} episodes incomplete on TheTVDB'.format(sid))
            return None

        episode_incomplete = False
        for cur_ep_id, cur_ep in episode_info.items():
            use_dvd = False

            if self.dvd_order:
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

                self.cache.add_item(sid, seas_no, ep_no, k, v)

            # add episode image url
            image_url = self.api['images']['prefix'].format(value='episodes/{}/{}.jpg'.format(sid, cur_ep['id']))
            self.cache.add_item(sid, seas_no, ep_no, 'filename', image_url)

        if episode_incomplete:
            sickrage.app.log.debug("{}: Series has incomplete season/episode numbers".format(sid))

        # set last updated
        self.cache.add_show_data(sid, 'last_updated', int(time.mktime(datetime.now().timetuple())))

        return self.cache[int(sid)]

    @login_required
    def image_key_types(self, sid, season=None, language='en'):
        key_types = {}

        resp = self._request('get', self.api['images']['params'].format(id=sid), language=language)
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
    def images(self, sid, key_type='poster', season=None, language='en'):
        sickrage.app.log.debug('Getting {} images for {}'.format(key_type, sid))

        images = []

        languages = ['en']
        if language and language not in languages:
            languages.append(language)

        for _language in languages:
            key_types = self.image_key_types(sid, season, _language)
            if not key_types or key_type not in key_types:
                continue

            if not season:
                resp = self._request('get', self.api['images'][key_type].format(id=sid), language=_language)
                if resp and 'data' in resp:
                    images = resp['data']
            else:
                resp = self._request('get', self.api['images'][key_type].format(id=sid, season=season), language=_language)
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
                v = (v, self.api['images']['prefix'].format(value=v))[k in ['filename', 'thumbnail']]
                images[i][k] = v

        return [item for item in sorted(images, key=itemgetter("score"), reverse=True)]

    @login_required
    def actors(self, sid):
        sickrage.app.log.debug("Getting actors for {}".format(sid))

        actors = TheTVDBActors()

        resp = self._request('get', self.api['actors'].format(id=sid))
        if not resp or 'data' not in resp:
            sickrage.app.log.debug('Actors result returned zero')
            return actors

        for cur_actor in resp['data']:
            actor = TheTVDBActor()
            for k, v in cur_actor.items():
                if not all([k, v]):
                    continue
                v = (v, self.api['images']['prefix'].format(value=v))[k == 'image']
                actor[k] = v

            actors.append(cur_actor)

        return actors

    @login_required
    def updated(self, fromTime):
        resp = self._request('get', self.api['updated'].format(time=fromTime))
        if resp and 'data' in resp:
            return resp['data']

    @login_required
    def languages(self):
        resp = self._request('get', self.api['languages'])
        if resp and 'data' in resp:
            return sorted(resp['data'], key=lambda i: i['englishname'])

    @login_required
    def language_info(self, lang_id):
        resp = self._request('get', self.api['languageInfo'].format(id=lang_id))
        if resp and 'data' in resp:
            return resp['data']

    @property
    def health(self):
        for i in range(3):
            try:
                health = requests.get(urljoin(self.api['base'], 'health'), verify=False, timeout=30).ok
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

    def __repr__(self):
        return repr(self.cache)
