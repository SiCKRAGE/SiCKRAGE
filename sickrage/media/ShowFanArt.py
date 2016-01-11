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

from sickbeard.image_cache import ImageCache
from sickrage.media.GenericMedia import GenericMedia


class ShowFanArt(GenericMedia):
    """
    Get the fan art of a show
    """

    def __init__(self, indexer_id, media_format):
        super(ShowFanArt, self).__init__(indexer_id, media_format)

    def get_default_media_name(self):
        return 'fanart.png'

    def get_media_path(self):
        media_file = None

        if self.get_show():
            media_file = ImageCache().fanart_path(self.indexer_id)

        if not all([media_file, os.path.exists(media_file)]):
            media_file = os.path.join(self.get_media_root(), 'images', self.get_default_media_name())

        return media_file