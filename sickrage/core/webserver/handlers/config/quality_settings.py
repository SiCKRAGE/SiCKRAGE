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
from sickrage.core.common import Quality
from sickrage.core.webserver import ConfigHandler
from sickrage.core.webserver.handlers.base import BaseHandler


class ConfigQualitySettingsHandler(BaseHandler, ABC):
    @authenticated
    async def get(self, *args, **kwargs):
        await self.run_in_executor(self.handle_get)

    def handle_get(self):
        return self.render('config/quality_settings.mako',
                           submenu=ConfigHandler.menu,
                           title=_('Config - Quality Settings'),
                           header=_('Quality Settings'),
                           topmenu='config',
                           controller='config',
                           action='quality_settings')


class SaveQualitiesHandler(BaseHandler, ABC):
    @authenticated
    async def post(self, *args, **kwargs):
        await self.run_in_executor(self.handle_post)

    def handle_post(self):
        quality_sizes = {
            Quality.UNKNOWN: int(self.get_argument(str(Quality.UNKNOWN))),
            Quality.SDTV: int(self.get_argument(str(Quality.SDTV))),
            Quality.SDDVD: int(self.get_argument(str(Quality.SDDVD))),
            Quality.HDTV: int(self.get_argument(str(Quality.HDTV))),
            Quality.RAWHDTV: int(self.get_argument(str(Quality.RAWHDTV))),
            Quality.FULLHDTV: int(self.get_argument(str(Quality.FULLHDTV))),
            Quality.HDWEBDL: int(self.get_argument(str(Quality.HDWEBDL))),
            Quality.FULLHDWEBDL: int(self.get_argument(str(Quality.FULLHDWEBDL))),
            Quality.HDBLURAY: int(self.get_argument(str(Quality.HDBLURAY))),
            Quality.FULLHDBLURAY: int(self.get_argument(str(Quality.FULLHDBLURAY))),
            Quality.UHD_4K_TV: int(self.get_argument(str(Quality.UHD_4K_TV))),
            Quality.UHD_4K_WEBDL: int(self.get_argument(str(Quality.UHD_4K_WEBDL))),
            Quality.UHD_4K_BLURAY: int(self.get_argument(str(Quality.UHD_4K_BLURAY))),
            Quality.UHD_8K_TV: int(self.get_argument(str(Quality.UHD_8K_TV))),
            Quality.UHD_8K_WEBDL: int(self.get_argument(str(Quality.UHD_8K_WEBDL))),
            Quality.UHD_8K_BLURAY: int(self.get_argument(str(Quality.UHD_8K_BLURAY))),
        }

        sickrage.app.config.quality_sizes.update(quality_sizes)

        sickrage.app.config.save()

        sickrage.app.alerts.message(_('[QUALITY SETTINGS] Configuration Encrypted and Saved to disk'))

        return self.redirect("/config/qualitySettings/")
