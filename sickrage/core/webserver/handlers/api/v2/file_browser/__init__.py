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

from sickrage.core.webserver.handlers.api import APIBaseHandler


class ApiV2FileBrowserHandler(APIBaseHandler):
    def get(self):
        path = self.get_argument('path', None)
        include_files = self.get_argument('includeFiles', None)

        return self.write_json(self.get_path(path, bool(include_files)))

    def get_path(self, path, include_files=False):
        entries = {
            'currentPath': '',
            'previousPath': '',
            'folders': [],
            'files': []
        }

        if not path:
            if os.name == 'nt':
                entries['currentPath'] = 'root'
                entries['previousPath'] = 'root'
                for drive_letter in self.get_win_drives():
                    drive_letter_path = drive_letter + ':\\'
                    entries['folders'].append({
                        'name': drive_letter_path,
                        'path': drive_letter_path
                    })
                return entries
            else:
                path = '/'

        # fix up the path and find the parent
        path = os.path.abspath(os.path.normpath(path))
        parent_path = os.path.dirname(path)

        # if we're at the root then the next step is the meta-node showing our drive letters
        if path == parent_path and os.name == 'nt':
            parent_path = ''

        entries['currentPath'] = path
        entries['previousPath'] = parent_path

        for (root, folders, files) in os.walk(path):
            for folder in folders:
                entries['folders'].append({
                    'name': folder,
                    'path': os.path.join(root, folder)
                })

            if include_files:
                for file in files:
                    entries['files'].append({
                        'name': file,
                        'path': os.path.join(root, file)
                    })

            break

        return entries

    def get_win_drives(self):
        assert os.name == 'nt'
        from ctypes import windll

        drives = []
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in map(chr, range(ord('A'), ord('Z') + 1)):
            if bitmask & 1:
                drives.append(letter)
            bitmask >>= 1

        return drives
