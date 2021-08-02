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


import sickrage
from sickrage.core.enums import SeriesProviderID
from sickrage.core.webserver.handlers.api.v2 import ApiV2BaseHandler


class ApiV2SeriesProvidersHandler(ApiV2BaseHandler):
    def get(self):
        return self.json_response([{'displayName': x.display_name, 'slug': x.slug} for x in SeriesProviderID])


class ApiV2SeriesProvidersSearchHandler(ApiV2BaseHandler):
    def get(self, series_provider_slug):
        search_term = self.get_argument('searchTerm', None)
        lang = self.get_argument('seriesProviderLanguage', None)

        series_provider_id = SeriesProviderID.by_slug(series_provider_slug)
        if not series_provider_id:
            return self._bad_request(error="Unable to identify a series provider using provided slug")

        sickrage.app.log.debug(f"Searching for show with term: {search_term} on series provider: {sickrage.app.series_providers[series_provider_id].name}")

        # search via series name
        results = sickrage.app.series_providers[series_provider_id].search(search_term, language=lang)
        if not results:
            return self._not_found(error=f"Unable to find the series using the search term: {search_term}")

        return self.json_response(results)


class ApiV2SeriesProvidersLanguagesHandler(ApiV2BaseHandler):
    def get(self, series_provider_slug):
        series_provider_id = SeriesProviderID.by_slug(series_provider_slug)
        if not series_provider_id:
            return self._not_found(error="Unable to identify a series provider using provided slug")

        return self.json_response(sickrage.app.series_providers[series_provider_id].languages())
