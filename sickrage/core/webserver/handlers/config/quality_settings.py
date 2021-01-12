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
from sickrage.core.webserver import ConfigWebHandler
from sickrage.core.webserver.handlers.base import BaseHandler


class ConfigQualitySettingsHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        return self.render('config/quality_settings.mako',
                           submenu=ConfigWebHandler.menu,
                           title=_('Config - Quality Settings'),
                           header=_('Quality Settings'),
                           topmenu='config',
                           controller='config',
                           action='quality_settings')


class SaveQualitiesHandler(BaseHandler):
    @authenticated
    def post(self, *args, **kwargs):
        for quality in sickrage.app.config.quality_sizes.keys():
            quality_size_min = self.get_argument(f"{quality}_min")
            quality_size_max = self.get_argument(f"{quality}_max")
            sickrage.app.config.quality_sizes[quality].min_size = int(quality_size_min)
            sickrage.app.config.quality_sizes[quality].max_size = int(quality_size_max)

        sickrage.app.config.save()

        sickrage.app.alerts.message(_('[QUALITY SETTINGS] Configuration Saved to Database'))

        return self.redirect("/config/qualitySettings/")
