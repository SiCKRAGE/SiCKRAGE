#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#
#  This file is part of SiCKRAGE.
#
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.

import os
from abc import ABC

from tornado.httpclient import AsyncHTTPClient
from tornado.httputil import url_concat
from tornado.web import authenticated

import sickrage
from sickrage.core.helpers import checkbox_to_value
from sickrage.core.nameparser import validator
from sickrage.core.webserver import ConfigHandler
from sickrage.core.webserver.handlers.base import BaseHandler


class ConfigPostProcessingHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        return self.render(
            "/config/postprocessing.mako",
            submenu=ConfigHandler.menu,
            title=_('Config - Post Processing'),
            header=_('Post Processing'),
            topmenu='config',
            controller='config',
            action='postprocessing'
        )


class SavePostProcessingHandler(BaseHandler, ABC):
    @authenticated
    async def post(self, *args, **kwargs):
        naming_pattern = self.get_body_argument('naming_pattern', None)
        naming_multi_ep = self.get_body_argument('naming_multi_ep', None)
        kodi_data = self.get_body_argument('kodi_data', None)
        kodi_12plus_data = self.get_body_argument('kodi_12plus_data', None)
        mediabrowser_data = self.get_body_argument('mediabrowser_data', None)
        sony_ps3_data = self.get_body_argument('sony_ps3_data', None)
        wdtv_data = self.get_body_argument('wdtv_data', None)
        tivo_data = self.get_body_argument('tivo_data', None)
        mede8er_data = self.get_body_argument('mede8er_data', None)
        keep_processed_dir = self.get_body_argument('keep_processed_dir', None)
        process_method = self.get_body_argument('process_method', None)
        del_rar_contents = self.get_body_argument('del_rar_contents', None)
        process_automatically = self.get_body_argument('process_automatically', None)
        no_delete = self.get_body_argument('no_delete', None)
        rename_episodes = self.get_body_argument('rename_episodes', None)
        airdate_episodes = self.get_body_argument('airdate_episodes', None)
        file_timestamp_timezone = self.get_body_argument('file_timestamp_timezone', None)
        unpack = self.get_body_argument('unpack', None)
        move_associated_files = self.get_body_argument('move_associated_files', None)
        sync_files = self.get_body_argument('sync_files', None)
        postpone_if_sync_files = self.get_body_argument('postpone_if_sync_files', None)
        nfo_rename = self.get_body_argument('nfo_rename', None)
        tv_download_dir = self.get_body_argument('tv_download_dir', None)
        naming_custom_abd = self.get_body_argument('naming_custom_abd', None)
        naming_anime = self.get_body_argument('naming_anime', None)
        create_missing_show_dirs = self.get_body_argument('create_missing_show_dirs', None)
        add_shows_wo_dir = self.get_body_argument('add_shows_wo_dir', None)
        naming_abd_pattern = self.get_body_argument('naming_abd_pattern', None)
        naming_strip_year = self.get_body_argument('naming_strip_year', None)
        delete_failed = self.get_body_argument('delete_failed', None)
        extra_scripts = self.get_body_argument('extra_scripts', None)
        naming_custom_sports = self.get_body_argument('naming_custom_sports', None)
        naming_sports_pattern = self.get_body_argument('naming_sports_pattern', None)
        naming_custom_anime = self.get_body_argument('naming_custom_anime', None)
        naming_anime_pattern = self.get_body_argument('naming_anime_pattern', None)
        naming_anime_multi_ep = self.get_body_argument('naming_anime_multi_ep', None)
        autopostprocessor_frequency = self.get_body_argument('autopostprocessor_frequency', None)
        delete_non_associated_files = self.get_body_argument('delete_non_associated_files', None)
        allowed_extensions = self.get_body_argument('allowed_extensions', None)
        processor_follow_symlinks = self.get_body_argument('processor_follow_symlinks', None)
        unpack_dir = self.get_body_argument('unpack_dir', None)

        results = []

        if not sickrage.app.config.change_tv_download_dir(tv_download_dir):
            results += [_("Unable to create directory ") + os.path.normpath(tv_download_dir) + _(", dir not changed.")]

        sickrage.app.config.change_autopostprocessor_freq(autopostprocessor_frequency)
        sickrage.app.config.process_automatically = checkbox_to_value(process_automatically)

        if unpack:
            response = await AsyncHTTPClient().fetch(self.get_url("/config/postProcessing/isRarSupported"))
            if response.body != "not supported":
                sickrage.app.config.unpack = checkbox_to_value(unpack)
                sickrage.app.config.unpack_dir = unpack_dir
            else:
                sickrage.app.config.unpack = 0
                results.append(_("Unpacking Not Supported, disabling unpack setting"))
        else:
            sickrage.app.config.unpack = checkbox_to_value(unpack)

        sickrage.app.config.no_delete = checkbox_to_value(no_delete)
        sickrage.app.config.keep_processed_dir = checkbox_to_value(keep_processed_dir)
        sickrage.app.config.create_missing_show_dirs = checkbox_to_value(create_missing_show_dirs)
        sickrage.app.config.add_shows_wo_dir = checkbox_to_value(add_shows_wo_dir)
        sickrage.app.config.process_method = process_method
        sickrage.app.config.delrarcontents = checkbox_to_value(del_rar_contents)
        sickrage.app.config.extra_scripts = [x.strip() for x in extra_scripts.split('|') if x.strip()]
        sickrage.app.config.rename_episodes = checkbox_to_value(rename_episodes)
        sickrage.app.config.airdate_episodes = checkbox_to_value(airdate_episodes)
        sickrage.app.config.file_timestamp_timezone = file_timestamp_timezone
        sickrage.app.config.move_associated_files = checkbox_to_value(move_associated_files)
        sickrage.app.config.sync_files = sync_files
        sickrage.app.config.postpone_if_sync_files = checkbox_to_value(postpone_if_sync_files)
        sickrage.app.config.allowed_extensions = ','.join(
            {x.strip() for x in allowed_extensions.split(',') if x.strip()})
        sickrage.app.config.naming_custom_abd = checkbox_to_value(naming_custom_abd)
        sickrage.app.config.naming_custom_sports = checkbox_to_value(naming_custom_sports)
        sickrage.app.config.naming_custom_anime = checkbox_to_value(naming_custom_anime)
        sickrage.app.config.naming_strip_year = checkbox_to_value(naming_strip_year)
        sickrage.app.config.delete_failed = checkbox_to_value(delete_failed)
        sickrage.app.config.nfo_rename = checkbox_to_value(nfo_rename)
        sickrage.app.config.delete_non_associated_files = checkbox_to_value(delete_non_associated_files)
        sickrage.app.config.processor_follow_symlinks = checkbox_to_value(processor_follow_symlinks)

        response = await AsyncHTTPClient().fetch(url_concat(self.get_url("/config/postProcessing/isNamingValid"),
                                                            dict(pattern=naming_pattern, multi=naming_multi_ep)))
        if response.body != "invalid":
            sickrage.app.config.naming_pattern = naming_pattern
            sickrage.app.config.naming_multi_ep = int(naming_multi_ep)
            sickrage.app.config.naming_force_folders = validator.check_force_season_folders()
        else:
            results.append(_("You tried saving an invalid naming config, not saving your naming settings"))

        response = await AsyncHTTPClient().fetch(url_concat(self.get_url("/config/postProcessing/isNamingValid"),
                                                            dict(pattern=naming_anime_pattern,
                                                                 multi=naming_anime_multi_ep, anime_type=naming_anime)))
        if response.body != "invalid":
            sickrage.app.config.naming_anime_pattern = naming_anime_pattern
            sickrage.app.config.naming_anime_multi_ep = int(naming_anime_multi_ep)
            sickrage.app.config.naming_anime = int(naming_anime)
        else:
            results.append(_("You tried saving an invalid anime naming config, not saving your naming settings"))

        response = await AsyncHTTPClient().fetch(url_concat(self.get_url("/config/postProcessing/isNamingValid"),
                                                            dict(pattern=naming_abd_pattern, abd=True)))
        if response.body != "invalid":
            sickrage.app.config.naming_abd_pattern = naming_abd_pattern
        else:
            results.append(_("You tried saving an invalid air-by-date naming config, not saving your air-by-date "
                             "settings"))

        response = await AsyncHTTPClient().fetch(url_concat(self.get_url("/config/postProcessing/isNamingValid"),
                                                            dict(pattern=naming_sports_pattern, multi=naming_multi_ep,
                                                                 sports=True)))
        if response.body != "invalid":
            sickrage.app.config.naming_sports_pattern = naming_sports_pattern
        else:
            results.append(_("You tried saving an invalid sports naming config, not saving your sports settings"))

        sickrage.app.metadata_providers['kodi'].set_config(kodi_data)
        sickrage.app.metadata_providers['kodi_12plus'].set_config(kodi_12plus_data)
        sickrage.app.metadata_providers['mediabrowser'].set_config(mediabrowser_data)
        sickrage.app.metadata_providers['sony_ps3'].set_config(sony_ps3_data)
        sickrage.app.metadata_providers['wdtv'].set_config(wdtv_data)
        sickrage.app.metadata_providers['tivo'].set_config(tivo_data)
        sickrage.app.metadata_providers['mede8er'].set_config(mede8er_data)

        sickrage.app.config.save()

        if len(results) > 0:
            [sickrage.app.log.warning(x) for x in results]
            sickrage.app.alerts.error(_('Error(s) Saving Configuration'), '<br>\n'.join(results))
        else:
            sickrage.app.alerts.message(_('[POST-PROCESSING] Configuration Encrypted and Saved to disk'))

        return self.redirect("/config/postProcessing/")


class TestNamingHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        pattern = self.get_query_argument('pattern', None)
        multi = self.get_query_argument('multi', None)
        abd = self.get_query_argument('abd', None)
        sports = self.get_query_argument('sports', None)
        anime_type = self.get_query_argument('anime_type', None)

        if multi is not None:
            multi = int(multi)

        if anime_type is not None:
            anime_type = int(anime_type)

        result = validator.test_name(pattern, multi, abd, sports, anime_type)

        result = os.path.join(result['dir'], result['name'])

        return self.write(result)


class IsNamingValidHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        pattern = self.get_query_argument('pattern', None)
        multi = self.get_query_argument('multi', None)
        abd = self.get_query_argument('abd', None)
        sports = self.get_query_argument('sports', None)
        anime_type = self.get_query_argument('anime_type', None)

        if pattern is None:
            return self.write('invalid')

        if multi is not None:
            multi = int(multi)

        if anime_type is not None:
            anime_type = int(anime_type)

        # air by date shows just need one check, we don't need to worry about season folders
        if abd:
            is_valid = validator.check_valid_abd_naming(pattern)
            require_season_folders = False

        # sport shows just need one check, we don't need to worry about season folders
        elif sports:
            is_valid = validator.check_valid_sports_naming(pattern)
            require_season_folders = False

        else:
            # check validity of single and multi ep cases for the whole path
            is_valid = validator.check_valid_naming(pattern, multi, anime_type)

            # check validity of single and multi ep cases for only the file name
            require_season_folders = validator.check_force_season_folders(pattern, multi, anime_type)

        if is_valid and not require_season_folders:
            return self.write('valid')
        elif is_valid and require_season_folders:
            return self.write('seasonfolders')
        else:
            return self.write('invalid')


class IsRarSupportedHandler(BaseHandler, ABC):
    @authenticated
    def get(self, *args, **kwargs):
        """
        Test Packing Support:
            - Simulating in memory rar extraction on test.rar file
        """

        check = sickrage.app.config.change_unrar_tool(sickrage.app.config.unrar_tool,
                                                      sickrage.app.config.unrar_alt_tool)

        if not check:
            sickrage.app.log.warning('Looks like unrar is not installed, check failed')
        return self.write(('not supported', 'supported')[check])
