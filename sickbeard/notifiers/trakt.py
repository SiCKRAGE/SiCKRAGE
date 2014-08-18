# Author: Dieter Blomme <dieterblomme@gmail.com>
# URL: http://code.google.com/p/sickbeard/
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

import sickbeard
from sickbeard import logger
from lib.trakt import *


class TraktNotifier:
    """
    A "notifier" for trakt.tv which keeps track of what has and hasn't been added to your library.
    """

    def notify_snatch(self, ep_name):
        pass

    def notify_download(self, ep_name):
        pass

    def notify_subtitle_download(self, ep_name, lang):
        pass
        
    def notify_git_update(self, new_version):
        pass

    def update_library(self, ep_obj):
        """
        Sends a request to trakt indicating that the given episode is part of our library.
        
        ep_obj: The TVEpisode object to add to trakt
        """

        if sickbeard.USE_TRAKT:

            # URL parameters
            data = {
                'tvdb_id': ep_obj.show.indexerid,
                'title': ep_obj.show.name,
                'year': ep_obj.show.startyear,
                'episodes': [{
                                 'season': ep_obj.season,
                                 'episode': ep_obj.episode
                             }]
            }

            if data is not None:
                TraktCall("show/episode/library/%API%", self._api(), self._username(), self._password(), data)
                if sickbeard.TRAKT_REMOVE_WATCHLIST:
                    TraktCall("show/episode/unwatchlist/%API%", self._api(), self._username(), self._password(), data)

                if sickbeard.TRAKT_REMOVE_SERIESLIST:
                    # URL parameters, should not need to recheck data (done above)
                    data = {
                        'tvdb_id': ep_obj.show.indexerid,
                        'title': ep_obj.show.name,'year': ep_obj.show.startyear
                    }
                    TraktCall("show/unwatchlist/%API%", self._api(), self._username(), self._password(), data)

                    # Remove all episodes from episode watchlist
                    # Start by getting all episodes in the watchlist
                    watchlist = TraktCall("user/watchlist/episodes.json/%API%/" + sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_API, sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_PASSWORD)

                    # Convert watchlist to only contain current show
                    for show in watchlist:
                        if unicode(data['shows'][0]['tvdb_id']) == show['tvdb_id']:
                            data_show = {
                                'title': show['title'],
                                'tvdb_id': show['tvdb_id'],
                                'episodes': []
                            }
                            
                            # Add series and episode (number) to the arry
                            for episodes in show['episodes']:
                                ep = {'season': episodes['season'], 'episode': episodes['number']}
                                data_show['episodes'].append(ep)
                    if data_show is not None:
                        TraktCall("show/episode/unwatchlist/%API%", sickbeard.TRAKT_API, sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_PASSWORD, data_show)

    def test_notify(self, api, username, password):
        """
        Sends a test notification to trakt with the given authentication info and returns a boolean
        representing success.
        
        api: The api string to use
        username: The username to use
        password: The password to use
        
        Returns: True if the request succeeded, False otherwise
        """

        data = TraktCall("account/test/%API%", api, username, password)
        if data and data["status"] == "success":
            return True

    def _username(self):
        return sickbeard.TRAKT_USERNAME

    def _password(self):
        return sickbeard.TRAKT_PASSWORD

    def _api(self):
        return sickbeard.TRAKT_API

    def _use_me(self):
        return sickbeard.USE_TRAKT


notifier = TraktNotifier
