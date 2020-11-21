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

from sickrage.core.common import Qualities, EpisodeStatus
from sickrage.core.databases.config import ConfigDB
from sickrage.core.enums import UserPermission, CheckPropersInterval, NzbMethod, ProcessMethod, FileTimestampTimezone, CpuPreset, MultiEpNaming, \
    DefaultHomePage, TorrentMethod, SearchFormat, PosterSortDirection, HomeLayout, PosterSortBy, HistoryLayout, TimezoneDisplay, UITheme, \
    TraktAddMethod, SeriesProviderID
from sickrage.core.helpers import camelcase
from sickrage.core.tv.show.coming_episodes import ComingEpsLayout, ComingEpsSortBy
from sickrage.notification_providers.nmjv2 import NMJv2Location
from sickrage.search_providers import SearchProviderType


class UsersSchema(SQLAlchemyAutoSchema):
    permissions = EnumField(UserPermission)

    class Meta:
        model = ConfigDB.Users
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class GeneralSchema(SQLAlchemyAutoSchema):
    proper_searcher_interval = EnumField(CheckPropersInterval)
    nzb_method = EnumField(NzbMethod)
    series_provider_default = EnumField(SeriesProviderID)
    process_method = EnumField(ProcessMethod)
    file_timestamp_timezone = EnumField(FileTimestampTimezone)
    cpu_preset = EnumField(CpuPreset)
    naming_multi_ep = EnumField(MultiEpNaming)
    naming_anime_multi_ep = EnumField(MultiEpNaming)
    default_page = EnumField(DefaultHomePage)
    status_default = EnumField(EpisodeStatus)
    status_default_after = EnumField(EpisodeStatus)
    ep_default_deleted_status = EnumField(EpisodeStatus)
    torrent_method = EnumField(TorrentMethod)
    quality_default = EnumField(Qualities)
    search_format_default = EnumField(SearchFormat)

    class Meta:
        model = ConfigDB.General
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class GUISchema(SQLAlchemyAutoSchema):
    poster_sort_dir = EnumField(PosterSortDirection)
    home_layout = EnumField(HomeLayout)
    coming_eps_layout = EnumField(ComingEpsLayout)
    coming_eps_sort = EnumField(ComingEpsSortBy)
    poster_sort_by = EnumField(PosterSortBy)
    history_layout = EnumField(HistoryLayout)
    timezone_display = EnumField(TimezoneDisplay)
    theme_name = EnumField(UITheme)

    class Meta:
        model = ConfigDB.GUI
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class BlackholeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.Blackhole
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class SABnzbdSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.SABnzbd
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class NZBgetSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.NZBget
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class SynologySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.Synology
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class TorrentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.Torrent
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class KodiSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.Kodi
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class PlexSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.Plex
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class EmbySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.Emby
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class GrowlSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.Growl
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class FreeMobileSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.FreeMobile
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class TelegramSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.Telegram
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class JoinSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.Join
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class ProwlSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.Prowl
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class TwitterSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.Twitter
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class TwilioSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.Twilio
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class Boxcar2Schema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.Boxcar2
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class PushoverSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.Pushover
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class LibnotifySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.Libnotify
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class NMJSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.NMJ
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class NMJv2Schema(SQLAlchemyAutoSchema):
    db_loc = EnumField(NMJv2Location)

    class Meta:
        model = ConfigDB.NMJv2
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class SlackSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.Slack
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class DiscordSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.Discord
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class TraktSchema(SQLAlchemyAutoSchema):
    method_add = EnumField(TraktAddMethod)
    series_provider_default = EnumField(SeriesProviderID)

    class Meta:
        model = ConfigDB.Trakt
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class PyTivoSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.PyTivo
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class NMASchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.NMA
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class PushalotSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.Pushalot
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class PushbulletSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.Pushbullet
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class EmailSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.Email
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class AlexaSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.Alexa
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class SubtitlesSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.Subtitles
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class FailedDownloadsSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.FailedDownloads
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class FailedSnatchesSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.FailedSnatches
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class AniDBSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.AniDB
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class QualitySizesSchema(SQLAlchemyAutoSchema):
    quality = EnumField(Qualities)

    class Meta:
        model = ConfigDB.QualitySizes
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class SearchProvidersTorrentSchema(SQLAlchemyAutoSchema):
    provider_type = EnumField(SearchProviderType)

    class Meta:
        model = ConfigDB.SearchProvidersTorrent
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class SearchProvidersNzbSchema(SQLAlchemyAutoSchema):
    provider_type = EnumField(SearchProviderType)

    class Meta:
        model = ConfigDB.SearchProvidersNzb
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class SearchProvidersTorrentRssSchema(SQLAlchemyAutoSchema):
    provider_type = EnumField(SearchProviderType)

    class Meta:
        model = ConfigDB.SearchProvidersTorrentRss
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class SearchProvidersNewznabSchema(SQLAlchemyAutoSchema):
    provider_type = EnumField(SearchProviderType)

    class Meta:
        model = ConfigDB.SearchProvidersNewznab
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class MetadataProvidersSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ConfigDB.MetadataProviders
        include_relationships = False
        load_instance = True

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)
