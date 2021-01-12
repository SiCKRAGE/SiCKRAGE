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

from tornado.escape import json_encode
from tornado.web import authenticated

from sickrage.core.helpers.browser import foldersAtPath
from sickrage.core.webserver.handlers.base import BaseHandler


class WebFileBrowserHandler(BaseHandler):
    def initialize(self):
        self.set_header('Content-Type', 'application/json')

    @authenticated
    def get(self, *args, **kwargs):
        path = self.get_argument('path', '')
        include_files = self.get_argument('includeFiles', None)
        file_types = self.get_argument('fileTypes', '')

        return self.write(json_encode(foldersAtPath(path, True, bool(int(include_files) if include_files else False), file_types.split(','))))


class WebFileBrowserCompleteHandler(BaseHandler):
    def initialize(self):
        self.set_header('Content-Type', 'application/json')

    @authenticated
    def get(self, *args, **kwargs):
        term = self.get_argument('term')
        include_files = self.get_argument('includeFiles', None)
        file_types = self.get_argument('fileTypes', '')

        return self.write(json_encode([entry['path'] for entry in foldersAtPath(
            os.path.dirname(term),
            includeFiles=bool(int(include_files) if include_files else False),
            fileTypes=file_types.split(',')
        ) if 'path' in entry]))
