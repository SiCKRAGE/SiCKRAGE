import sickrage
from sickrage.core.helpers import backup_app_data


class AutoBackup(object):
    def __init__(self, *args, **kwargs):
        self.name = "AUTO-BACKUP"

    def task(self):
        if not sickrage.app.config.general.auto_backup_enable:
            return

        sickrage.app.log.info("Performing automatic backup of SiCKRAGE")
        backup_app_data(sickrage.app.config.general.auto_backup_dir, backup_type="auto", keep_num=sickrage.app.config.general.auto_backup_keep_num)
        sickrage.app.log.info("Finished automatic backup of SiCKRAGE")