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

from tornado.escape import json_encode
from tornado.web import authenticated

import sickrage
from sickrage.core.helpers import checkbox_to_value
from sickrage.core.webserver import ConfigHandler
from sickrage.core.webserver.handlers.base import BaseHandler
from sickrage.subtitles import Subtitles


class ConfigSubtitlesHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
        return self.render('config/subtitles.mako',
                           submenu=ConfigHandler.menu,
                           title=_('Config - Subtitles Settings'),
                           header=_('Subtitles Settings'),
                           topmenu='config',
                           controller='config',
                           action='subtitles')


class ConfigSubtitleGetCodeHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
        q = self.get_argument('q')

        codes = [{"id": code, "name": Subtitles().name_from_code(code)} for code in Subtitles().subtitle_code_filter()]
        codes = list(filter(lambda code: q.lower() in code['name'].lower(), codes))

        return self.write(json_encode(codes))


class ConfigSubtitlesWantedLanguagesHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
        codes = [{"id": code, "name": Subtitles().name_from_code(code)} for code in Subtitles().subtitle_code_filter()]
        codes = list(filter(lambda code: code['id'] in Subtitles().wanted_languages(), codes))

        return self.write(json_encode(codes))


class SaveSubtitlesHandler(BaseHandler, ABC):
    @authenticated
    async def post(self, *args, **kwargs):
        await self.run_in_executor(self.handle_post)

    def handle_post(self):
        use_subtitles = self.get_argument('use_subtitles', None)
        subtitles_dir = self.get_argument('subtitles_dir', None)
        service_order = self.get_argument('service_order', None)
        subtitles_history = self.get_argument('subtitles_history', None)
        subtitles_finder_frequency = self.get_argument('subtitles_finder_frequency', None)
        subtitles_multi = self.get_argument('subtitles_multi', None)
        embedded_subtitles_all = self.get_argument('embedded_subtitles_all', None)
        subtitles_extra_scripts = self.get_argument('subtitles_extra_scripts', '')
        subtitles_hearing_impaired = self.get_argument('subtitles_hearing_impaired', None)
        itasa_user = self.get_argument('itasa_user', None)
        itasa_pass = self.get_argument('itasa_pass', None)
        addic7ed_user = self.get_argument('addic7ed_user', None)
        addic7ed_pass = self.get_argument('addic7ed_pass', None)
        legendastv_user = self.get_argument('legendastv_user', None)
        legendastv_pass = self.get_argument('legendastv_pass', None)
        opensubtitles_user = self.get_argument('opensubtitles_user', None)
        opensubtitles_pass = self.get_argument('opensubtitles_pass', None)
        subtitles_languages = self.get_arguments('subtitles_languages[]')

        results = []

        sickrage.app.config.change_subtitle_searcher_freq(subtitles_finder_frequency)
        sickrage.app.config.use_subtitles = checkbox_to_value(use_subtitles)
        sickrage.app.config.subtitles_dir = subtitles_dir
        sickrage.app.config.subtitles_history = checkbox_to_value(subtitles_history)
        sickrage.app.config.embedded_subtitles_all = checkbox_to_value(embedded_subtitles_all)
        sickrage.app.config.subtitles_hearing_impaired = checkbox_to_value(subtitles_hearing_impaired)
        sickrage.app.config.subtitles_multi = checkbox_to_value(subtitles_multi)
        sickrage.app.config.subtitles_extra_scripts = [x.strip() for x in subtitles_extra_scripts.split('|') if x.strip()]

        # Subtitle languages
        sickrage.app.config.subtitles_languages = subtitles_languages or ['eng']

        # Subtitles services
        services_str_list = service_order.split()
        subtitles_services_list = []
        subtitles_services_enabled = []
        for curServiceStr in services_str_list:
            cur_service, cur_enabled = curServiceStr.split(':')
            subtitles_services_list.append(cur_service)
            subtitles_services_enabled.append(int(cur_enabled))

        sickrage.app.config.subtitles_services_list = subtitles_services_list
        sickrage.app.config.subtitles_services_enabled = subtitles_services_enabled

        sickrage.app.config.addic7ed_user = addic7ed_user or ''
        sickrage.app.config.addic7ed_pass = addic7ed_pass or ''
        sickrage.app.config.legendastv_user = legendastv_user or ''
        sickrage.app.config.legendastv_pass = legendastv_pass or ''
        sickrage.app.config.itasa_user = itasa_user or ''
        sickrage.app.config.itasa_pass = itasa_pass or ''
        sickrage.app.config.opensubtitles_user = opensubtitles_user or ''
        sickrage.app.config.opensubtitles_pass = opensubtitles_pass or ''

        sickrage.app.config.save()

        if len(results) > 0:
            [sickrage.app.log.error(x) for x in results]
            sickrage.app.alerts.error(_('Error(s) Saving Configuration'), '<br>\n'.join(results))
        else:
            sickrage.app.alerts.message(_('[SUBTITLES] Configuration Encrypted and Saved to disk'))

        return self.redirect("/config/subtitles/")
