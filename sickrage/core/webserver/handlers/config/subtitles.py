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



from tornado.escape import json_encode
from tornado.web import authenticated

import sickrage
from sickrage.core.config.helpers import change_subtitle_searcher_freq
from sickrage.core.helpers import checkbox_to_value
from sickrage.core.webserver import ConfigWebHandler
from sickrage.core.webserver.handlers.base import BaseHandler
from sickrage.subtitles import Subtitles


class ConfigSubtitlesHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        return self.render('config/subtitles.mako',
                           submenu=ConfigWebHandler.menu,
                           title=_('Config - Subtitles Settings'),
                           header=_('Subtitles Settings'),
                           topmenu='config',
                           controller='config',
                           action='subtitles')


class ConfigSubtitleGetCodeHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        q = self.get_argument('q')

        codes = [{"id": code, "name": Subtitles().name_from_code(code)} for code in Subtitles().subtitle_code_filter()]
        codes = list(filter(lambda code: q.lower() in code['name'].lower(), codes))

        return json_encode(codes)


class ConfigSubtitlesWantedLanguagesHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        codes = [{"id": code, "name": Subtitles().name_from_code(code)} for code in Subtitles().subtitle_code_filter()]
        codes = list(filter(lambda code: code['id'] in Subtitles().wanted_languages(), codes))

        return json_encode(codes)


class SaveSubtitlesHandler(BaseHandler):
    @authenticated
    def post(self, *args, **kwargs):
        use_subtitles = self.get_argument('use_subtitles', None)
        subtitles_dir = self.get_argument('subtitles_dir', None)
        service_order = self.get_argument('service_order', None)
        subtitles_history = self.get_argument('subtitles_history', None)
        subtitles_finder_frequency = self.get_argument('subtitles_finder_frequency', None)
        subtitles_multi = self.get_argument('subtitles_multi', None)
        enable_embedded_subtitles = self.get_argument('enable_embedded_subtitles', None)
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

        change_subtitle_searcher_freq(subtitles_finder_frequency)

        sickrage.app.config.subtitles.enable = checkbox_to_value(use_subtitles)
        sickrage.app.config.subtitles.dir = subtitles_dir
        sickrage.app.config.subtitles.history = checkbox_to_value(subtitles_history)
        sickrage.app.config.subtitles.enable_embedded = checkbox_to_value(enable_embedded_subtitles)
        sickrage.app.config.subtitles.hearing_impaired = checkbox_to_value(subtitles_hearing_impaired)
        sickrage.app.config.subtitles.multi = checkbox_to_value(subtitles_multi)
        sickrage.app.config.subtitles.extra_scripts = subtitles_extra_scripts

        # Subtitle languages
        sickrage.app.config.subtitles.languages = ','.join(subtitles_languages) or 'eng'

        # Subtitles services
        services_str_list = service_order.split()
        subtitles_services_list = []
        subtitles_services_enabled = []
        for curServiceStr in services_str_list:
            cur_service, cur_enabled = curServiceStr.split(':')
            subtitles_services_list.append(cur_service)
            subtitles_services_enabled.append(cur_enabled)

        sickrage.app.config.subtitles.services_list = ','.join(subtitles_services_list)
        sickrage.app.config.subtitles.services_enabled = '|'.join(subtitles_services_enabled)

        sickrage.app.config.subtitles.addic7ed_user = addic7ed_user or ''
        sickrage.app.config.subtitles.addic7ed_pass = addic7ed_pass or ''
        sickrage.app.config.subtitles.legendastv_user = legendastv_user or ''
        sickrage.app.config.subtitles.legendastv_pass = legendastv_pass or ''
        sickrage.app.config.subtitles.itasa_user = itasa_user or ''
        sickrage.app.config.subtitles.itasa_pass = itasa_pass or ''
        sickrage.app.config.subtitles.opensubtitles_user = opensubtitles_user or ''
        sickrage.app.config.subtitles.opensubtitles_pass = opensubtitles_pass or ''

        sickrage.app.config.save()

        if len(results) > 0:
            [sickrage.app.log.error(x) for x in results]
            sickrage.app.alerts.error(_('Error(s) Saving Configuration'), '<br>\n'.join(results))
        else:
            sickrage.app.alerts.message(_('[SUBTITLES] Configuration Saved to Database'))

        return self.redirect("/config/subtitles/")
