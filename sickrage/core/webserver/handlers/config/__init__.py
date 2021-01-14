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
from sickrage.core.webserver.handlers.base import BaseHandler


class ConfigWebHandler(BaseHandler):
    menu = [
        {'title': _('Help and Info'), 'path': '/config/', 'icon': 'fas fa-info'},
        {'title': _('General'), 'path': '/config/general/', 'icon': 'fas fa-cogs'},
        {'title': _('Backup/Restore'), 'path': '/config/backuprestore/', 'icon': 'fas fa-upload'},
        {'title': _('Search Clients'), 'path': '/config/search/', 'icon': 'fas fa-binoculars'},
        {'title': _('Search Providers'), 'path': '/config/providers/', 'icon': 'fas fa-share-alt'},
        {'title': _('Subtitles Settings'), 'path': '/config/subtitles/', 'icon': 'fas fa-cc'},
        {'title': _('Quality Settings'), 'path': '/config/qualitySettings/', 'icon': 'fas fa-wrench'},
        {'title': _('Post Processing'), 'path': '/config/postProcessing/', 'icon': 'fas fa-refresh'},
        {'title': _('Notifications'), 'path': '/config/notifications/', 'icon': 'fas fa-bell'},
        {'title': _('Anime'), 'path': '/config/anime/', 'icon': 'fas fa-eye'},
    ]

    @authenticated
    def get(self, *args, **kwargs):
        return self.render('config/index.mako',
                           submenu=self.menu,
                           title=_('Configuration'),
                           header=_('Configuration'),
                           topmenu="config",
                           controller='config',
                           action='index')


class ConfigResetHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        sickrage.app.config.load(defaults=True)
        sickrage.app.alerts.message(_('Configuration Reset to Defaults'), os.path.join(sickrage.app.config_file))
        return self.redirect("/config/general")
