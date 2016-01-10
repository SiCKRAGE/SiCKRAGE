# This file is part of SickRage.
#
# URL: https://www.sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import os
from mimetypes import guess_type

import sickbeard
from sickbeard.helpers import findCertainShow
from sickrage.helper.exceptions import MultipleShowObjectsException

class GenericMedia(object):
    def __init__(self, indexer_id, media_format):
        """
        :param indexer_id: The indexer id of the show
        :param media_format: The media format of the show image
        """

        self.media_format = ('normal', 'thumb')[media_format in ('banner_thumb', 'poster_thumb', 'small')]

        try:
            self.indexer_id = int(indexer_id)
        except ValueError:
            self.indexer_id = 0

    def get_default_media_name(self):
        """
        :return: The name of the file to use as a fallback if the show media file is missing
        """

        return ''

    @property
    def get_media(self):
        """
        :return: The content of the desired media file
        """

        return os.path.relpath(self.get_static_media_path()).replace('\\','/')

    def get_media_path(self):
        """
        :return: The path to the media related to ``self.indexer_id``
        """

        return ''

    @staticmethod
    def get_media_root():
        """
        :return: The root folder containing the media
        """

        return os.path.join(sickbeard.GUI_DIR)

    def get_media_type(self):
        """
        :return: The mime type of the current media
        """

        static_media_path = self.get_static_media_path()

        if os.path.isfile(static_media_path):
            return guess_type(static_media_path)[0]

        return ''

    def get_show(self):
        """
        :return: The show object associated with ``self.indexer_id`` or ``None``
        """

        try:
            return findCertainShow(sickbeard.showList, self.indexer_id)
        except MultipleShowObjectsException:
            return None

    def get_static_media_path(self):
        """
        :return: The full path to the media
        """

        return os.path.normpath(self.get_media_path())
