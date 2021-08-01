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
from sickrage.core.config.helpers import change_tv_download_dir, change_auto_postprocessor_freq, change_unrar_tool
from sickrage.core.enums import FileTimestampTimezone, MultiEpNaming, ProcessMethod
from sickrage.core.helpers import checkbox_to_value
from sickrage.core.nameparser import validator
from sickrage.core.webserver import ConfigWebHandler
from sickrage.core.webserver.handlers.base import BaseHandler


def is_naming_pattern_valid(pattern=None, multi=None, abd=None, sports=None, anime_type=None):
    if pattern is None:
        return 'invalid'

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
        return 'valid'
    elif is_valid and require_season_folders:
        return 'seasonfolders'
    else:
        return 'invalid'


def is_rar_supported():
    """
    Test Packing Support:
        - Simulating in memory rar extraction on test.rar file
    """

    check = change_unrar_tool(sickrage.app.unrar_tool)

    if not check:
        sickrage.app.log.warning('Looks like unrar is not installed, check failed')

    return ('not supported', 'supported')[check]


class ConfigPostProcessingHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        return self.render('config/postprocessing.mako',
                           submenu=ConfigWebHandler.menu,
                           title=_('Config - Post Processing'),
                           header=_('Post Processing'),
                           topmenu='config',
                           controller='config',
                           action='postprocessing')


class SavePostProcessingHandler(BaseHandler):
    @authenticated
    def post(self, *args, **kwargs):
        naming_pattern = self.get_argument('naming_pattern', '')
        naming_multi_ep = self.get_argument('naming_multi_ep', '')
        kodi_data = self.get_argument('kodi_data', '')
        kodi_12plus_data = self.get_argument('kodi_12plus_data', '')
        mediabrowser_data = self.get_argument('mediabrowser_data', '')
        sony_ps3_data = self.get_argument('sony_ps3_data', '')
        wdtv_data = self.get_argument('wdtv_data', '')
        tivo_data = self.get_argument('tivo_data', '')
        mede8er_data = self.get_argument('mede8er_data', '')
        keep_processed_dir = self.get_argument('keep_processed_dir', '')
        process_method = self.get_argument('process_method', '')
        del_rar_contents = self.get_argument('del_rar_contents', '')
        process_automatically = self.get_argument('process_automatically', '')
        no_delete = self.get_argument('no_delete', '')
        rename_episodes = self.get_argument('rename_episodes', '')
        airdate_episodes = self.get_argument('airdate_episodes', '')
        file_timestamp_timezone = self.get_argument('file_timestamp_timezone', '')
        unpack = self.get_argument('unpack', '')
        move_associated_files = self.get_argument('move_associated_files', '')
        sync_files = self.get_argument('sync_files', '')
        postpone_if_sync_files = self.get_argument('postpone_if_sync_files', '')
        nfo_rename = self.get_argument('nfo_rename', '')
        tv_download_dir = self.get_argument('tv_download_dir', '')
        naming_custom_abd = self.get_argument('naming_custom_abd', '')
        naming_anime = self.get_argument('naming_anime', '')
        create_missing_show_dirs = self.get_argument('create_missing_show_dirs', '')
        add_shows_wo_dir = self.get_argument('add_shows_wo_dir', '')
        naming_abd_pattern = self.get_argument('naming_abd_pattern', '')
        naming_strip_year = self.get_argument('naming_strip_year', '')
        delete_failed = self.get_argument('delete_failed', '')
        extra_scripts = self.get_argument('extra_scripts', '')
        naming_custom_sports = self.get_argument('naming_custom_sports', '')
        naming_sports_pattern = self.get_argument('naming_sports_pattern', '')
        naming_custom_anime = self.get_argument('naming_custom_anime', '')
        naming_anime_pattern = self.get_argument('naming_anime_pattern', '')
        naming_anime_multi_ep = self.get_argument('naming_anime_multi_ep', '')
        auto_postprocessor_frequency = self.get_argument('auto_postprocessor_frequency', '')
        delete_non_associated_files = self.get_argument('delete_non_associated_files', '')
        allowed_extensions = self.get_argument('allowed_extensions', '')
        processor_follow_symlinks = self.get_argument('processor_follow_symlinks', '')
        unpack_dir = self.get_argument('unpack_dir', '')

        results = []

        if not change_tv_download_dir(tv_download_dir):
            results += [_("Unable to create directory ") + os.path.normpath(tv_download_dir) + _(", dir not changed.")]

        change_auto_postprocessor_freq(auto_postprocessor_frequency)
        sickrage.app.config.general.process_automatically = checkbox_to_value(process_automatically)

        if unpack:
            if is_rar_supported() != "not supported":
                sickrage.app.config.general.unpack = checkbox_to_value(unpack)
                sickrage.app.config.general.unpack_dir = unpack_dir
            else:
                sickrage.app.config.general.unpack = 0
                results.append(_("Unpacking Not Supported, disabling unpack setting"))
        else:
            sickrage.app.config.general.unpack = checkbox_to_value(unpack)

        sickrage.app.config.general.no_delete = checkbox_to_value(no_delete)
        sickrage.app.config.general.keep_processed_dir = checkbox_to_value(keep_processed_dir)
        sickrage.app.config.general.create_missing_show_dirs = checkbox_to_value(create_missing_show_dirs)
        sickrage.app.config.general.add_shows_wo_dir = checkbox_to_value(add_shows_wo_dir)
        sickrage.app.config.general.process_method = ProcessMethod[process_method]
        sickrage.app.config.general.del_rar_contents = checkbox_to_value(del_rar_contents)
        sickrage.app.config.general.extra_scripts = ','.join([x.strip() for x in extra_scripts.split('|') if x.strip()])
        sickrage.app.config.general.rename_episodes = checkbox_to_value(rename_episodes)
        sickrage.app.config.general.airdate_episodes = checkbox_to_value(airdate_episodes)
        sickrage.app.config.general.file_timestamp_timezone = FileTimestampTimezone[file_timestamp_timezone]
        sickrage.app.config.general.move_associated_files = checkbox_to_value(move_associated_files)
        sickrage.app.config.general.sync_files = sync_files
        sickrage.app.config.general.postpone_if_sync_files = checkbox_to_value(postpone_if_sync_files)
        sickrage.app.config.general.allowed_extensions = ','.join({x.strip() for x in allowed_extensions.split(',') if x.strip()})
        sickrage.app.config.general.naming_custom_abd = checkbox_to_value(naming_custom_abd)
        sickrage.app.config.general.naming_custom_sports = checkbox_to_value(naming_custom_sports)
        sickrage.app.config.general.naming_custom_anime = checkbox_to_value(naming_custom_anime)
        sickrage.app.config.general.naming_strip_year = checkbox_to_value(naming_strip_year)
        sickrage.app.config.failed_downloads.enable = checkbox_to_value(delete_failed)
        sickrage.app.config.general.nfo_rename = checkbox_to_value(nfo_rename)
        sickrage.app.config.general.delete_non_associated_files = checkbox_to_value(delete_non_associated_files)
        sickrage.app.config.general.processor_follow_symlinks = checkbox_to_value(processor_follow_symlinks)

        if is_naming_pattern_valid(pattern=naming_pattern, multi=MultiEpNaming[naming_multi_ep]) != "invalid":
            sickrage.app.config.general.naming_pattern = naming_pattern
            sickrage.app.config.general.naming_multi_ep = MultiEpNaming[naming_multi_ep]
            sickrage.app.naming_force_folders = validator.check_force_season_folders()
        else:
            results.append(_("You tried saving an invalid naming config, not saving your naming settings"))

        if is_naming_pattern_valid(pattern=naming_anime_pattern, multi=MultiEpNaming[naming_anime_multi_ep], anime_type=naming_anime) != "invalid":
            sickrage.app.config.general.naming_anime_pattern = naming_anime_pattern
            sickrage.app.config.general.naming_anime_multi_ep = MultiEpNaming[naming_anime_multi_ep]
            sickrage.app.config.general.naming_anime = int(naming_anime)
        else:
            results.append(_("You tried saving an invalid anime naming config, not saving your naming settings"))

        if is_naming_pattern_valid(pattern=naming_abd_pattern, abd=True) != "invalid":
            sickrage.app.config.general.naming_abd_pattern = naming_abd_pattern
        else:
            results.append(_("You tried saving an invalid air-by-date naming config, not saving your air-by-date settings"))

        if is_naming_pattern_valid(pattern=naming_sports_pattern, multi=MultiEpNaming[naming_multi_ep], sports=True) != "invalid":
            sickrage.app.config.general.naming_sports_pattern = naming_sports_pattern
        else:
            results.append(_("You tried saving an invalid sports naming config, not saving your sports settings"))

        sickrage.app.metadata_providers['kodi'].config = kodi_data
        sickrage.app.metadata_providers['kodi_12plus'].config = kodi_12plus_data
        sickrage.app.metadata_providers['mediabrowser'].config = mediabrowser_data
        sickrage.app.metadata_providers['sony_ps3'].config = sony_ps3_data
        sickrage.app.metadata_providers['wdtv'].config = wdtv_data
        sickrage.app.metadata_providers['tivo'].config = tivo_data
        sickrage.app.metadata_providers['mede8er'].config = mede8er_data

        sickrage.app.config.save()

        if len(results) > 0:
            [sickrage.app.log.warning(x) for x in results]
            sickrage.app.alerts.error(_('Error(s) Saving Configuration'), '<br>\n'.join(results))
        else:
            sickrage.app.alerts.message(_('[POST-PROCESSING] Configuration Saved to Database'))

        return self.redirect("/config/postProcessing/")


class TestNamingHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        pattern = self.get_argument('pattern', None)
        multi = self.get_argument('multi', None)
        abd = self.get_argument('abd', None)
        sports = self.get_argument('sports', None)
        anime_type = self.get_argument('anime_type', None)

        if multi is not None:
            multi = MultiEpNaming[multi]

        if anime_type is not None:
            anime_type = int(anime_type)

        result = validator.test_name(pattern, multi, abd, sports, anime_type)

        result = os.path.join(result['dir'], result['name'])

        return result


class IsNamingPatternValidHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        pattern = self.get_argument('pattern', None)
        multi = self.get_argument('multi', None)
        abd = self.get_argument('abd', None)
        sports = self.get_argument('sports', None)
        anime_type = self.get_argument('anime_type', None)

        if multi:
            multi = MultiEpNaming[multi]

        if anime_type is not None:
            anime_type = int(anime_type)

        return is_naming_pattern_valid(pattern=pattern, multi=multi, abd=abd, sports=sports, anime_type=anime_type)


class IsRarSupportedHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        return is_rar_supported()
