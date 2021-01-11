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
import datetime
import json
import random

import six
from sqlalchemy import Column, Text, Integer, ForeignKey, Boolean, Enum, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy_utils import JSONType
from sqlalchemy_utils.types.encrypted.encrypted_type import StringEncryptedType, DatetimeHandler

import sickrage
from sickrage.core.common import Qualities, EpisodeStatus
from sickrage.core.databases import SRDatabaseBase, SRDatabase, IntFlag
from sickrage.core.enums import DefaultHomePage, MultiEpNaming, CpuPreset, CheckPropersInterval, \
    FileTimestampTimezone, ProcessMethod, NzbMethod, TorrentMethod, SearchFormat, UserPermission, PosterSortDirection, HomeLayout, PosterSortBy, \
    HistoryLayout, TimezoneDisplay, UITheme, TraktAddMethod, SeriesProviderID
from sickrage.core.helpers import generate_api_key, generate_secret, get_lan_ip
from sickrage.core.tv.show.coming_episodes import ComingEpsLayout, ComingEpsSortBy
from sickrage.notification_providers.nmjv2 import NMJv2Location
from sickrage.search_providers import SearchProviderType

def encryption_key():
    try:
        return getattr(sickrage.app.config.user, 'sub_id', None) or 'sickrage'
    except Exception:
        return 'sickrage'


class CustomStringEncryptedType(StringEncryptedType):
    reset = False

    def process_bind_param(self, value, dialect):
        """Encrypt a value on the way in."""
        if value is not None:
            if not self.reset:
                self._update_key()
            else:
                self.engine._update_key('sickrage')

            try:
                value = self.underlying_type.process_bind_param(
                    value, dialect
                )
            except AttributeError:
                # Doesn't have 'process_bind_param'

                # Handle 'boolean' and 'dates'
                type_ = self.underlying_type.python_type
                if issubclass(type_, bool):
                    value = 'true' if value else 'false'

                elif issubclass(type_, (datetime.date, datetime.time)):
                    value = value.isoformat()

                elif issubclass(type_, JSONType):
                    value = six.text_type(json.dumps(value))

            return self.engine.encrypt(value)

    def process_result_value(self, value, dialect):
        """Decrypt value on the way out."""
        if value is not None:
            self._update_key()

            try:
                decrypted_value = self.engine.decrypt(value)
            except ValueError:
                self.engine._update_key('sickrage')
                decrypted_value = self.engine.decrypt(value)

            try:
                return self.underlying_type.process_result_value(
                    decrypted_value, dialect
                )
            except AttributeError:
                # Doesn't have 'process_result_value'

                # Handle 'boolean' and 'dates'
                type_ = self.underlying_type.python_type
                date_types = [datetime.datetime, datetime.time, datetime.date]

                if issubclass(type_, bool):
                    return decrypted_value == 'true'

                elif type_ in date_types:
                    return DatetimeHandler.process_value(
                        decrypted_value, type_
                    )

                elif issubclass(type_, JSONType):
                    return json.loads(decrypted_value)

                # Handle all others
                return self.underlying_type.python_type(decrypted_value)


class ConfigDB(SRDatabase):
    base = declarative_base(cls=SRDatabaseBase)
    
    def __init__(self, db_type, db_prefix, db_host, db_port, db_username, db_password):
        super(ConfigDB, self).__init__('config', db_type, db_prefix, db_host, db_port, db_username, db_password)

    def initialize(self):
        self.base.metadata.create_all(self.engine)

    class Users(base):
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True, autoincrement=True)
        username = Column(Text, default='', index=True, unique=True)
        password = Column(Text, default='')
        email = Column(Text, default='', index=True)
        sub_id = Column(Text, default='')
        permissions = Column(Enum(UserPermission), default=UserPermission.GUEST)
        enable = Column(Boolean, default=True)

    class General(base):
        __tablename__ = 'general'
        id = Column(Integer, primary_key=True, autoincrement=True)
        server_id = Column(Text, default='')
        enable_sickrage_api = Column(Boolean, default=True)
        log_size = Column(Integer, default=1048576)
        calendar_unprotected = Column(Boolean, default=False)
        https_key = Column(Text, default='server.key')
        https_cert = Column(Text, default='server.crt')
        allow_high_priority = Column(Boolean, default=False)
        anon_redirect = Column(Text, default='http://nullrefer.com/?')
        series_provider_timeout = Column(Integer, default=20)
        web_use_gzip = Column(Boolean, default=True)
        daily_searcher_freq = Column(Integer, default=40)
        ignore_words = Column(Text, default=','.join(['german', 'french', 'core2hd', 'dutch', 'swedish', 'reenc', 'MrLss']))
        api_v1_key = Column(Text, default=generate_api_key())
        sso_auth_enabled = Column(Boolean, default=True)
        local_auth_enabled = Column(Boolean, default=False)
        ip_whitelist_enabled = Column(Boolean, default=False)
        ip_whitelist_localhost_enabled = Column(Boolean, default=False)
        ip_whitelist = Column(Text, default='')
        proper_searcher_interval = Column(Enum(CheckPropersInterval), default=CheckPropersInterval.DAILY)
        nzb_method = Column(Enum(NzbMethod), default=NzbMethod.BLACKHOLE)
        web_cookie_secret = Column(Text, default=generate_secret())
        ssl_verify = Column(Boolean, default=False)
        enable_upnp = Column(Boolean, default=False)
        version_notify = Column(Boolean, default=False)
        web_root = Column(Text, default='')
        web_log = Column(Text, default='')
        add_shows_wo_dir = Column(Boolean, default=False)
        debug = Column(Boolean, default=False)
        series_provider_default = Column(Enum(SeriesProviderID), default=SeriesProviderID.THETVDB)
        use_torrents = Column(Boolean, default=True)
        display_all_seasons = Column(Boolean, default=True)
        usenet_retention = Column(Integer, default=500)
        download_propers = Column(Boolean, default=True)
        pip3_path = Column(Text, default='pip3')
        del_rar_contents = Column(Boolean, default=False)
        process_method = Column(Enum(ProcessMethod), default=ProcessMethod.COPY)
        file_timestamp_timezone = Column(Enum(FileTimestampTimezone), default=FileTimestampTimezone.NETWORK)
        auto_update = Column(Boolean, default=True)
        tv_download_dir = Column(Text, default='')
        naming_custom_abd = Column(Boolean, default=False)
        scene_default = Column(Boolean, default=False)
        skip_downloaded_default = Column(Boolean, default=False)
        add_show_year_default = Column(Boolean, default=False)
        naming_sports_pattern = Column(Text, default='%SN - %A-D - %EN')
        create_missing_show_dirs = Column(Boolean, default=False)
        trash_rotate_logs = Column(Boolean, default=False)
        airdate_episodes = Column(Boolean, default=False)
        notify_on_update = Column(Boolean, default=True)
        backup_on_update = Column(Boolean, default=True)
        backlog_days = Column(Integer, default=7)
        root_dirs = Column(Text, default='')
        naming_pattern = Column(Text, default='Season %0S/%SN - S%0SE%0E - %EN')
        sort_article = Column(Boolean, default=False)
        handle_reverse_proxy = Column(Boolean, default=False)
        postpone_if_sync_files = Column(Boolean, default=True)
        cpu_preset = Column(Enum(CpuPreset), default=CpuPreset.NORMAL)
        nfo_rename = Column(Boolean, default=True)
        naming_anime_multi_ep = Column(Enum(MultiEpNaming), default=MultiEpNaming.REPEAT)
        use_nzbs = Column(Boolean, default=False)
        web_ipv6 = Column(Boolean, default=False)
        anime_default = Column(Boolean, default=False)
        default_page = Column(Enum(DefaultHomePage), default=DefaultHomePage.HOME)
        version_updater_freq = Column(Integer, default=1)
        download_url = Column(Text, default='')
        show_update_hour = Column(Integer, default=3)
        enable_rss_cache = Column(Boolean, default=True)
        torrent_file_to_magnet = Column(Boolean, default=False)
        torrent_magnet_to_file = Column(Boolean, default=True)
        download_unverified_magnet_link = Column(Boolean, default=False)
        status_default = Column(Enum(EpisodeStatus), default=EpisodeStatus.SKIPPED)
        naming_anime = Column(Integer, default=3)
        naming_custom_sports = Column(Boolean, default=False)
        naming_custom_anime = Column(Boolean, default=False)
        naming_anime_pattern = Column(Text, default='Season %0S/%SN - S%0SE%0E - %EN')
        randomize_providers = Column(Boolean, default=False)
        web_host = Column(Text, default='0.0.0.0')
        process_automatically = Column(Boolean, default=False)
        git_path = Column(Text, default='git')
        sync_files = Column(Text, default=','.join(['!sync', 'lftp-pget-status', 'part', 'bts', '!qb']))
        web_port = Column(Integer, default=8081)
        web_external_port = Column(Integer, default=random.randint(49152, 65536))
        launch_browser = Column(Boolean, default=False)
        unpack = Column(Boolean, default=False)
        unpack_dir = Column(Text, default='')
        delete_non_associated_files = Column(Boolean, default=True)
        move_associated_files = Column(Boolean, default=False)
        naming_multi_ep = Column(Enum(MultiEpNaming), default=MultiEpNaming.REPEAT)
        random_user_agent = Column(Boolean, default=False)
        torrent_method = Column(Enum(TorrentMethod), default=TorrentMethod.BLACKHOLE)
        trash_remove_show = Column(Boolean, default=False)
        enable_https = Column(Boolean, default=False)
        no_delete = Column(Boolean, default=False)
        naming_abd_pattern = Column(Text, default='%SN - %A.D - %EN')
        socket_timeout = Column(Integer, default=30)
        proxy_setting = Column(Text, default='')
        backlog_searcher_freq = Column(Integer, default=1440)
        subtitle_searcher_freq = Column(Integer, default=1)
        auto_postprocessor_freq = Column(Integer, default=10)
        notify_on_login = Column(Boolean, default=False)
        rename_episodes = Column(Boolean, default=True)
        quality_default = Column(IntFlag(Qualities), default=Qualities.SD)
        extra_scripts = Column(Text, default='')
        flatten_folders_default = Column(Boolean, default=False)
        series_provider_default_language = Column(Text, default='en')
        show_update_stale = Column(Boolean, default=True)
        ep_default_deleted_status = Column(Enum(EpisodeStatus), default=EpisodeStatus.ARCHIVED)
        no_restart = Column(Boolean, default=False)
        allowed_video_file_exts = Column(Text, default=','.join(['avi', 'mkv', 'mpg', 'mpeg', 'wmv', 'ogm', 'mp4', 'iso', 'img', 'divx', 'm2ts', 'm4v', 'ts',
                                                                 'flv', 'f4v', 'mov', 'rmvb', 'vob', 'dvr-ms', 'wtv', 'ogv', '3gp', 'webm', 'tp']))
        require_words = Column(Text, default='')
        naming_strip_year = Column(Boolean, default=False)
        proxy_series_providers = Column(Boolean, default=True)
        log_nr = Column(Integer, default=5)
        git_reset = Column(Boolean, default=True)
        search_format_default = Column(Enum(SearchFormat), default=SearchFormat.STANDARD)
        skip_removed_files = Column(Boolean, default=False)
        status_default_after = Column(Enum(EpisodeStatus), default=EpisodeStatus.WANTED)
        ignored_subs_list = Column(Text, default=','.join(['dk', 'fin', 'heb', 'kor', 'nor', 'nordic', 'pl', 'swe']))
        calendar_icons = Column(Boolean, default=False)
        keep_processed_dir = Column(Boolean, default=True)
        processor_follow_symlinks = Column(Boolean, default=False)
        allowed_extensions = Column(Text, default=','.join(['srt', 'nfo', 'srr', 'sfv']))
        view_changelog = Column(Boolean, default=False)
        strip_special_file_bits = Column(Boolean, default=True)
        max_queue_workers = Column(Integer, default=5)

    class GUI(base):
        __tablename__ = 'gui'
        id = Column(Integer, primary_key=True, autoincrement=True)
        user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
        coming_eps_display_paused = Column(Boolean, default=False)
        display_show_specials = Column(Boolean, default=True)
        gui_lang = Column(Text, default='')
        history_limit = Column(Integer, default=100)
        poster_sort_dir = Column(Enum(PosterSortDirection), default=PosterSortDirection.ASCENDING)
        coming_eps_missed_range = Column(Integer, default=7)
        date_preset = Column(Text, default='%x')
        fuzzy_dating = Column(Boolean, default=False)
        fanart_background = Column(Boolean, default=True)
        home_layout = Column(Enum(HomeLayout), default=HomeLayout.POSTER)
        coming_eps_layout = Column(Enum(ComingEpsLayout), default=ComingEpsLayout.POSTER)
        coming_eps_sort = Column(Enum(ComingEpsSortBy), default=ComingEpsSortBy.DATE)
        poster_sort_by = Column(Enum(PosterSortBy), default=PosterSortBy.NAME)
        time_preset = Column(Text, default='%I:%M:%S%p')
        time_preset_w_seconds = Column(Text, default='')
        trim_zero = Column(Boolean, default=False)
        fanart_background_opacity = Column(Float, default=0.4)
        history_layout = Column(Enum(HistoryLayout), default=HistoryLayout.DETAILED)
        filter_row = Column(Boolean, default=False)
        timezone_display = Column(Enum(TimezoneDisplay), default=TimezoneDisplay.LOCAL)
        theme_name = Column(Enum(UITheme), default=UITheme.DARK)

    class Blackhole(base):
        __tablename__ = 'blackhole'
        id = Column(Integer, primary_key=True, autoincrement=True)
        nzb_dir = Column(Text, default='')
        torrent_dir = Column(Text, default='')

    class SABnzbd(base):
        __tablename__ = 'sabnzbd'
        id = Column(Integer, primary_key=True, autoincrement=True)
        username = Column(Text, default='')
        password = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        apikey = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        category = Column(Text, default='tv')
        category_backlog = Column(Text, default='tv')
        category_anime = Column(Text, default='anime')
        category_anime_backlog = Column(Text, default='anime')
        host = Column(Text, default='')
        forced = Column(Boolean, default=False)

    class NZBget(base):
        __tablename__ = 'nzbget'
        id = Column(Integer, primary_key=True, autoincrement=True)
        username = Column(Text, default='')
        password = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        category = Column(Text, default='tv')
        category_backlog = Column(Text, default='tv')
        category_anime = Column(Text, default='anime')
        category_anime_backlog = Column(Text, default='anime')
        host = Column(Text, default='')
        use_https = Column(Boolean, default=False)
        priority = Column(Integer, default=100)

    class Synology(base):
        __tablename__ = 'synology'
        id = Column(Integer, primary_key=True, autoincrement=True)
        username = Column(Text, default='')
        password = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        host = Column(Text, default='')
        path = Column(Text, default='')
        enable_index = Column(Boolean, default=False)
        enable_notifications = Column(Boolean, default=False)
        notify_on_snatch = Column(Boolean, default=False)
        notify_on_download = Column(Boolean, default=False)
        notify_on_subtitle_download = Column(Boolean, default=False)

    class Torrent(base):
        __tablename__ = 'torrent'
        id = Column(Integer, primary_key=True, autoincrement=True)
        username = Column(Text, default='')
        password = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        host = Column(Text, default='')
        path = Column(Text, default='')
        seed_time = Column(Integer, default=0)
        paused = Column(Boolean, default=False)
        high_bandwidth = Column(Boolean, default=False)
        verify_cert = Column(Boolean, default=False)
        label = Column(Text, default='')
        label_anime = Column(Text, default='')
        rpc_url = Column(Text, default='')
        auth_type = Column(Text, default='')

    class Kodi(base):
        __tablename__ = 'kodi'
        id = Column(Integer, primary_key=True, autoincrement=True)
        username = Column(Text, default='')
        password = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        host = Column(Text, default='')
        enable = Column(Boolean, default=False)
        notify_on_snatch = Column(Boolean, default=False)
        notify_on_download = Column(Boolean, default=False)
        notify_on_subtitle_download = Column(Boolean, default=False)
        update_library = Column(Boolean, default=False)
        update_full = Column(Boolean, default=False)
        update_only_first = Column(Boolean, default=False)
        always_on = Column(Boolean, default=False)

    class Plex(base):
        __tablename__ = 'plex'
        id = Column(Integer, primary_key=True, autoincrement=True)
        username = Column(Text, default='')
        password = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        client_username = Column(Text, default='')
        client_password = Column(Text, default='')
        host = Column(Text, default='')
        server_host = Column(Text, default='')
        server_token = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        enable = Column(Boolean, default=False)
        enable_client = Column(Boolean, default=False)
        notify_on_snatch = Column(Boolean, default=False)
        notify_on_download = Column(Boolean, default=False)
        notify_on_subtitle_download = Column(Boolean, default=False)
        update_library = Column(Boolean, default=False)

    class Emby(base):
        __tablename__ = 'emby'
        id = Column(Integer, primary_key=True, autoincrement=True)
        host = Column(Text, default='')
        apikey = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        notify_on_download = Column(Boolean, default=False)
        notify_on_subtitle_download = Column(Boolean, default=False)
        notify_on_snatch = Column(Boolean, default=False)
        enable = Column(Boolean, default=False)

    class Growl(base):
        __tablename__ = 'growl'
        id = Column(Integer, primary_key=True, autoincrement=True)
        host = Column(Text, default='')
        password = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        notify_on_download = Column(Boolean, default=False)
        notify_on_subtitle_download = Column(Boolean, default=False)
        notify_on_snatch = Column(Boolean, default=False)
        enable = Column(Boolean, default=False)

    class FreeMobile(base):
        __tablename__ = 'freemobile'
        id = Column(Integer, primary_key=True, autoincrement=True)
        user_id = Column(Text, default='')
        apikey = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        notify_on_download = Column(Boolean, default=False)
        notify_on_subtitle_download = Column(Boolean, default=False)
        notify_on_snatch = Column(Boolean, default=False)
        enable = Column(Boolean, default=False)

    class Telegram(base):
        __tablename__ = 'telegram'
        id = Column(Integer, primary_key=True, autoincrement=True)
        user_id = Column(Text, default='')
        apikey = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        notify_on_download = Column(Boolean, default=False)
        notify_on_subtitle_download = Column(Boolean, default=False)
        notify_on_snatch = Column(Boolean, default=False)
        enable = Column(Boolean, default=False)

    class Join(base):
        __tablename__ = 'join'
        id = Column(Integer, primary_key=True, autoincrement=True)
        user_id = Column(Text, default='')
        apikey = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        notify_on_download = Column(Boolean, default=False)
        notify_on_subtitle_download = Column(Boolean, default=False)
        notify_on_snatch = Column(Boolean, default=False)
        enable = Column(Boolean, default=False)

    class Prowl(base):
        __tablename__ = 'prowl'
        id = Column(Integer, primary_key=True, autoincrement=True)
        apikey = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        priority = Column(Integer, default=0)
        notify_on_download = Column(Boolean, default=False)
        notify_on_subtitle_download = Column(Boolean, default=False)
        notify_on_snatch = Column(Boolean, default=False)
        enable = Column(Boolean, default=False)

    class Twitter(base):
        __tablename__ = 'twitter'
        id = Column(Integer, primary_key=True, autoincrement=True)
        username = Column(Text, default='')
        password = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        prefix = Column(Text, default='')
        dm_to = Column(Text, default='')
        notify_on_download = Column(Boolean, default=False)
        notify_on_subtitle_download = Column(Boolean, default=False)
        notify_on_snatch = Column(Boolean, default=False)
        use_dm = Column(Boolean, default=False)
        enable = Column(Boolean, default=False)

    class Twilio(base):
        __tablename__ = 'twilio'
        id = Column(Integer, primary_key=True, autoincrement=True)
        phone_sid = Column(Text, default='')
        account_sid = Column(Text, default='')
        auth_token = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        to_number = Column(Text, default='')
        notify_on_download = Column(Boolean, default=False)
        notify_on_subtitle_download = Column(Boolean, default=False)
        notify_on_snatch = Column(Boolean, default=False)
        enable = Column(Boolean, default=False)

    class Boxcar2(base):
        __tablename__ = 'boxcar2'
        id = Column(Integer, primary_key=True, autoincrement=True)
        access_token = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        notify_on_download = Column(Boolean, default=False)
        notify_on_subtitle_download = Column(Boolean, default=False)
        notify_on_snatch = Column(Boolean, default=False)
        enable = Column(Boolean, default=False)

    class Pushover(base):
        __tablename__ = 'pushover'
        id = Column(Integer, primary_key=True, autoincrement=True)
        user_key = Column(Text, default='')
        apikey = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        device = Column(Text, default='')
        sound = Column(Text, default='pushover')
        notify_on_download = Column(Boolean, default=False)
        notify_on_subtitle_download = Column(Boolean, default=False)
        notify_on_snatch = Column(Boolean, default=False)
        enable = Column(Boolean, default=False)

    class Libnotify(base):
        __tablename__ = 'libnotify'
        id = Column(Integer, primary_key=True, autoincrement=True)
        notify_on_download = Column(Boolean, default=False)
        notify_on_subtitle_download = Column(Boolean, default=False)
        notify_on_snatch = Column(Boolean, default=False)
        enable = Column(Boolean, default=False)

    class NMJ(base):
        __tablename__ = 'nmj'
        id = Column(Integer, primary_key=True, autoincrement=True)
        host = Column(Text, default='')
        database = Column(Text, default='')
        mount = Column(Text, default='')
        enable = Column(Boolean, default=False)

    class NMJv2(base):
        __tablename__ = 'nmjv2'
        id = Column(Integer, primary_key=True, autoincrement=True)
        host = Column(Text, default='')
        database = Column(Text, default='')
        db_loc = Column(Enum(NMJv2Location), default=NMJv2Location.LOCAL)
        enable = Column(Boolean, default=False)

    class Slack(base):
        __tablename__ = 'slack'
        id = Column(Integer, primary_key=True, autoincrement=True)
        webhook = Column(Text, default='')
        notify_on_download = Column(Boolean, default=False)
        notify_on_subtitle_download = Column(Boolean, default=False)
        notify_on_snatch = Column(Boolean, default=False)
        enable = Column(Boolean, default=False)

    class Discord(base):
        __tablename__ = 'discord'
        id = Column(Integer, primary_key=True, autoincrement=True)
        webhook = Column(Text, default='')
        avatar_url = Column(Text, default='')
        name = Column(Text, default='')
        notify_on_download = Column(Boolean, default=False)
        notify_on_subtitle_download = Column(Boolean, default=False)
        notify_on_snatch = Column(Boolean, default=False)
        tts = Column(Boolean, default=False)
        enable = Column(Boolean, default=False)

    class Trakt(base):
        __tablename__ = 'trakt'
        id = Column(Integer, primary_key=True, autoincrement=True)
        username = Column(Text, default='')
        blacklist_name = Column(Text, default='')
        oauth_token = Column(MutableDict.as_mutable(CustomStringEncryptedType(JSONType, key=encryption_key)), default={})
        remove_watchlist = Column(Boolean, default=False)
        remove_serieslist = Column(Boolean, default=False)
        remove_show_from_sickrage = Column(Boolean, default=False)
        sync_watchlist = Column(Boolean, default=False)
        method_add = Column(Enum(TraktAddMethod), default=TraktAddMethod.SKIP_ALL)
        start_paused = Column(Boolean, default=False)
        use_recommended = Column(Boolean, default=False)
        sync = Column(Boolean, default=False)
        sync_remove = Column(Boolean, default=False)
        series_provider_default = Column(Enum(SeriesProviderID), default=SeriesProviderID.THETVDB)
        timeout = Column(Integer, default=30)
        enable = Column(Boolean, default=False)

    class PyTivo(base):
        __tablename__ = 'pytivo'
        id = Column(Integer, primary_key=True, autoincrement=True)
        notify_on_download = Column(Boolean, default=False)
        notify_on_subtitle_download = Column(Boolean, default=False)
        notify_on_snatch = Column(Boolean, default=False)
        update_library = Column(Boolean, default=False)
        host = Column(Text, default='')
        share_name = Column(Text, default='')
        tivo_name = Column(Text, default='')
        enable = Column(Boolean, default=False)

    class NMA(base):
        __tablename__ = 'nma'
        id = Column(Integer, primary_key=True, autoincrement=True)
        notify_on_download = Column(Boolean, default=False)
        notify_on_subtitle_download = Column(Boolean, default=False)
        notify_on_snatch = Column(Boolean, default=False)
        api_keys = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        priority = Column(Integer, default=0)
        enable = Column(Boolean, default=False)

    class Pushalot(base):
        __tablename__ = 'pushalot'
        id = Column(Integer, primary_key=True, autoincrement=True)
        notify_on_download = Column(Boolean, default=False)
        notify_on_subtitle_download = Column(Boolean, default=False)
        notify_on_snatch = Column(Boolean, default=False)
        auth_token = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        enable = Column(Boolean, default=False)

    class Pushbullet(base):
        __tablename__ = 'pushbullet'
        id = Column(Integer, primary_key=True, autoincrement=True)
        notify_on_download = Column(Boolean, default=False)
        notify_on_subtitle_download = Column(Boolean, default=False)
        notify_on_snatch = Column(Boolean, default=False)
        api_key = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        device = Column(Text, default='')
        enable = Column(Boolean, default=False)

    class Email(base):
        __tablename__ = 'email'
        id = Column(Integer, primary_key=True, autoincrement=True)
        notify_on_download = Column(Boolean, default=False)
        notify_on_subtitle_download = Column(Boolean, default=False)
        notify_on_snatch = Column(Boolean, default=False)
        host = Column(Text, default='')
        port = Column(Text, default='')
        tls = Column(Boolean, default=False)
        username = Column(Text, default='')
        password = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        send_from = Column(Text, default='')
        send_to_list = Column(Text, default='')
        enable = Column(Boolean, default=False)

    class Alexa(base):
        __tablename__ = 'alexa'
        id = Column(Integer, primary_key=True, autoincrement=True)
        notify_on_download = Column(Boolean, default=False)
        notify_on_subtitle_download = Column(Boolean, default=False)
        notify_on_snatch = Column(Boolean, default=False)
        enable = Column(Boolean, default=False)

    class Subtitles(base):
        __tablename__ = 'subtitles'
        id = Column(Integer, primary_key=True, autoincrement=True)
        languages = Column(Text, default='')
        services_list = Column(Text, default='')
        dir = Column(Text, default='')
        default = Column(Boolean, default=False)
        history = Column(Boolean, default=False)
        hearing_impaired = Column(Boolean, default=False)
        enable_embedded = Column(Boolean, default=False)
        multi = Column(Boolean, default=False)
        services_enabled = Column(Text, default='')
        extra_scripts = Column(Text, default='')
        addic7ed_user = Column(Text, default='')
        addic7ed_pass = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        legendastv_user = Column(Text, default='')
        legendastv_pass = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        itasa_user = Column(Text, default='')
        itasa_pass = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        opensubtitles_user = Column(Text, default='')
        opensubtitles_pass = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        enable = Column(Boolean, default=False)

    class FailedDownloads(base):
        __tablename__ = 'failed_downloads'
        id = Column(Integer, primary_key=True, autoincrement=True)
        enable = Column(Boolean, default=False)

    class FailedSnatches(base):
        __tablename__ = 'failed_snatches'
        id = Column(Integer, primary_key=True, autoincrement=True)
        age = Column(Integer, default=1)
        enable = Column(Boolean, default=False)

    class AniDB(base):
        __tablename__ = 'anidb'
        id = Column(Integer, primary_key=True, autoincrement=True)
        username = Column(Text, default='')
        password = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        use_my_list = Column(Boolean, default=False)
        split_home = Column(Boolean, default=False)
        enable = Column(Boolean, default=False)

    class QualitySizes(base):
        __tablename__ = 'quality_sizes'
        id = Column(Integer, primary_key=True, autoincrement=True)
        quality = Column(IntFlag(Qualities))
        min_size = Column(Integer, default=0)
        max_size = Column(Integer, default=0)

    class SearchProvidersMixin(object):
        id = Column(Integer, primary_key=True, autoincrement=True)
        provider_id = Column(Text, unique=True)
        sort_order = Column(Integer, default=0)
        search_mode = Column(Text, default='eponly')
        search_separator = Column(Text, default=' ')
        cookies = Column(Text, default='')
        proper_strings = Column(Text, default=','.join(['PROPER', 'REPACK', 'REAL', 'RERIP']))
        private = Column(Boolean, default=False)
        supports_backlog = Column(Boolean, default=True)
        supports_absolute_numbering = Column(Boolean, default=False)
        anime_only = Column(Boolean, default=False)
        search_fallback = Column(Boolean, default=False)
        enable_daily = Column(Boolean, default=True)
        enable_backlog = Column(Boolean, default=True)
        enable_cookies = Column(Boolean, default=False)
        custom_settings = Column(MutableDict.as_mutable(CustomStringEncryptedType(JSONType, key=encryption_key)), default={})
        enable = Column(Boolean, default=False)

    class SearchProvidersTorrent(SearchProvidersMixin, base):
        __tablename__ = 'search_providers_torrent'
        provider_type = Column(Enum(SearchProviderType), default=SearchProviderType.TORRENT)
        ratio = Column(Integer, default=0)

    class SearchProvidersNzb(SearchProvidersMixin, base):
        __tablename__ = 'search_providers_nzb'
        provider_type = Column(Enum(SearchProviderType), default=SearchProviderType.NZB)
        api_key = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        username = Column(Text, default='')

    class SearchProvidersTorrentRss(SearchProvidersMixin, base):
        __tablename__ = 'search_providers_torrent_rss'
        provider_type = Column(Enum(SearchProviderType), default=SearchProviderType.TORRENT_RSS)
        name = Column(Text, default='')
        url = Column(Text, default='')
        title_tag = Column(Text, default='')
        ratio = Column(Integer, default=0)

    class SearchProvidersNewznab(SearchProvidersMixin, base):
        __tablename__ = 'search_providers_newznab'
        provider_type = Column(Enum(SearchProviderType), default=SearchProviderType.NEWZNAB)
        name = Column(Text, default='')
        url = Column(Text, default='')
        key = Column(Text, default='')
        cat_ids = Column(Text, default='')
        api_key = Column(CustomStringEncryptedType(Text, key=encryption_key), default='')
        username = Column(Text, default='')

    class MetadataProviders(base):
        __tablename__ = 'metadata_providers'
        id = Column(Integer, primary_key=True, autoincrement=True)
        provider_id = Column(Text, unique=True)
        show_metadata = Column(Boolean, default=False)
        episode_metadata = Column(Boolean, default=False)
        fanart = Column(Boolean, default=False)
        poster = Column(Boolean, default=False)
        banner = Column(Boolean, default=False)
        episode_thumbnails = Column(Boolean, default=False)
        season_posters = Column(Boolean, default=False)
        season_banners = Column(Boolean, default=False)
        season_all_poster = Column(Boolean, default=False)
        season_all_banner = Column(Boolean, default=False)
        enable = Column(Boolean, default=False)
