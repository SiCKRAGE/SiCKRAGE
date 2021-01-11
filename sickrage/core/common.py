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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


# CPU Presets for sleep timers
import enum
import operator
import pathlib
import re
from functools import reduce

from aenum import IntEnum, extend_enum

from sickrage.core.helpers.metadata import get_file_metadata, get_resolution

countryList = {'Australia': 'AU',
               'Canada': 'CA',
               'USA': 'US'}

dateFormat = '%Y-%m-%d'
dateTimeFormat = '%Y-%m-%d %H:%M:%S'
timeFormat = '%A %I:%M %p'

# Other constants
MULTI_EP_RESULT = -1
SEASON_RESULT = -2


class EpisodeStatus(IntEnum):
    UNKNOWN = -1  # SHOULD NEVER HAPPEN
    UNAIRED = 1  # EPISODES THAT HAVEN'T AIRED YET
    SNATCHED = 2  # QUALIFIED WITH QUALITY
    WANTED = 3  # EPISODES WE DON'T HAVE BUT WANT TO GET
    DOWNLOADED = 4  # QUALIFIED WITH QUALITY
    SKIPPED = 5  # EPISODES WE DON'T WANT
    ARCHIVED = 6  # EPISODES THAT YOU DON'T HAVE LOCALLY (COUNTS TOWARD DOWNLOAD COMPLETION STATS)
    IGNORED = 7  # EPISODES THAT YOU DON'T WANT INCLUDED IN YOUR DOWNLOAD STATS
    SNATCHED_PROPER = 9  # QUALIFIED WITH QUALITY
    SUBTITLED = 10  # QUALIFIED WITH QUALITY
    FAILED = 11  # EPISODE DOWNLOADED OR SNATCHED WE DON'T WANT
    SNATCHED_BEST = 12  # EPISODE REDOWNLOADED USING BEST QUALITY
    MISSED = 13

    @classmethod
    def _strings(cls):
        return {
            cls.UNKNOWN.name: "Unknown",
            cls.UNAIRED.name: "Unaired",
            cls.SNATCHED.name: "Snatched",
            cls.SNATCHED_PROPER.name: "Snatched (Proper)",
            cls.SNATCHED_BEST.name: "Snatched (Best)",
            cls.DOWNLOADED.name: "Downloaded",
            cls.SKIPPED.name: "Skipped",
            cls.WANTED.name: "Wanted",
            cls.ARCHIVED.name: "Archived",
            cls.IGNORED.name: "Ignored",
            cls.SUBTITLED.name: "Subtitled",
            cls.FAILED.name: "Failed",
            cls.MISSED.name: "Missed"
        }

    @classmethod
    def _prefix_strings(cls):
        return {
            cls.DOWNLOADED.name: _("Downloaded"),
            cls.SNATCHED.name: _("Snatched"),
            cls.SNATCHED_PROPER.name: _("Snatched (Proper)"),
            cls.SNATCHED_BEST.name: _("Snatched (Best)"),
            cls.ARCHIVED.name: _("Archived"),
            cls.FAILED.name: _("Failed"),
            cls.MISSED.name: _("Missed")
        }

    @property
    def display_name(self):
        status, quality = Quality.split_composite_status(self)
        if quality == Qualities.NONE:
            return self._strings()[status.name]
        return self._strings()[status.name] + " (" + quality.display_name + ")"

    @property
    def prefix_name(self):
        return self._prefix_strings()[self.name]

    @staticmethod
    def composites(status):
        return {
            EpisodeStatus.DOWNLOADED: [EpisodeStatus[f"{EpisodeStatus.DOWNLOADED.name}_{q.name}"] for q in Qualities if not q.is_preset],
            EpisodeStatus.SNATCHED: [EpisodeStatus[f"{EpisodeStatus.SNATCHED.name}_{q.name}"] for q in Qualities if not q.is_preset],
            EpisodeStatus.SNATCHED_PROPER: [EpisodeStatus[f"{EpisodeStatus.SNATCHED_PROPER.name}_{q.name}"] for q in Qualities if not q.is_preset],
            EpisodeStatus.SNATCHED_BEST: [EpisodeStatus[f"{EpisodeStatus.SNATCHED_BEST.name}_{q.name}"] for q in Qualities if not q.is_preset],
            EpisodeStatus.ARCHIVED: [EpisodeStatus[f"{EpisodeStatus.ARCHIVED.name}_{q.name}"] for q in Qualities if not q.is_preset],
            EpisodeStatus.FAILED: [EpisodeStatus[f"{EpisodeStatus.FAILED.name}_{q.name}"] for q in Qualities if not q.is_preset],
            EpisodeStatus.IGNORED: [EpisodeStatus[f"{EpisodeStatus.IGNORED.name}_{q.name}"] for q in Qualities if not q.is_preset],
        }[status]


class Overview(enum.Enum):
    UNAIRED = EpisodeStatus.UNAIRED.value  # 1
    SNATCHED = EpisodeStatus.SNATCHED.value  # 2
    WANTED = EpisodeStatus.WANTED.value  # 3
    GOOD = EpisodeStatus.DOWNLOADED.value  # 4
    SKIPPED = EpisodeStatus.SKIPPED.value  # 5
    SNATCHED_PROPER = EpisodeStatus.SNATCHED_PROPER.value  # 9
    SNATCHED_BEST = EpisodeStatus.SNATCHED_BEST.value  # 12
    MISSED = EpisodeStatus.MISSED.value  # 13
    LOW_QUALITY = 50

    @property
    def _strings(self):
        return {
            self.SKIPPED.name: "skipped",
            self.WANTED.name: "wanted",
            self.LOW_QUALITY.name: "low-quality",
            self.GOOD.name: "good",
            self.UNAIRED.name: "unaired",
            self.SNATCHED.name: "snatched",
            self.SNATCHED_BEST.name: "snatched",
            self.SNATCHED_PROPER.name: "snatched",
            self.MISSED.name: "missed"
        }

    @property
    def css_name(self):
        return self._strings[self.name]


class Quality(object):
    @staticmethod
    def combine_qualities(anyQualities, bestQualities):
        any_quality = 0
        best_quality = 0

        if anyQualities:
            any_quality = reduce(operator.or_, anyQualities, any_quality)
        if bestQualities:
            best_quality = reduce(operator.or_, bestQualities, best_quality)

        return any_quality | (best_quality << 16)

    @staticmethod
    def split_quality(quality):
        any_qualities = [quality_flag for quality_flag in Qualities if
                         quality_flag in Qualities(quality) and quality_flag and not quality_flag.is_preset]

        best_qualities = [quality_flag for quality_flag in Qualities if
                          quality_flag in Qualities(quality >> 16) and quality_flag and not quality_flag.is_preset]

        return sorted(any_qualities), sorted(best_qualities)

    @staticmethod
    def name_quality(name, anime=False):
        """
        Return The quality from an episode File renamed by SiCKRAGE
        If no quality is achieved it will try sceneQuality regex

        :param anime: Boolean to indicate if the show we're resolving is Anime
        :return: Quality prefix
        """

        # Try Scene names first
        quality = Quality.scene_quality(name, anime)
        if quality != Qualities.UNKNOWN:
            return quality

        quality = Quality.quality_from_file_meta(name)
        if quality != Qualities.UNKNOWN:
            return quality

        if name.lower().endswith(".ts"):
            return Qualities.RAWHDTV

        return Qualities.UNKNOWN

    @staticmethod
    def scene_quality(name, anime=False):
        """
        Return The quality from the scene episode File

        :param name: Episode filename to analyse
        :param anime: Boolean to indicate if the show we're resolving is Anime
        :return: Quality prefix
        """

        ret = Qualities.UNKNOWN
        if not name:
            return ret

        name = pathlib.Path(name).name

        check_name = lambda l, func: func([re.search(x, name, re.I) for x in l])

        if anime:
            dvd_options = check_name([r"dvd", r"dvdrip"], any)
            blue_ray_options = check_name([r"BD", r"blue?-?ray"], any)
            sd_options = check_name([r"360p", r"480p", r"848x480", r"XviD"], any)
            hd_options = check_name([r"720p", r"1280x720", r"960x720"], any)
            full_hd = check_name([r"1080p", r"1920x1080"], any)

            if sd_options and not blue_ray_options and not dvd_options:
                ret = Qualities.SDTV
            elif dvd_options:
                ret = Qualities.SDDVD
            elif hd_options and not blue_ray_options and not full_hd:
                ret = Qualities.HDTV
            elif full_hd and not blue_ray_options and not hd_options:
                ret = Qualities.FULLHDTV
            elif hd_options and not blue_ray_options and not full_hd:
                ret = Qualities.HDWEBDL
            elif blue_ray_options and hd_options and not full_hd:
                ret = Qualities.HDBLURAY
            elif blue_ray_options and full_hd and not hd_options:
                ret = Qualities.FULLHDBLURAY

            return ret

        if (check_name([r"480p|\bweb\b|web.?dl|web(rip|mux|hd)|[sph]d.?tv|dsr|tv(rip|mux)|satrip", r"xvid|divx|[xh].?26[45]"], all)
                and not check_name([r"(720|1080|2160|4320)[pi]"], all)
                and not check_name([r"hr.ws.pdtv.[xh].?26[45]"], any)):
            ret = Qualities.SDTV
        elif (check_name([r"dvd(rip|mux)|b[rd](rip|mux)|blue?-?ray", r"xvid|divx|[xh].?26[45]"], all)
              and not check_name([r"(720|1080|2160|4320)[pi]"], all)
              and not check_name([r"hr.ws.pdtv.[xh].?26[45]"], any)):
            ret = Qualities.SDDVD
        elif (check_name([r"720p", r"hd.?tv", r"[xh].?26[45]"], all)
              or check_name([r"720p", r"hevc", r"[xh].?26[45]"], all)
              or check_name([r"hr.ws.pdtv.[xh].?26[45]"], any) and not check_name([r"1080[pi]"], all)):
            ret = Qualities.HDTV
        elif (check_name([r"720p|1080i", r"hd.?tv", r"mpeg-?2"], all)
              or check_name([r"1080[pi].hdtv", r"h.?26[45]"], all)):
            ret = Qualities.RAWHDTV
        elif (check_name([r"1080p", r"hd.?tv", r"[xh].?26[45]"], all)
              or check_name([r"1080p", r"hevc", r"[xh].?26[45]"], all)):
            ret = Qualities.FULLHDTV
        elif (check_name([r"720p", r"\bweb\b|web.?dl|web(rip|mux|hd)"], all)
              or check_name([r"720p", r"itunes", r"[xh].?26[45]"], all)):
            ret = Qualities.HDWEBDL
        elif (check_name([r"1080p", r"\bweb\b|web.?dl|web(rip|mux|hd)"], all)
              or check_name([r"1080p", r"itunes", r"[xh].?26[45]"], all)):
            ret = Qualities.FULLHDWEBDL
        elif check_name([r"720p", r"blue?-?ray|hddvd|b[rd](rip|mux)", r"[xh].?26[45]"], all):
            ret = Qualities.HDBLURAY
        elif check_name([r"1080p", r"blue?-?ray|hddvd|b[rd](rip|mux)", r"[xh].?26[45]"], all):
            ret = Qualities.FULLHDBLURAY
        elif check_name([r"2160p", r"hd.?tv", r"[xh].?26[45]"], all):
            ret = Qualities.UHD_4K_TV
        elif check_name([r"4320p", r"hd.?tv", r"[xh].?26[45]"], all):
            ret = Qualities.UHD_8K_TV
        elif (check_name([r"2160p", r"\bweb\b|web.?dl|web(rip|mux|hd)"], all)
              or check_name([r"2160p", r"itunes", r"[xh].?26[45]"], all)):
            ret = Qualities.UHD_4K_WEBDL
        elif (check_name([r"4320p", r"\bweb\b|web.?dl|web(rip|mux|hd)"], all)
              or check_name([r"4320p", r"itunes", r"[xh].?26[45]"], all)):
            ret = Qualities.UHD_8K_WEBDL
        elif check_name([r"2160p", r"blue?-?ray|hddvd|b[rd](rip|mux)", r"[xh].?26[45]"], all):
            ret = Qualities.UHD_4K_BLURAY
        elif check_name([r"4320p", r"blue?-?ray|hddvd|b[rd](rip|mux)", r"[xh].?26[45]"], all):
            ret = Qualities.UHD_8K_BLURAY

        return ret

    @staticmethod
    def composite_status(status, quality):
        return EpisodeStatus(status + 100 * quality)

    @staticmethod
    def split_composite_status(status):
        """Returns a tuple containing (status, quality)"""
        if status == EpisodeStatus.UNKNOWN:
            return status, Qualities.UNKNOWN

        for q in sorted(Qualities, reverse=True):
            if status > q * 100:
                return EpisodeStatus(status - q * 100), q

        return status, Qualities.NONE

    @staticmethod
    def quality_from_file_meta(filename):
        """
        Get quality from file metadata

        :param filename: Filename to analyse
        :return: Quality prefix
        """

        data = {}
        quality = Qualities.UNKNOWN

        try:
            if pathlib.Path(filename).is_file():
                meta = get_file_metadata(filename)

                if meta.get('resolution_width') and meta.get('resolution_height'):
                    data['resolution_width'] = meta.get('resolution_width')
                    data['resolution_height'] = meta.get('resolution_height')
                    data['aspect'] = round(float(meta.get('resolution_width')) / meta.get('resolution_height', 1), 2)
                else:
                    data.update(get_resolution(filename))

                base_filename = pathlib.Path(filename).name
                bluray = re.search(r"blue?-?ray|hddvd|b[rd](rip|mux)", base_filename, re.I) is not None
                webdl = re.search(r"\bweb\b|web.?dl|web(rip|mux|hd)", base_filename, re.I) is not None

                if 3240 < data['resolution_height']:
                    quality = ((Qualities.UHD_8K_TV, Qualities.UHD_8K_BLURAY)[bluray], Qualities.UHD_8K_WEBDL)[webdl]
                if 1620 < data['resolution_height'] <= 3240:
                    quality = ((Qualities.UHD_4K_TV, Qualities.UHD_4K_BLURAY)[bluray], Qualities.UHD_4K_WEBDL)[webdl]
                elif 800 < data['resolution_height'] <= 1620:
                    quality = ((Qualities.FULLHDTV, Qualities.FULLHDBLURAY)[bluray], Qualities.FULLHDWEBDL)[webdl]
                elif 680 < data['resolution_height'] < 800:
                    quality = ((Qualities.HDTV, Qualities.HDBLURAY)[bluray], Qualities.HDWEBDL)[webdl]
                elif data['resolution_height'] < 680:
                    quality = (Qualities.SDTV, Qualities.SDDVD)[re.search(r'dvd|b[rd]rip|blue?-?ray', base_filename, re.I) is not None]
        except Exception:
            pass

        return quality

    @staticmethod
    def scene_quality_from_name(name, quality):
        """
        Get scene naming parameters from filename and quality

        :param name: Filename to check
        :param quality: int of quality to make sure we get the right rip type
        :return: encoder type for scene quality naming
        """
        codecList = ['xvid', 'divx']
        x264List = ['x264', 'x 264', 'x.264']
        h264List = ['h264', 'h 264', 'h.264', 'avc']
        x265List = ['x265', 'x 265', 'x.265']
        h265List = ['h265', 'h 265', 'h.265', 'hevc']
        codecList.extend(x264List + h264List + x265List + h265List)

        found_codecs = {}
        found_codec = None
        rip_type = ""

        for codec in codecList:
            if codec in name.lower():
                found_codecs[name.lower().rfind(codec)] = codec

        if found_codecs:
            sorted_codecs = sorted(found_codecs, reverse=True)
            found_codec = found_codecs[list(sorted_codecs)[0]]

        if quality == Qualities.SDDVD:
            if re.search(r"b(r|d|rd)?([- .])?(rip|mux)", name.lower()):
                rip_type = " BDRip"
            elif re.search(r"(dvd)([- .])?(rip|mux)?", name.lower()):
                rip_type = " DVDRip"
            else:
                rip_type = ""

        if found_codec:
            if codecList[0] in found_codec:
                found_codec = 'XviD'
            elif codecList[1] in found_codec:
                found_codec = 'DivX'
            elif found_codec in x264List:
                found_codec = x264List[0]
            elif found_codec in h264List:
                found_codec = h264List[0]
            elif found_codec in x265List:
                found_codec = x265List[0]
            elif found_codec in h265List:
                found_codec = h265List[0]

            if quality == Qualities.SDDVD:
                return rip_type + " " + found_codec
            else:
                return " " + found_codec
        elif quality == Qualities.SDDVD:
            return rip_type
        else:
            return ""

    @staticmethod
    def status_from_name(name, assume=True, anime=False):
        """
        Get a status object from filename

        :param name: Filename to check
        :param assume: boolean to assume quality by extension if we can't figure it out
        :param anime: boolean to enable anime parsing
        :return: Composite status/quality object
        """
        quality = Quality.name_quality(name, anime)
        return Quality.composite_status(EpisodeStatus.DOWNLOADED, quality)

    @staticmethod
    def from_guessit(guess):
        """
        Return a Quality from a guessit dict.
        :param guess: guessit dict
        :type guess: dict
        :return: quality
        :rtype: int
        """
        guessit_map = {
            '720p': {
                'HDTV': Qualities.HDTV,
                'Web': Qualities.HDWEBDL,
                'Blu-ray': Qualities.HDBLURAY,
            },
            '1080i': Qualities.RAWHDTV,
            '1080p': {
                'HDTV': Qualities.FULLHDTV,
                'Web': Qualities.FULLHDWEBDL,
                'Blu-ray': Qualities.FULLHDBLURAY
            },
            '2160p': {
                'HDTV': Qualities.UHD_4K_TV,
                'Web': Qualities.UHD_4K_WEBDL,
                'Blu-ray': Qualities.UHD_4K_BLURAY
            },
            '4320p': {
                'HDTV': Qualities.UHD_8K_TV,
                'Web': Qualities.UHD_8K_WEBDL,
                'Blu-ray': Qualities.UHD_8K_BLURAY
            }
        }

        screen_size = guess.get('screen_size')
        source = guess.get('source')

        if not screen_size or isinstance(screen_size, list):
            return Qualities.UNKNOWN

        source_map = guessit_map.get(screen_size)
        if not source_map:
            return Qualities.UNKNOWN

        if isinstance(source_map, int):
            return source_map

        if not source or isinstance(source, list):
            return Qualities.UNKNOWN

        quality = source_map.get(source)
        return quality if quality is not None else Qualities.UNKNOWN

    @staticmethod
    def to_guessit(quality):
        """
        Return a guessit dict containing 'screen_size and source' from a Quality.
        :param quality: a quality
        :type quality: int
        :return: dict {'screen_size': <screen_size>, 'source': <source>}
        :rtype: dict (str, str)
        """
        if quality not in Qualities:
            quality = Qualities.UNKNOWN

        screen_size = Quality.to_guessit_screen_size(quality)
        source = Quality.to_guessit_source(quality)

        result = {}
        if screen_size:
            result['screen_size'] = screen_size
        if source:
            result['source'] = source

        return result

    @staticmethod
    def to_guessit_source(quality):
        """
        Return a guessit source from a Quality.
        :param quality: the quality
        :type quality: int
        :return: guessit source
        :rtype: str
        """

        source_map = {
            Qualities.ANYHDTV | Qualities.UHD_4K_TV | Qualities.UHD_8K_TV: 'HDTV',
            Qualities.ANYWEBDL | Qualities.UHD_4K_WEBDL | Qualities.UHD_8K_WEBDL: 'Web',
            Qualities.ANYBLURAY | Qualities.UHD_4K_BLURAY | Qualities.UHD_8K_BLURAY: 'Blu-ray'
        }

        for quality_set, source in source_map.items():
            if quality_set & quality:
                return source

    @staticmethod
    def to_guessit_screen_size(quality):
        """
        Return a guessit screen_size from a Quality.
        :param quality: the quality
        :type quality: int
        :return: guessit screen_size
        :rtype: str
        """

        screen_size_map = {
            Qualities.HDTV | Qualities.HDWEBDL | Qualities.HDBLURAY: '720p',
            Qualities.RAWHDTV: '1080i',
            Qualities.FULLHDTV | Qualities.FULLHDWEBDL | Qualities.FULLHDBLURAY: '1080p',
            Qualities.UHD_4K_TV | Qualities.UHD_4K_WEBDL | Qualities.UHD_4K_BLURAY: '2160p',
            Qualities.UHD_8K_TV | Qualities.UHD_8K_WEBDL | Qualities.UHD_8K_BLURAY: '4320p',
        }

        for quality_set, screen_size in screen_size_map.items():
            if quality_set & quality:
                return screen_size


class Qualities(enum.IntFlag):
    NONE = 0  # 0
    SDTV = 1  # 1
    SDDVD = 1 << 1  # 2
    HDTV = 1 << 2  # 4
    RAWHDTV = 1 << 3  # 8  -- 720P/1080I MPEG2 (TROLLHD RELEASES)
    FULLHDTV = 1 << 4  # 16 -- 1080P HDTV (QCF RELEASES)
    HDWEBDL = 1 << 5  # 32
    FULLHDWEBDL = 1 << 6  # 64 -- 1080P WEB-DL
    HDBLURAY = 1 << 7  # 128
    FULLHDBLURAY = 1 << 8  # 256
    UHD_4K_TV = 1 << 9  # 512 -- 2160P AKA 4K UHD AKA UHD-1
    UHD_4K_WEBDL = 1 << 10  # 1024
    UHD_4K_BLURAY = 1 << 11  # 2048
    UHD_8K_TV = 1 << 12  # 4096 -- 4320P AKA 8K UHD AKA UHD-2
    UHD_8K_WEBDL = 1 << 13  # 8192
    UHD_8K_BLURAY = 1 << 14  # 16384

    ANYHDTV = HDTV | FULLHDTV  # 20
    ANYWEBDL = HDWEBDL | FULLHDWEBDL  # 96
    ANYBLURAY = HDBLURAY | FULLHDBLURAY

    UNKNOWN = 1 << 15  # 32768

    # Presets
    SD = Quality.combine_qualities([SDTV, SDDVD], [])
    HD720P = Quality.combine_qualities([HDTV, HDWEBDL, HDBLURAY], [])
    HD1080P = Quality.combine_qualities([FULLHDTV, FULLHDWEBDL, FULLHDBLURAY], [])
    HD = Quality.combine_qualities([HD720P, HD1080P, RAWHDTV], [])
    UHD_4K = Quality.combine_qualities([UHD_4K_TV, UHD_4K_WEBDL, UHD_4K_BLURAY], [])
    UHD_8K = Quality.combine_qualities([UHD_8K_TV, UHD_8K_WEBDL, UHD_8K_BLURAY], [])
    UHD = Quality.combine_qualities([UHD_4K, UHD_8K], [])
    ANY = Quality.combine_qualities([SD, HD, UHD], [])
    ANY_PLUS_UNKNOWN = Quality.combine_qualities([UNKNOWN, SD, HD, UHD], [])

    @property
    def _strings(self):
        return {
            self.NONE.name: "N/A",
            self.UNKNOWN.name: "Unknown",
            self.SDTV.name: "SDTV",
            self.SDDVD.name: "SD DVD",
            self.HDTV.name: "720p HDTV",
            self.RAWHDTV.name: "RawHD",
            self.FULLHDTV.name: "1080p HDTV",
            self.HDWEBDL.name: "720p WEB-DL",
            self.FULLHDWEBDL.name: "1080p WEB-DL",
            self.HDBLURAY.name: "720p BluRay",
            self.FULLHDBLURAY.name: "1080p BluRay",
            self.UHD_4K_TV.name: "4K UHD TV",
            self.UHD_8K_TV.name: "8K UHD TV",
            self.UHD_4K_WEBDL.name: "4K UHD WEB-DL",
            self.UHD_8K_WEBDL.name: "8K UHD WEB-DL",
            self.UHD_4K_BLURAY.name: "4K UHD BluRay",
            self.UHD_8K_BLURAY.name: "8K UHD BluRay"
        }

    @property
    def _preset_strings(self):
        return {
            self.SD.name: "SD",
            self.HD.name: "HD",
            self.HD720P.name: "HD720p",
            self.HD1080P.name: "HD1080p",
            self.UHD.name: "UHD",
            self.UHD_4K.name: "UHD-4K",
            self.UHD_8K.name: "UHD-8K",
            self.ANY.name: "Any",
            self.ANY_PLUS_UNKNOWN.name: "Any + Unknown"
        }

    @property
    def _scene_strings(self):
        return {
            self.NONE.name: "N/A",
            self.UNKNOWN.name: "Unknown",
            self.SDTV.name: "HDTV",
            self.SDDVD.name: "",
            self.HDTV.name: "720p HDTV",
            self.RAWHDTV.name: "1080i HDTV",
            self.FULLHDTV.name: "1080p HDTV",
            self.HDWEBDL.name: "720p WEB-DL",
            self.FULLHDWEBDL.name: "1080p WEB-DL",
            self.HDBLURAY.name: "720p BluRay",
            self.FULLHDBLURAY.name: "1080p BluRay",
            self.UHD_4K_TV.name: "4K UHD TV",
            self.UHD_8K_TV.name: "8K UHD TV",
            self.UHD_4K_WEBDL.name: "4K UHD WEB-DL",
            self.UHD_8K_WEBDL.name: "8K UHD WEB-DL",
            self.UHD_4K_BLURAY.name: "4K UHD BluRay",
            self.UHD_8K_BLURAY.name: "8K UHD BluRay"
        }

    @property
    def _css_strings(self):
        return {
            self.NONE.name: "N/A",
            self.UNKNOWN.name: "Unknown",
            self.SDTV.name: "SDTV",
            self.SDDVD.name: "SDDVD",
            self.HDTV.name: "HD720p",
            self.RAWHDTV.name: "RawHD",
            self.FULLHDTV.name: "HD1080p",
            self.HDWEBDL.name: "HD720p",
            self.FULLHDWEBDL.name: "HD1080p",
            self.HDBLURAY.name: "HD720p",
            self.FULLHDBLURAY.name: "HD1080p",
            self.UHD_4K_TV.name: "UHD-4K",
            self.UHD_8K_TV.name: "UHD-8K",
            self.UHD_4K_WEBDL.name: "UHD-4K",
            self.UHD_8K_WEBDL.name: "UHD-8K",
            self.UHD_4K_BLURAY.name: "UHD-4K",
            self.UHD_8K_BLURAY.name: "UHD-8K",
            self.ANYHDTV.name: "any-hd",
            self.ANYWEBDL.name: "any-hd",
            self.ANYBLURAY.name: "any-hd"
        }

    @property
    def _combined_strings(self):
        return {
            self.ANYHDTV.name: "HDTV",
            self.ANYWEBDL.name: "WEB-DL",
            self.ANYBLURAY.name: "BluRay"
        }

    @property
    def display_name(self):
        if self.name in self._strings:
            return self._strings[self.name]
        elif self.name in self._preset_strings:
            return self._preset_strings[self.name]
        elif self.name in self._combined_strings:
            return self._combined_strings[self.name]
        return "Custom"

    @property
    def scene_name(self):
        if self.name in self._scene_strings:
            return self._scene_strings[self.name]
        return ""

    @property
    def css_name(self):
        if self.name in self._css_strings:
            return self._css_strings[self.name]
        elif self.name in self._preset_strings:
            return self._preset_strings[self.name]
        return ""

    @property
    def is_preset(self):
        return self.name in self._preset_strings

    @property
    def is_combined(self):
        return self.name in self._combined_strings


# extend episode status enum class with composite statuses
[extend_enum(EpisodeStatus, f"{status.name}_{q.name}", status + 100 * q)
 for status in list(EpisodeStatus).copy()
 for q in Qualities if not q.is_preset and status in [EpisodeStatus.DOWNLOADED,
                                                      EpisodeStatus.SNATCHED,
                                                      EpisodeStatus.SNATCHED_BEST,
                                                      EpisodeStatus.SNATCHED_PROPER,
                                                      EpisodeStatus.ARCHIVED,
                                                      EpisodeStatus.FAILED,
                                                      EpisodeStatus.IGNORED]]
