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
import re

import knowit

import sickrage

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


def get_resolution(filename):
    for key in resolutions:
        if key in filename.lower() and key != 'default':
            return resolutions[key]
    return resolutions['default']


def get_file_metadata(filename):
    try:
        p = knowit.know(filename)

        # Video codec
        vc = ('H264' if p['video'][0]['codec'] == 'AVC1' else 'x265' if p['video'][0]['codec'] == 'HEVC' else
        p['video'][0]['codec'])

        # Audio codec
        ac = p['audio'][0]['codec']

        # Resolution
        width = re.match(r'(\d+)', str(p['video'][0]['width']))
        height = re.match(r'(\d+)', str(p['video'][0]['height']))

        return {
            'title': p.get('title', ""),
            'video': vc,
            'audio': ac,
            'resolution_width': int(width.group(1)) if width else 0,
            'resolution_height': int(height.group(1)) if height else 0,
            'audio_channels': p['audio'][0]['channels'],
        }
    except Exception:
        sickrage.app.log.debug('Failed to parse meta for {}'.format(filename))

    return {}


