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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import os
import re
import traceback

import sickrage
from sickrage.core.common import Quality, get_quality_string
from sickrage.core.helpers import tryInt


extensions = {
    'tvshow': ['mkv', 'wmv', 'avi', 'mpg', 'mpeg', 'mp4', 'm2ts', 'iso', 'img', 'mdf', 'ts', 'm4v', 'flv'],
    'tvshow_extra': ['mds'],
    'dvd': ['vts_*', 'vob'],
    'nfo': ['nfo', 'txt', 'tag'],
    'subtitle': ['sub', 'srt', 'ssa', 'ass'],
    'subtitle_extra': ['idx'],
    'trailer': ['mov', 'mp4', 'flv']
}

codecs = {
    'audio': ['DTS', 'AC3', 'AC3D', 'MP3'],
    'video': ['x264', 'H264', 'x265', 'H265', 'DivX', 'Xvid']
}

file_sizes = {  # in MB
    'tvshow': {'min': 200},
    'trailer': {'min': 2, 'max': 199},
    'backdrop': {'min': 0, 'max': 5},
}

resolutions = {
    '2160p': {'resolution_width': 3840, 'resolution_height': 2160, 'aspect': 1.78},
    '1080p': {'resolution_width': 1920, 'resolution_height': 1080, 'aspect': 1.78},
    '1080i': {'resolution_width': 1920, 'resolution_height': 1080, 'aspect': 1.78},
    '720p': {'resolution_width': 1280, 'resolution_height': 720, 'aspect': 1.78},
    '720i': {'resolution_width': 1280, 'resolution_height': 720, 'aspect': 1.78},
    '480p': {'resolution_width': 640, 'resolution_height': 480, 'aspect': 1.33},
    '480i': {'resolution_width': 640, 'resolution_height': 480, 'aspect': 1.33},
    'default': {'resolution_width': 0, 'resolution_height': 0, 'aspect': 1},
}

audio_codec_map = {
    0x2000: 'AC3',
    0x2001: 'DTS',
    0x0055: 'MP3',
    0x0050: 'MP2',
    0x0001: 'PCM',
    0x003: 'WAV',
    0x77a1: 'TTA1',
    0x5756: 'WAV',
    0x6750: 'Vorbis',
    0xF1AC: 'FLAC',
    0x00ff: 'AAC',
}

def getResolution(filename):
    try:
        for key in resolutions:
            if key in filename.lower() and key != 'default':
                return resolutions[key]
    except:
        pass

    return resolutions['default']

def getShowImage(url, imgNum=None):
    if url is None:
        return None

    # if they provided a fanart number try to use it instead
    tempURL = url
    if imgNum:
        tempURL = url.split('-')[0] + "-" + str(imgNum) + ".jpg"

    sickrage.srCore.srLogger.debug("Fetching image from " + tempURL)

    try:
        return sickrage.srCore.srWebSession.get(tempURL).content
    except Exception:
        sickrage.srCore.srLogger.warning("There was an error trying to retrieve the image, aborting")

def getFileMetadata(filename):
    import enzyme

    try:
        p = enzyme.parse(filename)

        # Video codec
        vc = ('H264' if p.video[0].codec == 'AVC1' else 'x265' if p.video[0].codec == 'HEVC' else p.video[0].codec)

        # Audio codec
        ac = p.audio[0].codec
        try: ac = audio_codec_map.get(p.audio[0].codec)
        except: pass

        # Find title in video headers
        titles = []

        try:
            if p.title:
                titles.append(p.title)
        except:
            sickrage.srCore.srLogger.error('Failed getting title from meta: %s', traceback.format_exc())

        for video in p.video:
            try:
                if video.title:
                    titles.append(video.title)
            except:
                sickrage.srCore.srLogger.error('Failed getting title from meta: %s', traceback.format_exc())

        return {
            'titles': list(set(titles)),
            'video': vc,
            'audio': ac,
            'resolution_width': tryInt(p.video[0].width),
            'resolution_height': tryInt(p.video[0].height),
            'audio_channels': p.audio[0].channels,
        }
    except enzyme.exceptions.ParseError:
        sickrage.srCore.srLogger.debug('Failed to parse meta for %s', filename)
    except enzyme.exceptions.NoParserError:
        sickrage.srCore.srLogger.debug('No parser found for %s', filename)
    except:
        sickrage.srCore.srLogger.debug('Failed parsing %s', filename)

    return {}

def qualityFromFileMeta(filename):
    """
    Get quality from file metadata

    :param filename: Filename to analyse
    :return: Quality prefix
    """

    data = {}
    quality = Quality.UNKNOWN

    if os.path.isfile(filename):
        meta = getFileMetadata(filename)
        try:
            if meta.get('resolution_width'):
                data['resolution_width'] = meta.get('resolution_width')
                data['resolution_height'] = meta.get('resolution_height')
                data['aspect'] = round(float(meta.get('resolution_width')) / meta.get('resolution_height', 1), 2)
            else:
                data.update(getResolution(filename))
        except:
            sickrage.srCore.srLogger.debug('Error parsing metadata: %s %s', (filename, traceback.format_exc()))
            pass

        base_filename = os.path.basename(filename)
        bluray = re.search(r"blue?-?ray|hddvd|b[rd](rip|mux)", base_filename, re.I) is not None
        webdl = re.search(r"web.?dl|web(rip|mux|hd)", base_filename, re.I) is not None

        if data['resolution_height'] > 1000:
            quality = ((Quality.FULLHDTV, Quality.FULLHDBLURAY)[bluray], Quality.FULLHDWEBDL)[webdl]
        elif 680 < data['resolution_height'] < 800:
            quality = ((Quality.HDTV, Quality.HDBLURAY)[bluray], Quality.HDWEBDL)[webdl]
        elif data['resolution_height'] < 680:
            quality = (Quality.SDTV, Quality.SDDVD)[
                re.search(r'dvd|b[rd]rip|blue?-?ray', base_filename, re.I) is not None]

        sickrage.srCore.srLogger.debug("Quality from file metadata: {}".format(get_quality_string(quality)))

    return quality