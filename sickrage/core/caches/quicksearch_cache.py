# ##############################################################################
#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#  -
#  This file is part of SiCKRAGE.
#  -
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  -
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
# ##############################################################################
import threading

import sickrage
from sickrage.core.databases.cache import CacheDB
from sickrage.core.media.util import showImage
from sickrage.core.tv.show.helpers import find_show, get_show_list


class QuicksearchCache(object):
    def __init__(self):
        self.name = "QUICKSEARCH-CACHE"

        self.cache = {
            'shows': {},
            'episodes': {}
        }

    def run(self):
        # set thread name
        threading.currentThread().setName(self.name)

        self.load()
        [self.add_show(show.indexer_id) for show in get_show_list()]

    def load(self):
        session = sickrage.app.cache_db.session()

        for x in session.query(CacheDB.QuickSearchShow):
            self.cache['shows'][x.showid] = x.as_dict()
        for x in session.query(CacheDB.QuickSearchEpisode):
            self.cache['episodes'][x.episodeid] = x.as_dict()

        sickrage.app.log.debug("Loaded {} shows to QuickSearch cache".format(len(self.cache['shows'])))
        sickrage.app.log.debug("Loaded {} episodes to QuickSearch cache".format(len(self.cache['episodes'])))

    def get_shows(self, term):
        return [d for d in self.cache['shows'].values() if d['name'] is not None and term.lower() in d['name'].lower()]

    def get_episodes(self, term):
        return [d for d in self.cache['episodes'].values() if d['name'] is not None and term.lower() in d['name'].lower()]

    def update_show(self, indexer_id):
        self.del_show(indexer_id)
        self.add_show(indexer_id)

    def add_show(self, indexer_id):
        session = sickrage.app.cache_db.session()

        show = find_show(indexer_id)

        if indexer_id not in self.cache['shows']:
            sickrage.app.log.debug("Adding show {} to QuickSearch cache".format(show.name))

            qsData = {
                'category': 'shows',
                'showid': indexer_id,
                'seasons': len(show.episodes),
                'name': show.name,
                'img': sickrage.app.config.web_root + showImage(indexer_id, 'poster_thumb').url
            }

            self.cache['shows'][indexer_id] = qsData
            session.add(CacheDB.QuickSearchShow(**qsData))
            session.commit()

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

            session.bulk_insert_mappings(CacheDB.QuickSearchEpisode, sql_t)
            session.commit()

    def del_show(self, indexer_id):
        session = sickrage.app.cache_db.session()

        show = find_show(indexer_id)

        sickrage.app.log.debug("Deleting show {} from QuickSearch cache".format(show.name))

        if indexer_id in self.cache['shows'].copy():
            del self.cache['shows'][indexer_id]

        for k, v in self.cache['episodes'].copy().items():
            if v['showid'] == indexer_id:
                del self.cache['episodes'][k]

        # remove from database
        session.query(CacheDB.QuickSearchShow).filter_by(showid=indexer_id).delete()
        session.query(CacheDB.QuickSearchEpisode).filter_by(showid=indexer_id).delete()
        session.commit()
