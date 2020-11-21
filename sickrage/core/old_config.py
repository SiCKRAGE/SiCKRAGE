# Author: echel0n <tv@gmail.com>
# URL: https://tv
# Git: https://github.com/V/git
#
# This file is part of 
#
# is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with   If not, see <http://www.gnu.org/licenses/>.


import os
import os.path
import sys
from ast import literal_eval

from configobj import ConfigObj

import sickrage
from sickrage.core.config.helpers import encrypt_config, decrypt_config
from sickrage.core.enums import SearchFormat
from sickrage.core.helpers import auto_type, backup_versioned_file, convert_dict_keys_to_camelcase
from sickrage.core.common import Quality


class OldConfig(object):
    def __init__(self):
        self.loaded = False

        self.config_obj = None
        self.config_version = 15

        self.sub_id = ""
        self.server_id = ""

        self.debug = False

        self.last_db_compact = 0

        self.log_size = 1048576
        self.log_nr = 5

        self.enable_sickrage_api = False

        self.enable_upnp = False
        self.version_notify = False
        self.auto_update = False
        self.notify_on_update = False
        self.backup_on_update = False
        self.notify_on_login = False
        self.pip3_path = ""
        self.git_reset = False
        self.git_username = ""
        self.git_password = ""
        self.git_path = ""
        self.git_autoissues = False
        self.git_newver = False
        self.socket_timeout = 30
        self.web_host = ""
        self.web_username = ""
        self.web_password = ""
        self.web_port = 8081
        self.web_external_port = 0
        self.web_log = False
        self.web_root = ""
        self.web_ipv6 = False
        self.web_cookie_secret = ""
        self.web_use_gzip = True
        self.handle_reverse_proxy = False
        self.proxy_setting = ""
        self.proxy_series_providers = True
        self.ssl_verify = True
        self.enable_https = False
        self.https_cert = ""
        self.https_key = ""
        self.api_key = ""
        self.sso_auth_enabled = False
        self.local_auth_enabled = False
        self.ip_whitelist_enabled = False
        self.ip_whitelist_localhost_enabled = False
        self.ip_whitelist = ""
        self.series_provider_default_language = 'en'
        self.ep_default_deleted_status = None
        self.launch_browser = False
        self.show_update_stale = False
        self.root_dirs = ""
        self.cpu_preset = "NORMAL"
        self.anon_redirect = ""
        self.download_url = ""
        self.trash_remove_show = False
        self.trash_rotate_logs = False
        self.sort_article = False
        self.display_all_seasons = False
        self.default_page = ""
        self.use_listview = False
        self.processor_follow_symlinks = False
        self.quality_default = None
        self.status_default = None
        self.status_default_after = None
        self.flatten_folders_default = False
        self.subtitles_default = False
        self.series_provider_default = 0
        self.series_provider_timeout = 120
        self.search_format_default = SearchFormat.STANDARD
        self.anime_default = False
        self.scene_default = False
        self.skip_downloaded_default = False
        self.add_show_year_default = False
        self.naming_multi_ep = False
        self.naming_anime_multi_ep = False
        self.naming_pattern = ""
        self.naming_abd_pattern = ""
        self.naming_custom_abd = False
        self.naming_sports_pattern = ""
        self.naming_custom_sports = False
        self.naming_anime_pattern = ""
        self.naming_custom_anime = False
        self.naming_force_folders = False
        self.naming_strip_year = False
        self.naming_anime = ""
        self.use_nzbs = False
        self.use_torrents = False
        self.nzb_method = ""
        self.nzb_dir = ""
        self.usenet_retention = 500
        self.torrent_method = ""
        self.torrent_dir = ""
        self.download_propers = False
        self.enable_rss_cache = False
        self.torrent_file_to_magnet = False
        self.torrent_magnet_to_file = False
        self.download_unverified_magnet_link = False
        self.proper_searcher_interval = ""
        self.allow_high_priority = False
        self.sab_forced = False
        self.randomize_providers = False
        self.backlog_days = 7
        self.add_shows_wo_dir = False
        self.create_missing_show_dirs = False
        self.rename_episodes = False
        self.airdate_episodes = False
        self.file_timestamp_timezone = ""
        self.process_automatically = False
        self.no_delete = False
        self.keep_processed_dir = False
        self.process_method = ""
        self.del_rar_contents = False
        self.delete_non_associated_files = False
        self.move_associated_files = False
        self.postpone_if_sync_files = False
        self.nfo_rename = False
        self.tv_download_dir = ""
        self.unpack = False
        self.unpack_dir = ""
        self.skip_removed_files = False
        self.allowed_extensions = ""
        self.nzbs = False
        self.nzbs_uid = ""
        self.nzbs_hash = ""
        self.omgwtfnzbs = False
        self.newzbin = False
        self.newzbin_username = ""
        self.newzbin_password = ""
        self.sab_username = ""
        self.sab_password = ""
        self.sab_apikey = ""
        self.sab_category = ""
        self.sab_category_backlog = ""
        self.sab_category_anime = ""
        self.sab_category_anime_backlog = ""
        self.sab_host = ""
        self.nzbget_username = ""
        self.nzbget_password = ""
        self.nzbget_category = ""
        self.nzbget_category_backlog = ""
        self.nzbget_category_anime = ""
        self.nzbget_category_anime_backlog = ""
        self.nzbget_host = ""
        self.nzbget_use_https = False
        self.nzbget_priority = 100
        self.syno_dsm_host = ""
        self.syno_dsm_username = ""
        self.syno_dsm_password = ""
        self.syno_dsm_path = ""
        self.torrent_username = ""
        self.torrent_password = ""
        self.torrent_host = ""
        self.torrent_path = ""
        self.torrent_seed_time = ""
        self.torrent_paused = False
        self.torrent_high_bandwidth = False
        self.torrent_label = ""
        self.torrent_label_anime = ""
        self.torrent_verify_cert = False
        self.torrent_rpc_url = ""
        self.torrent_auth_type = ""
        self.use_kodi = False
        self.kodi_always_on = True
        self.kodi_notify_on_snatch = False
        self.kodi_notify_on_download = False
        self.kodi_notify_on_subtitle_download = False
        self.kodi_update_library = False
        self.kodi_update_full = False
        self.kodi_update_only_first = False
        self.kodi_host = ""
        self.kodi_username = ""
        self.kodi_password = ""
        self.use_plex = False
        self.plex_notify_on_snatch = False
        self.plex_notify_on_download = False
        self.plex_notify_on_subtitle_download = False
        self.plex_update_library = False
        self.plex_server_host = ""
        self.plex_server_token = ""
        self.plex_host = ""
        self.plex_username = ""
        self.plex_password = ""
        self.use_plex_client = False
        self.plex_client_username = ""
        self.plex_client_password = ""
        self.use_emby = False
        self.emby_notify_on_snatch = False
        self.emby_notify_on_download = False
        self.emby_notify_on_subtitle_download = False
        self.emby_host = ""
        self.emby_apikey = ""
        self.use_growl = False
        self.growl_notify_on_snatch = False
        self.growl_notify_on_download = False
        self.growl_notify_on_subtitle_download = False
        self.growl_host = ""
        self.growl_password = ""
        self.use_freemobile = False
        self.freemobile_notify_on_snatch = False
        self.freemobile_notify_on_download = False
        self.freemobile_notify_on_subtitle_download = False
        self.freemobile_id = ""
        self.freemobile_apikey = ""
        self.use_telegram = False
        self.telegram_notify_on_snatch = False
        self.telegram_notify_on_download = False
        self.telegram_notify_on_subtitle_download = False
        self.telegram_id = ""
        self.telegram_apikey = ""
        self.use_join = False
        self.join_notify_on_snatch = False
        self.join_notify_on_download = False
        self.join_notify_on_subtitle_download = False
        self.join_id = ""
        self.join_apikey = ""
        self.use_prowl = False
        self.prowl_notify_on_snatch = False
        self.prowl_notify_on_download = False
        self.prowl_notify_on_subtitle_download = False
        self.prowl_apikey = ""
        self.prowl_priority = 0
        self.use_twitter = False
        self.twitter_notify_on_snatch = False
        self.twitter_notify_on_download = False
        self.twitter_notify_on_subtitle_download = False
        self.twitter_username = ""
        self.twitter_password = ""
        self.twitter_prefix = ""
        self.twitter_dmto = ""
        self.twitter_usedm = False
        self.use_twilio = False
        self.twilio_notify_on_snatch = False
        self.twilio_notify_on_download = False
        self.twilio_notify_on_subtitle_download = False
        self.twilio_phone_sid = ""
        self.twilio_account_sid = ""
        self.twilio_auth_token = ""
        self.twilio_to_number = ""
        self.use_boxcar2 = False
        self.boxcar2_notify_on_snatch = False
        self.boxcar2_notify_on_download = False
        self.boxcar2_notify_on_subtitle_download = False
        self.boxcar2_accesstoken = ""
        self.use_pushover = False
        self.pushover_notify_on_snatch = False
        self.pushover_notify_on_download = False
        self.pushover_notify_on_subtitle_download = False
        self.pushover_userkey = ""
        self.pushover_apikey = ""
        self.pushover_device = ""
        self.pushover_sound = ""
        self.use_libnotify = False
        self.libnotify_notify_on_snatch = False
        self.libnotify_notify_on_download = False
        self.libnotify_notify_on_subtitle_download = False
        self.use_nmj = False
        self.nmj_host = ""
        self.nmj_database = ""
        self.nmj_mount = ""
        self.use_anidb = False
        self.anidb_username = ""
        self.anidb_password = ""
        self.anidb_use_mylist = False
        self.anime_split_home = False
        self.use_synoindex = False
        self.use_nmjv2 = False
        self.nmjv2_host = ""
        self.nmjv2_database = ""
        self.nmjv2_dbloc = ""
        self.use_synologynotifier = False
        self.synologynotifier_notify_on_snatch = False
        self.synologynotifier_notify_on_download = False
        self.synologynotifier_notify_on_subtitle_download = False
        self.use_slack = False
        self.slack_notify_on_snatch = False
        self.slack_notify_on_download = False
        self.slack_notify_on_subtitle_download = False
        self.slack_webhook = ""
        self.use_discord = False
        self.discord_notify_on_snatch = False
        self.discord_notify_on_download = False
        self.discord_notify_on_subtitle_download = False
        self.discord_webhook = ""
        self.discord_name = ""
        self.discord_avatar_url = ""
        self.discord_tts = False
        self.use_trakt = False
        self.trakt_username = ""
        self.trakt_oauth_token = ""
        self.trakt_remove_watchlist = False
        self.trakt_remove_serieslist = False
        self.trakt_remove_show_from_sickrage = False
        self.trakt_sync_watchlist = False
        self.trakt_method_add = False
        self.trakt_start_paused = False
        self.trakt_use_recommended = False
        self.trakt_sync = False
        self.trakt_sync_remove = False
        self.trakt_default_indexer = 1
        self.trakt_timeout = 30
        self.trakt_blacklist_name = ""
        self.use_pytivo = False
        self.pytivo_notify_on_snatch = False
        self.pytivo_notify_on_download = False
        self.pytivo_notify_on_subtitle_download = False
        self.pytivo_update_library = False
        self.pytivo_host = ""
        self.pytivo_share_name = ""
        self.pytivo_tivo_name = ""
        self.use_nma = False
        self.nma_notify_on_snatch = False
        self.nma_notify_on_download = False
        self.nma_notify_on_subtitle_download = False
        self.nma_api = ""
        self.nma_priority = 0
        self.use_pushalot = False
        self.pushalot_notify_on_snatch = False
        self.pushalot_notify_on_download = False
        self.pushalot_notify_on_subtitle_download = False
        self.pushalot_authorizationtoken = ""
        self.use_pushbullet = False
        self.pushbullet_notify_on_snatch = False
        self.pushbullet_notify_on_download = False
        self.pushbullet_notify_on_subtitle_download = False
        self.pushbullet_api = ""
        self.pushbullet_device = ""
        self.use_email = False
        self.email_notify_on_snatch = False
        self.email_notify_on_download = False
        self.email_notify_on_subtitle_download = False
        self.email_host = ""
        self.email_port = 25
        self.email_tls = False
        self.email_user = ""
        self.email_password = ""
        self.email_from = ""
        self.email_list = ""
        self.use_alexa = False
        self.alexa_notify_on_snatch = False
        self.alexa_notify_on_download = False
        self.alexa_notify_on_subtitle_download = False
        self.gui_lang = ""

        self.home_layout = ""
        self.history_layout = ""
        self.history_limit = 0
        self.display_show_specials = False
        self.coming_eps_layout = ""
        self.coming_eps_display_paused = False
        self.coming_eps_sort = ""
        self.coming_eps_missed_range = ""
        self.fuzzy_dating = False
        self.trim_zero = False
        self.date_preset = ""
        self.time_preset = ""
        self.time_preset_w_seconds = ""
        self.timezone_display = ""
        self.theme_name = ""
        self.poster_sort_by = ""
        self.poster_sort_dir = ""
        self.filter_row = True
        self.use_subtitles = False
        self.subtitles_languages = []
        self.subtitles_services_list = []
        self.subtitles_dir = ""
        self.subtitles_services_enabled = ""
        self.subtitles_history = False
        self.enable_embedded_subtitles = False
        self.subtitles_hearing_impaired = False
        self.subtitles_multi = False
        self.subtitles_extra_scripts = []
        self.addic7ed_user = ""
        self.addic7ed_pass = ""
        self.opensubtitles_user = ""
        self.opensubtitles_pass = ""
        self.legendastv_user = ""
        self.legendastv_pass = ""
        self.itasa_user = ""
        self.itasa_pass = ""
        self.delete_failed = False
        self.extra_scripts = []
        self.require_words = ""
        self.ignore_words = ""
        self.ignored_subs_list = ""
        self.sync_files = ""
        self.calendar_unprotected = False
        self.calendar_icons = False
        self.no_restart = False
        self.allowed_video_file_exts = []
        self.strip_special_file_bits = False
        self.thetvdb_ap_itoken = ""


        self.auto_postprocessor_freq = None
        self.daily_searcher_freq = None
        self.backlog_searcher_freq = None
        self.version_updater_freq = None
        self.subtitle_searcher_freq = None
        self.show_update_hour = None

        self.use_failed_snatcher = False
        self.failed_snatch_age = None

        self.quality_sizes = {}

        self.custom_providers = ""



        self.random_user_agent = False

        self.fanart_background = True
        self.fanart_background_opacity = 0.4

        self.view_changelog = False

        self.max_queue_workers = None

    @property
    def defaults(self):
        return {
            'Providers': {
                'custom_providers': '',
                'providers_order': []
            },
            # 'NZBs': {
            #     'nzbs': False,
            #     'nzbs_uid': '',
            #     'nzbs_hash': ''
            # },
            # 'Growl': {
            #     'growl_host': '',
            #     'use_growl': False,
            #     'growl_notify_on_download': False,
            #     'growl_notify_on_subtitle_download': False,
            #     'growl_notify_on_snatch': False,
            #     'growl_password': ''
            # },
            'Slack': {
                'slack_notify_on_snatch': False,
                'slack_notify_on_download': False,
                'slack_notify_on_subtitle_download': False,
                'use_slack': False,
                'slack_webhook': ''
            },
            'TELEGRAM': {
                'telegram_notify_on_download': False,
                'telegram_apikey': '',
                'telegram_id': '',
                'use_telegram': False,
                'telegram_notify_on_snatch': False,
                'telegram_notify_on_subtitle_download': False
            },
            'JOIN': {
                'join_notify_on_download': False,
                'join_apikey': '',
                'join_id': '',
                'use_join': False,
                'join_notify_on_snatch': False,
                'join_notify_on_subtitle_download': False
            },
            # 'GUI': {
            #     'coming_eps_display_paused': False,
            #     'display_show_specials': True,
            #     'gui_lang': '',
            #     'history_limit': '100',
            #     'poster_sort_dir': 1,
            #     'coming_eps_missed_range': 7,
            #     'date_preset': '%x',
            #     'fuzzy_dating': False,
            #     'fanart_background': True,
            #     'home_layout': 'poster',
            #     'coming_eps_layout': 'banner',
            #     'coming_eps_sort': 'date',
            #     'poster_sort_by': 'name',
            #     'time_preset': '%I:%M:%S%p',
            #     'trim_zero': False,
            #     'fanart_background_opacity': 0.4,
            #     'history_layout': 'detailed',
            #     'filter_row': True,
            #     'timezone_display': 'local',
            #     'theme_name': 'dark'
            # },
            'NMA': {
                'nma_notify_on_subtitle_download': False,
                'use_nma': False,
                'nma_notify_on_snatch': False,
                'nma_priority': '0',
                'nma_api': '',
                'nma_notify_on_download': False
            },
            'Prowl': {
                'prowl_notify_on_download': False,
                'prowl_apikey': '',
                'prowl_priority': '0',
                'prowl_notify_on_subtitle_download': False,
                'prowl_notify_on_snatch': False,
                'use_prowl': False
            },
            'Synology': {
                'use_synoindex': False
            },
            'Newzbin': {
                'newzbin': False,
                'newzbin_password': '',
                'newzbin_username': ''
            },
            'Trakt': {
                'trakt_remove_serieslist': False,
                'trakt_remove_show_from_sickrage': False,
                'trakt_use_recommended': False,
                'trakt_sync': False,
                'use_trakt': False,
                'trakt_blacklist_name': '',
                'trakt_start_paused': False,
                'trakt_sync_remove': False,
                'trakt_username': '',
                'trakt_oauth_token': '',
                'trakt_method_add': 0,
                'trakt_remove_watchlist': False,
                'trakt_sync_watchlist': False,
                'trakt_timeout': 30,
                'trakt_default_indexer': 1
            },
            'NMJv2': {
                'nmjv2_dbloc': '',
                'nmjv2_database': '',
                'nmjv2_host': '',
                'use_nmjv2': False
            },
            'SABnzbd': {
                'sab_forced': False,
                'sab_category': 'tv',
                'sab_apikey': '',
                'sab_category_anime': 'anime',
                'sab_category_backlog': 'tv',
                'sab_host': '',
                'sab_password': '',
                'sab_username': '',
                'sab_category_anime_backlog': 'anime'
            },
            'Plex': {
                'plex_update_library': False,
                'plex_server_host': '',
                'plex_host': '',
                'plex_password': '',
                'plex_notify_on_subtitle_download': False,
                'plex_notify_on_snatch': False,
                'plex_username': '',
                'plex_notify_on_download': False,
                'plex_server_token': '',
                'use_plex': False,
                'use_plex_client': False,
                'plex_client_username': '',
                'plex_client_password': ''
            },
            'TORRENT': {
                'torrent_verify_cert': False,
                'torrent_paused': False,
                'torrent_host': '',
                'torrent_label_anime': '',
                'torrent_path': '',
                'torrent_auth_type': '',
                'torrent_rpc_url': 'transmission',
                'torrent_username': '',
                'torrent_label': '',
                'torrent_password': '',
                'torrent_high_bandwidth': False,
                'torrent_seed_time': 0
            },
            'Pushalot': {
                'pushalot_notify_on_subtitle_download': False,
                'pushalot_authorizationtoken': '',
                'pushalot_notify_on_snatch': False,
                'pushalot_notify_on_download': False,
                'use_pushalot': False
            },
            'Pushover': {
                'pushover_notify_on_download': False,
                'pushover_sound': 'pushover',
                'use_pushover': False,
                'pushover_notify_on_subtitle_download': False,
                'pushover_device': '',
                'pushover_apikey': '',
                'pushover_userkey': '',
                'pushover_notify_on_snatch': False
            },
            'Email': {
                'email_notify_on_snatch': False,
                'email_list': '',
                'email_password': '',
                'email_tls': False,
                'use_email': False,
                'email_notify_on_download': False,
                'email_port': 25,
                'email_notify_on_subtitle_download': False,
                'email_user': '',
                'email_from': '',
                'email_host': ''
            },
            'KODI': {
                'kodi_update_only_first': False,
                'kodi_notify_on_snatch': False,
                'kodi_notify_on_download': False,
                'kodi_host': '',
                'kodi_username': '',
                'kodi_always_on': True,
                'kodi_update_library': False,
                'use_kodi': False,
                'kodi_password': '',
                'kodi_update_full': False,
                'kodi_notify_on_subtitle_download': False
            },
            'Quality': {
                'sizes': Quality.qualitySizes
            },
            'FreeMobile': {
                'freemobile_notify_on_snatch': False,
                'freemobile_notify_on_subtitle_download': False,
                'freemobile_notify_on_download': False,
                'freemobile_apikey': '',
                'freemobile_id': '',
                'use_freemobile': False
            },
            'Discord': {
                'discord_notify_on_subtitle_download': False,
                'discord_notify_on_download': False,
                'discord_notify_on_snatch': False,
                'discord_webhook': '',
                'use_discord': False,
                'discord_name': '',
                'discord_avatar_url': '',
                'discord_tts': False
            },
            'SynologyNotifier': {
                'synologynotifier_notify_on_snatch': False,
                'synologynotifier_notify_on_download': False,
                'use_synologynotifier': False,
                'synologynotifier_notify_on_subtitle_download': False
            },
            'ANIDB': {
                'anidb_use_mylist': False,
                'use_anidb': False,
                'anidb_password': '',
                'anidb_username': ''
            },
            'Blackhole': {
                'nzb_dir': '',
                'torrent_dir': ''
            },
            # 'General': {
            #     'sub_id': self.sub_id,
            #     'server_id': self.server_id,
            #     'enable_sickrage_api': True,
            #     'log_size': 1048576,
            #     'calendar_unprotected': False,
            #     'https_key': os.path.abspath(os.path.join(sickrage.app.data_dir, 'server.key')),
            #     'https_cert': os.path.abspath(os.path.join(sickrage.app.data_dir, 'server.crt')),
            #     'allow_high_priority': True,
            #     'anon_redirect': 'http://nullrefer.com/?',
            #     'series_provider_timeout': 120,
            #     'web_use_gzip': True,
            #     'dailysearch_frequency': 40,
            #     'ignore_words': 'german,french,core2hd,dutch,swedish,reenc,MrLss',
            #     'api_key': self.api_key or generate_api_key(),
            #     'sso_auth_enabled': True,
            #     'local_auth_enabled': False,
            #     'ip_whitelist_enabled': False,
            #     'ip_whitelist_localhost_enabled': False,
            #     'ip_whitelist': '',
            #     'check_propers_interval': 'daily',
            #     'nzb_method': 'blackhole',
            #     'web_cookie_secret': self.web_cookie_secret or generate_secret(),
            #     'ssl_verify': True,
            #     'enable_upnp': True,
            #     'version_notify': True,
            #     'web_root': '',
            #     'add_shows_wo_dir': False,
            #     'debug': True,
            #     'series_provider_default': 0,
            #     'use_torrents': True,
            #     'display_all_seasons': True,
            #     'usenet_retention': 500,
            #     'download_propers': True,
            #     'pip3_path': 'pip3',
            #     'del_rar_contents': False,
            #     'process_method': 'copy',
            #     'file_timestamp_timezone': 'network',
            #     'auto_update': True,
            #     'tv_download_dir': '',
            #     'naming_custom_abd': False,
            #     'scene_default': False,
            #     'skip_downloaded_default': False,
            #     'add_show_year_default': False,
            #     'naming_sports_pattern': '%SN - %A-D - %EN',
            #     'create_missing_show_dirs': False,
            #     'trash_rotate_logs': False,
            #     'airdate_episodes': False,
            #     'notify_on_update': True,
            #     'backup_on_update': True,
            #     'git_autoissues': False,
            #     'backlog_days': 7,
            #     'root_dirs': '',
            #     'naming_pattern': 'Season %0S/%SN - S%0SE%0E - %EN',
            #     'sort_article': False,
            #     'handle_reverse_proxy': False,
            #     'postpone_if_sync_files': True,
            #     'cpu_preset': 'NORMAL',
            #     'nfo_rename': True,
            #     'naming_anime_multi_ep': 1,
            #     'use_nzbs': False,
            #     'web_ipv6': False,
            #     'anime_default': False,
            #     'default_page': 'home',
            #     'update_frequency': 1,
            #     'download_url': '',
            #     'show_update_hour': 3,
            #     'enable_rss_cache': True,
            #     'torrent_file_to_magnet': False,
            #     'torrent_magnet_to_file': True,
            #     'download_unverified_magnet_link': False,
            #     'status_default': SKIPPED,
            #     'naming_anime': 3,
            #     'naming_custom_sports': False,
            #     'naming_anime_pattern': 'Season %0S/%SN - S%0SE%0E - %EN',
            #     'naming_custom_anime': False,
            #     'randomize_providers': False,
            #     'web_host': get_lan_ip(),
            #     'web_username': '',
            #     'web_password': '',
            #     'config_version': self.config_version,
            #     'process_automatically': False,
            #     'git_path': 'git',
            #     'sync_files': '!sync,lftp-pget-status,part,bts,!qb',
            #     'web_port': 8081,
            #     'web_external_port': self.web_external_port or random.randint(49152, 65536),
            #     'launch_browser': False,
            #     'unpack': False,
            #     'unpack_dir': "",
            #     'delete_non_associated_files': True,
            #     'move_associated_files': False,
            #     'naming_multi_ep': 1,
            #     'random_user_agent': False,
            #     'torrent_method': 'blackhole',
            #     'use_listview': False,
            #     'trash_remove_show': False,
            #     'enable_https': False,
            #     'no_delete': False,
            #     'naming_abd_pattern': '%SN - %A.D - %EN',
            #     'socket_timeout': 30,
            #     'proxy_setting': '',
            #     'backlog_frequency': 1440,
            #     'notify_on_login': False,
            #     'rename_episodes': True,
            #     'quality_default': SD,
            #     'git_username': '',
            #     'extra_scripts': '',
            #     'flatten_folders_default': False,
            #     'indexer_default_lang': 'en',
            #     'auto_postprocessor_frequency': 10,
            #     'show_update_stale': True,
            #     'git_password': '',
            #     'ep_default_deleted_status': 6,
            #     'no_restart': False,
            #     'allowed_video_file_exts': [
            #         'avi', 'mkv', 'mpg', 'mpeg', 'wmv',
            #         'ogm', 'mp4', 'iso', 'img', 'divx',
            #         'm2ts', 'm4v', 'ts', 'flv', 'f4v',
            #         'mov', 'rmvb', 'vob', 'dvr-ms', 'wtv',
            #         'ogv', '3gp', 'webm', 'tp'
            #     ],
            #     'require_words': '',
            #     'naming_strip_year': False,
            #     'proxy_series_providers': True,
            #     'web_log': False,
            #     'log_nr': 5,
            #     'git_newver': False,
            #     'git_reset': True,
            #     'search_format_default': SearchFormat.STANDARD,
            #     'skip_removed_files': False,
            #     'status_default_after': WANTED,
            #     'last_db_compact': 0,
            #     'ignored_subs_list': 'dk,fin,heb,kor,nor,nordic,pl,swe',
            #     'calendar_icons': False,
            #     'keep_processed_dir': True,
            #     'processor_follow_symlinks': False,
            #     'allowed_extensions': 'srt,nfo,srr,sfv',
            #     'view_changelog': False,
            #     'strip_special_file_bits': True,
            #     'max_queue_workers': 5
            # },
            'NZBget': {
                'nzbget_host': '',
                'nzbget_category_anime': 'anime',
                'nzbget_use_https': False,
                'nzbget_password': 'tegbzn6789',
                'nzbget_category': 'tv',
                'nzbget_priority': 100,
                'nzbget_category_anime_backlog': 'anime',
                'nzbget_username': 'nzbget',
                'nzbget_category_backlog': 'tv'
            },
            'SynologyDSM': {
                'syno_dsm_host': '',
                'syno_dsm_username': '',
                'syno_dsm_password': '',
                'syno_dsm_path': '',
            },
            'Emby': {
                'use_emby': False,
                'emby_apikey': '',
                'emby_host': '',
                'emby_notify_on_subtitle_download': False,
                'emby_notify_on_download': False,
                'emby_notify_on_snatch': False,
            },
            'pyTivo': {
                'pytivo_share_name': '',
                'pytivo_notify_on_download': False,
                'pytivo_tivo_name': '',
                'pytivo_notify_on_snatch': False,
                'pytivo_host': '',
                'pytivo_notify_on_subtitle_download': False,
                'pyTivo_update_library': False,
                'use_pytivo': False
            },
            'theTVDB': {
                'thetvdb_ap_itoken': ''
            },
            'Pushbullet': {
                'pushbullet_device': '',
                'use_pushbullet': False,
                'pushbullet_notify_on_download': False,
                'pushbullet_notify_on_subtitle_download': False,
                'pushbullet_notify_on_snatch': False,
                'pushbullet_api': ''
            },
            'Libnotify': {
                'libnotify_notify_on_subtitle_download': False,
                'libnotify_notify_on_snatch': False,
                'libnotify_notify_on_download': False,
                'use_libnotify': False
            },
            'Boxcar2': {
                'use_boxcar2': False,
                'boxcar2_notify_on_snatch': False,
                'boxcar2_notify_on_download': False,
                'boxcar2_accesstoken': '',
                'boxcar2_notify_on_subtitle_download': False
            },
            'FailedDownloads': {
                'delete_failed': False
            },
            'FailedSnatches': {
                'use_failed_snatcher': False,
                'failed_snatch_age': 2
            },
            'NMJ': {
                'nmj_host': '',
                'nmj_mount': '',
                'use_nmj': False,
                'nmj_database': ''
            },
            'Twitter': {
                'twitter_username': '',
                'use_twitter': False,
                'twitter_password': '',
                'twitter_notify_on_download': False,
                'twitter_notify_on_subtitle_download': False,
                'twitter_notify_on_snatch': False,
                'twitter_prefix': 'SiCKRAGE',
                'twitter_dmto': '',
                'twitter_usedm': False
            },
            'Twilio': {
                'use_twilio': False,
                'twilio_notify_on_snatch': False,
                'twilio_notify_on_download': False,
                'twilio_notify_on_subtitle_download': False,
                'twilio_phone_sid': '',
                'twilio_account_sid': '',
                'twilio_auth_token': '',
                'twilio_to_number': '',
            },
            'Alexa': {
                'use_alexa': False,
                'alexa_notify_on_snatch': False,
                'alexa_notify_on_download': False,
                'alexa_notify_on_subtitle_download': False,
            },
            'Subtitles': {
                'itasa_password': '',
                'opensubtitles_username': '',
                'subtitles_services_list': [],
                'subtitles_history': False,
                'legendastv_password': '',
                'subtitles_hearing_impaired': False,
                'addic7ed_password': '',
                'subtitles_languages': [],
                'enable_embedded_subtitles': False,
                'subtitles_finder_frequency': 1,
                'subtitles_default': False,
                'subtitles_multi': True,
                'subtitles_services_enabled': '',
                'itasa_username': '',
                'subtitles_dir': '',
                'addic7ed_username': '',
                'opensubtitles_password': '',
                'subtitles_extra_scripts': '',
                'use_subtitles': False,
                'legendastv_username': ''
            },
            'ANIME': {
                'anime_split_home': False
            }
        }

    @property
    def config_data(self):
        provider_keys = ['enabled', 'confirmed', 'ranked', 'engrelease', 'onlyspasearch', 'sorting', 'options', 'ratio',
                         'minseed', 'minleech', 'freeleech', 'search_mode', 'search_fallback', 'enable_daily', 'key',
                         'enable_backlog', 'cat', 'subtitle', 'api_key', 'hash', 'digest', 'username', 'password',
                         'passkey', 'pin', 'reject_m2ts', 'cookies', 'custom_url']

        return {
            'General': {
                'sub_id': self.sub_id,
                'server_id': self.server_id,
                'config_version': self.config_version,
                'last_db_compact': self.last_db_compact,
                'enable_sickrage_api': int(self.enable_sickrage_api),
                'git_autoissues': int(self.git_autoissues),
                'git_username': self.git_username,
                'git_password': self.git_password,
                'git_reset': int(self.git_reset),
                'git_newver': int(self.git_newver),
                'log_nr': int(self.log_nr),
                'log_size': int(self.log_size),
                'socket_timeout': self.socket_timeout,
                'web_port': self.web_port,
                'web_external_port': self.web_external_port,
                'web_host': self.web_host,
                'web_username': self.web_username,
                'web_password': self.web_password,
                'web_ipv6': int(self.web_ipv6),
                'web_log': int(self.web_log),
                'web_root': self.web_root,
                'web_cookie_secret': self.web_cookie_secret,
                'web_use_gzip': int(self.web_use_gzip),
                'ssl_verify': int(self.ssl_verify),
                'download_url': self.download_url,
                'cpu_preset': self.cpu_preset,
                'max_queue_workers': self.max_queue_workers,
                'anon_redirect': self.anon_redirect,
                'api_key': self.api_key,
                'sso_auth_enabled': int(self.sso_auth_enabled),
                'local_auth_enabled': int(self.local_auth_enabled),
                'ip_whitelist_enabled': self.ip_whitelist_enabled,
                'ip_whitelist_localhost_enabled': self.ip_whitelist_localhost_enabled,
                'ip_whitelist': self.ip_whitelist,
                'debug': int(self.debug),
                'default_page': self.default_page,
                'enable_https': int(self.enable_https),
                'https_cert': self.https_cert,
                'https_key': self.https_key,
                'handle_reverse_proxy': int(self.handle_reverse_proxy),
                'use_nzbs': int(self.use_nzbs),
                'use_torrents': int(self.use_torrents),
                'nzb_method': self.nzb_method,
                'torrent_method': self.torrent_method,
                'usenet_retention': int(self.usenet_retention),
                'auto_postprocessor_frequency': int(self.auto_postprocessor_freq),
                'dailysearch_frequency': int(self.daily_searcher_freq),
                'backlog_frequency': int(self.backlog_searcher_freq),
                'update_frequency': int(self.version_updater_freq),
                'show_update_hour': int(self.show_update_hour),
                'show_update_stale': int(self.show_update_stale),
                'download_propers': int(self.download_propers),
                'enable_rss_cache': int(self.enable_rss_cache),
                'torrent_file_to_magnet': int(self.torrent_file_to_magnet),
                'torrent_magnet_to_file': int(self.torrent_magnet_to_file),
                'download_unverified_magnet_link': int(self.download_unverified_magnet_link),
                'randomize_providers': int(self.randomize_providers),
                'check_propers_interval': self.proper_searcher_interval,
                'allow_high_priority': int(self.allow_high_priority),
                'skip_removed_files': int(self.skip_removed_files),
                'quality_default': int(self.quality_default),
                'status_default': int(self.status_default),
                'status_default_after': int(self.status_default_after),
                'flatten_folders_default': int(self.flatten_folders_default),
                'series_provider_default': int(self.series_provider_default),
                'series_provider_timeout': int(self.series_provider_timeout),
                'anime_default': int(self.anime_default),
                'search_format_default': int(self.search_format_default),
                'scene_default': int(self.scene_default),
                'skip_downloaded_default': int(self.skip_downloaded_default),
                'add_show_year_default': int(self.add_show_year_default),
                'enable_upnp': int(self.enable_upnp),
                'version_notify': int(self.version_notify),
                'auto_update': int(self.auto_update),
                'notify_on_update': int(self.notify_on_update),
                'backup_on_update': int(self.backup_on_update),
                'notify_on_login': int(self.notify_on_login),
                'naming_strip_year': int(self.naming_strip_year),
                'naming_pattern': self.naming_pattern,
                'naming_custom_abd': int(self.naming_custom_abd),
                'naming_abd_pattern': self.naming_abd_pattern,
                'naming_custom_sports': int(self.naming_custom_sports),
                'naming_sports_pattern': self.naming_sports_pattern,
                'naming_custom_anime': int(self.naming_custom_anime),
                'naming_anime_pattern': self.naming_anime_pattern,
                'naming_multi_ep': int(self.naming_multi_ep),
                'naming_anime_multi_ep': int(self.naming_anime_multi_ep),
                'naming_anime': int(self.naming_anime),
                'indexer_default_lang': self.series_provider_default_language,
                'ep_default_deleted_status': int(self.ep_default_deleted_status),
                'launch_browser': int(self.launch_browser),
                'trash_remove_show': int(self.trash_remove_show),
                'trash_rotate_logs': int(self.trash_rotate_logs),
                'sort_article': int(self.sort_article),
                'proxy_setting': self.proxy_setting,
                'proxy_series_providers': int(self.proxy_series_providers),
                'use_listview': int(self.use_listview),
                'backlog_days': int(self.backlog_days),
                'root_dirs': self.root_dirs,
                'tv_download_dir': self.tv_download_dir,
                'keep_processed_dir': int(self.keep_processed_dir),
                'process_method': self.process_method,
                'del_rar_contents': int(self.del_rar_contents),
                'move_associated_files': int(self.move_associated_files),
                'sync_files': self.sync_files,
                'postpone_if_sync_files': int(self.postpone_if_sync_files),
                'nfo_rename': int(self.nfo_rename),
                'process_automatically': int(self.process_automatically),
                'no_delete': int(self.no_delete),
                'unpack': int(self.unpack),
                'unpack_dir': self.unpack_dir,
                'rename_episodes': int(self.rename_episodes),
                'airdate_episodes': int(self.airdate_episodes),
                'file_timestamp_timezone': self.file_timestamp_timezone,
                'create_missing_show_dirs': int(self.create_missing_show_dirs),
                'add_shows_wo_dir': int(self.add_shows_wo_dir),
                'extra_scripts': '|'.join(self.extra_scripts),
                'pip3_path': self.pip3_path,
                'git_path': self.git_path,
                'ignore_words': self.ignore_words,
                'require_words': self.require_words,
                'ignored_subs_list': self.ignored_subs_list,
                'calendar_unprotected': int(self.calendar_unprotected),
                'calendar_icons': int(self.calendar_icons),
                'no_restart': int(self.no_restart),
                'allowed_video_file_exts': self.allowed_video_file_exts,
                'display_all_seasons': int(self.display_all_seasons),
                'random_user_agent': int(self.random_user_agent),
                'processor_follow_symlinks': int(self.processor_follow_symlinks),
                'delete_non_associated_files': int(self.delete_non_associated_files),
                'allowed_extensions': self.allowed_extensions,
                'view_changelog': int(self.view_changelog),
                'strip_special_file_bits': int(self.strip_special_file_bits)
            },
            'GUI': {
                'gui_lang': self.gui_lang,
                'theme_name': self.theme_name,
                'home_layout': self.home_layout,
                'history_layout': self.history_layout,
                'history_limit': self.history_limit,
                'display_show_specials': int(self.display_show_specials),
                'coming_eps_layout': self.coming_eps_layout,
                'coming_eps_display_paused': int(self.coming_eps_display_paused),
                'coming_eps_sort': self.coming_eps_sort,
                'coming_eps_missed_range': int(self.coming_eps_missed_range),
                'fuzzy_dating': int(self.fuzzy_dating),
                'trim_zero': int(self.trim_zero),
                'date_preset': self.date_preset,
                'time_preset': self.time_preset_w_seconds,
                'timezone_display': self.timezone_display,
                'poster_sort_by': self.poster_sort_by,
                'poster_sort_dir': self.poster_sort_dir,
                'filter_row': int(self.filter_row),
                'fanart_background': int(self.fanart_background),
                'fanart_background_opacity': self.fanart_background_opacity,
            },
            'Blackhole': {
                'nzb_dir': self.nzb_dir,
                'torrent_dir': self.torrent_dir,
            },
            'NZBs': {
                'nzbs': int(self.nzbs),
                'nzbs_uid': self.nzbs_uid,
                'nzbs_hash': self.nzbs_hash,
            },
            'Newzbin': {
                'newzbin': int(self.newzbin),
                'newzbin_username': self.newzbin_username,
                'newzbin_password': self.newzbin_password,
            },
            'SABnzbd': {
                'sab_username': self.sab_username,
                'sab_password': self.sab_password,
                'sab_apikey': self.sab_apikey,
                'sab_category': self.sab_category,
                'sab_category_backlog': self.sab_category_backlog,
                'sab_category_anime': self.sab_category_anime,
                'sab_category_anime_backlog': self.sab_category_anime_backlog,
                'sab_host': self.sab_host,
                'sab_forced': int(self.sab_forced),
            },
            'NZBget': {
                'nzbget_username': self.nzbget_username,
                'nzbget_password': self.nzbget_password,
                'nzbget_category': self.nzbget_category,
                'nzbget_category_backlog': self.nzbget_category_backlog,
                'nzbget_category_anime': self.nzbget_category_anime,
                'nzbget_category_anime_backlog': self.nzbget_category_anime_backlog,
                'nzbget_host': self.nzbget_host,
                'nzbget_use_https': int(self.nzbget_use_https),
                'nzbget_priority': self.nzbget_priority,
            },
            'SynologyDSM': {
                'syno_dsm_host': self.syno_dsm_host,
                'syno_dsm_username': self.syno_dsm_username,
                'syno_dsm_password': self.syno_dsm_password,
                'syno_dsm_path': self.syno_dsm_path,
            },
            'TORRENT': {
                'torrent_username': self.torrent_username,
                'torrent_password': self.torrent_password,
                'torrent_host': self.torrent_host,
                'torrent_path': self.torrent_path,
                'torrent_seed_time': int(self.torrent_seed_time),
                'torrent_paused': int(self.torrent_paused),
                'torrent_high_bandwidth': int(self.torrent_high_bandwidth),
                'torrent_label': self.torrent_label,
                'torrent_label_anime': self.torrent_label_anime,
                'torrent_verify_cert': int(self.torrent_verify_cert),
                'torrent_rpc_url': self.torrent_rpc_url,
                'torrent_auth_type': self.torrent_auth_type,
            },
            'KODI': {
                'use_kodi': int(self.use_kodi),
                'kodi_always_on': int(self.kodi_always_on),
                'kodi_notify_on_snatch': int(self.kodi_notify_on_snatch),
                'kodi_notify_on_download': int(self.kodi_notify_on_download),
                'kodi_notify_on_subtitle_download': int(self.kodi_notify_on_subtitle_download),
                'kodi_update_library': int(self.kodi_update_library),
                'kodi_update_full': int(self.kodi_update_full),
                'kodi_update_only_first': int(self.kodi_update_only_first),
                'kodi_host': self.kodi_host,
                'kodi_username': self.kodi_username,
                'kodi_password': self.kodi_password,
            },
            'Plex': {
                'use_plex': int(self.use_plex),
                'plex_notify_on_snatch': int(self.plex_notify_on_snatch),
                'plex_notify_on_download': int(self.plex_notify_on_download),
                'plex_notify_on_subtitle_download': int(self.plex_notify_on_subtitle_download),
                'plex_update_library': int(self.plex_update_library),
                'plex_server_host': self.plex_server_host,
                'plex_server_token': self.plex_server_token,
                'plex_host': self.plex_host,
                'plex_username': self.plex_username,
                'plex_password': self.plex_password,
            },
            'Emby': {
                'use_emby': int(self.use_emby),
                'emby_notify_on_snatch': int(self.emby_notify_on_snatch),
                'emby_notify_on_download': int(self.emby_notify_on_download),
                'emby_notify_on_subtitle_download': int(self.emby_notify_on_subtitle_download),
                'emby_host': self.emby_host,
                'emby_apikey': self.emby_apikey,
            },
            'Growl': {
                'use_growl': int(self.use_growl),
                'growl_notify_on_snatch': int(self.growl_notify_on_snatch),
                'growl_notify_on_download': int(self.growl_notify_on_download),
                'growl_notify_on_subtitle_download': int(self.growl_notify_on_subtitle_download),
                'growl_host': self.growl_host,
                'growl_password': self.growl_password,
            },
            'FreeMobile': {
                'use_freemobile': int(self.use_freemobile),
                'freemobile_notify_on_snatch': int(self.freemobile_notify_on_snatch),
                'freemobile_notify_on_download': int(self.freemobile_notify_on_download),
                'freemobile_notify_on_subtitle_download': int(self.freemobile_notify_on_subtitle_download),
                'freemobile_id': self.freemobile_id,
                'freemobile_apikey': self.freemobile_apikey,
            },
            'TELEGRAM': {
                'use_telegram': int(self.use_telegram),
                'telegram_notify_on_snatch': int(self.telegram_notify_on_snatch),
                'telegram_notify_on_download': int(self.telegram_notify_on_download),
                'telegram_notify_on_subtitle_download': int(self.telegram_notify_on_subtitle_download),
                'telegram_id': self.telegram_id,
                'telegram_apikey': self.telegram_apikey,
            },
            'JOIN': {
                'use_join': int(self.use_join),
                'join_notify_on_snatch': int(self.join_notify_on_snatch),
                'join_notify_on_download': int(self.join_notify_on_download),
                'join_notify_on_subtitle_download': int(self.join_notify_on_subtitle_download),
                'join_id': self.join_id,
                'join_apikey': self.join_apikey,
            },
            'Prowl': {
                'use_prowl': int(self.use_prowl),
                'prowl_notify_on_snatch': int(self.prowl_notify_on_snatch),
                'prowl_notify_on_download': int(self.prowl_notify_on_download),
                'prowl_notify_on_subtitle_download': int(self.prowl_notify_on_subtitle_download),
                'prowl_apikey': self.prowl_apikey,
                'prowl_priority': self.prowl_priority,
            },
            'Twitter': {
                'use_twitter': int(self.use_twitter),
                'twitter_notify_on_snatch': int(self.twitter_notify_on_snatch),
                'twitter_notify_on_download': int(self.twitter_notify_on_download),
                'twitter_notify_on_subtitle_download': int(self.twitter_notify_on_subtitle_download),
                'twitter_username': self.twitter_username,
                'twitter_password': self.twitter_password,
                'twitter_prefix': self.twitter_prefix,
                'twitter_dmto': self.twitter_dmto,
                'twitter_usedm': int(self.twitter_usedm),
            },
            'Twilio': {
                'use_twilio': int(self.use_twilio),
                'twilio_notify_on_snatch': int(self.twilio_notify_on_snatch),
                'twilio_notify_on_download': int(self.twilio_notify_on_download),
                'twilio_notify_on_subtitle_download': int(self.twilio_notify_on_subtitle_download),
                'twilio_phone_sid': self.twilio_phone_sid,
                'twilio_account_sid': self.twilio_account_sid,
                'twilio_auth_token': self.twilio_auth_token,
                'twilio_to_number': self.twilio_to_number,
            },
            'Alexa': {
                'use_alexa': int(self.use_alexa),
                'alexa_notify_on_snatch': int(self.alexa_notify_on_snatch),
                'alexa_notify_on_download': int(self.alexa_notify_on_download),
                'alexa_notify_on_subtitle_download': int(self.alexa_notify_on_subtitle_download),
            },
            'Boxcar2': {
                'use_boxcar2': int(self.use_boxcar2),
                'boxcar2_notify_on_snatch': int(self.boxcar2_notify_on_snatch),
                'boxcar2_notify_on_download': int(self.boxcar2_notify_on_download),
                'boxcar2_notify_on_subtitle_download': int(self.boxcar2_notify_on_subtitle_download),
                'boxcar2_accesstoken': self.boxcar2_accesstoken,
            },
            'Pushover': {
                'use_pushover': int(self.use_pushover),
                'pushover_notify_on_snatch': int(self.pushover_notify_on_snatch),
                'pushover_notify_on_download': int(self.pushover_notify_on_download),
                'pushover_notify_on_subtitle_download': int(self.pushover_notify_on_subtitle_download),
                'pushover_userkey': self.pushover_userkey,
                'pushover_apikey': self.pushover_apikey,
                'pushover_device': self.pushover_device,
                'pushover_sound': self.pushover_sound,
            },
            'Libnotify': {
                'use_libnotify': int(self.use_libnotify),
                'libnotify_notify_on_snatch': int(self.libnotify_notify_on_snatch),
                'libnotify_notify_on_download': int(self.libnotify_notify_on_download),
                'libnotify_notify_on_subtitle_download': int(self.libnotify_notify_on_subtitle_download)
            },
            'NMJ': {
                'use_nmj': int(self.use_nmj),
                'nmj_host': self.nmj_host,
                'nmj_database': self.nmj_database,
                'nmj_mount': self.nmj_mount,
            },
            'NMJv2': {
                'use_nmjv2': int(self.use_nmjv2),
                'nmjv2_host': self.nmjv2_host,
                'nmjv2_database': self.nmjv2_database,
                'nmjv2_dbloc': self.nmjv2_dbloc,
            },
            'Synology': {
                'use_synoindex': int(self.use_synoindex),
            },
            'SynologyNotifier': {
                'use_synologynotifier': int(self.use_synologynotifier),
                'synologynotifier_notify_on_snatch': int(self.synologynotifier_notify_on_snatch),
                'synologynotifier_notify_on_download': int(self.synologynotifier_notify_on_download),
                'synologynotifier_notify_on_subtitle_download': int(self.synologynotifier_notify_on_subtitle_download),
            },
            'theTVDB': {
                'thetvdb_ap_itoken': self.thetvdb_ap_itoken,
            },
            'Slack': {
                'use_slack': int(self.use_slack),
                'slack_notify_on_snatch': int(self.slack_notify_on_snatch),
                'slack_notify_on_download': int(self.slack_notify_on_download),
                'slack_notify_on_subtitle_download': int(self.slack_notify_on_subtitle_download),
                'slack_webhook': self.slack_webhook
            },
            'Discord': {
                'use_discord': int(self.use_discord),
                'discord_notify_on_snatch': int(self.discord_notify_on_snatch),
                'discord_notify_on_download': int(self.discord_notify_on_download),
                'discord_notify_on_subtitle_download': int(self.discord_notify_on_subtitle_download),
                'discord_webhook': self.discord_webhook,
                'discord_name': self.discord_name,
                'discord_avatar_url': self.discord_avatar_url,
                'discord_tts': int(self.discord_tts)
            },
            'Trakt': {
                'use_trakt': int(self.use_trakt),
                'trakt_username': self.trakt_username,
                'trakt_oauth_token': repr(self.trakt_oauth_token),
                'trakt_remove_watchlist': int(self.trakt_remove_watchlist),
                'trakt_remove_serieslist': int(self.trakt_remove_serieslist),
                'trakt_remove_show_from_sickrage': int(self.trakt_remove_show_from_sickrage),
                'trakt_sync_watchlist': int(self.trakt_sync_watchlist),
                'trakt_method_add': int(self.trakt_method_add),
                'trakt_start_paused': int(self.trakt_start_paused),
                'trakt_use_recommended': int(self.trakt_use_recommended),
                'trakt_sync': int(self.trakt_sync),
                'trakt_sync_remove': int(self.trakt_sync_remove),
                'trakt_default_indexer': int(self.trakt_default_indexer),
                'trakt_timeout': int(self.trakt_timeout),
                'trakt_blacklist_name': self.trakt_blacklist_name,
            },
            'pyTivo': {
                'use_pytivo': int(self.use_pytivo),
                'pytivo_notify_on_snatch': int(self.pytivo_notify_on_snatch),
                'pytivo_notify_on_download': int(self.pytivo_notify_on_download),
                'pytivo_notify_on_subtitle_download': int(self.pytivo_notify_on_subtitle_download),
                'pyTivo_update_library': int(self.pytivo_update_library),
                'pytivo_host': self.pytivo_host,
                'pytivo_share_name': self.pytivo_share_name,
                'pytivo_tivo_name': self.pytivo_tivo_name,
            },
            'NMA': {
                'use_nma': int(self.use_nma),
                'nma_notify_on_snatch': int(self.nma_notify_on_snatch),
                'nma_notify_on_download': int(self.nma_notify_on_download),
                'nma_notify_on_subtitle_download': int(self.nma_notify_on_subtitle_download),
                'nma_api': self.nma_api,
                'nma_priority': self.nma_priority,
            },
            'Pushalot': {
                'use_pushalot': int(self.use_pushalot),
                'pushalot_notify_on_snatch': int(self.pushalot_notify_on_snatch),
                'pushalot_notify_on_download': int(self.pushalot_notify_on_download),
                'pushalot_notify_on_subtitle_download': int(self.pushalot_notify_on_subtitle_download),
                'pushalot_authorizationtoken': self.pushalot_authorizationtoken,
            },
            'Pushbullet': {
                'use_pushbullet': int(self.use_pushbullet),
                'pushbullet_notify_on_snatch': int(self.pushbullet_notify_on_snatch),
                'pushbullet_notify_on_download': int(self.pushbullet_notify_on_download),
                'pushbullet_notify_on_subtitle_download': int(self.pushbullet_notify_on_subtitle_download),
                'pushbullet_api': self.pushbullet_api,
                'pushbullet_device': self.pushbullet_device,
            },
            'Email': {
                'use_email': int(self.use_email),
                'email_notify_on_snatch': int(self.email_notify_on_snatch),
                'email_notify_on_download': int(self.email_notify_on_download),
                'email_notify_on_subtitle_download': int(self.email_notify_on_subtitle_download),
                'email_host': self.email_host,
                'email_port': int(self.email_port),
                'email_tls': int(self.email_tls),
                'email_user': self.email_user,
                'email_password': self.email_password,
                'email_from': self.email_from,
                'email_list': self.email_list,
            },
            'Subtitles': {
                'use_subtitles': int(self.use_subtitles),
                'subtitles_languages': self.subtitles_languages,
                'subtitles_services_list': self.subtitles_services_list,
                'subtitles_services_enabled': '|'.join([str(x) for x in self.subtitles_services_enabled]),
                'subtitles_dir': self.subtitles_dir,
                'subtitles_default': int(self.subtitles_default),
                'subtitles_history': int(self.subtitles_history),
                'enable_embedded_subtitles': int(self.enable_embedded_subtitles),
                'subtitles_hearing_impaired': int(self.subtitles_hearing_impaired),
                'subtitles_finder_frequency': int(self.subtitle_searcher_freq),
                'subtitles_multi': int(self.subtitles_multi),
                'subtitles_extra_scripts': '|'.join(self.subtitles_extra_scripts),
                'addic7ed_username': self.addic7ed_user,
                'addic7ed_password': self.addic7ed_pass,
                'legendastv_username': self.legendastv_user,
                'legendastv_password': self.legendastv_pass,
                'itasa_username': self.itasa_user,
                'itasa_password': self.itasa_pass,
                'opensubtitles_username': self.opensubtitles_user,
                'opensubtitles_password': self.opensubtitles_pass,
            },
            'FailedDownloads': {
                'delete_failed': int(self.delete_failed),
            },
            'FailedSnatches': {
                'use_failed_snatcher': int(self.use_failed_snatcher),
                'failed_snatch_age': int(self.failed_snatch_age),
            },
            'ANIDB': {
                'use_anidb': int(self.use_anidb),
                'anidb_username': self.anidb_username,
                'anidb_password': self.anidb_password,
                'anidb_use_mylist': int(self.anidb_use_mylist),
            },
            'ANIME': {
                'anime_split_home': int(self.anime_split_home),
            },
            'Quality': {
                'sizes': repr(self.quality_sizes),
            },
            'Providers': dict({
                'providers_order': sickrage.app.search_providers.provider_order,
                'custom_providers': self.custom_providers,
            }, **{providerID: dict([(x, int(getattr(providerObj, x)) if isinstance(getattr(providerObj, x),
                                                                                   bool) else getattr(providerObj, x))
                                    for x in provider_keys if hasattr(providerObj, x)]) for providerID, providerObj in
                  sickrage.app.search_providers.all().items()}),
            'MetadataProviders': {metadataProviderID: metadataProviderObj.config for
                                  metadataProviderID, metadataProviderObj in sickrage.app.metadata_providers.items()}
        }


    ################################################################################
    # check_setting_int                                                            #
    ################################################################################
    def check_setting_int(self, section, key, def_val=None, silent=True):
        def_val = def_val if def_val is not None else self.defaults[section][key]

        try:
            my_val = self.config_obj.get(section).as_int(key) or def_val
        except Exception:
            my_val = def_val

        if str(my_val).lower() == "true":
            my_val = 1
        elif str(my_val).lower() == "false":
            my_val = 0

        if not silent:
            sickrage.app.log.debug(key + " -> " + str(my_val))

        return my_val

    ################################################################################
    # check_setting_float                                                          #
    ################################################################################
    def check_setting_float(self, section, key, def_val=None, silent=True):
        def_val = def_val if def_val is not None else self.defaults[section][key]

        try:
            my_val = self.config_obj.get(section).as_float(key) or def_val
        except Exception:
            my_val = def_val

        if not silent:
            sickrage.app.log.debug(section + " -> " + str(my_val))

        return my_val

    ################################################################################
    # check_setting_str                                                            #
    ################################################################################
    def check_setting_str(self, section, key, def_val=None, silent=True, censor=False):
        def_val = def_val if def_val is not None else self.defaults[section][key]

        try:
            my_val = self.config_obj.get(section).get(key) or def_val
        except Exception:
            my_val = def_val

        if censor or (section, key) in sickrage.app.log.CENSORED_ITEMS:
            sickrage.app.log.CENSORED_ITEMS[section, key] = my_val

        if not silent:
            sickrage.app.log.debug(key + " -> " + my_val)

        return my_val

    ################################################################################
    # check_setting_list                                                           #
    ################################################################################
    def check_setting_list(self, section, key, def_val=None, silent=True):
        def_val = def_val if def_val is not None else self.defaults[section][key]

        try:
            my_val = list(self.config_obj.get(section).get(key)) or def_val
        except Exception:
            my_val = def_val

        if not silent:
            print(key + " -> " + repr(my_val))

        return my_val

    ################################################################################
    # check_setting_dict                                                            #
    ################################################################################
    def check_setting_dict(self, section, key, def_val=None, silent=True):
        def_val = def_val if def_val is not None else self.defaults[section][key]

        try:
            my_val = dict(literal_eval(self.config_obj.get(section).get(key))) or def_val
        except Exception:
            my_val = def_val

        if not silent:
            print(key + " -> " + repr(my_val))

        return my_val

    ################################################################################
    # check_setting_bool                                                           #
    ################################################################################
    def check_setting_bool(self, section, key, def_val=None, silent=True):
        def_val = def_val if def_val is not None else self.defaults[section][key]

        try:
            my_val = self.config_obj.get(section).as_bool(key)
        except Exception:
            my_val = def_val

        if not silent:
            print(key + " -> " + my_val)

        return my_val

    def load(self, config_file=None, defaults=False):
        sickrage.app.log.info("Loading encrypted config from disk")

        if not config_file:
            config_file = sickrage.app.config_file

        if not os.path.isabs(config_file):
            config_file = os.path.abspath(os.path.join(sickrage.app.data_dir, config_file))

        if not os.access(config_file, os.W_OK):
            if os.path.isfile(config_file):
                sickrage.app.log.warning("Config file '{}' must be writeable.".format(config_file))
                raise SystemExit
            elif not os.access(os.path.dirname(config_file), os.W_OK):
                sickrage.app.log.warning("Config file root dir '{}' must be writeable.".format(os.path.dirname(config_file)))
                raise SystemExit

        # decrypt config
        self.config_obj = ConfigObj(encoding='utf8')
        if os.path.exists(config_file):
            try:
                self.config_obj = decrypt_config(config_file)
            except Exception:
                sickrage.app.log.warning("Unable to decrypt config file {}, config is most likely corrupted and needs to be deleted.".format(config_file))
                raise SystemExit

        # use defaults
        if defaults:
            self.config_obj.clear()

        # migrate config
        self.config_obj = OldConfigMigrator(self.config_obj).migrate_config(
            current_version=self.check_setting_int('General', 'config_version'),
            expected_version=self.config_version
        )

        # GENERAL SETTINGS
        self.sub_id = self.check_setting_str('General', 'sub_id')
        self.server_id = self.check_setting_str('General', 'server_id')
        self.config_version = self.check_setting_int('General', 'config_version')
        self.enable_sickrage_api = self.check_setting_bool('General', 'enable_sickrage_api')
        self.debug = sickrage.app.debug or self.check_setting_bool('General', 'debug')
        self.last_db_compact = self.check_setting_int('General', 'last_db_compact')
        self.log_nr = self.check_setting_int('General', 'log_nr')
        self.log_size = self.check_setting_int('General', 'log_size')
        self.socket_timeout = self.check_setting_int('General', 'socket_timeout')
        self.default_page = self.check_setting_str('General', 'default_page')
        self.pip3_path = self.check_setting_str('General', 'pip3_path')
        self.git_path = self.check_setting_str('General', 'git_path')
        self.git_autoissues = self.check_setting_bool('General', 'git_autoissues')
        self.git_username = self.check_setting_str('General', 'git_username', censor=True)
        self.git_password = self.check_setting_str('General', 'git_password', censor=True)
        self.git_newver = self.check_setting_bool('General', 'git_newver')
        self.git_reset = self.check_setting_bool('General', 'git_reset')
        self.web_port = sickrage.app.web_port or self.check_setting_int('General', 'web_port')
        self.web_host = sickrage.app.web_host or self.check_setting_str('General', 'web_host')
        self.web_username = self.check_setting_str('General', 'web_username')
        self.web_password = self.check_setting_str('General', 'web_password', censor=True)
        self.web_external_port = self.check_setting_int('General', 'web_external_port')
        self.web_ipv6 = self.check_setting_bool('General', 'web_ipv6')
        self.web_root = sickrage.app.web_root or self.check_setting_str('General', 'web_root').lstrip('/').rstrip('/')
        self.web_log = self.check_setting_bool('General', 'web_log')
        self.web_cookie_secret = self.check_setting_str('General', 'web_cookie_secret')
        self.web_use_gzip = self.check_setting_bool('General', 'web_use_gzip')
        self.ssl_verify = self.check_setting_bool('General', 'ssl_verify')
        self.launch_browser = self.check_setting_bool('General', 'launch_browser')
        self.series_provider_default_language = self.check_setting_str('General', 'indexer_default_lang')
        self.ep_default_deleted_status = self.check_setting_int('General', 'ep_default_deleted_status')
        self.download_url = self.check_setting_str('General', 'download_url')
        self.cpu_preset = self.check_setting_str('General', 'cpu_preset')
        self.max_queue_workers = self.check_setting_int('General', 'max_queue_workers')
        self.anon_redirect = self.check_setting_str('General', 'anon_redirect')
        self.proxy_setting = self.check_setting_str('General', 'proxy_setting')
        self.proxy_series_providers = self.check_setting_bool('General', 'proxy_series_providers')
        self.trash_remove_show = self.check_setting_bool('General', 'trash_remove_show')
        self.trash_rotate_logs = self.check_setting_bool('General', 'trash_rotate_logs')
        self.sort_article = self.check_setting_bool('General', 'sort_article')
        self.api_key = self.check_setting_str('General', 'api_key', censor=True)
        self.sso_auth_enabled = self.check_setting_bool('General', 'sso_auth_enabled')
        self.local_auth_enabled = self.check_setting_bool('General', 'local_auth_enabled')
        self.ip_whitelist_enabled = self.check_setting_bool('General', 'ip_whitelist_enabled')
        self.ip_whitelist_localhost_enabled = self.check_setting_bool('General', 'ip_whitelist_localhost_enabled')
        self.ip_whitelist = self.check_setting_str('General', 'ip_whitelist')
        self.enable_https = self.check_setting_bool('General', 'enable_https')
        self.https_cert = self.check_setting_str('General', 'https_cert')
        self.https_key = self.check_setting_str('General', 'https_key')
        self.handle_reverse_proxy = self.check_setting_bool('General', 'handle_reverse_proxy')
        self.root_dirs = self.check_setting_str('General', 'root_dirs')
        self.quality_default = self.check_setting_int('General', 'quality_default')
        self.status_default = self.check_setting_int('General', 'status_default')
        self.status_default_after = self.check_setting_int('General', 'status_default_after')
        self.enable_upnp = self.check_setting_bool('General', 'enable_upnp')
        self.version_notify = self.check_setting_bool('General', 'version_notify')
        self.auto_update = self.check_setting_bool('General', 'auto_update')
        self.notify_on_update = self.check_setting_bool('General', 'notify_on_update')
        self.backup_on_update = self.check_setting_bool('General', 'backup_on_update')
        self.notify_on_login = self.check_setting_bool('General', 'notify_on_login')
        self.flatten_folders_default = self.check_setting_bool('General', 'flatten_folders_default')
        self.series_provider_default = self.check_setting_int('General', 'series_provider_default')
        self.series_provider_timeout = self.check_setting_int('General', 'series_provider_timeout')
        self.anime_default = self.check_setting_bool('General', 'anime_default')
        self.search_format_default = self.check_setting_int('General', 'search_format_default')
        self.scene_default = self.check_setting_bool('General', 'scene_default')
        self.skip_downloaded_default = self.check_setting_bool('General', 'skip_downloaded_default')
        self.add_show_year_default = self.check_setting_bool('General', 'add_show_year_default')
        self.naming_pattern = self.check_setting_str('General', 'naming_pattern')
        self.naming_abd_pattern = self.check_setting_str('General', 'naming_abd_pattern')
        self.naming_custom_abd = self.check_setting_bool('General', 'naming_custom_abd')
        self.naming_sports_pattern = self.check_setting_str('General', 'naming_sports_pattern')
        self.naming_anime_pattern = self.check_setting_str('General', 'naming_anime_pattern')
        self.naming_anime = self.check_setting_int('General', 'naming_anime')
        self.naming_custom_sports = self.check_setting_bool('General', 'naming_custom_sports')
        self.naming_custom_anime = self.check_setting_bool('General', 'naming_custom_anime')
        self.naming_multi_ep = self.check_setting_int('General', 'naming_multi_ep')
        self.naming_anime_multi_ep = self.check_setting_int('General', 'naming_anime_multi_ep')
        self.naming_strip_year = self.check_setting_bool('General', 'naming_strip_year')
        self.use_nzbs = self.check_setting_bool('General', 'use_nzbs')
        self.use_torrents = self.check_setting_bool('General', 'use_torrents')
        self.nzb_method = self.check_setting_str('General', 'nzb_method')
        self.torrent_method = self.check_setting_str('General', 'torrent_method')
        self.download_propers = self.check_setting_bool('General', 'download_propers')
        self.enable_rss_cache = self.check_setting_bool('General', 'enable_rss_cache')
        self.torrent_file_to_magnet = self.check_setting_bool('General', 'torrent_file_to_magnet')
        self.torrent_magnet_to_file = self.check_setting_bool('General', 'torrent_magnet_to_file')
        self.download_unverified_magnet_link = self.check_setting_bool('General', 'download_unverified_magnet_link')
        self.proper_searcher_interval = self.check_setting_str('General', 'check_propers_interval')
        self.randomize_providers = self.check_setting_bool('General', 'randomize_providers')
        self.allow_high_priority = self.check_setting_bool('General', 'allow_high_priority')
        self.skip_removed_files = self.check_setting_bool('General', 'skip_removed_files')
        self.usenet_retention = self.check_setting_int('General', 'usenet_retention')
        self.daily_searcher_freq = self.check_setting_int('General', 'dailysearch_frequency')
        self.backlog_searcher_freq = self.check_setting_int('General', 'backlog_frequency')
        self.version_updater_freq = self.check_setting_int('General', 'update_frequency')
        self.show_update_stale = self.check_setting_bool('General', 'show_update_stale')
        self.show_update_hour = self.check_setting_int('General', 'show_update_hour')
        self.backlog_days = self.check_setting_int('General', 'backlog_days')
        self.auto_postprocessor_freq = self.check_setting_int('General', 'auto_postprocessor_frequency')
        self.tv_download_dir = self.check_setting_str('General', 'tv_download_dir')
        self.process_automatically = self.check_setting_bool('General', 'process_automatically')
        self.no_delete = self.check_setting_bool('General', 'no_delete')
        self.unpack = self.check_setting_bool('General', 'unpack')
        self.unpack_dir = self.check_setting_str('General', 'unpack_dir')
        self.rename_episodes = self.check_setting_bool('General', 'rename_episodes')
        self.airdate_episodes = self.check_setting_bool('General', 'airdate_episodes')
        self.file_timestamp_timezone = self.check_setting_str('General', 'file_timestamp_timezone')
        self.keep_processed_dir = self.check_setting_bool('General', 'keep_processed_dir')
        self.process_method = self.check_setting_str('General', 'process_method')
        self.processor_follow_symlinks = self.check_setting_bool('General', 'processor_follow_symlinks')
        self.del_rar_contents = self.check_setting_bool('General', 'del_rar_contents')
        self.delete_non_associated_files = self.check_setting_bool('General', 'delete_non_associated_files')
        self.move_associated_files = self.check_setting_bool('General', 'move_associated_files')
        self.postpone_if_sync_files = self.check_setting_bool('General', 'postpone_if_sync_files')
        self.sync_files = self.check_setting_str('General', 'sync_files')
        self.nfo_rename = self.check_setting_bool('General', 'nfo_rename')
        self.create_missing_show_dirs = self.check_setting_bool('General', 'create_missing_show_dirs')
        self.add_shows_wo_dir = self.check_setting_bool('General', 'add_shows_wo_dir')
        self.require_words = self.check_setting_str('General', 'require_words')
        self.ignore_words = self.check_setting_str('General', 'ignore_words')
        self.ignored_subs_list = self.check_setting_str('General', 'ignored_subs_list')
        self.calendar_unprotected = self.check_setting_bool('General', 'calendar_unprotected')
        self.calendar_icons = self.check_setting_bool('General', 'calendar_icons')
        self.no_restart = self.check_setting_bool('General', 'no_restart')
        self.allowed_video_file_exts = self.check_setting_list('General', 'allowed_video_file_exts')
        self.extra_scripts = [x.strip() for x in self.check_setting_str('General', 'extra_scripts').split('|') if x.strip()]
        self.use_listview = self.check_setting_bool('General', 'use_listview')
        self.display_all_seasons = self.check_setting_bool('General', 'display_all_seasons')
        self.random_user_agent = self.check_setting_bool('General', 'random_user_agent')
        self.allowed_extensions = self.check_setting_str('General', 'allowed_extensions')
        self.view_changelog = self.check_setting_bool('General', 'view_changelog')
        self.strip_special_file_bits = self.check_setting_bool('General', 'strip_special_file_bits')

        # GUI SETTINGS
        self.gui_lang = self.check_setting_str('GUI', 'gui_lang')
        self.theme_name = self.check_setting_str('GUI', 'theme_name')
        self.fanart_background = self.check_setting_bool('GUI', 'fanart_background')
        self.fanart_background_opacity = self.check_setting_float('GUI', 'fanart_background_opacity')
        self.home_layout = self.check_setting_str('GUI', 'home_layout')
        self.history_layout = self.check_setting_str('GUI', 'history_layout')
        self.history_limit = self.check_setting_str('GUI', 'history_limit')
        self.display_show_specials = self.check_setting_bool('GUI', 'display_show_specials')
        self.coming_eps_layout = self.check_setting_str('GUI', 'coming_eps_layout')
        self.coming_eps_display_paused = self.check_setting_bool('GUI', 'coming_eps_display_paused')
        self.coming_eps_sort = self.check_setting_str('GUI', 'coming_eps_sort')
        self.coming_eps_missed_range = self.check_setting_int('GUI', 'coming_eps_missed_range')
        self.fuzzy_dating = self.check_setting_bool('GUI', 'fuzzy_dating')
        self.trim_zero = self.check_setting_bool('GUI', 'trim_zero')
        self.date_preset = self.check_setting_str('GUI', 'date_preset')
        self.time_preset_w_seconds = self.check_setting_str('GUI', 'time_preset')
        self.time_preset = self.time_preset_w_seconds.replace(":%S", "")
        self.timezone_display = self.check_setting_str('GUI', 'timezone_display')
        self.poster_sort_by = self.check_setting_str('GUI', 'poster_sort_by')
        self.poster_sort_dir = self.check_setting_int('GUI', 'poster_sort_dir')
        self.filter_row = self.check_setting_bool('GUI', 'filter_row')

        # BLACKHOLE SETTINGS
        self.nzb_dir = self.check_setting_str('Blackhole', 'nzb_dir')
        self.torrent_dir = self.check_setting_str('Blackhole', 'torrent_dir')

        # SABNZBD SETTINGS
        self.sab_username = self.check_setting_str('SABnzbd', 'sab_username', censor=True)
        self.sab_password = self.check_setting_str('SABnzbd', 'sab_password', censor=True)
        self.sab_apikey = self.check_setting_str('SABnzbd', 'sab_apikey', censor=True)
        self.sab_category = self.check_setting_str('SABnzbd', 'sab_category')
        self.sab_category_backlog = self.check_setting_str('SABnzbd', 'sab_category_backlog')
        self.sab_category_anime = self.check_setting_str('SABnzbd', 'sab_category_anime')
        self.sab_category_anime_backlog = self.check_setting_str('SABnzbd', 'sab_category_anime_backlog')
        self.sab_host = self.check_setting_str('SABnzbd', 'sab_host')
        self.sab_forced = self.check_setting_bool('SABnzbd', 'sab_forced')

        # NZBGET SETTINGS
        self.nzbget_username = self.check_setting_str('NZBget', 'nzbget_username', censor=True)
        self.nzbget_password = self.check_setting_str('NZBget', 'nzbget_password', censor=True)
        self.nzbget_category = self.check_setting_str('NZBget', 'nzbget_category')
        self.nzbget_category_backlog = self.check_setting_str('NZBget', 'nzbget_category_backlog')
        self.nzbget_category_anime = self.check_setting_str('NZBget', 'nzbget_category_anime')
        self.nzbget_category_anime_backlog = self.check_setting_str('NZBget', 'nzbget_category_anime_backlog')
        self.nzbget_host = self.check_setting_str('NZBget', 'nzbget_host')
        self.nzbget_use_https = self.check_setting_bool('NZBget', 'nzbget_use_https')
        self.nzbget_priority = self.check_setting_int('NZBget', 'nzbget_priority')

        # SYNOLOGY DSM SETTINGS
        self.syno_dsm_host = self.check_setting_str('SynologyDSM', 'syno_dsm_host')
        self.syno_dsm_username = self.check_setting_str('SynologyDSM', 'syno_dsm_username', censor=True)
        self.syno_dsm_password = self.check_setting_str('SynologyDSM', 'syno_dsm_password', censor=True)
        self.syno_dsm_path = self.check_setting_str('SynologyDSM', 'syno_dsm_path')

        # TORRENT SETTINGS
        self.torrent_username = self.check_setting_str('TORRENT', 'torrent_username', censor=True)
        self.torrent_password = self.check_setting_str('TORRENT', 'torrent_password', censor=True)
        self.torrent_host = self.check_setting_str('TORRENT', 'torrent_host')
        self.torrent_path = self.check_setting_str('TORRENT', 'torrent_path')
        self.torrent_seed_time = self.check_setting_int('TORRENT', 'torrent_seed_time')
        self.torrent_paused = self.check_setting_bool('TORRENT', 'torrent_paused')
        self.torrent_high_bandwidth = self.check_setting_bool('TORRENT', 'torrent_high_bandwidth')
        self.torrent_label = self.check_setting_str('TORRENT', 'torrent_label')
        self.torrent_label_anime = self.check_setting_str('TORRENT', 'torrent_label_anime')
        self.torrent_verify_cert = self.check_setting_bool('TORRENT', 'torrent_verify_cert')
        self.torrent_rpc_url = self.check_setting_str('TORRENT', 'torrent_rpc_url')
        self.torrent_auth_type = self.check_setting_str('TORRENT', 'torrent_auth_type')

        # KODI SETTINGS
        self.use_kodi = self.check_setting_bool('KODI', 'use_kodi')
        self.kodi_always_on = self.check_setting_bool('KODI', 'kodi_always_on')
        self.kodi_notify_on_snatch = self.check_setting_bool('KODI', 'kodi_notify_on_snatch')
        self.kodi_notify_on_download = self.check_setting_bool('KODI', 'kodi_notify_on_download')
        self.kodi_notify_on_subtitle_download = self.check_setting_bool('KODI', 'kodi_notify_on_subtitle_download')
        self.kodi_update_library = self.check_setting_bool('KODI', 'kodi_update_library')
        self.kodi_update_full = self.check_setting_bool('KODI', 'kodi_update_full')
        self.kodi_update_only_first = self.check_setting_bool('KODI', 'kodi_update_only_first')
        self.kodi_host = self.check_setting_str('KODI', 'kodi_host')
        self.kodi_username = self.check_setting_str('KODI', 'kodi_username', censor=True)
        self.kodi_password = self.check_setting_str('KODI', 'kodi_password', censor=True)

        # PLEX SETTINGS
        self.use_plex = self.check_setting_bool('Plex', 'use_plex')
        self.plex_notify_on_snatch = self.check_setting_bool('Plex', 'plex_notify_on_snatch')
        self.plex_notify_on_download = self.check_setting_bool('Plex', 'plex_notify_on_download')
        self.plex_notify_on_subtitle_download = self.check_setting_bool('Plex', 'plex_notify_on_subtitle_download')
        self.plex_update_library = self.check_setting_bool('Plex', 'plex_update_library')
        self.plex_server_host = self.check_setting_str('Plex', 'plex_server_host')
        self.plex_server_token = self.check_setting_str('Plex', 'plex_server_token', censor=True)
        self.plex_host = self.check_setting_str('Plex', 'plex_host')
        self.plex_username = self.check_setting_str('Plex', 'plex_username', censor=True)
        self.plex_password = self.check_setting_str('Plex', 'plex_password', censor=True)
        self.use_plex_client = self.check_setting_bool('Plex', 'use_plex_client')
        self.plex_client_username = self.check_setting_str('Plex', 'plex_client_username', censor=True)
        self.plex_client_password = self.check_setting_str('Plex', 'plex_client_password', censor=True)

        # EMBY SETTINGS
        self.use_emby = self.check_setting_bool('Emby', 'use_emby')
        self.emby_notify_on_snatch = self.check_setting_bool('Emby', 'emby_notify_on_snatch')
        self.emby_notify_on_download = self.check_setting_bool('Emby', 'emby_notify_on_download')
        self.emby_notify_on_subtitle_download = self.check_setting_bool('Emby', 'emby_notify_on_subtitle_download')
        self.emby_host = self.check_setting_str('Emby', 'emby_host')
        self.emby_apikey = self.check_setting_str('Emby', 'emby_apikey', censor=True)

        # GROWL SETTINGS
        self.use_growl = self.check_setting_bool('Growl', 'use_growl')
        self.growl_notify_on_snatch = self.check_setting_bool('Growl', 'growl_notify_on_snatch')
        self.growl_notify_on_download = self.check_setting_bool('Growl', 'growl_notify_on_download')
        self.growl_notify_on_subtitle_download = self.check_setting_bool('Growl', 'growl_notify_on_subtitle_download')
        self.growl_host = self.check_setting_str('Growl', 'growl_host')
        self.growl_password = self.check_setting_str('Growl', 'growl_password', censor=True)

        # FREEMOBILE SETTINGS
        self.use_freemobile = self.check_setting_bool('FreeMobile', 'use_freemobile')
        self.freemobile_notify_on_snatch = self.check_setting_bool('FreeMobile', 'freemobile_notify_on_snatch')
        self.freemobile_notify_on_download = self.check_setting_bool('FreeMobile', 'freemobile_notify_on_download')
        self.freemobile_notify_on_subtitle_download = self.check_setting_bool('FreeMobile',
                                                                            'freemobile_notify_on_subtitle_download')
        self.freemobile_id = self.check_setting_str('FreeMobile', 'freemobile_id')
        self.freemobile_apikey = self.check_setting_str('FreeMobile', 'freemobile_apikey', censor=True)

        # TELEGRAM SETTINGS
        self.use_telegram = self.check_setting_bool('TELEGRAM', 'use_telegram')
        self.telegram_notify_on_snatch = self.check_setting_bool('TELEGRAM', 'telegram_notify_on_snatch')
        self.telegram_notify_on_download = self.check_setting_bool('TELEGRAM', 'telegram_notify_on_download')
        self.telegram_notify_on_subtitle_download = self.check_setting_bool('TELEGRAM',
                                                                          'telegram_notify_on_subtitle_download')
        self.telegram_id = self.check_setting_str('TELEGRAM', 'telegram_id')
        self.telegram_apikey = self.check_setting_str('TELEGRAM', 'telegram_apikey', censor=True)

        # JOIN SETTINGS
        self.use_join = self.check_setting_bool('JOIN', 'use_join')
        self.join_notify_on_snatch = self.check_setting_bool('JOIN', 'join_notify_on_snatch')
        self.join_notify_on_download = self.check_setting_bool('JOIN', 'join_notify_on_download')
        self.join_notify_on_subtitle_download = self.check_setting_bool('JOIN',
                                                                      'join_notify_on_subtitle_download')
        self.join_id = self.check_setting_str('JOIN', 'join_id')
        self.join_apikey = self.check_setting_str('JOIN', 'join_apikey', censor=True)

        # PROWL SETTINGS
        self.use_prowl = self.check_setting_bool('Prowl', 'use_prowl')
        self.prowl_notify_on_snatch = self.check_setting_bool('Prowl', 'prowl_notify_on_snatch')
        self.prowl_notify_on_download = self.check_setting_bool('Prowl', 'prowl_notify_on_download')
        self.prowl_notify_on_subtitle_download = self.check_setting_bool('Prowl', 'prowl_notify_on_subtitle_download')
        self.prowl_apikey = self.check_setting_str('Prowl', 'prowl_apikey', censor=True)
        self.prowl_priority = self.check_setting_str('Prowl', 'prowl_priority')

        # TWITTER SETTINGS
        self.use_twitter = self.check_setting_bool('Twitter', 'use_twitter')
        self.twitter_notify_on_snatch = self.check_setting_bool('Twitter', 'twitter_notify_on_snatch')
        self.twitter_notify_on_download = self.check_setting_bool('Twitter', 'twitter_notify_on_download')
        self.twitter_notify_on_subtitle_download = self.check_setting_bool('Twitter', 'twitter_notify_on_subtitle_download')
        self.twitter_username = self.check_setting_str('Twitter', 'twitter_username', censor=True)
        self.twitter_password = self.check_setting_str('Twitter', 'twitter_password', censor=True)
        self.twitter_prefix = self.check_setting_str('Twitter', 'twitter_prefix', 'SiCKRAGE')
        self.twitter_dmto = self.check_setting_str('Twitter', 'twitter_dmto')
        self.twitter_usedm = self.check_setting_bool('Twitter', 'twitter_usedm')

        self.use_twilio = self.check_setting_bool('Twilio', 'use_twilio')
        self.twilio_notify_on_snatch = self.check_setting_bool('Twilio', 'twilio_notify_on_snatch')
        self.twilio_notify_on_download = self.check_setting_bool('Twilio', 'twilio_notify_on_download')
        self.twilio_notify_on_subtitle_download = self.check_setting_bool('Twilio', 'twilio_notify_on_subtitle_download')
        self.twilio_phone_sid = self.check_setting_str('Twilio', 'twilio_phone_sid', censor=True)
        self.twilio_account_sid = self.check_setting_str('Twilio', 'twilio_account_sid', censor=True)
        self.twilio_auth_token = self.check_setting_str('Twilio', 'twilio_auth_token', censor=True)
        self.twilio_to_number = self.check_setting_str('Twilio', 'twilio_to_number', censor=True)

        self.use_boxcar2 = self.check_setting_bool('Boxcar2', 'use_boxcar2')
        self.boxcar2_notify_on_snatch = self.check_setting_bool('Boxcar2', 'boxcar2_notify_on_snatch')
        self.boxcar2_notify_on_download = self.check_setting_bool('Boxcar2', 'boxcar2_notify_on_download')
        self.boxcar2_notify_on_subtitle_download = self.check_setting_bool('Boxcar2', 'boxcar2_notify_on_subtitle_download')
        self.boxcar2_accesstoken = self.check_setting_str('Boxcar2', 'boxcar2_accesstoken', censor=True)

        self.use_pushover = self.check_setting_bool('Pushover', 'use_pushover')
        self.pushover_notify_on_snatch = self.check_setting_bool('Pushover', 'pushover_notify_on_snatch')
        self.pushover_notify_on_download = self.check_setting_bool('Pushover', 'pushover_notify_on_download')
        self.pushover_notify_on_subtitle_download = self.check_setting_bool('Pushover',
                                                                          'pushover_notify_on_subtitle_download')
        self.pushover_userkey = self.check_setting_str('Pushover', 'pushover_userkey', censor=True)
        self.pushover_apikey = self.check_setting_str('Pushover', 'pushover_apikey', censor=True)
        self.pushover_device = self.check_setting_str('Pushover', 'pushover_device')
        self.pushover_sound = self.check_setting_str('Pushover', 'pushover_sound', 'pushover')

        self.use_libnotify = self.check_setting_bool('Libnotify', 'use_libnotify')
        self.libnotify_notify_on_snatch = self.check_setting_bool('Libnotify', 'libnotify_notify_on_snatch')
        self.libnotify_notify_on_download = self.check_setting_bool('Libnotify', 'libnotify_notify_on_download')
        self.libnotify_notify_on_subtitle_download = self.check_setting_bool('Libnotify',
                                                                           'libnotify_notify_on_subtitle_download')

        self.use_nmj = self.check_setting_bool('NMJ', 'use_nmj')
        self.nmj_host = self.check_setting_str('NMJ', 'nmj_host')
        self.nmj_database = self.check_setting_str('NMJ', 'nmj_database')
        self.nmj_mount = self.check_setting_str('NMJ', 'nmj_mount')

        self.use_nmjv2 = self.check_setting_bool('NMJv2', 'use_nmjv2')
        self.nmjv2_host = self.check_setting_str('NMJv2', 'nmjv2_host')
        self.nmjv2_database = self.check_setting_str('NMJv2', 'nmjv2_database')
        self.nmjv2_dbloc = self.check_setting_str('NMJv2', 'nmjv2_dbloc')

        self.use_synoindex = self.check_setting_bool('Synology', 'use_synoindex')

        self.use_synologynotifier = self.check_setting_bool('SynologyNotifier', 'use_synologynotifier')
        self.synologynotifier_notify_on_snatch = self.check_setting_bool('SynologyNotifier',
                                                                        'synologynotifier_notify_on_snatch')
        self.synologynotifier_notify_on_download = self.check_setting_bool('SynologyNotifier',
                                                                          'synologynotifier_notify_on_download')
        self.synologynotifier_notify_on_subtitle_download = self.check_setting_bool('SynologyNotifier',
                                                                                  'synologynotifier_notify_on_subtitle_download')

        self.thetvdb_ap_itoken = self.check_setting_str('theTVDB', 'thetvdb_ap_itoken', censor=True)

        self.use_slack = self.check_setting_bool('Slack', 'use_slack')
        self.slack_notify_on_snatch = self.check_setting_bool('Slack', 'slack_notify_on_snatch')
        self.slack_notify_on_download = self.check_setting_bool('Slack', 'slack_notify_on_download')
        self.slack_notify_on_subtitle_download = self.check_setting_bool('Slack', 'slack_notify_on_subtitle_download')
        self.slack_webhook = self.check_setting_str('Slack', 'slack_webhook')

        self.use_discord = self.check_setting_bool('Discord', 'use_discord')
        self.discord_notify_on_snatch = self.check_setting_bool('Discord', 'discord_notify_on_snatch')
        self.discord_notify_on_download = self.check_setting_bool('Discord', 'discord_notify_on_download')
        self.discord_notify_on_subtitle_download = self.check_setting_bool('Discord', 'discord_notify_on_subtitle_download')
        self.discord_webhook = self.check_setting_str('Discord', 'discord_webhook')
        self.discord_avatar_url = self.check_setting_str('Discord', 'discord_avatar_url')
        self.discord_name = self.check_setting_str('Discord', 'discord_name')
        self.discord_tts = self.check_setting_bool('Discord', 'discord_tts')

        self.use_trakt = self.check_setting_bool('Trakt', 'use_trakt')
        self.trakt_username = self.check_setting_str('Trakt', 'trakt_username', censor=True)
        self.trakt_oauth_token = self.check_setting_dict('Trakt', 'trakt_oauth_token')
        self.trakt_remove_watchlist = self.check_setting_bool('Trakt', 'trakt_remove_watchlist')
        self.trakt_remove_serieslist = self.check_setting_bool('Trakt', 'trakt_remove_serieslist')
        self.trakt_remove_show_from_sickrage = self.check_setting_bool('Trakt', 'trakt_remove_show_from_sickrage')
        self.trakt_sync_watchlist = self.check_setting_bool('Trakt', 'trakt_sync_watchlist')
        self.trakt_method_add = self.check_setting_int('Trakt', 'trakt_method_add')
        self.trakt_start_paused = self.check_setting_bool('Trakt', 'trakt_start_paused')
        self.trakt_use_recommended = self.check_setting_bool('Trakt', 'trakt_use_recommended')
        self.trakt_sync = self.check_setting_bool('Trakt', 'trakt_sync')
        self.trakt_sync_remove = self.check_setting_bool('Trakt', 'trakt_sync_remove')
        self.trakt_default_indexer = self.check_setting_int('Trakt', 'trakt_default_indexer')
        self.trakt_timeout = self.check_setting_int('Trakt', 'trakt_timeout')
        self.trakt_blacklist_name = self.check_setting_str('Trakt', 'trakt_blacklist_name')

        self.use_pytivo = self.check_setting_bool('pyTivo', 'use_pytivo')
        self.pytivo_notify_on_snatch = self.check_setting_bool('pyTivo', 'pytivo_notify_on_snatch')
        self.pytivo_notify_on_download = self.check_setting_bool('pyTivo', 'pytivo_notify_on_download')
        self.pytivo_notify_on_subtitle_download = self.check_setting_bool('pyTivo', 'pytivo_notify_on_subtitle_download')
        self.pytivo_update_library = self.check_setting_bool('pyTivo', 'pyTivo_update_library')
        self.pytivo_host = self.check_setting_str('pyTivo', 'pytivo_host')
        self.pytivo_share_name = self.check_setting_str('pyTivo', 'pytivo_share_name')
        self.pytivo_tivo_name = self.check_setting_str('pyTivo', 'pytivo_tivo_name')

        self.use_nma = self.check_setting_bool('NMA', 'use_nma')
        self.nma_notify_on_snatch = self.check_setting_bool('NMA', 'nma_notify_on_snatch')
        self.nma_notify_on_download = self.check_setting_bool('NMA', 'nma_notify_on_download')
        self.nma_notify_on_subtitle_download = self.check_setting_bool('NMA', 'nma_notify_on_subtitle_download')
        self.nma_api = self.check_setting_str('NMA', 'nma_api', censor=True)
        self.nma_priority = self.check_setting_str('NMA', 'nma_priority')

        self.use_pushalot = self.check_setting_bool('Pushalot', 'use_pushalot')
        self.pushalot_notify_on_snatch = self.check_setting_bool('Pushalot', 'pushalot_notify_on_snatch')
        self.pushalot_notify_on_download = self.check_setting_bool('Pushalot', 'pushalot_notify_on_download')
        self.pushalot_notify_on_subtitle_download = self.check_setting_bool('Pushalot',
                                                                          'pushalot_notify_on_subtitle_download')
        self.pushalot_authorizationtoken = self.check_setting_str('Pushalot', 'pushalot_authorizationtoken',
                                                                  censor=True)

        self.use_pushbullet = self.check_setting_bool('Pushbullet', 'use_pushbullet')
        self.pushbullet_notify_on_snatch = self.check_setting_bool('Pushbullet', 'pushbullet_notify_on_snatch')
        self.pushbullet_notify_on_download = self.check_setting_bool('Pushbullet', 'pushbullet_notify_on_download')
        self.pushbullet_notify_on_subtitle_download = self.check_setting_bool('Pushbullet',
                                                                            'pushbullet_notify_on_subtitle_download')
        self.pushbullet_api = self.check_setting_str('Pushbullet', 'pushbullet_api', censor=True)
        self.pushbullet_device = self.check_setting_str('Pushbullet', 'pushbullet_device')

        self.use_email = self.check_setting_bool('Email', 'use_email')
        self.email_notify_on_snatch = self.check_setting_bool('Email', 'email_notify_on_snatch')
        self.email_notify_on_download = self.check_setting_bool('Email', 'email_notify_on_download')
        self.email_notify_on_subtitle_download = self.check_setting_bool('Email', 'email_notify_on_subtitle_download')
        self.email_host = self.check_setting_str('Email', 'email_host')
        self.email_port = self.check_setting_int('Email', 'email_port')
        self.email_tls = self.check_setting_bool('Email', 'email_tls')
        self.email_user = self.check_setting_str('Email', 'email_user', censor=True)
        self.email_password = self.check_setting_str('Email', 'email_password', censor=True)
        self.email_from = self.check_setting_str('Email', 'email_from')
        self.email_list = self.check_setting_str('Email', 'email_list')

        self.use_alexa = self.check_setting_bool('Alexa', 'use_alexa')
        self.alexa_notify_on_snatch = self.check_setting_bool('Alexa', 'alexa_notify_on_snatch')
        self.alexa_notify_on_download = self.check_setting_bool('Alexa', 'alexa_notify_on_download')
        self.alexa_notify_on_subtitle_download = self.check_setting_bool('Alexa', 'alexa_notify_on_subtitle_download')

        # SUBTITLE SETTINGS
        self.use_subtitles = self.check_setting_bool('Subtitles', 'use_subtitles')
        self.subtitles_languages = self.check_setting_list('Subtitles', 'subtitles_languages')
        self.subtitles_services_list = self.check_setting_list('Subtitles', 'subtitles_services_list')
        self.subtitles_dir = self.check_setting_str('Subtitles', 'subtitles_dir')
        self.subtitles_default = self.check_setting_bool('Subtitles', 'subtitles_default')
        self.subtitles_history = self.check_setting_bool('Subtitles', 'subtitles_history')
        self.subtitles_hearing_impaired = self.check_setting_bool('Subtitles', 'subtitles_hearing_impaired')
        self.enable_embedded_subtitles = self.check_setting_bool('Subtitles', 'enable_embedded_subtitles')
        self.subtitles_multi = self.check_setting_bool('Subtitles', 'subtitles_multi')
        self.subtitles_services_enabled = [int(x) for x in
                                           self.check_setting_str('Subtitles', 'subtitles_services_enabled').split('|')
                                           if x]
        self.subtitles_extra_scripts = [x.strip() for x in
                                        self.check_setting_str('Subtitles', 'subtitles_extra_scripts').split('|') if
                                        x.strip()]
        self.addic7ed_user = self.check_setting_str('Subtitles', 'addic7ed_username', censor=True)
        self.addic7ed_pass = self.check_setting_str('Subtitles', 'addic7ed_password', censor=True)
        self.legendastv_user = self.check_setting_str('Subtitles', 'legendastv_username', censor=True)
        self.legendastv_pass = self.check_setting_str('Subtitles', 'legendastv_password', censor=True)
        self.itasa_user = self.check_setting_str('Subtitles', 'itasa_username', censor=True)
        self.itasa_pass = self.check_setting_str('Subtitles', 'itasa_password', censor=True)
        self.opensubtitles_user = self.check_setting_str('Subtitles', 'opensubtitles_username', censor=True)
        self.opensubtitles_pass = self.check_setting_str('Subtitles', 'opensubtitles_password', censor=True)
        self.subtitle_searcher_freq = self.check_setting_int('Subtitles', 'subtitles_finder_frequency')

        # FAILED DOWNLOAD SETTINGS
        self.delete_failed = self.check_setting_bool('FailedDownloads', 'delete_failed')

        # FAILED SNATCH SETTINGS
        self.use_failed_snatcher = self.check_setting_bool('FailedSnatches', 'use_failed_snatcher')
        self.failed_snatch_age = self.check_setting_int('FailedSnatches', 'failed_snatch_age')

        # ANIDB SETTINGS
        self.use_anidb = self.check_setting_bool('ANIDB', 'use_anidb')
        self.anidb_username = self.check_setting_str('ANIDB', 'anidb_username', censor=True)
        self.anidb_password = self.check_setting_str('ANIDB', 'anidb_password', censor=True)
        self.anidb_use_mylist = self.check_setting_bool('ANIDB', 'anidb_use_mylist')
        self.anime_split_home = self.check_setting_bool('ANIME', 'anime_split_home')

        self.quality_sizes = self.check_setting_dict('Quality', 'sizes')

        self.custom_providers = self.check_setting_str('Providers', 'custom_providers')

        # load providers
        sickrage.app.search_providers.load()

        # provider settings
        for providerID, providerObj in sickrage.app.search_providers.all().items():
            providerSettings = self.check_setting_str('Providers', providerID, '') or {}
            for k, v in providerSettings.items():
                providerSettings[k] = auto_type(v)

            [setattr(providerObj, x, providerSettings[x]) for x in
             set(providerObj.__dict__).intersection(providerSettings)]

        # order providers
        sickrage.app.search_providers.provider_order = self.check_setting_str('Providers', 'providers_order')

        for metadataProviderID, metadataProviderObj in sickrage.app.metadata_providers.items():
            metadataProviderObj.config = self.check_setting_str('MetadataProviders', metadataProviderID, '0|0|0|0|0|0|0|0|0|0|0')

        # mark config settings loaded
        self.loaded = True

        # save config settings
        self.save()

    def save(self):
        # dont bother saving settings if there not loaded
        if not self.loaded:
            return

        config_obj = ConfigObj(indent_type='  ', encoding='utf8')
        config_obj.clear()

        config_obj.update(self.config_data)

        # encrypt config
        return encrypt_config(config_obj)



    def to_json(self):
        return convert_dict_keys_to_camelcase(self.config_data)


class OldConfigMigrator(OldConfig):
    def __init__(self, config_obj):
        """
        Initializes a config migrator that can take the config from the version indicated in the config
        file up to the latest version
        """
        super(OldConfigMigrator, self).__init__()
        self.config_obj = config_obj

        self.migration_names = {
            9: 'Update config encryption level to 2',
            10: 'Update all metadata settings to new config format',
            11: 'Update all provider settings to new config format',
            12: 'Migrate external API token to its own file',
            14: 'Migrate app_sub to sub_id variable',
            15: 'Bump config version to 15',
        }

    def migrate_config(self, current_version=0, expected_version=0):
        """
        Calls each successive migration until the config is the same version as SB expects
        """

        if current_version > expected_version:
            sickrage.app.log.warning("Your config version (%i) has been incremented past what this version of "
                                     "supports (%i). If you have used other forks or a newer version of  your config "
                                     "file may be unusable due to their modifications." % (current_version,
                                                                                           expected_version))
            sys.exit(1)

        while current_version < expected_version:
            next_version = current_version + 1

            if next_version in self.migration_names:
                migration_name = ': ' + self.migration_names[next_version]
            else:
                migration_name = ''

            sickrage.app.log.info("Backing up config before upgrade")
            if not backup_versioned_file(sickrage.app.config_file, current_version):
                sickrage.app.log.fatal("Config backup failed, abort upgrading config")
            else:
                sickrage.app.log.info("Proceeding with upgrade")

            # do the migration, expect a method named _migrate_v<num>
            migration_func = getattr(self, '_migrate_v' + str(next_version), None)
            if migration_func:
                sickrage.app.log.info("Migrating config up to version " + str(next_version) + migration_name)
                self.config_obj = migration_func()
            current_version = next_version

            # update config version to newest
            self.config_obj['General']['config_version'] = current_version

        return self.config_obj

    def _migrate_v9(self):
        self.config_obj['General']['encryption_version'] = 2
        return self.config_obj

    def _migrate_v10(self):
        def _migrate_metadata(metadata):
            cur_metadata = metadata.split('|')

            # if target has the old number of values, do upgrade
            if len(cur_metadata) == 10:
                # write new format
                cur_metadata.append('0')
                metadata = '|'.join(cur_metadata)
            elif len(cur_metadata) == 11:
                metadata = '|'.join(cur_metadata)
            else:
                metadata = '0|0|0|0|0|0|0|0|0|0|0'

            return metadata

        metadata_kodi = self.check_setting_str('General', 'metadata_kodi', '0|0|0|0|0|0|0|0|0|0|0')
        metadata_kodi_12plus = self.check_setting_str('General', 'metadata_kodi_12plus', '0|0|0|0|0|0|0|0|0|0|0')
        metadata_mediabrowser = self.check_setting_str('General', 'metadata_mediabrowser', '0|0|0|0|0|0|0|0|0|0|0')
        metadata_ps3 = self.check_setting_str('General', 'metadata_ps3', '0|0|0|0|0|0|0|0|0|0|0')
        metadata_wdtv = self.check_setting_str('General', 'metadata_wdtv', '0|0|0|0|0|0|0|0|0|0|0')
        metadata_tivo = self.check_setting_str('General', 'metadata_tivo', '0|0|0|0|0|0|0|0|0|0|0')
        metadata_mede8er = self.check_setting_str('General', 'metadata_mede8er', '0|0|0|0|0|0|0|0|0|0|0')

        self.config_obj['MetadataProviders'] = {}
        self.config_obj['MetadataProviders']['kodi'] = _migrate_metadata(metadata_kodi)
        self.config_obj['MetadataProviders']['kodi_12plus'] = _migrate_metadata(metadata_kodi_12plus)
        self.config_obj['MetadataProviders']['mediabrowser'] = _migrate_metadata(metadata_mediabrowser)
        self.config_obj['MetadataProviders']['sony_ps3'] = _migrate_metadata(metadata_ps3)
        self.config_obj['MetadataProviders']['wdtv'] = _migrate_metadata(metadata_wdtv)
        self.config_obj['MetadataProviders']['tivo'] = _migrate_metadata(metadata_tivo)
        self.config_obj['MetadataProviders']['mede8er'] = _migrate_metadata(metadata_mede8er)

        return self.config_obj

    def _migrate_v11(self):
        def _migrate_custom_providers(newznab, torrentrss):
            custom_providers = ""

            for provider in newznab.split('!!!'):
                cur_provider = provider.split('|')
                if len(cur_provider) > 5:
                    cur_provider.insert(0, 'newznab')
                    custom_providers += '|'.join(cur_provider[:5]) + '!!!'

            for provider in torrentrss.split('!!!'):
                cur_provider = provider.split('|')
                if len(cur_provider) == 9:
                    cur_provider.insert(0, 'torrentrss')
                    custom_providers += '|'.join(cur_provider[:5]) + '!!!'

            return custom_providers

        provider_keys = ['confirmed', 'ranked', 'engrelease', 'onlyspasearch', 'sorting', 'options', 'ratio',
                         'minseed', 'minleech', 'freeleech', 'search_mode', 'search_fallback', 'enable_daily', 'key',
                         'enable_backlog', 'cat', 'subtitle', 'api_key', 'hash', 'digest', 'username', 'password',
                         'passkey', 'pin', 'reject_m2ts', 'cookies', 'custom_url']

        self.config_obj['Providers'] = {'providers_order': self.check_setting_str('General', 'provider_order', '')}

        self.config_obj['Providers']['custom_providers'] = _migrate_custom_providers(
            self.check_setting_str('Newznab', 'newznab_data', ''),
            self.check_setting_str('TorrentRss', 'torrentrss_data', '')
        )

        sickrage.app.search_providers.load()

        for providerID, providerObj in sickrage.app.search_providers.all().items():
            provider_settings = {'enabled': self.check_setting_str(providerID.upper(), providerID, 0)}

            for k in provider_keys:
                if hasattr(providerObj, k):
                    provider_settings[k] = self.check_setting_str(providerID.upper(), '{}_{}'.format(providerID, k), '')

            self.config_obj['Providers'][providerID] = provider_settings

        return self.config_obj

    def _migrate_v12(self):
        app_oauth_token = self.check_setting_str('General', 'app_oauth_token', '')
        if app_oauth_token:
            # token_file = os.path.abspath(os.path.join(sickrage.app.data_dir, 'token.json'))
            # with open(token_file, 'w') as fd:
            #     try:
            #         json.dump(json.loads(app_oauth_token), fd)
            #     except JSONDecodeError:
            #         pass
            del self.config_obj['General']['app_oauth_token']
        return self.config_obj

    def _migrate_v14(self):
        sub_id = self.check_setting_str('General', 'app_sub', '')
        if sub_id:
            self.config_obj['General']['sub_id'] = sub_id
        return self.config_obj

    def _migrate_v15(self):
        # server_id = self.check_setting_str('General', 'server_id', '')
        # if not server_id and API().token:
        #     self.config_obj['General']['server_id'] = AccountAPI().register_app_id()
        return self.config_obj
