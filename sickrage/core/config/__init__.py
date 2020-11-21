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
import os

from sqlalchemy import exc, orm

import sickrage
from sickrage.core.common import Qualities, EpisodeStatus
from sickrage.core.config.helpers import decrypt_config
from sickrage.core.databases.config import ConfigDB
from sickrage.core.databases.config.schemas import GeneralSchema, GUISchema, BlackholeSchema, SABnzbdSchema, NZBgetSchema, SynologySchema, \
    TorrentSchema, KodiSchema, PlexSchema, EmbySchema, GrowlSchema, FreeMobileSchema, TelegramSchema, JoinSchema, ProwlSchema, TwitterSchema, TwilioSchema, \
    Boxcar2Schema, PushoverSchema, LibnotifySchema, NMJSchema, NMJv2Schema, SlackSchema, DiscordSchema, TraktSchema, PyTivoSchema, NMASchema, PushalotSchema, \
    PushbulletSchema, EmailSchema, AlexaSchema, SubtitlesSchema, FailedDownloadsSchema, FailedSnatchesSchema, QualitySizesSchema, AniDBSchema, \
    MetadataProvidersSchema, SearchProvidersTorrentSchema, SearchProvidersNzbSchema, SearchProvidersTorrentRssSchema, SearchProvidersNewznabSchema
from sickrage.core.enums import UserPermission, CheckPropersInterval, NzbMethod, ProcessMethod, FileTimestampTimezone, MultiEpNaming, \
    DefaultHomePage, TorrentMethod, SearchFormat, PosterSortDirection, HomeLayout, PosterSortBy, \
    TimezoneDisplay, HistoryLayout, UITheme, TraktAddMethod, SeriesProviderID, CpuPreset
from sickrage.core.helpers import backup_versioned_file, arg_to_bool, auto_type
from sickrage.core.helpers.encryption import load_private_key
from sickrage.core.tv.show.coming_episodes import ComingEpsLayout, ComingEpsSortBy
from sickrage.notification_providers.nmjv2 import NMJv2Location
from sickrage.search_providers import SearchProviderType, TorrentRssProvider, NewznabProvider


class Config(object):
    def __init__(self, db_type, db_prefix, db_host, db_port, db_username, db_password):
        self.db = ConfigDB(db_type, db_prefix, db_host, db_port, db_username, db_password)
        self.session = self.db.session()

        # sections
        self.user = None
        self.general = None
        self.gui = None
        self.blackhole = None
        self.sabnzbd = None
        self.nzbget = None
        self.synology = None
        self.torrent = None
        self.kodi = None
        self.plex = None
        self.emby = None
        self.growl = None
        self.freemobile = None
        self.telegram = None
        self.join_app = None
        self.prowl = None
        self.twitter = None
        self.twilio = None
        self.boxcar2 = None
        self.pushover = None
        self.libnotify = None
        self.nmj = None
        self.nmjv2 = None
        self.slack = None
        self.discord = None
        self.trakt = None
        self.pytivo = None
        self.nma = None
        self.pushalot = None
        self.pushbullet = None
        self.email = None
        self.alexa = None
        self.subtitles = None
        self.failed_downloads = None
        self.failed_snatches = None
        self.anidb = None
        self.quality_sizes = {}

    def load(self):
        self.user = self.session.query(self.db.Users).first()
        if not self.user:
            self.user = self.db.Users(username='admin', permissions=UserPermission.SUPERUSER)
            self.session.add(self.user)
            self.session.commit()

        self.general = self.session.query(self.db.General).first()
        if not self.general:
            self.general = self.db.General()
            self.session.add(self.general)
            self.session.commit()

        self.gui = self.session.query(self.db.GUI).first()
        if not self.gui:
            self.gui = self.db.GUI(user_id=self.user.id)
            self.session.add(self.gui)
            self.session.commit()

        self.blackhole = self.session.query(self.db.Blackhole).first()
        if not self.blackhole:
            self.blackhole = self.db.Blackhole()
            self.session.add(self.blackhole)
            self.session.commit()

        self.sabnzbd = self.session.query(self.db.SABnzbd).first()
        if not self.sabnzbd:
            self.sabnzbd = self.db.SABnzbd()
            self.session.add(self.sabnzbd)
            self.session.commit()

        self.nzbget = self.session.query(self.db.NZBget).first()
        if not self.nzbget:
            self.nzbget = self.db.NZBget()
            self.session.add(self.nzbget)
            self.session.commit()

        self.synology = self.session.query(self.db.Synology).first()
        if not self.synology:
            self.synology = self.db.Synology()
            self.session.add(self.synology)
            self.session.commit()

        self.torrent = self.session.query(self.db.Torrent).first()
        if not self.torrent:
            self.torrent = self.db.Torrent()
            self.session.add(self.torrent)
            self.session.commit()

        self.kodi = self.session.query(self.db.Kodi).first()
        if not self.kodi:
            self.kodi = self.db.Kodi()
            self.session.add(self.kodi)
            self.session.commit()

        self.plex = self.session.query(self.db.Plex).first()
        if not self.plex:
            self.plex = self.db.Plex()
            self.session.add(self.plex)
            self.session.commit()

        self.emby = self.session.query(self.db.Emby).first()
        if not self.emby:
            self.emby = self.db.Emby()
            self.session.add(self.emby)
            self.session.commit()

        self.growl = self.session.query(self.db.Growl).first()
        if not self.growl:
            self.growl = self.db.Growl()
            self.session.add(self.growl)
            self.session.commit()

        self.freemobile = self.session.query(self.db.FreeMobile).first()
        if not self.freemobile:
            self.freemobile = self.db.FreeMobile()
            self.session.add(self.freemobile)
            self.session.commit()

        self.telegram = self.session.query(self.db.Telegram).first()
        if not self.telegram:
            self.telegram = self.db.Telegram()
            self.session.add(self.telegram)
            self.session.commit()

        self.join_app = self.session.query(self.db.Join).first()
        if not self.join_app:
            self.join_app = self.db.Join()
            self.session.add(self.join_app)
            self.session.commit()

        self.prowl = self.session.query(self.db.Prowl).first()
        if not self.prowl:
            self.prowl = self.db.Prowl()
            self.session.add(self.prowl)
            self.session.commit()

        self.twitter = self.session.query(self.db.Twitter).first()
        if not self.twitter:
            self.twitter = self.db.Twitter()
            self.session.add(self.twitter)
            self.session.commit()

        self.twilio = self.session.query(self.db.Twilio).first()
        if not self.twilio:
            self.twilio = self.db.Twilio()
            self.session.add(self.twilio)
            self.session.commit()

        self.boxcar2 = self.session.query(self.db.Boxcar2).first()
        if not self.boxcar2:
            self.boxcar2 = self.db.Boxcar2()
            self.session.add(self.boxcar2)
            self.session.commit()

        self.pushover = self.session.query(self.db.Pushover).first()
        if not self.pushover:
            self.pushover = self.db.Pushover()
            self.session.add(self.pushover)
            self.session.commit()

        self.libnotify = self.session.query(self.db.Libnotify).first()
        if not self.libnotify:
            self.libnotify = self.db.Libnotify()
            self.session.add(self.libnotify)
            self.session.commit()

        self.nmj = self.session.query(self.db.NMJ).first()
        if not self.nmj:
            self.nmj = self.db.NMJ()
            self.session.add(self.nmj)
            self.session.commit()

        self.nmjv2 = self.session.query(self.db.NMJv2).first()
        if not self.nmjv2:
            self.nmjv2 = self.db.NMJv2()
            self.session.add(self.nmjv2)
            self.session.commit()

        self.slack = self.session.query(self.db.Slack).first()
        if not self.slack:
            self.slack = self.db.Slack()
            self.session.add(self.slack)
            self.session.commit()

        self.discord = self.session.query(self.db.Discord).first()
        if not self.discord:
            self.discord = self.db.Discord()
            self.session.add(self.discord)
            self.session.commit()

        self.trakt = self.session.query(self.db.Trakt).first()
        if not self.trakt:
            self.trakt = self.db.Trakt()
            self.session.add(self.trakt)
            self.session.commit()

        self.pytivo = self.session.query(self.db.PyTivo).first()
        if not self.pytivo:
            self.pytivo = self.db.PyTivo()
            self.session.add(self.pytivo)
            self.session.commit()

        self.nma = self.session.query(self.db.NMA).first()
        if not self.nma:
            self.nma = self.db.NMA()
            self.session.add(self.nma)
            self.session.commit()

        self.pushalot = self.session.query(self.db.Pushalot).first()
        if not self.pushalot:
            self.pushalot = self.db.Pushalot()
            self.session.add(self.pushalot)
            self.session.commit()

        self.pushbullet = self.session.query(self.db.Pushbullet).first()
        if not self.pushbullet:
            self.pushbullet = self.db.Pushbullet()
            self.session.add(self.pushbullet)
            self.session.commit()

        self.email = self.session.query(self.db.Email).first()
        if not self.email:
            self.email = self.db.Email()
            self.session.add(self.email)
            self.session.commit()

        self.alexa = self.session.query(self.db.Alexa).first()
        if not self.alexa:
            self.alexa = self.db.Alexa()
            self.session.add(self.alexa)
            self.session.commit()

        self.subtitles = self.session.query(self.db.Subtitles).first()
        if not self.subtitles:
            self.subtitles = self.db.Subtitles()
            self.session.add(self.subtitles)
            self.session.commit()

        self.failed_downloads = self.session.query(self.db.FailedDownloads).first()
        if not self.failed_downloads:
            self.failed_downloads = self.db.FailedDownloads()
            self.session.add(self.failed_downloads)
            self.session.commit()

        self.failed_snatches = self.session.query(self.db.FailedSnatches).first()
        if not self.failed_snatches:
            self.failed_snatches = self.db.FailedSnatches()
            self.session.add(self.failed_snatches)
            self.session.commit()

        self.anidb = self.session.query(self.db.AniDB).first()
        if not self.anidb:
            self.anidb = self.db.AniDB()
            self.session.add(self.anidb)
            self.session.commit()

        # QUALITY SIZES
        for quality in Qualities:
            if quality.is_preset or quality.is_combined:
                continue

            if quality in [Qualities.NONE, Qualities.UNKNOWN]:
                continue

            try:
                quality_size = self.session.query(self.db.QualitySizes).filter_by(quality=quality).one()
            except orm.exc.NoResultFound:
                quality_size = self.db.QualitySizes(quality=quality, min_size=0, max_size=0)
                self.session.add(quality_size)
                self.session.commit()

            self.quality_sizes[quality_size.quality.name] = {
                'min_size': quality_size.min_size,
                'max_size': quality_size.max_size,
            }

        # CUSTOM SEARCH PROVIDERS
        for search_providers in self.session.query(self.db.SearchProvidersTorrentRss, self.db.SearchProvidersNewznab):
            for search_provider in search_providers:
                if search_provider.provider_id in sickrage.app.search_providers.all():
                    continue

                if search_provider.provider_type == SearchProviderType.TORRENT_RSS:
                    sickrage.app.search_providers[search_provider.provider_type.name][search_provider.provider_id] = TorrentRssProvider(**{
                        'name': search_provider.name,
                        'url': search_provider.url,
                        'titleTAG': search_provider.title_tag
                    })
                elif search_provider.provider_type == SearchProviderType.NEWZNAB:
                    sickrage.app.search_providers[search_provider.provider_type.name][search_provider.provider_id] = NewznabProvider(**{
                        'name': search_provider.name,
                        'url': search_provider.url,
                        'key': search_provider.key,
                        'catIDs': search_provider.cat_ids
                    })

        # SEARCH PROVIDERS
        for search_provider_id, _search_provider in sickrage.app.search_providers.all().items():
            search_provider = None

            try:
                if _search_provider.provider_type == SearchProviderType.TORRENT:
                    search_provider = self.session.query(self.db.SearchProvidersTorrent).filter_by(provider_id=search_provider_id).one()
                elif _search_provider.provider_type == SearchProviderType.NZB:
                    search_provider = self.session.query(self.db.SearchProvidersNzb).filter_by(provider_id=search_provider_id).one()
                elif _search_provider.provider_type == SearchProviderType.TORRENT_RSS:
                    search_provider = self.session.query(self.db.SearchProvidersTorrentRss).filter_by(provider_id=search_provider_id).one()
                elif _search_provider.provider_type == SearchProviderType.NEWZNAB:
                    search_provider = self.session.query(self.db.SearchProvidersNewznab).filter_by(provider_id=search_provider_id).one()

                if search_provider:
                    if search_provider.provider_type in [SearchProviderType.TORRENT, SearchProviderType.TORRENT_RSS]:
                        sickrage.app.search_providers.all()[search_provider.provider_id].ratio = search_provider.ratio
                    elif search_provider.provider_type in [SearchProviderType.NZB, SearchProviderType.NEWZNAB]:
                        sickrage.app.search_providers.all()[search_provider.provider_id].api_key = search_provider.api_key
                        sickrage.app.search_providers.all()[search_provider.provider_id].username = search_provider.username

                    sickrage.app.search_providers.all()[search_provider.provider_id].search_mode = search_provider.search_mode
                    sickrage.app.search_providers.all()[search_provider.provider_id].search_separator = search_provider.search_separator
                    sickrage.app.search_providers.all()[search_provider.provider_id].cookies = search_provider.cookies
                    sickrage.app.search_providers.all()[search_provider.provider_id].proper_strings = search_provider.proper_strings.split(',')
                    sickrage.app.search_providers.all()[search_provider.provider_id].private = search_provider.private
                    sickrage.app.search_providers.all()[search_provider.provider_id].supports_backlog = search_provider.supports_backlog
                    sickrage.app.search_providers.all()[search_provider.provider_id].supports_absolute_numbering = search_provider.supports_absolute_numbering
                    sickrage.app.search_providers.all()[search_provider.provider_id].anime_only = search_provider.anime_only
                    sickrage.app.search_providers.all()[search_provider.provider_id].search_fallback = search_provider.search_fallback
                    sickrage.app.search_providers.all()[search_provider.provider_id].enable_daily = search_provider.enable_daily
                    sickrage.app.search_providers.all()[search_provider.provider_id].enable_backlog = search_provider.enable_backlog
                    sickrage.app.search_providers.all()[search_provider.provider_id].enable_cookies = search_provider.enable_cookies
                    sickrage.app.search_providers.all()[search_provider.provider_id].enabled = search_provider.enable
                    sickrage.app.search_providers.all()[search_provider.provider_id].sort_order = search_provider.sort_order
                    sickrage.app.search_providers.all()[search_provider.provider_id].custom_settings = search_provider.custom_settings
            except orm.exc.NoResultFound:
                continue

        # METADATA PROVIDERS
        for metadata_provider_id in sickrage.app.metadata_providers:
            try:
                metadata_provider = self.session.query(self.db.MetadataProviders).filter_by(provider_id=metadata_provider_id).one()

                sickrage.app.metadata_providers[metadata_provider.provider_id].show_metadata = metadata_provider.show_metadata
                sickrage.app.metadata_providers[metadata_provider.provider_id].episode_metadata = metadata_provider.episode_metadata
                sickrage.app.metadata_providers[metadata_provider.provider_id].fanart = metadata_provider.fanart
                sickrage.app.metadata_providers[metadata_provider.provider_id].poster = metadata_provider.poster
                sickrage.app.metadata_providers[metadata_provider.provider_id].banner = metadata_provider.banner
                sickrage.app.metadata_providers[metadata_provider.provider_id].episode_thumbnails = metadata_provider.episode_thumbnails
                sickrage.app.metadata_providers[metadata_provider.provider_id].season_posters = metadata_provider.season_posters
                sickrage.app.metadata_providers[metadata_provider.provider_id].season_banners = metadata_provider.season_banners
                sickrage.app.metadata_providers[metadata_provider.provider_id].season_all_poster = metadata_provider.season_all_poster
                sickrage.app.metadata_providers[metadata_provider.provider_id].season_all_banner = metadata_provider.season_all_banner
                sickrage.app.metadata_providers[metadata_provider.provider_id].enabled = metadata_provider.enable
            except orm.exc.NoResultFound:
                continue

    def save(self):
        try:
            # QUALITY SIZES
            for quality_size in self.session.query(self.db.QualitySizes):
                quality_size.min_size = self.quality_sizes[quality_size.quality.name]['min_size']
                quality_size.max_size = self.quality_sizes[quality_size.quality.name]['max_size']

                self.session.commit()

            # SEARCH PROVIDERS
            for _search_provider_id, _search_provider in sickrage.app.search_providers.all().copy().items():
                search_provider = None

                if _search_provider.provider_type == SearchProviderType.TORRENT:
                    try:
                        search_provider = self.session.query(self.db.SearchProvidersTorrent).filter_by(provider_id=_search_provider_id).one()
                    except orm.exc.NoResultFound:
                        search_provider = self.db.SearchProvidersTorrent(provider_id=_search_provider_id, provider_type=_search_provider.provider_type)
                        self.session.add(search_provider)
                        self.session.commit()
                elif _search_provider.provider_type == SearchProviderType.NZB:
                    try:
                        search_provider = self.session.query(self.db.SearchProvidersNzb).filter_by(provider_id=_search_provider_id).one()
                    except orm.exc.NoResultFound:
                        search_provider = self.db.SearchProvidersNzb(provider_id=_search_provider_id, provider_type=_search_provider.provider_type)
                        self.session.add(search_provider)
                        self.session.commit()
                elif _search_provider.provider_type == SearchProviderType.TORRENT_RSS:
                    try:
                        search_provider = self.session.query(self.db.SearchProvidersTorrentRss).filter_by(provider_id=_search_provider_id).one()
                        if _search_provider.provider_deleted:
                            del sickrage.app.search_providers[_search_provider.provider_type.name][_search_provider_id]
                            self.session.query(self.db.SearchProvidersTorrentRss).filter_by(provider_id=_search_provider_id).delete()
                            self.session.commit()
                            continue
                    except orm.exc.NoResultFound:
                        search_provider = self.db.SearchProvidersTorrentRss(provider_id=_search_provider_id, provider_type=_search_provider.provider_type)
                        self.session.add(search_provider)
                        self.session.commit()

                    search_provider.name = sickrage.app.search_providers.all()[search_provider.provider_id].name
                    search_provider.url = sickrage.app.search_providers.all()[search_provider.provider_id].urls['base_url']
                    search_provider.title_tag = sickrage.app.search_providers.all()[search_provider.provider_id].titleTAG
                elif _search_provider.provider_type == SearchProviderType.NEWZNAB:
                    try:
                        search_provider = self.session.query(self.db.SearchProvidersNewznab).filter_by(provider_id=_search_provider_id).one()
                        if _search_provider.provider_deleted:
                            del sickrage.app.search_providers[_search_provider.provider_type.name][_search_provider_id]
                            self.session.query(self.db.SearchProvidersNewznab).filter_by(provider_id=_search_provider_id).delete()
                            self.session.commit()
                            continue
                    except orm.exc.NoResultFound:
                        search_provider = self.db.SearchProvidersNewznab(provider_id=_search_provider_id, provider_type=_search_provider.provider_type)
                        self.session.add(search_provider)
                        self.session.commit()

                    search_provider.name = sickrage.app.search_providers.all()[search_provider.provider_id].name
                    search_provider.url = sickrage.app.search_providers.all()[search_provider.provider_id].urls['base_url']
                    search_provider.key = sickrage.app.search_providers.all()[search_provider.provider_id].key
                    search_provider.cat_ids = sickrage.app.search_providers.all()[search_provider.provider_id].catIDs

                if search_provider:
                    if search_provider.provider_type in [SearchProviderType.TORRENT, SearchProviderType.TORRENT_RSS]:
                        search_provider.ratio = sickrage.app.search_providers.all()[search_provider.provider_id].ratio
                    elif search_provider.provider_type in [SearchProviderType.NZB, SearchProviderType.NEWZNAB]:
                        search_provider.api_key = sickrage.app.search_providers.all()[search_provider.provider_id].api_key
                        search_provider.username = sickrage.app.search_providers.all()[search_provider.provider_id].username

                    search_provider.search_mode = sickrage.app.search_providers.all()[search_provider.provider_id].search_mode
                    search_provider.search_separator = sickrage.app.search_providers.all()[search_provider.provider_id].search_separator
                    search_provider.cookies = sickrage.app.search_providers.all()[search_provider.provider_id].cookies
                    search_provider.proper_strings = ','.join(sickrage.app.search_providers.all()[search_provider.provider_id].proper_strings)
                    search_provider.private = sickrage.app.search_providers.all()[search_provider.provider_id].private
                    search_provider.supports_backlog = sickrage.app.search_providers.all()[search_provider.provider_id].supports_backlog
                    search_provider.supports_absolute_numbering = sickrage.app.search_providers.all()[search_provider.provider_id].supports_absolute_numbering
                    search_provider.anime_only = sickrage.app.search_providers.all()[search_provider.provider_id].anime_only
                    search_provider.search_fallback = sickrage.app.search_providers.all()[search_provider.provider_id].search_fallback
                    search_provider.enable_daily = sickrage.app.search_providers.all()[search_provider.provider_id].enable_daily
                    search_provider.enable_backlog = sickrage.app.search_providers.all()[search_provider.provider_id].enable_backlog
                    search_provider.enable_cookies = sickrage.app.search_providers.all()[search_provider.provider_id].enable_cookies
                    search_provider.enable = sickrage.app.search_providers.all()[search_provider.provider_id].enabled
                    search_provider.sort_order = sickrage.app.search_providers.all()[search_provider.provider_id].sort_order
                    search_provider.custom_settings = sickrage.app.search_providers.all()[search_provider.provider_id].custom_settings

                    self.session.commit()

            # METADATA PROVIDERS
            for metadata_provider_id in sickrage.app.metadata_providers:
                try:
                    metadata_provider = self.session.query(self.db.MetadataProviders).filter_by(provider_id=metadata_provider_id).one()
                except orm.exc.NoResultFound:
                    metadata_provider = self.db.MetadataProviders(provider_id=metadata_provider_id)
                    self.session.add(metadata_provider)
                    self.session.commit()

                metadata_provider.show_metadata = sickrage.app.metadata_providers[metadata_provider.provider_id].show_metadata
                metadata_provider.episode_metadata = sickrage.app.metadata_providers[metadata_provider.provider_id].episode_metadata
                metadata_provider.fanart = sickrage.app.metadata_providers[metadata_provider.provider_id].fanart
                metadata_provider.poster = sickrage.app.metadata_providers[metadata_provider.provider_id].poster
                metadata_provider.banner = sickrage.app.metadata_providers[metadata_provider.provider_id].banner
                metadata_provider.episode_thumbnails = sickrage.app.metadata_providers[metadata_provider.provider_id].episode_thumbnails
                metadata_provider.season_posters = sickrage.app.metadata_providers[metadata_provider.provider_id].season_posters
                metadata_provider.season_banners = sickrage.app.metadata_providers[metadata_provider.provider_id].season_banners
                metadata_provider.season_all_poster = sickrage.app.metadata_providers[metadata_provider.provider_id].season_all_poster
                metadata_provider.season_all_banner = sickrage.app.metadata_providers[metadata_provider.provider_id].season_all_banner
                metadata_provider.enable = sickrage.app.metadata_providers[metadata_provider.provider_id].enabled

                self.session.commit()

            sickrage.app.log.info("Config saved to database successfully!")
        except exc.StatementError as e:
            sickrage.app.log.warning("Failed to save config to database")
            sickrage.app.log.debug(f"Failed to save config to database: {e}")

    def migrate_config_file(self, filename):
        try:
            private_key_filename = os.path.join(sickrage.app.data_dir, 'privatekey.pem')
            config_object = decrypt_config(filename, load_private_key(private_key_filename))
        except Exception as e:
            sickrage.app.log.warning(f"Unable to decrypt config file {filename}, config can not be migrated to database")
            return

        config_version = self._get_config_file_value(config_object, 'General', 'config_version', field_type=int)

        sickrage.app.log.info("Backing up config and private key files before performing migration to database")

        if not backup_versioned_file(filename, config_version):
            sickrage.app.log.fatal("Failed to backup config, aborting migration of config file to database")
            return

        if not backup_versioned_file(private_key_filename, config_version):
            sickrage.app.log.fatal("Failed to backup config private key, aborting migration of config file to database")
            return

        sickrage.app.log.info("Migrating config file to database")

        # USER SETTINGS
        self.user.username = self._get_config_file_value(config_object, 'General', 'web_username', field_type=str)
        self.user.password = self._get_config_file_value(config_object, 'General', 'web_password', field_type=str)
        self.user.sub_id = self._get_config_file_value(config_object, 'General', 'sub_id', field_type=str)

        # GENERAL SETTINGS
        self.general.server_id = self._get_config_file_value(config_object, 'General', 'server_id', field_type=str)
        self.general.sso_auth_enabled = self._get_config_file_value(config_object, 'General', 'sso_auth_enabled', field_type=bool)
        self.general.local_auth_enabled = self._get_config_file_value(config_object, 'General', 'local_auth_enabled', field_type=bool)
        self.general.ip_whitelist_enabled = self._get_config_file_value(config_object, 'General', 'ip_whitelist_enabled', field_type=bool)
        self.general.ip_whitelist_localhost_enabled = self._get_config_file_value(config_object, 'General', 'ip_whitelist_localhost_enabled', field_type=bool)
        self.general.ip_whitelist = self._get_config_file_value(config_object, 'General', 'ip_whitelist', field_type=str)
        if not any([self.general.sso_auth_enabled, self.general.local_auth_enabled, self.general.ip_whitelist_enabled]):
            self.general.sso_auth_enabled = True

        self.general.enable_sickrage_api = self._get_config_file_value(config_object, 'General', 'enable_sickrage_api', field_type=bool)
        self.general.debug = self._get_config_file_value(config_object, 'General', 'debug', field_type=bool)
        self.general.log_nr = self._get_config_file_value(config_object, 'General', 'log_nr', field_type=int)
        self.general.log_size = self._get_config_file_value(config_object, 'General', 'log_size', field_type=int)
        self.general.socket_timeout = self._get_config_file_value(config_object, 'General', 'socket_timeout', field_type=int)
        self.general.default_page = DefaultHomePage[self._get_config_file_value(config_object, 'General', 'default_page', field_type=str.upper)]
        self.general.pip3_path = self._get_config_file_value(config_object, 'General', 'pip3_path', field_type=str)
        self.general.git_path = self._get_config_file_value(config_object, 'General', 'git_path', field_type=str)
        self.general.git_reset = self._get_config_file_value(config_object, 'General', 'git_reset', field_type=bool)
        self.general.web_port = self._get_config_file_value(config_object, 'General', 'web_port', default=8081, field_type=int)
        self.general.web_host = self._get_config_file_value(config_object, 'General', 'web_host', default='0.0.0.0', field_type=str)
        self.general.web_log = self._get_config_file_value(config_object, 'General', 'web_log', field_type=str)
        self.general.web_external_port = self._get_config_file_value(config_object, 'General', 'web_external_port', default=8081, field_type=int)
        self.general.web_ipv6 = self._get_config_file_value(config_object, 'General', 'web_ipv6', field_type=bool)
        self.general.web_root = self._get_config_file_value(config_object, 'General', 'web_root', field_type=str).lstrip('/').rstrip('/')
        self.general.web_cookie_secret = self._get_config_file_value(config_object, 'General', 'web_cookie_secret', field_type=str)
        self.general.web_use_gzip = self._get_config_file_value(config_object, 'General', 'web_use_gzip', field_type=bool)
        self.general.ssl_verify = self._get_config_file_value(config_object, 'General', 'ssl_verify', field_type=bool)
        self.general.launch_browser = self._get_config_file_value(config_object, 'General', 'launch_browser', field_type=bool)
        self.general.series_provider_default_language = self._get_config_file_value(config_object, 'General', 'indexer_default_lang', field_type=str)
        self.general.ep_default_deleted_status = EpisodeStatus(
            self._get_config_file_value(config_object, 'General', 'ep_default_deleted_status', default=EpisodeStatus.WANTED.value, field_type=int))
        self.general.download_url = self._get_config_file_value(config_object, 'General', 'download_url', field_type=str)
        self.general.cpu_preset = CpuPreset[
            self._get_config_file_value(config_object, 'General', 'cpu_preset', default=CpuPreset.NORMAL.name, field_type=str.upper)]
        self.general.max_queue_workers = self._get_config_file_value(config_object, 'General', 'max_queue_workers', field_type=int)
        self.general.anon_redirect = self._get_config_file_value(config_object, 'General', 'anon_redirect', field_type=str)
        self.general.proxy_setting = self._get_config_file_value(config_object, 'General', 'proxy_setting', field_type=str)
        self.general.proxy_series_providers = self._get_config_file_value(config_object, 'General', 'proxy_indexers', field_type=bool)
        self.general.trash_remove_show = self._get_config_file_value(config_object, 'General', 'trash_remove_show', field_type=bool)
        self.general.trash_rotate_logs = self._get_config_file_value(config_object, 'General', 'trash_rotate_logs', field_type=bool)
        self.general.sort_article = self._get_config_file_value(config_object, 'General', 'sort_article', field_type=bool)
        self.general.api_v1_key = self._get_config_file_value(config_object, 'General', 'api_key', field_type=str)
        self.general.enable_https = self._get_config_file_value(config_object, 'General', 'enable_https', field_type=bool)
        self.general.https_cert = self._get_config_file_value(config_object, 'General', 'https_cert', field_type=str)
        self.general.https_key = self._get_config_file_value(config_object, 'General', 'https_key', field_type=str)
        self.general.handle_reverse_proxy = self._get_config_file_value(config_object, 'General', 'handle_reverse_proxy', field_type=bool)
        self.general.root_dirs = self._get_config_file_value(config_object, 'General', 'root_dirs', field_type=str)
        self.general.quality_default = Qualities(self._get_config_file_value(config_object, 'General', 'quality_default', field_type=int))
        self.general.status_default = EpisodeStatus(self._get_config_file_value(config_object, 'General', 'status_default', field_type=int))
        self.general.status_default_after = EpisodeStatus(self._get_config_file_value(config_object, 'General', 'status_default_after', field_type=int))
        self.general.enable_upnp = self._get_config_file_value(config_object, 'General', 'enable_upnp', field_type=bool)
        self.general.version_notify = self._get_config_file_value(config_object, 'General', 'version_notify', field_type=bool)
        self.general.auto_update = self._get_config_file_value(config_object, 'General', 'auto_update', field_type=bool)
        self.general.notify_on_update = self._get_config_file_value(config_object, 'General', 'notify_on_update', field_type=bool)
        self.general.backup_on_update = self._get_config_file_value(config_object, 'General', 'backup_on_update', field_type=bool)
        self.general.notify_on_login = self._get_config_file_value(config_object, 'General', 'notify_on_login', field_type=bool)
        self.general.flatten_folders_default = self._get_config_file_value(config_object, 'General', 'flatten_folders_default', field_type=bool)
        self.general.series_provider_default = SeriesProviderID.THETVDB
        self.general.series_provider_timeout = self._get_config_file_value(config_object, 'General', 'indexer_timeout', field_type=int)
        self.general.anime_default = self._get_config_file_value(config_object, 'General', 'anime_default', field_type=bool)
        self.general.search_format_default = SearchFormat(
            self._get_config_file_value(config_object, 'General', 'search_format_default', field_type=int) or SearchFormat.STANDARD)
        self.general.scene_default = self._get_config_file_value(config_object, 'General', 'scene_default', field_type=bool)
        self.general.skip_downloaded_default = self._get_config_file_value(config_object, 'General', 'skip_downloaded_default', field_type=bool)
        self.general.add_show_year_default = self._get_config_file_value(config_object, 'General', 'add_show_year_default', field_type=bool)
        self.general.naming_pattern = self._get_config_file_value(config_object, 'General', 'naming_pattern', field_type=str)
        self.general.naming_abd_pattern = self._get_config_file_value(config_object, 'General', 'naming_abd_pattern', field_type=str)
        self.general.naming_custom_abd = self._get_config_file_value(config_object, 'General', 'naming_custom_abd', field_type=bool)
        self.general.naming_sports_pattern = self._get_config_file_value(config_object, 'General', 'naming_sports_pattern', field_type=str)
        self.general.naming_anime_pattern = self._get_config_file_value(config_object, 'General', 'naming_anime_pattern', field_type=str)
        self.general.naming_anime = self._get_config_file_value(config_object, 'General', 'naming_anime', field_type=int)
        self.general.naming_custom_sports = self._get_config_file_value(config_object, 'General', 'naming_custom_sports', field_type=bool)
        self.general.naming_custom_anime = self._get_config_file_value(config_object, 'General', 'naming_custom_anime', field_type=bool)
        self.general.naming_multi_ep = MultiEpNaming(self._get_config_file_value(config_object, 'General', 'naming_multi_ep', field_type=int))
        self.general.naming_anime_multi_ep = MultiEpNaming(self._get_config_file_value(config_object, 'General', 'naming_anime_multi_ep', field_type=int))
        self.general.naming_strip_year = self._get_config_file_value(config_object, 'General', 'naming_strip_year', field_type=bool)
        self.general.use_nzbs = self._get_config_file_value(config_object, 'General', 'use_nzbs', field_type=bool)
        self.general.use_torrents = self._get_config_file_value(config_object, 'General', 'use_torrents', field_type=bool)
        self.general.nzb_method = NzbMethod[self._get_config_file_value(config_object, 'General', 'nzb_method', field_type=str.upper)]
        self.general.torrent_method = TorrentMethod[self._get_config_file_value(config_object, 'General', 'torrent_method', field_type=str.upper)]
        self.general.download_propers = self._get_config_file_value(config_object, 'General', 'download_propers', field_type=bool)
        self.general.enable_rss_cache = self._get_config_file_value(config_object, 'General', 'enable_rss_cache', field_type=bool)
        self.general.torrent_file_to_magnet = self._get_config_file_value(config_object, 'General', 'torrent_file_to_magnet', field_type=bool)
        self.general.torrent_magnet_to_file = self._get_config_file_value(config_object, 'General', 'torrent_magnet_to_file', field_type=bool)
        self.general.download_unverified_magnet_link = self._get_config_file_value(config_object, 'General', 'download_unverified_magnet_link',
                                                                                   field_type=bool)
        self.general.proper_searcher_interval = CheckPropersInterval.DAILY
        self.general.randomize_providers = self._get_config_file_value(config_object, 'General', 'randomize_providers', field_type=bool)
        self.general.allow_high_priority = self._get_config_file_value(config_object, 'General', 'allow_high_priority', field_type=bool)
        self.general.skip_removed_files = self._get_config_file_value(config_object, 'General', 'skip_removed_files', field_type=bool)
        self.general.usenet_retention = self._get_config_file_value(config_object, 'General', 'usenet_retention', field_type=int)
        self.general.daily_searcher_freq = self._get_config_file_value(config_object, 'General', 'dailysearch_frequency', field_type=int)
        self.general.backlog_searcher_freq = self._get_config_file_value(config_object, 'General', 'backlog_frequency', field_type=int)
        self.general.version_updater_freq = self._get_config_file_value(config_object, 'General', 'update_frequency', field_type=int)
        self.general.subtitle_searcher_freq = self._get_config_file_value(config_object, 'Subtitles', 'subtitles_finder_frequency', field_type=int)
        self.general.show_update_stale = self._get_config_file_value(config_object, 'General', 'showupdate_stale', field_type=bool)
        self.general.show_update_hour = self._get_config_file_value(config_object, 'General', 'showupdate_hour', field_type=int)
        self.general.backlog_days = self._get_config_file_value(config_object, 'General', 'backlog_days', field_type=int)
        self.general.auto_postprocessor_freq = self._get_config_file_value(config_object, 'General', 'autopostprocessor_frequency', field_type=int)
        self.general.tv_download_dir = self._get_config_file_value(config_object, 'General', 'tv_download_dir', field_type=str)
        self.general.process_automatically = self._get_config_file_value(config_object, 'General', 'process_automatically', field_type=bool)
        self.general.no_delete = self._get_config_file_value(config_object, 'General', 'no_delete', field_type=bool)
        self.general.unpack = self._get_config_file_value(config_object, 'General', 'unpack', field_type=bool)
        self.general.unpack_dir = self._get_config_file_value(config_object, 'General', 'unpack_dir', field_type=str)
        self.general.rename_episodes = self._get_config_file_value(config_object, 'General', 'rename_episodes', field_type=bool)
        self.general.airdate_episodes = self._get_config_file_value(config_object, 'General', 'airdate_episodes', field_type=bool)
        self.general.file_timestamp_timezone = FileTimestampTimezone[
            self._get_config_file_value(config_object, 'General', 'file_timestamp_timezone', field_type=str.upper)]
        self.general.keep_processed_dir = self._get_config_file_value(config_object, 'General', 'keep_processed_dir', field_type=bool)
        self.general.process_method = ProcessMethod[self._get_config_file_value(config_object, 'General', 'process_method', field_type=str.upper)]
        self.general.processor_follow_symlinks = self._get_config_file_value(config_object, 'General', 'processor_follow_symlinks', field_type=bool)
        self.general.del_rar_contents = self._get_config_file_value(config_object, 'General', 'del_rar_contents', field_type=bool)
        self.general.delete_non_associated_files = self._get_config_file_value(config_object, 'General', 'delete_non_associated_files', field_type=bool)
        self.general.move_associated_files = self._get_config_file_value(config_object, 'General', 'move_associated_files', field_type=bool)
        self.general.postpone_if_sync_files = self._get_config_file_value(config_object, 'General', 'postpone_if_sync_files', field_type=bool)
        self.general.sync_files = self._get_config_file_value(config_object, 'General', 'sync_files', field_type=str)
        self.general.nfo_rename = self._get_config_file_value(config_object, 'General', 'nfo_rename', field_type=bool)
        self.general.create_missing_show_dirs = self._get_config_file_value(config_object, 'General', 'create_missing_show_dirs', field_type=bool)
        self.general.add_shows_wo_dir = self._get_config_file_value(config_object, 'General', 'add_shows_wo_dir', field_type=bool)
        self.general.require_words = self._get_config_file_value(config_object, 'General', 'require_words', field_type=str)
        self.general.ignore_words = self._get_config_file_value(config_object, 'General', 'ignore_words', field_type=str)
        self.general.ignored_subs_list = self._get_config_file_value(config_object, 'General', 'ignored_subs_list', field_type=str)
        self.general.calendar_unprotected = self._get_config_file_value(config_object, 'General', 'calendar_unprotected', field_type=bool)
        self.general.calendar_icons = self._get_config_file_value(config_object, 'General', 'calendar_icons', field_type=bool)
        self.general.no_restart = self._get_config_file_value(config_object, 'General', 'no_restart', field_type=bool)
        self.general.allowed_video_file_exts = ','.join(self._get_config_file_value(config_object, 'General', 'allowed_video_file_exts', field_type=list))
        self.general.extra_scripts = self._get_config_file_value(config_object, 'General', 'extra_scripts', field_type=str)
        self.general.display_all_seasons = self._get_config_file_value(config_object, 'General', 'display_all_seasons', field_type=bool)
        self.general.random_user_agent = self._get_config_file_value(config_object, 'General', 'random_user_agent', field_type=bool)
        self.general.allowed_extensions = self._get_config_file_value(config_object, 'General', 'allowed_extensions', field_type=str)
        self.general.view_changelog = self._get_config_file_value(config_object, 'General', 'view_changelog', field_type=bool)
        self.general.strip_special_file_bits = self._get_config_file_value(config_object, 'General', 'strip_special_file_bits', field_type=bool)

        # GUI SETTINGS
        self.gui.gui_lang = self._get_config_file_value(config_object, 'GUI', 'gui_lang', field_type=str)
        self.gui.theme_name = UITheme[self._get_config_file_value(config_object, 'GUI', 'theme_name', field_type=str.upper)]
        self.gui.fanart_background = self._get_config_file_value(config_object, 'GUI', 'fanart_background', field_type=bool)
        self.gui.fanart_background_opacity = self._get_config_file_value(config_object, 'GUI', 'fanart_background_opacity', field_type=float)
        self.gui.home_layout = HomeLayout[self._get_config_file_value(config_object, 'GUI', 'home_layout', field_type=str.upper)]
        self.gui.history_layout = HistoryLayout[self._get_config_file_value(config_object, 'GUI', 'history_layout', field_type=str.upper)]
        self.gui.history_limit = self._get_config_file_value(config_object, 'GUI', 'history_limit', field_type=int)
        self.gui.display_show_specials = self._get_config_file_value(config_object, 'GUI', 'display_show_specials', field_type=bool)
        self.gui.coming_eps_layout = ComingEpsLayout[self._get_config_file_value(config_object, 'GUI', 'coming_eps_layout', field_type=str.upper)]
        self.gui.coming_eps_display_paused = self._get_config_file_value(config_object, 'GUI', 'coming_eps_display_paused', field_type=bool)
        self.gui.coming_eps_sort = ComingEpsSortBy[self._get_config_file_value(config_object, 'GUI', 'coming_eps_sort', field_type=str.upper)]
        self.gui.coming_eps_missed_range = self._get_config_file_value(config_object, 'GUI', 'coming_eps_missed_range', field_type=int)
        self.gui.fuzzy_dating = self._get_config_file_value(config_object, 'GUI', 'fuzzy_dating', field_type=bool)
        self.gui.trim_zero = self._get_config_file_value(config_object, 'GUI', 'trim_zero', field_type=bool)
        self.gui.date_preset = self._get_config_file_value(config_object, 'GUI', 'date_preset', field_type=str)
        self.gui.time_preset_w_seconds = self._get_config_file_value(config_object, 'GUI', 'time_preset', field_type=str)
        self.gui.time_preset = self.gui.time_preset_w_seconds.replace(":%S", "")
        self.gui.timezone_display = TimezoneDisplay[self._get_config_file_value(config_object, 'GUI', 'timezone_display', field_type=str.upper)]
        self.gui.poster_sort_by = PosterSortBy[self._get_config_file_value(config_object, 'GUI', 'poster_sortby', field_type=str.upper)]
        self.gui.poster_sort_dir = PosterSortDirection(self._get_config_file_value(config_object, 'GUI', 'poster_sortdir', field_type=int))
        self.gui.filter_row = self._get_config_file_value(config_object, 'GUI', 'filter_row', field_type=bool)

        # BLACKHOLE SETTINGS
        self.blackhole.nzb_dir = self._get_config_file_value(config_object, 'Blackhole', 'nzb_dir', field_type=str)
        self.blackhole.torrent_dir = self._get_config_file_value(config_object, 'Blackhole', 'torrent_dir', field_type=str)

        # SABNZBD SETTINGS
        self.sabnzbd.username = self._get_config_file_value(config_object, 'SABnzbd', 'sab_username', field_type=str)
        self.sabnzbd.password = self._get_config_file_value(config_object, 'SABnzbd', 'sab_password', field_type=str)
        self.sabnzbd.apikey = self._get_config_file_value(config_object, 'SABnzbd', 'sab_apikey', field_type=str)
        self.sabnzbd.category = self._get_config_file_value(config_object, 'SABnzbd', 'sab_category', field_type=str)
        self.sabnzbd.category_backlog = self._get_config_file_value(config_object, 'SABnzbd', 'sab_category_backlog', field_type=str)
        self.sabnzbd.category_anime = self._get_config_file_value(config_object, 'SABnzbd', 'sab_category_anime', field_type=str)
        self.sabnzbd.category_anime_backlog = self._get_config_file_value(config_object, 'SABnzbd', 'sab_category_anime_backlog', field_type=str)
        self.sabnzbd.host = self._get_config_file_value(config_object, 'SABnzbd', 'sab_host', field_type=str)
        self.sabnzbd.forced = self._get_config_file_value(config_object, 'SABnzbd', 'sab_forced', field_type=bool)

        # NZBGET SETTINGS
        self.nzbget.username = self._get_config_file_value(config_object, 'NZBget', 'nzbget_username', field_type=str)
        self.nzbget.password = self._get_config_file_value(config_object, 'NZBget', 'nzbget_password', field_type=str)
        self.nzbget.category = self._get_config_file_value(config_object, 'NZBget', 'nzbget_category', field_type=str)
        self.nzbget.category_backlog = self._get_config_file_value(config_object, 'NZBget', 'nzbget_category_backlog', field_type=str)
        self.nzbget.category_anime = self._get_config_file_value(config_object, 'NZBget', 'nzbget_category_anime', field_type=str)
        self.nzbget.category_anime_backlog = self._get_config_file_value(config_object, 'NZBget', 'nzbget_category_anime_backlog', field_type=str)
        self.nzbget.host = self._get_config_file_value(config_object, 'NZBget', 'nzbget_host', field_type=str)
        self.nzbget.use_https = self._get_config_file_value(config_object, 'NZBget', 'nzbget_use_https', field_type=bool)
        self.nzbget.priority = self._get_config_file_value(config_object, 'NZBget', 'nzbget_priority', field_type=int)

        # TORRENT SETTINGS
        self.torrent.username = self._get_config_file_value(config_object, 'TORRENT', 'torrent_username', field_type=str)
        self.torrent.password = self._get_config_file_value(config_object, 'TORRENT', 'torrent_password', field_type=str)
        self.torrent.host = self._get_config_file_value(config_object, 'TORRENT', 'torrent_host', field_type=str)
        self.torrent.path = self._get_config_file_value(config_object, 'TORRENT', 'torrent_path', field_type=str)
        self.torrent.seed_time = self._get_config_file_value(config_object, 'TORRENT', 'torrent_seed_time', field_type=int)
        self.torrent.paused = self._get_config_file_value(config_object, 'TORRENT', 'torrent_paused', field_type=bool)
        self.torrent.high_bandwidth = self._get_config_file_value(config_object, 'TORRENT', 'torrent_high_bandwidth', field_type=bool)
        self.torrent.label = self._get_config_file_value(config_object, 'TORRENT', 'torrent_label', field_type=str)
        self.torrent.label_anime = self._get_config_file_value(config_object, 'TORRENT', 'torrent_label_anime', field_type=str)
        self.torrent.verify_cert = self._get_config_file_value(config_object, 'TORRENT', 'torrent_verify_cert', field_type=bool)
        self.torrent.rpc_url = self._get_config_file_value(config_object, 'TORRENT', 'torrent_rpcurl', field_type=str)
        self.torrent.auth_type = self._get_config_file_value(config_object, 'TORRENT', 'torrent_auth_type', field_type=str)

        # KODI SETTINGS
        self.kodi.enable = self._get_config_file_value(config_object, 'KODI', 'use_kodi', field_type=bool)
        self.kodi.always_on = self._get_config_file_value(config_object, 'KODI', 'kodi_always_on', field_type=bool)
        self.kodi.notify_on_snatch = self._get_config_file_value(config_object, 'KODI', 'kodi_notify_onsnatch', field_type=bool)
        self.kodi.notify_on_download = self._get_config_file_value(config_object, 'KODI', 'kodi_notify_ondownload', field_type=bool)
        self.kodi.notify_on_subtitle_download = self._get_config_file_value(config_object, 'KODI', 'kodi_notify_onsubtitledownload', field_type=bool)
        self.kodi.update_library = self._get_config_file_value(config_object, 'KODI', 'kodi_update_library', field_type=bool)
        self.kodi.update_full = self._get_config_file_value(config_object, 'KODI', 'kodi_update_full', field_type=bool)
        self.kodi.update_only_first = self._get_config_file_value(config_object, 'KODI', 'kodi_update_onlyfirst', field_type=bool)
        self.kodi.host = self._get_config_file_value(config_object, 'KODI', 'kodi_host', field_type=str)
        self.kodi.username = self._get_config_file_value(config_object, 'KODI', 'kodi_username', field_type=str)
        self.kodi.password = self._get_config_file_value(config_object, 'KODI', 'kodi_password', field_type=str)

        # PLEX SETTINGS
        self.plex.enable = self._get_config_file_value(config_object, 'Plex', 'use_plex', field_type=bool)
        self.plex.notify_on_snatch = self._get_config_file_value(config_object, 'Plex', 'plex_notify_onsnatch', field_type=bool)
        self.plex.notify_on_download = self._get_config_file_value(config_object, 'Plex', 'plex_notify_ondownload', field_type=bool)
        self.plex.notify_on_subtitle_download = self._get_config_file_value(config_object, 'Plex', 'plex_notify_onsubtitledownload', field_type=bool)
        self.plex.update_library = self._get_config_file_value(config_object, 'Plex', 'plex_update_library', field_type=bool)
        self.plex.server_host = self._get_config_file_value(config_object, 'Plex', 'plex_server_host', field_type=str)
        self.plex.server_token = self._get_config_file_value(config_object, 'Plex', 'plex_server_token', field_type=str)
        self.plex.host = self._get_config_file_value(config_object, 'Plex', 'plex_host', field_type=str)
        self.plex.username = self._get_config_file_value(config_object, 'Plex', 'plex_username', field_type=str)
        self.plex.password = self._get_config_file_value(config_object, 'Plex', 'plex_password', field_type=str)
        self.plex.enable_client = self._get_config_file_value(config_object, 'Plex', 'use_plex_client', field_type=bool)
        self.plex.client_username = self._get_config_file_value(config_object, 'Plex', 'plex_client_username', field_type=str)
        self.plex.client_password = self._get_config_file_value(config_object, 'Plex', 'plex_client_password', field_type=str)

        # EMBY SETTINGS
        self.emby.enable = self._get_config_file_value(config_object, 'Emby', 'use_emby', field_type=bool)
        self.emby.notify_on_snatch = self._get_config_file_value(config_object, 'Emby', 'emby_notify_onsnatch', field_type=bool)
        self.emby.notify_on_download = self._get_config_file_value(config_object, 'Emby', 'emby_notify_ondownload', field_type=bool)
        self.emby.notify_on_subtitle_download = self._get_config_file_value(config_object, 'Emby', 'emby_notify_onsubtitledownload', field_type=bool)
        self.emby.host = self._get_config_file_value(config_object, 'Emby', 'emby_host', field_type=str)
        self.emby.apikey = self._get_config_file_value(config_object, 'Emby', 'emby_apikey', field_type=str)

        # GROWL SETTINGS
        self.growl.enable = self._get_config_file_value(config_object, 'Growl', 'use_growl', field_type=bool)
        self.growl.notify_on_snatch = self._get_config_file_value(config_object, 'Growl', 'growl_notify_onsnatch', field_type=bool)
        self.growl.notify_on_download = self._get_config_file_value(config_object, 'Growl', 'growl_notify_ondownload', field_type=bool)
        self.growl.notify_on_subtitle_download = self._get_config_file_value(config_object, 'Growl', 'growl_notify_onsubtitledownload', field_type=bool)
        self.growl.host = self._get_config_file_value(config_object, 'Growl', 'growl_host', field_type=str)
        self.growl.password = self._get_config_file_value(config_object, 'Growl', 'growl_password', field_type=str)

        # FREEMOBILE SETTINGS
        self.freemobile.enable = self._get_config_file_value(config_object, 'FreeMobile', 'use_freemobile', field_type=bool)
        self.freemobile.notify_on_snatch = self._get_config_file_value(config_object, 'FreeMobile', 'freemobile_notify_onsnatch', field_type=bool)
        self.freemobile.notify_on_download = self._get_config_file_value(config_object, 'FreeMobile', 'freemobile_notify_ondownload', field_type=bool)
        self.freemobile.notify_on_subtitle_download = self._get_config_file_value(config_object, 'FreeMobile', 'freemobile_notify_onsubtitledownload',
                                                                                  field_type=bool)
        self.freemobile.user_id = self._get_config_file_value(config_object, 'FreeMobile', 'freemobile_id', field_type=str)
        self.freemobile.apikey = self._get_config_file_value(config_object, 'FreeMobile', 'freemobile_apikey', field_type=str)

        # TELEGRAM SETTINGS
        self.telegram.enable = self._get_config_file_value(config_object, 'TELEGRAM', 'use_telegram', field_type=bool)
        self.telegram.notify_on_snatch = self._get_config_file_value(config_object, 'TELEGRAM', 'telegram_notify_onsnatch', field_type=bool)
        self.telegram.notify_on_download = self._get_config_file_value(config_object, 'TELEGRAM', 'telegram_notify_ondownload', field_type=bool)
        self.telegram.notify_on_subtitle_download = self._get_config_file_value(config_object, 'TELEGRAM', 'telegram_notify_on_subtitledownload',
                                                                                field_type=bool)
        self.telegram.user_id = self._get_config_file_value(config_object, 'TELEGRAM', 'telegram_id', field_type=str)
        self.telegram.apikey = self._get_config_file_value(config_object, 'TELEGRAM', 'telegram_apikey', field_type=str)

        # JOIN SETTINGS
        self.join_app.enable = self._get_config_file_value(config_object, 'JOIN', 'use_join', field_type=bool)
        self.join_app.notify_on_snatch = self._get_config_file_value(config_object, 'JOIN', 'join_notify_onsnatch', field_type=bool)
        self.join_app.notify_on_download = self._get_config_file_value(config_object, 'JOIN', 'join_notify_ondownload', field_type=bool)
        self.join_app.notify_on_subtitle_download = self._get_config_file_value(config_object, 'JOIN', 'join_notify_onsubtitledownload', field_type=bool)
        self.join_app.user_id = self._get_config_file_value(config_object, 'JOIN', 'join_id', field_type=str)
        self.join_app.apikey = self._get_config_file_value(config_object, 'JOIN', 'join_apikey', field_type=str)

        # PROWL SETTINGS
        self.prowl.enable = self._get_config_file_value(config_object, 'Prowl', 'use_prowl', field_type=bool)
        self.prowl.notify_on_snatch = self._get_config_file_value(config_object, 'Prowl', 'prowl_notify_onsnatch', field_type=bool)
        self.prowl.notify_on_download = self._get_config_file_value(config_object, 'Prowl', 'prowl_notify_ondownload', field_type=bool)
        self.prowl.notify_on_subtitle_download = self._get_config_file_value(config_object, 'Prowl', 'prowl_notify_onsubtitledownload', field_type=bool)
        self.prowl.apikey = self._get_config_file_value(config_object, 'Prowl', 'prowl_api', field_type=str)
        self.prowl.priority = self._get_config_file_value(config_object, 'Prowl', 'prowl_priority', field_type=int)

        # TWITTER SETTINGS
        self.twitter.enable = self._get_config_file_value(config_object, 'Twitter', 'use_twitter', field_type=bool)
        self.twitter.notify_on_snatch = self._get_config_file_value(config_object, 'Twitter', 'twitter_notify_onsnatch', field_type=bool)
        self.twitter.notify_on_download = self._get_config_file_value(config_object, 'Twitter', 'twitter_notify_ondownload', field_type=bool)
        self.twitter.notify_on_subtitle_download = self._get_config_file_value(config_object, 'Twitter', 'twitter_notify_onsubtitledownload',
                                                                               field_type=bool)
        self.twitter.username = self._get_config_file_value(config_object, 'Twitter', 'twitter_username', field_type=str)
        self.twitter.password = self._get_config_file_value(config_object, 'Twitter', 'twitter_password', field_type=str)
        self.twitter.prefix = self._get_config_file_value(config_object, 'Twitter', 'twitter_prefix', field_type=str)
        self.twitter.dm_to = self._get_config_file_value(config_object, 'Twitter', 'twitter_dmto', field_type=str)
        self.twitter.use_dm = self._get_config_file_value(config_object, 'Twitter', 'twitter_usedm', field_type=bool)

        # TWIILIO SETTINGS
        self.twilio.enable = self._get_config_file_value(config_object, 'Twilio', 'use_twilio', field_type=bool)
        self.twilio.notify_on_snatch = self._get_config_file_value(config_object, 'Twilio', 'twilio_notify_onsnatch', field_type=bool)
        self.twilio.notify_on_download = self._get_config_file_value(config_object, 'Twilio', 'twilio_notify_ondownload', field_type=bool)
        self.twilio.notify_on_subtitle_download = self._get_config_file_value(config_object, 'Twilio', 'twilio_notify_onsubtitledownload',
                                                                              field_type=bool)
        self.twilio.phone_sid = self._get_config_file_value(config_object, 'Twilio', 'twilio_phone_sid', field_type=str)
        self.twilio.account_sid = self._get_config_file_value(config_object, 'Twilio', 'twilio_account_sid', field_type=str)
        self.twilio.auth_token = self._get_config_file_value(config_object, 'Twilio', 'twilio_auth_token', field_type=str)
        self.twilio.to_number = self._get_config_file_value(config_object, 'Twilio', 'twilio_to_number', field_type=str)

        # BOXCAR2 SETTINGS
        self.boxcar2.enable = self._get_config_file_value(config_object, 'Boxcar2', 'use_boxcar2', field_type=bool)
        self.boxcar2.notify_on_snatch = self._get_config_file_value(config_object, 'Boxcar2', 'boxcar2_notify_onsnatch', field_type=bool)
        self.boxcar2.notify_on_download = self._get_config_file_value(config_object, 'Boxcar2', 'boxcar2_notify_ondownload', field_type=bool)
        self.boxcar2.notify_on_subtitle_download = self._get_config_file_value(config_object, 'Boxcar2', 'boxcar2_notify_onsubtitledownload', field_type=bool)
        self.boxcar2.access_token = self._get_config_file_value(config_object, 'Boxcar2', 'boxcar2_accesstoken', field_type=str)

        # PUSHOVER SETTINGS
        self.pushover.enable = self._get_config_file_value(config_object, 'Pushover', 'use_pushover', field_type=bool)
        self.pushover.notify_on_snatch = self._get_config_file_value(config_object, 'Pushover', 'pushover_notify_onsnatch', field_type=bool)
        self.pushover.notify_on_download = self._get_config_file_value(config_object, 'Pushover', 'pushover_notify_ondownload', field_type=bool)
        self.pushover.notify_on_subtitle_download = self._get_config_file_value(config_object, 'Pushover', 'pushover_notify_onsubtitledownload',
                                                                                field_type=bool)
        self.pushover.user_key = self._get_config_file_value(config_object, 'Pushover', 'pushover_userkey', field_type=str)
        self.pushover.apikey = self._get_config_file_value(config_object, 'Pushover', 'pushover_apikey', field_type=str)
        self.pushover.device = self._get_config_file_value(config_object, 'Pushover', 'pushover_device', field_type=str)
        self.pushover.sound = self._get_config_file_value(config_object, 'Pushover', 'pushover_sound', field_type=str)

        # LIBNOTIFY SETTINGS
        self.libnotify.enable = self._get_config_file_value(config_object, 'Libnotify', 'use_libnotify', field_type=bool)
        self.libnotify.notify_on_snatch = self._get_config_file_value(config_object, 'Libnotify', 'libnotify_notify_onsnatch', field_type=bool)
        self.libnotify.notify_on_download = self._get_config_file_value(config_object, 'Libnotify', 'libnotify_notify_ondownload', field_type=bool)
        self.libnotify.notify_on_subtitle_download = self._get_config_file_value(config_object, 'Libnotify', 'libnotify_notify_onsubtitledownload',
                                                                                 field_type=bool)

        # NMJ SETTINGS
        self.nmj.enable = self._get_config_file_value(config_object, 'NMJ', 'use_nmj', field_type=bool)
        self.nmj.host = self._get_config_file_value(config_object, 'NMJ', 'nmj_host', field_type=str)
        self.nmj.database = self._get_config_file_value(config_object, 'NMJ', 'nmj_database', field_type=str)
        self.nmj.mount = self._get_config_file_value(config_object, 'NMJ', 'nmj_mount', field_type=str)

        # NMJV2 SETTINGS
        self.nmjv2.enable = self._get_config_file_value(config_object, 'NMJv2', 'use_nmjv2', field_type=bool)
        self.nmjv2.host = self._get_config_file_value(config_object, 'NMJv2', 'nmjv2_host', field_type=str)
        self.nmjv2.database = self._get_config_file_value(config_object, 'NMJv2', 'nmjv2_database', field_type=str)
        self.nmjv2.db_loc = NMJv2Location[
            self._get_config_file_value(config_object, 'NMJv2', 'nmjv2_dbloc', default=NMJv2Location.LOCAL.name, field_type=str.upper)]

        # SYNOLOGY SETTINGS
        self.synology.host = self._get_config_file_value(config_object, 'SynologyDSM', 'syno_dsm_host', field_type=str)
        self.synology.username = self._get_config_file_value(config_object, 'SynologyDSM', 'syno_dsm_username', field_type=str)
        self.synology.password = self._get_config_file_value(config_object, 'SynologyDSM', 'syno_dsm_password', field_type=str)
        self.synology.path = self._get_config_file_value(config_object, 'SynologyDSM', 'syno_dsm_path', field_type=str)
        self.synology.enable_index = self._get_config_file_value(config_object, 'Synology', 'use_synoindex', field_type=bool)
        self.synology.enable_notifications = self._get_config_file_value(config_object, 'SynologyNotifier', 'use_synologynotifier', field_type=bool)
        self.synology.notify_on_snatch = self._get_config_file_value(config_object, 'SynologyNotifier', 'synologynotifier_notify_onsnatch',
                                                                     field_type=bool)
        self.synology.notify_on_download = self._get_config_file_value(config_object, 'SynologyNotifier', 'synologynotifier_notify_ondownload',
                                                                       field_type=bool)
        self.synology.notify_on_subtitle_download = self._get_config_file_value(config_object, 'SynologyNotifier',
                                                                                'synologynotifier_notify_onsubtitledownload', field_type=bool)

        # SLACK SETTINGS
        self.slack.enable = self._get_config_file_value(config_object, 'Slack', 'use_slack', field_type=bool)
        self.slack.notify_on_snatch = self._get_config_file_value(config_object, 'Slack', 'slack_notify_onsnatch', field_type=bool)
        self.slack.notify_on_download = self._get_config_file_value(config_object, 'Slack', 'slack_notify_ondownload', field_type=bool)
        self.slack.notify_on_subtitle_download = self._get_config_file_value(config_object, 'Slack', 'slack_notify_onsubtitledownload', field_type=bool)
        self.slack.webhook = self._get_config_file_value(config_object, 'Slack', 'slack_webhook', field_type=str)

        # DISCORD SETTINGS
        self.discord.enable = self._get_config_file_value(config_object, 'Discord', 'use_discord', field_type=bool)
        self.discord.notify_on_snatch = self._get_config_file_value(config_object, 'Discord', 'discord_notify_onsnatch', field_type=bool)
        self.discord.notify_on_download = self._get_config_file_value(config_object, 'Discord', 'discord_notify_ondownload', field_type=bool)
        self.discord.notify_on_subtitle_download = self._get_config_file_value(config_object, 'Discord', 'discord_notify_onsubtitledownload',
                                                                               field_type=bool)
        self.discord.webhook = self._get_config_file_value(config_object, 'Discord', 'discord_webhook', field_type=str)
        self.discord.avatar_url = self._get_config_file_value(config_object, 'Discord', 'discord_avatar_url', field_type=str)
        self.discord.name = self._get_config_file_value(config_object, 'Discord', 'discord_name', field_type=str)
        self.discord.tts = self._get_config_file_value(config_object, 'Discord', 'discord_tts', field_type=bool)

        # TRAKT SETTINGS
        self.trakt.enable = self._get_config_file_value(config_object, 'Trakt', 'use_trakt', field_type=bool)
        self.trakt.username = self._get_config_file_value(config_object, 'Trakt', 'trakt_username', field_type=str)
        self.trakt.remove_watchlist = self._get_config_file_value(config_object, 'Trakt', 'trakt_remove_watchlist', field_type=bool)
        self.trakt.remove_serieslist = self._get_config_file_value(config_object, 'Trakt', 'trakt_remove_serieslist', field_type=bool)
        self.trakt.remove_show_from_sickrage = self._get_config_file_value(config_object, 'Trakt', 'trakt_remove_show_from_sickrage', field_type=bool)
        self.trakt.sync_watchlist = self._get_config_file_value(config_object, 'Trakt', 'trakt_sync_watchlist', field_type=bool)
        self.trakt.method_add = TraktAddMethod(self._get_config_file_value(config_object, 'Trakt', 'trakt_method_add', field_type=int))
        self.trakt.start_paused = self._get_config_file_value(config_object, 'Trakt', 'trakt_start_paused', field_type=bool)
        self.trakt.use_recommended = self._get_config_file_value(config_object, 'Trakt', 'trakt_use_recommended', field_type=bool)
        self.trakt.sync = self._get_config_file_value(config_object, 'Trakt', 'trakt_sync', field_type=bool)
        self.trakt.sync_remove = self._get_config_file_value(config_object, 'Trakt', 'trakt_sync_remove', field_type=bool)
        self.trakt.series_provider_default = SeriesProviderID.THETVDB
        self.trakt.timeout = self._get_config_file_value(config_object, 'Trakt', 'trakt_timeout', field_type=int)
        self.trakt.blacklist_name = self._get_config_file_value(config_object, 'Trakt', 'trakt_blacklist_name', field_type=str)

        # PYTIVO SETTINGS
        self.pytivo.enable = self._get_config_file_value(config_object, 'pyTivo', 'use_pytivo', field_type=bool)
        self.pytivo.notify_on_snatch = self._get_config_file_value(config_object, 'pyTivo', 'pytivo_notify_onsnatch', field_type=bool)
        self.pytivo.notify_on_download = self._get_config_file_value(config_object, 'pyTivo', 'pytivo_notify_ondownload', field_type=bool)
        self.pytivo.notify_on_subtitle_download = self._get_config_file_value(config_object, 'pyTivo', 'pytivo_notify_onsubtitledownload',
                                                                              field_type=bool)
        self.pytivo.update_library = self._get_config_file_value(config_object, 'pyTivo', 'pyTivo_update_library', field_type=bool)
        self.pytivo.host = self._get_config_file_value(config_object, 'pyTivo', 'pytivo_host', field_type=str)
        self.pytivo.share_name = self._get_config_file_value(config_object, 'pyTivo', 'pytivo_share_name', field_type=str)
        self.pytivo.tivo_name = self._get_config_file_value(config_object, 'pyTivo', 'pytivo_tivo_name', field_type=str)

        # NMA SETTINGS
        self.nma.enable = self._get_config_file_value(config_object, 'NMA', 'use_nma', field_type=bool)
        self.nma.notify_on_snatch = self._get_config_file_value(config_object, 'NMA', 'nma_notify_onsnatch', field_type=bool)
        self.nma.notify_on_download = self._get_config_file_value(config_object, 'NMA', 'nma_notify_ondownload', field_type=bool)
        self.nma.notify_on_subtitle_download = self._get_config_file_value(config_object, 'NMA', 'nma_notify_onsubtitledownload', field_type=bool)
        self.nma.api_keys = self._get_config_file_value(config_object, 'NMA', 'nma_api', field_type=str)
        self.nma.priority = self._get_config_file_value(config_object, 'NMA', 'nma_priority', field_type=str)

        # PUSHALOT SETTINGS
        self.pushalot.enable = self._get_config_file_value(config_object, 'Pushalot', 'use_pushalot', field_type=bool)
        self.pushalot.notify_on_snatch = self._get_config_file_value(config_object, 'Pushalot', 'pushalot_notify_onsnatch', field_type=bool)
        self.pushalot.notify_on_download = self._get_config_file_value(config_object, 'Pushalot', 'pushalot_notify_ondownload', field_type=bool)
        self.pushalot.notify_on_subtitle_download = self._get_config_file_value(config_object, 'Pushalot', 'pushalot_notify_onsubtitledownload',
                                                                                field_type=bool)
        self.pushalot.auth_token = self._get_config_file_value(config_object, 'Pushalot', 'pushalot_authorizationtoken', field_type=str)

        # PUSHBULLET SETTINGS
        self.pushbullet.enable = self._get_config_file_value(config_object, 'Pushbullet', 'use_pushbullet', field_type=bool)
        self.pushbullet.notify_on_snatch = self._get_config_file_value(config_object, 'Pushbullet', 'pushbullet_notify_onsnatch', field_type=bool)
        self.pushbullet.notify_on_download = self._get_config_file_value(config_object, 'Pushbullet', 'pushbullet_notify_ondownload', field_type=bool)
        self.pushbullet.notify_on_subtitle_download = self._get_config_file_value(config_object, 'Pushbullet', 'pushbullet_notify_onsubtitledownload',
                                                                                  field_type=bool)
        self.pushbullet.api_key = self._get_config_file_value(config_object, 'Pushbullet', 'pushbullet_api', field_type=str)
        self.pushbullet.device = self._get_config_file_value(config_object, 'Pushbullet', 'pushbullet_device', field_type=str)

        # EMAIL SETTINGS
        self.email.enable = self._get_config_file_value(config_object, 'Email', 'use_email', field_type=bool)
        self.email.notify_on_snatch = self._get_config_file_value(config_object, 'Email', 'email_notify_onsnatch', field_type=bool)
        self.email.notify_on_download = self._get_config_file_value(config_object, 'Email', 'email_notify_ondownload', field_type=bool)
        self.email.notify_on_subtitle_download = self._get_config_file_value(config_object, 'Email', 'email_notify_onsubtitledownload', field_type=bool)
        self.email.host = self._get_config_file_value(config_object, 'Email', 'email_host', field_type=str)
        self.email.port = self._get_config_file_value(config_object, 'Email', 'email_port', field_type=int)
        self.email.tls = self._get_config_file_value(config_object, 'Email', 'email_tls', field_type=bool)
        self.email.username = self._get_config_file_value(config_object, 'Email', 'email_user', field_type=str)
        self.email.password = self._get_config_file_value(config_object, 'Email', 'email_password', field_type=str)
        self.email.send_from = self._get_config_file_value(config_object, 'Email', 'email_from', field_type=str)
        self.email.send_to_list = self._get_config_file_value(config_object, 'Email', 'email_list', field_type=str)

        # ALEXA SETTINGS
        self.alexa.enable = self._get_config_file_value(config_object, 'Alexa', 'use_alexa', field_type=bool)
        self.alexa.notify_on_snatch = self._get_config_file_value(config_object, 'Alexa', 'alexa_notify_onsnatch', field_type=bool)
        self.alexa.notify_on_download = self._get_config_file_value(config_object, 'Alexa', 'alexa_notify_ondownload', field_type=bool)
        self.alexa.notify_on_subtitle_download = self._get_config_file_value(config_object, 'Alexa', 'alexa_notify_onsubtitledownload', field_type=bool)

        # SUBTITLE SETTINGS
        self.subtitles.enable = self._get_config_file_value(config_object, 'Subtitles', 'use_subtitles', field_type=bool)
        self.subtitles.languages = ','.join(self._get_config_file_value(config_object, 'Subtitles', 'subtitles_languages', field_type=list))
        self.subtitles.services_list = ','.join(self._get_config_file_value(config_object, 'Subtitles', 'subtitles_services_list', field_type=list))
        self.subtitles.dir = self._get_config_file_value(config_object, 'Subtitles', 'subtitles_dir', field_type=str)
        self.subtitles.default = self._get_config_file_value(config_object, 'Subtitles', 'subtitles_default', field_type=bool)
        self.subtitles.history = self._get_config_file_value(config_object, 'Subtitles', 'subtitles_history', field_type=bool)
        self.subtitles.hearing_impaired = self._get_config_file_value(config_object, 'Subtitles', 'subtitles_hearing_impaired', field_type=bool)
        self.subtitles.enable_embedded = self._get_config_file_value(config_object, 'Subtitles', 'embedded_subtitles_all', field_type=bool)
        self.subtitles.multi = self._get_config_file_value(config_object, 'Subtitles', 'subtitles_multi', field_type=bool)
        self.subtitles.services_enabled = self._get_config_file_value(config_object, 'Subtitles', 'subtitles_services_enabled', field_type=str)
        self.subtitles.extra_scripts = self._get_config_file_value(config_object, 'Subtitles', 'subtitles_extra_scripts', field_type=str)
        self.subtitles.addic7ed_user = self._get_config_file_value(config_object, 'Subtitles', 'addic7ed_username', field_type=str)
        self.subtitles.addic7ed_pass = self._get_config_file_value(config_object, 'Subtitles', 'addic7ed_password', field_type=str)
        self.subtitles.legendastv_user = self._get_config_file_value(config_object, 'Subtitles', 'legendastv_username', field_type=str)
        self.subtitles.legendastv_pass = self._get_config_file_value(config_object, 'Subtitles', 'legendastv_password', field_type=str)
        self.subtitles.itasa_user = self._get_config_file_value(config_object, 'Subtitles', 'itasa_username', field_type=str)
        self.subtitles.itasa_pass = self._get_config_file_value(config_object, 'Subtitles', 'itasa_password', field_type=str)
        self.subtitles.opensubtitles_user = self._get_config_file_value(config_object, 'Subtitles', 'opensubtitles_username', field_type=str)
        self.subtitles.opensubtitles_pass = self._get_config_file_value(config_object, 'Subtitles', 'opensubtitles_password', field_type=str)

        # FAILED DOWNLOAD SETTINGS
        self.failed_downloads.enable = self._get_config_file_value(config_object, 'FailedDownloads', 'delete_failed', field_type=bool)

        # FAILED SNATCH SETTINGS
        self.failed_snatches.enable = self._get_config_file_value(config_object, 'FailedSnatches', 'use_failed_snatcher', field_type=bool)
        self.failed_snatches.age = self._get_config_file_value(config_object, 'FailedSnatches', 'failed_snatch_age', field_type=int)

        # ANIDB SETTINGS
        self.anidb.enable = self._get_config_file_value(config_object, 'ANIDB', 'use_anidb', field_type=bool)
        self.anidb.username = self._get_config_file_value(config_object, 'ANIDB', 'anidb_username', field_type=str)
        self.anidb.password = self._get_config_file_value(config_object, 'ANIDB', 'anidb_password', field_type=str)
        self.anidb.use_my_list = self._get_config_file_value(config_object, 'ANIDB', 'anidb_use_mylist', field_type=bool)
        self.anidb.split_home = self._get_config_file_value(config_object, 'ANIME', 'anime_split_home', field_type=bool)

        # CUSTOM SEARCH PROVIDERS
        custom_providers = self._get_config_file_value(config_object, 'Providers', 'custom_providers', field_type=str)
        for curProviderStr in custom_providers.split('!!!'):
            if not len(curProviderStr):
                continue

            cur_provider_type, cur_provider_data = curProviderStr.split('|', 1)
            if SearchProviderType(cur_provider_type) == SearchProviderType.TORRENT_RSS:
                cur_name, cur_url, cur_cookies, cur_title_tag = cur_provider_data.split('|')
                search_provider = TorrentRssProvider(cur_name, cur_url, cur_cookies, cur_title_tag)
                sickrage.app.search_providers[search_provider.provider_type.name][search_provider.id] = search_provider
            elif SearchProviderType(cur_provider_type) == SearchProviderType.NEWZNAB:
                cur_name, cur_url, cur_key, cur_cat = cur_provider_data.split('|')
                search_provider = NewznabProvider(cur_name, cur_url, cur_key, cur_cat)
                sickrage.app.search_providers[search_provider.provider_type.name][search_provider.id] = search_provider

        # SEARCH PROVIDER SETTINGS
        for provider_id, provider_obj in sickrage.app.search_providers.all().items():
            provider_settings = self._get_config_file_value(config_object, 'Providers', provider_id, field_type=dict)
            provider_obj.enabled = auto_type(provider_settings.get('enabled', False))
            provider_obj.search_mode = auto_type(provider_settings.get('search_mode', 'eponly'))
            provider_obj.search_fallback = auto_type(provider_settings.get('search_fallback', False))
            provider_obj.enable_daily = auto_type(provider_settings.get('enable_daily', False))
            provider_obj.enable_backlog = auto_type(provider_settings.get('enable_backlog', False))
            provider_obj.cookies = auto_type(provider_settings.get('cookies', ''))

            if provider_obj.provider_type in [SearchProviderType.TORRENT, SearchProviderType.TORRENT_RSS]:
                provider_obj.ratio = auto_type(provider_settings.get('ratio', 0) or 0)
            elif provider_obj.provider_type in [SearchProviderType.NZB, SearchProviderType.NEWZNAB]:
                provider_obj.username = auto_type(provider_settings.get('username', ''))
                provider_obj.api_key = auto_type(provider_settings.get('api_key', ''))

            custom_settings = {
                'minseed': auto_type(provider_settings.get('minseed', 0)),
                'minleech': auto_type(provider_settings.get('minleech', 0)),
                'digest': auto_type(provider_settings.get('digest', '')),
                'hash': auto_type(provider_settings.get('hash', '')),
                'api_key': auto_type(provider_settings.get('api_key', '')),
                'username': auto_type(provider_settings.get('username', '')),
                'password': auto_type(provider_settings.get('password', '')),
                'passkey': auto_type(provider_settings.get('passkey', '')),
                'pin': auto_type(provider_settings.get('pin', '')),
                'confirmed': auto_type(provider_settings.get('confirmed', False)),
                'ranked': auto_type(provider_settings.get('ranked', False)),
                'engrelease': auto_type(provider_settings.get('engrelease', False)),
                'onlyspasearch': auto_type(provider_settings.get('onlyspasearch', False)),
                'sorting': auto_type(provider_settings.get('sorting', 'seeders')),
                'freeleech': auto_type(provider_settings.get('freeleech', False)),
                'reject_m2ts': auto_type(provider_settings.get('reject_m2ts', False)),
                # 'cat': int(auto_type(provider_settings.get('cat', None) or 0),
                'subtitle': auto_type(provider_settings.get('subtitle', False)),
                'custom_url': auto_type(provider_settings.get('custom_url', ''))
            }

            provider_obj.custom_settings.update((k, v) for k, v in custom_settings.items() if k in provider_obj.custom_settings)

        # SEARCH PROVIDER ORDER SETTINGS
        search_provider_order = self._get_config_file_value(config_object, 'Providers', 'providers_order', field_type=list)
        for idx, search_provider_id in enumerate(search_provider_order):
            if search_provider_id in sickrage.app.search_providers.all():
                search_provider = sickrage.app.search_providers.all()[search_provider_id]
                search_provider.sort_order = idx

        # METADATA PROVIDER SETTINGS
        for metadata_provider in self.session.query(self.db.MetadataProviders):
            config_values = self._get_config_file_value(config_object, 'MetadataProviders', metadata_provider.provider_id, field_type=str)
            if not config_values:
                continue

            metadata_provider.update(**{
                'show_metadata': bool(int(config_values.split('|')[0])),
                'episode_metadata': bool(int(config_values.split('|')[1])),
                'fanart': bool(int(config_values.split('|')[2])),
                'poster': bool(int(config_values.split('|')[3])),
                'banner': bool(int(config_values.split('|')[4])),
                'episode_thumbnails': bool(int(config_values.split('|')[5])),
                'season_posters': bool(int(config_values.split('|')[6])),
                'season_banners': bool(int(config_values.split('|')[7])),
                'season_all_poster': bool(int(config_values.split('|')[8])),
                'season_all_banner': bool(int(config_values.split('|')[9])),
                'enable': bool(int(config_values.split('|')[10])),
            })

        self.save()

        # delete old config
        os.remove(filename)

        # delete old config private key
        if os.path.exists(private_key_filename):
            os.remove(private_key_filename)

        sickrage.app.log.info("Migrating config file to database was successful!")

    def _get_config_file_value(self, config_object, section, key, default=None, field_type=None):
        if not field_type:
            field_type = str

        if not default:
            default = field_type() if field_type is not str.upper else str()

        if section in config_object:
            section_object = config_object.get(section)
            if key in section_object:
                try:
                    value = self.convert_value(section_object.get(key), field_type)
                    if not value:
                        return default
                except Exception:
                    return default

        return default

    def convert_value(self, value, field_type):
        if not field_type:
            field_type = str

        if value == 'None':
            return ''

        if field_type == bool:
            return arg_to_bool(value)

        return field_type(value)

    def to_json(self):
        return {
            'general': GeneralSchema().dump(self.general),
            'gui': GUISchema().dump(self.gui),
            'blackhole': BlackholeSchema().dump(self.blackhole),
            'sabnzbd': SABnzbdSchema().dump(self.sabnzbd),
            'nzbget': NZBgetSchema().dump(self.nzbget),
            'synology': SynologySchema().dump(self.synology),
            'torrent': TorrentSchema().dump(self.torrent),
            'kodi': KodiSchema().dump(self.kodi),
            'plex': PlexSchema().dump(self.plex),
            'emby': EmbySchema().dump(self.emby),
            'growl': GrowlSchema().dump(self.growl),
            'freemobile': FreeMobileSchema().dump(self.freemobile),
            'telegram': TelegramSchema().dump(self.telegram),
            'join': JoinSchema().dump(self.join_app),
            'prowl': ProwlSchema().dump(self.prowl),
            'twitter': TwitterSchema().dump(self.twitter),
            'twilio': TwilioSchema().dump(self.twilio),
            'boxcar2': Boxcar2Schema().dump(self.boxcar2),
            'pushover': PushoverSchema().dump(self.pushover),
            'libnotify': LibnotifySchema().dump(self.libnotify),
            'nmj': NMJSchema().dump(self.nmj),
            'nmjv2': NMJv2Schema().dump(self.nmjv2),
            'slack': SlackSchema().dump(self.slack),
            'discord': DiscordSchema().dump(self.discord),
            'trakt': TraktSchema().dump(self.trakt),
            'pytivo': PyTivoSchema().dump(self.pytivo),
            'nma': NMASchema().dump(self.nma),
            'pushalot': PushalotSchema().dump(self.pushalot),
            'pushbullet': PushbulletSchema().dump(self.pushbullet),
            'email': EmailSchema().dump(self.email),
            'alexa': AlexaSchema().dump(self.alexa),
            'subtitles': SubtitlesSchema().dump(self.subtitles),
            'failedDownloads': FailedDownloadsSchema().dump(self.failed_downloads),
            'failedSnatches': FailedSnatchesSchema().dump(self.failed_snatches),
            'anidb': AniDBSchema().dump(self.anidb),
            'qualitySizes': QualitySizesSchema().dump(self.session.query(self.db.QualitySizes), many=True),
            'searchProvidersTorrent': SearchProvidersTorrentSchema().dump(self.session.query(self.db.SearchProvidersTorrent), many=True),
            'searchProvidersNzb': SearchProvidersNzbSchema().dump(self.session.query(self.db.SearchProvidersNzb), many=True),
            'searchProvidersTorrentRss': SearchProvidersTorrentRssSchema().dump(self.session.query(self.db.SearchProvidersTorrentRss), many=True),
            'searchProvidersNewznab': SearchProvidersNewznabSchema().dump(self.session.query(self.db.SearchProvidersNewznab), many=True),
            'metadataProviders': MetadataProvidersSchema().dump(self.session.query(self.db.MetadataProviders), many=True),
        }
