# Author: echel0n <sickrage.tv@gmail.com>
# URL: https://sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
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
import operator
import re
import threading
import traceback

from tornado import gen

import sickrage
from sickrage.core.common import DOWNLOADED, Quality, SNATCHED, SNATCHED_PROPER, \
    cpu_presets
from sickrage.core.databases import main_db
from sickrage.core.exceptions import AuthException
from sickrage.core.helpers import remove_non_release_groups
from sickrage.core.nameparser import InvalidNameException, InvalidShowException, \
    NameParser
from sickrage.core.search import pickBestResult, snatchEpisode
from sickrage.core.tv.show.history import History
from sickrage.providers import sortedProviderDict


class ProperSearcher(object):
    def __init__(self, *args, **kwargs):
        self.name = "PROPERSEARCHER"
        self.amActive = False

    def run(self, force=False):
        """
        Start looking for new propers
        :param force: Start even if already running (currently not used, defaults to False)
        """
        if self.amActive:
            return

        sickrage.LOGGER.info("Beginning the search for new propers")

        self.amActive = True

        propers = self._getProperList()

        if propers:
            self._downloadPropers(propers)

        self._set_lastProperSearch(datetime.datetime.today().toordinal())

        run_at = ""
        if None is sickrage.PROPERSEARCHER.start_time:
            run_in = sickrage.PROPERSEARCHER.lastRun + sickrage.PROPERSEARCHER.cycleTime - datetime.datetime.now()
            hours, remainder = divmod(run_in.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            run_at = ", next check in approx. " + (
                "%dh, %dm" % (hours, minutes) if 0 < hours else "%dm, %ds" % (minutes, seconds))

        sickrage.LOGGER.info("Completed the search for new propers%s" % run_at)

        self.amActive = False

    def _getProperList(self):
        """
        Walk providers for propers
        """
        propers = {}

        search_date = datetime.datetime.today() - datetime.timedelta(days=2)

        origThreadName = threading.currentThread().getName()

        # for each provider get a list of the
        for providerID, providerObj in {k: v for k, v in sortedProviderDict(sickrage.RANDOMIZE_PROVIDERS).items()
                                        if v.isActive}.items():

            threading.currentThread().setName(origThreadName + " :: [" + providerObj.name + "]")

            sickrage.LOGGER.info("Searching for any new PROPER releases from " + providerObj.name)

            try:
                curPropers = providerObj.findPropers(search_date)
            except AuthException as e:
                sickrage.LOGGER.debug("Authentication error: {}".format(e))
                continue
            except Exception as e:
                sickrage.LOGGER.debug("Error while searching " + providerObj.name + ", skipping: {}".format(e))
                sickrage.LOGGER.debug(traceback.format_exc())
                continue

            # if they haven't been added by a different provider than add the proper to the list
            for x in curPropers:
                if not re.search(r'(^|[\. _-])(proper|repack)([\. _-]|$)', x.name, re.I):
                    sickrage.LOGGER.debug('findPropers returned a non-proper, we have caught and skipped it.')
                    continue

                name = self._genericName(x.name)
                if not name in propers:
                    sickrage.LOGGER.debug("Found new proper: " + x.name)
                    x.provider = providerObj
                    propers[name] = x

            threading.currentThread().setName(origThreadName)

        # take the list of unique propers and get it sorted by
        sortedPropers = sorted(propers.values(), key=operator.attrgetter('date'), reverse=True)
        finalPropers = []

        for curProper in sortedPropers:

            try:
                myParser = NameParser(False)
                parse_result = myParser.parse(curProper.name)
            except InvalidNameException:
                sickrage.LOGGER.debug("Unable to parse the filename " + curProper.name + " into a valid episode")
                continue
            except InvalidShowException:
                sickrage.LOGGER.debug("Unable to parse the filename " + curProper.name + " into a valid show")
                continue

            if not parse_result.series_name:
                continue

            if not parse_result.episode_numbers:
                sickrage.LOGGER.debug(
                        "Ignoring " + curProper.name + " because it's for a full season rather than specific episode")
                continue

            sickrage.LOGGER.debug(
                    "Successful match! Result " + parse_result.original_name + " matched to show " + parse_result.show.name)

            # set the indexerid in the db to the show's indexerid
            curProper.indexerid = parse_result.show.indexerid

            # set the indexer in the db to the show's indexer
            curProper.indexer = parse_result.show.indexer

            # populate our Proper instance
            curProper.show = parse_result.show
            curProper.season = parse_result.season_number if parse_result.season_number is not None else 1
            curProper.episode = parse_result.episode_numbers[0]
            curProper.release_group = parse_result.release_group
            curProper.version = parse_result.version
            curProper.quality = Quality.nameQuality(curProper.name, parse_result.is_anime)
            curProper.content = None

            # filter release
            bestResult = pickBestResult(curProper, parse_result.show)
            if not bestResult:
                sickrage.LOGGER.debug("Proper " + curProper.name + " were rejected by our release filters.")
                continue

            # only get anime proper if it has release group and version
            if bestResult.show.is_anime:
                if not bestResult.release_group and bestResult.version == -1:
                    sickrage.LOGGER.debug("Proper " + bestResult.name + " doesn't have a release group and version, ignoring it")
                    continue

            # check if we actually want this proper (if it's the right quality)            
            sqlResults = main_db.MainDB().select(
                "SELECT status FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?",
                                     [bestResult.indexerid, bestResult.season, bestResult.episode])
            if not sqlResults:
                continue

            # only keep the proper if we have already retrieved the same quality ep (don't get better/worse ones)
            oldStatus, oldQuality = Quality.splitCompositeStatus(int(sqlResults[0][b"status"]))
            if oldStatus not in (DOWNLOADED, SNATCHED) or oldQuality != bestResult.quality:
                continue

            # check if we actually want this proper (if it's the right release group and a higher version)
            if bestResult.show.is_anime:
                sqlResults = main_db.MainDB().select(
                        "SELECT release_group, version FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?",
                        [bestResult.indexerid, bestResult.season, bestResult.episode])

                oldVersion = int(sqlResults[0][b"version"])
                oldRelease_group = (sqlResults[0][b"release_group"])

                if oldVersion > -1 and oldVersion < bestResult.version:
                    sickrage.LOGGER.info(
                        "Found new anime v" + str(bestResult.version) + " to replace existing v" + str(oldVersion))
                else:
                    continue

                if oldRelease_group != bestResult.release_group:
                    sickrage.LOGGER.info(
                        "Skipping proper from release group: " + bestResult.release_group + ", does not match existing release group: " + oldRelease_group)
                    continue

            # if the show is in our list and there hasn't been a proper already added for that particular episode then add it to our list of propers
            if bestResult.indexerid != -1 and (bestResult.indexerid, bestResult.season, bestResult.episode) not in map(
                    operator.attrgetter('indexerid', 'season', 'episode'), finalPropers):
                sickrage.LOGGER.info("Found a proper that we need: " + str(bestResult.name))
                finalPropers.append(bestResult)

        return finalPropers

    def _downloadPropers(self, properList):
        """
        Download proper (snatch it)

        :param properList:
        """

        for curProper in properList:

            historyLimit = datetime.datetime.today() - datetime.timedelta(days=30)

            # make sure the episode has been downloaded before
            historyResults = main_db.MainDB().select(
                    "SELECT resource FROM history " +
                    "WHERE showid = ? AND season = ? AND episode = ? AND quality = ? AND date >= ? " +
                    "AND action IN (" + ",".join([str(x) for x in Quality.SNATCHED + Quality.DOWNLOADED]) + ")",
                    [curProper.indexerid, curProper.season, curProper.episode, curProper.quality,
                     historyLimit.strftime(History.date_format)])

            # if we didn't download this episode in the first place we don't know what quality to use for the proper so we can't do it
            if len(historyResults) == 0:
                sickrage.LOGGER.info(
                        "Unable to find an original history entry for proper " + curProper.name + " so I'm not downloading it.")
                continue

            else:

                # make sure that none of the existing history downloads are the same proper we're trying to download
                clean_proper_name = self._genericName(remove_non_release_groups(curProper.name))
                isSame = False
                for curResult in historyResults:
                    # if the result exists in history already we need to skip it
                    if self._genericName(
                            remove_non_release_groups(curResult[b"resource"])) == clean_proper_name:
                        isSame = True
                        break
                if isSame:
                    sickrage.LOGGER.debug("This proper is already in history, skipping it")
                    continue

                # get the episode object
                epObj = curProper.show.getEpisode(curProper.season, curProper.episode)

                # make the result object
                result = curProper.provider.getResult([epObj])
                result.show = curProper.show
                result.url = curProper.url
                result.name = curProper.name
                result.quality = curProper.quality
                result.release_group = curProper.release_group
                result.version = curProper.version
                result.content = curProper.content

                # snatch it
                snatchEpisode(result, SNATCHED_PROPER)
                gen.sleep(cpu_presets[sickrage.CPU_PRESET])

    def _genericName(self, name):
        return name.replace(".", " ").replace("-", " ").replace("_", " ").lower()

    def _set_lastProperSearch(self, when):
        """
        Record last propersearch in DB

        :param when: When was the last proper search
        """

        sickrage.LOGGER.debug("Setting the last Proper search in the DB to " + str(when))

        sqlResults = main_db.MainDB().select("SELECT * FROM info")

        if len(sqlResults) == 0:
            main_db.MainDB().action("INSERT INTO info (last_backlog, last_indexer, last_proper_search) VALUES (?,?,?)",
                                    [0, 0, str(when)])
        else:
            main_db.MainDB().action("UPDATE info SET last_proper_search=" + str(when))

    @staticmethod
    def _get_lastProperSearch():
        """
        Find last propersearch from DB
        """

        sqlResults = main_db.MainDB().select("SELECT * FROM info")

        try:
            last_proper_search = datetime.date.fromordinal(int(sqlResults[0][b"last_proper_search"]))
        except:
            return datetime.date.fromordinal(1)

        return last_proper_search
