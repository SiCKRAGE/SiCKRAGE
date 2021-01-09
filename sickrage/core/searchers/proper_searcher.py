# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import datetime
import operator
import re
import threading
import time
import traceback

from sqlalchemy import orm

import sickrage
from sickrage.core.common import Quality, EpisodeStatus
from sickrage.core.databases.main import MainDB
from sickrage.core.exceptions import AuthException
from sickrage.core.helpers import remove_non_release_groups, flatten
from sickrage.core.nameparser import InvalidNameException, InvalidShowException, NameParser
from sickrage.core.search import pick_best_result, snatch_episode
from sickrage.core.tv.show.helpers import find_show, get_show_list
from sickrage.search_providers import NZBProvider, NewznabProvider, TorrentProvider, TorrentRssProvider


class ProperSearcher(object):
    def __init__(self, *args, **kwargs):
        self.name = "PROPERSEARCHER"
        self.running = False

    def task(self, force=False):
        """
        Start looking for new propers
        :param force: Start even if already running (currently not used, defaults to False)
        """
        if self.running or not sickrage.app.config.general.download_propers:
            return

        try:
            self.running = True

            # set thread name
            threading.currentThread().setName(self.name)

            sickrage.app.log.info("Beginning the search for new propers")

            propers = self._get_proper_list()
            if propers:
                self._download_propers(propers)
            else:
                sickrage.app.log.info('No recently aired episodes, no propers to search for')

            sickrage.app.log.info("Completed the search for new propers")
        finally:
            self.running = False

    def _get_proper_list(self):
        """
        Walk providers for propers
        """

        session = sickrage.app.main_db.session()

        propers = {}
        final_propers = []

        search_date = datetime.datetime.today() - datetime.timedelta(days=2)

        orig_thread_name = threading.currentThread().getName()

        for show in get_show_list():
            wanted = self._get_wanted(show, search_date)
            if not wanted:
                sickrage.app.log.debug("Nothing needs to be downloaded for {}, skipping".format(show.name))
                continue

            self._lastProperSearch = self._get_last_proper_search(show.series_id, show.series_provider_id)

            # for each provider get a list of the
            for providerID, providerObj in sickrage.app.search_providers.sort(randomize=sickrage.app.config.general.randomize_providers).items():
                # check provider type and provider is enabled
                if not sickrage.app.config.general.use_nzbs and providerObj.provider_type in [NZBProvider.provider_type, NewznabProvider.provider_type]:
                    continue
                elif not sickrage.app.config.general.use_torrents and providerObj.provider_type in [TorrentProvider.provider_type, TorrentRssProvider.provider_type]:
                    continue
                elif not providerObj.is_enabled:
                    continue

                threading.currentThread().setName(orig_thread_name + " :: [" + providerObj.name + "]")

                sickrage.app.log.info("Searching for any new PROPER releases from " + providerObj.name)

                try:
                    for season, episode in wanted:
                        for x in providerObj.find_propers(show.series_id, show.series_provider_id, season, episode):
                            if not re.search(r'(^|[. _-])(proper|repack)([. _-]|$)', x.name, re.I):
                                sickrage.app.log.debug('Found a non-proper, we have caught and skipped it.')
                                continue

                            name = self._generic_name(x.name)
                            if name not in propers:
                                sickrage.app.log.debug("Found new proper: " + x.name)
                                x.provider = providerObj
                                propers[name] = x
                except AuthException as e:
                    sickrage.app.log.warning("Authentication error: {}".format(e))
                    continue
                except Exception as e:
                    sickrage.app.log.debug("Error while searching " + providerObj.name + ", skipping: {}".format(e))
                    sickrage.app.log.debug(traceback.format_exc())
                    continue

                threading.currentThread().setName(orig_thread_name)

            self._set_last_proper_search(show.series_id, show.series_provider_id, datetime.datetime.now())

        # take the list of unique propers and get it sorted by
        sorted_propers = sorted(propers.values(), key=operator.attrgetter('date'), reverse=True)
        for curProper in sorted_propers:
            try:
                parse_result = NameParser(False).parse(curProper.name)
            except InvalidNameException:
                sickrage.app.log.debug("Unable to parse the filename " + curProper.name + " into a valid episode")
                continue
            except InvalidShowException:
                sickrage.app.log.debug("Unable to parse the filename " + curProper.name + " into a valid show")
                continue

            if not parse_result.series_name:
                continue

            if not parse_result.episode_numbers:
                sickrage.app.log.debug("Ignoring " + curProper.name + " because it's for a full season rather than specific episode")
                continue

            show = find_show(parse_result.series_id, parse_result.series_provider_id)
            sickrage.app.log.debug("Successful match! Result " + parse_result.original_name + " matched to show " + show.name)

            # set the series_id in the db to the show's series_id
            curProper.series_id = parse_result.series_id

            # set the series_provider_id in the db to the show's series_provider_id
            curProper.series_provider_id = show.series_provider_id

            # populate our Proper instance
            curProper.season = parse_result.season_number if parse_result.season_number is not None else 1
            curProper.episode = parse_result.episode_numbers[0]
            curProper.release_group = parse_result.release_group
            curProper.version = parse_result.version
            curProper.quality = Quality.name_quality(curProper.name, parse_result.is_anime)
            curProper.content = None

            # filter release
            best_result = pick_best_result(curProper)
            if not best_result:
                sickrage.app.log.debug("Proper " + curProper.name + " were rejected by our release filters.")
                continue

            # only get anime proper if it has release group and version
            if show.is_anime:
                if not best_result.release_group and best_result.version == -1:
                    sickrage.app.log.debug("Proper " + best_result.name + " doesn't have a release group and version, ignoring it")
                    continue

            # check if we actually want this proper (if it's the right quality)            
            dbData = session.query(MainDB.TVEpisode).filter_by(series_id=best_result.series_id, season=best_result.season,
                                                               episode=best_result.episode).one_or_none()
            if not dbData:
                continue

            # only keep the proper if we have already retrieved the same quality ep (don't get better/worse ones)
            old_status, old_quality = Quality.split_composite_status(int(dbData.status))
            if old_status not in (EpisodeStatus.DOWNLOADED, EpisodeStatus.SNATCHED) or old_quality != best_result.quality:
                continue

            # check if we actually want this proper (if it's the right release group and a higher version)
            if show.is_anime:
                old_version = int(dbData.version)
                old_release_group = dbData.release_group
                if not -1 < old_version < best_result.version:
                    continue

                sickrage.app.log.info("Found new anime v" + str(best_result.version) + " to replace existing v" + str(old_version))

                if old_release_group != best_result.release_group:
                    sickrage.app.log.info("Skipping proper from release group: {}, does not match existing release "
                                          "group: {}".format(best_result.release_group, old_release_group))
                    continue

            # if the show is in our list and there hasn't been a proper already added for that particular episode
            # then add it to our list of propers
            if best_result.series_id != -1 and (best_result.series_id, best_result.season, best_result.episode) not in map(
                    operator.attrgetter('series_id', 'season', 'episode'), final_propers):
                sickrage.app.log.info("Found a proper that we need: " + str(best_result.name))
                final_propers.append(best_result)

        return final_propers

    def _get_wanted(self, show, search_date):
        session = sickrage.app.main_db.session()

        wanted = []

        for result in session.query(MainDB.TVEpisode).filter_by(series_id=show.series_id).filter(MainDB.TVEpisode.airdate >= search_date,
                                                                                                 MainDB.TVEpisode.status.in_(flatten(
                                                                                                         [EpisodeStatus.composites(EpisodeStatus.DOWNLOADED),
                                                                                                          EpisodeStatus.composites(EpisodeStatus.SNATCHED),
                                                                                                          EpisodeStatus.composites(
                                                                                                                  EpisodeStatus.SNATCHED_BEST)]))):
            wanted += [(result.season, result.episode)]

        return wanted

    def _download_propers(self, proper_list):
        """
        Download proper (snatch it)

        :param proper_list:
        """

        session = sickrage.app.main_db.session()

        for curProper in proper_list:
            history_limit = datetime.datetime.today() - datetime.timedelta(days=30)

            # make sure the episode has been downloaded before
            history_results = [x for x in
                               session.query(MainDB.History).filter_by(series_id=curProper.series_id, season=curProper.season, episode=curProper.episode,
                                                                       quality=curProper.quality).filter(MainDB.History.date >= history_limit,
                                                                                                         MainDB.History.action.in_(flatten(
                                                                                                             [EpisodeStatus.composites(EpisodeStatus.SNATCHED),
                                                                                                              EpisodeStatus.composites(
                                                                                                                  EpisodeStatus.DOWNLOADED)])))]

            # if we didn't download this episode in the first place we don't know what quality to use for the proper
            # so we can't do it
            if len(history_results) == 0:
                sickrage.app.log.info("Unable to find an original history entry for proper {} so I'm not downloading "
                                      "it.".format(curProper.name))
                continue

            # make sure that none of the existing history downloads are the same proper we're trying to download
            is_same = False
            clean_proper_name = self._generic_name(remove_non_release_groups(curProper.name))

            for curResult in history_results:
                # if the result exists in history already we need to skip it
                if self._generic_name(
                        remove_non_release_groups(curResult.resource)) == clean_proper_name:
                    is_same = True
                    break

            if is_same:
                sickrage.app.log.debug("This proper is already in history, skipping it")
                continue

            # make the result object
            result = curProper.provider.get_result(curProper.season, [curProper.episode])
            result.series_id = curProper.series_id
            result.url = curProper.url
            result.name = curProper.name
            result.quality = curProper.quality
            result.release_group = curProper.release_group
            result.version = curProper.version
            result.seeders = curProper.seeders
            result.leechers = curProper.leechers
            result.size = curProper.size
            result.files = curProper.files
            result.content = curProper.content

            # snatch it
            snatch_episode(result, EpisodeStatus.SNATCHED_PROPER)
            time.sleep(sickrage.app.config.general.cpu_preset.value)

    def _generic_name(self, name):
        return name.replace(".", " ").replace("-", " ").replace("_", " ").lower()

    def _set_last_proper_search(self, series_id, series_provider_id, when):
        """
        Record last propersearch in DB

        :param when: When was the last proper search
        """

        sickrage.app.log.debug("Setting the last proper search in database to " + str(when))

        try:
            show = find_show(series_id, series_provider_id)
            show.last_proper_search = when
            show.save()
        except orm.exc.NoResultFound:
            pass

    def _get_last_proper_search(self, series_id, series_provider_id):
        """
        Find last propersearch from DB
        """

        sickrage.app.log.debug("Retrieving the last check time from the DB")

        try:
            show = find_show(series_id, series_provider_id)
            return show.last_proper_search
        except orm.exc.NoResultFound:
            return 1
