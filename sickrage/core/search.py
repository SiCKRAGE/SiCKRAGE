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
import itertools
import re
import threading
from datetime import date, timedelta

import sickrage
from sickrage.clients import get_client_instance
from sickrage.clients.nzb.nzbget import NZBGet
from sickrage.clients.nzb.sabnzbd import SabNZBd
from sickrage.core.common import Quality, Qualities, EpisodeStatus
from sickrage.core.common import (
    SEASON_RESULT,
    MULTI_EP_RESULT
)
from sickrage.core.enums import NzbMethod, TorrentMethod
from sickrage.core.exceptions import AuthException
from sickrage.core.helpers import show_names
from sickrage.core.nzbSplitter import split_nzb_result
from sickrage.core.tv.show.helpers import find_show
from sickrage.core.tv.show.history import (
    FailedHistory,
    History
)
from sickrage.notification_providers import NotificationProvider
from sickrage.search_providers import (
    NZBProvider,
    NewznabProvider,
    TorrentProvider,
    TorrentRssProvider, SearchProviderType
)


def snatch_episode(result, end_status=EpisodeStatus.SNATCHED):
    """
    Contains the internal logic necessary to actually "snatch" a result that
    has been found.

    :param result: SearchResult instance to be snatched.
    :param end_status: the episode status that should be used for the episode object once it's snatched.
    :return: boolean, True on success
    """

    if result is None:
        return False

    show_object = find_show(result.series_id, result.series_provider_id)

    result.priority = 0  # -1 = low, 0 = normal, 1 = high
    if sickrage.app.config.general.allow_high_priority:
        # if it aired recently make it high priority
        for episode_number in result.episodes:
            if date.today() - show_object.get_episode(result.season, episode_number).airdate <= timedelta(days=7):
                result.priority = 1

    if re.search(r'(^|[. _-])(proper|repack)([. _-]|$)', result.name, re.I) is not None:
        end_status = EpisodeStatus.SNATCHED_PROPER

    # get result content
    result.content = result.provider.get_content(result.url)

    dlResult = False
    if result.provider_type in (SearchProviderType.NZB, SearchProviderType.NZBDATA):
        if sickrage.app.config.general.nzb_method == NzbMethod.BLACKHOLE:
            dlResult = result.provider.download_result(result)
        elif sickrage.app.config.general.nzb_method == NzbMethod.SABNZBD:
            dlResult = SabNZBd.sendNZB(result)
        elif sickrage.app.config.general.nzb_method == NzbMethod.NZBGET:
            is_proper = True if end_status == EpisodeStatus.SNATCHED_PROPER else False
            dlResult = NZBGet.sendNZB(result, is_proper)
        elif sickrage.app.config.general.nzb_method == NzbMethod.DOWNLOAD_STATION:
            client = get_client_instance(sickrage.app.config.general.nzb_method.value, client_type='nzb')()
            dlResult = client.sendNZB(result)
    elif result.provider_type in (SearchProviderType.TORRENT, SearchProviderType.TORZNAB):
        # add public trackers to torrent result
        if not result.provider.private:
            result = result.provider.add_trackers(result)

        if sickrage.app.config.general.torrent_method == TorrentMethod.BLACKHOLE:
            dlResult = result.provider.download_result(result)
        else:
            if any([result.content, result.url.startswith('magnet:')]):
                client = get_client_instance(sickrage.app.config.general.torrent_method.value, client_type='torrent')()
                dlResult = client.send_torrent(result)
            else:
                sickrage.app.log.warning("Torrent file content is empty")
    else:
        sickrage.app.log.error("Unknown result type, unable to download it (%r)" % result.provider_type.display_name)

    # no download results found
    if not dlResult:
        return False

    FailedHistory.log_snatch(result)
    History.log_snatch(result)

    sickrage.app.alerts.message(_('Episode snatched'), result.name)

    trakt_data = []
    for episode_number in result.episodes:
        episode_obj = show_object.get_episode(result.season, episode_number)

        if is_first_best_match(result):
            episode_obj.status = Quality.composite_status(EpisodeStatus.SNATCHED_BEST, result.quality)
        else:
            episode_obj.status = Quality.composite_status(end_status, result.quality)

        episode_obj.save()

        # don't notify when we re-download an episode
        if episode_obj.status not in EpisodeStatus.composites(EpisodeStatus.DOWNLOADED):
            try:
                NotificationProvider.mass_notify_snatch(episode_obj._format_pattern('%SN - %Sx%0E - %EN - %QN') + " from " + result.provider.name)
            except Exception:
                sickrage.app.log.debug("Failed to send snatch notification")

            trakt_data.append((episode_obj.season, episode_obj.episode))

    data = sickrage.app.notification_providers['trakt'].trakt_episode_data_generate(trakt_data)

    if sickrage.app.config.trakt.enable and sickrage.app.config.trakt.sync_watchlist:
        if data:
            sickrage.app.notification_providers['trakt'].update_watchlist(show_object, data_episode=data, update="add")

    return True


def pick_best_result(results, season_pack=False):
    """
    Find the best result out of a list of search results for a show

    :param results: list of result objects
    :param series_id: Show ID we check for
    :return: best result object
    """

    results = results if isinstance(results, list) else [results]

    sickrage.app.log.debug("Picking the best result out of " + str([x.name for x in results]))

    best_result = None

    # find the best result for the current episode
    for cur_result in results:
        show_obj = find_show(cur_result.series_id, cur_result.series_provider_id)

        # build the black And white list
        if show_obj.is_anime:
            if not show_obj.release_groups.is_valid(cur_result):
                continue

        sickrage.app.log.info("Quality of " + cur_result.name + " is " + cur_result.quality.display_name)

        any_qualities, best_qualities = Quality.split_quality(show_obj.quality)
        if cur_result.quality not in any_qualities + best_qualities:
            sickrage.app.log.debug(cur_result.name + " is a quality we know we don't want, rejecting it")
            continue

        # check if seeders meet out minimum requirements, disgard result if it does not
        if cur_result.provider.custom_settings.get('minseed', 0) and cur_result.seeders not in (-1, None):
            if int(cur_result.seeders) < min(cur_result.provider.custom_settings.get('minseed', 0), 1):
                sickrage.app.log.info("Discarding torrent because it doesn't meet the minimum seeders: {}. Seeders:  "
                                      "{}".format(cur_result.name, cur_result.seeders))
                continue

        # check if leechers meet out minimum requirements, disgard result if it does not
        if cur_result.provider.custom_settings.get('minleech', 0) and cur_result.leechers not in (-1, None):
            if int(cur_result.leechers) < min(cur_result.provider.custom_settings.get('minleech', 0), 0):
                sickrage.app.log.info("Discarding torrent because it doesn't meet the minimum leechers: {}. Leechers:  "
                                      "{}".format(cur_result.name, cur_result.leechers))
                continue

        if show_obj.rls_ignore_words and show_names.contains_at_least_one_word(cur_result.name, show_obj.rls_ignore_words):
            sickrage.app.log.info("Ignoring " + cur_result.name + " based on ignored words filter: " + show_obj.rls_ignore_words)
            continue

        if show_obj.rls_require_words and not show_names.contains_at_least_one_word(cur_result.name, show_obj.rls_require_words):
            sickrage.app.log.info("Ignoring " + cur_result.name + " based on required words filter: " + show_obj.rls_require_words)
            continue

        if not show_names.filter_bad_releases(cur_result.name, parse=False):
            sickrage.app.log.info("Ignoring " + cur_result.name + " because its not a valid scene release that we want")
            continue

        if hasattr(cur_result, 'size'):
            if FailedHistory.has_failed(cur_result.name, cur_result.size, cur_result.provider.name):
                sickrage.app.log.info(cur_result.name + " has previously failed, rejecting it")
                continue

            # quality definition video file size constraints check
            try:
                if cur_result.size:
                    quality_size_min = sickrage.app.config.quality_sizes[cur_result.quality.name].min_size
                    quality_size_max = sickrage.app.config.quality_sizes[cur_result.quality.name].max_size

                    if quality_size_min != 0 and quality_size_max != 0:
                        if season_pack and not len(cur_result.episodes):
                            episode_count = len([x for x in show_obj.episodes if x.season == cur_result.season])
                            file_size = float(cur_result.size / episode_count / 1000000)
                        else:
                            file_size = float(cur_result.size / len(cur_result.episodes) / 1000000)

                        if quality_size_min > file_size > quality_size_max:
                            raise Exception("Ignoring " + cur_result.name + " with size {}".format(file_size))
            except Exception as e:
                sickrage.app.log.info(e)
                continue

        # verify result content
        # if not cur_result.provider.private:
        #     if cur_result.provider_type in ["nzb", "torrent"] and not cur_result.provider.get_content(cur_result.url):
        #         if not sickrage.app.config.general.download_unverified_magnet_link and cur_result.url.startswith('magnet'):
        #             sickrage.app.log.info("Ignoring {} because we are unable to verify the download url".format(cur_result.name))
        #             continue

        if not best_result:
            best_result = cur_result
        elif cur_result.quality in best_qualities and (
                best_result.quality < cur_result.quality or best_result.quality not in best_qualities):
            best_result = cur_result
        elif cur_result.quality in any_qualities and best_result.quality not in best_qualities and best_result.quality < cur_result.quality:
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


def is_final_result(result):
    """
    Checks if the given result is good enough quality that we can stop searching for other ones.

    If the result is the highest quality in both the any/best quality lists then this function
    returns True, if not then it's False
    """

    sickrage.app.log.debug("Checking if we should keep searching after we've found " + result.name)

    show_obj = find_show(result.series_id, result.series_provider_id)

    any_qualities, best_qualities = Quality.split_quality(show_obj.quality)

    # if there is a download that's higher than this then we definitely need to keep looking
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


def is_first_best_match(result):
    """
    Checks if the given result is a best quality match and if we want to archive the episode on first match.
    """

    sickrage.app.log.debug("Checking if we should archive our first best quality match for episode " + result.name)

    show_obj = find_show(result.series_id, result.series_provider_id)

    any_qualities, best_qualities = Quality.split_quality(show_obj.quality)

    # if there is a re-download that's a match to one of our best qualities and we want to skip downloaded then we
    # are done
    if best_qualities and show_obj.skip_downloaded and result.quality in best_qualities:
        return True

    return False


def search_providers(series_id, series_provider_id, season, episode, manualSearch=False, downCurQuality=False, cacheOnly=False):
    """
    Walk providers for information on shows

    :param series_id: Show ID we are looking for
    :param episodes: Episode IDs we hope to find
    :param manualSearch: Boolean, is this a manual search?
    :param downCurQuality: Boolean, should we re-download currently available quality file
    :return: results for search
    """

    orig_thread_name = threading.currentThread().getName()

    show_object = find_show(series_id, series_provider_id)

    final_results = []

    for providerID, providerObj in sickrage.app.search_providers.sort(randomize=sickrage.app.config.general.randomize_providers).items():
        # check if provider is enabled
        if not providerObj.is_enabled:
            continue

        # check provider type
        if not sickrage.app.config.general.use_nzbs and providerObj.provider_type in [NZBProvider.provider_type, NewznabProvider.provider_type]:
            continue
        elif not sickrage.app.config.general.use_torrents and providerObj.provider_type in [TorrentProvider.provider_type, TorrentRssProvider.provider_type]:
            continue

        if providerObj.anime_only and not show_object.is_anime:
            sickrage.app.log.debug("" + str(show_object.name) + " is not an anime, skiping")
            continue

        found_results = {}

        search_count = 0
        search_mode = providerObj.search_mode

        # Always search for episode when manually searching when in sponly
        if search_mode == 'sponly' and manualSearch is True:
            search_mode = 'eponly'

        while True:
            search_count += 1

            try:
                threading.currentThread().setName(orig_thread_name + "::[" + providerObj.name + "]")

                if episode and search_mode == 'eponly':
                    sickrage.app.log.info("Performing episode search for " + show_object.name)
                else:
                    sickrage.app.log.info("Performing season pack search for " + show_object.name)

                # search provider for episodes
                found_results = providerObj.find_search_results(series_id,
                                                                series_provider_id,
                                                                season,
                                                                episode,
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
                threading.currentThread().setName(orig_thread_name)

            if len(found_results):
                # make a list of all the results for this provider
                for search_result in found_results:
                    # Sort results by seeders if available
                    if providerObj.provider_type == SearchProviderType.TORRENT or getattr(providerObj, 'torznab', False):
                        found_results[search_result].sort(key=lambda k: int(k.seeders), reverse=True)
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
        if not len(found_results):
            continue

        # remove duplicates
        for cur_episode in found_results:
            found_results[cur_episode] = [next(obj) for i, obj in itertools.groupby(sorted(found_results[cur_episode], key=lambda x: x.url), lambda x: x.url)]

        # pick the best season NZB
        best_season_result = None
        if SEASON_RESULT in found_results:
            best_season_result = pick_best_result(found_results[SEASON_RESULT], season_pack=True)

        highest_quality_overall = 0
        for cur_episode in found_results:
            for cur_result in found_results[cur_episode]:
                if cur_result.quality != Qualities.UNKNOWN and cur_result.quality > highest_quality_overall:
                    highest_quality_overall = cur_result.quality

        sickrage.app.log.debug("The highest quality of any match is " + highest_quality_overall.display_name)

        # see if every episode is wanted
        if best_season_result:
            # get the quality of the season nzb
            season_qual = best_season_result.quality
            sickrage.app.log.debug("The quality of the season " + best_season_result.provider.provider_type.display_name + " is " + season_qual.display_name)

            all_episodes = set([x.episode for x in show_object.episodes if x.season == best_season_result.season])

            sickrage.app.log.debug("Episodes list: {}".format(','.join(map(str, all_episodes))))

            all_wanted = True
            any_wanted = False

            for curEp in all_episodes:
                if not show_object.want_episode(season, curEp, season_qual, downCurQuality):
                    all_wanted = False
                else:
                    any_wanted = True

            # if we need every ep in the season and there's nothing better then just download this and be done
            # with it (unless single episodes are preferred)
            if all_wanted and best_season_result.quality == highest_quality_overall:
                sickrage.app.log.info("Every ep in this season is needed, "
                                      "downloading the whole " + best_season_result.provider.provider_type.display_name + " " + best_season_result.name)

                best_season_result.episodes = all_episodes

                return best_season_result
            elif not any_wanted:
                sickrage.app.log.debug("No eps from this season are wanted at this quality, ignoring the result of {}".format(best_season_result.name))
            else:
                if best_season_result.provider.provider_type == NZBProvider.provider_type:
                    sickrage.app.log.debug("Breaking apart the NZB and adding the individual ones to our results")

                    # if not, break it apart and add them as the lowest priority results
                    individual_results = split_nzb_result(best_season_result)
                    for curResult in individual_results:
                        ep_num = -1
                        if len(curResult.episodes) == 1:
                            ep_num = curResult.episodes[0]
                        elif len(curResult.episodes) > 1:
                            ep_num = MULTI_EP_RESULT

                        if ep_num in found_results:
                            found_results[ep_num].append(curResult)
                        else:
                            found_results[ep_num] = [curResult]

                # If this is a torrent all we can do is leech the entire torrent, user will have to select which
                # eps not do download in his torrent client
                else:
                    # Season result from Torrent Provider must be a full-season torrent, creating multi-ep result
                    # for it.
                    sickrage.app.log.info("Adding multi-ep result for full-season torrent. Set the episodes you "
                                          "don't want to 'don't download' in your torrent client if desired!")

                    best_season_result.episodes = all_episodes

                    if MULTI_EP_RESULT in found_results:
                        found_results[MULTI_EP_RESULT].append(best_season_result)
                    else:
                        found_results[MULTI_EP_RESULT] = [best_season_result]

        # go through multi-ep results and see if we really want them or not, get rid of the rest
        multi_results = {}
        if MULTI_EP_RESULT in found_results:
            for _multiResult in found_results[MULTI_EP_RESULT]:
                sickrage.app.log.debug(
                    "Seeing if we want to bother with multi-episode result " + _multiResult.name)

                # Filter result by ignore/required/whitelist/blacklist/quality, etc
                multi_result = pick_best_result(_multiResult)
                if not multi_result:
                    continue

                # see how many of the eps that this result covers aren't covered by single results
                needed_eps = []
                not_needed_eps = []
                for multi_result_episode in multi_result.episodes:
                    # if we have results for the episode
                    if multi_result_episode in found_results and len(found_results[multi_result_episode]) > 0:
                        not_needed_eps.append(multi_result_episode)
                    else:
                        needed_eps.append(multi_result_episode)

                sickrage.app.log.debug("Single-ep check result is neededEps: " + str(needed_eps) + ", notNeededEps: " + str(not_needed_eps))
                if not needed_eps:
                    sickrage.app.log.debug("All of these episodes were covered by single episode results, ignoring this multi-episode result")
                    continue

                # check if these eps are already covered by another multi-result
                multi_needed_eps = []
                multi_not_needed_eps = []
                for multi_result_episode in multi_result.episodes:
                    if multi_result_episode in multi_results:
                        multi_not_needed_eps.append(multi_result_episode)
                    else:
                        multi_needed_eps.append(multi_result_episode)

                sickrage.app.log.debug(
                    "Multi-ep check result is multiNeededEps: " + str(
                        multi_needed_eps) + ", multiNotNeededEps: " + str(
                        multi_not_needed_eps)
                )

                if not multi_needed_eps:
                    sickrage.app.log.debug("All of these episodes were covered by another multi-episode nzbs, ignoring this multi-ep result")
                    continue

                # don't bother with the single result if we're going to get it with a multi result
                for multi_result_episode in multi_result.episodes:
                    multi_results[multi_result_episode] = multi_result

                    if multi_result_episode in found_results:
                        sickrage.app.log.debug("A needed multi-episode result overlaps with a single-episode result for ep #" + str(
                            multi_result_episode) + ", removing the single-episode results from the list")
                        del found_results[multi_result_episode]

        # of all the single ep results narrow it down to the best one
        final_results += list(set(multi_results.values()))
        for curEp, curResults in found_results.items():
            if curEp in (MULTI_EP_RESULT, SEASON_RESULT):
                continue

            if not len(curResults) > 0:
                continue

            # if all results were rejected move on to the next episode
            best_result = pick_best_result(curResults)
            if not best_result:
                continue

            # add result
            final_results.append(best_result)

        # narrow results by comparing quality
        if len(final_results) > 1:
            final_results = list(set([a for a, b in itertools.product(final_results, repeat=len(final_results)) if a.quality >= b.quality]))

        # narrow results by comparing seeders for torrent results
        if len(final_results) > 1:
            final_results = list(set(
                [a for a, b in itertools.product(final_results, repeat=len(final_results)) if a.provider.provider_type == NZBProvider.provider_type or a.seeders > b.seeders]))

        # check that we got all the episodes we wanted first before doing a match and snatch
        for result in final_results.copy():
            if all([episode in result.episodes and is_final_result(result)]):
                return result

    if len(final_results) == 1:
        return next(iter(final_results))
