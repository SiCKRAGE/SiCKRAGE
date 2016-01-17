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
import io
import os
import re
import threading
import traceback

import sickrage
from sickrage.clients import getClientIstance
from sickrage.clients.nzbget_client import NZBGet
from sickrage.clients.sabnzbd_client import SabNZBd
from sickrage.core.common import Quality, SEASON_RESULT, SNATCHED_BEST, \
    SNATCHED_PROPER, SNATCHED, DOWNLOADED, WANTED, MULTI_EP_RESULT
from sickrage.core.databases import main_db
from sickrage.core.exceptions import AuthException
from sickrage.core.helpers import show_names, chmodAsParent
from sickrage.core.nzbSplitter import splitNZBResult
from sickrage.core.tv.show.history import FailedHistory, History
from sickrage.core.ui import notifications
from sickrage.notifiers import notify_snatch
from sickrage.providers import sortedProviderDict, GenericProvider


def _downloadResult(result):
    """
    Downloads a result to the appropriate black hole folder.

    :param result: SearchResult instance to download.
    :return: boolean, True on success
    """

    resProvider = result.provider
    if resProvider is None:
        sickrage.LOGGER.error("Invalid provider name - this is a coding error, report it please")
        return False

    # nzbs with an URL can just be downloaded from the provider
    if result.resultType == "nzb":
        newResult = resProvider.downloadResult(result)
    # if it's an nzb data result
    elif result.resultType == "nzbdata":

        # get the final file path to the nzb
        fileName = os.path.join(sickrage.NZB_DIR, result.name + ".nzb")

        sickrage.LOGGER.info("Saving NZB to " + fileName)

        newResult = True

        # save the data to disk
        try:
            with io.open(fileName, 'w') as fileOut:
                fileOut.write(result.extraInfo[0])

            chmodAsParent(fileName)

        except EnvironmentError as e:
            sickrage.LOGGER.error("Error trying to save NZB to black hole: {}".format(e))
            newResult = False
    elif resProvider.type == "torrent":
        newResult = resProvider.downloadResult(result)
    else:
        sickrage.LOGGER.error("Invalid provider type - this is a coding error, report it please")
        newResult = False

    return newResult


def snatchEpisode(result, endStatus=SNATCHED):
    """
    Contains the internal logic necessary to actually "snatch" a result that
    has been found.

    :param result: SearchResult instance to be snatched.
    :param endStatus: the episode status that should be used for the episode object once it's snatched.
    :return: boolean, True on success
    """

    if result is None:
        return False

    result.priority = 0  # -1 = low, 0 = normal, 1 = high
    if sickrage.ALLOW_HIGH_PRIORITY:
        # if it aired recently make it high priority
        for curEp in result.episodes:
            if datetime.date.today() - curEp.airdate <= datetime.timedelta(days=7):
                result.priority = 1
    if re.search(r'(^|[\. _-])(proper|repack)([\. _-]|$)', result.name, re.I) is not None:
        endStatus = SNATCHED_PROPER

    if result.url.startswith('magnet') or result.url.endswith('torrent'):
        result.resultType = 'torrent'

    # NZBs can be sent straight to SAB or saved to disk
    if result.resultType in ("nzb", "nzbdata"):
        if sickrage.NZB_METHOD == "blackhole":
            dlResult = _downloadResult(result)
        elif sickrage.NZB_METHOD == "sabnzbd":
            dlResult = SabNZBd.sendNZB(result)
        elif sickrage.NZB_METHOD == "nzbget":
            is_proper = True if endStatus == SNATCHED_PROPER else False
            dlResult = NZBGet.sendNZB(result, is_proper)
        else:
            sickrage.LOGGER.error("Unknown NZB action specified in config: " + sickrage.NZB_METHOD)
            dlResult = False

    # TORRENTs can be sent to clients or saved to disk
    elif result.resultType == "torrent":
        # torrents are saved to disk when blackhole mode
        if sickrage.TORRENT_METHOD == "blackhole":
            dlResult = _downloadResult(result)
        else:
            if not result.content and not result.url.startswith('magnet'):
                result.content = result.provider.getURL(result.url, needBytes=True)

            if result.content or result.url.startswith('magnet'):
                client = getClientIstance(sickrage.TORRENT_METHOD)()
                dlResult = client.sendTORRENT(result)
            else:
                sickrage.LOGGER.warning("Torrent file content is empty")
                dlResult = False
    else:
        sickrage.LOGGER.error("Unknown result type, unable to download it (%r)" % result.resultType)
        dlResult = False

    if not dlResult:
        return False

    if sickrage.USE_FAILED_DOWNLOADS:
        FailedHistory.logSnatch(result)

    notifications.message('Episode snatched', result.name)

    History.logSnatch(result)

    # don't notify when we re-download an episode
    sql_l = []
    trakt_data = []
    for curEpObj in result.episodes:
        with curEpObj.lock:
            if isFirstBestMatch(result):
                curEpObj.status = Quality.compositeStatus(SNATCHED_BEST, result.quality)
            else:
                curEpObj.status = Quality.compositeStatus(endStatus, result.quality)

            sql_l.append(curEpObj.get_sql())

        if curEpObj.status not in Quality.DOWNLOADED:
            try:
                notify_snatch(
                        curEpObj._format_pattern('%SN - %Sx%0E - %EN - %QN') + " from " + result.provider.name)
            except:
                sickrage.LOGGER.debug("Failed to send snatch notification")

            trakt_data.append((curEpObj.season, curEpObj.episode))

    data = sickrage.NOTIFIERS.trakt_notifier.trakt_episode_data_generate(trakt_data)

    if sickrage.USE_TRAKT and sickrage.TRAKT_SYNC_WATCHLIST:
        sickrage.LOGGER.debug("Add episodes, showid: indexerid " + str(result.show.indexerid) + ", Title " + str(
                result.show.name) + " to Traktv Watchlist")
        if data:
            sickrage.NOTIFIERS.trakt_notifier.update_watchlist(result.show, data_episode=data, update="add")

    if len(sql_l) > 0:
        main_db.MainDB().mass_action(sql_l)

    return True


def pickBestResult(results, show):
    """
    Find the best result out of a list of search results for a show

    :param results: list of result objects
    :param show: Shows we check for
    :return: best result object
    """
    results = results if isinstance(results, list) else [results]

    sickrage.LOGGER.debug("Picking the best result out of " + str([x.name for x in results]))

    bestResult = None

    # find the best result for the current episode
    for cur_result in results:
        if show and cur_result.show is not show:
            continue

        # build the black And white list
        if show.is_anime:
            if not show.release_groups.is_valid(cur_result):
                continue

        sickrage.LOGGER.info("Quality of " + cur_result.name + " is " + Quality.qualityStrings[cur_result.quality])

        anyQualities, bestQualities = Quality.splitQuality(show.quality)

        if cur_result.quality not in anyQualities + bestQualities:
            sickrage.LOGGER.debug(cur_result.name + " is a quality we know we don't want, rejecting it")
            continue

        if show.rls_ignore_words and show_names.containsAtLeastOneWord(cur_result.name,
                                                                       cur_result.show.rls_ignore_words):
            sickrage.LOGGER.info(
                    "Ignoring " + cur_result.name + " based on ignored words filter: " + show.rls_ignore_words)
            continue

        if show.rls_require_words and not show_names.containsAtLeastOneWord(cur_result.name,
                                                                            cur_result.show.rls_require_words):
            sickrage.LOGGER.info(
                    "Ignoring " + cur_result.name + " based on required words filter: " + show.rls_require_words)
            continue

        if not show_names.filterBadReleases(cur_result.name, parse=False):
            sickrage.LOGGER.info(
                    "Ignoring " + cur_result.name + " because its not a valid scene release that we want, ignoring it")
            continue

        if hasattr(cur_result, 'size'):
            if sickrage.USE_FAILED_DOWNLOADS and FailedHistory.hasFailed(cur_result.name, cur_result.size,
                                                                         cur_result.provider.name):
                sickrage.LOGGER.info(cur_result.name + " has previously failed, rejecting it")
                continue

        if not bestResult:
            bestResult = cur_result
        elif cur_result.quality in bestQualities and (
                        bestResult.quality < cur_result.quality or bestResult.quality not in bestQualities):
            bestResult = cur_result
        elif cur_result.quality in anyQualities and bestResult.quality not in bestQualities and bestResult.quality < cur_result.quality:
            bestResult = cur_result
        elif bestResult.quality == cur_result.quality:
            if "proper" in cur_result.name.lower() or "repack" in cur_result.name.lower():
                bestResult = cur_result
            elif "internal" in bestResult.name.lower() and "internal" not in cur_result.name.lower():
                bestResult = cur_result
            elif "xvid" in bestResult.name.lower() and "x264" in cur_result.name.lower():
                sickrage.LOGGER.info("Preferring " + cur_result.name + " (x264 over xvid)")
                bestResult = cur_result

    if bestResult:
        sickrage.LOGGER.debug("Picked " + bestResult.name + " as the best")
    else:
        sickrage.LOGGER.debug("No result picked.")

    return bestResult


def isFinalResult(result):
    """
    Checks if the given result is good enough quality that we can stop searching for other ones.

    If the result is the highest quality in both the any/best quality lists then this function
    returns True, if not then it's False
    """

    sickrage.LOGGER.debug("Checking if we should keep searching after we've found " + result.name)

    show_obj = result.episodes[0].show

    any_qualities, best_qualities = Quality.splitQuality(show_obj.quality)

    # if there is a redownload that's higher than this then we definitely need to keep looking
    if best_qualities and result.quality < max(best_qualities):
        return False

    # if it does not match the shows black and white list its no good
    elif show_obj.is_anime and show_obj.release_groups.is_valid(result):
        return False

    # if there's no redownload that's higher (above) and this is the highest initial download then we're good
    elif any_qualities and result.quality in any_qualities:
        return True

    elif best_qualities and result.quality == max(best_qualities):
        return True

    # if we got here than it's either not on the lists, they're empty, or it's lower than the highest required
    else:
        return False


def isFirstBestMatch(result):
    """
    Checks if the given result is a best quality match and if we want to archive the episode on first match.
    """

    sickrage.LOGGER.debug("Checking if we should archive our first best quality match for for episode " + result.name)

    show_obj = result.episodes[0].show

    any_qualities, best_qualities = Quality.splitQuality(show_obj.quality)

    # if there is a redownload that's a match to one of our best qualities and we want to archive the episode then we are done
    if best_qualities and show_obj.archive_firstmatch and result.quality in best_qualities:
        return True

    return False


def wantedEpisodes(show, fromDate):
    """
    Get a list of episodes that we want to download
    :param show: Show these episodes are from
    :param fromDate: Search from a certain date
    :return: list of wanted episodes
    """

    anyQualities, bestQualities = Quality.splitQuality(show.quality)  # @UnusedVariable
    allQualities = list(set(anyQualities + bestQualities))

    sickrage.LOGGER.debug("Seeing if we need anything from " + show.name)

    sqlResults = main_db.MainDB().select(
            "SELECT status, season, episode FROM tv_episodes WHERE showid = ? AND season > 0 AND airdate > ?",
            [show.indexerid, fromDate.toordinal()])

    # check through the list of statuses to see if we want any
    wanted = []
    for result in sqlResults:
        curCompositeStatus = int(result[b"status"] or -1)
        curStatus, curQuality = Quality.splitCompositeStatus(curCompositeStatus)

        if bestQualities:
            highestBestQuality = max(allQualities)
        else:
            highestBestQuality = 0

        # if we need a better one then say yes
        if (curStatus in (DOWNLOADED, SNATCHED,
                          SNATCHED_PROPER) and curQuality < highestBestQuality) or curStatus == WANTED:
            epObj = show.getEpisode(int(result[b"season"]), int(result[b"episode"]))
            epObj.wantedQuality = [i for i in allQualities if (i > curQuality and i != Quality.UNKNOWN)]
            wanted.append(epObj)

    return wanted


def searchForNeededEpisodes():
    """
    Check providers for details on wanted episodes

    :return: episodes we have a search hit for
    """
    foundResults = {}

    origThreadName = threading.currentThread().getName()

    fromDate = datetime.date.fromordinal(1)
    episodes = []

    with threading.Lock():
        for curShow in sickrage.showList:
            if not curShow.paused:
                episodes.extend(wantedEpisodes(curShow, fromDate))

    # list of providers
    providers = {k: v for k, v in sortedProviderDict(sickrage.RANDOMIZE_PROVIDERS).items() if v.isActive}

    # perform provider searchers
    def perform_searches():
        didSearch = False
        for providerID, providerObj in providers.items():
            threading.currentThread().setName(origThreadName + "::[" + providerObj.name + "]")

            try:
                providerObj.cache.updateCache()
                curFoundResults = dict(providerObj.searchRSS(episodes))
            except AuthException as e:
                sickrage.LOGGER.error("Authentication error: {}".format(e))
                return
            except Exception as e:
                sickrage.LOGGER.error("Error while searching " + providerObj.name + ", skipping: {}".format(e))
                sickrage.LOGGER.debug(traceback.format_exc())
                return

            didSearch = True

            # pick a single result for each episode, respecting existing results
            for curEp in curFoundResults:
                if not curEp.show or curEp.show.paused:
                    sickrage.LOGGER.debug("Skipping %s because the show is paused " % curEp.prettyName())
                    continue

                bestResult = pickBestResult(curFoundResults[curEp], curEp.show)

                # if all results were rejected move on to the next episode
                if not bestResult:
                    sickrage.LOGGER.debug("All found results for " + curEp.prettyName() + " were rejected.")
                    continue

                # if it's already in the list (from another provider) and the newly found quality is no better then skip it
                if curEp in foundResults and bestResult.quality <= foundResults[curEp].quality:
                    continue

                foundResults[curEp] = bestResult

        if not didSearch:
            sickrage.LOGGER.warning(
                    "No NZB/Torrent providers found or enabled in the sickrage config for daily searches. Please check your settings.")

        return foundResults.values()
    return perform_searches()

def searchProviders(show, episodes, manualSearch=False, downCurQuality=False):
    """
    Walk providers for information on shows

    :param show: Show we are looking for
    :param episodes: Episodes we hope to find
    :param manualSearch: Boolean, is this a manual search?
    :param downCurQuality: Boolean, should we redownload currently avaialble quality file
    :return: results for search
    """
    foundResults = {}

    # build name cache for show
    sickrage.NAMECACHE.buildNameCache(show)

    origThreadName = threading.currentThread().getName()

    providers = {k: v for k, v in sortedProviderDict(sickrage.RANDOMIZE_PROVIDERS).items() if v.isActive}

    def perform_searches():

        finalResults = []
        didSearch = False

        for providerID, providerObj in providers.items():
            if providerObj.anime_only and not show.is_anime:
                sickrage.LOGGER.debug("" + str(show.name) + " is not an anime, skiping")
                continue

            threading.currentThread().setName(origThreadName + "::[" + providerObj.name + "]")

            foundResults[providerObj.name] = {}

            searchCount = 0
            search_mode = providerObj.search_mode

            # Always search for episode when manually searching when in sponly
            if search_mode == 'sponly' and manualSearch == True:
                search_mode = 'eponly'

            while True:
                searchCount += 1

                if search_mode == 'eponly':
                    sickrage.LOGGER.info("Performing episode search for " + show.name)
                else:
                    sickrage.LOGGER.info("Performing season pack search for " + show.name)

                try:
                    providerObj.cache.updateCache()
                    searchResults = providerObj.findSearchResults(show, episodes, search_mode, manualSearch, downCurQuality)
                except AuthException as e:
                    sickrage.LOGGER.error("Authentication error: {}".format(e))
                    break
                except Exception as e:
                    sickrage.LOGGER.error("Error while searching " + providerObj.name + ", skipping: {}".format(e))
                    sickrage.LOGGER.debug(traceback.format_exc())
                    break

                didSearch = True

                if len(searchResults):
                    # make a list of all the results for this provider
                    for curEp in searchResults:
                        if curEp in foundResults:
                            foundResults[providerObj.name][curEp] += searchResults[curEp]
                        else:
                            foundResults[providerObj.name][curEp] = searchResults[curEp]

                    break
                elif not providerObj.search_fallback or searchCount == 2:
                    break

                if search_mode == 'sponly':
                    sickrage.LOGGER.debug("Fallback episode search initiated")
                    search_mode = 'eponly'
                else:
                    sickrage.LOGGER.debug("Fallback season pack search initiate")
                    search_mode = 'sponly'

            # skip to next provider if we have no results to process
            if not len(foundResults[providerObj.name]):
                continue

            # pick the best season NZB
            bestSeasonResult = None
            if SEASON_RESULT in foundResults[providerObj.name]:
                bestSeasonResult = pickBestResult(foundResults[providerObj.name][SEASON_RESULT], show)

            highest_quality_overall = 0
            for cur_episode in foundResults[providerObj.name]:
                for cur_result in foundResults[providerObj.name][cur_episode]:
                    if cur_result.quality != Quality.UNKNOWN and cur_result.quality > highest_quality_overall:
                        highest_quality_overall = cur_result.quality
            sickrage.LOGGER.debug("The highest quality of any match is " + Quality.qualityStrings[highest_quality_overall])

            # see if every episode is wanted
            if bestSeasonResult:
                searchedSeasons = [str(x.season) for x in episodes]

                # get the quality of the season nzb
                seasonQual = bestSeasonResult.quality
                sickrage.LOGGER.debug(
                        "The quality of the season " + bestSeasonResult.provider.type + " is " +
                        Quality.qualityStrings[
                            seasonQual])

                allEps = [int(x[b"episode"])
                          for x in main_db.MainDB().select(
                            "SELECT episode FROM tv_episodes WHERE showid = ? AND ( season IN ( " + ','.join(
                                    searchedSeasons) + " ) )",
                            [show.indexerid])]

                sickrage.LOGGER.info(
                        "Executed query: [SELECT episode FROM tv_episodes WHERE showid = %s AND season in  %s]" % (
                            show.indexerid, ','.join(searchedSeasons)))
                sickrage.LOGGER.debug("Episode list: " + str(allEps))

                allWanted = True
                anyWanted = False
                for curEpNum in allEps:
                    for season in set([x.season for x in episodes]):
                        if not show.wantEpisode(season, curEpNum, seasonQual, downCurQuality):
                            allWanted = False
                        else:
                            anyWanted = True

                # if we need every ep in the season and there's nothing better then just download this and be done with it (unless single episodes are preferred)
                if allWanted and bestSeasonResult.quality == highest_quality_overall:
                    sickrage.LOGGER.info(
                            "Every ep in this season is needed, downloading the whole " + bestSeasonResult.provider.type + " " + bestSeasonResult.name)
                    epObjs = []
                    for curEpNum in allEps:
                        for season in set([x.season for x in episodes]):
                            epObjs.append(show.getEpisode(season, curEpNum))
                    bestSeasonResult.episodes = epObjs

                    return [bestSeasonResult]

                elif not anyWanted:
                    sickrage.LOGGER.debug(
                            "No eps from this season are wanted at this quality, ignoring the result of " + bestSeasonResult.name)

                else:

                    if bestSeasonResult.provider.type == GenericProvider.NZB:
                        sickrage.LOGGER.debug("Breaking apart the NZB and adding the individual ones to our results")

                        # if not, break it apart and add them as the lowest priority results
                        individualResults = splitNZBResult(bestSeasonResult)
                        for curResult in individualResults:
                            if len(curResult.episodes) == 1:
                                epNum = curResult.episodes[0].episode
                            elif len(curResult.episodes) > 1:
                                epNum = MULTI_EP_RESULT

                            if epNum in foundResults[providerObj.name]:
                                foundResults[providerObj.name][epNum].append(curResult)
                            else:
                                foundResults[providerObj.name][epNum] = [curResult]

                    # If this is a torrent all we can do is leech the entire torrent, user will have to select which eps not do download in his torrent client
                    else:

                        # Season result from Torrent Provider must be a full-season torrent, creating multi-ep result for it.
                        sickrage.LOGGER.info(
                                "Adding multi-ep result for full-season torrent. Set the episodes you don't want to 'don't download' in your torrent client if desired!")
                        epObjs = []
                        for curEpNum in allEps:
                            for season in set([x.season for x in episodes]):
                                epObjs.append(show.getEpisode(season, curEpNum))
                        bestSeasonResult.episodes = epObjs

                        if MULTI_EP_RESULT in foundResults[providerObj.name]:
                            foundResults[providerObj.name][MULTI_EP_RESULT].append(bestSeasonResult)
                        else:
                            foundResults[providerObj.name][MULTI_EP_RESULT] = [bestSeasonResult]

            # go through multi-ep results and see if we really want them or not, get rid of the rest
            multiResults = {}
            if MULTI_EP_RESULT in foundResults[providerObj.name]:
                for _multiResult in foundResults[providerObj.name][MULTI_EP_RESULT]:

                    sickrage.LOGGER.debug("Seeing if we want to bother with multi-episode result " + _multiResult.name)

                    # Filter result by ignore/required/whitelist/blacklist/quality, etc
                    multiResult = pickBestResult(_multiResult, show)
                    if not multiResult:
                        continue

                    # see how many of the eps that this result covers aren't covered by single results
                    neededEps = []
                    notNeededEps = []
                    for epObj in multiResult.episodes:
                        # if we have results for the episode
                        if epObj.episode in foundResults[providerObj.name] and len(
                                foundResults[providerObj.name][epObj.episode]) > 0:
                            notNeededEps.append(epObj.episode)
                        else:
                            neededEps.append(epObj.episode)

                    sickrage.LOGGER.debug(
                            "Single-ep check result is neededEps: " + str(neededEps) + ", notNeededEps: " + str(
                                    notNeededEps))

                    if not neededEps:
                        sickrage.LOGGER.debug(
                                "All of these episodes were covered by single episode results, ignoring this multi-episode result")
                        continue

                    # check if these eps are already covered by another multi-result
                    multiNeededEps = []
                    multiNotNeededEps = []
                    for epObj in multiResult.episodes:
                        if epObj.episode in multiResults:
                            multiNotNeededEps.append(epObj.episode)
                        else:
                            multiNeededEps.append(epObj.episode)

                    sickrage.LOGGER.debug(
                            "Multi-ep check result is multiNeededEps: " + str(
                                    multiNeededEps) + ", multiNotNeededEps: " + str(
                                    multiNotNeededEps))

                    if not multiNeededEps:
                        sickrage.LOGGER.debug(
                                "All of these episodes were covered by another multi-episode nzbs, ignoring this multi-ep result")
                        continue

                    # don't bother with the single result if we're going to get it with a multi result
                    for epObj in multiResult.episodes:
                        multiResults[epObj.episode] = multiResult
                        if epObj.episode in foundResults[providerObj.name]:
                            sickrage.LOGGER.debug(
                                    "A needed multi-episode result overlaps with a single-episode result for ep #" + str(
                                            epObj.episode) + ", removing the single-episode results from the list")
                            del foundResults[providerObj.name][epObj.episode]

            # of all the single ep results narrow it down to the best one for each episode
            finalResults += set(multiResults.values())
            for curEp in foundResults[providerObj.name]:
                if curEp in (MULTI_EP_RESULT, SEASON_RESULT):
                    continue

                if not len(foundResults[providerObj.name][curEp]) > 0:
                    continue

                # if all results were rejected move on to the next episode
                bestResult = pickBestResult(foundResults[providerObj.name][curEp], show)
                if not bestResult:
                    continue

                # add result if its not a duplicate and
                found = False
                for i, result in enumerate(finalResults):
                    for bestResultEp in bestResult.episodes:
                        if bestResultEp in result.episodes:
                            if result.quality < bestResult.quality:
                                finalResults.pop(i)
                            else:
                                found = True
                if not found:
                    finalResults += [bestResult]

            # check that we got all the episodes we wanted first before doing a match and snatch
            wantedEpCount = 0
            for wantedEp in episodes:
                for result in finalResults:
                    if wantedEp in result.episodes and isFinalResult(result):
                        wantedEpCount += 1

            # make sure we search every provider for results unless we found everything we wanted
            if wantedEpCount == len(episodes):
                break

        if not didSearch:
            sickrage.LOGGER.warning(
                    "No NZB/Torrent providers found or enabled in the sickrage config for backlog searches. Please check your settings.")

        return finalResults
    return perform_searches()