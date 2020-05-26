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

from tornado.web import authenticated

import sickrage
from sickrage.core.helpers import checkbox_to_value, clean_hosts, clean_host, try_int
from sickrage.core.webserver import ConfigHandler
from sickrage.core.webserver.handlers.base import BaseHandler


class ConfigNotificationsHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
        return self.render('config/notifications.mako',
                           submenu=ConfigHandler.menu,
                           title=_('Config - Notifications'),
                           header=_('Notifications'),
                           topmenu='config',
                           controller='config',
                           action='notifications')


class SaveNotificationsHandler(BaseHandler, ABC):
    @authenticated
    async def post(self, *args, **kwargs):
        await self.run_in_executor(self.handle_post)

    def handle_post(self):
        use_kodi = self.get_argument('use_kodi', None)
        kodi_always_on = self.get_argument('kodi_always_on', None)
        kodi_notify_onsnatch = self.get_argument('kodi_notify_onsnatch', None)
        kodi_notify_ondownload = self.get_argument('kodi_notify_ondownload', None)
        kodi_notify_onsubtitledownload = self.get_argument('kodi_notify_onsubtitledownload', None)
        kodi_update_onlyfirst = self.get_argument('kodi_update_onlyfirst', None)
        kodi_update_library = self.get_argument('kodi_update_library', None)
        kodi_update_full = self.get_argument('kodi_update_full', None)
        kodi_host = self.get_argument('kodi_host', None)
        kodi_username = self.get_argument('kodi_username', None)
        kodi_password = self.get_argument('kodi_password', None)
        use_plex = self.get_argument('use_plex', None)
        plex_notify_onsnatch = self.get_argument('plex_notify_onsnatch', None)
        plex_notify_ondownload = self.get_argument('plex_notify_ondownload', None)
        plex_notify_onsubtitledownload = self.get_argument('plex_notify_onsubtitledownload', None)
        plex_update_library = self.get_argument('plex_update_library', None)
        plex_server_host = self.get_argument('plex_server_host', None)
        plex_server_token = self.get_argument('plex_server_token', None)
        plex_host = self.get_argument('plex_host', None)
        plex_username = self.get_argument('plex_username', None)
        plex_password = self.get_argument('plex_password', None)
        use_emby = self.get_argument('use_emby', None)
        emby_notify_onsnatch = self.get_argument('emby_notify_onsnatch', None)
        emby_notify_ondownload = self.get_argument('emby_notify_ondownload', None)
        emby_notify_onsubtitledownload = self.get_argument('emby_notify_onsubtitledownload', None)
        emby_host = self.get_argument('emby_host', None)
        emby_apikey = self.get_argument('emby_apikey', None)
        use_growl = self.get_argument('use_growl', None)
        growl_notify_onsnatch = self.get_argument('growl_notify_onsnatch', None)
        growl_notify_ondownload = self.get_argument('growl_notify_ondownload', None)
        growl_notify_onsubtitledownload = self.get_argument('growl_notify_onsubtitledownload', None)
        growl_host = self.get_argument('growl_host', None)
        growl_password = self.get_argument('growl_password', None)
        use_freemobile = self.get_argument('use_freemobile', None)
        freemobile_notify_onsnatch = self.get_argument('freemobile_notify_onsnatch', None)
        freemobile_notify_ondownload = self.get_argument('freemobile_notify_ondownload', None)
        freemobile_notify_onsubtitledownload = self.get_argument('freemobile_notify_onsubtitledownload', None)
        freemobile_id = self.get_argument('freemobile_id', None)
        freemobile_apikey = self.get_argument('freemobile_apikey', None)
        use_telegram = self.get_argument('use_telegram', None)
        telegram_notify_onsnatch = self.get_argument('telegram_notify_onsnatch', None)
        telegram_notify_ondownload = self.get_argument('telegram_notify_ondownload', None)
        telegram_notify_onsubtitledownload = self.get_argument('telegram_notify_onsubtitledownload', None)
        telegram_id = self.get_argument('telegram_id', None)
        telegram_apikey = self.get_argument('telegram_apikey', None)
        use_join = self.get_argument('use_join', None)
        join_notify_onsnatch = self.get_argument('join_notify_onsnatch', None)
        join_notify_ondownload = self.get_argument('join_notify_ondownload', None)
        join_notify_onsubtitledownload = self.get_argument('join_notify_onsubtitledownload', None)
        join_id = self.get_argument('join_id', None)
        join_apikey = self.get_argument('join_apikey', None)
        use_prowl = self.get_argument('use_prowl', None)
        prowl_notify_onsnatch = self.get_argument('prowl_notify_onsnatch', None)
        prowl_notify_ondownload = self.get_argument('prowl_notify_ondownload', None)
        prowl_notify_onsubtitledownload = self.get_argument('prowl_notify_onsubtitledownload', None)
        prowl_api = self.get_argument('prowl_api', None)
        prowl_priority = self.get_argument('prowl_priority', None) or 0
        use_twitter = self.get_argument('use_twitter', None)
        twitter_notify_onsnatch = self.get_argument('twitter_notify_onsnatch', None)
        twitter_notify_ondownload = self.get_argument('twitter_notify_ondownload', None)
        twitter_notify_onsubtitledownload = self.get_argument('twitter_notify_onsubtitledownload', None)
        twitter_usedm = self.get_argument('twitter_usedm', None)
        twitter_dmto = self.get_argument('twitter_dmto', None)
        use_twilio = self.get_argument('use_twilio', None)
        twilio_notify_onsnatch = self.get_argument('twilio_notify_onsnatch', None)
        twilio_notify_ondownload = self.get_argument('twilio_notify_ondownload', None)
        twilio_notify_onsubtitledownload = self.get_argument('twilio_notify_onsubtitledownload', None)
        twilio_phone_sid = self.get_argument('twilio_phone_sid', None)
        twilio_account_sid = self.get_argument('twilio_account_sid', None)
        twilio_auth_token = self.get_argument('twilio_auth_token', None)
        twilio_to_number = self.get_argument('twilio_to_number', None)
        use_boxcar2 = self.get_argument('use_boxcar2', None)
        boxcar2_notify_onsnatch = self.get_argument('boxcar2_notify_onsnatch', None)
        boxcar2_notify_ondownload = self.get_argument('boxcar2_notify_ondownload', None)
        boxcar2_notify_onsubtitledownload = self.get_argument('boxcar2_notify_onsubtitledownload', None)
        boxcar2_accesstoken = self.get_argument('boxcar2_accesstoken', None)
        use_pushover = self.get_argument('use_pushover', None)
        pushover_notify_onsnatch = self.get_argument('pushover_notify_onsnatch', None)
        pushover_notify_ondownload = self.get_argument('pushover_notify_ondownload', None)
        pushover_notify_onsubtitledownload = self.get_argument('pushover_notify_onsubtitledownload', None)
        pushover_userkey = self.get_argument('pushover_userkey', None)
        pushover_apikey = self.get_argument('pushover_apikey', None)
        pushover_device = self.get_argument('pushover_device', None)
        pushover_sound = self.get_argument('pushover_sound', None)
        use_libnotify = self.get_argument('use_libnotify', None)
        libnotify_notify_onsnatch = self.get_argument('libnotify_notify_onsnatch', None)
        libnotify_notify_ondownload = self.get_argument('libnotify_notify_ondownload', None)
        libnotify_notify_onsubtitledownload = self.get_argument('libnotify_notify_onsubtitledownload', None)
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
        trakt_default_indexer = self.get_argument('trakt_default_indexer', None)
        trakt_remove_serieslist = self.get_argument('trakt_remove_serieslist', None)
        trakt_timeout = self.get_argument('trakt_timeout', None)
        trakt_blacklist_name = self.get_argument('trakt_blacklist_name', None)
        use_synologynotifier = self.get_argument('use_synologynotifier', None)
        synologynotifier_notify_onsnatch = self.get_argument('synologynotifier_notify_onsnatch', None)
        synologynotifier_notify_ondownload = self.get_argument('synologynotifier_notify_ondownload', None)
        synologynotifier_notify_onsubtitledownload = self.get_argument('synologynotifier_notify_onsubtitledownload', None)
        use_pytivo = self.get_argument('use_pytivo', None)
        pytivo_notify_onsnatch = self.get_argument('pytivo_notify_onsnatch', None)
        pytivo_notify_ondownload = self.get_argument('pytivo_notify_ondownload', None)
        pytivo_notify_onsubtitledownload = self.get_argument('pytivo_notify_onsubtitledownload', None)
        pytivo_update_library = self.get_argument('pytivo_update_library', None)
        pytivo_host = self.get_argument('pytivo_host', None)
        pytivo_share_name = self.get_argument('pytivo_share_name', None)
        pytivo_tivo_name = self.get_argument('pytivo_tivo_name', None)
        use_nma = self.get_argument('use_nma', None)
        nma_notify_onsnatch = self.get_argument('nma_notify_onsnatch', None)
        nma_notify_ondownload = self.get_argument('nma_notify_ondownload', None)
        nma_notify_onsubtitledownload = self.get_argument('nma_notify_onsubtitledownload', None)
        nma_api = self.get_argument('nma_api', None)
        nma_priority = self.get_argument('nma_priority', None) or 0
        use_pushalot = self.get_argument('use_pushalot', None)
        pushalot_notify_onsnatch = self.get_argument('pushalot_notify_onsnatch', None)
        pushalot_notify_ondownload = self.get_argument('pushalot_notify_ondownload', None)
        pushalot_notify_onsubtitledownload = self.get_argument('pushalot_notify_onsubtitledownload', None)
        pushalot_authorizationtoken = self.get_argument('pushalot_authorizationtoken', None)
        use_pushbullet = self.get_argument('use_pushbullet', None)
        pushbullet_notify_onsnatch = self.get_argument('pushbullet_notify_onsnatch', None)
        pushbullet_notify_ondownload = self.get_argument('pushbullet_notify_ondownload', None)
        pushbullet_notify_onsubtitledownload = self.get_argument('pushbullet_notify_onsubtitledownload', None)
        pushbullet_api = self.get_argument('pushbullet_api', None)
        pushbullet_device_list = self.get_argument('pushbullet_device_list', None)
        use_email = self.get_argument('use_email', None)
        email_notify_onsnatch = self.get_argument('email_notify_onsnatch', None)
        email_notify_ondownload = self.get_argument('email_notify_ondownload', None)
        email_notify_onsubtitledownload = self.get_argument('email_notify_onsubtitledownload', None)
        email_host = self.get_argument('email_host', None)
        email_port = self.get_argument('email_port', None) or 25
        email_from = self.get_argument('email_from', None)
        email_tls = self.get_argument('email_tls', None)
        email_user = self.get_argument('email_user', None)
        email_password = self.get_argument('email_password', None)
        email_list = self.get_argument('email_list', None)
        use_slack = self.get_argument('use_slack', None)
        slack_notify_onsnatch = self.get_argument('slack_notify_onsnatch', None)
        slack_notify_ondownload = self.get_argument('slack_notify_ondownload', None)
        slack_notify_onsubtitledownload = self.get_argument('slack_notify_onsubtitledownload', None)
        slack_webhook = self.get_argument('slack_webhook', None)
        use_discord = self.get_argument('use_discord', None)
        discord_notify_onsnatch = self.get_argument('discord_notify_onsnatch', None)
        discord_notify_ondownload = self.get_argument('discord_notify_ondownload', None)
        discord_notify_onsubtitledownload = self.get_argument('discord_notify_onsubtitledownload', None)
        discord_webhook = self.get_argument('discord_webhook', None)
        discord_name = self.get_argument('discord_name', None)
        discord_avatar_url = self.get_argument('discord_avatar_url', None)
        discord_tts = self.get_argument('discord_tts', None)
        use_alexa = self.get_argument('use_alexa', None)
        alexa_notify_onsnatch = self.get_argument('alexa_notify_onsnatch', None)
        alexa_notify_ondownload = self.get_argument('alexa_notify_ondownload', None)
        alexa_notify_onsubtitledownload = self.get_argument('alexa_notify_onsubtitledownload', None)

        results = []

        sickrage.app.config.use_kodi = checkbox_to_value(use_kodi)
        sickrage.app.config.kodi_always_on = checkbox_to_value(kodi_always_on)
        sickrage.app.config.kodi_notify_onsnatch = checkbox_to_value(kodi_notify_onsnatch)
        sickrage.app.config.kodi_notify_ondownload = checkbox_to_value(kodi_notify_ondownload)
        sickrage.app.config.kodi_notify_onsubtitledownload = checkbox_to_value(kodi_notify_onsubtitledownload)
        sickrage.app.config.kodi_update_library = checkbox_to_value(kodi_update_library)
        sickrage.app.config.kodi_update_full = checkbox_to_value(kodi_update_full)
        sickrage.app.config.kodi_update_onlyfirst = checkbox_to_value(kodi_update_onlyfirst)
        sickrage.app.config.kodi_host = clean_hosts(kodi_host)
        sickrage.app.config.kodi_username = kodi_username
        sickrage.app.config.kodi_password = kodi_password

        sickrage.app.config.use_plex = checkbox_to_value(use_plex)
        sickrage.app.config.plex_notify_onsnatch = checkbox_to_value(plex_notify_onsnatch)
        sickrage.app.config.plex_notify_ondownload = checkbox_to_value(plex_notify_ondownload)
        sickrage.app.config.plex_notify_onsubtitledownload = checkbox_to_value(plex_notify_onsubtitledownload)
        sickrage.app.config.plex_update_library = checkbox_to_value(plex_update_library)
        sickrage.app.config.plex_host = clean_hosts(plex_host)
        sickrage.app.config.plex_server_host = clean_hosts(plex_server_host)
        sickrage.app.config.plex_server_token = clean_host(plex_server_token)
        sickrage.app.config.plex_username = plex_username
        sickrage.app.config.plex_password = plex_password
        sickrage.app.config.use_plex_client = checkbox_to_value(use_plex)
        sickrage.app.config.plex_client_username = plex_username
        sickrage.app.config.plex_client_password = plex_password

        sickrage.app.config.use_emby = checkbox_to_value(use_emby)
        sickrage.app.config.emby_notify_onsnatch = checkbox_to_value(emby_notify_onsnatch)
        sickrage.app.config.emby_notify_ondownload = checkbox_to_value(emby_notify_ondownload)
        sickrage.app.config.emby_notify_onsubtitledownload = checkbox_to_value(emby_notify_onsubtitledownload)
        sickrage.app.config.emby_host = clean_host(emby_host)
        sickrage.app.config.emby_apikey = emby_apikey

        sickrage.app.config.use_growl = checkbox_to_value(use_growl)
        sickrage.app.config.growl_notify_onsnatch = checkbox_to_value(growl_notify_onsnatch)
        sickrage.app.config.growl_notify_ondownload = checkbox_to_value(growl_notify_ondownload)
        sickrage.app.config.growl_notify_onsubtitledownload = checkbox_to_value(growl_notify_onsubtitledownload)
        sickrage.app.config.growl_host = clean_host(growl_host, default_port=23053)
        sickrage.app.config.growl_password = growl_password

        sickrage.app.config.use_freemobile = checkbox_to_value(use_freemobile)
        sickrage.app.config.freemobile_notify_onsnatch = checkbox_to_value(freemobile_notify_onsnatch)
        sickrage.app.config.freemobile_notify_ondownload = checkbox_to_value(freemobile_notify_ondownload)
        sickrage.app.config.freemobile_notify_onsubtitledownload = checkbox_to_value(freemobile_notify_onsubtitledownload)
        sickrage.app.config.freemobile_id = freemobile_id
        sickrage.app.config.freemobile_apikey = freemobile_apikey

        sickrage.app.config.use_telegram = checkbox_to_value(use_telegram)
        sickrage.app.config.telegram_notify_onsnatch = checkbox_to_value(telegram_notify_onsnatch)
        sickrage.app.config.telegram_notify_ondownload = checkbox_to_value(telegram_notify_ondownload)
        sickrage.app.config.telegram_notify_onsubtitledownload = checkbox_to_value(telegram_notify_onsubtitledownload)
        sickrage.app.config.telegram_id = telegram_id
        sickrage.app.config.telegram_apikey = telegram_apikey

        sickrage.app.config.use_join = checkbox_to_value(use_join)
        sickrage.app.config.join_notify_onsnatch = checkbox_to_value(join_notify_onsnatch)
        sickrage.app.config.join_notify_ondownload = checkbox_to_value(join_notify_ondownload)
        sickrage.app.config.join_notify_onsubtitledownload = checkbox_to_value(join_notify_onsubtitledownload)
        sickrage.app.config.join_id = join_id
        sickrage.app.config.join_apikey = join_apikey

        sickrage.app.config.use_prowl = checkbox_to_value(use_prowl)
        sickrage.app.config.prowl_notify_onsnatch = checkbox_to_value(prowl_notify_onsnatch)
        sickrage.app.config.prowl_notify_ondownload = checkbox_to_value(prowl_notify_ondownload)
        sickrage.app.config.prowl_notify_onsubtitledownload = checkbox_to_value(prowl_notify_onsubtitledownload)
        sickrage.app.config.prowl_api = prowl_api
        sickrage.app.config.prowl_priority = prowl_priority

        sickrage.app.config.use_twitter = checkbox_to_value(use_twitter)
        sickrage.app.config.twitter_notify_onsnatch = checkbox_to_value(twitter_notify_onsnatch)
        sickrage.app.config.twitter_notify_ondownload = checkbox_to_value(twitter_notify_ondownload)
        sickrage.app.config.twitter_notify_onsubtitledownload = checkbox_to_value(twitter_notify_onsubtitledownload)
        sickrage.app.config.twitter_usedm = checkbox_to_value(twitter_usedm)
        sickrage.app.config.twitter_dmto = twitter_dmto

        sickrage.app.config.use_twilio = checkbox_to_value(use_twilio)
        sickrage.app.config.twilio_notify_onsnatch = checkbox_to_value(twilio_notify_onsnatch)
        sickrage.app.config.twilio_notify_ondownload = checkbox_to_value(twilio_notify_ondownload)
        sickrage.app.config.twilio_notify_onsubtitledownload = checkbox_to_value(twilio_notify_onsubtitledownload)
        sickrage.app.config.twilio_phone_sid = twilio_phone_sid
        sickrage.app.config.twilio_account_sid = twilio_account_sid
        sickrage.app.config.twilio_auth_token = twilio_auth_token
        sickrage.app.config.twilio_to_number = twilio_to_number

        sickrage.app.config.use_alexa = checkbox_to_value(use_alexa)
        sickrage.app.config.alexa_notify_onsnatch = checkbox_to_value(alexa_notify_onsnatch)
        sickrage.app.config.alexa_notify_ondownload = checkbox_to_value(alexa_notify_ondownload)
        sickrage.app.config.alexa_notify_onsubtitledownload = checkbox_to_value(alexa_notify_onsubtitledownload)

        sickrage.app.config.use_slack = checkbox_to_value(use_slack)
        sickrage.app.config.slack_notify_onsnatch = checkbox_to_value(slack_notify_onsnatch)
        sickrage.app.config.slack_notify_ondownload = checkbox_to_value(slack_notify_ondownload)
        sickrage.app.config.slack_notify_onsubtitledownload = checkbox_to_value(slack_notify_onsubtitledownload)
        sickrage.app.config.slack_webhook = slack_webhook

        sickrage.app.config.use_discord = checkbox_to_value(use_discord)
        sickrage.app.config.discord_notify_onsnatch = checkbox_to_value(discord_notify_onsnatch)
        sickrage.app.config.discord_notify_ondownload = checkbox_to_value(discord_notify_ondownload)
        sickrage.app.config.discord_notify_onsubtitledownload = checkbox_to_value(discord_notify_onsubtitledownload)
        sickrage.app.config.discord_webhook = discord_webhook
        sickrage.app.config.discord_name = discord_name
        sickrage.app.config.discord_avatar_url = discord_avatar_url
        sickrage.app.config.discord_tts = checkbox_to_value(discord_tts)

        sickrage.app.config.use_boxcar2 = checkbox_to_value(use_boxcar2)
        sickrage.app.config.boxcar2_notify_onsnatch = checkbox_to_value(boxcar2_notify_onsnatch)
        sickrage.app.config.boxcar2_notify_ondownload = checkbox_to_value(boxcar2_notify_ondownload)
        sickrage.app.config.boxcar2_notify_onsubtitledownload = checkbox_to_value(boxcar2_notify_onsubtitledownload)
        sickrage.app.config.boxcar2_accesstoken = boxcar2_accesstoken

        sickrage.app.config.use_pushover = checkbox_to_value(use_pushover)
        sickrage.app.config.pushover_notify_onsnatch = checkbox_to_value(pushover_notify_onsnatch)
        sickrage.app.config.pushover_notify_ondownload = checkbox_to_value(pushover_notify_ondownload)
        sickrage.app.config.pushover_notify_onsubtitledownload = checkbox_to_value(pushover_notify_onsubtitledownload)
        sickrage.app.config.pushover_userkey = pushover_userkey
        sickrage.app.config.pushover_apikey = pushover_apikey
        sickrage.app.config.pushover_device = pushover_device
        sickrage.app.config.pushover_sound = pushover_sound

        sickrage.app.config.use_libnotify = checkbox_to_value(use_libnotify)
        sickrage.app.config.libnotify_notify_onsnatch = checkbox_to_value(libnotify_notify_onsnatch)
        sickrage.app.config.libnotify_notify_ondownload = checkbox_to_value(libnotify_notify_ondownload)
        sickrage.app.config.libnotify_notify_onsubtitledownload = checkbox_to_value(libnotify_notify_onsubtitledownload)

        sickrage.app.config.use_nmj = checkbox_to_value(use_nmj)
        sickrage.app.config.nmj_host = clean_host(nmj_host)
        sickrage.app.config.nmj_database = nmj_database
        sickrage.app.config.nmj_mount = nmj_mount

        sickrage.app.config.use_nmjv2 = checkbox_to_value(use_nmjv2)
        sickrage.app.config.nmjv2_host = clean_host(nmjv2_host)
        sickrage.app.config.nmjv2_database = nmjv2_database
        sickrage.app.config.nmjv2_dbloc = nmjv2_dbloc

        sickrage.app.config.use_synoindex = checkbox_to_value(use_synoindex)

        sickrage.app.config.use_synologynotifier = checkbox_to_value(use_synologynotifier)
        sickrage.app.config.synologynotifier_notify_onsnatch = checkbox_to_value(synologynotifier_notify_onsnatch)
        sickrage.app.config.synologynotifier_notify_ondownload = checkbox_to_value(synologynotifier_notify_ondownload)
        sickrage.app.config.synologynotifier_notify_onsubtitledownload = checkbox_to_value(synologynotifier_notify_onsubtitledownload)

        sickrage.app.config.use_trakt = checkbox_to_value(use_trakt)
        sickrage.app.config.trakt_username = trakt_username
        sickrage.app.config.trakt_remove_watchlist = checkbox_to_value(trakt_remove_watchlist)
        sickrage.app.config.trakt_remove_serieslist = checkbox_to_value(trakt_remove_serieslist)
        sickrage.app.config.trakt_remove_show_from_sickrage = checkbox_to_value(trakt_remove_show_from_sickrage)
        sickrage.app.config.trakt_sync_watchlist = checkbox_to_value(trakt_sync_watchlist)
        sickrage.app.config.trakt_method_add = int(trakt_method_add)
        sickrage.app.config.trakt_start_paused = checkbox_to_value(trakt_start_paused)
        sickrage.app.config.trakt_use_recommended = checkbox_to_value(trakt_use_recommended)
        sickrage.app.config.trakt_sync = checkbox_to_value(trakt_sync)
        sickrage.app.config.trakt_sync_remove = checkbox_to_value(trakt_sync_remove)
        sickrage.app.config.trakt_default_indexer = int(trakt_default_indexer)
        sickrage.app.config.trakt_timeout = int(trakt_timeout)
        sickrage.app.config.trakt_blacklist_name = trakt_blacklist_name

        sickrage.app.config.use_email = checkbox_to_value(use_email)
        sickrage.app.config.email_notify_onsnatch = checkbox_to_value(email_notify_onsnatch)
        sickrage.app.config.email_notify_ondownload = checkbox_to_value(email_notify_ondownload)
        sickrage.app.config.email_notify_onsubtitledownload = checkbox_to_value(email_notify_onsubtitledownload)
        sickrage.app.config.email_host = clean_host(email_host)
        sickrage.app.config.email_port = try_int(email_port, 25)
        sickrage.app.config.email_from = email_from
        sickrage.app.config.email_tls = checkbox_to_value(email_tls)
        sickrage.app.config.email_user = email_user
        sickrage.app.config.email_password = email_password
        sickrage.app.config.email_list = email_list

        sickrage.app.config.use_pytivo = checkbox_to_value(use_pytivo)
        sickrage.app.config.pytivo_notify_onsnatch = checkbox_to_value(pytivo_notify_onsnatch)
        sickrage.app.config.pytivo_notify_ondownload = checkbox_to_value(pytivo_notify_ondownload)
        sickrage.app.config.pytivo_notify_onsubtitledownload = checkbox_to_value(pytivo_notify_onsubtitledownload)
        sickrage.app.config.pytivo_update_library = checkbox_to_value(pytivo_update_library)
        sickrage.app.config.pytivo_host = clean_host(pytivo_host)
        sickrage.app.config.pytivo_share_name = pytivo_share_name
        sickrage.app.config.pytivo_tivo_name = pytivo_tivo_name

        sickrage.app.config.use_nma = checkbox_to_value(use_nma)
        sickrage.app.config.nma_notify_onsnatch = checkbox_to_value(nma_notify_onsnatch)
        sickrage.app.config.nma_notify_ondownload = checkbox_to_value(nma_notify_ondownload)
        sickrage.app.config.nma_notify_onsubtitledownload = checkbox_to_value(nma_notify_onsubtitledownload)
        sickrage.app.config.nma_api = nma_api
        sickrage.app.config.nma_priority = nma_priority

        sickrage.app.config.use_pushalot = checkbox_to_value(use_pushalot)
        sickrage.app.config.pushalot_notify_onsnatch = checkbox_to_value(pushalot_notify_onsnatch)
        sickrage.app.config.pushalot_notify_ondownload = checkbox_to_value(pushalot_notify_ondownload)
        sickrage.app.config.pushalot_notify_onsubtitledownload = checkbox_to_value(pushalot_notify_onsubtitledownload)
        sickrage.app.config.pushalot_authorizationtoken = pushalot_authorizationtoken

        sickrage.app.config.use_pushbullet = checkbox_to_value(use_pushbullet)
        sickrage.app.config.pushbullet_notify_onsnatch = checkbox_to_value(pushbullet_notify_onsnatch)
        sickrage.app.config.pushbullet_notify_ondownload = checkbox_to_value(pushbullet_notify_ondownload)
        sickrage.app.config.pushbullet_notify_onsubtitledownload = checkbox_to_value(pushbullet_notify_onsubtitledownload)
        sickrage.app.config.pushbullet_api = pushbullet_api
        sickrage.app.config.pushbullet_device = pushbullet_device_list

        sickrage.app.config.save()

        if len(results) > 0:
            [sickrage.app.log.error(x) for x in results]
            sickrage.app.alerts.error(_('Error(s) Saving Configuration'), '<br>\n'.join(results))
        else:
            sickrage.app.alerts.message(_('[NOTIFICATIONS] Configuration Encrypted and Saved to disk'))

        return self.redirect("/config/notifications/")
