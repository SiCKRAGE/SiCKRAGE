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
from abc import ABC

import sickrage
from sickrage.core.webserver.handlers.api.v2 import APIv2BaseHandler
from sickrage.indexers import IndexerApi


class IndexersHandler(APIv2BaseHandler, ABC):
    def get(self):
        self.write_json(IndexerApi().indexers)


class IndexersSearchHandler(APIv2BaseHandler, ABC):
    def get(self, indexer_slug):
        search_term = self.get_argument('searchTerm', None)
        lang = self.get_argument('indexerLanguage', None)

        indexer_id = IndexerApi().indexers_by_slug[indexer_slug]['id']

        indexer_api_params = IndexerApi(indexer_id).api_params.copy()
        indexer_api_params['language'] = lang
        indexer_api = IndexerApi(indexer_id).indexer(**indexer_api_params)

        sickrage.app.log.debug("Searching for Show with term: %s on Indexer: %s" % (search_term, IndexerApi(indexer_id).name))

        # search via series name
        results = indexer_api.search(search_term)
        if not results:
            return self.send_error(404, reason="Unable to find the series using the search term: {}".format(search_term))

        return self.write_json(results)


class IndexersLanguagesHandler(APIv2BaseHandler, ABC):
    def get(self, indexer_slug):
        indexer_id = IndexerApi().indexers_by_slug[indexer_slug]['id']

        self.write_json(IndexerApi(indexer_id).indexer().languages())
