from __future__ import unicode_literals

import io
import os
from mimetypes import guess_type

import sickrage
from sickrage.core.exceptions import MultipleShowObjectsException
from sickrage.core.helpers import findCertainShow

class Media(object):
    def __init__(self, indexer_id, media_format=None):
        """
        :param indexer_id: The indexer id of the show
        :param media_format: The media format of the show image
        """

        self.media_format = media_format
        if not self.media_format:
            self.media_format = 'normal'

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

        return os.path.realpath(self.get_static_media_path()).replace('\\','/')

    @property
    def get_media_bytes(self):
        """
        :return: The content of the desired media file
        """

        with io.open(os.path.abspath(self.get_static_media_path()).replace('\\', '/'), 'rb') as media:
            return media.read()

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

        return os.path.join(sickrage.srCore.srConfig.GUI_DIR)

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
            return findCertainShow(sickrage.srCore.SHOWLIST, self.indexer_id)
        except MultipleShowObjectsException:
            return None

    def get_static_media_path(self):
        """
        :return: The full path to the media
        """

        return os.path.normpath(self.get_media_path())