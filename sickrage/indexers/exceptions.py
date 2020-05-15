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


from sickrage.indexers.thetvdb.exceptions import tvdb_attributenotfound, tvdb_episodenotfound, tvdb_error, tvdb_exception, tvdb_seasonnotfound, \
    tvdb_showincomplete, tvdb_shownotfound

indexerExcepts = ["indexer_exception", "indexer_error", "indexer_userabort", "indexer_shownotfound",
                  "indexer_showincomplete", "indexer_seasonnotfound", "indexer_episodenotfound",
                  "indexer_attributenotfound"]

tvdbExcepts = ["tvdb_exception", "tvdb_error", "tvdb_shownotfound", "tvdb_showincomplete",
               "tvdb_seasonnotfound", "tvdb_episodenotfound", "tvdb_attributenotfound"]

# link API exceptions to our exception handler
indexer_exception = tvdb_exception
indexer_error = tvdb_error
indexer_attributenotfound = tvdb_attributenotfound
indexer_episodenotfound = tvdb_episodenotfound
indexer_seasonnotfound = tvdb_seasonnotfound
indexer_shownotfound = tvdb_shownotfound
indexer_showincomplete = tvdb_showincomplete
