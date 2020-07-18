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
from abc import ABC

from tornado.web import authenticated

import sickrage
from sickrage.core import common
from sickrage.core.common import Quality
from sickrage.core.helpers import generate_api_key, checkbox_to_value, try_int
from sickrage.core.webserver import ConfigHandler
from sickrage.core.webserver.handlers.base import BaseHandler


class ConfigGeneralHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
        return self.render('config/general.mako',
                           title=_('Config - General'),
                           header=_('General Configuration'),
                           topmenu='config',
                           submenu=ConfigHandler.menu,
                           controller='config',
                           action='general', )


class GenerateApiKeyHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
        return self.write(generate_api_key())


class SaveRootDirsHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
        sickrage.app.config.root_dirs = self.get_argument('rootDirString', '')
        sickrage.app.config.save()


class SaveAddShowDefaultsHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
        default_status = self.get_argument('defaultStatus', '5')
        any_qualities = self.get_argument('anyQualities', '')
        best_qualities = self.get_argument('bestQualities', '')
        default_flatten_folders = self.get_argument('defaultFlattenFolders', None)
        subtitles = self.get_argument('subtitles', None)
        anime = self.get_argument('anime', None)
        search_format = self.get_argument('search_format', None)
        default_status_after = self.get_argument('defaultStatusAfter', common.WANTED)
        scene = self.get_argument('scene', None)
        skip_downloaded = self.get_argument('skip_downloaded', None)
        add_show_year = self.get_argument('add_show_year', None)

        any_qualities = any_qualities.split(',') if len(any_qualities) else []
        best_qualities = best_qualities.split(',') if len(best_qualities) else []

        new_quality = Quality.combine_qualities(list(map(int, any_qualities)), list(map(int, best_qualities)))

        sickrage.app.config.status_default = int(default_status)
        sickrage.app.config.status_default_after = int(default_status_after)
        sickrage.app.config.quality_default = int(new_quality)

        sickrage.app.config.flatten_folders_default = not checkbox_to_value(default_flatten_folders)
        sickrage.app.config.subtitles_default = checkbox_to_value(subtitles)

        sickrage.app.config.anime_default = checkbox_to_value(anime)
        sickrage.app.config.search_format_default = int(search_format)
        sickrage.app.config.scene_default = checkbox_to_value(scene)
        sickrage.app.config.skip_downloaded_default = checkbox_to_value(skip_downloaded)
        sickrage.app.config.add_show_year_default = checkbox_to_value(add_show_year)

        sickrage.app.config.save()


class SaveGeneralHandler(BaseHandler, ABC):
    @authenticated
    async def post(self, *args, **kwargs):
        await self.run_in_executor(self.handle_post)

    def handle_post(self):
        log_nr = self.get_argument('log_nr', '5')
        log_size = self.get_argument('log_size', '1048576')
        web_port = self.get_argument('web_port', None)
        web_ipv6 = self.get_argument('web_ipv6', None)
        web_host = self.get_argument('web_host', None)
        trash_remove_show = self.get_argument('trash_remove_show', None)
        trash_rotate_logs = self.get_argument('trash_rotate_logs', None)
        update_frequency = self.get_argument('update_frequency', None)
        skip_removed_files = self.get_argument('skip_removed_files', None)
        indexerDefaultLang = self.get_argument('indexerDefaultLang', 'en')
        ep_default_deleted_status = self.get_argument('ep_default_deleted_status', None)
        launch_browser = self.get_argument('launch_browser', None)
        showupdate_hour = self.get_argument('showupdate_hour', '3')
        api_key = self.get_argument('api_key', None)
        indexer_default = self.get_argument('indexer_default', None)
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
        proxy_indexers = self.get_argument('proxy_indexers', None)
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
        indexer_timeout = self.get_argument('indexer_timeout', None)
        download_url = self.get_argument('download_url', None)
        theme_name = self.get_argument('theme_name', None)
        default_page = self.get_argument('default_page', None)
        git_username = self.get_argument('git_username', None)
        git_password = self.get_argument('git_password', None)
        git_autoissues = self.get_argument('git_autoissues', None)
        gui_language = self.get_argument('gui_language', None)
        display_all_seasons = self.get_argument('display_all_seasons', None)
        showupdate_stale = self.get_argument('showupdate_stale', None)
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

        # Language
        sickrage.app.config.change_gui_lang(gui_language)

        # Debug
        sickrage.app.config.debug = checkbox_to_value(debug)
        sickrage.app.log.set_level()

        # Misc
        sickrage.app.config.enable_upnp = checkbox_to_value(enable_upnp)
        sickrage.app.config.download_url = download_url
        sickrage.app.config.indexer_default_language = indexerDefaultLang
        sickrage.app.config.ep_default_deleted_status = ep_default_deleted_status
        sickrage.app.config.skip_removed_files = checkbox_to_value(skip_removed_files)
        sickrage.app.config.launch_browser = checkbox_to_value(launch_browser)
        sickrage.app.config.change_showupdate_hour(showupdate_hour)
        sickrage.app.config.change_version_notify(checkbox_to_value(version_notify))
        sickrage.app.config.auto_update = checkbox_to_value(auto_update)
        sickrage.app.config.notify_on_update = checkbox_to_value(notify_on_update)
        sickrage.app.config.backup_on_update = checkbox_to_value(backup_on_update)
        sickrage.app.config.notify_on_login = checkbox_to_value(notify_on_login)
        sickrage.app.config.showupdate_stale = checkbox_to_value(showupdate_stale)
        sickrage.app.config.log_nr = log_nr
        sickrage.app.config.log_size = log_size

        sickrage.app.config.trash_remove_show = checkbox_to_value(trash_remove_show)
        sickrage.app.config.trash_rotate_logs = checkbox_to_value(trash_rotate_logs)
        sickrage.app.config.change_updater_freq(update_frequency)
        sickrage.app.config.launch_browser = checkbox_to_value(launch_browser)
        sickrage.app.config.sort_article = checkbox_to_value(sort_article)
        sickrage.app.config.cpu_preset = cpu_preset
        sickrage.app.config.anon_redirect = anon_redirect
        sickrage.app.config.proxy_setting = proxy_setting
        sickrage.app.config.proxy_indexers = checkbox_to_value(proxy_indexers)
        sickrage.app.config.git_username = git_username
        sickrage.app.config.git_password = git_password
        sickrage.app.config.git_reset = 1
        sickrage.app.config.git_autoissues = checkbox_to_value(git_autoissues)
        sickrage.app.config.git_path = git_path
        sickrage.app.config.pip3_path = pip3_path
        sickrage.app.config.calendar_unprotected = checkbox_to_value(calendar_unprotected)
        sickrage.app.config.calendar_icons = checkbox_to_value(calendar_icons)
        sickrage.app.config.no_restart = checkbox_to_value(no_restart)

        sickrage.app.config.ssl_verify = checkbox_to_value(ssl_verify)
        sickrage.app.config.coming_eps_missed_range = try_int(coming_eps_missed_range, 7)
        sickrage.app.config.display_all_seasons = checkbox_to_value(display_all_seasons)

        sickrage.app.config.web_port = try_int(web_port)
        sickrage.app.config.web_ipv6 = checkbox_to_value(web_ipv6)

        sickrage.app.config.filter_row = checkbox_to_value(filter_row)
        sickrage.app.config.fuzzy_dating = checkbox_to_value(fuzzy_dating)
        sickrage.app.config.trim_zero = checkbox_to_value(trim_zero)

        sickrage.app.config.allowed_video_file_exts = [x.lower() for x in allowed_video_file_exts.split(',')]

        sickrage.app.config.strip_special_file_bits = checkbox_to_value(strip_special_file_bits)

        sickrage.app.config.web_root = web_root
        sickrage.app.config.web_host = web_host

        sickrage.app.config.ip_whitelist_enabled = checkbox_to_value(ip_whitelist_enabled)
        sickrage.app.config.ip_whitelist_localhost_enabled = checkbox_to_value(ip_whitelist_localhost_enabled)
        sickrage.app.config.ip_whitelist = ip_whitelist

        if web_auth_method == 'sso_auth':
            sickrage.app.config.sso_auth_enabled = True
            sickrage.app.config.local_auth_enabled = False
        else:
            sickrage.app.config.sso_auth_enabled = False
            sickrage.app.config.local_auth_enabled = True
            sickrage.app.config.web_username = web_username
            sickrage.app.config.web_password = web_password

        sickrage.app.config.enable_sickrage_api = checkbox_to_value(enable_sickrage_api)

        # sickrage.app.config.change_web_external_port(web_external_port)

        if date_preset:
            sickrage.app.config.date_preset = date_preset

        if indexer_default:
            sickrage.app.config.indexer_default = try_int(indexer_default)

        if indexer_timeout:
            sickrage.app.config.indexer_timeout = try_int(indexer_timeout)

        if time_preset:
            sickrage.app.config.time_preset_w_seconds = time_preset
            sickrage.app.config.time_preset = sickrage.app.config.time_preset_w_seconds.replace(":%S", "")

        sickrage.app.config.timezone_display = timezone_display

        sickrage.app.config.api_key = api_key

        sickrage.app.config.enable_https = checkbox_to_value(enable_https)

        if not sickrage.app.config.change_https_cert(https_cert):
            results += [
                "Unable to create directory " + os.path.normpath(https_cert) + ", https cert directory not changed."]

        if not sickrage.app.config.change_https_key(https_key):
            results += [
                "Unable to create directory " + os.path.normpath(https_key) + ", https key directory not changed."]

        sickrage.app.config.handle_reverse_proxy = checkbox_to_value(handle_reverse_proxy)

        sickrage.app.config.theme_name = theme_name

        sickrage.app.config.default_page = default_page

        sickrage.app.config.max_queue_workers = try_int(max_queue_workers)

        sickrage.app.config.save()

        if len(results) > 0:
            [sickrage.app.log.error(x) for x in results]
            sickrage.app.alerts.error(_('Error(s) Saving Configuration'), '<br>\n'.join(results))
        else:
            sickrage.app.alerts.message(_('[GENERAL] Configuration Encrypted and Saved to disk'))

        return self.redirect("/config/general/")
