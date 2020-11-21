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
from marshmallow_enum import EnumField
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from sickrage.core.common import EpisodeStatus, Qualities
from sickrage.core.databases.main import MainDB
from sickrage.core.enums import SearchFormat, SeriesProviderID
from sickrage.core.helpers import camelcase


class TVShowSchema(SQLAlchemyAutoSchema):
    search_format = EnumField(SearchFormat)
    series_provider_id = EnumField(SeriesProviderID)
    default_ep_status = EnumField(EpisodeStatus)
    quality = EnumField(Qualities)

    class Meta:
        model = MainDB.TVShow
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class TVEpisodeSchema(SQLAlchemyAutoSchema):
    series_provider_id = EnumField(SeriesProviderID)
    status = EnumField(EpisodeStatus)

    class Meta:
        model = MainDB.TVEpisode
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class IMDbInfoSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = MainDB.IMDbInfo
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class BlacklistSchema(SQLAlchemyAutoSchema):
    series_provider_id = EnumField(SeriesProviderID)

    class Meta:
        model = MainDB.Blacklist
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class WhitelistSchema(SQLAlchemyAutoSchema):
    series_provider_id = EnumField(SeriesProviderID)

    class Meta:
        model = MainDB.Whitelist
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class HistoryScheme(SQLAlchemyAutoSchema):
    series_provider_id = EnumField(SeriesProviderID)
    quality = EnumField(Qualities)

    class Meta:
        model = MainDB.History
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class FailedSnatchHistoryScheme(SQLAlchemyAutoSchema):
    series_provider_id = EnumField(SeriesProviderID)
    old_status = EnumField(EpisodeStatus)

    class Meta:
        model = MainDB.FailedSnatchHistory
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)
