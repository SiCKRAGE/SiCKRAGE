# This file is part of SickRage.
#
# URL: https://www.sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
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

from datetime import date, timedelta
from sickbeard.common import IGNORED, Quality, WANTED
from sickbeard.db import DBConnection
from sickbeard.network_timezones import parse_date_time
from sickbeard.sbdatetime import sbdatetime
from sickrage.helper.common import dateFormat, timeFormat
from sickrage.helper.quality import get_quality_string


class ComingEpisodes:
    """
    Missed:   yesterday...(less than 1 week)
    Today:    today
    Soon:     tomorrow till next week
    Later:    later than next week
    """
    categories = [u'later', u'missed', u'soon', u'today']
    sorts = {
        'date': (lambda a, b: cmp(a[u'localtime'], b[u'localtime'])),
        'network': (lambda a, b: cmp((a[u'network'], a[u'localtime']), (b[u'network'], b[u'localtime']))),
        'show': (lambda a, b: cmp((a[u'show_name'], a[u'localtime']), (b[u'show_name'], b[u'localtime']))),
    }

    def __init__(self):
        pass

    @staticmethod
    def get_coming_episodes(categories, sort, group, paused=sickbeard.COMING_EPS_DISPLAY_PAUSED):
        """
        :param categories: The categories of coming episodes. See ``ComingEpisodes.categories``
        :param sort: The sort to apply to the coming episodes. See ``ComingEpisodes.sorts``
        :param group: ``True`` to group the coming episodes by category, ``False`` otherwise
        :param paused: ``True`` to include paused shows, ``False`` otherwise
        :return: The list of coming episodes
        """

        if not isinstance(categories, list):
            categories = categories.split('|')

        if sort not in ComingEpisodes.sorts.keys():
            sort = u'date'

        today = date.today().toordinal()
        next_week = (date.today() + timedelta(days=7)).toordinal()
        recently = (date.today() - timedelta(days=sickbeard.COMING_EPS_MISSED_RANGE)).toordinal()
        qualities_list = Quality.DOWNLOADED + Quality.SNATCHED + Quality.ARCHIVED + [IGNORED]

        db = DBConnection()
        fields_to_select = ', '.join(
            [u'airdate', u'airs', u'description', u'episode', u'imdb_id', u'e.indexer', u'indexer_id', u'name',
             u'network', u'paused', u'quality', u'runtime', u'season', u'show_name', u'showid', u's.status']
        )
        results = db.select(
            u'SELECT %s ' % fields_to_select +
            u'FROM tv_episodes e, tv_shows s '
            u'WHERE season != 0 '
            u'AND airdate >= ? '
            u'AND airdate < ? '
            u'AND s.indexer_id = e.showid '
            u'AND e.status NOT IN (' + ','.join([u'?'] * len(qualities_list)) + u')',
            [today, next_week] + qualities_list
        )

        done_shows_list = [int(result['showid']) for result in results]
        placeholder = ','.join([u'?'] * len(done_shows_list))
        placeholder2 = ','.join([u'?'] * len(Quality.DOWNLOADED + Quality.SNATCHED))

        results += db.select(
            u'SELECT %s ' % fields_to_select +
            u'FROM tv_episodes e, tv_shows s '
            u'WHERE season != 0 '
            u'AND showid NOT IN (' + placeholder + u') '
                                                   u'AND s.indexer_id = e.showid '
                                                   u'AND airdate = (SELECT airdate '
                                                   u'FROM tv_episodes inner_e '
                                                   u'WHERE inner_e.season != 0 '
                                                   u'AND inner_e.showid = e.showid '
                                                   u'AND inner_e.airdate >= ? '
                                                   u'ORDER BY inner_e.airdate ASC LIMIT 1) '
                                                   u'AND e.status NOT IN (' + placeholder2 + u')',
            done_shows_list + [next_week] + Quality.DOWNLOADED + Quality.SNATCHED
        )

        results += db.select(
            u'SELECT %s ' % fields_to_select +
            u'FROM tv_episodes e, tv_shows s '
            u'WHERE season != 0 '
            u'AND s.indexer_id = e.showid '
            u'AND airdate < ? '
            u'AND airdate >= ? '
            u'AND e.status = ? '
            u'AND e.status NOT IN (' + ','.join([u'?'] * len(qualities_list)) + u')',
            [today, recently, WANTED] + qualities_list
        )

        results = [dict(result) for result in results]

        for index, item in enumerate(results):
            results[index]['localtime'] = sbdatetime.convert_to_setting(
                parse_date_time(item['airdate'], item['airs'], item['network']))

        results.sort(ComingEpisodes.sorts[sort])

        if not group:
            return results

        grouped_results = {category: [] for category in categories}

        for result in results:
            if result['paused'] and not paused:
                continue

            result['airs'] = str(result['airs']).replace('am', ' AM').replace('pm', ' PM').replace('  ', ' ')
            result['airdate'] = result['localtime'].toordinal()

            if result['airdate'] < today:
                category = 'missed'
            elif result['airdate'] >= next_week:
                category = 'later'
            elif result['airdate'] == today:
                category = 'today'
            else:
                category = 'soon'

            if len(categories) > 0 and category not in categories:
                continue

            if not result['network']:
                result['network'] = u''

            result['quality'] = get_quality_string(result['quality'])
            result['airs'] = sbdatetime.sbftime(result['localtime'], t_preset=timeFormat).lstrip('0').replace(' 0', ' ')
            result['weekday'] = 1 + date.fromordinal(result['airdate']).weekday()
            result['tvdbid'] = result['indexer_id']
            result['airdate'] = sbdatetime.sbfdate(result['localtime'], d_preset=dateFormat)
            result['localtime'] = result['localtime'].toordinal()

            grouped_results[category].append(result)

        return grouped_results
