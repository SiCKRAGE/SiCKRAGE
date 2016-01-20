from __future__ import unicode_literals

import ast
import base64
import ctypes
import datetime
import errno
import hashlib
import httplib
import io
import operator
import os
import platform
import random
import re
import shutil
import socket
import stat
import tempfile
import time
import traceback
import urllib2
import urlparse
import uuid
import zipfile
from _socket import timeout as SocketTimeout
from contextlib import closing, contextmanager
from itertools import cycle, izip

import cachecontrol
import certifi
import requests
import six
from bs4 import BeautifulSoup
from cachecontrol.caches import FileCache
from tornado import gen

import sickrage
from sickrage.clients import http_error_code
from sickrage.core.exceptions import MultipleShowObjectsException
from sickrage.indexers import adba
from sickrage.indexers.indexer_exceptions import indexer_episodenotfound, \
    indexer_seasonnotfound

USER_AGENTS = [
    {'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:5.0) Gecko/20100101 Firefox/5.0"},
    {"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1) Gecko/20090624 Firefox/3.5"},
    {'User-Agent': "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6"},
    {"User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1"},
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11"},
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER"},
    {
        "User-Agent": "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; LBBROWSER)"},
    {
        "User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E; LBBROWSER)"},
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 LBBROWSER"},
    {
        "User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)"},
    {
        "User-Agent": "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; QQBrowser/7.0.3698.400)"},
    {"User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)"},
    {
        "User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; 360SE)"},
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1"},
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1"},
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 SE 2.X MetaSr 1.0"},
    {
        "User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; SE 2.X MetaSr 1.0)"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:16.0) Gecko/20121026 Firefox/16.0"},
    {
        "User-Agent": "Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; zh-cn) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b13pre) Gecko/20110307 Firefox/4.0b13pre"},
    {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:16.0) Gecko/20100101 Firefox/16.0"},
    {"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; zh-CN; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15"},
    {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11"},
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11"},
    {
        "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133"},
    {"User-Agent": "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0)"},
    {"User-Agent": "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)"},
    {
        "User-Agent": "Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10"},
    {"User-Agent": "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)"},
    {"User-Agent": "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)"},
    {"User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)"},
    {"User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1"}
]

mediaExtensions = [
    'avi', 'mkv', 'mpg', 'mpeg', 'wmv',
    'ogm', 'mp4', 'iso', 'img', 'divx',
    'm2ts', 'm4v', 'ts', 'flv', 'f4v',
    'mov', 'rmvb', 'vob', 'dvr-ms', 'wtv',
    'ogv', '3gp', 'webm', 'tp'
]

subtitleExtensions = ['srt', 'sub', 'ass', 'idx', 'ssa']


def readFileBuffered(filename, reverse=False):
    blocksize = (1 << 15)
    with io.open(filename, 'rb') as fh:
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


def normalize_url(url):
    url = str(url)
    segments = url.split('/')
    correct_segments = []
    for segment in segments:
        if segment != '':
            correct_segments.append(segment)
    first_segment = str(correct_segments[0])
    if first_segment.find('http') == -1:
        correct_segments = ['http:'] + correct_segments
    correct_segments[0] = correct_segments[0] + '/'
    normalized_url = '/'.join(correct_segments)
    return normalized_url


def argToBool(x):
    """
    convert argument of unknown type to a bool:
    """

    class FalseStrings:
        val = ("", "0", "false", "f", "no", "n", "off")

    if isinstance(x, six.string_types):
        return (x.lower() not in FalseStrings.val)
    return bool(x)


def fixGlob(path):
    path = re.sub(r'\[', '[[]', path)
    return re.sub(r'(?<!\[)\]', '[]]', path)


def indentXML(elem, level=0):
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
            indentXML(elem, level + 1)
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
        base_name, sep, extension = name.rpartition('.')  # @UnusedVariable
        if base_name and extension.lower() in ['nzb', 'torrent'] + mediaExtensions:
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
    removeWordsList = {
        r'\[rartv\]$': 'searchre',
        r'\[rarbg\]$': 'searchre',
        r'\[eztv\]$': 'searchre',
        r'\[ettv\]$': 'searchre',
        r'\[cttv\]$': 'searchre',
        r'\[vtv\]$': 'searchre',
        r'\[EtHD\]$': 'searchre',
        r'\[GloDLS\]$': 'searchre',
        r'\[silv4\]$': 'searchre',
        r'\[Seedbox\]$': 'searchre',
        r'\[PublicHD\]$': 'searchre',
        r'\[AndroidTwoU\]$': 'searchre',
        r'\.\[BT\]$': 'searchre',
        r' \[1044\]$': 'searchre',
        r'\.RiPSaLoT$': 'searchre',
        r'\.GiuseppeTnT$': 'searchre',
        r'\.Renc$': 'searchre',
        r'-NZBGEEK$': 'searchre',
        r'-Siklopentan$': 'searchre',
        r'-\[SpastikusTV\]$': 'searchre',
        r'-RP$': 'searchre',
        r'-20-40$': 'searchre',
        r'\.\[www\.usabit\.com\]$': 'searchre',
        r'^\[www\.Cpasbien\.pe\] ': 'searchre',
        r'^\[www\.Cpasbien\.com\] ': 'searchre',
        r'^\[ www\.Cpasbien\.pw \] ': 'searchre',
        r'^\.www\.Cpasbien\.pw': 'searchre',
        r'^\[www\.newpct1\.com\]': 'searchre',
        r'^\[ www\.Cpasbien\.com \] ': 'searchre',
        r'- \{ www\.SceneTime\.com \}$': 'searchre',
        r'^\{ www\.SceneTime\.com \} - ': 'searchre',
        r'^\]\.\[www\.tensiontorrent.com\] - ': 'searchre',
        r'^\]\.\[ www\.tensiontorrent.com \] - ': 'searchre',
        r'- \[ www\.torrentday\.com \]$': 'searchre',
        r'^\[ www\.TorrentDay\.com \] - ': 'searchre',
        r'\[NO-RAR\] - \[ www\.torrentday\.com \]$': 'searchre',
    }

    _name = name
    for remove_string, remove_type in removeWordsList.iteritems():
        if remove_type == 'search':
            _name = _name.replace(remove_string, '')
        elif remove_type == 'searchre':
            _name = re.sub(r'(?i)' + remove_string, '', _name)

    return _name.strip('.- []{}')


def replaceExtension(filename, newExt):
    """
    >>> replaceExtension('foo.avi', 'mkv')
    'foo.mkv'
    >>> replaceExtension('.vimrc', 'arglebargle')
    '.vimrc'
    >>> replaceExtension('a.b.c', 'd')
    'a.b.d'
    >>> replaceExtension('', 'a')
    ''
    >>> replaceExtension('foo.bar', '')
    'foo.'
    """
    sepFile = filename.rpartition(".")
    if sepFile[0] == "":
        return filename
    else:
        return sepFile[0] + "." + newExt


def notTorNZBFile(filename):
    """
    Returns true if filename is not a NZB nor Torrent file

    :param filename: Filename to check
    :return: True if filename is not a NZB nor Torrent
    """

    return not (filename.endswith(".torrent") or filename.endswith(".nzb"))


def isSyncFile(filename):
    """
    Returns true if filename is a syncfile, indicating filesystem may be in flux

    :param filename: Filename to check
    :return: True if this file is a syncfile, False otherwise
    """

    extension = filename.rpartition(".")[2].lower()
    # if extension == '!sync' or extension == 'lftp-pget-status' or extension == 'part' or extension == 'bts':
    syncfiles = sickrage.SYNC_FILES
    if extension in syncfiles.split(",") or filename.startswith('.syncthing'):
        return True
    else:
        return False


def isMediaFile(filename):
    """
    Check if named file may contain media

    :param filename: Filename to check
    :return: True if this is a known media file, False if not
    """

    # ignore samples
    if re.search(r'(^|[\W_])(?<!shomin.)(sample\d*)[\W_]', filename, re.I):
        return False

    # ignore RARBG release intro
    if re.search(r'^RARBG\.\w+\.(mp4|avi|txt)$', filename, re.I):
        return False

    # ignore MAC OS's retarded "resource fork" files
    if filename.startswith('._'):
        return False

    sepFile = filename.rpartition(".")

    if re.search('extras?$', sepFile[0], re.I):
        return False

    if sepFile[2].lower() in mediaExtensions:
        return True
    else:
        return False


def isRarFile(filename):
    """
    Check if file is a RAR file, or part of a RAR set

    :param filename: Filename to check
    :return: True if this is RAR/Part file, False if not
    """

    archive_regex = r'(?P<file>^(?P<base>(?:(?!\.part\d+\.rar$).)*)\.(?:(?:part0*1\.)?rar)$)'

    if re.search(archive_regex, filename):
        return True

    return False


def isBeingWritten(filepath):
    """
    Check if file has been written in last 60 seconds

    :param filepath: Filename to check
    :return: True if file has been written recently, False if none
    """

    # Return True if file was modified within 60 seconds. it might still be being written to.
    ctime = max(os.path.getctime(filepath), os.path.getmtime(filepath))
    if ctime > time.time() - 60:
        return True

    return False


def sanitizeFileName(name):
    """
    >>> sanitizeFileName('a/b/c')
    'a-b-c'
    >>> sanitizeFileName('abc')
    'abc'
    >>> sanitizeFileName('a"b')
    'ab'
    >>> sanitizeFileName('.a.b..')
    'a.b'
    """

    # remove bad chars from the filename
    name = re.sub(r'[\\/\*]', '-', name)
    name = re.sub(r'[:"<>|?]', '', name)
    name = re.sub(ur'\u2122', '', name)  # Trade Mark Sign

    # remove leading/trailing periods and spaces
    name = name.strip(' .')

    return name


def remove_file_failed(failed_file):
    """
    Remove file from filesystem

    """

    try:
        os.remove(failed_file)
    except Exception:
        pass


def findCertainShow(showList, indexerid):
    """
    Find a show by indexer ID in the show list

    :param showList: List of shows to search in (needle)
    :param indexerid: Show to look for
    :return: result list
    """

    results = []

    if not isinstance(indexerid, list):
        indexerid = [indexerid]

    if showList and indexerid:
        results = [show for show in showList if show.indexerid in indexerid]

    if not results:
        return None

    if len(results) == 1:
        return results[0]
    elif len(results) > 1:
        raise MultipleShowObjectsException()


def makeDir(path):
    """
    Make a directory on the filesystem

    :param path: directory to make
    :return: True if success, False if failure
    """

    if not os.path.isdir(path):
        try:
            os.makedirs(path)
            # do the library update for synoindex
            sickrage.NOTIFIERS.synoindex_notifier.addFolder(path)
        except OSError:
            return False
    return True


def searchIndexerForShowID(regShowName, indexer=None, indexer_id=None, ui=None):
    """
    Contacts indexer to check for information on shows by showid

    :param regShowName: Name of show
    :param indexer: Which indexer to use
    :param indexer_id: Which indexer ID to look for
    :param ui: Custom UI for indexer use
    :return:
    """

    showNames = [re.sub('[. -]', ' ', regShowName)]

    # Query Indexers for each search term and build the list of results
    for i in sickrage.INDEXER_API().indexers if not indexer else int(indexer or []):
        # Query Indexers for each search term and build the list of results
        lINDEXER_API_PARMS = sickrage.INDEXER_API(i).api_params.copy()
        if ui is not None:
            lINDEXER_API_PARMS[b'custom_ui'] = ui
        t = sickrage.INDEXER_API(i).indexer(**lINDEXER_API_PARMS)

        for name in showNames:
            sickrage.LOGGER.debug("Trying to find " + name + " on " + sickrage.INDEXER_API(i).name)

            try:
                search = t[indexer_id] if indexer_id else t[name]
            except Exception:
                continue

            try:
                seriesname = search[0][b'seriesname']
            except Exception:
                seriesname = None

            try:
                series_id = search[0][b'id']
            except Exception:
                series_id = None

            if not (seriesname and series_id):
                continue
            ShowObj = findCertainShow(sickrage.showList, int(series_id))
            # Check if we can find the show in our list (if not, it's not the right show)
            if (indexer_id is None) and (ShowObj is not None) and (ShowObj.indexerid == int(series_id)):
                return seriesname, i, int(series_id)
            elif (indexer_id is not None) and (int(indexer_id) == int(series_id)):
                return seriesname, i, int(indexer_id)

        if indexer:
            break

    return None, None, None


def listMediaFiles(path):
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
            files += listMediaFiles(fullCurFile)

        elif isMediaFile(curFile):
            files.append(fullCurFile)

    return files


def copyFile(srcFile, destFile):
    """
    Copy a file from source to destination

    :param srcFile: Path of source file
    :param destFile: Path of destination file
    """

    try:
        shutil.copyfile(srcFile, destFile)
        shutil.copymode(srcFile, destFile)
    except OSError as e:
        raise


def moveFile(srcFile, destFile):
    """
    Move a file from source to destination

    :param srcFile: Path of source file
    :param destFile: Path of destination file
    """

    try:
        shutil.move(srcFile, destFile)
        fixSetGroupID(destFile)
    except OSError as e:
        try:
            copyFile(srcFile, destFile)
            os.unlink(srcFile)
        except Exception as e:
            raise


def link(src, dst):
    """
    Create a file link from source to destination.
    TODO: Make this unicode proof

    :param src: Source file
    :param dst: Destination file
    """

    if os.name == 'nt':
        if ctypes.windll.kernel32.CreateHardLinkW(unicode(dst), unicode(src), 0) == 0:
            raise ctypes.WinError()
    else:
        os.link(src, dst)


def hardlinkFile(srcFile, destFile):
    """
    Create a hard-link (inside filesystem link) between source and destination

    :param srcFile: Source file
    :param destFile: Destination file
    """

    try:
        link(srcFile, destFile)
        fixSetGroupID(destFile)
    except Exception as e:
        sickrage.LOGGER.warning("Failed to create hardlink of %s at %s. Error: %r. Copying instead"
                        % (srcFile, destFile, e))
        copyFile(srcFile, destFile)


def symlink(src, dst):
    """
    Create a soft/symlink between source and destination

    :param src: Source file
    :param dst: Destination file
    """

    if os.name == 'nt':
        if ctypes.windll.kernel32.CreateSymbolicLinkW(unicode(dst), unicode(src),
                                                      1 if os.path.isdir(src) else 0) in [0, 1280]:
            raise ctypes.WinError()
    else:
        os.symlink(src, dst)


def moveAndSymlinkFile(srcFile, destFile):
    """
    Move a file from source to destination, then create a symlink back from destination from source. If this fails, copy
    the file from source to destination

    :param srcFile: Source file
    :param destFile: Destination file
    """

    try:
        shutil.move(srcFile, destFile)
        fixSetGroupID(destFile)
        symlink(destFile, srcFile)
    except Exception as e:
        sickrage.LOGGER.warning("Failed to create symlink of %s at %s. Error: %r. Copying instead"
                        % (srcFile, destFile, e))
        copyFile(srcFile, destFile)


def make_dirs(path):
    """
    Creates any folders that are missing and assigns them the permissions of their
    parents
    """

    sickrage.LOGGER.debug("Checking if the path %s already exists" % path)

    if not os.path.isdir(path):
        # Windows, create all missing folders
        if os.name == 'nt' or os.name == 'ce':
            try:
                sickrage.LOGGER.debug("Folder %s didn't exist, creating it" % path)
                os.makedirs(path)
            except (OSError, IOError) as e:
                sickrage.LOGGER.error("Failed creating %s : %r" % (path, e))
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
                    sickrage.LOGGER.debug("Folder %s didn't exist, creating it" % sofar)
                    os.mkdir(sofar)
                    # use normpath to remove end separator, otherwise checks permissions against itself
                    chmodAsParent(os.path.normpath(sofar))
                    # do the library update for synoindex
                    sickrage.NOTIFIERS.synoindex_notifier.addFolder(sofar)
                except (OSError, IOError) as e:
                    sickrage.LOGGER.error("Failed creating %s : %r" % (sofar, e))
                    return False

    return True


def rename_ep_file(cur_path, new_path, old_path_length=0):
    """
    Creates all folders needed to move a file to its new location, renames it, then cleans up any folders
    left that are now empty.

    :param  cur_path: The absolute path to the file you want to move/rename
    :param new_path: The absolute path to the destination for the file WITHOUT THE EXTENSION
    :param old_path_length: The length of media file path (old name) WITHOUT THE EXTENSION
    """

    # new_dest_dir, new_dest_name = os.path.split(new_path)  # @UnusedVariable

    if old_path_length == 0 or old_path_length > len(cur_path):
        # approach from the right
        cur_file_name, cur_file_ext = os.path.splitext(cur_path)  # @UnusedVariable
    else:
        # approach from the left
        cur_file_ext = cur_path[old_path_length:]
        cur_file_name = cur_path[:old_path_length]

    if cur_file_ext[1:] in subtitleExtensions:
        # Extract subtitle language from filename
        sublang = os.path.splitext(cur_file_name)[1][1:]

        # Check if the language extracted from filename is a valid language
        if sickrage.SUBTITLESEARCHER.isValidLanguage(sublang):
            cur_file_ext = '.' + sublang + cur_file_ext

    # put the extension on the incoming file
    new_path += cur_file_ext

    make_dirs(os.path.dirname(new_path))

    # move the file
    try:
        sickrage.LOGGER.info("Renaming file from %s to %s" % (cur_path, new_path))
        shutil.move(cur_path, new_path)
    except (OSError, IOError) as e:
        sickrage.LOGGER.error("Failed renaming %s to %s : %r" % (cur_path, new_path, e))
        return False

    # clean up any old folders that are empty
    delete_empty_folders(os.path.dirname(cur_path))

    return True


def delete_empty_folders(check_empty_dir, keep_dir=None):
    """
    Walks backwards up the path and deletes any empty folders found.

    :param check_empty_dir: The path to clean (absolute path to a folder)
    :param keep_dir: Clean until this path is reached
    """

    # treat check_empty_dir as empty when it only contains these items
    ignore_items = []

    sickrage.LOGGER.info("Trying to clean any empty folders under " + check_empty_dir)

    # as long as the folder exists and doesn't contain any files, delete it
    try:
        while os.path.isdir(check_empty_dir) and check_empty_dir != keep_dir:
            check_files = os.listdir(check_empty_dir)

            if not check_files or (len(check_files) <= len(ignore_items)
                                   and all([check_file in ignore_items for check_file in check_files])):

                try:
                    # directory is empty or contains only ignore_items
                    sickrage.LOGGER.info("Deleting empty folder: " + check_empty_dir)
                    os.rmdir(check_empty_dir)

                    # do the library update for synoindex
                    sickrage.NOTIFIERS.synoindex_notifier.deleteFolder(check_empty_dir)
                except OSError as e:
                    sickrage.LOGGER.warning("Unable to delete %s. Error: %r" % (check_empty_dir, repr(e)))
                    raise StopIteration
                check_empty_dir = os.path.dirname(check_empty_dir)
            else:
                raise StopIteration
    except StopIteration:
        pass


def fileBitFilter(mode):
    """
    Strip special filesystem bits from file

    :param mode: mode to check and strip
    :return: required mode for media file
    """

    for bit in [stat.S_IXUSR, stat.S_IXGRP, stat.S_IXOTH, stat.S_ISUID, stat.S_ISGID]:
        if mode & bit:
            mode -= bit

    return mode


def chmodAsParent(childPath):
    """
    Retain permissions of parent for childs
    (Does not work for Windows hosts)

    :param childPath: Child Path to change permissions to sync from parent
    """

    if os.name == 'nt' or os.name == 'ce':
        return

    parentPath = os.path.dirname(childPath)

    if not parentPath:
        sickrage.LOGGER.debug("No parent path provided in " + childPath + ", unable to get permissions from it")
        return

    childPath = os.path.join(parentPath, os.path.basename(childPath))

    parentPathStat = os.stat(parentPath)
    parentMode = stat.S_IMODE(parentPathStat[stat.ST_MODE])

    childPathStat = os.stat(childPath)
    childPath_mode = stat.S_IMODE(childPathStat[stat.ST_MODE])

    if os.path.isfile(childPath):
        childMode = fileBitFilter(parentMode)
    else:
        childMode = parentMode

    if childPath_mode == childMode:
        return

    childPath_owner = childPathStat.st_uid
    user_id = os.geteuid()  # @UndefinedVariable - only available on UNIX

    if user_id != 0 and user_id != childPath_owner:
        sickrage.LOGGER.debug("Not running as root or owner of " + childPath + ", not trying to set permissions")
        return

    try:
        os.chmod(childPath, childMode)
        sickrage.LOGGER.debug(
                "Setting permissions for %s to %o as parent directory has %o" % (childPath, childMode, parentMode))
    except OSError:
        sickrage.LOGGER.debug("Failed to set permission for %s to %o" % (childPath, childMode))


def fixSetGroupID(childPath):
    """
    Inherid SGID from parent
    (does not work on Windows hosts)

    :param childPath: Path to inherit SGID permissions from parent
    """

    if os.name == 'nt' or os.name == 'ce':
        return

    parentPath = os.path.dirname(childPath)
    parentStat = os.stat(parentPath)
    parentMode = stat.S_IMODE(parentStat[stat.ST_MODE])

    childPath = os.path.join(parentPath, os.path.basename(childPath))

    if parentMode & stat.S_ISGID:
        parentGID = parentStat[stat.ST_GID]
        childStat = os.stat(childPath)
        childGID = childStat[stat.ST_GID]

        if childGID == parentGID:
            return

        childPath_owner = childStat.st_uid
        user_id = os.geteuid()  # @UndefinedVariable - only available on UNIX

        if user_id != 0 and user_id != childPath_owner:
            sickrage.LOGGER.debug("Not running as root or owner of " + childPath + ", not trying to set the set-group-ID")
            return

        try:
            os.chown(childPath, -1, parentGID)  # @UndefinedVariable - only available on UNIX
            sickrage.LOGGER.debug("Respecting the set-group-ID bit on the parent directory for %s" % childPath)
        except OSError:
            sickrage.LOGGER.error(
                    "Failed to respect the set-group-ID bit on the parent directory for %s (setting group ID %i)" % (
                        childPath, parentGID))


def is_anime_in_show_list():
    """
    Check if any shows in list contain anime

    :return: True if global showlist contains Anime, False if not
    """

    for show in sickrage.showList:
        if show.is_anime:
            return True
    return False


def update_anime_support():
    """Check if we need to support anime, and if we do, enable the feature"""

    sickrage.ANIMESUPPORT = is_anime_in_show_list()


def get_all_episodes_from_absolute_number(show, absolute_numbers, indexer_id=None):
    episodes = []
    season = None

    if len(absolute_numbers):
        if not show and indexer_id:
            show = findCertainShow(sickrage.showList, indexer_id)

        for absolute_number in absolute_numbers if show else []:
            ep = show.getEpisode(None, None, absolute_number=absolute_number)
            if ep:
                episodes.append(ep.episode)
                season = ep.season  # this will always take the last found season so eps that cross the season border are not handeled well

    return season, episodes


def sanitizeSceneName(name, anime=False):
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


_binOps = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.div,
    ast.Mod: operator.mod
}


def arithmeticEval(s):
    """
    A safe eval supporting basic arithmetic operations.

    :param s: expression to evaluate
    :return: value
    """
    node = ast.parse(s, mode='eval')

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            return _binOps[type(node.op)](_eval(node.left), _eval(node.right))
        else:
            raise Exception('Unsupported type {}'.format(node))

    return _eval(node.body)


def create_https_certificates(ssl_cert, ssl_key):
    """This function takes a domain name as a parameter and then creates a certificate and key with the
    domain name(replacing dots by underscores), finally signing the certificate using specified CA and
    returns the path of key and cert files. If you are yet to generate a CA then check the top comments"""

    try:
        import OpenSSL
    except ImportError:
        from sickrage.requirements import install_ssl
        install_ssl()
        import OpenSSL

    # Check happens if the certificate and key pair already exists for a domain
    if not os.path.exists(ssl_key) and os.path.exists(ssl_cert):
        # Serial Generation - Serial number must be unique for each certificate,
        serial = int(time.time())

        # Create the CA Certificate
        cakey = OpenSSL.crypto.PKey().generate_key(OpenSSL.crypto.TYPE_RSA, 2048)
        careq = OpenSSL.crypto.X509()
        careq.get_subject().CN = "Certificate Authority"
        careq.set_pubkey(cakey)
        careq.sign(cakey, "sha1")

        # Sign the CA Certificate
        cacert = OpenSSL.crypto.X509()
        cacert.set_serial_number(serial)
        cacert.gmtime_adj_notBefore(0)
        cacert.gmtime_adj_notAfter(365 * 24 * 60 * 60)
        cacert.set_issuer(careq.get_subject())
        cacert.set_subject(careq.get_subject())
        cacert.set_pubkey(careq.get_pubkey())
        cacert.sign(cakey, "sha1")

        # Generate self-signed certificate
        key = OpenSSL.crypto.PKey()
        key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)
        cert = OpenSSL.crypto.X509()
        cert.get_subject().CN = "SiCKRAGE"
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)
        cert.set_serial_number(serial)
        cert.set_issuer(cacert.get_subject())
        cert.set_pubkey(key)
        cert.sign(cakey, "sha1")

        # Save the key and certificate to disk
        try:
            # pylint: disable=E1101
            # Module has no member
            with io.open(ssl_key, 'w') as keyout:
                keyout.write(OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key))
            with io.open(ssl_cert, 'w') as certout:
                certout.write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert))
        except Exception:
            sickrage.LOGGER.error("Error creating SSL key and certificate")
            return False

    return True


def tryInt(s, s_default=0):
    """
    Try to convert to int, if it fails, the default will be returned

    :param s: Value to attempt to convert to int
    :param s_default: Default value to return on failure (defaults to 0)
    :return: integer, or default value on failure
    """

    try:
        return int(s)
    except Exception:
        return s_default


def md5_for_file(filename):
    """
    Generate an md5 hash for a file
    :param filename: File to generate md5 hash for
    :return MD5 hexdigest on success, or None on failure
    """

    try:
        md5 = hashlib.md5()
        for byte in readFileBuffered(filename):
            md5.update(byte)
        return md5.hexdigest()
    except Exception:
        return None


def get_lan_ip():
    """Returns IP of system"""

    try:
        return [l for l in (
            [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1],
            [[(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in
              [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]
        ) if l][0][0]
    except:
        return socket.gethostname()


def check_url(url):
    """
    Check if a URL exists without downloading the whole file.
    We only check the URL header.
    """
    # see also http://stackoverflow.com/questions/2924422
    # http://stackoverflow.com/questions/1140661
    good_codes = [httplib.OK, httplib.FOUND, httplib.MOVED_PERMANENTLY]

    host, path = urlparse.urlparse(url)[1:3]  # elems [1] and [2]
    try:
        conn = httplib.HTTPConnection(host)
        conn.request('HEAD', path)
        return conn.getresponse().status in good_codes
    except StandardError:
        return None


def anon_url(*url):
    """
    Return a URL string consisting of the Anonymous redirect URL and an arbitrary number of values appended.
    """
    return '{}{}'.format(sickrage.ANON_REDIRECT, ''.join(map(str, url)))


unique_key1 = hex(uuid.getnode() ** 2)  # Used in encryption v1


def encrypt(data, encryption_version=0, _decrypt=False):
    # Version 1: Simple XOR encryption (this is not very secure, but works)
    """

    :rtype: basestring
    """
    if encryption_version == 1:
        if _decrypt:
            return ''.join(chr(ord(x) ^ ord(y)) for (x, y) in izip(base64.decodestring(data), cycle(unique_key1)))
        else:
            return base64.encodestring(
                    ''.join(chr(ord(x) ^ ord(y)) for (x, y) in izip(data, cycle(unique_key1)))).strip()
    # Version 2: Simple XOR encryption (this is not very secure, but works)
    elif encryption_version == 2:
        if _decrypt:
            return ''.join(chr(ord(x) ^ ord(y)) for (x, y) in
                           izip(base64.decodestring(data), cycle(sickrage.ENCRYPTION_SECRET)))
        else:
            return base64.encodestring(
                    ''.join(chr(ord(x) ^ ord(y)) for (x, y) in izip(data, cycle(sickrage.ENCRYPTION_SECRET)))).strip()
    # Version 0: Plain text
    else:
        return data


def decrypt(data, encryption_version=0):
    return encrypt(data, encryption_version, _decrypt=True)


def full_sanitizeSceneName(name):
    return re.sub('[. -]', ' ', sanitizeSceneName(name)).lower().lstrip()


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
            attrs = ctypes.windll.kernel32.GetFileAttributesW(unicode(filepath))
            assert attrs != -1
            result = bool(attrs & 2)
        except (AttributeError, AssertionError):
            result = False
        return result

    if os.path.isdir(folder):
        if is_hidden(folder):
            return True

    return False


def real_path(path):
    """
    Returns: the canonicalized absolute pathname. The resulting path will have no symbolic link, '/./' or '/../' components.
    """
    return os.path.normpath(os.path.normcase(os.path.realpath(path)))


def validateShow(show, season=None, episode=None):
    indexer_lang = show.lang

    try:
        lINDEXER_API_PARMS = sickrage.INDEXER_API(show.indexer).api_params.copy()

        if indexer_lang and not indexer_lang == sickrage.INDEXER_DEFAULT_LANGUAGE:
            lINDEXER_API_PARMS[b'language'] = indexer_lang

        if show.dvdorder != 0:
            lINDEXER_API_PARMS[b'dvdorder'] = True

        t = sickrage.INDEXER_API(show.indexer).indexer(**lINDEXER_API_PARMS)
        if season is None and episode is None:
            return t

        return t[show.indexerid][season][episode]
    except (indexer_episodenotfound, indexer_seasonnotfound):
        pass


def set_up_anidb_connection():
    """Connect to anidb"""

    if not sickrage.USE_ANIDB:
        sickrage.LOGGER.debug("Usage of anidb disabled. Skiping")
        return False

    if not sickrage.ANIDB_USERNAME and not sickrage.ANIDB_PASSWORD:
        sickrage.LOGGER.debug("anidb username and/or password are not set. Aborting anidb lookup.")
        return False

    if not sickrage.ADBA_CONNECTION:
        def anidb_logger(msg):
            return sickrage.LOGGER.debug("anidb: %s " % msg)

        try:
            sickrage.ADBA_CONNECTION = adba.Connection(keepAlive=True, log=anidb_logger)
        except Exception as e:
            sickrage.LOGGER.warning("anidb exception msg: %r " % repr(e))
            return False

    try:
        if not sickrage.ADBA_CONNECTION.authed():
            sickrage.ADBA_CONNECTION.auth(sickrage.ANIDB_USERNAME, sickrage.ANIDB_PASSWORD)
        else:
            return True
    except Exception as e:
        sickrage.LOGGER.warning("anidb exception msg: %r " % repr(e))
        return False

    return sickrage.ADBA_CONNECTION.authed()


def makeZip(fileList, archive):
    """
    Create a ZIP of files

    :param fileList: A list of file names - full path each name
    :param archive: File name for the archive with a full path
    """

    try:
        a = zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, allowZip64=True)
        for f in fileList:
            a.write(f)
        a.close()
        return True
    except Exception as e:
        sickrage.LOGGER.error("Zip creation error: %r " % repr(e))
        return False


def extractZip(archive, targetDir):
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
            target = file(os.path.join(targetDir, filename), "wb")
            shutil.copyfileobj(source, target)
            source.close()
            target.close()
        zip_file.close()
        return True
    except Exception as e:
        sickrage.LOGGER.error("Zip extraction error: %r " % repr(e))
        return False


def backupConfigZip(fileList, archive, arcname=None):
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
        sickrage.LOGGER.error("Zip creation error: {} ".format(e.message))
        return False


def restoreConfigZip(archive, targetDir):
    """
    Restores a Config ZIP file back in place

    :param archive: ZIP filename
    :param targetDir: Directory to restore to
    :return: True on success, False on failure
    """

    try:
        if not os.path.exists(targetDir):
            os.mkdir(targetDir)
        else:
            def path_leaf(path):
                head, tail = os.path.split(path)
                return tail or os.path.basename(head)

            bakFilename = '{0}-{1}'.format(path_leaf(targetDir), datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
            shutil.move(targetDir, os.path.join(os.path.dirname(targetDir), bakFilename))

        with zipfile.ZipFile(archive, 'r', allowZip64=True) as zip_file:
            for member in zip_file.namelist():
                zip_file.extract(member, targetDir)

        return True
    except Exception as e:
        sickrage.LOGGER.error("Zip extraction error: {}".format(e.message))
        removetree(targetDir)


def backupAll(backupDir):
    source = []

    filesList = ['sickrage.db',
                 'scheduer.db',
                 'config.ini',
                 'failed.db',
                 'cache.db',
                 sickrage.CONFIG_FILE]

    for f in filesList:
        fp = os.path.join(sickrage.DATA_DIR, f)
        if os.path.exists(fp):
            source += [fp]

    if sickrage.CACHE_DIR:
        for (path, dirs, files) in os.walk(sickrage.CACHE_DIR, topdown=True):
            for dirname in dirs:
                if path == sickrage.CACHE_DIR and dirname not in ['images']:
                    dirs.remove(dirname)
            for filename in files:
                source += [os.path.join(path, filename)]

    target = os.path.join(backupDir, 'sickrage-{}.zip'.format(datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
    return backupConfigZip(source, target, sickrage.DATA_DIR)


def touchFile(fname, atime=None):
    """
    Touch a file (change modification date)

    :param fname: Filename to touch
    :param atime: Specific access time (defaults to None)
    :return: True on success, False on failure
    """

    if atime is not None:
        try:
            with file(fname, 'a'):
                os.utime(fname, (atime, atime))
                return True
        except OSError as e:
            if e.errno == errno.ENOSYS:
                sickrage.LOGGER.debug("File air date stamping not available on your OS. Please disable setting")
            elif e.errno == errno.EACCES:
                sickrage.LOGGER.error(
                        "File air date stamping failed(Permission denied). Check permissions for file: %s" % fname)
            else:
                sickrage.LOGGER.error("File air date stamping failed. The error is: %r" % e)

    return False


def _getTempDir():
    """
    Returns the [system temp dir]/thetvdb-u501 (or
    thetvdb-myuser)
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


def codeDescription(status_code):
    """
    Returns the description of the URL error code
    """
    if status_code in http_error_code:
        return http_error_code[status_code]
    else:
        sickrage.LOGGER.error("Unknown error code: %s. Please submit an issue" % status_code)
        return 'unknown'


def _setUpSession(session=None, headers=None, params=None):
    """
    Returns a session initialized with default cache and parameter settings

    :param session: session object to (re)use
    :param headers: Headers to pass to session
    :return: session object
    """

    # request session
    if headers is None:
        headers = {}
    session = session or requests.Session()
    sessionCache = FileCache(os.path.join(sickrage.CACHE_DIR or _getTempDir(), 'sessions'), use_dir_lock=True)
    session = cachecontrol.CacheControl(sess=session, cache=sessionCache, cache_etags=False)

    # request session headers
    session.headers.update(headers)
    session.headers.update({'Accept-Encoding': 'gzip,deflate'})
    session.headers.update(random.choice(USER_AGENTS))

    # request session clear residual referer
    if 'Referer' in session.headers and 'Referer' not in headers:
        session.headers.pop('Referer')

    # request session ssl verify
    session.verify = certifi.where() if sickrage.SSL_VERIFY else False

    # request session proxies
    if 'Referer' not in session.headers and sickrage.PROXY_SETTING:
        sickrage.LOGGER.debug("Using global proxy: " + sickrage.PROXY_SETTING)
        scheme, address = urllib2.splittype(sickrage.PROXY_SETTING)
        address = sickrage.PROXY_SETTING if scheme else 'http://' + sickrage.PROXY_SETTING
        session.proxies = {
            "http": address,
            "https": address,
        }
        session.headers.update({'Referer': address})

    if 'Content-Type' in session.headers:
        session.headers.pop('Content-Type')

    if params and isinstance(params, (list, dict)):
        for param in params:
            if isinstance(params[param], unicode):
                params[param] = params[param].encode('utf-8')
        session.params = params

    return session


def getURL(url, post_data=None, params=None, headers=None, timeout=30, session=None, json=False, needBytes=False):
    """
    Returns a byte-string retrieved from the url provider.
    """

    if headers is None:
        headers = {}
    if not requests.__version__ < (2, 8):
        sickrage.LOGGER.debug("Requests version 2.8+ needed to avoid SSL cert verify issues, please upgrade your copy")

    url = normalize_url(url)
    session = _setUpSession(session or requests.Session(), headers, params)

    try:
        # decide if we get or post data to server
        if post_data:
            if isinstance(post_data, (list, dict)):
                for param in post_data:
                    if isinstance(post_data[param], unicode):
                        post_data[param] = post_data[param].encode('utf-8')

            session.headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
            resp = session.post(url, data=post_data, timeout=timeout, allow_redirects=True, verify=session.verify)
        else:
            resp = session.get(url, timeout=timeout, allow_redirects=True, verify=session.verify)

        if not resp.ok:
            sickrage.LOGGER.debug("Requested getURL %s returned status code is %s: %s"
                          % (url, resp.status_code, codeDescription(resp.status_code)))
            return None

    except (SocketTimeout, TypeError) as e:
        sickrage.LOGGER.warning("Connection timed out (sockets) accessing getURL %s Error: %r" % (url, e))
        return None
    except requests.exceptions.HTTPError as e:
        sickrage.LOGGER.debug("HTTP error in getURL %s Error: %r" % (url, e))
        return None
    except requests.exceptions.ConnectionError as e:
        sickrage.LOGGER.debug("Connection error to getURL %s Error: %r" % (url, e))
        return None
    except requests.exceptions.Timeout as e:
        sickrage.LOGGER.warning("Connection timed out accessing getURL %s Error: %r" % (url, e))
        return None
    except requests.exceptions.ContentDecodingError:
        sickrage.LOGGER.debug("Content-Encoding was gzip, but content was not compressed. getURL: %s" % url)
        sickrage.LOGGER.debug(traceback.format_exc())
        return None
    except Exception as e:
        sickrage.LOGGER.debug("Unknown exception in getURL %s Error: %r" % (url, e))
        sickrage.LOGGER.debug(traceback.format_exc())
        return None

    return (resp.text, resp.content)[needBytes] if not json else resp.json()


def download_file(url, filename, session=None, headers=None):
    """
    Downloads a file specified

    :param url: Source URL
    :param filename: Target file on filesystem
    :param session: request session to use
    :param headers: override existing headers in request session
    :return: True on success, False on failure
    """

    if headers is None:
        headers = {}
    url = normalize_url(url)
    session = _setUpSession(session, headers)
    session.stream = True

    try:
        with closing(session.get(url, allow_redirects=True, verify=session.verify)) as resp:
            if not resp.ok:
                sickrage.LOGGER.debug("Requested download url %s returned status code is %s: %s"
                              % (url, resp.status_code, codeDescription(resp.status_code)))
                return False

            try:
                with io.open(filename, 'wb') as fp:
                    for chunk in resp.iter_content(chunk_size=1024):
                        if chunk:
                            fp.write(chunk)
                            fp.flush()

                chmodAsParent(filename)
            except Exception:
                sickrage.LOGGER.warning("Problem setting permissions or writing file to: %s" % filename)

    except (SocketTimeout, TypeError) as e:
        remove_file_failed(filename)
        sickrage.LOGGER.warning("Connection timed out (sockets) while loading download URL %s Error: %r" % (url, e))
        return None
    except requests.exceptions.HTTPError as e:
        remove_file_failed(filename)
        sickrage.LOGGER.warning("HTTP error %r while loading download URL %s " % (e), url)
        return False
    except requests.exceptions.ConnectionError as e:
        remove_file_failed(filename)
        sickrage.LOGGER.warning("Connection error %r while loading download URL %s " % (e), url)
        return False
    except requests.exceptions.Timeout as e:
        remove_file_failed(filename)
        sickrage.LOGGER.warning("Connection timed out %r while loading download URL %s " % (e), url)
        return False
    except EnvironmentError as e:
        remove_file_failed(filename)
        sickrage.LOGGER.warning("Unable to save the file: %r " % e)
        return False
    except Exception:
        remove_file_failed(filename)
        sickrage.LOGGER.warning("Unknown exception while loading download URL %s : %r" % (url, traceback.format_exc()))
        return False

    return True


def get_size(start_path='.'):
    """
    Find the total dir and filesize of a path

    :param start_path: Path to recursively count size
    :return: total filesize
    """

    if not os.path.isdir(start_path):
        return -1

    total_size = 0
    for dirpath, _, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total_size += os.path.getsize(fp)
            except OSError as e:
                sickrage.LOGGER.error("Unable to get size for file %s Error: %r" % (fp, e))
                sickrage.LOGGER.debug(traceback.format_exc())
    return total_size


def generateApiKey():
    """ Return a new randomized API_KEY"""

    try:
        from hashlib import md5
    except ImportError:
        from md5 import md5

    # Create some values to seed md5
    t = str(time.time())
    r = str(random.random())

    # Create the md5 instance and give it the current time
    m = md5(t)

    # Update the md5 instance with the random variable
    m.update(r)

    # Return a hex digest of the md5, eg 49f68a5c8493ec2c0bf489821c21fc3b
    sickrage.LOGGER.info("New API generated")
    return m.hexdigest()


def pretty_filesize(file_bytes):
    """Return humanly formatted sizes from bytes"""
    for mod in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if file_bytes < 1024.00:
            return "%3.2f %s" % (file_bytes, mod)
        file_bytes /= 1024.00


def remove_article(text=''):
    """Remove the english articles from a text string"""

    return re.sub(ur'(?i)^(?:(?:A(?!\s+to)n?)|The)\s(\w)', r'\1', text)


def generateCookieSecret():
    """Generate a new cookie secret"""

    return base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)


def verify_freespace(src, dest, oldfile=None):
    """
    Checks if the target system has enough free space to copy or move a file.

    :param src: Source filename
    :param dest: Destination path
    :param oldfile: File to be replaced (defaults to None)
    :return: True if there is enough space for the file, False if there isn't. Also returns True if the OS doesn't support this option
    """

    if not isinstance(oldfile, list):
        oldfile = [oldfile]

    sickrage.LOGGER.debug("Trying to determine free space on destination drive")

    if hasattr(os, 'statvfs'):  # POSIX
        def disk_usage(path):
            st = os.statvfs(path)
            free = st.f_bavail * st.f_frsize
            return free

    elif os.name == 'nt':  # Windows
        import sys

        def disk_usage(path):
            _, total, free = ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong()
            if sys.version_info >= (3,) or isinstance(path, unicode):
                fun = ctypes.windll.kernel32.GetDiskFreeSpaceExW
            else:
                fun = ctypes.windll.kernel32.GetDiskFreeSpaceExA
            ret = fun(path, ctypes.byref(_), ctypes.byref(total), ctypes.byref(free))
            if ret == 0:
                sickrage.LOGGER.warning("Unable to determine free space, something went wrong")
                raise ctypes.WinError()
            return free.value
    else:
        sickrage.LOGGER.info("Unable to determine free space on your OS")
        return True

    if not os.path.isfile(src):
        sickrage.LOGGER.warning("A path to a file is required for the source. " + src + " is not a file.")
        return True

    try:
        diskfree = disk_usage(dest)
    except Exception:
        sickrage.LOGGER.warning("Unable to determine free space, so I will assume there is enough.")
        return True

    neededspace = int(os.path.getsize(src))

    if oldfile:
        for f in oldfile:
            if os.path.isfile(f.location):
                diskfree += os.path.getsize(f.location)

    if diskfree > neededspace:
        return True
    else:
        sickrage.LOGGER.warning("Not enough free space: Needed: %s bytes ( %s ), found: %s bytes ( %s )"
                        % (neededspace, pretty_filesize(neededspace), diskfree, pretty_filesize(diskfree)))
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


def isFileLocked(checkfile, writeLockCheck=False):
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
        with io.open(checkfile, 'rb'):
            pass
    except IOError:
        return True

    if writeLockCheck:
        lockFile = checkfile + ".lckchk"
        if os.path.exists(lockFile):
            os.remove(lockFile)
        try:
            os.rename(checkfile, lockFile)
            gen.sleep(1)
            os.rename(lockFile, checkfile)
        except (Exception, OSError, IOError) as e:
            return True

    return False


def getDiskSpaceUsage(diskPath=None):
    """
    returns the free space in human readable bytes for a given path or False if no path given
    :param diskPath: the filesystem path being checked
    """
    if diskPath and os.path.exists(diskPath):
        if platform.system() == 'Windows':
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(diskPath), None, None,
                                                       ctypes.pointer(free_bytes))
            return pretty_filesize(free_bytes.value)
        else:
            st = os.statvfs(diskPath)
            return pretty_filesize(st.f_bavail * st.f_frsize)
    else:
        return False


def removetree(tgt):
    def error_handler(func, path, execinfo):
        # figure out recovery based on error...
        e = execinfo[1]
        if e.errno == errno.ENOENT or not os.path.exists(path):
            return  # path does not exist
        if func in (os.rmdir, os.remove) and e.errno == errno.EACCES:
            os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
            func(path)  # read-only file; make writable and retry
        raise e

    # Rename target directory to temporary value, then remove it
    count = 0
    while count < 10:  # prevents indefinite loop
        count += 1
        tmp = os.path.join(os.path.dirname(tgt), "_removetree_tmp_%d" % (count))
        try:
            os.rename(tgt, tmp)
            shutil.rmtree(tmp, onerror=error_handler)
            break
        except OSError as e:
            gen.sleep(1)
            if e.errno in [errno.EACCES, errno.ENOTEMPTY]:
                continue  # Try another temp name
            if e.errno == errno.EEXIST:
                shutil.rmtree(tmp, ignore_errors=True)  # Try to clean up old files
                continue  # Try another temp name
            if e.errno == errno.ENOENT:
                break  # 'src' does not exist(?)
            raise  # Other error - propagate
    return


def restoreDB(srcDir, dstDir):
    try:
        filesList = ['sickrage.db',
                     'scheduler.db',
                     'config.ini',
                     'failed.db',
                     'cache.db',
                     sickrage.CONFIG_FILE]

        for filename in filesList:
            srcFile = os.path.join(srcDir, filename)
            dstFile = os.path.join(dstDir, filename)
            bakFile = os.path.join(dstDir, '{0}.bak-{1}'
                                   .format(filename, datetime.datetime.now().strftime('%Y%m%d_%H%M%S')))

            if os.path.exists(srcFile):
                if os.path.isfile(dstFile):
                    shutil.move(dstFile, bakFile)
                shutil.move(srcFile, dstFile)

        return True
    except Exception:
        return False


def restoreVersionedFile(backup_file, version):
    """
    Restore a file version to original state

    :param backup_file: File to restore
    :param version: Version of file to restore
    :return: True on success, False on failure
    """

    numTries = 0

    new_file, _ = os.path.splitext(backup_file)
    restore_file = '{}.v{}'.format(new_file, version)

    if not os.path.isfile(new_file):
        sickrage.LOGGER.debug("Not restoring, %s doesn't exist" % new_file)
        return False

    try:
        sickrage.LOGGER.debug("Trying to backup %s to %s.r%s before restoring backup"
                      % (new_file, new_file, version))

        shutil.move(new_file, new_file + '.' + 'r' + str(version))
    except Exception as e:
        sickrage.LOGGER.warning("Error while trying to backup file %s before proceeding with restore: %r"
                        % (restore_file, e))
        return False

    while not os.path.isfile(new_file):
        if not os.path.isfile(restore_file):
            sickrage.LOGGER.debug("Not restoring, %s doesn't exist" % restore_file)
            break

        try:
            sickrage.LOGGER.debug("Trying to restore file %s to %s" % (restore_file, new_file))
            shutil.copy(restore_file, new_file)
            sickrage.LOGGER.debug("Restore done")
            break
        except Exception as e:
            sickrage.LOGGER.warning("Error while trying to restore file %s. Error: %r" % (restore_file, e))
            numTries += 1
            gen.sleep(1)
            sickrage.LOGGER.debug("Trying again. Attempt #: %s" % numTries)

        if numTries >= 10:
            sickrage.LOGGER.warning("Unable to restore file %s to %s" % (restore_file, new_file))
            return False

    return True


def backupVersionedFile(old_file, version):
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
            sickrage.LOGGER.debug("Not creating backup, %s doesn't exist" % old_file)
            break

        try:
            sickrage.LOGGER.debug("Trying to back up %s to %s" % (old_file, new_file))
            shutil.copyfile(old_file, new_file)
            sickrage.LOGGER.debug("Backup done")
            break
        except Exception as e:
            sickrage.LOGGER.warning("Error while trying to back up %s to %s : %r" % (old_file, new_file, e))
            numTries += 1
            gen.sleep(1)
            sickrage.LOGGER.debug("Trying again.")

        if numTries >= 10:
            sickrage.LOGGER.error("Unable to back up %s to %s please do it manually." % (old_file, new_file))
            return False

    return True

def flatten_dict(d, delimiter='.'):
    def expand(key, value):
        if isinstance(value, dict):
            return [(delimiter.join([key, k]), v) for k, v in flatten_dict(value, delimiter).items()]
        else:return [(key, value)]
    return dict([item for k, v in d.items() for item in expand(k, v)])

@contextmanager
def bs4_parser(markup, features="html5lib", *args, **kwargs):

    _soup = BeautifulSoup(markup, features=features, *args, **kwargs)

    try:
        yield _soup
    finally:
        _soup.clear(True)