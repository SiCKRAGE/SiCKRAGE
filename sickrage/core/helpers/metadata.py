# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
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

import enzyme

import sickrage
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


def getFileMetadata(filename):
    try:
        p = enzyme.parse(filename)

        # Video codec
        vc = ('H264' if p.video[0].codec == 'AVC1' else 'x265' if p.video[0].codec == 'HEVC' else p.video[0].codec)

        # Audio codec
        ac = p.audio[0].codec
        try:
            ac = audio_codec_map.get(p.audio[0].codec)
        except:
            pass

        # Find title in video headers
        titles = []

        try:
            if hasattr(p, 'title') and p.title:
                titles.append(p.title)
        except:
            sickrage.srCore.srLogger.error('Failed getting title from meta')

        for video in p.video:
            try:
                if video.title:
                    titles.append(video.title)
            except:
                sickrage.srCore.srLogger.error('Failed getting title from meta')

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
