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
from sickrage.core.media.util import showImage
from sickrage.core.tv.show.helpers import find_show


class QuicksearchCache(object):
    def __init__(self):
        self.cache = {
            'shows': {},
            'episodes': {}
        }

    def load(self):
        with sickrage.app.cache_db.session() as session:
            for x in session.query(CacheDB.QuickSearchShow):
                self.cache['shows'][x.showid] = x.as_dict()
            for x in session.query(CacheDB.QuickSearchEpisode):
                self.cache['episodes'][x.episodeid] = x.as_dict()

        sickrage.app.log.debug("Loaded {} shows to QuickSearch cache".format(len(self.cache['shows'])))
        sickrage.app.log.debug("Loaded {} episodes to QuickSearch cache".format(len(self.cache['episodes'])))

    def get_shows(self, term):
        return [d for d in self.cache['shows'].values() if term.lower() in d['name'].lower()]

    def get_episodes(self, term):
        return [d for d in self.cache['episodes'].values() if term.lower() in d['name'].lower()]

    def update_show(self, indexer_id):
        self.del_show(indexer_id)
        self.add_show(indexer_id)

    def add_show(self, indexer_id):
        show = find_show(indexer_id)

        if indexer_id not in self.cache['shows']:
            sickrage.app.log.debug("Adding show {} to QuickSearch cache".format(show.name))

            qsData = {
                'category': 'shows',
                'showid': indexer_id,
                'seasons': len(set([e.season for e in show.episodes if e.season != 0])),
                'name': show.name,
                'img': sickrage.app.config.web_root + showImage(indexer_id, 'poster_thumb').url
            }

            self.cache['shows'][indexer_id] = qsData
            sickrage.app.cache_db.add(CacheDB.QuickSearchShow(**qsData))

            sql_t = []
            for e in show.episodes:
                qsData = {
                    'category': 'episodes',
                    'showid': e.showid,
                    'episodeid': e.indexer_id,
                    'season': e.season,
                    'episode': e.episode,
                    'name': e.name,
                    'showname': show.name,
                    'img': sickrage.app.config.web_root + showImage(e.showid, 'poster_thumb').url
                }

                sql_t.append(qsData)

                self.cache['episodes'][e.indexer_id] = qsData

            sickrage.app.cache_db.bulk_add(CacheDB.QuickSearchEpisode, sql_t)

    def del_show(self, indexer_id):
        show = find_show(indexer_id)

        sickrage.app.log.debug("Deleting show {} from QuickSearch cache".format(show.name))

        if indexer_id in self.cache['shows'].copy():
            del self.cache['shows'][indexer_id]

        for k, v in self.cache['episodes'].copy().items():
            if v['showid'] == indexer_id:
                del self.cache['episodes'][k]

        # remove from database
        sickrage.app.cache_db.delete(CacheDB.QuickSearchShow, showid=indexer_id)
        sickrage.app.cache_db.delete(CacheDB.QuickSearchEpisode, showid=indexer_id)
