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


import datetime
import threading
import time

import feedparser
from sqlalchemy import orm
from sqlalchemy.exc import IntegrityError

import sickrage
from sickrage.core.common import Quality, Qualities
from sickrage.core.databases.cache import CacheDB
from sickrage.core.enums import SeriesProviderID
from sickrage.core.exceptions import AuthException
from sickrage.core.helpers import show_names, try_int
from sickrage.core.nameparser import InvalidNameException, NameParser, InvalidShowException
from sickrage.core.tv.show.helpers import find_show
from sickrage.core.websession import WebSession


class TVCache(object):
    def __init__(self, provider, **kwargs):
        self.lock = threading.Lock()
        self.provider = provider
        self.providerID = self.provider.id
        self.min_time = kwargs.pop('min_time', 10)
        self.search_strings = kwargs.pop('search_strings', dict(RSS=['']))

    def clear(self):
        session = sickrage.app.cache_db.session()
        if self.shouldClearCache():
            session.query(CacheDB.Provider).filter_by(provider=self.providerID).delete()
            session.commit()

    def _get_title_and_url(self, item):
        return self.provider._get_title_and_url(item)

    def _get_result_stats(self, item):
        return self.provider._get_result_stats(item)

    def _get_size(self, item):
        return self.provider._get_size(item)

    def _get_rss_data(self):
        if self.search_strings:
            return {'entries': self.provider.search(self.search_strings)}

    def _check_auth(self, data):
        return True

    def check_item(self, title, url):
        return True

    def update(self, force=False):
        # check if we should update
        if self.should_update() or force:
            try:
                data = self._get_rss_data()
                if not self._check_auth(data):
                    return False

                # clear cache
                self.clear()

                # set updated
                self.last_update = datetime.datetime.today()

                [self._parseItem(item) for item in data['entries']]

                sickrage.app.log.debug("Updated RSS cache")
            except AuthException as e:
                sickrage.app.log.warning("Authentication error: {}".format(e))
                return False
            except Exception as e:
                sickrage.app.log.debug("Error while searching {}, skipping: {}".format(self.provider.name, repr(e)))
                return False

        return True

    def get_rss_feed(self, url, params=None):
        try:
            if self.provider.login():
                resp = WebSession().get(url, timeout=30, params=params)
                if resp:
                    return feedparser.parse(resp.text)
        except Exception as e:
            sickrage.app.log.debug("RSS Error: {}".format(e))

        return feedparser.FeedParserDict()

    def _translateTitle(self, title):
        return '' + title.replace(' ', '.')

    def _translateLinkURL(self, url):
        return url.replace('&amp;', '&')

    def _parseItem(self, item):
        title, url = self._get_title_and_url(item)
        seeders, leechers = self._get_result_stats(item)
        size = self._get_size(item)

        self.check_item(title, url)

        if title and url:
            self.add_cache_entry(self._translateTitle(title), self._translateLinkURL(url), seeders, leechers, size)
        else:
            sickrage.app.log.debug(
                "The data returned from the " + self.provider.name + " feed is incomplete, this result is unusable")

    @property
    def last_update(self):
        session = sickrage.app.cache_db.session()

        try:
            dbData = session.query(CacheDB.LastUpdate).filter_by(provider=self.providerID).one()
            lastTime = int(dbData.time)
            if lastTime > int(time.mktime(datetime.datetime.today().timetuple())):
                lastTime = 0
        except orm.exc.NoResultFound:
            lastTime = 0

        return datetime.datetime.fromtimestamp(lastTime)

    @last_update.setter
    def last_update(self, toDate):
        session = sickrage.app.cache_db.session()

        with self.lock:
            try:
                dbData = session.query(CacheDB.LastUpdate).filter_by(provider=self.providerID).one()
                dbData.time = int(time.mktime(toDate.timetuple()))
            except orm.exc.NoResultFound:
                session.add(CacheDB.LastUpdate(**{
                    'provider': self.providerID,
                    'time': int(time.mktime(toDate.timetuple()))
                }))
            finally:
                session.commit()

    @property
    def last_search(self):
        session = sickrage.app.cache_db.session()

        try:
            dbData = session.query(CacheDB.LastSearch).filter_by(provider=self.providerID).one()
            lastTime = int(dbData.time)
            if lastTime > int(time.mktime(datetime.datetime.today().timetuple())):
                lastTime = 0
        except orm.exc.NoResultFound:
            lastTime = 0

        return datetime.datetime.fromtimestamp(lastTime)

    @last_search.setter
    def last_search(self, toDate):
        session = sickrage.app.cache_db.session()

        with self.lock:
            try:
                dbData = session.query(CacheDB.LastSearch).filter_by(provider=self.providerID).one()
                dbData.time = int(time.mktime(toDate.timetuple()))
            except orm.exc.NoResultFound:
                session.add(CacheDB.LastSearch(**{
                    'provider': self.providerID,
                    'time': int(time.mktime(toDate.timetuple()))
                }))
            finally:
                session.commit()

    def should_update(self):
        # if we've updated recently then skip the update
        if datetime.datetime.today() - self.last_update < datetime.timedelta(minutes=self.min_time):
            return False
        return True

    def shouldClearCache(self):
        # if daily search hasn't used our previous results yet then don't clear the cache
        if self.last_update > self.last_search:
            return False
        return True

    def add_cache_entry(self, name, url, seeders, leechers, size):
        session = sickrage.app.cache_db.session()

        # check for existing entry in cache
        if session.query(CacheDB.Provider).filter_by(url=url).count():
            return

        try:
            # parse release name
            parse_result = NameParser(validate_show=True).parse(name)
            if parse_result.series_name and parse_result.quality != Qualities.UNKNOWN:
                season = parse_result.season_number if parse_result.season_number else 1
                episodes = parse_result.episode_numbers

                if season and episodes:
                    # store episodes as a seperated string
                    episode_text = "|" + "|".join(map(str, episodes)) + "|"

                    # get quality of release
                    quality = parse_result.quality

                    # get release group
                    release_group = parse_result.release_group

                    # get version
                    version = parse_result.version

                    dbData = {
                        'provider': self.providerID,
                        'name': name,
                        'season': season,
                        'episodes': episode_text,
                        'series_id': parse_result.series_id,
                        'series_provider_id': parse_result.series_provider_id.name,
                        'url': url,
                        'time': int(time.mktime(datetime.datetime.today().timetuple())),
                        'quality': quality,
                        'release_group': release_group,
                        'version': version,
                        'seeders': try_int(seeders),
                        'leechers': try_int(leechers),
                        'size': try_int(size, -1)
                    }

                    # add to internal database
                    try:
                        session.add(CacheDB.Provider(**dbData))
                        session.commit()
                        sickrage.app.log.debug("SEARCH RESULT:[{}] ADDED TO CACHE!".format(name))
                    except IntegrityError:
                        pass

                    # add to external provider cache database
                    if sickrage.app.config.general.enable_sickrage_api:
                        from sickrage.search_providers import SearchProviderType
                        if not self.provider.private and self.provider.provider_type in [SearchProviderType.NZB, SearchProviderType.TORRENT]:
                            try:
                                sickrage.app.api.provider.add_search_result(provider=self.providerID, data=dbData)
                            except Exception as e:
                                pass
        except (InvalidShowException, InvalidNameException):
            pass

    def search_cache(self, series_id, series_provider_id, season, episode, manualSearch=False, downCurQuality=False):
        cache_results = {}
        dbData = []

        # get data from external database
        if sickrage.app.config.general.enable_sickrage_api and not self.provider.private:
            resp = sickrage.app.api.provider.get_search_result(self.providerID, series_id, season, episode)
            if resp and 'data' in resp:
                dbData += resp['data']

        # get data from internal database
        session = sickrage.app.cache_db.session()
        dbData += [x.as_dict() for x in
                   session.query(CacheDB.Provider).filter_by(provider=self.providerID,
                                                             series_id=series_id,
                                                             season=season).filter(CacheDB.Provider.episodes.contains("|{}|".format(episode)))]

        for curResult in dbData:
            result = self.provider.get_result()

            result.series_id = int(curResult["series_id"])
            result.series_provider_id = curResult["series_provider_id"]

            # convert to series provider id enum
            if not isinstance(result.series_provider_id, SeriesProviderID):
                result.series_provider_id = SeriesProviderID[curResult["series_provider_id"]]

            # get series, if it's not one of our shows then ignore it
            series = find_show(result.series_id, result.series_provider_id)
            if not series or series.series_provider_id != series_provider_id:
                continue

            # ignored/required words, and non-tv junk
            if not show_names.filter_bad_releases(curResult["name"]):
                continue

            # skip if provider is anime only and show is not anime
            if self.provider.anime_only and not series.is_anime:
                sickrage.app.log.debug("" + str(series.name) + " is not an anime, skiping")
                continue

            # get season and ep data (ignoring multi-eps for now)
            curSeason = int(curResult["season"])
            if curSeason == -1:
                continue

            result.season = curSeason
            result.episodes = [int(curEp) for curEp in filter(None, curResult["episodes"].split("|"))]

            result.quality = Qualities(curResult["quality"])
            result.release_group = curResult["release_group"]
            result.version = curResult["version"]

            # make sure we want the episode
            wantEp = False
            for result_episode in result.episodes:
                if series.want_episode(result.season, result_episode, result.quality, manualSearch, downCurQuality):
                    wantEp = True

            if not wantEp:
                sickrage.app.log.info("Skipping " + curResult["name"] + " because we don't want an episode that's " + result.quality.display_name)
                continue

            # build a result object
            result.name = curResult["name"]
            result.url = curResult["url"]

            sickrage.app.log.info("Found cached {} result {}".format(result.provider_type, result.name))

            result.seeders = curResult.get("seeders", -1)
            result.leechers = curResult.get("leechers", -1)
            result.size = curResult.get("size", -1)
            result.content = None

            # add it to the list
            if episode not in cache_results:
                cache_results[int(episode)] = [result]
            else:
                cache_results[int(episode)] += [result]

        # datetime stamp this search so cache gets cleared
        self.last_search = datetime.datetime.today()

        return cache_results
