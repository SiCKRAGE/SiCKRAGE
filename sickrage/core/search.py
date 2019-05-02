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


import re
import threading
from datetime import date, timedelta

import sickrage
from sickrage.clients import getClientIstance
from sickrage.clients.nzbget import NZBGet
from sickrage.clients.sabnzbd import SabNZBd
from sickrage.core.common import Quality, SEASON_RESULT, SNATCHED_BEST, \
    SNATCHED_PROPER, SNATCHED, MULTI_EP_RESULT
from sickrage.core.databases.main import MainDB
from sickrage.core.exceptions import AuthException
from sickrage.core.helpers import show_names
from sickrage.core.nzbSplitter import split_nzb_result
from sickrage.core.tv.episode.helpers import find_episode
from sickrage.core.tv.show import find_show
from sickrage.core.tv.show.history import FailedHistory, History
from sickrage.notifiers import Notifiers
from sickrage.providers import NZBProvider, NewznabProvider, TorrentProvider, TorrentRssProvider


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
    if sickrage.app.config.allow_high_priority:
        # if it aired recently make it high priority
        for curEp in result.episodes:
            if date.today() - curEp.airdate <= timedelta(days=7):
                result.priority = 1

    if re.search(r'(^|[. _-])(proper|repack)([. _-]|$)', result.name, re.I) is not None:
        endStatus = SNATCHED_PROPER

    # get result content
    result.content = result.provider.get_content(result.url)

    dlResult = False
    if result.resultType in ("nzb", "nzbdata"):
        if sickrage.app.config.nzb_method == "blackhole":
            dlResult = result.provider.download_result(result)
        elif sickrage.app.config.nzb_method == "sabnzbd":
            dlResult = SabNZBd.sendNZB(result)
        elif sickrage.app.config.nzb_method == "nzbget":
            is_proper = True if endStatus == SNATCHED_PROPER else False
            dlResult = NZBGet.sendNZB(result, is_proper)
        else:
            sickrage.app.log.error("Unknown NZB action specified in config: " + sickrage.app.config.nzb_method)
    elif result.resultType in ("torrent", "torznab"):
        # add public trackers to torrent result
        if not result.provider.private:
            result = result.provider.add_trackers(result)

        if sickrage.app.config.torrent_method == "blackhole":
            dlResult = result.provider.download_result(result)
        else:
            if any([result.content, result.url.startswith('magnet:')]):
                client = getClientIstance(sickrage.app.config.torrent_method)()
                dlResult = client.send_torrent(result)
            else:
                sickrage.app.log.warning("Torrent file content is empty")
    else:
        sickrage.app.log.error("Unknown result type, unable to download it (%r)" % result.resultType)

    # no download results found
    if not dlResult:
        return False

    FailedHistory.logSnatch(result)

    sickrage.app.alerts.message(_('Episode snatched'), result.name)

    History.logSnatch(result)

    # don't notify when we re-download an episode
    trakt_data = []
    for curEpObj in result.episodes:
        with curEpObj.lock:
            if isFirstBestMatch(result):
                curEpObj.status = Quality.composite_status(SNATCHED_BEST, result.quality)
            else:
                curEpObj.status = Quality.composite_status(endStatus, result.quality)

            # save episode to DB
            # curEpObj.save_to_db()

        if curEpObj.status not in Quality.DOWNLOADED:
            try:
                Notifiers.mass_notify_snatch(
                    curEpObj._format_pattern('%SN - %Sx%0E - %EN - %QN') + " from " + result.provider.name)
            except Exception:
                sickrage.app.log.debug("Failed to send snatch notification")

            trakt_data.append((curEpObj.season, curEpObj.episode))

    data = sickrage.app.notifier_providers['trakt'].trakt_episode_data_generate(trakt_data)

    if sickrage.app.config.use_trakt and sickrage.app.config.trakt_sync_watchlist:
        if data:
            sickrage.app.notifier_providers['trakt'].update_watchlist(result.show_id, data_episode=data, update="add")

    return True


def pickBestResult(results):
    """
    Find the best result out of a list of search results for a show

    :param results: list of result objects
    :param show_id: Show ID we check for
    :return: best result object
    """
    results = results if isinstance(results, list) else [results]

    sickrage.app.log.debug("Picking the best result out of " + str([x.name for x in results]))

    best_result = None

    # find the best result for the current episode
    for cur_result in results:
        show = find_show(cur_result.indexer_id)

        # build the black And white list
        if show.is_anime:
            if not show.release_groups.is_valid(cur_result):
                continue

        sickrage.app.log.info(
            "Quality of " + cur_result.name + " is " + Quality.qualityStrings[cur_result.quality])

        anyQualities, bestQualities = Quality.split_quality(show.quality)

        if cur_result.quality not in anyQualities + bestQualities:
            sickrage.app.log.debug(cur_result.name + " is a quality we know we don't want, rejecting it")
            continue

        # check if seeders meet out minimum requirements, disgard result if it does not
        if hasattr(cur_result.provider, 'minseed') and cur_result.seeders not in (-1, None):
            if int(cur_result.seeders) < min(cur_result.provider.minseed, 1):
                sickrage.app.log.info("Discarding torrent because it doesn't meet the minimum seeders: {}. Seeders:  "
                                      "{}".format(cur_result.name, cur_result.seeders))
                continue

        # check if leechers meet out minimum requirements, disgard result if it does not
        if hasattr(cur_result.provider, 'minleech') and cur_result.leechers not in (-1, None):
            if int(cur_result.leechers) < min(cur_result.provider.minleech, 0):
                sickrage.app.log.info("Discarding torrent because it doesn't meet the minimum leechers: {}. Leechers:  "
                                      "{}".format(cur_result.name, cur_result.leechers))
                continue

        if show.rls_ignore_words and show_names.containsAtLeastOneWord(cur_result.name, show.rls_ignore_words):
            sickrage.app.log.info(
                "Ignoring " + cur_result.name + " based on ignored words filter: " + show.rls_ignore_words)
            continue

        if show.rls_require_words and not show_names.containsAtLeastOneWord(cur_result.name, show.rls_require_words):
            sickrage.app.log.info(
                "Ignoring " + cur_result.name + " based on required words filter: " + show.rls_require_words)
            continue

        if not show_names.filterBadReleases(cur_result.name, parse=False):
            sickrage.app.log.info(
                "Ignoring " + cur_result.name + " because its not a valid scene release that we want")
            continue

        if hasattr(cur_result, 'size'):
            if FailedHistory.hasFailed(cur_result.name, cur_result.size, cur_result.provider.name):
                sickrage.app.log.info(cur_result.name + " has previously failed, rejecting it")
                continue

            # quality definition video file size constraints check
            try:
                if cur_result.size:
                    quality_size = sickrage.app.config.quality_sizes[cur_result.quality]
                    file_size = float(cur_result.size / 1000000)
                    if file_size > quality_size:
                        raise Exception(
                            "Ignoring " + cur_result.name + " with size: {} based on quality size filter: {}".format(
                                file_size, quality_size)
                        )
            except Exception as e:
                sickrage.app.log.info(str(e))
                continue

        # verify result content
        if not cur_result.provider.private:
            if cur_result.resultType in ["nzb", "torrent"] and not cur_result.provider.get_content(cur_result.url):
                if sickrage.app.config.download_unverified_magnet_link and cur_result.url.startswith('magnet'):
                    # Attempt downloading unverified torrent magnet link
                    pass
                else:
                    sickrage.app.log.info(
                        "Ignoring {} because we are unable to verify the download url".format(cur_result.name))
                    continue

        if not best_result:
            best_result = cur_result
        elif cur_result.quality in bestQualities and (
                best_result.quality < cur_result.quality or best_result.quality not in bestQualities):
            best_result = cur_result
        elif cur_result.quality in anyQualities and best_result.quality not in bestQualities and best_result.quality < cur_result.quality:
            best_result = cur_result
        elif best_result.quality == cur_result.quality:
            if "proper" in cur_result.name.lower() or "repack" in cur_result.name.lower():
                best_result = cur_result
            elif "internal" in best_result.name.lower() and "internal" not in cur_result.name.lower():
                best_result = cur_result
            elif "xvid" in best_result.name.lower() and "x264" in cur_result.name.lower():
                sickrage.app.log.info("Preferring " + cur_result.name + " (x264 over xvid)")
                best_result = cur_result

    if best_result:
        sickrage.app.log.debug("Picked " + best_result.name + " as the best")
    else:
        sickrage.app.log.debug("No result picked.")

    return best_result


def isFinalResult(result):
    """
    Checks if the given result is good enough quality that we can stop searching for other ones.

    If the result is the highest quality in both the any/best quality lists then this function
    returns True, if not then it's False
    """

    sickrage.app.log.debug("Checking if we should keep searching after we've found " + result.name)

    show_obj = result.episodes[0].show

    any_qualities, best_qualities = Quality.split_quality(show_obj.quality)

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

    sickrage.app.log.debug(
        "Checking if we should archive our first best quality match for episode " + result.name)

    show_obj = result.episodes[0].show

    any_qualities, best_qualities = Quality.split_quality(show_obj.quality)

    # if there is a re-download that's a match to one of our best qualities and we want to skip downloaded then we
    # are done
    if best_qualities and show_obj.skip_downloaded and result.quality in best_qualities:
        return True

    return False


def searchProviders(show_id, episode_ids, manualSearch=False, downCurQuality=False, cacheOnly=False):
    """
    Walk providers for information on shows

    :param show_id: Show we are looking for
    :param episode_ids: Episodes we hope to find
    :param manualSearch: Boolean, is this a manual search?
    :param downCurQuality: Boolean, should we redownload currently avaialble quality file
    :return: results for search
    """

    show = find_show(show_id)

    # build name cache for show
    sickrage.app.name_cache.build(show)

    origThreadName = threading.currentThread().getName()

    def perform_searches(show_id, episode_ids):
        search_results = {}
        found_results = {}
        final_results = []

        for providerID, providerObj in sickrage.app.search_providers.sort(
                randomize=sickrage.app.config.randomize_providers).items():

            # check if provider is enabled
            if not providerObj.isEnabled:
                continue

            # check provider type
            if not sickrage.app.config.use_nzbs and providerObj.type in [NZBProvider.type, NewznabProvider.type]:
                continue
            elif not sickrage.app.config.use_torrents and providerObj.type in [TorrentProvider.type,
                                                                               TorrentRssProvider.type]:
                continue

            if providerObj.anime_only and not show.is_anime:
                sickrage.app.log.debug("" + str(show.name) + " is not an anime, skiping")
                continue

            found_results[providerObj.name] = {}

            search_count = 0
            search_mode = providerObj.search_mode

            # Always search for episode when manually searching when in sponly
            if search_mode == 'sponly' and manualSearch == True:
                search_mode = 'eponly'

            while True:
                search_count += 1

                try:
                    threading.currentThread().setName(origThreadName + "::[" + providerObj.name + "]")

                    if len(episode_ids):
                        if search_mode == 'eponly':
                            sickrage.app.log.info("Performing episode search for " + show.name)
                        else:
                            sickrage.app.log.info("Performing season pack search for " + show.name)

                    # search provider for episodes
                    search_results = providerObj.find_search_results(show.indexer_id,
                                                                     episode_ids,
                                                                     search_mode,
                                                                     manualSearch,
                                                                     downCurQuality,
                                                                     cacheOnly)
                except AuthException as e:
                    sickrage.app.log.warning("Authentication error: {}".format(e))
                    break
                except Exception as e:
                    sickrage.app.log.error("Error while searching " + providerObj.name + ", skipping: {}".format(e))
                    break
                finally:
                    threading.currentThread().setName(origThreadName)

                if len(search_results):
                    # make a list of all the results for this provider
                    for cur_eid in search_results:
                        if cur_eid in found_results:
                            found_results[providerObj.name][cur_eid] += search_results[cur_eid]
                        else:
                            found_results[providerObj.name][cur_eid] = search_results[cur_eid]

                        # Sort results by seeders if available
                        if providerObj.type == 'torrent' or getattr(providerObj, 'torznab', False):
                            found_results[providerObj.name][cur_eid].sort(key=lambda k: int(k.seeders), reverse=True)

                    break
                elif not providerObj.search_fallback or search_count == 2:
                    break

                if search_mode == 'sponly':
                    sickrage.app.log.debug("Fallback episode search initiated")
                    search_mode = 'eponly'
                else:
                    sickrage.app.log.debug("Fallback season pack search initiate")
                    search_mode = 'sponly'

            # skip to next provider if we have no results to process
            if not len(found_results[providerObj.name]):
                continue

            # pick the best season NZB
            bestSeasonResult = None
            if SEASON_RESULT in found_results[providerObj.name]:
                bestSeasonResult = pickBestResult(found_results[providerObj.name][SEASON_RESULT])

            highest_quality_overall = 0
            for cur_episode in found_results[providerObj.name]:
                for cur_result in found_results[providerObj.name][cur_episode]:
                    if cur_result.quality != Quality.UNKNOWN and cur_result.quality > highest_quality_overall:
                        highest_quality_overall = cur_result.quality

            sickrage.app.log.debug(
                "The highest quality of any match is " + Quality.qualityStrings[highest_quality_overall])

            # see if every episode is wanted
            if bestSeasonResult:
                searchedSeasons = {find_episode(show_id, eid).season for eid in episode_ids}

                # get the quality of the season nzb
                seasonQual = bestSeasonResult.quality
                sickrage.app.log.debug(
                    "The quality of the season " + bestSeasonResult.provider.type + " is " +
                    Quality.qualityStrings[
                        seasonQual])

                allEps = [x.episode for x in show.episodes if x.season in searchedSeasons]

                sickrage.app.log.debug("Episode list: " + str(allEps))

                allWanted = True
                anyWanted = False
                for curEpNum in allEps:
                    for season in {find_episode(show_id, eid).season for eid in episode_ids}:
                        if not show.want_episode(season, curEpNum, seasonQual, downCurQuality):
                            allWanted = False
                        else:
                            anyWanted = True

                # if we need every ep in the season and there's nothing better then just download this and be done
                # with it (unless single episodes are preferred)
                if allWanted and bestSeasonResult.quality == highest_quality_overall:
                    sickrage.app.log.info(
                        "Every ep in this season is needed, downloading the whole " + bestSeasonResult.provider.type + " " + bestSeasonResult.name)

                    episode_ids = []
                    for curEpNum in allEps:
                        for season in {find_episode(show_id, eid).season for eid in episode_ids}:
                            episode_ids.append(show.get_episode(season, curEpNum).indexer_id)

                    bestSeasonResult.episode_ids = episode_ids

                    return [bestSeasonResult]

                elif not anyWanted:
                    sickrage.app.log.debug(
                        "No eps from this season are wanted at this quality, ignoring the result of " + bestSeasonResult.name)
                else:
                    if bestSeasonResult.provider.type == NZBProvider.type:
                        sickrage.app.log.debug(
                            "Breaking apart the NZB and adding the individual ones to our results")

                        # if not, break it apart and add them as the lowest priority results
                        individualResults = split_nzb_result(bestSeasonResult)
                        for curResult in individualResults:
                            epNum = -1
                            if len(curResult.episodes) == 1:
                                epNum = curResult.episodes[0].episode
                            elif len(curResult.episodes) > 1:
                                epNum = MULTI_EP_RESULT

                            if epNum in found_results[providerObj.name]:
                                found_results[providerObj.name][epNum].append(curResult)
                            else:
                                found_results[providerObj.name][epNum] = [curResult]

                    # If this is a torrent all we can do is leech the entire torrent, user will have to select which
                    # eps not do download in his torrent client
                    else:
                        # Season result from Torrent Provider must be a full-season torrent, creating multi-ep result
                        # for it.
                        sickrage.app.log.info("Adding multi-ep result for full-season torrent. Set the episodes you "
                                              "don't want to 'don't download' in your torrent client if desired!")

                        epObjs = []
                        for curEpNum in allEps:
                            for season in set([x.season for x in episodes]):
                                epObjs.append(show.get_episode(season, curEpNum))
                        bestSeasonResult.episodes = epObjs

                        if MULTI_EP_RESULT in found_results[providerObj.name]:
                            found_results[providerObj.name][MULTI_EP_RESULT].append(bestSeasonResult)
                        else:
                            found_results[providerObj.name][MULTI_EP_RESULT] = [bestSeasonResult]

            # go through multi-ep results and see if we really want them or not, get rid of the rest
            multiResults = {}
            if MULTI_EP_RESULT in found_results[providerObj.name]:
                for _multiResult in found_results[providerObj.name][MULTI_EP_RESULT]:

                    sickrage.app.log.debug(
                        "Seeing if we want to bother with multi-episode result " + _multiResult.name)

                    # Filter result by ignore/required/whitelist/blacklist/quality, etc
                    multiResult = pickBestResult(_multiResult)
                    if not multiResult:
                        continue

                    # see how many of the eps that this result covers aren't covered by single results
                    neededEps = []
                    notNeededEps = []
                    for epObj in multiResult.episodes:
                        # if we have results for the episode
                        if epObj.episode in found_results[providerObj.name] and len(
                                found_results[providerObj.name][epObj.episode]) > 0:
                            notNeededEps.append(epObj.episode)
                        else:
                            neededEps.append(epObj.episode)

                    sickrage.app.log.debug(
                        "Single-ep check result is neededEps: " + str(neededEps) + ", notNeededEps: " + str(
                            notNeededEps))

                    if not neededEps:
                        sickrage.app.log.debug(
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

                    sickrage.app.log.debug(
                        "Multi-ep check result is multiNeededEps: " + str(
                            multiNeededEps) + ", multiNotNeededEps: " + str(
                            multiNotNeededEps))

                    if not multiNeededEps:
                        sickrage.app.log.debug(
                            "All of these episodes were covered by another multi-episode nzbs, ignoring this multi-ep result")
                        continue

                    # don't bother with the single result if we're going to get it with a multi result
                    for epObj in multiResult.episodes:
                        multiResults[epObj.episode] = multiResult
                        if epObj.episode in found_results[providerObj.name]:
                            sickrage.app.log.debug(
                                "A needed multi-episode result overlaps with a single-episode result for ep #" + str(
                                    epObj.episode) + ", removing the single-episode results from the list")
                            del found_results[providerObj.name][epObj.episode]

            # of all the single ep results narrow it down to the best one for each episode
            final_results += set(multiResults.values())
            for curEp in found_results[providerObj.name]:
                if curEp in (MULTI_EP_RESULT, SEASON_RESULT):
                    continue

                if not len(found_results[providerObj.name][curEp]) > 0:
                    continue

                # if all results were rejected move on to the next episode
                bestResult = pickBestResult(found_results[providerObj.name][curEp])
                if not bestResult:
                    continue

                # add result if its not a duplicate and
                found = False
                for i, result in enumerate(final_results):
                    for bestResultEp in bestResult.episodes:
                        if bestResultEp in result.episodes:
                            if result.quality < bestResult.quality:
                                final_results.pop(i)
                            else:
                                found = True
                if not found:
                    final_results += [bestResult]

            # check that we got all the episodes we wanted first before doing a match and snatch
            wantedEpCount = 0
            for wantedEp in episodes:
                for result in final_results:
                    if wantedEp in result.episodes and isFinalResult(result):
                        wantedEpCount += 1

            # make sure we search every provider for results unless we found everything we wanted
            if wantedEpCount == len(episode_ids):
                break

        return final_results

    return perform_searches(show_id, episode_ids)
