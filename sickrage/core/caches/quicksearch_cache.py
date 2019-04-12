# Author: echel0n <echel0n@sickrage.ca>
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
from sickrage.core.databases.cache import CacheDB
from sickrage.core.databases.main import MainDB
from sickrage.core.media.util import showImage


class QuicksearchCache(object):
    def __init__(self):
        self.cache = {
            'shows': {},
            'episodes': {}
        }

    def load(self):
        for x in CacheDB.QuickSearchShow.query:
            self.cache['shows'][x.showid] = x.as_dict()
        for x in CacheDB.QuickSearchEpisode.query:
            self.cache['episodes'][x.episodeid] = x.as_dict()

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
        show = MainDB.TVShow.query.filter_by(indexer_id=indexerid).one()

        if indexerid not in self.cache['shows']:
            sickrage.app.log.debug("Adding show {} to QuickSearch cache".format(show.show_name))

            qsData = {
                'category': 'shows',
                'showid': indexerid,
                'seasons': len(set([e.season for e in show.episodes if e.season != 0])),
                'name': show.show_name,
                'img': sickrage.app.config.web_root + showImage(indexerid, 'poster_thumb').url
            }

            self.cache['shows'][indexerid] = qsData
            sickrage.app.cache_db.add(CacheDB.QuickSearchShow(**qsData))

            sql_l = []
            for e in show.episodes:
                qsData = {
                    'category': 'episodes',
                    'showid': e.showid,
                    'episodeid': e.indexerid,
                    'season': e.season,
                    'episode': e.episode,
                    'name': e.name,
                    'showname': show.show_name,
                    'img': sickrage.app.config.web_root + showImage(e.showid, 'poster_thumb').url
                }

                self.cache['episodes'][e.indexerid] = qsData
                sql_l += [qsData]

            if len(sql_l):
                sickrage.app.cache_db.bulk_add(CacheDB.QuickSearchEpisode, sql_l)
                del sql_l

    def del_show(self, indexerid):
        show = MainDB.TVShow.query.filter_by(indexer_id=indexerid).one()

        sickrage.app.log.debug("Deleting show {} from QuickSearch cache".format(show.show_name))

        if indexerid in self.cache['shows'].copy():
            del self.cache['shows'][indexerid]

        for k, v in self.cache['episodes'].copy().items():
            if v['showid'] == indexerid:
                del self.cache['episodes'][k]

        # remove from database
        sickrage.app.cache_db.delete(CacheDB.QuickSearchShow, showid=indexerid)
        sickrage.app.cache_db.delete(CacheDB.QuickSearchEpisode, showid=indexerid)
