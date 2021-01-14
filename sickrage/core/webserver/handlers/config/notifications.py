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


from tornado.web import authenticated

import sickrage
from sickrage.core.enums import TraktAddMethod, SeriesProviderID
from sickrage.core.helpers import checkbox_to_value, clean_hosts, clean_host, try_int
from sickrage.core.webserver import ConfigWebHandler
from sickrage.core.webserver.handlers.base import BaseHandler
from sickrage.notification_providers.nmjv2 import NMJv2Location


class ConfigNotificationsHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        return self.render('config/notifications.mako',
                           submenu=ConfigWebHandler.menu,
                           title=_('Config - Notifications'),
                           header=_('Notifications'),
                           topmenu='config',
                           controller='config',
                           action='notifications')


class SaveNotificationsHandler(BaseHandler):
    @authenticated
    def post(self, *args, **kwargs):
        use_kodi = self.get_argument('use_kodi', None)
        kodi_always_on = self.get_argument('kodi_always_on', None)
        kodi_notify_on_snatch = self.get_argument('kodi_notify_on_snatch', None)
        kodi_notify_on_download = self.get_argument('kodi_notify_on_download', None)
        kodi_notify_on_subtitle_download = self.get_argument('kodi_notify_on_subtitle_download', None)
        kodi_update_only_first = self.get_argument('kodi_update_only_first', None)
        kodi_update_library = self.get_argument('kodi_update_library', None)
        kodi_update_full = self.get_argument('kodi_update_full', None)
        kodi_host = self.get_argument('kodi_host', None)
        kodi_username = self.get_argument('kodi_username', None)
        kodi_password = self.get_argument('kodi_password', None)
        use_plex = self.get_argument('use_plex', None)
        plex_notify_on_snatch = self.get_argument('plex_notify_on_snatch', None)
        plex_notify_on_download = self.get_argument('plex_notify_on_download', None)
        plex_notify_on_subtitle_download = self.get_argument('plex_notify_on_subtitle_download', None)
        plex_update_library = self.get_argument('plex_update_library', None)
        plex_server_host = self.get_argument('plex_server_host', None)
        plex_server_token = self.get_argument('plex_server_token', None)
        plex_host = self.get_argument('plex_host', None)
        plex_username = self.get_argument('plex_username', None)
        plex_password = self.get_argument('plex_password', None)
        use_emby = self.get_argument('use_emby', None)
        emby_notify_on_snatch = self.get_argument('emby_notify_on_snatch', None)
        emby_notify_on_download = self.get_argument('emby_notify_on_download', None)
        emby_notify_on_subtitle_download = self.get_argument('emby_notify_on_subtitle_download', None)
        emby_host = self.get_argument('emby_host', None)
        emby_apikey = self.get_argument('emby_apikey', None)
        use_growl = self.get_argument('use_growl', None)
        growl_notify_on_snatch = self.get_argument('growl_notify_on_snatch', None)
        growl_notify_on_download = self.get_argument('growl_notify_on_download', None)
        growl_notify_on_subtitle_download = self.get_argument('growl_notify_on_subtitle_download', None)
        growl_host = self.get_argument('growl_host', None)
        growl_password = self.get_argument('growl_password', None)
        use_freemobile = self.get_argument('use_freemobile', None)
        freemobile_notify_on_snatch = self.get_argument('freemobile_notify_on_snatch', None)
        freemobile_notify_on_download = self.get_argument('freemobile_notify_on_download', None)
        freemobile_notify_on_subtitle_download = self.get_argument('freemobile_notify_on_subtitle_download', None)
        freemobile_id = self.get_argument('freemobile_id', None)
        freemobile_apikey = self.get_argument('freemobile_apikey', None)
        use_telegram = self.get_argument('use_telegram', None)
        telegram_notify_on_snatch = self.get_argument('telegram_notify_on_snatch', None)
        telegram_notify_on_download = self.get_argument('telegram_notify_on_download', None)
        telegram_notify_on_subtitle_download = self.get_argument('telegram_notify_on_subtitle_download', None)
        telegram_id = self.get_argument('telegram_id', None)
        telegram_apikey = self.get_argument('telegram_apikey', None)
        use_join = self.get_argument('use_join', None)
        join_notify_on_snatch = self.get_argument('join_notify_on_snatch', None)
        join_notify_on_download = self.get_argument('join_notify_on_download', None)
        join_notify_on_subtitle_download = self.get_argument('join_notify_on_subtitle_download', None)
        join_id = self.get_argument('join_id', None)
        join_apikey = self.get_argument('join_apikey', None)
        use_prowl = self.get_argument('use_prowl', None)
        prowl_notify_on_snatch = self.get_argument('prowl_notify_on_snatch', None)
        prowl_notify_on_download = self.get_argument('prowl_notify_on_download', None)
        prowl_notify_on_subtitle_download = self.get_argument('prowl_notify_on_subtitle_download', None)
        prowl_apikey = self.get_argument('prowl_apikey', None)
        prowl_priority = self.get_argument('prowl_priority', None) or 0
        use_twitter = self.get_argument('use_twitter', None)
        twitter_notify_on_snatch = self.get_argument('twitter_notify_on_snatch', None)
        twitter_notify_on_download = self.get_argument('twitter_notify_on_download', None)
        twitter_notify_on_subtitle_download = self.get_argument('twitter_notify_on_subtitle_download', None)
        twitter_usedm = self.get_argument('twitter_usedm', None)
        twitter_dmto = self.get_argument('twitter_dmto', None)
        use_twilio = self.get_argument('use_twilio', None)
        twilio_notify_on_snatch = self.get_argument('twilio_notify_on_snatch', None)
        twilio_notify_on_download = self.get_argument('twilio_notify_on_download', None)
        twilio_notify_on_subtitle_download = self.get_argument('twilio_notify_on_subtitle_download', None)
        twilio_phone_sid = self.get_argument('twilio_phone_sid', None)
        twilio_account_sid = self.get_argument('twilio_account_sid', None)
        twilio_auth_token = self.get_argument('twilio_auth_token', None)
        twilio_to_number = self.get_argument('twilio_to_number', None)
        use_boxcar2 = self.get_argument('use_boxcar2', None)
        boxcar2_notify_on_snatch = self.get_argument('boxcar2_notify_on_snatch', None)
        boxcar2_notify_on_download = self.get_argument('boxcar2_notify_on_download', None)
        boxcar2_notify_on_subtitle_download = self.get_argument('boxcar2_notify_on_subtitle_download', None)
        boxcar2_accesstoken = self.get_argument('boxcar2_accesstoken', None)
        use_pushover = self.get_argument('use_pushover', None)
        pushover_notify_on_snatch = self.get_argument('pushover_notify_on_snatch', None)
        pushover_notify_on_download = self.get_argument('pushover_notify_on_download', None)
        pushover_notify_on_subtitle_download = self.get_argument('pushover_notify_on_subtitle_download', None)
        pushover_userkey = self.get_argument('pushover_userkey', None)
        pushover_apikey = self.get_argument('pushover_apikey', None)
        pushover_device = self.get_argument('pushover_device', None)
        pushover_sound = self.get_argument('pushover_sound', None)
        use_libnotify = self.get_argument('use_libnotify', None)
        libnotify_notify_on_snatch = self.get_argument('libnotify_notify_on_snatch', None)
        libnotify_notify_on_download = self.get_argument('libnotify_notify_on_download', None)
        libnotify_notify_on_subtitle_download = self.get_argument('libnotify_notify_on_subtitle_download', None)
        use_nmj = self.get_argument('use_nmj', None)
        nmj_host = self.get_argument('nmj_host', None)
        nmj_database = self.get_argument('nmj_database', None)
        nmj_mount = self.get_argument('nmj_mount', None)
        use_synoindex = self.get_argument('use_synoindex', None)
        use_nmjv2 = self.get_argument('use_nmjv2', None)
        nmjv2_host = self.get_argument('nmjv2_host', None)
        nmjv2_dbloc = self.get_argument('nmjv2_dbloc', None)
        nmjv2_database = self.get_argument('nmjv2_database', None)
        use_trakt = self.get_argument('use_trakt', None)
        trakt_username = self.get_argument('trakt_username', None)
        trakt_remove_watchlist = self.get_argument('trakt_remove_watchlist', None)
        trakt_sync_watchlist = self.get_argument('trakt_sync_watchlist', None)
        trakt_remove_show_from_sickrage = self.get_argument('trakt_remove_show_from_sickrage', None)
        trakt_method_add = self.get_argument('trakt_method_add', None)
        trakt_start_paused = self.get_argument('trakt_start_paused', None)
        trakt_use_recommended = self.get_argument('trakt_use_recommended', None)
        trakt_sync = self.get_argument('trakt_sync', None)
        trakt_sync_remove = self.get_argument('trakt_sync_remove', None)
        trakt_default_series_provider = self.get_argument('trakt_default_series_provider', None)
        trakt_remove_serieslist = self.get_argument('trakt_remove_serieslist', None)
        trakt_timeout = self.get_argument('trakt_timeout', None)
        trakt_blacklist_name = self.get_argument('trakt_blacklist_name', None)
        use_synology_notification_provider = self.get_argument('use_synology_notification_provider', None)
        synology_notification_provider_notify_on_snatch = self.get_argument('synology_notification_provider_notify_on_snatch', None)
        synology_notification_provider_notify_on_download = self.get_argument('synology_notification_provider_notify_on_download', None)
        synology_notification_provider_notify_on_subtitle_download = self.get_argument('synology_notification_provider_notify_on_subtitle_download', None)
        use_pytivo = self.get_argument('use_pytivo', None)
        pytivo_notify_on_snatch = self.get_argument('pytivo_notify_on_snatch', None)
        pytivo_notify_on_download = self.get_argument('pytivo_notify_on_download', None)
        pytivo_notify_on_subtitle_download = self.get_argument('pytivo_notify_on_subtitle_download', None)
        pytivo_update_library = self.get_argument('pytivo_update_library', None)
        pytivo_host = self.get_argument('pytivo_host', None)
        pytivo_share_name = self.get_argument('pytivo_share_name', None)
        pytivo_tivo_name = self.get_argument('pytivo_tivo_name', None)
        use_nma = self.get_argument('use_nma', None)
        nma_notify_on_snatch = self.get_argument('nma_notify_on_snatch', None)
        nma_notify_on_download = self.get_argument('nma_notify_on_download', None)
        nma_notify_on_subtitle_download = self.get_argument('nma_notify_on_subtitle_download', None)
        nma_api = self.get_argument('nma_api', None)
        nma_priority = self.get_argument('nma_priority', None) or 0
        use_pushalot = self.get_argument('use_pushalot', None)
        pushalot_notify_on_snatch = self.get_argument('pushalot_notify_on_snatch', None)
        pushalot_notify_on_download = self.get_argument('pushalot_notify_on_download', None)
        pushalot_notify_on_subtitle_download = self.get_argument('pushalot_notify_on_subtitle_download', None)
        pushalot_authorizationtoken = self.get_argument('pushalot_authorizationtoken', None)
        use_pushbullet = self.get_argument('use_pushbullet', None)
        pushbullet_notify_on_snatch = self.get_argument('pushbullet_notify_on_snatch', None)
        pushbullet_notify_on_download = self.get_argument('pushbullet_notify_on_download', None)
        pushbullet_notify_on_subtitle_download = self.get_argument('pushbullet_notify_on_subtitle_download', None)
        pushbullet_api = self.get_argument('pushbullet_api', None)
        pushbullet_device_list = self.get_argument('pushbullet_device_list', None)
        use_email = self.get_argument('use_email', None)
        email_notify_on_snatch = self.get_argument('email_notify_on_snatch', None)
        email_notify_on_download = self.get_argument('email_notify_on_download', None)
        email_notify_on_subtitle_download = self.get_argument('email_notify_on_subtitle_download', None)
        email_host = self.get_argument('email_host', None)
        email_port = self.get_argument('email_port', None) or 25
        email_from = self.get_argument('email_from', None)
        email_tls = self.get_argument('email_tls', None)
        email_user = self.get_argument('email_user', None)
        email_password = self.get_argument('email_password', None)
        email_list = self.get_argument('email_list', None)
        use_slack = self.get_argument('use_slack', None)
        slack_notify_on_snatch = self.get_argument('slack_notify_on_snatch', None)
        slack_notify_on_download = self.get_argument('slack_notify_on_download', None)
        slack_notify_on_subtitle_download = self.get_argument('slack_notify_on_subtitle_download', None)
        slack_webhook = self.get_argument('slack_webhook', None)
        use_discord = self.get_argument('use_discord', None)
        discord_notify_on_snatch = self.get_argument('discord_notify_on_snatch', None)
        discord_notify_on_download = self.get_argument('discord_notify_on_download', None)
        discord_notify_on_subtitle_download = self.get_argument('discord_notify_on_subtitle_download', None)
        discord_webhook = self.get_argument('discord_webhook', None)
        discord_name = self.get_argument('discord_name', None)
        discord_avatar_url = self.get_argument('discord_avatar_url', None)
        discord_tts = self.get_argument('discord_tts', None)
        use_alexa = self.get_argument('use_alexa', None)
        alexa_notify_on_snatch = self.get_argument('alexa_notify_on_snatch', None)
        alexa_notify_on_download = self.get_argument('alexa_notify_on_download', None)
        alexa_notify_on_subtitle_download = self.get_argument('alexa_notify_on_subtitle_download', None)

        results = []

        sickrage.app.config.kodi.enable = checkbox_to_value(use_kodi)
        sickrage.app.config.kodi.always_on = checkbox_to_value(kodi_always_on)
        sickrage.app.config.kodi.notify_on_snatch = checkbox_to_value(kodi_notify_on_snatch)
        sickrage.app.config.kodi.notify_on_download = checkbox_to_value(kodi_notify_on_download)
        sickrage.app.config.kodi.notify_on_subtitle_download = checkbox_to_value(kodi_notify_on_subtitle_download)
        sickrage.app.config.kodi.update_library = checkbox_to_value(kodi_update_library)
        sickrage.app.config.kodi.update_full = checkbox_to_value(kodi_update_full)
        sickrage.app.config.kodi.update_only_first = checkbox_to_value(kodi_update_only_first)
        sickrage.app.config.kodi.host = clean_hosts(kodi_host)
        sickrage.app.config.kodi.username = kodi_username
        sickrage.app.config.kodi.password = kodi_password

        sickrage.app.config.plex.enable = checkbox_to_value(use_plex)
        sickrage.app.config.plex.notify_on_snatch = checkbox_to_value(plex_notify_on_snatch)
        sickrage.app.config.plex.notify_on_download = checkbox_to_value(plex_notify_on_download)
        sickrage.app.config.plex.notify_on_subtitle_download = checkbox_to_value(plex_notify_on_subtitle_download)
        sickrage.app.config.plex.update_library = checkbox_to_value(plex_update_library)
        sickrage.app.config.plex.host = clean_hosts(plex_host)
        sickrage.app.config.plex.server_host = clean_hosts(plex_server_host)
        sickrage.app.config.plex.server_token = clean_host(plex_server_token)
        sickrage.app.config.plex.username = plex_username
        sickrage.app.config.plex.password = plex_password
        sickrage.app.config.plex.enable_client = checkbox_to_value(use_plex)
        sickrage.app.config.plex.client_username = plex_username
        sickrage.app.config.plex.client_password = plex_password

        sickrage.app.config.emby.enable = checkbox_to_value(use_emby)
        sickrage.app.config.emby.notify_on_snatch = checkbox_to_value(emby_notify_on_snatch)
        sickrage.app.config.emby.notify_on_download = checkbox_to_value(emby_notify_on_download)
        sickrage.app.config.emby.notify_on_subtitle_download = checkbox_to_value(emby_notify_on_subtitle_download)
        sickrage.app.config.emby.host = clean_host(emby_host)
        sickrage.app.config.emby.apikey = emby_apikey

        sickrage.app.config.growl.enable = checkbox_to_value(use_growl)
        sickrage.app.config.growl.notify_on_snatch = checkbox_to_value(growl_notify_on_snatch)
        sickrage.app.config.growl.notify_on_download = checkbox_to_value(growl_notify_on_download)
        sickrage.app.config.growl.notify_on_subtitle_download = checkbox_to_value(growl_notify_on_subtitle_download)
        sickrage.app.config.growl.host = clean_host(growl_host, default_port=23053)
        sickrage.app.config.growl.password = growl_password

        sickrage.app.config.freemobile.enable = checkbox_to_value(use_freemobile)
        sickrage.app.config.freemobile.notify_on_snatch = checkbox_to_value(freemobile_notify_on_snatch)
        sickrage.app.config.freemobile.notify_on_download = checkbox_to_value(freemobile_notify_on_download)
        sickrage.app.config.freemobile.notify_on_subtitle_download = checkbox_to_value(freemobile_notify_on_subtitle_download)
        sickrage.app.config.freemobile.user_id = freemobile_id
        sickrage.app.config.freemobile.apikey = freemobile_apikey

        sickrage.app.config.telegram.enable = checkbox_to_value(use_telegram)
        sickrage.app.config.telegram.notify_on_snatch = checkbox_to_value(telegram_notify_on_snatch)
        sickrage.app.config.telegram.notify_on_download = checkbox_to_value(telegram_notify_on_download)
        sickrage.app.config.telegram.notify_on_subtitle_download = checkbox_to_value(telegram_notify_on_subtitle_download)
        sickrage.app.config.telegram.user_id = telegram_id
        sickrage.app.config.telegram.apikey = telegram_apikey

        sickrage.app.config.join_app.enable = checkbox_to_value(use_join)
        sickrage.app.config.join_app.notify_on_snatch = checkbox_to_value(join_notify_on_snatch)
        sickrage.app.config.join_app.notify_on_download = checkbox_to_value(join_notify_on_download)
        sickrage.app.config.join_app.notify_on_subtitle_download = checkbox_to_value(join_notify_on_subtitle_download)
        sickrage.app.config.join_app.user_id = join_id
        sickrage.app.config.join_app.apikey = join_apikey

        sickrage.app.config.prowl.enable = checkbox_to_value(use_prowl)
        sickrage.app.config.prowl.notify_on_snatch = checkbox_to_value(prowl_notify_on_snatch)
        sickrage.app.config.prowl.notify_on_download = checkbox_to_value(prowl_notify_on_download)
        sickrage.app.config.prowl.notify_on_subtitle_download = checkbox_to_value(prowl_notify_on_subtitle_download)
        sickrage.app.config.prowl.apikey = prowl_apikey
        sickrage.app.config.prowl.priority = prowl_priority

        sickrage.app.config.twitter.enable = checkbox_to_value(use_twitter)
        sickrage.app.config.twitter.notify_on_snatch = checkbox_to_value(twitter_notify_on_snatch)
        sickrage.app.config.twitter.notify_on_download = checkbox_to_value(twitter_notify_on_download)
        sickrage.app.config.twitter.notify_on_subtitle_download = checkbox_to_value(twitter_notify_on_subtitle_download)
        sickrage.app.config.twitter.use_dm = checkbox_to_value(twitter_usedm)
        sickrage.app.config.twitter.dm_to = twitter_dmto

        sickrage.app.config.twilio.enable = checkbox_to_value(use_twilio)
        sickrage.app.config.twilio.notify_on_snatch = checkbox_to_value(twilio_notify_on_snatch)
        sickrage.app.config.twilio.notify_on_download = checkbox_to_value(twilio_notify_on_download)
        sickrage.app.config.twilio.notify_on_subtitle_download = checkbox_to_value(twilio_notify_on_subtitle_download)
        sickrage.app.config.twilio.phone_sid = twilio_phone_sid
        sickrage.app.config.twilio.account_sid = twilio_account_sid
        sickrage.app.config.twilio.auth_token = twilio_auth_token
        sickrage.app.config.twilio.to_number = twilio_to_number

        sickrage.app.config.alexa.enable = checkbox_to_value(use_alexa)
        sickrage.app.config.alexa.notify_on_snatch = checkbox_to_value(alexa_notify_on_snatch)
        sickrage.app.config.alexa.notify_on_download = checkbox_to_value(alexa_notify_on_download)
        sickrage.app.config.alexa.notify_on_subtitle_download = checkbox_to_value(alexa_notify_on_subtitle_download)

        sickrage.app.config.slack.enable = checkbox_to_value(use_slack)
        sickrage.app.config.slack.notify_on_snatch = checkbox_to_value(slack_notify_on_snatch)
        sickrage.app.config.slack.notify_on_download = checkbox_to_value(slack_notify_on_download)
        sickrage.app.config.slack.notify_on_subtitle_download = checkbox_to_value(slack_notify_on_subtitle_download)
        sickrage.app.config.slack.webhook = slack_webhook

        sickrage.app.config.discord.enable = checkbox_to_value(use_discord)
        sickrage.app.config.discord.notify_on_snatch = checkbox_to_value(discord_notify_on_snatch)
        sickrage.app.config.discord.notify_on_download = checkbox_to_value(discord_notify_on_download)
        sickrage.app.config.discord.notify_on_subtitle_download = checkbox_to_value(discord_notify_on_subtitle_download)
        sickrage.app.config.discord.webhook = discord_webhook
        sickrage.app.config.discord.name = discord_name
        sickrage.app.config.discord.avatar_url = discord_avatar_url
        sickrage.app.config.discord.tts = checkbox_to_value(discord_tts)

        sickrage.app.config.boxcar2.enable = checkbox_to_value(use_boxcar2)
        sickrage.app.config.boxcar2.notify_on_snatch = checkbox_to_value(boxcar2_notify_on_snatch)
        sickrage.app.config.boxcar2.notify_on_download = checkbox_to_value(boxcar2_notify_on_download)
        sickrage.app.config.boxcar2.notify_on_subtitle_download = checkbox_to_value(boxcar2_notify_on_subtitle_download)
        sickrage.app.config.boxcar2.access_token = boxcar2_accesstoken

        sickrage.app.config.pushover.enable = checkbox_to_value(use_pushover)
        sickrage.app.config.pushover.notify_on_snatch = checkbox_to_value(pushover_notify_on_snatch)
        sickrage.app.config.pushover.notify_on_download = checkbox_to_value(pushover_notify_on_download)
        sickrage.app.config.pushover.notify_on_subtitle_download = checkbox_to_value(pushover_notify_on_subtitle_download)
        sickrage.app.config.pushover.user_key = pushover_userkey
        sickrage.app.config.pushover.apikey = pushover_apikey
        sickrage.app.config.pushover.device = pushover_device
        sickrage.app.config.pushover.sound = pushover_sound

        sickrage.app.config.libnotify.enable = checkbox_to_value(use_libnotify)
        sickrage.app.config.libnotify.notify_on_snatch = checkbox_to_value(libnotify_notify_on_snatch)
        sickrage.app.config.libnotify.notify_on_download = checkbox_to_value(libnotify_notify_on_download)
        sickrage.app.config.libnotify.notify_on_subtitle_download = checkbox_to_value(libnotify_notify_on_subtitle_download)

        sickrage.app.config.nmj.enable = checkbox_to_value(use_nmj)
        sickrage.app.config.nmj.host = clean_host(nmj_host)
        sickrage.app.config.nmj.database = nmj_database
        sickrage.app.config.nmj.mount = nmj_mount

        sickrage.app.config.nmjv2.enable = checkbox_to_value(use_nmjv2)
        sickrage.app.config.nmjv2.host = clean_host(nmjv2_host)
        sickrage.app.config.nmjv2.database = nmjv2_database
        sickrage.app.config.nmjv2.db_loc = NMJv2Location[nmjv2_dbloc]

        sickrage.app.config.synology.enable_index = checkbox_to_value(use_synoindex)

        sickrage.app.config.synology.enable_notifications = checkbox_to_value(use_synology_notification_provider)
        sickrage.app.config.synology.notify_on_snatch = checkbox_to_value(synology_notification_provider_notify_on_snatch)
        sickrage.app.config.synology.notify_on_download = checkbox_to_value(synology_notification_provider_notify_on_download)
        sickrage.app.config.synology.notify_on_subtitle_download = checkbox_to_value(synology_notification_provider_notify_on_subtitle_download)

        sickrage.app.config.trakt.enable = checkbox_to_value(use_trakt)
        sickrage.app.config.trakt.username = trakt_username
        sickrage.app.config.trakt.remove_watchlist = checkbox_to_value(trakt_remove_watchlist)
        sickrage.app.config.trakt.remove_serieslist = checkbox_to_value(trakt_remove_serieslist)
        sickrage.app.config.trakt.remove_show_from_sickrage = checkbox_to_value(trakt_remove_show_from_sickrage)
        sickrage.app.config.trakt.sync_watchlist = checkbox_to_value(trakt_sync_watchlist)
        sickrage.app.config.trakt.method_add = TraktAddMethod[trakt_method_add]
        sickrage.app.config.trakt.start_paused = checkbox_to_value(trakt_start_paused)
        sickrage.app.config.trakt.use_recommended = checkbox_to_value(trakt_use_recommended)
        sickrage.app.config.trakt.sync = checkbox_to_value(trakt_sync)
        sickrage.app.config.trakt.sync_remove = checkbox_to_value(trakt_sync_remove)
        sickrage.app.config.trakt.series_provider_default = SeriesProviderID[trakt_default_series_provider]
        sickrage.app.config.trakt.timeout = int(trakt_timeout)
        sickrage.app.config.trakt.blacklist_name = trakt_blacklist_name

        sickrage.app.config.email.enable = checkbox_to_value(use_email)
        sickrage.app.config.email.notify_on_snatch = checkbox_to_value(email_notify_on_snatch)
        sickrage.app.config.email.notify_on_download = checkbox_to_value(email_notify_on_download)
        sickrage.app.config.email.notify_on_subtitle_download = checkbox_to_value(email_notify_on_subtitle_download)
        sickrage.app.config.email.host = clean_host(email_host)
        sickrage.app.config.email.port = try_int(email_port, 25)
        sickrage.app.config.email.send_from = email_from
        sickrage.app.config.email.tls = checkbox_to_value(email_tls)
        sickrage.app.config.email.username = email_user
        sickrage.app.config.email.password = email_password
        sickrage.app.config.email.send_to_list = email_list

        sickrage.app.config.pytivo.enable = checkbox_to_value(use_pytivo)
        sickrage.app.config.pytivo.notify_on_snatch = checkbox_to_value(pytivo_notify_on_snatch)
        sickrage.app.config.pytivo.notify_on_download = checkbox_to_value(pytivo_notify_on_download)
        sickrage.app.config.pytivo.notify_on_subtitle_download = checkbox_to_value(pytivo_notify_on_subtitle_download)
        sickrage.app.config.pytivo.update_library = checkbox_to_value(pytivo_update_library)
        sickrage.app.config.pytivo.host = clean_host(pytivo_host)
        sickrage.app.config.pytivo.share_name = pytivo_share_name
        sickrage.app.config.pytivo.tivo_name = pytivo_tivo_name

        sickrage.app.config.nma.enable = checkbox_to_value(use_nma)
        sickrage.app.config.nma.notify_on_snatch = checkbox_to_value(nma_notify_on_snatch)
        sickrage.app.config.nma.notify_on_download = checkbox_to_value(nma_notify_on_download)
        sickrage.app.config.nma.notify_on_subtitle_download = checkbox_to_value(nma_notify_on_subtitle_download)
        sickrage.app.config.nma.api_keys = nma_api
        sickrage.app.config.nma.priority = nma_priority

        sickrage.app.config.pushalot.enable = checkbox_to_value(use_pushalot)
        sickrage.app.config.pushalot.notify_on_snatch = checkbox_to_value(pushalot_notify_on_snatch)
        sickrage.app.config.pushalot.notify_on_download = checkbox_to_value(pushalot_notify_on_download)
        sickrage.app.config.pushalot.notify_on_subtitle_download = checkbox_to_value(pushalot_notify_on_subtitle_download)
        sickrage.app.config.pushalot.auth_token = pushalot_authorizationtoken

        sickrage.app.config.pushbullet.enable = checkbox_to_value(use_pushbullet)
        sickrage.app.config.pushbullet.notify_on_snatch = checkbox_to_value(pushbullet_notify_on_snatch)
        sickrage.app.config.pushbullet.notify_on_download = checkbox_to_value(pushbullet_notify_on_download)
        sickrage.app.config.pushbullet.notify_on_subtitle_download = checkbox_to_value(pushbullet_notify_on_subtitle_download)
        sickrage.app.config.pushbullet.api_key = pushbullet_api
        sickrage.app.config.pushbullet.device = pushbullet_device_list

        sickrage.app.config.save()

        if len(results) > 0:
            [sickrage.app.log.error(x) for x in results]
            sickrage.app.alerts.error(_('Error(s) Saving Configuration'), '<br>\n'.join(results))
        else:
            sickrage.app.alerts.message(_('[NOTIFICATIONS] Configuration Saved to Database'))

        return self.redirect("/config/notifications/")
