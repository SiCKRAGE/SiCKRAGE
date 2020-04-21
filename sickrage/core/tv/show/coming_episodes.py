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
from functools import cmp_to_key

import sickrage
from sickrage.core.common import Quality, get_quality_string, WANTED, UNAIRED, timeFormat, dateFormat
from sickrage.core.databases.main import MainDB
from sickrage.core.helpers.srdatetime import SRDateTime
from sickrage.core.tv.show.helpers import get_show_list


class ComingEpisodes:
    """
    Missed:   yesterday...(less than 1 week)
    Today:    today
    Soon:     tomorrow till next week
    Later:    later than next week
    """
    categories = ['later', 'missed', 'soon', 'today']
    sorts = {
        'date': lambda a: a['localtime'].date(),
        'network': cmp_to_key(lambda a, b: (a['network'], a['localtime'].date()) < (b['network'], b['localtime'].date())),
        'show': cmp_to_key(lambda a, b: (a['show_name'], a['localtime'].date()) < (b['show_name'], b['localtime'].date())),
    }

    @staticmethod
    def get_coming_episodes(categories, sort, group, paused=False):
        """
        :param categories: The categories of coming episodes. See ``ComingEpisodes.categories``
        :param sort: The sort to apply to the coming episodes. See ``ComingEpisodes.sorts``
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
                'indexer': episode.indexer,
                'indexer_id': show.indexer_id,
                'name': episode.name,
                'network': show.network,
                'paused': show.paused,
                'quality': show.quality,
                'runtime': show.runtime,
                'season': episode.season,
                'show_name': show.name,
                'showid': episode.showid,
                'status': show.status,
                'localtime': SRDateTime(sickrage.app.tz_updater.parse_date_time(episode.airdate, show.airs, show.network), convert=True).dt
            }

            if grouped:
                to_return['airs'] = SRDateTime(to_return['localtime']).srftime(t_preset=timeFormat).lstrip('0').replace(' 0', ' ')
                to_return['airdate'] = SRDateTime(to_return['localtime']).srfdate(d_preset=dateFormat)
                to_return['quality'] = get_quality_string(to_return['quality'])
                to_return['weekday'] = 1 + to_return['localtime'].date().weekday()
                to_return['tvdbid'] = to_return['indexer_id']

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

        paused = sickrage.app.config.coming_eps_display_paused or paused

        if not isinstance(categories, list):
            categories = categories.split('|')

        if sort not in ComingEpisodes.sorts.keys():
            sort = 'date'

        results = []
        grouped_results = {category: [] for category in categories}

        today = datetime.date.today()
        next_week = datetime.date.today() + datetime.timedelta(days=7)

        recently = datetime.date.today() - datetime.timedelta(days=sickrage.app.config.coming_eps_missed_range)

        qualities_list = Quality.DOWNLOADED + \
                         Quality.SNATCHED + \
                         Quality.SNATCHED_BEST + \
                         Quality.SNATCHED_PROPER + \
                         Quality.ARCHIVED + \
                         Quality.IGNORED

        for show in get_show_list():
            with sickrage.app.main_db.session() as session:
                [add_result(show, episode, grouped=group) for episode in session.query(
                    MainDB.TVEpisode
                ).filter_by(
                    showid=show.indexer_id,
                    indexer=show.indexer
                ).filter(
                    MainDB.TVEpisode.airdate < next_week,
                    MainDB.TVEpisode.airdate >= today,
                    MainDB.TVEpisode.season != 0,
                    ~MainDB.TVEpisode.status.in_(qualities_list)
                )]

                if show.indexer_id not in [int(r['showid']) for r in results]:
                    [add_result(show, episode, grouped=group) for episode in session.query(
                        MainDB.TVEpisode
                    ).filter_by(
                        showid=show.indexer_id,
                        indexer=show.indexer
                    ).filter(
                        MainDB.TVEpisode.airdate >= next_week,
                        MainDB.TVEpisode.season != 0,
                        ~MainDB.TVEpisode.status.in_(Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_BEST + Quality.SNATCHED_PROPER)
                    )]

                [add_result(show, episode, grouped=group) for episode in session.query(
                    MainDB.TVEpisode
                ).filter_by(
                    showid=show.indexer_id,
                    indexer=show.indexer
                ).filter(
                    MainDB.TVEpisode.airdate >= recently,
                    MainDB.TVEpisode.airdate < today,
                    MainDB.TVEpisode.season != 0,
                    MainDB.TVEpisode.status.in_([WANTED, UNAIRED]),
                    ~MainDB.TVEpisode.status.in_(qualities_list)
                )]

        if group:
            for category in categories:
                grouped_results[category].sort(key=ComingEpisodes.sorts[sort])
            return grouped_results
        else:
            results.sort(key=ComingEpisodes.sorts[sort])
            return results
