# -*- coding: utf-8 -*-
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.tv/
# Git: https://github.com/SiCKRAGETV/SickRage.git
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

import os
import string

import logging
from sickrage.helper.encoding import ek


# adapted from http://stackoverflow.com/questions/827371/is-there-a-way-to-list-all-the-available-drive-letters-in-python/827490
def getWinDrives():
    """ Return list of detected drives """
    assert os.name == 'nt'
    from ctypes import windll

    drives = []
    bitmask = windll.kernel32.GetLogicalDrives()  # @UndefinedVariable
    for letter in string.uppercase:
        if bitmask & 1:
            drives.append(letter)
        bitmask >>= 1

    return drives


def foldersAtPath(path, includeParent=False, includeFiles=False):
    """ Returns a list of dictionaries with the folders contained at the given path
        Give the empty string as the path to list the contents of the root path
        (under Unix this means "/", on Windows this will be a list of drive letters)

        :param includeParent: boolean, include parent dir in list as well
        :param includeFiles: boolean, include files or only directories
        :return: list of folders/files
    """

    # walk up the tree until we find a valid path
    while path and not ek(os.path.isdir, path):
        if path == ek(os.path.dirname, path):
            path = ''
            break
        else:
            path = ek(os.path.dirname, path)

    if path == "":
        if os.name == 'nt':
            entries = [{'current_path': 'Root'}]
            for letter in getWinDrives():
                letterPath = letter + ':\\'
                entries.append({'name': letterPath, 'path': letterPath})
            return entries
        else:
            path = '/'

    # fix up the path and find the parent
    path = ek(os.path.abspath, ek(os.path.normpath, path))
    parentPath = ek(os.path.dirname, path)

    # if we're at the root then the next step is the meta-node showing our drive letters
    if path == parentPath and os.name == 'nt':
        parentPath = ""

    try:
        fileList = [{'name': filename, 'path': ek(os.path.join, path, filename)} for filename in ek(os.listdir, path)]
    except OSError as e:
        logging.warning("Unable to open " + path + ": " + repr(e) + " / " + str(e))
        fileList = [{'name': filename, 'path': ek(os.path.join, parentPath, filename)} for filename in
                    ek(os.listdir, parentPath)]

    if not includeFiles:
        fileList = [x for x in fileList if ek(os.path.isdir, x['path'])]

    # prune out directories to protect the user from doing stupid things (already lower case the dir to reduce calls)
    hideList = ["boot", "bootmgr", "cache", "msocache", "recovery", "$recycle.bin", "recycler",
                "system volume information", "temporary internet files"]  # windows specific
    hideList += [".fseventd", ".spotlight", ".trashes", ".vol", "cachedmessages", "caches", "trash"]  # osx specific

    fileList = [x for x in fileList if x['name'].lower() not in hideList]

    fileList = sorted(fileList,
                      lambda x, y: cmp(ek(os.path.basename, x['name']).lower(),
                                       ek(os.path.basename, y['path']).lower()))

    entries = [{'current_path': path}]
    if includeParent and parentPath != path:
        entries.append({'name': "..", 'path': parentPath})
    entries.extend(fileList)

    return entries
