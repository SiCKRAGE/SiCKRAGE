# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca/
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.



import os
from operator import itemgetter

import sickrage


def get_win_drives():
    """ Return list of detected drives """
    assert os.name == 'nt'
    from ctypes import windll

    drives = []
    bitmask = windll.kernel32.GetLogicalDrives()
    for letter in map(chr, range(ord('A'), ord('Z')+1)):
        if bitmask & 1:
            drives.append(letter)
        bitmask >>= 1

    return drives


def getFileList(path, includeFiles, fileTypes):
    # prune out directories to protect the user from doing stupid things (already lower case the dir to reduce calls)
    hide_list = ['boot', 'bootmgr', 'cache', 'config.msi', 'msocache', 'recovery', '$recycle.bin',
                 'recycler', 'system volume information', 'temporary internet files']  # windows specific
    hide_list += ['.fseventd', '.spotlight', '.trashes', '.vol', 'cachedmessages', 'caches', 'trash']  # osx specific
    hide_list += ['.git']

    file_list = []
    dir_list = []
    for filename in os.listdir(path):
        if filename.lower() in hide_list:
            continue

        full_filename = os.path.join(path, filename)
        is_file = os.path.isfile(full_filename)

        if not includeFiles and is_file:
            continue

        is_image = False
        allowed_type = True
        if is_file and fileTypes:
            if 'images' in fileTypes:
                is_image = filename.endswith(('jpg', 'jpeg', 'png', 'tiff', 'gif'))
            allowed_type = filename.endswith(tuple(fileTypes)) or is_image

            if not allowed_type:
                continue

        item_to_add = {
            'name': filename,
            'path': full_filename,
            'isFile': is_file,
            'isImage': is_image,
            'isAllowed': allowed_type
        }

        if is_file:
            file_list.append(item_to_add)
        else:
            dir_list.append(item_to_add)

    # Sort folders first, alphabetically, case insensitive
    dir_list.sort(key=lambda mbr: itemgetter('name')(mbr).lower())
    file_list.sort(key=lambda mbr: itemgetter('name')(mbr).lower())
    return dir_list + file_list


def foldersAtPath(path, includeParent=False, includeFiles=False, fileTypes=None):
    """
    Returns a list of dictionaries with the folders contained at the given path.

    Give the empty string as the path to list the contents of the root path
    (under Unix this means "/", on Windows this will be a list of drive letters)

    :param path: to list contents
    :param includeParent: boolean, include parent dir in list as well
    :param includeFiles: boolean, include files or only directories
    :param fileTypes: list, file extensions to include, 'images' is an alias for image types
    :return: list of folders/files
    """

    fileTypes = fileTypes or []

    # walk up the tree until we find a valid path
    while path and not os.path.isdir(path):
        if path == os.path.dirname(path):
            path = ''
            break
        else:
            path = os.path.dirname(path)

    if path == '':
        if os.name == 'nt':
            entries = [{'currentPath': 'Root'}]
            for letter in get_win_drives():
                letter_path = letter + ':\\'
                entries.append({'name': letter_path, 'path': letter_path})

            return entries
        else:
            path = '/'

    # fix up the path and find the parent
    path = os.path.abspath(os.path.normpath(path))
    parent_path = os.path.dirname(path)

    # if we're at the root then the next step is the meta-node showing our drive letters
    if path == parent_path and os.name == 'nt':
        parent_path = ''

    try:
        file_list = getFileList(path, includeFiles, fileTypes)
    except OSError as e:
        sickrage.app.log.warning('Unable to open {}: {} / {}'.format(path, repr(e), str(e)))
        file_list = getFileList(parent_path, includeFiles, fileTypes)

    entries = [{'currentPath': path}]

    if includeParent and parent_path != path:
        entries.append({'name': '..', 'path': parent_path})
    entries.extend(file_list)

    return entries
