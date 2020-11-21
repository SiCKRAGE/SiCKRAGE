import os
from base64 import b64decode

from tornado.escape import json_encode

import sickrage

currentInfo = ''
percentDone = 0


class GoogleDrive(object):
    def __init__(self):
        self.reset_progress()

    def reset_progress(self):
        self.set_progress('Syncing', 0)

    def set_progress(self, current_info, percent_done):
        global currentInfo, percentDone
        currentInfo = current_info
        percentDone = percent_done

    @staticmethod
    def get_progress():
        return json_encode({'percent_done': percentDone, 'current_info': currentInfo})

    def walk_drive(self, folder_id):
        dirs, nondirs = {}, {}
        for item in sickrage.app.api.google.list_files(folder_id)['data']:
            if item['type'] == "application/vnd.google-apps.folder":
                dirs.update({str(item['id']): item['name']})
            else:
                nondirs.update({str(item['id']): item['name']})

        yield folder_id, dirs, nondirs

        for name in dirs.keys():
            for x in self.walk_drive(name):
                yield x

    def sync_remote(self):
        main_folder = 'appDataFolder'
        folder_id = sickrage.app.api.google.search_files(main_folder, sickrage.app.config.user.sub_id)['data']

        local_dirs = set()
        local_files = set()

        # sync local drive to google drive
        for root, dirs, files in os.walk(sickrage.app.data_dir):
            local_dirs.update(dirs)
            local_files.update(files)

            folder = root.replace(sickrage.app.data_dir, '{}/{}'.format(main_folder, sickrage.app.config.user.sub_id))
            folder = folder.replace('\\', '/')
            for f in files:
                self.set_progress('Syncing {} to Google Drive'.format(os.path.join(root, f)), 0)
                sickrage.app.api.google.upload(os.path.join(root, f), folder)

        # removing deleted local folders/files from google drive
        for drive_root, drive_folders, drive_files in self.walk_drive(folder_id):
            for folder_id, folder_name in drive_folders.items():
                if folder_name not in local_dirs:
                    sickrage.app.api.google.delete(folder_id)

            for file_id, file_name in drive_files.items():
                if file_name not in local_files:
                    sickrage.app.api.google.delete(file_id)

    def sync_local(self):
        main_folder = 'appDataFolder'
        folder_id = sickrage.app.api.google.search_files(main_folder, sickrage.app.config.user.sub_id)['data']

        for drive_root, drive_folders, drive_files in self.walk_drive(folder_id):
            folder = drive_root.replace(folder_id, sickrage.app.data_dir)
            folder = folder.replace('/', '\\')
            for file_id, name in drive_files.items():
                content = b64decode(sickrage.app.api.google.download(file_id)).strip()
