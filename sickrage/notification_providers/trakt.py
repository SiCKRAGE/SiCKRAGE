# Author: Dieter Blomme <dieterblomme@gmail.com>
# URL: https://sickrage.ca
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


import sickrage
from sickrage.core.traktapi import TraktAPI
from sickrage.notification_providers import NotificationProvider


class TraktNotification(NotificationProvider):
    """
    A "notifier" for trakt.tv which keeps track of what has and hasn't been added to your library.
    """

    def __init__(self):
        super(TraktNotification, self).__init__()
        self.name = 'trakt'

    def notify_snatch(self, ep_name):
        pass

    def notify_download(self, ep_name):
        pass

    def notify_subtitle_download(self, ep_name, lang):
        pass

    def notify_version_update(self, new_version):
        pass

    def update_library(self, ep_obj):
        """
        Sends a request to trakt indicating that the given episode is part of our library.

        ep_obj: The TVEpisode object to add to trakt
        """

        if sickrage.app.config.trakt.enable:
            try:
                # URL parameters
                data = {
                    'shows': [
                        {
                            'title': ep_obj.show.name,
                            'year': ep_obj.show.startyear,
                            'ids': {sickrage.app.series_provider[ep_obj.show.series_provider_id].trakt_id: ep_obj.show.series_id},
                        }
                    ]
                }

                if sickrage.app.config.trakt.sync_watchlist:
                    if sickrage.app.config.trakt.remove_serieslist:
                        TraktAPI()["sync/watchlist"].remove(data)

                # Add Season and Episode + Related Episodes
                data['shows'][0]['seasons'] = [{'number': ep_obj.season, 'episodes': []}]

                for relEp_Obj in [ep_obj] + ep_obj.related_episodes:
                    data['shows'][0]['seasons'][0]['episodes'].append({'number': relEp_Obj.episode})

                if sickrage.app.config.trakt.sync_watchlist:
                    if sickrage.app.config.trakt.remove_watchlist:
                        TraktAPI()["sync/watchlist"].remove(data)

                # update library
                TraktAPI()["sync/collection"].add(data)

            except Exception as e:
                sickrage.app.log.warning("Could not connect to Trakt service: %s" % e)

    def update_watchlist(self, show_object=None, s=None, e=None, data_show=None, data_episode=None, update="add"):

        """
        Sends a request to trakt indicating that the given episode is part of our library.

        show_obj: The TVShow object to add to trakt
        s: season number
        e: episode number
        data_show: structured object of shows traktv type
        data_episode: structured object of episodes traktv type
        update: type o action add or remove
        """

        sickrage.app.log.debug(f"Add episodes, series_id: {show_object.series_id}, Title {show_object.name} to Trak.tv Watchlist")

        if sickrage.app.config.trakt.enable:
            data = {}
            try:
                # URL parameters
                if show_object is not None:
                    data = {
                        'shows': [
                            {
                                'title': show_object.name,
                                'year': show_object.startyear,
                                'ids': {sickrage.app.series_provider[show_object.series_provider_id].trakt_id: show_object.series_id},
                            }
                        ]
                    }
                elif data_show is not None:
                    data.update(data_show)
                else:
                    sickrage.app.log.warning("there's a coding problem contact developer. It's needed to be provided "
                                             "at lest one of the two: data_show or show_obj")
                    return False

                if data_episode is not None:
                    data['shows'][0].update(data_episode)

                elif s is not None:
                    # traktv URL parameters
                    season = {
                        'season': [
                            {
                                'number': s,
                            }
                        ]
                    }

                    if e is not None:
                        # traktv URL parameters
                        episode = {
                            'episodes': [
                                {
                                    'number': e
                                }
                            ]
                        }

                        season['season'][0].update(episode)

                    data['shows'][0].update(season)

                trakt_url = "sync/watchlist"
                if update == "remove":
                    TraktAPI()[trakt_url].remove(data)
                else:
                    TraktAPI()[trakt_url].add(data)

            except Exception as e:
                sickrage.app.log.warning("Could not connect to Trakt service: %s" % e)
                return False

        return True

    def trakt_show_data_generate(self, data):
        show_list = []

        for series_provider_id, series_id, title, year in data:
            show = {'title': title,
                    'year': year,
                    'ids': {sickrage.app.series_provider[series_provider_id].trakt_id: series_id}}

            show_list.append(show)

        post_data = {'shows': show_list}

        return post_data

    def trakt_episode_data_generate(self, data):
        # Find how many unique season we have
        unique_seasons = []

        for season, episode in data:
            if season not in unique_seasons:
                unique_seasons.append(season)

        # build the query
        seasonsList = []
        for searchedSeason in unique_seasons:
            episodesList = []
            for season, episode in data:
                if season == searchedSeason:
                    episodesList.append({'number': episode})
            seasonsList.append({'number': searchedSeason, 'episodes': episodesList})

        post_data = {'seasons': seasonsList}

        return post_data

    def test_notify(self, username, blacklist_name=None):
        """
        Sends a test notification to trakt with the given authentication info and returns a boolean
        representing success.

        api: The api string to use
        username: The username to use
        blacklist_name: slug of trakt list used to hide not interested show

        Returns: True if the request succeeded, False otherwise
        """
        try:
            if blacklist_name and blacklist_name is not None:
                if not TraktAPI()["users/me/lists/{list}".format(list=blacklist_name)].get():
                    return "Trakt blacklist doesn't exists"
            return "Test notice sent successfully to Trakt"
        except Exception as e:
            sickrage.app.log.warning("Could not connect to Trakt service: %s" % e)
            return "Test notice failed to Trakt: %s" % e
