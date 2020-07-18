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


import operator
import pathlib
import re
from collections import UserDict
from functools import reduce

from sickrage.core.helpers.metadata import get_file_metadata, get_resolution

# CPU Presets for sleep timers
cpu_presets = {
    'HIGH': 0.05,
    'NORMAL': 0.02,
    'LOW': 0.01
}

countryList = {'Australia': 'AU',
               'Canada': 'CA',
               'USA': 'US'}

dateFormat = '%Y-%m-%d'
dateTimeFormat = '%Y-%m-%d %H:%M:%S'
timeFormat = '%A %I:%M %p'

# Other constants
MULTI_EP_RESULT = -1
SEASON_RESULT = -2

# Episode statuses
UNKNOWN = -1  # should never happen
UNAIRED = 1  # episodes that haven't aired yet
SNATCHED = 2  # qualified with quality
WANTED = 3  # episodes we don't have but want to get
DOWNLOADED = 4  # qualified with quality
SKIPPED = 5  # episodes we don't want
ARCHIVED = 6  # episodes that you don't have locally (counts toward download completion stats)
IGNORED = 7  # episodes that you don't want included in your download stats
SNATCHED_PROPER = 9  # qualified with quality
SUBTITLED = 10  # qualified with quality
FAILED = 11  # episode downloaded or snatched we don't want
SNATCHED_BEST = 12  # episode redownloaded using best quality
MISSED = 13  # episode missed

NAMING_REPEAT = 1
NAMING_EXTEND = 2
NAMING_DUPLICATE = 4
NAMING_LIMITED_EXTEND = 8
NAMING_SEPARATED_REPEAT = 16
NAMING_LIMITED_EXTEND_E_PREFIXED = 32

multiEpStrings = {NAMING_REPEAT: _("Repeat"),
                  NAMING_SEPARATED_REPEAT: _("Repeat (Separated)"),
                  NAMING_DUPLICATE: _("Duplicate"),
                  NAMING_EXTEND: _("Extend"),
                  NAMING_LIMITED_EXTEND: _("Extend (Limited)"),
                  NAMING_LIMITED_EXTEND_E_PREFIXED: _("Extend (Limited, E-prefixed)")}


class SearchFormats(object):
    STANDARD = 1
    AIR_BY_DATE = 2
    ANIME = 3
    SPORTS = 4
    COLLECTION = 6

    search_format_strings = {
        STANDARD: 'Standard (Show.S01E01)',
        AIR_BY_DATE: 'Air By Date (Show.2010.03.02)',
        ANIME: 'Anime (Show.265)',
        SPORTS: 'Sports (Show.2010.03.02)',
        COLLECTION: 'Collection (Show.Series.1.1of10) or (Show.Series.1.Part.1)'
    }


class Quality(object):
    NONE = 0  # 0
    SDTV = 1  # 1
    SDDVD = 1 << 1  # 2
    HDTV = 1 << 2  # 4
    RAWHDTV = 1 << 3  # 8  -- 720p/1080i mpeg2 (trollhd releases)
    FULLHDTV = 1 << 4  # 16 -- 1080p HDTV (QCF releases)
    HDWEBDL = 1 << 5  # 32
    FULLHDWEBDL = 1 << 6  # 64 -- 1080p web-dl
    HDBLURAY = 1 << 7  # 128
    FULLHDBLURAY = 1 << 8  # 256
    UHD_4K_TV = 1 << 9  # 512 -- 2160p aka 4K UHD aka UHD-1
    UHD_4K_WEBDL = 1 << 10  # 1024
    UHD_4K_BLURAY = 1 << 11  # 2048
    UHD_8K_TV = 1 << 12  # 4096 -- 4320p aka 8K UHD aka UHD-2
    UHD_8K_WEBDL = 1 << 13  # 8192
    UHD_8K_BLURAY = 1 << 14  # 16384
    ANYHDTV = HDTV | FULLHDTV  # 20
    ANYWEBDL = HDWEBDL | FULLHDWEBDL  # 96
    ANYBLURAY = HDBLURAY | FULLHDBLURAY  # 384

    # put these bits at the other end of the spectrum, far enough out that they shouldn't interfere
    UNKNOWN = 1 << 15  # 32768

    qualitySizes = {NONE: 0,
                    UNKNOWN: 500,
                    SDTV: 1200,
                    SDDVD: 1200,
                    HDTV: 1500,
                    RAWHDTV: 1500,
                    FULLHDTV: 1500,
                    HDWEBDL: 1500,
                    FULLHDWEBDL: 1800,
                    HDBLURAY: 1500,
                    FULLHDBLURAY: 1800,
                    UHD_4K_TV: 8000,
                    UHD_8K_TV: 16000,
                    UHD_4K_WEBDL: 8000,
                    UHD_8K_WEBDL: 16000,
                    UHD_4K_BLURAY: 8000,
                    UHD_8K_BLURAY: 16000}

    qualityStrings = {NONE: "N/A",
                      UNKNOWN: "Unknown",
                      SDTV: "SDTV",
                      SDDVD: "SD DVD",
                      HDTV: "720p HDTV",
                      RAWHDTV: "RawHD",
                      FULLHDTV: "1080p HDTV",
                      HDWEBDL: "720p WEB-DL",
                      FULLHDWEBDL: "1080p WEB-DL",
                      HDBLURAY: "720p BluRay",
                      FULLHDBLURAY: "1080p BluRay",
                      UHD_4K_TV: "4K UHD TV",
                      UHD_8K_TV: "8K UHD TV",
                      UHD_4K_WEBDL: "4K UHD WEB-DL",
                      UHD_8K_WEBDL: "8K UHD WEB-DL",
                      UHD_4K_BLURAY: "4K UHD BluRay",
                      UHD_8K_BLURAY: "8K UHD BluRay"}

    sceneQualityStrings = {NONE: "N/A",
                           UNKNOWN: "Unknown",
                           SDTV: "HDTV",
                           SDDVD: "",
                           HDTV: "720p HDTV",
                           RAWHDTV: "1080i HDTV",
                           FULLHDTV: "1080p HDTV",
                           HDWEBDL: "720p WEB-DL",
                           FULLHDWEBDL: "1080p WEB-DL",
                           HDBLURAY: "720p BluRay",
                           FULLHDBLURAY: "1080p BluRay",
                           UHD_4K_TV: "4K UHD TV",
                           UHD_8K_TV: "8K UHD TV",
                           UHD_4K_WEBDL: "4K UHD WEB-DL",
                           UHD_8K_WEBDL: "8K UHD WEB-DL",
                           UHD_4K_BLURAY: "4K UHD BluRay",
                           UHD_8K_BLURAY: "8K UHD BluRay"}

    combinedQualityStrings = {ANYHDTV: "HDTV",
                              ANYWEBDL: "WEB-DL",
                              ANYBLURAY: "BluRay"}

    cssClassStrings = {NONE: "N/A",
                       UNKNOWN: "Unknown",
                       SDTV: "SDTV",
                       SDDVD: "SDDVD",
                       HDTV: "HD720p",
                       RAWHDTV: "RawHD",
                       FULLHDTV: "HD1080p",
                       HDWEBDL: "HD720p",
                       FULLHDWEBDL: "HD1080p",
                       HDBLURAY: "HD720p",
                       FULLHDBLURAY: "HD1080p",
                       UHD_4K_TV: "UHD-4K",
                       UHD_8K_TV: "UHD-8K",
                       UHD_4K_WEBDL: "UHD-4K",
                       UHD_8K_WEBDL: "UHD-8K",
                       UHD_4K_BLURAY: "UHD-4K",
                       UHD_8K_BLURAY: "UHD-8K",
                       ANYHDTV: "any-hd",
                       ANYWEBDL: "any-hd",
                       ANYBLURAY: "any-hd"}

    statusPrefixes = {DOWNLOADED: _("Downloaded"),
                      SNATCHED: _("Snatched"),
                      SNATCHED_PROPER: _("Snatched (Proper)"),
                      SNATCHED_BEST: _("Snatched (Best)"),
                      ARCHIVED: _("Archived"),
                      FAILED: _("Failed"),
                      MISSED: _("Missed"), }

    @staticmethod
    def _get_status_strings(status):
        """
        Returns string values associated with Status prefix

        :param status: Status prefix to resolve
        :return: Human readable status value
        """
        toReturn = {}
        for q in Quality.qualityStrings.keys():
            toReturn[Quality.composite_status(status, q)] = Quality.statusPrefixes[status] + " (" + \
                                                            Quality.qualityStrings[q] + ")"
        return toReturn

    @staticmethod
    def combine_qualities(anyQualities, bestQualities):
        anyQuality = 0
        bestQuality = 0

        if anyQualities:
            anyQuality = reduce(operator.or_, anyQualities, anyQuality)
        if bestQualities:
            bestQuality = reduce(operator.or_, bestQualities, bestQuality)

        return anyQuality | (bestQuality << 16)

    @staticmethod
    def split_quality(quality):
        anyQualities = []
        bestQualities = []

        for curQual in Quality.qualityStrings.keys():
            if curQual & quality:
                anyQualities.append(curQual)
            if curQual << 16 & quality:
                bestQualities.append(curQual)

        return sorted(anyQualities), sorted(bestQualities)

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
        if quality != Quality.UNKNOWN:
            return quality

        quality = Quality.quality_from_file_meta(name)
        if quality != Quality.UNKNOWN:
            return quality

        if name.lower().endswith(".ts"):
            return Quality.RAWHDTV

        return Quality.UNKNOWN

    @staticmethod
    def scene_quality(name, anime=False):
        """
        Return The quality from the scene episode File

        :param name: Episode filename to analyse
        :param anime: Boolean to indicate if the show we're resolving is Anime
        :return: Quality prefix
        """

        # pylint: disable=R0912

        ret = Quality.UNKNOWN
        if not name:
            return ret

        name = pathlib.Path(name).name

        check_name = lambda l, func: func([re.search(x, name, re.I) for x in l])

        if anime:
            dvdOptions = check_name([r"dvd", r"dvdrip"], any)
            blueRayOptions = check_name([r"BD", r"blue?-?ray"], any)
            sdOptions = check_name([r"360p", r"480p", r"848x480", r"XviD"], any)
            hdOptions = check_name([r"720p", r"1280x720", r"960x720"], any)
            fullHD = check_name([r"1080p", r"1920x1080"], any)

            if sdOptions and not blueRayOptions and not dvdOptions:
                ret = Quality.SDTV
            elif dvdOptions:
                ret = Quality.SDDVD
            elif hdOptions and not blueRayOptions and not fullHD:
                ret = Quality.HDTV
            elif fullHD and not blueRayOptions and not hdOptions:
                ret = Quality.FULLHDTV
            elif hdOptions and not blueRayOptions and not fullHD:
                ret = Quality.HDWEBDL
            elif blueRayOptions and hdOptions and not fullHD:
                ret = Quality.HDBLURAY
            elif blueRayOptions and fullHD and not hdOptions:
                ret = Quality.FULLHDBLURAY

            return ret

        if (check_name([r"480p|\bweb\b|web.?dl|web(rip|mux|hd)|[sph]d.?tv|dsr|tv(rip|mux)|satrip", r"xvid|divx|[xh].?26[45]"], all)
                and not check_name([r"(720|1080|2160|4320)[pi]"], all)
                and not check_name([r"hr.ws.pdtv.[xh].?26[45]"], any)):
            ret = Quality.SDTV
        elif (check_name([r"dvd(rip|mux)|b[rd](rip|mux)|blue?-?ray", r"xvid|divx|[xh].?26[45]"], all)
              and not check_name([r"(720|1080|2160|4320)[pi]"], all)
              and not check_name([r"hr.ws.pdtv.[xh].?26[45]"], any)):
            ret = Quality.SDDVD
        elif (check_name([r"720p", r"hd.?tv", r"[xh].?26[45]"], all)
              or check_name([r"720p", r"hevc", r"[xh].?26[45]"], all)
              or check_name([r"hr.ws.pdtv.[xh].?26[45]"], any) and not check_name([r"1080[pi]"], all)):
            ret = Quality.HDTV
        elif (check_name([r"720p|1080i", r"hd.?tv", r"mpeg-?2"], all)
              or check_name([r"1080[pi].hdtv", r"h.?26[45]"], all)):
            ret = Quality.RAWHDTV
        elif (check_name([r"1080p", r"hd.?tv", r"[xh].?26[45]"], all)
              or check_name([r"1080p", r"hevc", r"[xh].?26[45]"], all)):
            ret = Quality.FULLHDTV
        elif (check_name([r"720p", r"\bweb\b|web.?dl|web(rip|mux|hd)"], all)
              or check_name([r"720p", r"itunes", r"[xh].?26[45]"], all)):
            ret = Quality.HDWEBDL
        elif (check_name([r"1080p", r"\bweb\b|web.?dl|web(rip|mux|hd)"], all)
              or check_name([r"1080p", r"itunes", r"[xh].?26[45]"], all)):
            ret = Quality.FULLHDWEBDL
        elif check_name([r"720p", r"blue?-?ray|hddvd|b[rd](rip|mux)", r"[xh].?26[45]"], all):
            ret = Quality.HDBLURAY
        elif check_name([r"1080p", r"blue?-?ray|hddvd|b[rd](rip|mux)", r"[xh].?26[45]"], all):
            ret = Quality.FULLHDBLURAY
        elif check_name([r"2160p", r"hd.?tv", r"[xh].?26[45]"], all):
            ret = Quality.UHD_4K_TV
        elif check_name([r"4320p", r"hd.?tv", r"[xh].?26[45]"], all):
            ret = Quality.UHD_8K_TV
        elif (check_name([r"2160p", r"\bweb\b|web.?dl|web(rip|mux|hd)"], all)
              or check_name([r"2160p", r"itunes", r"[xh].?26[45]"], all)):
            ret = Quality.UHD_4K_WEBDL
        elif (check_name([r"4320p", r"\bweb\b|web.?dl|web(rip|mux|hd)"], all)
              or check_name([r"4320p", r"itunes", r"[xh].?26[45]"], all)):
            ret = Quality.UHD_8K_WEBDL
        elif check_name([r"2160p", r"blue?-?ray|hddvd|b[rd](rip|mux)", r"[xh].?26[45]"], all):
            ret = Quality.UHD_4K_BLURAY
        elif check_name([r"4320p", r"blue?-?ray|hddvd|b[rd](rip|mux)", r"[xh].?26[45]"], all):
            ret = Quality.UHD_8K_BLURAY

        return ret

    @staticmethod
    def composite_status(status, quality):
        return status + 100 * quality

    @staticmethod
    def quality_downloaded(status):
        return (status - DOWNLOADED) / 100

    @staticmethod
    def split_composite_status(status):
        """Returns a tuple containing (status, quality)"""
        if status == UNKNOWN:
            return UNKNOWN, Quality.UNKNOWN

        for q in sorted(Quality.qualityStrings.keys(), reverse=True):
            if status > q * 100:
                return status - q * 100, q

        return status, Quality.NONE

    @staticmethod
    def status_from_composite_status(status):
        status, quality = Quality.split_composite_status(status)
        return status

    @staticmethod
    def quality_from_composite_status(status):
        status, quality = Quality.split_composite_status(status)
        return quality

    @staticmethod
    def quality_from_file_meta(filename):
        """
        Get quality from file metadata

        :param filename: Filename to analyse
        :return: Quality prefix
        """

        data = {}
        quality = Quality.UNKNOWN

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
                    quality = ((Quality.UHD_8K_TV, Quality.UHD_8K_BLURAY)[bluray], Quality.UHD_8K_WEBDL)[webdl]
                if 1620 < data['resolution_height'] <= 3240:
                    quality = ((Quality.UHD_4K_TV, Quality.UHD_4K_BLURAY)[bluray], Quality.UHD_4K_WEBDL)[webdl]
                elif 800 < data['resolution_height'] <= 1620:
                    quality = ((Quality.FULLHDTV, Quality.FULLHDBLURAY)[bluray], Quality.FULLHDWEBDL)[webdl]
                elif 680 < data['resolution_height'] < 800:
                    quality = ((Quality.HDTV, Quality.HDBLURAY)[bluray], Quality.HDWEBDL)[webdl]
                elif data['resolution_height'] < 680:
                    quality = (Quality.SDTV, Quality.SDDVD)[
                        re.search(r'dvd|b[rd]rip|blue?-?ray', base_filename, re.I) is not None]
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

        # 2 corresponds to SDDVD quality
        if quality == 2:
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

            if quality == 2:
                return rip_type + " " + found_codec
            else:
                return " " + found_codec
        elif quality == 2:
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
        return Quality.composite_status(DOWNLOADED, quality)

    DOWNLOADED = None
    SNATCHED = None
    SNATCHED_PROPER = None
    SNATCHED_BEST = None
    ARCHIVED = None
    FAILED = None
    IGNORED = None


Quality.DOWNLOADED = [Quality.composite_status(DOWNLOADED, x) for x in Quality.qualityStrings.keys()]
Quality.SNATCHED = [Quality.composite_status(SNATCHED, x) for x in Quality.qualityStrings.keys()]
Quality.SNATCHED_PROPER = [Quality.composite_status(SNATCHED_PROPER, x) for x in Quality.qualityStrings.keys()]
Quality.SNATCHED_BEST = [Quality.composite_status(SNATCHED_BEST, x) for x in Quality.qualityStrings.keys()]
Quality.ARCHIVED = [Quality.composite_status(ARCHIVED, x) for x in Quality.qualityStrings.keys()]
Quality.FAILED = [Quality.composite_status(FAILED, x) for x in Quality.qualityStrings.keys()]
Quality.IGNORED = [Quality.composite_status(IGNORED, x) for x in Quality.qualityStrings.keys()]

Quality.DOWNLOADED.sort()
Quality.SNATCHED.sort()
Quality.SNATCHED_BEST.sort()
Quality.SNATCHED_PROPER.sort()
Quality.FAILED.sort()
Quality.ARCHIVED.sort()

HD720p = Quality.combine_qualities([Quality.HDTV, Quality.HDWEBDL, Quality.HDBLURAY], [])
HD1080p = Quality.combine_qualities([Quality.FULLHDTV, Quality.FULLHDWEBDL, Quality.FULLHDBLURAY], [])
UHD_4K = Quality.combine_qualities([Quality.UHD_4K_TV, Quality.UHD_4K_WEBDL, Quality.UHD_4K_BLURAY], [])
UHD_8K = Quality.combine_qualities([Quality.UHD_8K_TV, Quality.UHD_8K_WEBDL, Quality.UHD_8K_BLURAY], [])

SD = Quality.combine_qualities([Quality.SDTV, Quality.SDDVD], [])
HD = Quality.combine_qualities([HD720p, HD1080p, Quality.RAWHDTV], [])
UHD = Quality.combine_qualities([UHD_4K, UHD_8K], [])
ANY = Quality.combine_qualities([SD, HD, UHD], [])
ANY_PLUS_UNKNOWN = Quality.combine_qualities([Quality.UNKNOWN, SD, HD, UHD], [])

# legacy template, cant remove due to reference in mainDB upgrade?
BEST = Quality.combine_qualities([Quality.SDTV, Quality.HDTV, Quality.HDWEBDL], [Quality.HDTV])

qualityPresets = (SD,
                  HD,
                  HD720p,
                  HD1080p,
                  UHD,
                  UHD_4K,
                  UHD_8K,
                  ANY,
                  ANY_PLUS_UNKNOWN)

qualityPresetStrings = {SD: "SD",
                        HD: "HD",
                        HD720p: "HD720p",
                        HD1080p: "HD1080p",
                        UHD: "UHD",
                        UHD_4K: "UHD-4K",
                        UHD_8K: "UHD-8K",
                        ANY: "Any",
                        ANY_PLUS_UNKNOWN: "Any + Unknown"}


class StatusStrings(UserDict):
    """
    Dictionary containing strings for status codes

    Keys must be convertible to int or a ValueError will be raised.  This is intentional to match old functionality until
    the old StatusStrings is fully deprecated, then we will raise a KeyError instead, where appropriate.

    Membership checks using __contains__ (i.e. 'x in y') do not raise a ValueError to match expected dict functionality
    """

    # todo: Deprecate StatusStrings().status_strings and use StatusStrings() directly
    # todo: Deprecate .has_key and switch to 'x in y'
    # todo: Switch from raising ValueError to a saner KeyError
    # todo: Raise KeyError when unable to resolve a missing key instead of returning ''
    # todo: Make key of None match dict() functionality

    @property
    def status_strings(self):  # for backwards compatibility
        return self.data

    def __setitem__(self, key, value):
        self.data[int(key)] = value  # make sure all keys being assigned values are ints

    def __missing__(self, key):
        """
        If the key is not found, search for the missing key in qualities

        Keys must be convertible to int or a ValueError will be raised.  This is intentional to match old functionality until
        the old StatusStrings is fully deprecated, then we will raise a KeyError instead, where appropriate.
        """
        if isinstance(key, int):  # if the key is already an int...
            if key in list(
                    self.keys()) + Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST + Quality.ARCHIVED + Quality.FAILED:
                status, quality = Quality.split_composite_status(key)
                if quality == Quality.NONE:  # If a Quality is not listed... (shouldn't this be 'if not quality:'?)
                    return self[status]  # ...return the status...
                else:
                    return self[status] + " (" + Quality.qualityStrings[
                        quality] + ")"  # ...otherwise append the quality to the status
            else:
                return ''  # return '' to match old functionality when the numeric key is not found
        return self[int(key)]  # Since the key was not an int, let's try int(key) instead

    # Keep this until all has_key() checks are converted to 'key in dict'
    # or else has_keys() won't search __missing__ for keys
    def has_key(self, key):
        """
        Override has_key() to test membership using an 'x in y' search

        Keys must be convertible to int or a ValueError will be raised.  This is intentional to match old functionality until
        the old StatusStrings is fully deprecated, then we will raise a KeyError instead, where appropriate.
        """
        return key in self  # This will raise a ValueError if __missing__ can't convert the key to int

    def __contains__(self, key):
        """
        Checks for existence of key

        Unlike has_key() and __missing__() this will NOT raise a ValueError to match expected functionality
        when checking for 'key in dict'
        """
        try:
            # This will raise a ValueError if we can't convert the key to int
            return ((int(key) in self.data) or
                    (int(
                        key) in Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST + Quality.ARCHIVED + Quality.FAILED))
        except ValueError:  # The key is not numeric and since we only want numeric keys...
            # ...and we don't want this function to fail...
            pass  # ...suppress the ValueError and do nothing, the key does not exist


statusStrings = StatusStrings({UNKNOWN: _("Unknown"),
                               UNAIRED: _("Unaired"),
                               SNATCHED: _("Snatched"),
                               SNATCHED_PROPER: _("Snatched (Proper)"),
                               SNATCHED_BEST: _("Snatched (Best)"),
                               DOWNLOADED: _("Downloaded"),
                               SKIPPED: _("Skipped"),
                               WANTED: _("Wanted"),
                               ARCHIVED: _("Archived"),
                               IGNORED: _("Ignored"),
                               SUBTITLED: _("Subtitled"),
                               FAILED: _("Failed"),
                               MISSED: _("Missed")})


class Overview(object):
    UNAIRED = UNAIRED  # 1
    SNATCHED = SNATCHED  # 2
    WANTED = WANTED  # 3
    GOOD = DOWNLOADED  # 4
    SKIPPED = SKIPPED  # 5
    SNATCHED_PROPER = SNATCHED_PROPER  # 9
    SNATCHED_BEST = SNATCHED_BEST  # 12
    MISSED = MISSED  # 13

    QUAL = 50

    overviewStrings = {SKIPPED: "skipped",
                       WANTED: "wanted",
                       QUAL: "qual",
                       GOOD: "good",
                       UNAIRED: "unaired",
                       SNATCHED: "snatched",
                       SNATCHED_BEST: "snatched",
                       SNATCHED_PROPER: "snatched",
                       MISSED: "missed"}


def get_quality_string(quality):
    """
    :param quality: The quality to convert into a string
    :return: The string representation of the provided quality
    """

    if quality in qualityPresetStrings:
        return qualityPresetStrings[quality]

    if quality in Quality.qualityStrings:
        return Quality.qualityStrings[quality]

    return 'Custom'
