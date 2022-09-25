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
from sickrage.core.config.helpers import change_auto_backup_freq
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

        return final_result


class ConfigRestoreHandler(BaseHandler):
    @authenticated
    def get(self, *args, **kwargs):
        backup_file = self.get_argument('backupFile')
        restore_main_database = self.get_argument('restore_main_database')
        restore_config_database = self.get_argument('restore_config_database')
        restore_cache_database = self.get_argument('restore_cache_database')
        restore_image_cache = self.get_argument('restore_image_cache')

        final_result = ''

        if backup_file:
            source = backup_file
            target_dir = os.path.join(sickrage.app.data_dir, 'restore')

            restore_main_database = checkbox_to_value(restore_main_database)
            restore_config_database = checkbox_to_value(restore_config_database)
            restore_cache_database = checkbox_to_value(restore_cache_database)
            restore_image_cache = checkbox_to_value(restore_image_cache)

            if restore_config_zip(source, target_dir, restore_main_database, restore_config_database, restore_cache_database, restore_image_cache):
                final_result += _("Successfully extracted restore files to " + target_dir)
                final_result += _("<br>Restart sickrage to complete the restore.")
            else:
                final_result += _("Restore FAILED")
        else:
            final_result += _("You need to select a backup file to restore!")

        final_result += "<br>\n"

        return final_result


class SaveBackupRestoreHandler(BaseHandler):
    @authenticated
    def post(self, *args, **kwargs):
        backup_dir = self.get_argument('backupDir')
        auto_backup_enable = self.get_argument('auto_backup_enable', False)
        auto_backup_freq = self.get_argument('auto_backup_freq')
        auto_backup_keep_num = self.get_argument('auto_backup_keep_num')

        results = []

        sickrage.app.config.general.auto_backup_dir = backup_dir
        sickrage.app.config.general.auto_backup_enable = checkbox_to_value(auto_backup_enable)
        sickrage.app.config.general.auto_backup_keep_num = int(auto_backup_keep_num)

        change_auto_backup_freq(auto_backup_freq)

        sickrage.app.config.save()

        if len(results) > 0:
            [sickrage.app.log.error(x) for x in results]
            sickrage.app.alerts.error(_('Error(s) Saving Configuration'), '<br>\n'.join(results))
        else:
            sickrage.app.alerts.message(_('[BACKUP] Configuration Saved to Database'))

        return self.redirect("/config/backuprestore/")
