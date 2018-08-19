# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
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

import sickrage
from sickrage.core.media.util import showImage


class QuicksearchCache(object):
    def __init__(self):
        self.cache = {
            'shows': {},
            'episodes': {}
        }

    def load(self):
        for x in sickrage.app.cache_db.all('quicksearch'):
            if x['category'] == 'shows':
                self.cache['shows'][x['showid']] = x
            elif x['category'] == 'episodes':
                self.cache['episodes'][x['episodeid']] = x

        sickrage.app.log.debug("Loaded {} shows to QuickSearch cache".format(len(self.cache['shows'])))
        sickrage.app.log.debug("Loaded {} episodes to QuickSearch cache".format(len(self.cache['episodes'])))

    def get_shows(self, term):
        return [d for d in self.cache['shows'].values() if term.lower() in d['name'].lower()]

    def get_episodes(self, term):
        return [d for d in self.cache['episodes'].values() if term.lower() in d['name'].lower()]

    def update_show(self, indexerid):
        self.del_show(indexerid)
        self.add_show(indexerid)

    def add_show(self, indexerid):
        show_name = sickrage.app.main_db.get('tv_shows', indexerid)['show_name']

        if indexerid not in self.cache['shows']:
            sickrage.app.log.debug("Adding show {} to QuickSearch cache".format(show_name))

            qsData = {
                '_t': 'quicksearch',
                'category': 'shows',
                'showid': indexerid,
                'seasons': len(set([e['season'] for e in sickrage.app.main_db.get_many('tv_episodes', indexerid) if e['season'] != 0])),
                'name': show_name,
                'img': sickrage.app.config.web_root + showImage(indexerid, 'poster_thumb').url
            }

            self.cache['shows'][indexerid] = qsData
            sickrage.app.cache_db.insert(qsData)

            for e in sickrage.app.main_db.get_many('tv_episodes', indexerid):
                qsData = {
                    '_t': 'quicksearch',
                    'category': 'episodes',
                    'showid': e['showid'],
                    'episodeid': e['indexerid'],
                    'season': e['season'],
                    'episode': e['episode'],
                    'name': e['name'],
                    'showname': show_name,
                    'img': sickrage.app.config.web_root + showImage(e['showid'], 'poster_thumb').url
                }

                self.cache['episodes'][e['indexerid']] = qsData
                sickrage.app.cache_db.insert(qsData)

    def del_show(self, indexerid):
        show_name = sickrage.app.main_db.get('tv_shows', indexerid)['show_name']

        sickrage.app.log.debug("Deleting show {} from QuickSearch cache".format(show_name))

        if indexerid in self.cache['shows']:
            del self.cache['shows'][indexerid]

        for k, v in self.cache['episodes'].items():
            if v['showid'] == indexerid:
                del self.cache['episodes'][k]

        # remove from database
        [sickrage.app.cache_db.delete(x) for x in sickrage.app.cache_db.get_many('quicksearch', indexerid)]
