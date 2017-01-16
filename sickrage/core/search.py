# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
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

import io
import os
import re
import threading
from datetime import date, timedelta

import sickrage
from sickrage.clients import getClientIstance
from sickrage.clients.nzbget import NZBGet
from sickrage.clients.sabnzbd import SabNZBd
from sickrage.core.common import Quality, SEASON_RESULT, SNATCHED_BEST, \
    SNATCHED_PROPER, SNATCHED, DOWNLOADED, WANTED, MULTI_EP_RESULT, video_exts
from sickrage.core.exceptions import AuthException
from sickrage.core.helpers import show_names, chmodAsParent
from sickrage.core.nzbSplitter import splitNZBResult
from sickrage.core.tv.show.history import FailedHistory, History
from sickrage.notifiers import srNotifiers
from sickrage.providers import NZBProvider, NewznabProvider, TorrentProvider, TorrentRssProvider


def _downloadResult(result):
    """
    Downloads a result to the appropriate black hole folder.

    :param result: SearchResult instance to download.
    :return: boolean, True on success
    """

    resProvider = result.provider
    if resProvider is None:
        sickrage.srCore.srLogger.error("Invalid provider name - this is a coding error, report it please")
        return False

    # nzbs with an URL can just be downloaded from the provider
    if result.resultType == "nzb":
        newResult = resProvider.downloadResult(result)
    # if it's an nzb data result
    elif result.resultType == "nzbdata":

        # get the final file path to the nzb
        fileName = os.path.join(sickrage.srCore.srConfig.NZB_DIR, result.name + ".nzb")

        sickrage.srCore.srLogger.info("Saving NZB to " + fileName)

        newResult = True

        # save the data to disk
        try:
            with io.open(fileName, 'w') as fileOut:
                fileOut.write(result.extraInfo[0])

            chmodAsParent(fileName)

        except EnvironmentError as e:
            sickrage.srCore.srLogger.error("Error trying to save NZB to black hole: {}".format(e.message))
            newResult = False
    elif resProvider.type == "torrent":
        newResult = resProvider.downloadResult(result)
    else:
        sickrage.srCore.srLogger.error("Invalid provider type - this is a coding error, report it please")
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
    if sickrage.srCore.srConfig.ALLOW_HIGH_PRIORITY:
        # if it aired recently make it high priority
        for curEp in result.episodes:
            if date.today() - curEp.airdate <= timedelta(days=7):
                result.priority = 1

    if re.search(r'(^|[\. _-])(proper|repack)([\. _-]|$)', result.name, re.I) is not None:
        endStatus = SNATCHED_PROPER

    if result.url.startswith('magnet') or result.url.endswith('torrent'):
        result.resultType = 'torrent'

    dlResult = False
    if result.resultType in ("nzb", "nzbdata"):
        if sickrage.srCore.srConfig.NZB_METHOD == "blackhole":
            dlResult = _downloadResult(result)
        elif sickrage.srCore.srConfig.NZB_METHOD == "sabnzbd":
            dlResult = SabNZBd.sendNZB(result)
        elif sickrage.srCore.srConfig.NZB_METHOD == "nzbget":
            is_proper = True if endStatus == SNATCHED_PROPER else False
            dlResult = NZBGet.sendNZB(result, is_proper)
        else:
            sickrage.srCore.srLogger.error(
                "Unknown NZB action specified in config: " + sickrage.srCore.srConfig.NZB_METHOD)
    elif result.resultType == "torrent":
        if sickrage.srCore.srConfig.TORRENT_METHOD == "blackhole":
            dlResult = _downloadResult(result)
        else:
            if all([not result.content, not result.url.startswith('magnet:')]):
                result.content = sickrage.srCore.srWebSession.get(result.url).content

            if any([result.content, result.url.startswith('magnet:')]):
                # add public trackers to magnet url for non-private torrent providers
                if not result.provider.private and result.url.startswith('magnet:'):
                    result.url += '&tr='.join(
                        [x.strip() for x in sickrage.srCore.srConfig.TORRENT_TRACKERS.split(',') if x.strip()])

                client = getClientIstance(sickrage.srCore.srConfig.TORRENT_METHOD)()
                dlResult = client.sendTORRENT(result)
            else:
                sickrage.srCore.srLogger.warning("Torrent file content is empty")
    else:
        sickrage.srCore.srLogger.error("Unknown result type, unable to download it (%r)" % result.resultType)

    # no download results found
    if not dlResult:
        return False

    if sickrage.srCore.srConfig.USE_FAILED_DOWNLOADS:
        FailedHistory.logSnatch(result)

    sickrage.srCore.srNotifications.message('Episode snatched', result.name)

    History.logSnatch(result)

    # don't notify when we re-download an episode
    trakt_data = []
    for curEpObj in result.episodes:
        with curEpObj.lock:
            if isFirstBestMatch(result):
                curEpObj.status = Quality.compositeStatus(SNATCHED_BEST, result.quality)
            else:
                curEpObj.status = Quality.compositeStatus(endStatus, result.quality)

            # save episode to DB
            curEpObj.saveToDB()

        if curEpObj.status not in Quality.DOWNLOADED:
            try:
                srNotifiers.notify_snatch(
                    curEpObj._format_pattern('%SN - %Sx%0E - %EN - %QN') + " from " + result.provider.name)
            except:
                sickrage.srCore.srLogger.debug("Failed to send snatch notification")

            trakt_data.append((curEpObj.season, curEpObj.episode))

    data = sickrage.srCore.notifiersDict.trakt_notifier.trakt_episode_data_generate(trakt_data)

    if sickrage.srCore.srConfig.USE_TRAKT and sickrage.srCore.srConfig.TRAKT_SYNC_WATCHLIST:
        sickrage.srCore.srLogger.debug(
            "Add episodes, showid: indexerid " + str(result.show.indexerid) + ", Title " + str(
                result.show.name) + " to Traktv Watchlist")
        if data:
            sickrage.srCore.notifiersDict.trakt_notifier.update_watchlist(result.show, data_episode=data, update="add")

    return True


def pickBestResult(results, show):
    """
    Find the best result out of a list of search results for a show

    :param results: list of result objects
    :param show: Shows we check for
    :return: best result object
    """
    results = results if isinstance(results, list) else [results]

    sickrage.srCore.srLogger.debug("Picking the best result out of " + str([x.name for x in results]))

    bestResult = None

    # find the best result for the current episode
    for cur_result in results:
        if show and cur_result.show is not show:
            continue

        # build the black And white list
        if show.is_anime:
            if not show.release_groups.is_valid(cur_result):
                continue

        sickrage.srCore.srLogger.info(
            "Quality of " + cur_result.name + " is " + Quality.qualityStrings[cur_result.quality])

        anyQualities, bestQualities = Quality.splitQuality(show.quality)

        if cur_result.quality not in anyQualities + bestQualities:
            sickrage.srCore.srLogger.debug(cur_result.name + " is a quality we know we don't want, rejecting it")
            continue

        if show.rls_ignore_words and show_names.containsAtLeastOneWord(cur_result.name,
                                                                       cur_result.show.rls_ignore_words):
            sickrage.srCore.srLogger.info(
                "Ignoring " + cur_result.name + " based on ignored words filter: " + show.rls_ignore_words)
            continue

        if show.rls_require_words and not show_names.containsAtLeastOneWord(cur_result.name,
                                                                            cur_result.show.rls_require_words):
            sickrage.srCore.srLogger.info(
                "Ignoring " + cur_result.name + " based on required words filter: " + show.rls_require_words)
            continue

        if not show_names.filterBadReleases(cur_result.name, parse=False):
            sickrage.srCore.srLogger.info(
                "Ignoring " + cur_result.name + " because its not a valid scene release that we want, ignoring it")
            continue

        if hasattr(cur_result, 'size'):
            if sickrage.srCore.srConfig.USE_FAILED_DOWNLOADS and FailedHistory.hasFailed(cur_result.name,
                                                                                         cur_result.size,
                                                                                         cur_result.provider.name):
                sickrage.srCore.srLogger.info(cur_result.name + " has previously failed, rejecting it")
                continue

        # quality definition video file size constraints check
        try:
            for file, file_size in cur_result.files.items():
                if not file.endswith(tuple(video_exts)):
                    continue

                file_size = float(file_size / 1000000)
                if file_size > sickrage.srCore.srConfig.QUALITY_SIZES[cur_result.quality]:
                    raise (
                        "Ignoring " + cur_result.name + " based on quality size filter: {}, ignoring it".format(
                            file_size))
        except Exception as e:
            sickrage.srCore.srLogger.info(e.message)
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
                sickrage.srCore.srLogger.info("Preferring " + cur_result.name + " (x264 over xvid)")
                bestResult = cur_result

    if bestResult:
        sickrage.srCore.srLogger.debug("Picked " + bestResult.name + " as the best")
    else:
        sickrage.srCore.srLogger.debug("No result picked.")

    return bestResult


def isFinalResult(result):
    """
    Checks if the given result is good enough quality that we can stop searching for other ones.

    If the result is the highest quality in both the any/best quality lists then this function
    returns True, if not then it's False
    """

    sickrage.srCore.srLogger.debug("Checking if we should keep searching after we've found " + result.name)

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

    sickrage.srCore.srLogger.debug(
        "Checking if we should archive our first best quality match for episode " + result.name)

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

    wanted = []
    anyQualities, bestQualities = Quality.splitQuality(show.quality)  # @UnusedVariable
    allQualities = list(set(anyQualities + bestQualities))

    sickrage.srCore.srLogger.debug("Seeing if we need anything from {}".format(show.name))

    # check through the list of statuses to see if we want any
    for dbData in [x['doc'] for x in sickrage.srCore.mainDB.db.get_many('tv_episodes', show.indexerid, with_doc=True)
                   if x['doc']['season'] > 0 and x['doc']['airdate'] > fromDate.toordinal()]:

        curCompositeStatus = int(dbData["status"] or -1)
        curStatus, curQuality = Quality.splitCompositeStatus(curCompositeStatus)

        if bestQualities:
            highestBestQuality = max(allQualities)
        else:
            highestBestQuality = 0

        # if we need a better one then say yes
        if (curStatus in (DOWNLOADED, SNATCHED,
                          SNATCHED_PROPER) and curQuality < highestBestQuality) or curStatus == WANTED:
            epObj = show.getEpisode(int(dbData["season"]), int(dbData["episode"]))
            epObj.wantedQuality = [i for i in allQualities if (i > curQuality and i != Quality.UNKNOWN)]
            wanted.append(epObj)

    return wanted


def searchForNeededEpisodes():
    """
    Check providers for details on wanted episodes

    :return: episodes we have a search hit for
    """

    results = []

    for curShow in sickrage.srCore.SHOWLIST:
        if curShow.paused:
            continue

        episodes = wantedEpisodes(curShow, date.fromordinal(1))
        result = searchProviders(curShow, episodes, cacheOnly=True)
        if result: results += result

    return results


def searchProviders(show, episodes, manualSearch=False, downCurQuality=False, cacheOnly=False):
    """
    Walk providers for information on shows

    :param show: Show we are looking for
    :param episodes: Episodes we hope to find
    :param manualSearch: Boolean, is this a manual search?
    :param downCurQuality: Boolean, should we redownload currently avaialble quality file
    :return: results for search
    """

    if not len(sickrage.srCore.providersDict.enabled()):
        sickrage.srCore.srLogger.warning("No NZB/Torrent providers enabled. Please check your settings.")
        return

    # build name cache for show
    sickrage.srCore.NAMECACHE.build(show)

    origThreadName = threading.currentThread().getName()

    def perform_searches():
        foundResults = {}
        finalResults = []

        for providerID, providerObj in sickrage.srCore.providersDict.sort(
                randomize=sickrage.srCore.srConfig.RANDOMIZE_PROVIDERS).items():

            # check provider type and provider is enabled
            if not sickrage.srCore.srConfig.USE_NZBS and providerObj.type in [NZBProvider.type, NewznabProvider.type]:
                continue
            elif not sickrage.srCore.srConfig.USE_TORRENTS and providerObj.type in [TorrentProvider.type,
                                                                                    TorrentRssProvider.type]:
                continue
            elif not providerObj.isEnabled:
                continue

            if providerObj.anime_only and not show.is_anime:
                sickrage.srCore.srLogger.debug("" + str(show.name) + " is not an anime, skiping")
                continue

            foundResults[providerObj.name] = {}

            searchCount = 0
            search_mode = providerObj.search_mode

            # Always search for episode when manually searching when in sponly
            if search_mode == 'sponly' and manualSearch == True:
                search_mode = 'eponly'

            while True:
                searchCount += 1

                try:
                    threading.currentThread().setName(origThreadName + "::[" + providerObj.name + "]")

                    # update provider RSS cache
                    providerObj.cache.update()

                    if search_mode == 'eponly':
                        sickrage.srCore.srLogger.info("Performing episode search for " + show.name)
                    else:
                        sickrage.srCore.srLogger.info("Performing season pack search for " + show.name)

                    # search provider for episodes
                    searchResults = providerObj.findSearchResults(show,
                                                                  episodes,
                                                                  search_mode,
                                                                  manualSearch,
                                                                  downCurQuality,
                                                                  cacheOnly)
                except AuthException as e:
                    sickrage.srCore.srLogger.warning("Authentication error: {}".format(e.message))
                    break
                except Exception as e:
                    sickrage.srCore.srLogger.error(
                        "Error while searching " + providerObj.name + ", skipping: {}".format(e.message))
                    break
                finally:
                    threading.currentThread().setName(origThreadName)

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
                    sickrage.srCore.srLogger.debug("Fallback episode search initiated")
                    search_mode = 'eponly'
                else:
                    sickrage.srCore.srLogger.debug("Fallback season pack search initiate")
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

            sickrage.srCore.srLogger.debug(
                "The highest quality of any match is " + Quality.qualityStrings[highest_quality_overall])

            # see if every episode is wanted
            if bestSeasonResult:
                searchedSeasons = {x.season for x in episodes}

                # get the quality of the season nzb
                seasonQual = bestSeasonResult.quality
                sickrage.srCore.srLogger.debug(
                    "The quality of the season " + bestSeasonResult.provider.type + " is " +
                    Quality.qualityStrings[
                        seasonQual])

                allEps = [int(x['doc']["episode"]) for x in
                          sickrage.srCore.mainDB.db.get_many('tv_episodes', show.indexerid, with_doc=True)
                          if x['doc']['season'] in searchedSeasons]

                sickrage.srCore.srLogger.debug("Episode list: " + str(allEps))

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
                    sickrage.srCore.srLogger.info(
                        "Every ep in this season is needed, downloading the whole " + bestSeasonResult.provider.type + " " + bestSeasonResult.name)

                    epObjs = []
                    for curEpNum in allEps:
                        for season in set([x.season for x in episodes]):
                            epObjs.append(show.getEpisode(season, curEpNum))

                    bestSeasonResult.episodes = epObjs

                    return [bestSeasonResult]

                elif not anyWanted:
                    sickrage.srCore.srLogger.debug(
                        "No eps from this season are wanted at this quality, ignoring the result of " + bestSeasonResult.name)
                else:
                    if bestSeasonResult.provider.type == NZBProvider.type:
                        sickrage.srCore.srLogger.debug(
                            "Breaking apart the NZB and adding the individual ones to our results")

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
                        sickrage.srCore.srLogger.info(
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

                    sickrage.srCore.srLogger.debug(
                        "Seeing if we want to bother with multi-episode result " + _multiResult.name)

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

                    sickrage.srCore.srLogger.debug(
                        "Single-ep check result is neededEps: " + str(neededEps) + ", notNeededEps: " + str(
                            notNeededEps))

                    if not neededEps:
                        sickrage.srCore.srLogger.debug(
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

                    sickrage.srCore.srLogger.debug(
                        "Multi-ep check result is multiNeededEps: " + str(
                            multiNeededEps) + ", multiNotNeededEps: " + str(
                            multiNotNeededEps))

                    if not multiNeededEps:
                        sickrage.srCore.srLogger.debug(
                            "All of these episodes were covered by another multi-episode nzbs, ignoring this multi-ep result")
                        continue

                    # don't bother with the single result if we're going to get it with a multi result
                    for epObj in multiResult.episodes:
                        multiResults[epObj.episode] = multiResult
                        if epObj.episode in foundResults[providerObj.name]:
                            sickrage.srCore.srLogger.debug(
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

        return finalResults

    return perform_searches()
