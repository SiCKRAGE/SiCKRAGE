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

from tornado.web import authenticated

import sickrage
from sickrage.core.common import Quality, Qualities, EpisodeStatus
from sickrage.core.config.helpers import change_gui_lang, change_https_key, change_https_cert, change_updater_freq, change_show_update_hour, \
    change_version_notify
from sickrage.core.enums import UITheme, DefaultHomePage, TimezoneDisplay, SearchFormat, SeriesProviderID, CpuPreset
from sickrage.core.helpers import generate_api_key, checkbox_to_value, try_int
from sickrage.core.webserver import ConfigWebHandler
from sickrage.core.webserver.handlers.base import BaseHandler


class ConfigGeneralHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        return self.render('config/general.mako',
                           title=_('Config - General'),
                           header=_('General Configuration'),
                           topmenu='config',
                           submenu=ConfigWebHandler.menu,
                           controller='config',
                           action='general', )


class GenerateApiKeyHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        return self.write(generate_api_key())


class SaveRootDirsHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        sickrage.app.config.general.root_dirs = self.get_argument('rootDirString', '')
        sickrage.app.config.save()


class SaveAddShowDefaultsHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        default_status = self.get_argument('defaultStatus', '5')
        quality_preset = self.get_argument('qualityPreset', '')
        any_qualities = self.get_argument('anyQualities', '')
        best_qualities = self.get_argument('bestQualities', '')
        default_flatten_folders = self.get_argument('defaultFlattenFolders', None)
        subtitles = self.get_argument('subtitles', None)
        anime = self.get_argument('anime', None)
        search_format = self.get_argument('search_format', None)
        default_status_after = self.get_argument('defaultStatusAfter', None) or EpisodeStatus.WANTED
        scene = self.get_argument('scene', None)
        skip_downloaded = self.get_argument('skip_downloaded', None)
        add_show_year = self.get_argument('add_show_year', None)

        any_qualities = any_qualities.split(',') if len(any_qualities) else []
        best_qualities = best_qualities.split(',') if len(best_qualities) else []

        try:
            new_quality = Qualities[quality_preset]
        except KeyError:
            new_quality = Quality.combine_qualities([Qualities[x] for x in any_qualities], [Qualities[x] for x in best_qualities])

        sickrage.app.config.general.status_default = EpisodeStatus[default_status]
        sickrage.app.config.general.status_default_after = EpisodeStatus[default_status_after]
        sickrage.app.config.general.quality_default = new_quality

        sickrage.app.config.general.flatten_folders_default = not checkbox_to_value(default_flatten_folders)
        sickrage.app.config.subtitles.default = checkbox_to_value(subtitles)

        sickrage.app.config.general.anime_default = checkbox_to_value(anime)
        sickrage.app.config.general.search_format_default = SearchFormat[search_format]
        sickrage.app.config.general.scene_default = checkbox_to_value(scene)
        sickrage.app.config.general.skip_downloaded_default = checkbox_to_value(skip_downloaded)
        sickrage.app.config.general.add_show_year_default = checkbox_to_value(add_show_year)

        sickrage.app.config.save()


class SaveGeneralHandler(BaseHandler):
    @authenticated
    def post(self, *args, **kwargs):
        log_nr = self.get_argument('log_nr', '5')
        log_size = self.get_argument('log_size', '1048576')
        web_port = self.get_argument('web_port', None)
        web_ipv6 = self.get_argument('web_ipv6', None)
        web_host = self.get_argument('web_host', None)
        trash_remove_show = self.get_argument('trash_remove_show', None)
        trash_rotate_logs = self.get_argument('trash_rotate_logs', None)
        update_frequency = self.get_argument('update_frequency', None)
        skip_removed_files = self.get_argument('skip_removed_files', None)
        series_provider_default_language = self.get_argument('series_provider_default_language', 'en')
        ep_default_deleted_status = self.get_argument('ep_default_deleted_status', None)
        launch_browser = self.get_argument('launch_browser', None)
        show_update_hour = self.get_argument('show_update_hour', '3')
        api_key = self.get_argument('api_key', None)
        series_provider_default = self.get_argument('series_provider_default', None)
        timezone_display = self.get_argument('timezone_display', None)
        cpu_preset = self.get_argument('cpu_preset', 'NORMAL')
        version_notify = self.get_argument('version_notify', None)
        enable_https = self.get_argument('enable_https', None)
        https_cert = self.get_argument('https_cert', None)
        https_key = self.get_argument('https_key', None)
        handle_reverse_proxy = self.get_argument('handle_reverse_proxy', None)
        sort_article = self.get_argument('sort_article', None)
        auto_update = self.get_argument('auto_update', None)
        notify_on_update = self.get_argument('notify_on_update', None)
        backup_on_update = self.get_argument('backup_on_update', None)
        proxy_setting = self.get_argument('proxy_setting', None)
        proxy_series_providers = self.get_argument('proxy_series_providers', None)
        anon_redirect = self.get_argument('anon_redirect', None)
        git_path = self.get_argument('git_path', None)
        pip3_path = self.get_argument('pip3_path', None)
        calendar_unprotected = self.get_argument('calendar_unprotected', None)
        calendar_icons = self.get_argument('calendar_icons', None)
        debug = self.get_argument('debug', None)
        ssl_verify = self.get_argument('ssl_verify', None)
        no_restart = self.get_argument('no_restart', None)
        coming_eps_missed_range = self.get_argument('coming_eps_missed_range', None)
        filter_row = self.get_argument('filter_row', None)
        fuzzy_dating = self.get_argument('fuzzy_dating', None)
        trim_zero = self.get_argument('trim_zero', None)
        date_preset = self.get_argument('date_preset', None)
        time_preset = self.get_argument('time_preset', None)
        series_provider_timeout = self.get_argument('series_provider_timeout', None)
        download_url = self.get_argument('download_url', None)
        theme_name = self.get_argument('theme_name', None)
        default_page = self.get_argument('default_page', None)
        gui_language = self.get_argument('gui_language', None)
        display_all_seasons = self.get_argument('display_all_seasons', None)
        show_update_stale = self.get_argument('show_update_stale', None)
        notify_on_login = self.get_argument('notify_on_login', None)
        allowed_video_file_exts = self.get_argument('allowed_video_file_exts', '')
        enable_upnp = self.get_argument('enable_upnp', None)
        strip_special_file_bits = self.get_argument('strip_special_file_bits', None)
        max_queue_workers = self.get_argument('max_queue_workers', None)
        web_root = self.get_argument('web_root', '')
        ip_whitelist_localhost_enabled = self.get_argument('ip_whitelist_localhost_enabled', None)
        ip_whitelist_enabled = self.get_argument('ip_whitelist_enabled', None)
        ip_whitelist = self.get_argument('ip_whitelist', '')
        web_auth_method = self.get_argument('web_auth_method', '')
        web_username = self.get_argument('web_username', '')
        web_password = self.get_argument('web_password', '')
        enable_sickrage_api = self.get_argument('enable_sickrage_api', None)

        results = []

        change_gui_lang(gui_language)
        change_updater_freq(update_frequency)
        change_show_update_hour(show_update_hour)
        change_version_notify(checkbox_to_value(version_notify))

        # Debug
        sickrage.app.config.general.debug = sickrage.app.debug = checkbox_to_value(debug)
        sickrage.app.log.set_level()

        # Misc
        sickrage.app.config.general.enable_upnp = checkbox_to_value(enable_upnp)
        sickrage.app.config.general.download_url = download_url
        sickrage.app.config.general.series_provider_default_language = series_provider_default_language
        sickrage.app.config.general.ep_default_deleted_status = EpisodeStatus[ep_default_deleted_status]
        sickrage.app.config.general.skip_removed_files = checkbox_to_value(skip_removed_files)
        sickrage.app.config.general.launch_browser = checkbox_to_value(launch_browser)
        sickrage.app.config.general.auto_update = checkbox_to_value(auto_update)
        sickrage.app.config.general.notify_on_update = checkbox_to_value(notify_on_update)
        sickrage.app.config.general.backup_on_update = checkbox_to_value(backup_on_update)
        sickrage.app.config.general.notify_on_login = checkbox_to_value(notify_on_login)
        sickrage.app.config.general.show_update_stale = checkbox_to_value(show_update_stale)
        sickrage.app.config.general.log_nr = int(log_nr)
        sickrage.app.config.general.log_size = int(log_size)

        sickrage.app.config.general.trash_remove_show = checkbox_to_value(trash_remove_show)
        sickrage.app.config.general.trash_rotate_logs = checkbox_to_value(trash_rotate_logs)
        sickrage.app.config.general.launch_browser = checkbox_to_value(launch_browser)
        sickrage.app.config.general.sort_article = checkbox_to_value(sort_article)
        sickrage.app.config.general.cpu_preset = CpuPreset[cpu_preset]
        sickrage.app.config.general.anon_redirect = anon_redirect
        sickrage.app.config.general.proxy_setting = proxy_setting
        sickrage.app.config.general.proxy_series_providers = checkbox_to_value(proxy_series_providers)
        sickrage.app.config.general.git_reset = 1
        sickrage.app.config.general.git_path = git_path
        sickrage.app.config.general.pip3_path = pip3_path
        sickrage.app.config.general.calendar_unprotected = checkbox_to_value(calendar_unprotected)
        sickrage.app.config.general.calendar_icons = checkbox_to_value(calendar_icons)
        sickrage.app.config.general.no_restart = checkbox_to_value(no_restart)

        sickrage.app.config.general.ssl_verify = checkbox_to_value(ssl_verify)
        sickrage.app.config.gui.coming_eps_missed_range = try_int(coming_eps_missed_range, 7)
        sickrage.app.config.general.display_all_seasons = checkbox_to_value(display_all_seasons)

        sickrage.app.config.general.web_port = int(web_port)
        sickrage.app.config.general.web_ipv6 = checkbox_to_value(web_ipv6)

        sickrage.app.config.gui.filter_row = checkbox_to_value(filter_row)
        sickrage.app.config.gui.fuzzy_dating = checkbox_to_value(fuzzy_dating)
        sickrage.app.config.gui.trim_zero = checkbox_to_value(trim_zero)

        sickrage.app.config.general.allowed_video_file_exts = ','.join([x.lower() for x in allowed_video_file_exts.split(',')])

        sickrage.app.config.general.strip_special_file_bits = checkbox_to_value(strip_special_file_bits)

        sickrage.app.config.general.web_root = web_root
        sickrage.app.config.general.web_host = web_host

        sickrage.app.config.general.ip_whitelist_enabled = checkbox_to_value(ip_whitelist_enabled)
        sickrage.app.config.general.ip_whitelist_localhost_enabled = checkbox_to_value(ip_whitelist_localhost_enabled)
        sickrage.app.config.general.ip_whitelist = ip_whitelist

        if web_auth_method == 'sso_auth':
            auth_method_changed = not sickrage.app.config.general.sso_auth_enabled
            sickrage.app.config.general.sso_auth_enabled = True
            sickrage.app.config.general.local_auth_enabled = False
        else:
            auth_method_changed = not sickrage.app.config.general.local_auth_enabled
            sickrage.app.config.general.sso_auth_enabled = False
            sickrage.app.config.general.local_auth_enabled = True
            sickrage.app.config.user.username = web_username
            sickrage.app.config.user.password = web_password

        sickrage.app.config.general.enable_sickrage_api = checkbox_to_value(enable_sickrage_api)

        # change_web_external_port(web_external_port)

        if date_preset:
            sickrage.app.config.gui.date_preset = date_preset

        if series_provider_default:
            sickrage.app.config.general.series_provider_default = SeriesProviderID[series_provider_default]

        if series_provider_timeout:
            sickrage.app.config.general.series_provider_timeout = try_int(series_provider_timeout)

        if time_preset:
            sickrage.app.config.gui.time_preset_w_seconds = time_preset
            sickrage.app.config.gui.time_preset = sickrage.app.config.gui.time_preset_w_seconds.replace(":%S", "")

        sickrage.app.config.gui.timezone_display = TimezoneDisplay[timezone_display]

        sickrage.app.config.general.api_v1_key = api_key

        sickrage.app.config.general.enable_https = checkbox_to_value(enable_https)

        if not change_https_cert(https_cert):
            results += ["Unable to create directory " + os.path.normpath(https_cert) + ", https cert directory not changed."]

        if not change_https_key(https_key):
            results += ["Unable to create directory " + os.path.normpath(https_key) + ", https key directory not changed."]

        sickrage.app.config.general.handle_reverse_proxy = checkbox_to_value(handle_reverse_proxy)

        sickrage.app.config.gui.theme_name = UITheme[theme_name]

        sickrage.app.config.general.default_page = DefaultHomePage[default_page]

        sickrage.app.config.general.max_queue_workers = try_int(max_queue_workers)

        sickrage.app.config.save()

        if auth_method_changed:
            return self.redirect('/logout')

        if len(results) > 0:
            [sickrage.app.log.error(x) for x in results]
            sickrage.app.alerts.error(_('Error(s) Saving Configuration'), '<br>\n'.join(results))
        else:
            sickrage.app.alerts.message(_('[GENERAL] Configuration Saved to Database'))

        return self.redirect("/config/general/")
