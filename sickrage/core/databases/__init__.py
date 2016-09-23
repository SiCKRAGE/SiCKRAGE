# Author: echel0n <echel0n@sickrage.ca>
# URL: http://github.com/SiCKRAGETV/SickRage/
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

__all__ = ["main_db", "cache_db", "failed_db"]

import os
import re

import sickrage


def prettyName(class_name):
    return ' '.join([x.group() for x in re.finditer("([A-Z])([a-z0-9]+)", class_name)])


def dbFilename(filename=None, suffix=None):
    """
    @param filename: The sqlite database filename to use. If not specified,
                     will be made to be sickrage.db
    @param suffix: The suffix to append to the filename. A '.' will be added
                   automatically, i.e. suffix='v0' will make dbfile.db.v0
    @return: the correct location of the database file.
    """

    filename = filename or 'sickrage.db'

    if suffix:
        filename += ".{}".format(suffix)

    return os.path.join(sickrage.DATA_DIR, filename)


class srDatabase(object):
    def __init__(self, filename=None, suffix=None, row_type=None, timeout=None):
        self.filename = dbFilename(filename, suffix)
        self.indexes = {}
