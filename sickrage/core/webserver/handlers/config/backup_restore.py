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
from sickrage.core.helpers import backup_app_data, checkbox_to_value, restore_config_zip
from sickrage.core.webserver import ConfigWebHandler
from sickrage.core.webserver.handlers.base import BaseHandler


class ConfigBackupRestoreHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        return self.render('config/backup_restore.mako',
                           submenu=ConfigWebHandler.menu,
                           title=_('Config - Backup/Restore'),
                           header=_('Backup/Restore'),
                           topmenu='config',
                           controller='config',
                           action='backup_restore')


class ConfigBackupHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        backup_dir = self.get_argument('backupDir')

        final_result = ''

        if backup_dir:
            if backup_app_data(backup_dir):
                final_result += _("Backup SUCCESSFUL")
            else:
                final_result += _("Backup FAILED!")
        else:
            final_result += _("You need to choose a folder to save your backup to first!")

        final_result += "<br>\n"

        return self.write(final_result)


class ConfigRestoreHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        backup_file = self.get_argument('backupFile')
        restore_database = self.get_argument('restore_database')
        restore_config = self.get_argument('restore_config')
        restore_cache = self.get_argument('restore_cache')

        final_result = ''

        if backup_file:
            source = backup_file
            target_dir = os.path.join(sickrage.app.data_dir, 'restore')

            restore_database = checkbox_to_value(restore_database)
            restore_config = checkbox_to_value(restore_config)
            restore_cache = checkbox_to_value(restore_cache)

            if restore_config_zip(source, target_dir, restore_database, restore_config, restore_cache):
                final_result += _("Successfully extracted restore files to " + target_dir)
                final_result += _("<br>Restart sickrage to complete the restore.")
            else:
                final_result += _("Restore FAILED")
        else:
            final_result += _("You need to select a backup file to restore!")

        final_result += "<br>\n"

        return self.write(final_result)


class SaveBackupRestoreHandler(BaseHandler):
    @authenticated
    def post(self, *args, **kwargs):
        return self.redirect("/config/backuprestore/")
