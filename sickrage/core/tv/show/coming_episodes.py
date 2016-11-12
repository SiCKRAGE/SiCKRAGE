# This file is part of SickRage.
#
# URL: https://www.sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
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

import sickrage
from sickrage.core.common import Quality, get_quality_string, WANTED, UNAIRED, timeFormat, dateFormat
from sickrage.core.helpers.srdatetime import srDateTime
from sickrage.core.updaters.tz_updater import parse_date_time


class ComingEpisodes:
    """
    Missed:   yesterday...(less than 1 week)
    Today:    today
    Soon:     tomorrow till next week
    Later:    later than next week
    """
    categories = ['later', 'missed', 'soon', 'today']
    sorts = {
        'date': (lambda a, b: cmp(a['localtime'], b['localtime'])),
        'network': (lambda a, b: cmp((a['network'], a['localtime']), (b['network'], b['localtime']))),
        'show': (lambda a, b: cmp((a['show_name'], a['localtime']), (b['show_name'], b['localtime']))),
    }

    def __init__(self):
        pass

    @staticmethod
    def get_coming_episodes(categories, sort, group, paused=False):
        """
        :param categories: The categories of coming episodes. See ``ComingEpisodes.categories``
        :param sort: The sort to apply to the coming episodes. See ``ComingEpisodes.sorts``
        :param group: ``True`` to group the coming episodes by category, ``False`` otherwise
        :param paused: ``True`` to include paused shows, ``False`` otherwise
        :return: The list of coming episodes
        """

        paused = sickrage.srCore.srConfig.COMING_EPS_DISPLAY_PAUSED or paused

        if not isinstance(categories, list):
            categories = categories.split('|')

        if sort not in ComingEpisodes.sorts.keys():
            sort = 'date'

        today = datetime.date.today().toordinal()
        next_week = (datetime.date.today() + datetime.timedelta(days=7)).toordinal()

        recently = (
            datetime.date.today() - datetime.timedelta(
                days=sickrage.srCore.srConfig.COMING_EPS_MISSED_RANGE)).toordinal()

        qualities_list = Quality.DOWNLOADED + \
                         Quality.SNATCHED + \
                         Quality.SNATCHED_BEST + \
                         Quality.SNATCHED_PROPER + \
                         Quality.ARCHIVED + \
                         Quality.IGNORED

        results = []
        for s in [s['doc'] for s in sickrage.srCore.mainDB.db.all('tv_shows', with_doc=True)]:
            for e in [e['doc'] for e in sickrage.srCore.mainDB.db.get_many('tv_episodes', s['indexer_id'], with_doc=True)
                      if e['doc']['season'] != 0
                      and today <= e['doc']['airdate'] < next_week
                      and e['doc']['status'] not in qualities_list]:
                results += [{
                    'airdate': e['airdate'],
                    'airs': s['airs'],
                    'description': e['description'],
                    'episode': e['episode'],
                    'imdb_id': s['imdb_id'],
                    'indexer': e['indexer'],
                    'indexer_id': s['indexer_id'],
                    'name': e['name'],
                    'network': s['network'],
                    'paused': s['paused'],
                    'quality': s['quality'],
                    'runtime': s['runtime'],
                    'season': e['season'],
                    'show_name': s['show_name'],
                    'showid': e['showid'],
                    'status': s['status']
                }]

        done_shows_list = [int(result['showid']) for result in results]

        for s in [s['doc'] for s in sickrage.srCore.mainDB.db.all('tv_shows', with_doc=True)]:
            for e in [e['doc'] for e in sickrage.srCore.mainDB.db.get_many('tv_episodes', s['indexer_id'], with_doc=True)
                      if e['doc']['season'] != 0
                      and e['doc']['showid'] not in done_shows_list
                      and e['doc']['airdate'] >= next_week
                      and e['doc']['status'] not in Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_BEST + Quality.SNATCHED_PROPER]:
                results += [{
                    'airdate': e['airdate'],
                    'airs': s['airs'],
                    'description': e['description'],
                    'episode': e['episode'],
                    'imdb_id': s['imdb_id'],
                    'indexer': e['indexer'],
                    'indexer_id': s['indexer_id'],
                    'name': e['name'],
                    'network': s['network'],
                    'paused': s['paused'],
                    'quality': s['quality'],
                    'runtime': s['runtime'],
                    'season': e['season'],
                    'show_name': s['show_name'],
                    'showid': e['showid'],
                    'status': s['status']
                }]

        for s in [s['doc'] for s in sickrage.srCore.mainDB.db.all('tv_shows', with_doc=True)]:
            for e in [e['doc'] for e in sickrage.srCore.mainDB.db.get_many('tv_episodes', s['indexer_id'], with_doc=True)
                      if e['doc']['season'] != 0
                      and today > e['doc']['airdate'] >= recently
                      and e['doc']['status'] in [WANTED, UNAIRED] and e['doc']['status'] not in qualities_list]:
                results += [{
                    'airdate': e['airdate'],
                    'airs': s['airs'],
                    'description': e['description'],
                    'episode': e['episode'],
                    'imdb_id': s['imdb_id'],
                    'indexer': e['indexer'],
                    'indexer_id': s['indexer_id'],
                    'name': e['name'],
                    'network': s['network'],
                    'paused': s['paused'],
                    'quality': s['quality'],
                    'runtime': s['runtime'],
                    'season': e['season'],
                    'show_name': s['show_name'],
                    'showid': e['showid'],
                    'status': s['status']
                }]

        for index, item in enumerate(results):
            results[index]['localtime'] = srDateTime.convert_to_setting(
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
                result['network'] = ''

            result['quality'] = get_quality_string(result['quality'])
            result['airs'] = srDateTime.srftime(result['localtime'], t_preset=timeFormat).lstrip('0').replace(' 0',
                                                                                                              ' ')
            result['weekday'] = 1 + datetime.date.fromordinal(result['airdate']).weekday()
            result['tvdbid'] = result['indexer_id']
            result['airdate'] = srDateTime.srfdate(result['localtime'], d_preset=dateFormat)
            result['localtime'] = result['localtime'].toordinal()

            grouped_results[category].append(result)

        return grouped_results
