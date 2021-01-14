# This file is part of SiCKRAGE.
#
# URL: https://www.sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
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
import enum
from functools import cmp_to_key

import sickrage
from sickrage.core.common import Qualities, EpisodeStatus
from sickrage.core.common import timeFormat, dateFormat
from sickrage.core.databases.main import MainDB
from sickrage.core.helpers import flatten
from sickrage.core.helpers.srdatetime import SRDateTime


class ComingEpsLayout(enum.Enum):
    POSTER = 'poster'
    BANNER = 'banner'
    CALENDAR = 'calendar'
    LIST = 'list'

    @property
    def _strings(self):
        return {
            self.POSTER.name: 'Poster',
            self.BANNER.name: 'Banner',
            self.CALENDAR.name: 'Calendar',
            self.LIST.name: 'List',
        }

    @property
    def display_name(self):
        return self._strings[self.name]


class ComingEpsSortBy(enum.Enum):
    DATE = 1
    NETWORK = 2
    SHOW = 3

    @property
    def _strings(self):
        return {
            self.DATE.name: 'Date',
            self.NETWORK.name: 'Network',
            self.SHOW.name: 'Show',
        }

    @property
    def display_name(self):
        return self._strings[self.name]


class ComingEpisodes:
    """
    Missed:   yesterday...(less than 1 week)
    Today:    today
    Soon:     tomorrow till next week
    Later:    later than next week
    """
    categories = ['later', 'missed', 'soon', 'today']

    sort = {
        ComingEpsSortBy.DATE.name: lambda a: a['localtime'].date(),
        ComingEpsSortBy.NETWORK.name: cmp_to_key(lambda a, b: (a['network'], a['localtime'].date()) < (b['network'], b['localtime'].date())),
        ComingEpsSortBy.SHOW.name: cmp_to_key(lambda a, b: (a['show_name'], a['localtime'].date()) < (b['show_name'], b['localtime'].date()))
    }

    @staticmethod
    def get_coming_episodes(categories, sort_by, group, paused=False):
        """
        :param categories: The categories of coming episodes. See ``ComingEpisodes.categories``
        :param sort: The sort to apply to the coming episodes. See ``ComingEpsSortBy``
        :param group: ``True`` to group the coming episodes by category, ``False`` otherwise
        :param paused: ``True`` to include paused shows, ``False`` otherwise
        :return: The list of coming episodes
        """

        def add_result(show, episode, grouped=False):
            to_return = {
                'airdate': episode.airdate,
                'airs': show.airs,
                'description': episode.description,
                'episode': episode.episode,
                'imdb_id': show.imdb_id,
                'series_provider_id': show.series_provider_id,
                'series_id': show.series_id,
                'name': episode.name,
                'network': show.network,
                'paused': show.paused,
                'quality': show.quality,
                'runtime': show.runtime,
                'season': episode.season,
                'show_name': show.name,
                'episode_id': episode.episode_id,
                'status': show.status,
                'localtime': SRDateTime(sickrage.app.tz_updater.parse_date_time(episode.airdate, show.airs, show.network), convert=True).dt
            }

            if grouped:
                to_return['airs'] = SRDateTime(to_return['localtime']).srftime(t_preset=timeFormat).lstrip('0').replace(' 0', ' ')
                to_return['airdate'] = SRDateTime(to_return['localtime']).srfdate(d_preset=dateFormat)
                to_return['quality'] = Qualities(to_return['quality']).display_name
                to_return['weekday'] = 1 + to_return['localtime'].date().weekday()
                to_return['series_provider_id'] = to_return['series_provider_id'].display_name

            if grouped:
                if to_return['paused'] and not paused:
                    return

                if to_return['localtime'].date() < today:
                    category = 'missed'
                elif to_return['localtime'].date() >= next_week:
                    category = 'later'
                elif to_return['localtime'].date() == today:
                    category = 'today'
                else:
                    category = 'soon'

                if len(categories) > 0 and category not in categories:
                    return

                grouped_results[category].append(to_return)
            else:
                results.append(to_return)

        paused = sickrage.app.config.gui.coming_eps_display_paused or paused

        if not isinstance(categories, list):
            categories = categories.split('|')

        results = []
        grouped_results = {category: [] for category in categories}

        today = datetime.date.today()
        next_week = datetime.date.today() + datetime.timedelta(days=7)

        recently = datetime.date.today() - datetime.timedelta(days=sickrage.app.config.gui.coming_eps_missed_range)

        qualities_list = flatten([EpisodeStatus.composites(EpisodeStatus.DOWNLOADED), EpisodeStatus.composites(EpisodeStatus.SNATCHED),
                                  EpisodeStatus.composites(EpisodeStatus.SNATCHED_BEST), EpisodeStatus.composites(EpisodeStatus.SNATCHED_PROPER),
                                  EpisodeStatus.composites(EpisodeStatus.ARCHIVED), EpisodeStatus.composites(EpisodeStatus.IGNORED)])

        with sickrage.app.main_db.session() as session:
            for episode in session.query(MainDB.TVEpisode).filter(
                    MainDB.TVEpisode.airdate <= next_week,
                    MainDB.TVEpisode.airdate >= today,
                    MainDB.TVEpisode.season != 0,
                    ~MainDB.TVEpisode.status.in_(qualities_list)):

                # if not episode.show:
                #     continue

                add_result(episode.show, episode, grouped=group)

            for episode in session.query(MainDB.TVEpisode).filter(
                    MainDB.TVEpisode.airdate >= recently,
                    MainDB.TVEpisode.airdate < today,
                    MainDB.TVEpisode.season != 0,
                    MainDB.TVEpisode.status.in_([EpisodeStatus.WANTED, EpisodeStatus.UNAIRED]),
                    ~MainDB.TVEpisode.status.in_(qualities_list)):

                # if not episode.show:
                #     continue

                add_result(episode.show, episode, grouped=group)

        if group:
            for category in categories:
                grouped_results[category].sort(key=ComingEpisodes.sort[sort_by.name])
            return grouped_results
        else:
            results.sort(key=ComingEpisodes.sort[sort_by.name])
            return results
