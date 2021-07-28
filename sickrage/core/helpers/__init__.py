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


import base64
import ctypes
import datetime
import glob
import hashlib
import ipaddress
import os
import platform
import random
import re
import shutil
import socket
import stat
import string
import tempfile
import time
import traceback
import unicodedata
import uuid
import webbrowser
import zipfile
from collections import OrderedDict, Iterable
from contextlib import contextmanager
from urllib.parse import uses_netloc, urlsplit, urlunsplit, urljoin

import errno
import rarfile
import requests
from bs4 import BeautifulSoup
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

import sickrage
from sickrage.core.enums import TorrentMethod
from sickrage.core.helpers import encryption
from sickrage.core.websession import WebSession


def safe_getattr(object, name, default=None):
    try:
        return getattr(object, name, default) or default
    except:
        return default


def try_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def read_file_buffered(filename, reverse=False):
    blocksize = (1 << 15)
    with open(filename, 'r', encoding='utf-8') as fh:
        if reverse:
            fh.seek(0, os.SEEK_END)
        pos = fh.tell()
        while True:

            if reverse:
                chunksize = min(blocksize, pos)
                pos -= chunksize
            else:
                chunksize = max(blocksize, pos)
                pos += chunksize

            fh.seek(pos, os.SEEK_SET)
            data = fh.read(chunksize)
            if not data:
                break
            yield data
            del data


def arg_to_bool(x):
    """
    convert argument of unknown type to a bool:
    """

    if isinstance(x, str):
        if x.lower() in ("0", "false", "f", "no", "n", "off"):
            return False
        elif x.lower() in ("1", "true", "t", "yes", "y", "on"):
            return True
        raise ValueError("failed to cast as boolean")

    return bool(x)


def auto_type(s):
    for fn in (int, float, arg_to_bool):
        try:
            return fn(s)
        except ValueError:
            pass

    return (s, '')[s.lower() == "none"]


def fix_glob(path):
    path = re.sub(r'\[', '[[]', path)
    return re.sub(r'(?<!\[)\]', '[]]', path)


def indent_xml(elem, level=0):
    """
    Does our pretty printing, makes Matt very happy
    """
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent_xml(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def remove_extension(name):
    """
    Remove download or media extension from name (if any)
    """

    if name and "." in name:
        base_name, sep, extension = name.rpartition('.')
        if base_name and extension.lower() in ['nzb', 'torrent'] + sickrage.app.config.general.allowed_video_file_exts.split(','):
            name = base_name

    return name


def remove_non_release_groups(name):
    """
    Remove non release groups from name
    """
    if not name:
        return name

    # Do not remove all [....] suffixes, or it will break anime releases ## Need to verify this is true now
    # Check your database for funky release_names and add them here, to improve failed handling, archiving, and history.
    # select release_name from tv_episodes WHERE LENGTH(release_name);
    # [eSc], [SSG], [GWC] are valid release groups for non-anime
    removeWordsList = OrderedDict([
        (r'^\[www\.Cpasbien\.pe\] ', 'searchre'),
        (r'^\[www\.Cpasbien\.com\] ', 'searchre'),
        (r'^\[ www\.Cpasbien\.pw \] ', 'searchre'),
        (r'^\.www\.Cpasbien\.pw', 'searchre'),
        (r'^\[www\.newpct1\.com\]', 'searchre'),
        (r'^\[ www\.Cpasbien\.com \] ', 'searchre'),
        (r'^\{ www\.SceneTime\.com \} - ', 'searchre'),
        (r'^\]\.\[www\.tensiontorrent.com\] - ', 'searchre'),
        (r'^\]\.\[ www\.tensiontorrent.com \] - ', 'searchre'),
        (r'^\[ www\.TorrentDay\.com \] - ', 'searchre'),
        (r'^www\.Torrenting\.com\.-\.', 'searchre'),
        (r'\[rartv\]$', 'searchre'),
        (r'\[rarbg\]$', 'searchre'),
        (r'\.\[eztv\]$', 'searchre'),
        (r'\[eztv\]$', 'searchre'),
        (r'\[ettv\]$', 'searchre'),
        (r'\[cttv\]$', 'searchre'),
        (r'\.\[vtv\]$', 'searchre'),
        (r'\[vtv\]$', 'searchre'),
        (r'\[EtHD\]$', 'searchre'),
        (r'\[GloDLS\]$', 'searchre'),
        (r'\[silv4\]$', 'searchre'),
        (r'\[Seedbox\]$', 'searchre'),
        (r'\[PublicHD\]$', 'searchre'),
        (r'\.\[PublicHD\]$', 'searchre'),
        (r'\.\[NO.RAR\]$', 'searchre'),
        (r'\[NO.RAR\]$', 'searchre'),
        (r'-\=\{SPARROW\}\=-$', 'searchre'),
        (r'\=\{SPARR$', 'searchre'),
        (r'\.\[720P\]\[HEVC\]$', 'searchre'),
        (r'\[AndroidTwoU\]$', 'searchre'),
        (r'\[brassetv\]$', 'searchre'),
        (r'\[Talamasca32\]$', 'searchre'),
        (r'\(musicbolt\.com\)$', 'searchre'),
        (r'\.\(NLsub\)$', 'searchre'),
        (r'\(NLsub\)$', 'searchre'),
        (r'\.\[BT\]$', 'searchre'),
        (r' \[1044\]$', 'searchre'),
        (r'\.RiPSaLoT$', 'searchre'),
        (r'\.GiuseppeTnT$', 'searchre'),
        (r'\.Renc$', 'searchre'),
        (r'\.gz$', 'searchre'),
        (r'\.English$', 'searchre'),
        (r'\.German$', 'searchre'),
        (r'\.\.Italian$', 'searchre'),
        (r'\.Italian$', 'searchre'),
        (r'(?<![57])\.1$', 'searchre'),
        (r'-NZBGEEK$', 'searchre'),
        (r'-Siklopentan$', 'searchre'),
        (r'-Chamele0n$', 'searchre'),
        (r'-Obfuscated$', 'searchre'),
        (r'-BUYMORE$', 'searchre'),
        (r'-\[SpastikusTV\]$', 'searchre'),
        (r'-RP$', 'searchre'),
        (r'-20-40$', 'searchre'),
        (r'\.\[www\.usabit\.com\]$', 'searchre'),
        (r'\[NO-RAR\] - \[ www\.torrentday\.com \]$', 'searchre'),
        (r'- \[ www\.torrentday\.com \]$', 'searchre'),
        (r'- \{ www\.SceneTime\.com \}$', 'searchre'),
        (r'-Scrambled$', 'searchre')
    ])

    _name = name
    for remove_string, remove_type in removeWordsList.items():
        if remove_type == 'search':
            _name = _name.replace(remove_string, '')
        elif remove_type == 'searchre':
            _name = re.sub(r'(?i)' + remove_string, '', _name)

    return _name


def replace_extension(filename, newExt):
    """
    >>> replace_extension('foo.avi', 'mkv')
    'foo.mkv'
    >>> replace_extension('.vimrc', 'arglebargle')
    '.vimrc'
    >>> replace_extension('a.b.c', 'd')
    'a.b.d'
    >>> replace_extension('', 'a')
    ''
    >>> replace_extension('foo.bar', '')
    'foo.'
    """
    sepFile = filename.rpartition(".")
    if sepFile[0] == "":
        return filename
    else:
        return sepFile[0] + "." + newExt


def is_torrent_or_nzb_file(filename):
    """
    Check if the provided ``filename`` is a NZB file or a torrent file, based on its extension.
    :param filename: The filename to check
    :return: ``True`` if the ``filename`` is a NZB file or a torrent file, ``False`` otherwise
    """

    if not isinstance(filename, str):
        return False

    return filename.rpartition('.')[2].lower() in ['nzb', 'torrent']


def is_sync_file(filename):
    """
    Returns true if filename is a syncfile, indicating filesystem may be in flux

    :param filename: Filename to check
    :return: True if this file is a syncfile, False otherwise
    """

    extension = filename.rpartition(".")[2].lower()
    # if extension == '!sync' or extension == 'lftp-pget-status' or extension == 'part' or extension == 'bts':
    syncfiles = sickrage.app.config.general.sync_files
    if extension in syncfiles.split(",") or filename.startswith('.syncthing'):
        return True
    else:
        return False


def is_media_file(filename):
    """
    Check if named file may contain media

    :param filename: Filename to check
    :return: True if this is a known media file, False if not
    """

    # ignore samples
    if re.search(r'(^|[\W_])(?<!shomin.)(sample\d*)[\W_]', filename, re.I):
        return False

    # ignore RARBG release intro
    if re.search(r'^RARBG\.(\w+\.)?(mp4|avi|txt)$', filename, re.I):
        return False

    # ignore MAC OS's retarded "resource fork" files
    if filename.startswith('._'):
        return False

    sepFile = filename.rpartition(".")

    if re.search('extras?$', sepFile[0], re.I):
        return False

    return sepFile[-1].lower() in sickrage.app.config.general.allowed_video_file_exts.split(',')


def is_rar_file(filename):
    """
    Check if file is a RAR file, or part of a RAR set

    :param filename: Filename to check
    :return: True if this is RAR/Part file, False if not
    """

    archive_regex = r'(?P<file>^(?P<base>(?:(?!\.part\d+\.rar$).)*)\.(?:(?:part0*1\.)?rar)$)'
    ret = re.search(archive_regex, filename) is not None
    try:
        if ret and os.path.exists(filename) and os.path.isfile(filename):
            ret = rarfile.is_rarfile(filename)
    except (IOError, OSError):
        pass

    return ret


def sanitize_file_name(name):
    """
    >>> sanitize_file_name('a/b/c')
    'a-b-c'
    >>> sanitize_file_name('abc')
    'abc'
    >>> sanitize_file_name('a"b')
    'ab'
    >>> sanitize_file_name('.a.b..')
    'a.b'
    """

    # remove bad chars from the filename
    name = re.sub(r'[\\/*]', '-', name)
    name = re.sub(r'[:"<>|?]', '', name)
    name = re.sub(r'\u2122', '', name)  # Trade Mark Sign

    # remove leading/trailing periods and spaces
    name = name.strip(' .')

    return name


def make_dir(path):
    """
    Make a directory on the filesystem

    :param path: directory to make
    :return: True if success, False if failure
    """

    if not os.path.isdir(path):
        try:
            os.makedirs(path)
            sickrage.app.notification_providers['synoindex'].addFolder(path)
        except OSError:
            return False
    return True


def list_media_files(path):
    """
    Get a list of files possibly containing media in a path

    :param path: Path to check for files
    :return: list of files
    """

    if not dir or not os.path.isdir(path):
        return []

    files = []
    for curFile in os.listdir(path):
        fullCurFile = os.path.join(path, curFile)

        # if it's a folder do it recursively
        if os.path.isdir(fullCurFile) and not curFile.startswith('.') and not curFile == 'Extras':
            files += list_media_files(fullCurFile)

        elif is_media_file(curFile):
            files.append(fullCurFile)

    return files


def copy_file(src_file, dest_file):
    """
    Copy a file from source to destination

    :param src_file: Path of source file
    :param dest_file: Path of destination file
    """

    try:
        shutil.copyfile(src_file, dest_file)
    except (OSError, PermissionError) as e:
        if e.errno in [errno.ENOSPC, errno.EACCES]:
            sickrage.app.log.warning(e)
        else:
            sickrage.app.log.error(e)
    else:
        try:
            shutil.copymode(src_file, dest_file)
        except OSError:
            pass


def move_file(src_file, dest_file):
    """
    Move a file from source to destination

    :param src_file: Path of source file
    :param dest_file: Path of destination file
    """

    try:
        shutil.move(src_file, dest_file)
        fix_set_group_id(dest_file)
    except OSError:
        copy_file(src_file, dest_file)
        os.unlink(src_file)


def link(src, dst):
    """
    Create a file link from source to destination.
    TODO: Make this unicode proof

    :param src: Source file
    :param dst: Destination file
    """

    if os.name == 'nt':
        if ctypes.windll.kernel32.CreateHardLinkW(ctypes.c_wchar_p(dst), ctypes.c_wchar_p(src), None) == 0:
            raise ctypes.WinError()
    else:
        os.link(src, dst)


def hardlink_file(src_file, dest_file):
    """
    Create a hard-link (inside filesystem link) between source and destination

    :param src_file: Source file
    :param dest_file: Destination file
    """

    try:
        link(src_file, dest_file)
        fix_set_group_id(dest_file)
    except OSError as e:
        if e.errno == errno.EEXIST:
            # File exists. Don't fallback to copy
            sickrage.app.log.warning('Failed to create hardlink of {src} at {dest}. Error: {error!r}'.format(
                **{'src': src_file, 'dest': dest_file, 'error': e}))
        else:
            sickrage.app.log.warning(
                "Failed to create hardlink of {src} at {dest}. Error: {error!r}. Copying instead".format(
                    **{'src': src_file, 'dest': dest_file, 'error': e}))
            copy_file(src_file, dest_file)


def symlink(src, dst):
    """
    Create a soft/symlink between source and destination

    :param src: Source file
    :param dst: Destination file
    """

    if os.name == 'nt':
        if ctypes.windll.kernel32.CreateSymbolicLinkW(ctypes.c_wchar_p(dst), ctypes.c_wchar_p(src),
                                                      1 if os.path.isdir(src) else 0) in [0, 1280]:
            raise ctypes.WinError()
    else:
        os.symlink(src, dst)


def move_and_symlink_file(src_file, dest_file):
    """
    Move a file from source to destination, then create a symlink back from destination from source. If this fails, copy
    the file from source to destination

    :param src_file: Source file
    :param dest_file: Destination file
    """

    try:
        shutil.move(src_file, dest_file)
        fix_set_group_id(dest_file)
        symlink(dest_file, src_file)
    except OSError as e:
        if e.errno == errno.EEXIST:
            # File exists. Don't fallback to copy
            sickrage.app.log.warning('Failed to create symlink of {src} at {dest}. Error: {error!r}'.format(
                **{'src': src_file, 'dest': dest_file, 'error': e}))
        else:
            sickrage.app.log.warning(
                "Failed to create symlink of {src} at {dest}. Error: {error!r}. Copying instead".format(
                    **{'src': src_file, 'dest': dest_file, 'error': e}))
            copy_file(src_file, dest_file)


def make_dirs(path):
    """
    Creates any folders that are missing and assigns them the permissions of their
    parents
    """

    sickrage.app.log.debug("Checking if the path [{}] already exists".format(path))

    if not os.path.isdir(path):
        # Windows, create all missing folders
        if os.name == 'nt' or os.name == 'ce':
            try:
                sickrage.app.log.debug("Folder %s didn't exist, creating it" % path)
                os.makedirs(path)
            except (OSError, IOError) as e:
                sickrage.app.log.warning("Failed creating %s : %r" % (path, e))
                return False

        # not Windows, create all missing folders and set permissions
        else:
            sofar = ''
            folder_list = path.split(os.path.sep)

            # look through each subfolder and make sure they all exist
            for cur_folder in folder_list:
                sofar += cur_folder + os.path.sep

                # if it exists then just keep walking down the line
                if os.path.isdir(sofar):
                    continue

                try:
                    sickrage.app.log.debug("Folder %s didn't exist, creating it" % sofar)
                    os.mkdir(sofar)
                    # use normpath to remove end separator, otherwise checks permissions against itself
                    chmod_as_parent(os.path.normpath(sofar))
                    # do the library update for synoindex
                    sickrage.app.notification_providers['synoindex'].addFolder(sofar)
                except (OSError, IOError) as e:
                    sickrage.app.log.error("Failed creating %s : %r" % (sofar, e))
                    return False

    return True


def delete_empty_folders(check_empty_dir, keep_dir=None):
    """
    Walks backwards up the path and deletes any empty folders found.

    :param check_empty_dir: The path to clean (absolute path to a folder)
    :param keep_dir: Clean until this path is reached
    """

    # treat check_empty_dir as empty when it only contains these items
    ignore_items = []

    sickrage.app.log.info("Trying to clean any empty folders under " + check_empty_dir)

    # as long as the folder exists and doesn't contain any files, delete it
    try:
        while os.path.isdir(check_empty_dir) and check_empty_dir != keep_dir:
            check_files = os.listdir(check_empty_dir)

            if not check_files or (len(check_files) <= len(ignore_items)
                                   and all([check_file in ignore_items for check_file in check_files])):

                try:
                    # directory is empty or contains only ignore_items
                    sickrage.app.log.info("Deleting empty folder: " + check_empty_dir)
                    shutil.rmtree(check_empty_dir)

                    # do the library update for synoindex
                    sickrage.app.notification_providers['synoindex'].deleteFolder(check_empty_dir)
                except OSError as e:
                    sickrage.app.log.warning("Unable to delete %s. Error: %r" % (check_empty_dir, repr(e)))
                    raise StopIteration
                check_empty_dir = os.path.dirname(check_empty_dir)
            else:
                raise StopIteration
    except StopIteration:
        pass


def file_bit_filter(mode):
    """
    Strip special filesystem bits from file

    :param mode: mode to check and strip
    :return: required mode for media file
    """

    for bit in [stat.S_IXUSR, stat.S_IXGRP, stat.S_IXOTH, stat.S_ISUID, stat.S_ISGID]:
        if mode & bit:
            mode -= bit

    return mode


def chmod_as_parent(child_path):
    """
    Retain permissions of parent for childs

    (Does not work for Windows hosts)

    :param child_path: Child Path to change permissions to sync from parent
    """

    if os.name == 'nt' or os.name == 'ce':
        return

    parent_path = os.path.dirname(child_path)

    if not parent_path:
        sickrage.app.log.debug("No parent path provided in " + child_path + ", unable to get permissions from it")
        return

    child_path = os.path.join(parent_path, os.path.basename(child_path))
    if not os.path.exists(child_path):
        return

    parent_path_stat = os.stat(parent_path)
    parent_mode = stat.S_IMODE(parent_path_stat[stat.ST_MODE])

    child_path_stat = os.stat(child_path)
    child_path_mode = stat.S_IMODE(child_path_stat[stat.ST_MODE])

    if os.path.isfile(child_path) and sickrage.app.config.general.strip_special_file_bits:
        child_mode = file_bit_filter(parent_mode)
    else:
        child_mode = parent_mode

    if child_path_mode == child_mode:
        return

    child_path_owner = child_path_stat.st_uid
    user_id = os.geteuid()

    if user_id not in (0, child_path_owner):
        sickrage.app.log.debug("Not running as root or owner of " + child_path + ", not trying to set permissions")
        return

    try:
        os.chmod(child_path, child_mode)
        sickrage.app.log.debug(
            "Setting permissions for %s to %o as parent directory has %o" % (child_path, child_mode, parent_mode))
    except OSError:
        sickrage.app.log.debug("Failed to set permission for %s to %o" % (child_path, child_mode))


def fix_set_group_id(child_path):
    """
    Inherit SGID from parent

    (does not work on Windows hosts)

    :param child_path: Path to inherit SGID permissions from parent
    """

    if os.name == 'nt' or os.name == 'ce':
        return

    parent_path = os.path.dirname(child_path)
    parent_stat = os.stat(parent_path)
    parent_mode = stat.S_IMODE(parent_stat[stat.ST_MODE])

    child_path = os.path.join(parent_path, os.path.basename(child_path))

    if parent_mode & stat.S_ISGID:
        parent_gid = parent_stat[stat.ST_GID]
        child_stat = os.stat(child_path)
        child_gid = child_stat[stat.ST_GID]

        if child_gid == parent_gid:
            return

        child_path_owner = child_stat.st_uid
        user_id = os.geteuid()

        if user_id not in (0, child_path_owner):
            sickrage.app.log.debug(
                "Not running as root or owner of {}, not trying to set the set-group-ID".format(child_path))
            return

        try:
            os.chown(child_path, -1, parent_gid)
            sickrage.app.log.debug("Respecting the set-group-ID bit on the parent directory for {}".format(child_path))
        except OSError:
            sickrage.app.log.error("Failed to respect the set-group-ID bit on the parent directory for {} (setting "
                                   "group ID {})".format(child_path, parent_gid))


def sanitize_scene_name(name, anime=False):
    """
    Takes a show name and returns the "scenified" version of it.

    :param anime: Some show have a ' in their name(Kuroko's Basketball) and is needed for search.
    :return: A string containing the scene version of the show name given.
    """

    if not name:
        return ''

    bad_chars = ',:()!?\u2019'
    if not anime:
        bad_chars += "'"

    # strip out any bad chars
    for x in bad_chars:
        name = name.replace(x, "")

    # tidy up stuff that doesn't belong in scene names
    name = name.replace("- ", ".").replace(" ", ".").replace("&", "and").replace('/', '.')
    name = re.sub(r"\.\.*", ".", name)

    if name.endswith('.'):
        name = name[:-1]

    return name


def create_https_certificates(ssl_cert, ssl_key):
    """This function takes a domain name as a parameter and then creates a certificate and key with the
    domain name(replacing dots by underscores), finally signing the certificate using specified CA and
    returns the path of key and cert files. If you are yet to generate a CA then check the top comments"""

    # Generate our key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )

    name = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, 'SiCKRAGE')
    ])

    # path_len=0 means this cert can only sign itself, not other certs.
    basic_contraints = x509.BasicConstraints(ca=True, path_length=0)
    now = datetime.datetime.utcnow()
    cert = (
        x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(key.public_key())
            .serial_number(1000)
            .not_valid_before(now)
            .not_valid_after(now + datetime.timedelta(days=10 * 365))
            .add_extension(basic_contraints, False)
            # .add_extension(san, False)
            .sign(key, hashes.SHA256(), default_backend())
    )
    cert_pem = cert.public_bytes(encoding=serialization.Encoding.PEM)
    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    with open(ssl_key, 'wb') as key_out:
        key_out.write(key_pem)

    with open(ssl_cert, 'wb') as cert_out:
        cert_out.write(cert_pem)

    return True


def anon_url(*url):
    """
    Return a URL string consisting of the Anonymous redirect URL and an arbitrary number of values appended.
    """

    url = ''.join(map(str, url))

    # Handle URL's containing https or http, previously only handled http
    uri_pattern = '^https?://'
    unicode_uri_pattern = re.compile(uri_pattern, re.UNICODE)
    if not re.search(unicode_uri_pattern, url):
        url = 'http://' + url

    return '{}{}'.format(sickrage.app.config.general.anon_redirect, url)


def full_sanitize_scene_name(name):
    return re.sub('[. -]', ' ', sanitize_scene_name(name)).lower().lstrip()


def is_hidden_folder(folder):
    """
    Returns True if folder is hidden.
    On Linux based systems hidden folders start with . (dot)
    :param folder: Full path of folder to check
    """

    def is_hidden(filepath):
        name = os.path.basename(os.path.abspath(filepath))
        return name.startswith('.') or has_hidden_attribute(filepath)

    def has_hidden_attribute(filepath):
        try:
            attrs = ctypes.windll.kernel32.GetFileAttributesW(filepath)
            assert attrs != -1
            result = bool(attrs & 2)
        except (AttributeError, AssertionError):
            result = False
        return result

    if os.path.isdir(folder):
        if is_hidden(folder):
            return True

    return False


def file_size(fname):
    return os.stat(fname).st_size


def real_path(path):
    """
    Returns: the canonicalized absolute pathname. The resulting path will have no symbolic link, '/./' or '/../' components.
    """
    return os.path.normpath(os.path.normcase(os.path.realpath(path)))


def extract_zipfile(archive, targetDir):
    """
    Unzip a file to a directory

    :param archive: The file name for the archive with a full path
    """

    try:
        if not os.path.exists(targetDir):
            os.mkdir(targetDir)

        zip_file = zipfile.ZipFile(archive, 'r', allowZip64=True)
        for member in zip_file.namelist():
            filename = os.path.basename(member)
            # skip directories
            if not filename:
                continue

            # copy file (taken from zipfile's extract)
            source = zip_file.open(member)
            target = open(os.path.join(targetDir, filename), "wb")
            shutil.copyfileobj(source, target)
            source.close()
            target.close()
        zip_file.close()
        return True
    except Exception as e:
        sickrage.app.log.warning("Zip extraction error: %r " % repr(e))
        return False


def create_zipfile(fileList, archive, arcname=None):
    """
    Store the config file as a ZIP

    :param fileList: List of files to store
    :param archive: ZIP file name
    :param arcname: Archive path
    :return: True on success, False on failure
    """

    try:
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as z:
            for f in list(set(fileList)):
                z.write(f, os.path.relpath(f, arcname))
        return True
    except Exception as e:
        sickrage.app.log.warning("Zip creation error: {} ".format(e))
        return False


def restore_config_zip(archive, targetDir, restore_database=True, restore_config=True, restore_cache=True):
    """
    Restores a backup ZIP file back in place

    :param archive: ZIP filename
    :param targetDir: Directory to restore to
    :return: True on success, False on failure
    """

    if not os.path.isfile(archive):
        return

    try:
        if not os.path.exists(targetDir):
            os.mkdir(targetDir)
        else:
            def path_leaf(path):
                head, tail = os.path.split(path)
                return tail or os.path.basename(head)

            bakFilename = '{0}-{1}'.format(path_leaf(targetDir), datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
            move_file(targetDir, os.path.join(os.path.dirname(targetDir), bakFilename))

        with zipfile.ZipFile(archive, 'r', allowZip64=True) as zip_file:
            for member in zip_file.namelist():
                if not restore_database and member.split('/')[0] in ['main_db_backup.json',
                                                                     'main.db',
                                                                     'main.db-shm',
                                                                     'main.db-wal',
                                                                     'cache_db_backup.json',
                                                                     'cache.db',
                                                                     'cache.db-shm',
                                                                     'cache.db-wal']:
                    continue

                if not restore_config and member.split('/')[0] in ['config.ini',
                                                                   'privatekey.pem'
                                                                   'config.db']:
                    continue

                if not restore_cache and member.split('/')[0] == 'cache':
                    continue

                zip_file.extract(member, targetDir)

        return True
    except Exception as e:
        sickrage.app.log.warning("Zip extraction error: {}".format(e))
        shutil.rmtree(targetDir)


def backup_app_data(backupDir, keep_latest=False):
    source = []

    # files_list = [
    #     'privatekey.pem',
    #     os.path.basename(sickrage.app.config_file)
    # ]

    def _keep_latest_backup():
        for x in sorted(glob.glob(os.path.join(backupDir, '*.zip')), key=os.path.getctime, reverse=True)[1:]:
            os.remove(x)

    if not os.path.exists(backupDir):
        os.mkdir(backupDir)

    if keep_latest:
        _keep_latest_backup()

    # individual files
    # for f in files_list:
    #     fp = os.path.join(sickrage.app.data_dir, f)
    #     if os.path.exists(fp):
    #         source += [fp]

    # databases
    for db in [sickrage.app.main_db, sickrage.app.config.db, sickrage.app.cache_db]:
        backup_file = os.path.join(*[sickrage.app.data_dir, '{}_db_backup.json'.format(db.name)])
        db.backup(backup_file)
        source += [backup_file]

    # cache folder
    if sickrage.app.cache_dir:
        for (path, dirs, files) in os.walk(sickrage.app.cache_dir, topdown=True):
            for dirname in dirs:
                if path == sickrage.app.cache_dir and dirname not in ['images']:
                    dirs.remove(dirname)

            for filename in files:
                source += [os.path.join(path, filename)]

    # ZIP filename
    target = os.path.join(backupDir, 'sickrage-{}.zip'.format(datetime.datetime.now().strftime('%Y%m%d%H%M%S')))

    return create_zipfile(source, target, sickrage.app.data_dir)


def restore_app_data(srcDir, dstDir):
    try:
        files_list = [
            'main.db',
            'main.db-shm',
            'main.db-wal',
            'config.db',
            'cache.db',
            'cache.db-shm',
            'cache.db-wal',
            'main.codernitydb',
            'cache.codernitydb',
            'privatekey.pem',
            os.path.basename(sickrage.app.config_file)
        ]

        for filename in files_list:
            srcFile = os.path.join(srcDir, filename)
            dstFile = os.path.join(dstDir, filename)
            bakFile = os.path.join(dstDir, '{}_{}.bak'.format(filename, datetime.datetime.now().strftime('%Y%m%d_%H%M%S')))

            if os.path.exists(srcFile):
                if os.path.isfile(dstFile):
                    move_file(dstFile, bakFile)
                move_file(srcFile, dstFile)

        # database
        for db in [sickrage.app.main_db, sickrage.app.config.db, sickrage.app.cache_db]:
            backup_file = os.path.join(*[srcDir, '{}_db_backup.json'.format(db.name)])
            if os.path.exists(backup_file):
                db.restore(backup_file)

        # cache
        if os.path.exists(os.path.join(srcDir, 'cache')):
            if os.path.exists(os.path.join(dstDir, 'cache')):
                move_file(os.path.join(dstDir, 'cache'), os.path.join(dstDir, '{}_{}.bak'.format('cache', datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))))
            move_file(os.path.join(srcDir, 'cache'), dstDir)

        return True
    except Exception as e:
        return False


def modify_file_timestamp(fname, atime=None):
    """
    Change a file timestamp (change modification date)

    :param fname: Filename to touch
    :param atime: Specific access time (defaults to None)
    :return: True on success, False on failure
    """

    if atime and fname and os.path.isfile(fname):
        os.utime(fname, (atime, atime))
        return True

    return False


def touch_file(fname):
    with open(fname, 'a'):
        os.utime(fname, None)


def get_size(start_path='.'):
    """
    Find the total dir and filesize of a path

    :param start_path: Path to recursively count size
    :return: total filesize
    """

    if not os.path.isdir(start_path):
        return -1

    total_size = 0

    try:
        for dirpath, __, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total_size += os.path.getsize(fp)
                except OSError as e:
                    sickrage.app.log.warning("Unable to get size for file %s Error: %r" % (fp, e))
                    sickrage.app.log.debug(traceback.format_exc())
    except Exception as e:
        pass

    return total_size


def generate_api_key():
    """ Return a new randomized API_KEY"""

    from hashlib import md5

    # Create some values to seed md5
    t = str(time.time()).encode('utf-8')
    r = str(random.random()).encode('utf-8')

    # Create the md5 instance and give it the current time
    m = md5(t)

    # Update the md5 instance with the random variable
    m.update(r)

    # Return a hex digest of the md5, eg 49f68a5c8493ec2c0bf489821c21fc3b
    return m.hexdigest()


def pretty_file_size(size, use_decimal=False, **kwargs):
    """
    Return a human readable representation of the provided ``size``.

    :param size: The size to convert
    :param use_decimal: use decimal instead of binary prefixes (e.g. kilo = 1000 instead of 1024)

    :keyword units: A list of unit names in ascending order.
        Default units: ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

    :return: The converted size
    """
    try:
        size = max(float(size), 0.)
    except (ValueError, TypeError):
        size = 0.

    remaining_size = size
    units = kwargs.pop('units', ['B', 'KB', 'MB', 'GB', 'TB', 'PB'])
    block = 1024. if not use_decimal else 1000.
    for unit in units:
        if remaining_size < block:
            return '{0:3.2f} {1}'.format(remaining_size, unit)
        remaining_size /= block
    return size


def remove_article(text=''):
    """Remove the english articles from a text string"""

    return re.sub(r'(?i)^(?:(?:A(?!\s+to)n?)|The)\s(\w)', r'\1', text)


def generate_secret():
    """Generate a new secret"""

    return base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes).decode()


def verify_freespace(src, dest, oldfile=None):
    """Check if the target system has enough free space to copy or move a file.

    :param src: Source filename
    :param dest: Destination path
    :param oldfile: File to be replaced (defaults to None)
    :return: True if there is enough space for the file,
             False if there isn't. Also returns True if the OS doesn't support this option
    """

    if not isinstance(oldfile, list):
        oldfile = [oldfile]

    sickrage.app.log.debug(u'Trying to determine free space on destination drive')
    if not os.path.isfile(src):
        sickrage.app.log.warning('A path to a file is required for the source.'
                                 ' {source} is not a file.', {'source': src})
        return True

    try:
        diskfree = get_disk_space_usage(dest, False)
        if not diskfree:
            sickrage.app.log.warning('Unable to determine the free space on your OS.')
            return True
    except Exception:
        sickrage.app.log.warning('Unable to determine free space, assuming there is '
                                 'enough.')
        return True

    try:
        neededspace = os.path.getsize(src)
    except OSError as error:
        sickrage.app.log.warning('Unable to determine needed space. Aborting.'
                                 ' Error: {msg}', {'msg': error})
        return False

    if oldfile:
        for f in oldfile:
            if os.path.isfile(f.location):
                diskfree += os.path.getsize(f.location)

    if diskfree > neededspace:
        return True
    else:
        sickrage.app.log.warning(
            'Not enough free space.'
            ' Needed: {0} bytes ({1}),'
            ' found: {2} bytes ({3})',
            neededspace, pretty_file_size(neededspace),
            diskfree, pretty_file_size(diskfree)
        )

        return False


def pretty_time_delta(seconds):
    sign_string = '-' if seconds < 0 else ''
    seconds = abs(int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    time_delta = sign_string

    if days > 0:
        time_delta += ' %dd' % days
    if hours > 0:
        time_delta += ' %dh' % hours
    if minutes > 0:
        time_delta += ' %dm' % minutes
    if seconds > 0:
        time_delta += ' %ds' % seconds

    return time_delta


def is_file_locked(checkfile, writeLockCheck=False):
    """
    Checks to see if a file is locked. Performs three checks
        1. Checks if the file even exists
        2. Attempts to open the file for reading. This will determine if the file has a write lock.
            Write locks occur when the file is being edited or copied to, e.g. a file copy destination
        3. If the readLockCheck parameter is True, attempts to rename the file. If this fails the
            file is open by some other process for reading. The file can be read, but not written to
            or deleted.
    :param checkfile: the file being checked
    :param writeLockCheck: when true will check if the file is locked for writing (prevents move operations)
    """

    checkfile = os.path.abspath(checkfile)

    if not os.path.exists(checkfile):
        return True
    try:
        with open(checkfile, 'rb'):
            pass
    except IOError:
        return True

    if writeLockCheck:
        lockFile = checkfile + ".lckchk"
        if os.path.exists(lockFile):
            os.remove(lockFile)

        try:
            os.rename(checkfile, lockFile)
            time.sleep(1)
            os.rename(lockFile, checkfile)
        except (OSError, IOError):
            return True

    return False


def get_disk_space_usage(disk_path=None, pretty=True):
    """Return the free space in human readable bytes for a given path or False if no path given.

    :param disk_path: the filesystem path being checked
    :param pretty: return as bytes if None
    """
    if disk_path and os.path.exists(disk_path):
        if platform.system() == 'Windows':
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(disk_path), None, None,
                                                       ctypes.pointer(free_bytes))
            return pretty_file_size(free_bytes.value) if pretty else free_bytes.value
        else:
            st = os.statvfs(disk_path)
            file_size = st.f_bavail * st.f_frsize
            return pretty_file_size(file_size) if pretty else file_size
    else:
        return False


def get_free_space(directories):
    single = not isinstance(directories, (tuple, list))
    if single:
        directories = [directories]

    free_space = {}
    for folder in directories:
        size = None
        if os.path.isdir(folder):
            if os.name == 'nt':
                __, total, free = ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong()
                fun = ctypes.windll.kernel32.GetDiskFreeSpaceExW
                ret = fun(folder, ctypes.byref(__), ctypes.byref(total), ctypes.byref(free))
                if ret == 0: raise ctypes.WinError()

                return [total.value, free.value]
            else:
                s = os.statvfs(folder)

                size = [s.f_blocks * s.f_frsize / (1024 * 1024), (s.f_bavail * s.f_frsize) / (1024 * 1024)]

        if single:
            return size

        free_space[folder] = size

    return free_space


def restore_versioned_file(backup_file, version):
    """
    Restore a file version to original state

    :param backup_file: File to restore
    :param version: Version of file to restore
    :return: True on success, False on failure
    """

    numTries = 0

    new_file, __ = os.path.splitext(backup_file)
    restore_file = '{}.v{}'.format(new_file, version)

    if not os.path.isfile(new_file):
        sickrage.app.log.debug("Not restoring, %s doesn't exist" % new_file)
        return False

    try:
        sickrage.app.log.debug("Trying to backup %s to %s.r%s before restoring backup"
                               % (new_file, new_file, version))

        move_file(new_file, new_file + '.' + 'r' + str(version))
    except Exception as e:
        sickrage.app.log.warning("Error while trying to backup file %s before proceeding with restore: %r"
                                 % (restore_file, e))
        return False

    while not os.path.isfile(new_file):
        if not os.path.isfile(restore_file):
            sickrage.app.log.debug("Not restoring, %s doesn't exist" % restore_file)
            break

        try:
            sickrage.app.log.debug("Trying to restore file %s to %s" % (restore_file, new_file))
            shutil.copy(restore_file, new_file)
            sickrage.app.log.debug("Restore done")
            break
        except Exception as e:
            sickrage.app.log.warning("Error while trying to restore file %s. Error: %r" % (restore_file, e))
            numTries += 1
            time.sleep(1)
            sickrage.app.log.debug("Trying again. Attempt #: %s" % numTries)

        if numTries >= 10:
            sickrage.app.log.warning("Unable to restore file %s to %s" % (restore_file, new_file))
            return False

    return True


def backup_versioned_file(old_file, version):
    """
    Back up an old version of a file

    :param old_file: Original file, to take a backup from
    :param version: Version of file to store in backup
    :return: True if success, False if failure
    """

    numTries = 0

    new_file = '{}.v{}'.format(old_file, version)

    while not os.path.isfile(new_file):
        if not os.path.isfile(old_file):
            sickrage.app.log.debug("Not creating backup, %s doesn't exist" % old_file)
            break

        try:
            sickrage.app.log.debug("Trying to back up %s to %s" % (old_file, new_file))
            shutil.copyfile(old_file, new_file)
            sickrage.app.log.debug("Backup completed: {}".format(new_file))
            break
        except Exception as e:
            sickrage.app.log.warning("Error while trying to back up %s to %s : %r" % (old_file, new_file, e))
            numTries += 1
            time.sleep(1)
            sickrage.app.log.debug("Trying to perform backup again.")

        if numTries >= 10:
            sickrage.app.log.error("Unable to back up %s to %s please do it manually." % (old_file, new_file))
            return False

    return True


@contextmanager
def bs4_parser(markup, features="html5lib", *args, **kwargs):
    try:
        _soup = BeautifulSoup(markup, features=features, *args, **kwargs)
    except:
        _soup = BeautifulSoup(markup, features="html.parser", *args, **kwargs)

    try:
        yield _soup
    finally:
        _soup.clear(True)


def get_file_size(file):
    try:
        return os.path.getsize(file) / 1024 / 1024
    except:
        return None


def get_temp_dir():
    """
    Returns the [system temp dir]/sickrage-u501 or sickrage-myuser
    """

    import getpass

    if hasattr(os, 'getuid'):
        uid = "u%d" % (os.getuid())
    else:
        # For Windows
        try:
            uid = getpass.getuser()
        except ImportError:
            return os.path.join(tempfile.gettempdir(), "sickrage")

    return os.path.join(tempfile.gettempdir(), "sickrage-%s" % uid)


def scrub(obj):
    if isinstance(obj, dict):
        for k in obj.copy().keys():
            scrub(obj[k])
            del obj[k]
    elif isinstance(obj, list):
        for i in reversed(range(len(obj.copy()))):
            scrub(obj[i])
            del obj[i]


def convert_size(size, default=0, units=None):
    if units is None:
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

    size_regex = re.compile(r'([\d+.]+)\s?({})?'.format('|'.join(units)), re.I)

    try:
        size, unit = float(size_regex.search(str(size)).group(1) or -1), size_regex.search(str(size)).group(2) or 'B'
    except Exception:
        return default

    size *= 1024 ** units.index(unit.upper())

    return max(int(size), 0)


def random_string(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for __ in range(size))


def clean_url(url):
    """
    Returns an cleaned url starting with a scheme and folder with trailing /
    or an empty string
    """

    uses_netloc.append('scgi')

    if url and url.strip():
        url = url.strip()

        if '://' not in url:
            url = '//' + url

        scheme, netloc, path, query, fragment = urlsplit(url, 'http')

        if not path:
            path += '/'

        cleaned_url = urlunsplit((scheme, netloc, path, query, fragment))
    else:
        cleaned_url = ''

    return cleaned_url


def launch_browser(protocol=None, host=None, startport=None):
    browserurl = '{}://{}:{}/home/'.format(protocol or 'http', host, startport or 8081)

    try:
        sickrage.app.log.info("Launching browser window")

        try:
            webbrowser.open(browserurl, 2, 1)
        except webbrowser.Error:
            webbrowser.open(browserurl, 1, 1)
    except webbrowser.Error:
        print("Unable to launch a browser")


def is_ip_private(ip):
    if isinstance(ip, bytes):
        ip = ip.decode()
    return ipaddress.ip_address(ip).is_private


def is_ip_whitelisted(ip):
    to_return = False

    whitelisted_addresses = []

    if sickrage.app.config.general.ip_whitelist_enabled:
        whitelisted_addresses += sickrage.app.config.general.ip_whitelist.split(',')
    if sickrage.app.config.general.ip_whitelist_localhost_enabled:
        whitelisted_addresses += ['127.0.0.1', '::1']

    for x in whitelisted_addresses:
        try:
            if ip == x:
                to_return = True
            elif ipaddress.ip_address(ip) in ipaddress.ip_network(x):
                to_return = True
        except (TypeError, AttributeError, ValueError):
            continue

    if whitelisted_addresses and not to_return:
        sickrage.app.log.debug('IP address {} is not allowed to bypass web authentication, not found in whitelists'.format(ip))

    return to_return


def validate_url(value):
    """
    Return whether or not given value is a valid URL.
    :param value: URL address string to validate
    """

    regex = (
        r'^[a-z]+://([^/:]+{tld}|([0-9]{{1,3}}\.)'
        r'{{3}}[0-9]{{1,3}})(:[0-9]+)?(\/.*)?$'
    )

    return (True, False)[not re.compile(regex.format(tld=r'\.[a-z]{2,10}')).match(value)]


def torrent_webui_url(reset=False):
    if not reset:
        return sickrage.app.client_web_urls.get('torrent', '')

    if not sickrage.app.config.general.use_torrents or \
            not sickrage.app.config.torrent.host.lower().startswith('http') or \
            sickrage.app.config.general.torrent_method == TorrentMethod.BLACKHOLE or sickrage.app.config.general.enable_https and \
            not sickrage.app.config.torrent.host.lower().startswith('https'):
        sickrage.app.client_web_urls['torrent'] = ''
        return sickrage.app.client_web_urls['torrent']

    torrent_ui_url = re.sub('localhost|127.0.0.1', sickrage.app.web_host or get_internal_ip(), sickrage.app.config.torrent.host or '', re.I)

    def test_exists(url):
        try:
            h = requests.head(url)
            return h.status_code != 404
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout):
            return False

    if sickrage.app.config.general.torrent_method == TorrentMethod.UTORRENT:
        torrent_ui_url = '/'.join(s.strip('/') for s in (torrent_ui_url, 'gui/'))
    elif sickrage.app.config.general.torrent_method == TorrentMethod.DOWNLOAD_STATION:
        if test_exists(urljoin(torrent_ui_url, 'download/')):
            torrent_ui_url = urljoin(torrent_ui_url, 'download/')

    sickrage.app.client_web_urls['torrent'] = ('', torrent_ui_url)[test_exists(torrent_ui_url)]

    return sickrage.app.client_web_urls['torrent']


def checkbox_to_value(option, value_on=True, value_off=False):
    """
    Turns checkbox option 'on' or 'true' to value_on (1)
    any other value returns value_off (0)
    """

    if isinstance(option, list):
        option = option[-1]

    if isinstance(option, str):
        option = str(option).strip().lower()

    if option in (True, 'on', 'true', value_on) or try_int(option) > 0:
        return value_on

    return value_off


def clean_host(host, default_port=None):
    """
    Returns host or host:port or empty string from a given url or host
    If no port is found and default_port is given use host:default_port
    """

    host = host.strip()

    if host:

        match_host_port = re.search(r'(?:http.*://)?(?P<host>[^:/]+).?(?P<port>[0-9]*).*', host)

        cleaned_host = match_host_port.group('host')
        cleaned_port = match_host_port.group('port')

        if cleaned_host:

            if cleaned_port:
                host = cleaned_host + ':' + cleaned_port

            elif default_port:
                host = cleaned_host + ':' + str(default_port)

            else:
                host = cleaned_host

        else:
            host = ''

    return host


def clean_hosts(hosts, default_port=None):
    """
    Returns list of cleaned hosts by Config.clean_host

    :param hosts: list of hosts
    :param default_port: default port to use
    :return: list of cleaned hosts
    """
    cleaned_hosts = []

    for cur_host in [x.strip() for x in hosts.split(",")]:
        if cur_host:
            cleaned_host = clean_host(cur_host, default_port)
            if cleaned_host:
                cleaned_hosts.append(cleaned_host)

    if cleaned_hosts:
        cleaned_hosts = ",".join(cleaned_hosts)

    else:
        cleaned_hosts = ''

    return cleaned_hosts


def glob_escape(pathname):
    """
    Escape all special characters.
    """

    MAGIC_CHECK = re.compile(r'([*?[])')

    drive, pathname = os.path.splitdrive(pathname)
    pathname = MAGIC_CHECK.sub(r'[\1]', pathname)

    return drive + pathname


def convert_to_timedelta(time_val):
    """
    Given a *time_val* (string) such as '5d', returns a `datetime.timedelta`
    object representing the given value (e.g. `timedelta(days=5)`).  Accepts the
    following '<num><char>' formats:
    =========   ============ =========================
    Character   Meaning      Example
    =========   ============ =========================
    (none)      Milliseconds '500' -> 500 Milliseconds
    s           Seconds      '60s' -> 60 Seconds
    m           Minutes      '5m'  -> 5 Minutes
    h           Hours        '24h' -> 24 Hours
    d           Days         '7d'  -> 7 Days
    M           Months       '2M'  -> 2 Months
    y           Years        '10y' -> 10 Years
    =========   ============ =========================
    """

    try:
        num = int(time_val)
        return datetime.timedelta(milliseconds=num)
    except ValueError:
        pass
    num = int(time_val[:-1])
    if time_val.endswith('s'):
        return datetime.timedelta(seconds=num)
    elif time_val.endswith('m'):
        return datetime.timedelta(minutes=num)
    elif time_val.endswith('h'):
        return datetime.timedelta(hours=num)
    elif time_val.endswith('d'):
        return datetime.timedelta(days=num)
    elif time_val.endswith('M'):
        return datetime.timedelta(days=(num * 30))  # Yeah this is approximate
    elif time_val.endswith('y'):
        return datetime.timedelta(days=(num * 365))  # Sorry, no leap year support


def total_seconds(td):
    """
    Given a timedelta (*td*) return an integer representing the equivalent of
    Python 2.7's :meth:`datetime.timdelta.total_seconds`.
    """
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10 ** 6) / 10 ** 6


def episode_num(season=None, episode=None, **kwargs):
    """
    Convert season and episode into string
    :param season: Season number
    :param episode: Episode Number
    :keyword numbering: Absolute for absolute numbering
    :returns: a string in s01e01 format or absolute numbering
    """

    numbering = kwargs.pop('numbering', 'standard')

    if numbering == 'standard':
        if season is not None and episode:
            return 'S{0:0>2}E{1:02}'.format(season, episode)
    elif numbering == 'absolute':
        if not (season and episode) and (season or episode):
            return '{0:0>3}'.format(season or episode)


def strip_accents(name):
    try:
        name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore')
    except UnicodeDecodeError:
        pass

    if isinstance(name, bytes):
        name = name.decode()

    return name


def md5_file_hash(filename):
    blocksize = 8192
    hasher = hashlib.md5()
    with open(filename, 'rb') as afile:
        buf = afile.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(blocksize)
    return hasher.hexdigest()


def get_extension(filename):
    __, file_extension = os.path.splitext(filename)
    return file_extension


def get_external_ip():
    """Return external IP of system."""
    resp = WebSession().get('https://api.ipify.org')
    if not resp or not resp.text:
        return ''
    return resp.text


def get_internal_ip():
    """Return internal IP of system."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 1))
    return s.getsockname()[0]


def get_ip_address(hostname):
    return socket.gethostbyname(hostname)


def camelcase(s):
    parts = iter(s.split("_"))
    return next(parts) + "".join(i.title() for i in parts)


def convert_dict_keys_to_camelcase(d):
    new = {}

    for k, v in d.items():
        if isinstance(v, dict):
            v = convert_dict_keys_to_camelcase(v)
        if isinstance(k, str):
            new[camelcase(k)] = v

    return new


def flatten(nested_list):
    flat = []

    for x in nested_list:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            for sub_x in flatten(x):
                flat.append(sub_x)
        else:
            flat.append(x)

    return flat
